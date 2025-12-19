from bounce_desktop import Desktop
import subprocess
import time
import numpy as np

d = Desktop.create(1000, 600)
p = subprocess.Popen(["/home/william/Games/factorio/bin/x64/factorio"], env=d.get_desktop_env())

time.sleep(4)
f = d.get_frame()

pixel_val = f[377, 280]
expected = np.array([255, 158, 26, 255])
if not (pixel_val==expected).all():
    print(f"Test failed. Expected: {expected}, but got {pixel_val}")
else:
    print("Test passed!")
