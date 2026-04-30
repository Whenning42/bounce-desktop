"""
Lightweight Wayland GUI client: screenshot + virtual keyboard + virtual pointer.

Targets wlroots-style compositors that expose:
  - zwlr_screencopy_manager_v1
  - zwlr_virtual_pointer_manager_v1
  - zwp_virtual_keyboard_manager_v1
"""

from __future__ import annotations

import time
from buttons import X11_TO_EVDEV_BUTTON_MAP

from frame import Frame
from pywayland.client import Display
from wayland_client_impl import dispatch_with_timeout, take_screenshot, _Registry
from keymap import US_LAYOUT_KEYMAP, send_keymap

_WL_KEYBOARD_KEY_STATE_RELEASED = 0
_WL_KEYBOARD_KEY_STATE_PRESSED = 1


class WaylandClient:
    """Headless Wayland client for screenshots and synthetic input.

    Each instance owns a separate pywayland Display connection, so multiple
    compositors can be driven concurrently in one process.
    """

    def __init__(
        self, display: str = "wayland-0", resolution: tuple[int, int] | None = None
    ):
        self._display = Display(display)
        self._display.connect()
        self._registry = _Registry(self._display.get_registry())

        # Wait for required globals.
        while not self._registry.has_required_globals():
            dispatch_with_timeout(self._display)
        self._display.roundtrip()

        if resolution is None:
            # Direct WaylandClient users fall back to the compositor's current
            # output mode. WaylandDesktop passes its fixed logical resolution.
            while not self._registry.has_output_size():
                dispatch_with_timeout(self._display)
            resolution = (self._registry.output_width, self._registry.output_height)
        self._output_w, self._output_h = resolution

        pointer_manager = self._registry.zwlr_virtual_pointer_manager_v1
        if hasattr(pointer_manager, "create_virtual_pointer_with_output"):
            self._pointer = pointer_manager.create_virtual_pointer_with_output(
                self._registry.wl_seat, self._registry.wl_output
            )
        else:
            self._pointer = (
                pointer_manager.create_virtual_pointer(self._registry.wl_seat)
            )

        self._keyboard = (
            self._registry.zwp_virtual_keyboard_manager_v1.create_virtual_keyboard(
                self._registry.wl_seat
            )
        )
        self._keymap_file = send_keymap(self._keyboard, US_LAYOUT_KEYMAP)
        self._flush()

    def screenshot(self) -> Frame:
        """Capture the current contents of the first wl_output."""
        return take_screenshot(self._registry, self._display)

    def mouse_press(self, button: int) -> None:
        """Press a mouse button. button: 1=left, 2=middle, 3=right."""
        self._pointer.button(self._now_ms(), X11_TO_EVDEV_BUTTON_MAP[button], 1)
        self._pointer.frame()
        self._flush()

    def mouse_release(self, button: int) -> None:
        """Release a mouse button. button: 1=left, 2=middle, 3=right."""
        self._pointer.button(self._now_ms(), X11_TO_EVDEV_BUTTON_MAP[button], 0)
        self._pointer.frame()
        self._flush()

    def move_mouse(self, dx: float, dy: float) -> None:
        """Relative pointer motion in pixels."""
        self._pointer.motion(self._now_ms(), dx, dy)
        self._pointer.frame()
        self._flush()

    def move_mouse_to(self, x: int, y: int) -> None:
        """Absolute pointer move to (x, y) in output-pixel coordinates."""
        self._pointer.motion_absolute(
            self._now_ms(), x, y, self._output_w, self._output_h
        )
        self._pointer.frame()
        self._flush()

    def keycode_down(self, keycode: int) -> None:
        """Press a key given its evdev keycode."""
        self._keyboard.key(self._now_ms(), keycode, _WL_KEYBOARD_KEY_STATE_PRESSED)
        self._flush()

    def keycode_up(self, keycode: int) -> None:
        """Release a key given its evdev keycode."""
        self._keyboard.key(self._now_ms(), keycode, _WL_KEYBOARD_KEY_STATE_RELEASED)
        self._flush()

    def _flush(self) -> None:
        self._display.flush()

    @staticmethod
    def _now_ms() -> int:
        return int(time.monotonic() * 1000) & 0xFFFFFFFF

    def __del__(self):
        if hasattr(self, "_keymap_file"):
            self._keymap_file.close()
        if hasattr(self, "_display"):
            self._display.disconnect()
