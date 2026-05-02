from __future__ import annotations

import mmap
import select
import tempfile
from dataclasses import dataclass

from bounce_desktop.frame import Frame
from bounce_desktop.wayland_protocols_generate import ensure_wayland_protocols

from pywayland.client import Display

ensure_wayland_protocols()

from bounce_desktop.wayland_generated_protocols.virtual_keyboard_unstable_v1 import (
    ZwpVirtualKeyboardManagerV1,
)
from bounce_desktop.wayland_generated_protocols.wayland import WlOutput, WlSeat, WlShm
from bounce_desktop.wayland_generated_protocols.wlr_screencopy_unstable_v1 import (
    ZwlrScreencopyFrameV1,
    ZwlrScreencopyManagerV1,
)
from bounce_desktop.wayland_generated_protocols.wlr_virtual_pointer_unstable_v1 import (
    ZwlrVirtualPointerManagerV1,
)


def dispatch_with_timeout(display: Display, timeout: float = 0.2) -> None:
    display.dispatch(block=False)
    display.flush()
    readable, _, _ = select.select([display.get_fd()], [], [], timeout)
    if readable:
        display.dispatch(block=True)


class _Registry:
    _INTERFACES = {
        WlShm.name: WlShm,
        WlOutput.name: WlOutput,
        WlSeat.name: WlSeat,
        ZwlrScreencopyManagerV1.name: ZwlrScreencopyManagerV1,
        ZwlrVirtualPointerManagerV1.name: ZwlrVirtualPointerManagerV1,
        ZwpVirtualKeyboardManagerV1.name: ZwpVirtualKeyboardManagerV1,
    }
    NEEDED = tuple(_INTERFACES)

    def __init__(self, registry_proxy):
        self._registry_proxy = registry_proxy
        self.output_width = 0
        self.output_height = 0
        for name in self.NEEDED:
            setattr(self, name, None)
        registry_proxy.dispatcher["global"] = self._on_global

    def has_required_globals(self) -> bool:
        return all(getattr(self, name) is not None for name in self.NEEDED)

    def has_output_size(self) -> bool:
        return self.output_width > 0 and self.output_height > 0

    def _on_global(self, _registry_proxy, name: int, interface: str, version: int):
        if interface not in self._INTERFACES or getattr(self, interface) is not None:
            return

        interface_class = self._INTERFACES[interface]
        proxy = self._registry_proxy.bind(
            name, interface_class, min(version, interface_class.version)
        )
        setattr(self, interface, proxy)

        if interface == WlOutput.name:
            proxy.dispatcher["mode"] = self._on_output_mode

    def _on_output_mode(self, _output_proxy, flags, width, height, _refresh):
        if flags & WlOutput.mode.current:
            self.output_width = width
            self.output_height = height


@dataclass
class _ShmBuffer:
    buffer: object
    pool: object
    mapped_file: mmap.mmap
    file: object
    size: int

    @classmethod
    def create(cls, shm, width: int, height: int, stride: int, pixel_format):
        size = stride * height
        file = tempfile.TemporaryFile(prefix="ez-desk-screenshot-")
        file.truncate(size)
        mapped_file = mmap.mmap(file.fileno(), size, access=mmap.ACCESS_WRITE)
        pool = shm.create_pool(file.fileno(), size)
        buffer = pool.create_buffer(0, width, height, stride, int(pixel_format))
        return cls(buffer, pool, mapped_file, file, size)

    def close(self) -> None:
        if self.buffer is not None:
            self.buffer.destroy()
            self.buffer = None
        if self.pool is not None:
            self.pool.destroy()
            self.pool = None
        self.mapped_file.close()
        self.file.close()


class _ScreencopyState:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.stride = 0
        self.format = None
        self.y_invert = False
        self.buffer_announced = False
        self.ready = False
        self.failed = False

    def attach(self, frame) -> None:
        frame.dispatcher["buffer"] = self._on_buffer
        frame.dispatcher["linux_dmabuf"] = self._on_linux_dmabuf
        frame.dispatcher["buffer_done"] = self._on_buffer_done
        frame.dispatcher["flags"] = self._on_flags
        frame.dispatcher["ready"] = self._on_ready
        frame.dispatcher["failed"] = self._on_failed

    def _on_buffer(self, _frame, format, width, height, stride):
        self.format = WlShm.format(format)
        self.width = width
        self.height = height
        self.stride = stride

    def _on_linux_dmabuf(self, _frame, _format, _width, _height):
        pass

    def _on_buffer_done(self, _frame):
        self.buffer_announced = True

    def _on_flags(self, _frame, flags):
        self.y_invert = bool(flags & ZwlrScreencopyFrameV1.flags.y_invert)

    def _on_ready(self, _frame, _tv_sec_hi, _tv_sec_lo, _tv_nsec):
        self.ready = True

    def _on_failed(self, _frame):
        self.failed = True


def take_screenshot(registry: _Registry, display: Display) -> Frame:
    scpy_frame = registry.zwlr_screencopy_manager_v1.capture_output(
        1, registry.wl_output
    )
    state = _ScreencopyState()
    state.attach(scpy_frame)

    while not state.buffer_announced and not state.failed:
        dispatch_with_timeout(display)
    if state.failed:
        scpy_frame.destroy()
        raise RuntimeError("screencopy failed before buffer announce")

    shm_buffer = _ShmBuffer.create(
        registry.wl_shm, state.width, state.height, state.stride, state.format
    )
    try:
        scpy_frame.copy(shm_buffer.buffer)
        while not (state.ready or state.failed):
            dispatch_with_timeout(display)
        if state.failed:
            raise RuntimeError("screencopy failed during copy")

        return Frame(
            pixels=bytes(shm_buffer.mapped_file[: shm_buffer.size]),
            width=state.width,
            height=state.height,
            stride=state.stride,
            format=state.format,
            y_invert=state.y_invert,
        )
    finally:
        scpy_frame.destroy()
        shm_buffer.close()
