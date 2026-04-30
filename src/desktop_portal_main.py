from __future__ import annotations

import argparse

from desktop_portal import DesktopPortal
from wayland_client import WaylandClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("wayland_display")
    parser.add_argument("display_x_res", type=int)
    parser.add_argument("display_y_res", type=int)
    parser.add_argument("--title", default="ez_desk portal")
    parser.add_argument("--interactive", action="store_true", default=False)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = WaylandClient(
        args.wayland_display,
        (args.display_x_res, args.display_y_res),
    )

    with DesktopPortal(client, interactive=args.interactive, title=args.title) as portal:
        portal.run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
