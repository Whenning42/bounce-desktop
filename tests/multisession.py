# Verify that multiple concurrent desktop sessions run performantly.

from contextlib import contextmanager
from pathlib import Path
import shlex
import shutil
import tempfile
import time

from bounce_desktop import WaylandDesktop
from bounce_desktop.launch_portal import launch_portal


REPO_TMP_DIR = Path(__file__).resolve().parent.parent / "tmp"


@contextmanager
def factorio_copies(source: Path, count: int):
    REPO_TMP_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="factorio-multisession-",
        dir=REPO_TMP_DIR,
    ) as tmp_dir:
        tmp_path = Path(tmp_dir)
        copies = []
        for i in range(count):
            copy = tmp_path / str(i)
            shutil.copytree(source, copy, symlinks=True)
            copies.append(copy)
        yield copies


session_count = 4
resolution = (1000, 600)

with factorio_copies(Path.home() / "Games" / "factorio", session_count) as factorios:
    desktops = [
        WaylandDesktop(
            f"mangohud {shlex.quote(str(factorio / 'bin' / 'x64' / 'factorio'))}",
            resolution,
        )
        for factorio in factorios
    ]
    portals = [
        launch_portal(
            d.server.display_string(),
            d.get_resolution(),
            title="desktop view",
            interactive=True,
        )
        for d in desktops
    ]

    try:
        while True:
            time.sleep(10)
    finally:
        for p in portals:
            p.close()
        del portals
        del desktops
