import os
import wayland
from wayland.client.package import get_package_root
import json

_PROTOCOLS_JSON_PATH = os.path.join(get_package_root(), "protocols.json")


def monkey_patch_wayland_virtual_keyboard() -> None:
    """Monkey patc wlroots protocls into our wayland client library to enable
    the `zwp_virtual_keyboard_v1 protocol.`"""

    with open(_PROTOCOLS_JSON_PATH, encoding="utf-8") as f:
        if "zwp_virtual_keyboard_v1" in json.load(f):
            return

    from wayland import parser as _parser

    _parser.REMOTE_PROTOCOL_SOURCES.append(
        {
            "name": "wlroots",
            "url": "https://gitlab.freedesktop.org/wlroots/wlroots.git",
            "dirs": ["protocol"],
        }
    )

    from wayland.__main__ import main as _wayland_main

    saved_argv = sys.argv
    sys.argv = ["wayland", "--download"]
    try:
        _wayland_main()
    finally:
        sys.argv = saved_argv

    # Re-load the freshly written protocols.json into the live Proxy so the
    # new interfaces are usable in this same process.
    from wayland.proxy import Proxy

    Proxy().initialise(wayland.__dict__)
