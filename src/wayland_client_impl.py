import wayland
from wayland.client import wayland_class

from frame import Frame


@wayland_class("wl_output")
class _Output(wayland.wl_output):
    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0

    def on_mode(self, flags, width, height, refresh):
        # Bit 0x1 of flags indicates the current mode.
        if flags & wayland.wl_output.mode.current:
            self.width = width
            self.height = height


@wayland_class("wl_registry")
class _Registry(wayland.wl_registry):
    NEEDED = (
        "wl_shm",
        "wl_output",
        "wl_seat",
        "zwlr_screencopy_manager_v1",
        "zwlr_virtual_pointer_manager_v1",
        "zwp_virtual_keyboard_manager_v1",
    )

    def __init__(self):
        super().__init__()
        for name in self.NEEDED:
            setattr(self, name, None)

    def on_global(self, name, interface, version):
        if interface in self.NEEDED and getattr(self, interface) is None:
            setattr(self, interface, self.bind(name, interface, version))


@wayland_class("zwlr_screencopy_frame_v1")
class _ScreencopyFrame(wayland.zwlr_screencopy_frame_v1):
    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0
        self.stride = 0
        self.format = None
        self.y_invert = False
        self.buffer_announced = False
        self.ready = False
        self.failed = False

    def on_buffer(self, format, width, height, stride):
        self.format = wayland.wl_shm.format(format)
        self.width = width
        self.height = height
        self.stride = stride

    def on_linux_dmabuf(self, format, width, height):
        pass

    def on_buffer_done(self):
        self.buffer_announced = True

    def on_flags(self, flags):
        self.y_invert = bool(flags & 1)

    def on_ready(self, tv_sec_hi, tv_sec_lo, tv_nsec):
        self.ready = True

    def on_failed(self):
        self.failed = True


def take_screenshot(registry, display, shm_pool):
    scpy_frame: wayland.zwlr_screencopy_frame_v1 = (
        registry.zwlr_screencopy_manager_v1.capture_output(0, registry.wl_output)
    )
    while not scpy_frame.buffer_announced and not scpy_frame.failed:
        display.dispatch_timeout(0.2)
    if scpy_frame.failed:
        raise RuntimeError("screencopy failed before buffer announce")

    buf, ptr = shm_pool.create_buffer(
        scpy_frame.width, scpy_frame.height, pixel_format=scpy_frame.format
    )
    if buf is None:
        raise RuntimeError(f"could not allocate buffer for {scpy_frame.format!r}")

    scpy_frame.copy(buf)
    while not (scpy_frame.ready or scpy_frame.failed):
        display.dispatch_timeout(0.2)
    if scpy_frame.failed:
        raise RuntimeError("screencopy failed during copy")

    return Frame(
        pixels=bytes(ptr[: scpy_frame.stride * scpy_frame.height]),
        width=scpy_frame.width,
        height=scpy_frame.height,
        stride=scpy_frame.stride,
        format=scpy_frame.format,
        y_invert=scpy_frame.y_invert,
    )
