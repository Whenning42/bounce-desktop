# Check that WaylandDesktop's `visible` argument draws a visible but non-interactive
# window on the screen.

import time

from bounce_desktop import WaylandDesktop

app = "/home/william/Games/factorio/bin/x64/factorio"
desktop = WaylandDesktop(app, (1000, 600), visible=True)

time.sleep(60)
