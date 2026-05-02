"""
A Wayland + Labwc-based virtual desktop implementation.
"""

from bounce_desktop.frame import Frame
from bounce_desktop.wayland_client import WaylandClient
from bounce_desktop.wayland_server import WaylandServer


class WaylandDesktop:
    def __init__(self, command, resolution):
        self.server = WaylandServer(command, resolution)
        self.client = WaylandClient(self.server.display_string(), resolution)

    def screenshot(self) -> Frame:
        return self.client.screenshot()

    def mouse_press(self, button: int) -> None:
        self.client.mouse_press(button)

    def mouse_release(self, button: int) -> None:
        self.client.mouse_release(button)

    def move_mouse(self, dx: float, dy: float) -> None:
        self.client.move_mouse(dx, dy)

    def move_mouse_to(self, x: int, y: int) -> None:
        self.client.move_mouse_to(x, y)

    def keycode_down(self, keycode: int) -> None:
        self.client.keycode_down(keycode)

    def keycode_up(self, keycode: int) -> None:
        self.client.keycode_up(keycode)

    def get_resolution(self):
        return self.server.get_resolution()

    def get_desktop_env(self):
        return self.server.get_desktop_env()

    def __del__(self):
        # self.client and self.server might be unset if an exception is thrown
        # during __init__, so we hasattr check for these objects before deleting them.
        if "client" in self.__dict__:
            del self.client
        if "server" in self.__dict__:
            del self.server
