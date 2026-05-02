# Verify that Desktop.get_frame() is thread safe by connecting multiple
# DesktopPortals to a single desktop.

import time

from bounce_desktop import WaylandDesktop
from bounce_desktop.launch_portal import launch_portal

app = "/home/william/Games/factorio/bin/x64/factorio"
desktop = WaylandDesktop(app, (1000, 600))
resolution = desktop.get_resolution()
wayland_display = desktop.server.display_string()

portal_0 = launch_portal(wayland_display, resolution, title="Portal 0")
portal_1 = launch_portal(wayland_display, resolution, title="Portal 1")

try:
    while True:
        time.sleep(10)
finally:
    portal_0.close()
    portal_1.close()
