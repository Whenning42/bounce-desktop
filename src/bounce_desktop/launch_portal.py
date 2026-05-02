import supervise_api
import sys


def launch_portal(
    wayland_display: str,
    resolution: tuple[int, int],
    *,
    title: str,
    interactive: bool = False,
) -> supervise_api.Process:
    command = [
        sys.executable,
        "-m",
        "bounce_desktop.desktop_portal_main",
        wayland_display,
        str(resolution[0]),
        str(resolution[1]),
        "--title",
        title,
    ]
    if interactive:
        command.append("--interactive")
    return supervise_api.Process(command)
