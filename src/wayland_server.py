"""
A wayland server class that runs a labwc wayland display and provides access to
it via a display string.
"""

import supervise_api
import os
import shlex
import tempfile
import time


class WaylandServer:
    def __init__(self, command: str, resolution: tuple[int, int]):
        """Starts a wayland compositor running the given shell command."""
        self.resolution = resolution

        with tempfile.NamedTemporaryFile(
            prefix="bounce_desk_handshake", mode="r+", encoding="utf-8"
        ) as tmp_file:
            self.wayland_display = ""
            subcompositor_command = shlex.split(command)
            if len(subcompositor_command) == 0:
                raise ValueError("WaylandServer requires a non-empty command")

            startup_command = shlex.join(
                [
                    "bash",
                    "src/labwc_entry.sh",
                    tmp_file.name,
                    str(resolution[0]),
                    str(resolution[1]),
                    "--",
                    *subcompositor_command,
                ]
            )
            env = {
                "WLR_RENDERER": os.environ.get("WLR_RENDERER", "vulkan"),
                "WLR_BACKENDS": os.environ.get("WLR_BACKENDS", "headless"),
            }
            self.p = supervise_api.Process(
                ["labwc", "-s", startup_command], env=env, fds={1: 1, 2: 2}
            )
            start = time.time()
            while time.time() - start < 3:
                tmp_file.seek(0)
                self.wayland_display = tmp_file.read().strip()
                if len(self.wayland_display) > 0:
                    break

                time.sleep(0.01)
            if not self.wayland_display.startswith("wayland-"):
                raise ValueError(
                    "Recieved unexpected display string from WaylandServer display "
                    f"string handshake: {repr(self.wayland_display)}"
                )

    def display_string(self) -> str:
        return self.wayland_display

    def get_resolution(self) -> tuple[int, int]:
        return self.resolution

    def get_desktop_env(self) -> dict[str, str]:
        return {"WAYLAND_DISPLAY": self.wayland_display}

    def __del__(self):
        try:
            self.p.close()
        except:  # noqa
            pass
