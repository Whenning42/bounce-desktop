"""
An SDL app that:
- Runs in fullscreen
- Sets (0, 0), (100, 0), (0, 100), (100, 100) to black, red, green, blue
  respectively
- Logs all mouse and keyboard events to the path given by "--log_to" if the
  argument was provided.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
from typing import TextIO

import sdl2

SDL_BUTTON_TO_DESKTOP = {
    sdl2.SDL_BUTTON_LEFT: 1,
    sdl2.SDL_BUTTON_MIDDLE: 2,
    sdl2.SDL_BUTTON_RIGHT: 3,
}


def sdl_error() -> str:
    err = sdl2.SDL_GetError()
    return err.decode("utf-8", errors="replace") if err else "unknown SDL error"


def fill_rect(
    surface: ctypes.POINTER(sdl2.SDL_Surface),
    x: int,
    y: int,
    width: int,
    height: int,
    color: tuple[int, int, int, int],
) -> None:
    mapped = sdl2.SDL_MapRGBA(surface.contents.format, *color)
    rect = sdl2.SDL_Rect(x, y, width, height)
    if sdl2.SDL_FillRect(surface, ctypes.byref(rect), mapped) != 0:
        raise RuntimeError(f"SDL_FillRect failed: {sdl_error()}")


def draw_test_pattern(window: ctypes.POINTER(sdl2.SDL_Window)) -> None:
    surface = sdl2.SDL_GetWindowSurface(window)
    if not surface:
        raise RuntimeError(f"SDL_GetWindowSurface failed: {sdl_error()}")

    fill_rect(
        surface,
        0,
        0,
        surface.contents.w,
        surface.contents.h,
        (255, 255, 255, 255),
    )
    fill_rect(surface, 0, 0, 1, 1, (0, 0, 0, 255))
    fill_rect(surface, 100, 0, 1, 1, (255, 0, 0, 255))
    fill_rect(surface, 0, 100, 1, 1, (0, 255, 0, 255))
    fill_rect(surface, 100, 100, 1, 1, (0, 0, 255, 255))

    if sdl2.SDL_UpdateWindowSurface(window) != 0:
        raise RuntimeError(f"SDL_UpdateWindowSurface failed: {sdl_error()}")


def write_log(log_file: TextIO | None, *parts: object) -> None:
    if log_file is None:
        return
    print(" ".join(str(part) for part in parts), file=log_file, flush=True)


def evdev_keycode_from_sdl_scancode(scancode: int) -> int:
    # SDL uses USB HID mappings which aren't generally convertible to evdevs in a nice
    # way, so we just hardcode a few correspondances.
    _mapping = {
        26: 17,  # W
        4: 30,  # A
        22: 31,  # S
    }

    if scancode in _mapping:
        return _mapping[scancode]
    return scancode


def event_loop(log_file: TextIO | None) -> None:
    event = sdl2.SDL_Event()
    drop_first_mouse = True

    while True:
        while sdl2.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl2.SDL_QUIT:
                return

            if event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
                if event.key.repeat:
                    continue
                name = (
                    "keycode_down" if event.type == sdl2.SDL_KEYDOWN else "keycode_up"
                )
                write_log(
                    log_file,
                    name,
                    evdev_keycode_from_sdl_scancode(event.key.keysym.scancode),
                )
                continue

            if event.type in (sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP):
                button = SDL_BUTTON_TO_DESKTOP.get(event.button.button)
                if button is None:
                    continue
                name = (
                    "mouse_press"
                    if event.type == sdl2.SDL_MOUSEBUTTONDOWN
                    else "mouse_release"
                )
                write_log(log_file, name, button)
                continue

            if event.type == sdl2.SDL_MOUSEMOTION:
                if drop_first_mouse:
                    drop_first_mouse = False
                    continue
                write_log(log_file, "move_mouse_to", event.motion.x, event.motion.y)

        sdl2.SDL_Delay(5)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_to", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if "WAYLAND_DISPLAY" in os.environ:
        os.environ.setdefault("SDL_VIDEODRIVER", "wayland")

    if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_EVENTS) != 0:
        raise RuntimeError(f"SDL_Init failed: {sdl_error()}")

    window = None
    log_file = None
    try:
        window = sdl2.SDL_CreateWindow(
            b"ez_desk test app",
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            640,
            480,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP,
        )
        if not window:
            raise RuntimeError(f"SDL_CreateWindow failed: {sdl_error()}")

        draw_test_pattern(window)

        if args.log_to is not None:
            log_file = open(args.log_to, "a", encoding="utf-8", buffering=1)
        event_loop(log_file)
    finally:
        if log_file is not None:
            log_file.close()
        if window:
            sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
