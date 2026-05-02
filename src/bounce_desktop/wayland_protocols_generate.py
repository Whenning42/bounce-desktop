from __future__ import annotations

from pathlib import Path

from pywayland.scanner import Protocol


_ROOT = Path(__file__).resolve().parent
_OUTPUT_DIR = _ROOT / "wayland_generated_protocols"
_PROTOCOL_FILES = (
    _ROOT / "wayland_protocols" / "wayland.xml",
    _ROOT / "wayland_protocols" / "wlr-screencopy-unstable-v1.xml",
    _ROOT / "wayland_protocols" / "wlr-virtual-pointer-unstable-v1.xml",
    _ROOT / "wayland_protocols" / "virtual-keyboard-unstable-v1.xml",
)


def ensure_wayland_protocols() -> None:
    if (_OUTPUT_DIR / "wlr_screencopy_unstable_v1").is_dir():
        return

    protocols = [Protocol.parse_file(str(path)) for path in _PROTOCOL_FILES]
    module_imports = {
        interface.name: protocol.name
        for protocol in protocols
        for interface in protocol.interface
    }

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for protocol in protocols:
        protocol.output(str(_OUTPUT_DIR), module_imports)
