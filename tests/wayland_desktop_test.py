# TODO(whenning):
# - Clean up race conditions in test app startup.
# - Identify source of flakey dropped events?


import unittest
import tempfile
from bounce_desktop import WaylandDesktop
import numpy as np
from pathlib import Path
import shlex
import sys
import time


def _make_log_lines_absolute(expected_log_lines: list[str]) -> list[str]:
    expected_log_lines = expected_log_lines.copy()
    last_mouse_x = None
    last_mouse_y = None
    for i in range(len(expected_log_lines)):
        line = expected_log_lines[i].split(" ")
        if line[0] == "move_mouse_to":
            last_mouse_x = int(line[1])
            last_mouse_y = int(line[2])
        if line[0] == "move_mouse":
            assert last_mouse_x is not None and last_mouse_y is not None
            _, dx, dy = line
            last_mouse_x += int(dx)
            last_mouse_y += int(dy)
            expected_log_lines[i] = " ".join(
                ("move_mouse_to", str(last_mouse_x), str(last_mouse_y))
            )
    return expected_log_lines


def _test_app_command(log_path: Path) -> str:
    return (
        f"{shlex.quote(sys.executable)} -m bounce_desktop.test_app --log_to={log_path}"
    )


class TestWaylandDesktop(unittest.TestCase):
    # Prevent race conditions on test_app startup, by polling
    # for test app to appear reday before continuing with our tests.
    def wait_for_test_app(self, desktop: WaylandDesktop) -> None:
        start = time.time()
        while time.time() - start < 3:
            frame = desktop.get_frame()
            if (
                tuple(frame[0, 0]) == (0, 0, 0, 255)
                and tuple(frame[0, 100]) == (255, 0, 0, 255)
                and tuple(frame[100, 0]) == (0, 255, 0, 255)
                and tuple(frame[100, 100]) == (0, 0, 255, 255)
            ):
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for test app to draw its test pattern")

    def expect_sequence(self, desktop: WaylandDesktop, test_seq: list, log_path: Path):
        for c in test_seq:
            fn_name, *args = c
            getattr(desktop, fn_name)(*args)
            time.sleep(0.01)

        expected_log_lines = [" ".join(map(str, c)) for c in test_seq]
        actual_log_lines = []

        start = time.time()
        while time.time() - start < 2:
            actual_log_lines = log_path.read_text(encoding="utf-8").splitlines()
            if actual_log_lines == expected_log_lines:
                break
            time.sleep(0.01)

        expected_log_lines = _make_log_lines_absolute(expected_log_lines)
        self.assertEqual(expected_log_lines, actual_log_lines)

    def test_desktop(self):
        with tempfile.TemporaryDirectory(prefix="bounce-desk-unittest") as tmpdir:
            log_path = Path(tmpdir) / "events.log"
            log_path.touch()
            RESOLUTION = (640, 480)
            desktop = WaylandDesktop(_test_app_command(log_path), RESOLUTION)
            self.wait_for_test_app(desktop)

            test_seq = [
                ("move_mouse_to", 20, 10),
                ("move_mouse", 5, 2),
                ("mouse_press", 1),
                ("mouse_press", 2),
                ("mouse_release", 1),
                ("mouse_release", 2),
                ("keycode_down", 17),
                ("keycode_down", 30),
                ("keycode_down", 31),
                ("keycode_up", 17),
                ("keycode_up", 30),
                ("keycode_up", 31),
            ]
            self.expect_sequence(desktop, test_seq, log_path)

            frame = desktop.get_frame()
            self.assertEqual(frame.dtype, np.uint8)
            self.assertEqual(frame.shape, (RESOLUTION[1], RESOLUTION[0], 4))
            np.testing.assert_array_equal(frame[0, 0], (0, 0, 0, 255))
            np.testing.assert_array_equal(frame[0, 100], (255, 0, 0, 255))
            np.testing.assert_array_equal(frame[100, 0], (0, 255, 0, 255))
            np.testing.assert_array_equal(frame[100, 100], (0, 0, 255, 255))

            del desktop

    def test_concurrent_desktops(self):
        with tempfile.TemporaryDirectory(prefix="bounce-desk-unittest") as tmpdir:
            log_path_0 = Path(tmpdir) / "events_0.log"
            log_path_1 = Path(tmpdir) / "events_1.log"
            log_path_0.touch()
            log_path_1.touch()
            RESOLUTION = (640, 480)
            desktop_0 = WaylandDesktop(_test_app_command(log_path_0), RESOLUTION)
            desktop_1 = WaylandDesktop(_test_app_command(log_path_1), RESOLUTION)
            self.wait_for_test_app(desktop_0)
            self.wait_for_test_app(desktop_1)

            test_seq_0 = [
                ("move_mouse_to", 20, 10),
                ("move_mouse", 5, 2),
                ("keycode_down", 17),
                ("keycode_up", 17),
            ]
            test_seq_1 = [
                ("move_mouse_to", 40, 20),
                ("move_mouse", 10, 5),
                ("keycode_down", 30),
                ("keycode_up", 30),
            ]
            self.expect_sequence(desktop_0, test_seq_0, log_path_0)
            self.expect_sequence(desktop_1, test_seq_1, log_path_1)

            del desktop_0
            del desktop_1


if __name__ == "__main__":
    unittest.main()
