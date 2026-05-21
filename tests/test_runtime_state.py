import threading
import unittest

from control.runtime_state import RuntimeState
from control.scroll_constants import ACTION_SCROLL_DOWN, DIRECTION_DOWN
from vision.gaze_detector import DOUBLE_BLINK


class RuntimeStateTests(unittest.TestCase):
    def test_snapshot_returns_locked_copy_of_state(self):
        state = RuntimeState()

        state.update(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="fast",
            last_gesture=DOUBLE_BLINK,
            last_action=ACTION_SCROLL_DOWN,
        )
        snapshot = state.snapshot()

        self.assertTrue(snapshot.enabled)
        self.assertTrue(snapshot.auto_scroll)
        self.assertEqual(snapshot.direction, DIRECTION_DOWN)
        self.assertEqual(snapshot.speed_preset, "fast")
        self.assertEqual(snapshot.last_gesture, DOUBLE_BLINK)
        self.assertEqual(snapshot.last_action, ACTION_SCROLL_DOWN)

    def test_updates_are_thread_safe(self):
        state = RuntimeState()

        def update_state(index):
            state.update(
                enabled=bool(index % 2),
                speed_preset=f"preset-{index}",
            )

        threads = [
            threading.Thread(target=update_state, args=(index,))
            for index in range(25)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=1.0)

        snapshot = state.snapshot()

        self.assertIn(snapshot.speed_preset, {f"preset-{index}" for index in range(25)})


if __name__ == "__main__":
    unittest.main()
