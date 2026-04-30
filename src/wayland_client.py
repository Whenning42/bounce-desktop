"""
Lightweight Wayland GUI client: screenshot + virtual keyboard + virtual pointer.

Targets wlroots-style compositors that expose:
  - zwlr_screencopy_manager_v1
  - zwlr_virtual_pointer_manager_v1
  - zwp_virtual_keyboard_manager_v1

The virtual_keyboard protocol is not bundled with python-wayland, so on
first run we monkey-patch wayland.parser.REMOTE_PROTOCOL_SOURCES to
include the wlroots tree and trigger the package's own --download to
regenerate its protocols.json. Subsequent runs find the protocol present
and skip the regen.
"""

from __future__ import annotations

import os
import time
from buttons import X11_TO_EVDEV_BUTTON_MAP

from frame import Frame
from wayland_client_impl import take_screenshot, _Registry
from monkey_patch_wayland import monkey_patch_wayland_virtual_keyboard
from keymap import US_LAYOUT_KEYMAP, send_keymap
import wayland
from wayland.client.memory_pool import SharedMemoryPool

monkey_patch_wayland_virtual_keyboard()

_WL_KEYBOARD_KEY_STATE_RELEASED = 0
_WL_KEYBOARD_KEY_STATE_PRESSED = 1


class WaylandClient:
    """Headless Wayland client for screenshots and synthetic input.

    One process talks to one compositor; python-wayland's state is a
    singleton, so creating a second WaylandConnection in the same process
    isn't supported.
    """

    def __init__(self, display: str = "wayland-0"):
        os.environ["WAYLAND_DISPLAY"] = display

        self._display = wayland.wl_display()
        self._registry = self._display.get_registry()

        # Wait for required globals.
        while not all(getattr(self._registry, n) is not None for n in _Registry.NEEDED):
            self._display.dispatch_timeout(0.2)

        # Wait for output dimensions (needed for absolute pointer motion).
        out = self._registry.wl_output
        while out.width == 0 or out.height == 0:
            self._display.dispatch_timeout(0.2)
        self._output_w = out.width
        self._output_h = out.height

        self._pool = SharedMemoryPool(self._registry.wl_shm)

        self._pointer = (
            self._registry.zwlr_virtual_pointer_manager_v1.create_virtual_pointer(
                self._registry.wl_seat
            )
        )

        self._keyboard = (
            self._registry.zwp_virtual_keyboard_manager_v1.create_virtual_keyboard(
                self._registry.wl_seat
            )
        )
        self._keymap_file = send_keymap(self._keyboard, US_LAYOUT_KEYMAP)

    def screenshot(self) -> Frame:
        """Capture the current contents of the first wl_output."""
        return take_screenshot(self._registry, self._display, self._pool)

    def mouse_press(self, button: int) -> None:
        """Press a mouse button. button: 1=left, 2=middle, 3=right."""
        self._pointer.button(self._now_ms(), X11_TO_EVDEV_BUTTON_MAP[button], 1)
        self._pointer.frame()

    def mouse_release(self, button: int) -> None:
        """Release a mouse button. button: 1=left, 2=middle, 3=right."""
        self._pointer.button(self._now_ms(), X11_TO_EVDEV_BUTTON_MAP[button], 0)
        self._pointer.frame()

    def move_mouse(self, dx: float, dy: float) -> None:
        """Relative pointer motion in pixels."""
        self._pointer.motion(self._now_ms(), dx, dy)
        self._pointer.frame()

    def move_mouse_to(self, x: int, y: int) -> None:
        """Absolute pointer move to (x, y) in output-pixel coordinates."""
        self._pointer.motion_absolute(
            self._now_ms(), x, y, self._output_w, self._output_h
        )
        self._pointer.frame()

    def keycode_down(self, keycode: int) -> None:
        """Press a key given its evdev keycode."""
        self._keyboard.key(self._now_ms(), keycode, _WL_KEYBOARD_KEY_STATE_PRESSED)

    def keycode_up(self, keycode: int) -> None:
        """Release a key given its evdev keycode."""
        self._keyboard.key(self._now_ms(), keycode, _WL_KEYBOARD_KEY_STATE_RELEASED)

    @staticmethod
    def _now_ms() -> int:
        return int(time.monotonic() * 1000) & 0xFFFFFFFF

    def __del__(self):
        if hasattr(self, "_keymap_file"):
            self._keymap_file.close()
