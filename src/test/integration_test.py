import subprocess

import bounce_desktop

d = bounce_desktop.Desktop.create(640, 480, True)
p = subprocess.Popen(["xeyes"], env=d.get_desktop_env())
p.wait()
