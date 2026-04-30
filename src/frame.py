from dataclasses import dataclass


@dataclass
class Frame:
    pixels: bytes
    width: int
    height: int
    stride: int
    format: object  # wayland.wl_shm.format enum
    y_invert: bool

    def get_pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        if not 0 <= x < self.width or not 0 <= y < self.height:
            raise IndexError(f"pixel coordinate ({x}, {y}) is outside the frame")

        if self.y_invert:
            y = self.height - y - 1

        offset = y * self.stride + x * 4
        b0, b1, b2, b3 = self.pixels[offset : offset + 4]
        format_name = getattr(self.format, "name", str(self.format))

        if format_name == "argb8888":
            return (b2, b1, b0, b3)
        if format_name == "xrgb8888":
            return (b2, b1, b0, 255)
        if format_name == "abgr8888":
            return (b0, b1, b2, b3)
        if format_name == "xbgr8888":
            return (b0, b1, b2, 255)

        raise NotImplementedError(f"unsupported wl_shm pixel format: {self.format!r}")
