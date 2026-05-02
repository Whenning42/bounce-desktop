from typing import Protocol

import numpy as np


class Desktop(Protocol):
    """A virtual desktop interface. Supports frame capture and mouse and keyboard inputs."""

    def get_resolution(self) -> tuple[int, int]:
        """Returns the desktop's resolution."""
        ...

    def get_desktop_env(self) -> dict[str, str]:
        """Returns the environment variables that put processes onto this desktop."""
        ...

    def get_frame(self) -> np.ndarray:
        """Return an RGBA8888 frame as a uint8 array shaped (height, width, 4)."""
        ...

    def mouse_press(self, button: int) -> None:
        """Press a mouse button. Buttons are: 1=left, 2=middle, 3=right."""
        ...

    def mouse_release(self, button: int) -> None:
        """Release a mouse button. Buttons are: 1=left, 2=middle, 3=right."""
        ...

    def move_mouse(self, dx: float, dy: float) -> None:
        """Relative pointer motion in pixels."""
        ...

    def move_mouse_to(self, x: int, y: int) -> None:
        """Absolute pointer move to (x, y) in output-pixel coordinates."""
        ...

    def keycode_down(self, keycode: int) -> None:
        """Press down a key given its evdev keycode."""
        ...

    def keycode_up(self, keycode: int) -> None:
        """Release a key given its evdev keycode."""
        ...
