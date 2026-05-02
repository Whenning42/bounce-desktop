# Bounce Desktop

Bounce desktop is a Python library for running subprocesses in hardware accelerated virtual desktops and for interacting with those desktops. It's built to provide isolated desktops for compute-use agents as a part of my [BounceRL](https://github.com/Whenning42/bounce-rl) project.

## Getting Started

Install the `bounce_desktop` package, then use the desktop as:

```python
from bounce_desktop import WaylandDesktop

desktop = WaylandDesktop("/path/to/my/app", resolution=(640, 480), visible=False)

# Wait for desktop to be ready. Desktop.get_frame() throws RuntimeErrors
# if you call it before the compositor is ready.
...

desktop.move_mouse_to(200, 200)
desktop.mouse_press(button=1)
desktop.mouse_release(button=1)
...
```

The `Desktop` interface is described in [desktopy.py](src/bounce_desktop/desktop.py) and the constructor for `WaylandDesktop` is documented in [wayland_desktop.py](src/bounce_desktop/wayland_desktop.py)

## System Dependencies

This package depends on `labwc` and `wlr-randr`.
