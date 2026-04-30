from __future__ import annotations

import ctypes
import os
import threading
import time

import sdl2

from frame import Frame
from sdl_to_evdev import SDL_TO_EVDEV
from wayland_client import WaylandClient

SDL_BUTTON_TO_DESKTOP = {
    sdl2.SDL_BUTTON_LEFT: 1,
    sdl2.SDL_BUTTON_MIDDLE: 2,
    sdl2.SDL_BUTTON_RIGHT: 3,
}

FRAME_FORMAT_TO_SDL_PIXEL_FORMAT = {
    "argb8888": sdl2.SDL_PIXELFORMAT_ARGB8888,
    "xrgb8888": sdl2.SDL_PIXELFORMAT_XRGB8888,
    "abgr8888": sdl2.SDL_PIXELFORMAT_ABGR8888,
    "xbgr8888": sdl2.SDL_PIXELFORMAT_XBGR8888,
}


def sdl_error() -> str:
    err = sdl2.SDL_GetError()
    return err.decode("utf-8", errors="replace") if err else "unknown SDL error"


def evdev_keycode_from_sdl_scancode(scancode: int) -> int:
    return SDL_TO_EVDEV.get(scancode, scancode)


class DesktopPortal:
    """Render a WaylandClient's output in an SDL window.

    Call run() to block until the SDL window is closed, or call pump()/render()
    from another loop when embedding the portal into a larger process.
    """

    def __init__(
        self,
        client: WaylandClient,
        interactive: bool = False,
        *,
        title: str = "ez_desk portal",
        fps: int = 60,
    ):
        if fps <= 0:
            raise ValueError("fps must be positive")

        self.client = client
        self.interactive = interactive
        self.fps = fps
        self.width, self.height = client.get_resolution()
        self.title = title
        self._running = True
        self._window = None
        self._renderer = None
        self._texture = None
        self._texture_spec: tuple[int, int, int] | None = None
        self._sdl_init_flags = 0
        self._thread: threading.Thread | None = None

        self._init_sdl()
        try:
            self._window = sdl2.SDL_CreateWindow(
                title.encode("utf-8"),
                sdl2.SDL_WINDOWPOS_UNDEFINED,
                sdl2.SDL_WINDOWPOS_UNDEFINED,
                self.width,
                self.height,
                sdl2.SDL_WINDOW_SHOWN,
            )
            if not self._window:
                raise RuntimeError(f"SDL_CreateWindow failed: {sdl_error()}")

            self._renderer = sdl2.SDL_CreateRenderer(
                self._window,
                -1,
                sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC,
            )
            if not self._renderer:
                self._renderer = sdl2.SDL_CreateRenderer(
                    self._window, -1, sdl2.SDL_RENDERER_SOFTWARE
                )
            if not self._renderer:
                raise RuntimeError(f"SDL_CreateRenderer failed: {sdl_error()}")

            if (
                sdl2.SDL_RenderSetLogicalSize(self._renderer, self.width, self.height)
                != 0
            ):
                raise RuntimeError(f"SDL_RenderSetLogicalSize failed: {sdl_error()}")
        except Exception:
            self.close()
            raise

    def _init_sdl(self) -> None:
        if "WAYLAND_DISPLAY" in os.environ:
            os.environ.setdefault("SDL_VIDEODRIVER", "wayland")

        required_flags = sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_EVENTS
        already_initialized = sdl2.SDL_WasInit(required_flags)
        self._sdl_init_flags = required_flags & ~already_initialized
        if self._sdl_init_flags:
            if sdl2.SDL_InitSubSystem(self._sdl_init_flags) != 0:
                raise RuntimeError(f"SDL_InitSubSystem failed: {sdl_error()}")

    @property
    def running(self) -> bool:
        return self._running

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        frame_interval = 1.0 / self.fps
        next_frame = time.monotonic()

        while self._running:
            self.pump()
            self.render()

            next_frame += frame_interval
            delay = next_frame - time.monotonic()
            if delay > 0:
                sdl2.SDL_Delay(int(delay * 1000))
            else:
                next_frame = time.monotonic()

    def run_async(self) -> threading.Thread:
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("DesktopPortal is already running asynchronously")

        self._running = True
        self._thread = threading.Thread(
            target=self.run,
            daemon=True,
        )
        self._thread.start()
        return self._thread

    def pump(self) -> None:
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl2.SDL_QUIT:
                self.stop()
                continue

            if (
                event.type == sdl2.SDL_WINDOWEVENT
                and event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE
            ):
                self.stop()
                continue

            if self.interactive:
                self._handle_interactive_event(event)

    def render(self) -> None:
        frame = self.client.screenshot()
        self._ensure_texture(frame)
        self._update_texture(frame)

        if sdl2.SDL_RenderClear(self._renderer) != 0:
            raise RuntimeError(f"SDL_RenderClear failed: {sdl_error()}")
        if sdl2.SDL_RenderCopy(self._renderer, self._texture, None, None) != 0:
            raise RuntimeError(f"SDL_RenderCopy failed: {sdl_error()}")
        sdl2.SDL_RenderPresent(self._renderer)

    def _ensure_texture(self, frame: Frame) -> None:
        pixel_format = self._sdl_pixel_format(frame)
        texture_spec = (frame.width, frame.height, pixel_format)
        if self._texture_spec == texture_spec:
            return

        if self._texture:
            sdl2.SDL_DestroyTexture(self._texture)

        self._texture = sdl2.SDL_CreateTexture(
            self._renderer,
            pixel_format,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            frame.width,
            frame.height,
        )
        if not self._texture:
            raise RuntimeError(f"SDL_CreateTexture failed: {sdl_error()}")
        self._texture_spec = texture_spec

    def _update_texture(self, frame: Frame) -> None:
        pixels = frame.pixels
        pitch = frame.stride

        if frame.y_invert:
            pixels = b"".join(
                frame.pixels[y * frame.stride : (y + 1) * frame.stride]
                for y in range(frame.height - 1, -1, -1)
            )

        if (
            sdl2.SDL_UpdateTexture(self._texture, None, ctypes.c_char_p(pixels), pitch)
            != 0
        ):
            raise RuntimeError(f"SDL_UpdateTexture failed: {sdl_error()}")

    def _sdl_pixel_format(self, frame: Frame) -> int:
        format_name = getattr(frame.format, "name", str(frame.format)).lower()
        try:
            return FRAME_FORMAT_TO_SDL_PIXEL_FORMAT[format_name]
        except KeyError as exc:
            raise NotImplementedError(
                f"unsupported wl_shm pixel format: {frame.format!r}"
            ) from exc

    def _handle_interactive_event(self, event: sdl2.SDL_Event) -> None:
        if event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
            if event.key.repeat:
                return

            keycode = evdev_keycode_from_sdl_scancode(event.key.keysym.scancode)
            if event.type == sdl2.SDL_KEYDOWN:
                self.client.keycode_down(keycode)
            else:
                self.client.keycode_up(keycode)
            return

        if event.type in (sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP):
            button = SDL_BUTTON_TO_DESKTOP.get(event.button.button)
            if button is None:
                return

            self.client.move_mouse_to(
                self._clamp_x(event.button.x), self._clamp_y(event.button.y)
            )
            if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                self.client.mouse_press(button)
            else:
                self.client.mouse_release(button)
            return

        if event.type == sdl2.SDL_MOUSEMOTION:
            self.client.move_mouse_to(
                self._clamp_x(event.motion.x), self._clamp_y(event.motion.y)
            )

    def _clamp_x(self, x: int) -> int:
        return min(max(x, 0), self.width - 1)

    def _clamp_y(self, y: int) -> int:
        return min(max(y, 0), self.height - 1)

    def close(self) -> None:
        self.stop()

        if (
            self._thread is not None
            and self._thread.is_alive()
            and self._thread is not threading.current_thread()
        ):
            self._thread.join()

        if self._texture:
            sdl2.SDL_DestroyTexture(self._texture)
            self._texture = None
            self._texture_spec = None
        if self._renderer:
            sdl2.SDL_DestroyRenderer(self._renderer)
            self._renderer = None
        if self._window:
            sdl2.SDL_DestroyWindow(self._window)
            self._window = None
        if self._sdl_init_flags:
            sdl2.SDL_QuitSubSystem(self._sdl_init_flags)
            self._sdl_init_flags = 0

    def __enter__(self) -> DesktopPortal:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
