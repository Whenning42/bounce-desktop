"""
A Wayland + Labwc-based virtual desktop implementation.
"""

from wayland_client import WaylandClient
from wayland_server import WaylandServer


class WaylandDesktop:
    def __init__(self, command, resolution):
        self.server = WaylandServer(command, resolution)
        self.client = WaylandClient(self.server.display_string(), resolution)
        self._client_forwards = {
            "screenshot",
            "mouse_press",
            "mouse_release",
            "move_mouse",
            "move_mouse_to",
            "keycode_down",
            "keycode_up",
        }

    # TODO(code): Replace the _getattr__ dynamic dispatch with
    # actual method defintions that just forward to the client
    # implementations.

    def __getattr__(self, name):
        if name in self.__dict__.get("_client_forwards", ()):
            return getattr(self.client, name)

        raise AttributeError(
            f"Attribute {name} isn't on this WaylandDesktop, nor is it forwardable "
            "to the desktop's WaylandClient."
        )

    def get_desktop_env(self):
        return self.server.get_desktop_env()

    def __del__(self):
        # self.client and self.server might be unset if an exception is thrown
        # during __init__, so we hasattr check for these objects before deleting them.
        if "client" in self.__dict__:
            del self.client
        if "server" in self.__dict__:
            del self.server
