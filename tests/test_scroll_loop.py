import threading
import unittest

from control.scroll_loop import run_scroll_loop


class FakeScrollEngine:
    def __init__(self, stop_event, stop_after_updates=3):
        self.stop_event = stop_event
        self.stop_after_updates = stop_after_updates
        self.update_calls = 0

    def update(self):
        self.update_calls += 1
        if self.update_calls >= self.stop_after_updates:
            self.stop_event.set()


class ScrollLoopTests(unittest.TestCase):
    def test_scroll_loop_runs_until_stop_event_is_set(self):
        stop_event = threading.Event()
        scroll_engine = FakeScrollEngine(stop_event)
        sleep_calls = []

        run_scroll_loop(
            scroll_engine,
            stop_event,
            sleep_interval_s=0.01,
            sleep_fn=sleep_calls.append,
        )

        self.assertEqual(scroll_engine.update_calls, 3)
        self.assertEqual(sleep_calls, [0.01, 0.01, 0.01])

    def test_scroll_loop_does_not_update_after_already_stopped(self):
        stop_event = threading.Event()
        stop_event.set()
        scroll_engine = FakeScrollEngine(stop_event)

        run_scroll_loop(
            scroll_engine,
            stop_event,
            sleep_fn=lambda _: None,
        )

        self.assertEqual(scroll_engine.update_calls, 0)


if __name__ == "__main__":
    unittest.main()
