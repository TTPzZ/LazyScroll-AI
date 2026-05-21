import unittest

import numpy as np

from utils.frame_rate import FrameRateLimiter
from utils.preview_frame import resize_preview_frame


class PreviewFrameTests(unittest.TestCase):
    def test_resize_preview_frame_uses_requested_dimensions(self):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        resized = resize_preview_frame(frame, width=640, height=480)

        self.assertEqual(resized.shape, (480, 640, 3))

    def test_resize_preview_frame_returns_original_when_dimensions_are_missing(self):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        resized = resize_preview_frame(frame, width=0, height=480)

        self.assertIs(resized, frame)


class FrameRateLimiterTests(unittest.TestCase):
    def test_wait_sleeps_when_frame_arrives_before_limit(self):
        times = [0, 10, 33]
        sleeps = []

        limiter = FrameRateLimiter(
            fps_limit=30,
            time_provider=lambda: times.pop(0),
            sleep_fn=sleeps.append,
        )

        limiter.wait()
        limiter.wait()

        self.assertAlmostEqual(sleeps, [23.333333333333336])

    def test_wait_does_not_sleep_when_limiter_is_disabled(self):
        sleeps = []
        limiter = FrameRateLimiter(
            fps_limit=0,
            time_provider=lambda: 0,
            sleep_fn=sleeps.append,
        )

        limiter.wait()
        limiter.wait()

        self.assertEqual(sleeps, [])


if __name__ == "__main__":
    unittest.main()
