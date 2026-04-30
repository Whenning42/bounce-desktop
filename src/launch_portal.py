import supervise_api
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
_PORTAL_MAIN = _ROOT / "src" / "desktop_portal_main.py"


def launch_portal(
    wayland_display: str,
    resolution: tuple[int, int],
    *,
    title: str,
    interactive: bool = False,
) -> supervise_api.Process:
    command = [
        sys.executable,
        str(_PORTAL_MAIN),
        wayland_display,
        str(resolution[0]),
        str(resolution[1]),
        "--title",
        title,
    ]
    if interactive:
        command.append("--interactive")
    return supervise_api.Process(command)
