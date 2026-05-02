import tempfile

XKB_KEYMAP_FORMAT_TEXT_V1 = 1

US_LAYOUT_KEYMAP = b"""
xkb_keymap {
    xkb_keycodes  { include "evdev+aliases(qwerty)" };
    xkb_types     { include "complete" };
    xkb_compat    { include "complete" };
    xkb_symbols   { include "pc+us+inet(evdev)" };
    xkb_geometry  { include "pc(pc105)" };
};
""".lstrip()


def send_keymap(keyboard, keymap_text: bytes):
    """Returns a tempfile that the caller should keep open until it's done with the keyboard."""
    f = tempfile.TemporaryFile(prefix="vkb-keymap-")
    f.write(keymap_text)
    f.flush()
    size = f.tell()
    f.seek(0)
    keyboard.keymap(XKB_KEYMAP_FORMAT_TEXT_V1, f.fileno(), size)
    return f
