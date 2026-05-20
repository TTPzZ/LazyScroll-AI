import unittest

from vision.gaze_detector import (
    DOUBLE_BLINK,
    LONG_BLINK,
    NO_GESTURE,
    SINGLE_BLINK,
    BlinkGestureDetector,
)


class BlinkGestureDetectorTests(unittest.TestCase):
    def test_returns_no_gesture_while_eye_stays_open(self):
        detector = BlinkGestureDetector(closed_threshold=0.18)

        gesture, closed = detector.update(0.25, timestamp_ms=1000)

        self.assertEqual(gesture, NO_GESTURE)
        self.assertFalse(closed)

    def test_single_blink_emits_only_after_confirmation_delay(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            double_blink_window_ms=800,
        )

        detector.update(0.25, timestamp_ms=1000)
        closed_gesture, closed = detector.update(0.08, timestamp_ms=1040)
        held_gesture, held_closed = detector.update(0.07, timestamp_ms=1080)
        reopen_gesture, reopened_closed = detector.update(0.24, timestamp_ms=1120)
        before_confirm_gesture, before_confirm_closed = detector.update(0.25, timestamp_ms=1919)
        confirmed_gesture, confirmed_closed = detector.update(0.25, timestamp_ms=1921)
        repeated_gesture, repeated_closed = detector.update(0.25, timestamp_ms=2000)

        self.assertEqual(closed_gesture, NO_GESTURE)
        self.assertTrue(closed)
        self.assertEqual(held_gesture, NO_GESTURE)
        self.assertTrue(held_closed)
        self.assertEqual(reopen_gesture, NO_GESTURE)
        self.assertFalse(reopened_closed)
        self.assertEqual(before_confirm_gesture, NO_GESTURE)
        self.assertFalse(before_confirm_closed)
        self.assertEqual(confirmed_gesture, SINGLE_BLINK)
        self.assertFalse(confirmed_closed)
        self.assertEqual(repeated_gesture, NO_GESTURE)
        self.assertFalse(repeated_closed)

    def test_double_blink_emits_double_blink_only(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            double_blink_window_ms=800,
        )

        gestures = []
        gestures.append(detector.update(0.25, timestamp_ms=1000)[0])
        gestures.append(detector.update(0.08, timestamp_ms=1040)[0])
        first_gesture, _ = detector.update(0.25, timestamp_ms=1100)
        gestures.append(first_gesture)
        gestures.append(detector.update(0.07, timestamp_ms=1300)[0])
        second_gesture, _ = detector.update(0.25, timestamp_ms=1360)
        gestures.append(second_gesture)
        gestures.append(detector.update(0.25, timestamp_ms=2200)[0])

        self.assertEqual(first_gesture, NO_GESTURE)
        self.assertEqual(second_gesture, DOUBLE_BLINK)
        self.assertNotIn(SINGLE_BLINK, gestures)
        self.assertEqual(gestures.count(DOUBLE_BLINK), 1)

    def test_long_blink_emits_long_blink_only(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            long_blink_ms=700,
        )

        gestures = []
        gestures.append(detector.update(0.25, timestamp_ms=1000)[0])
        gestures.append(detector.update(0.08, timestamp_ms=1100)[0])
        early_gesture, early_closed = detector.update(0.07, timestamp_ms=1700)
        gestures.append(early_gesture)
        long_gesture, long_closed = detector.update(0.07, timestamp_ms=1800)
        gestures.append(long_gesture)
        repeated_gesture, repeated_closed = detector.update(0.07, timestamp_ms=1900)
        gestures.append(repeated_gesture)
        reopened_gesture, reopened_closed = detector.update(0.25, timestamp_ms=2000)
        gestures.append(reopened_gesture)
        gestures.append(detector.update(0.25, timestamp_ms=2900)[0])

        self.assertEqual(early_gesture, NO_GESTURE)
        self.assertTrue(early_closed)
        self.assertEqual(long_gesture, LONG_BLINK)
        self.assertTrue(long_closed)
        self.assertEqual(repeated_gesture, NO_GESTURE)
        self.assertTrue(repeated_closed)
        self.assertEqual(reopened_gesture, NO_GESTURE)
        self.assertFalse(reopened_closed)
        self.assertNotIn(SINGLE_BLINK, gestures)
        self.assertEqual(gestures.count(LONG_BLINK), 1)

    def test_missing_eye_open_breaks_blink_transition(self):
        detector = BlinkGestureDetector(closed_threshold=0.18)

        detector.update(0.25, timestamp_ms=1000)
        detector.update(0.08, timestamp_ms=1040)
        missing_gesture, missing_closed = detector.update(None, timestamp_ms=1080)
        reopened_gesture, reopened_closed = detector.update(0.25, timestamp_ms=1120)

        self.assertEqual(missing_gesture, NO_GESTURE)
        self.assertFalse(missing_closed)
        self.assertEqual(reopened_gesture, NO_GESTURE)
        self.assertFalse(reopened_closed)


if __name__ == "__main__":
    unittest.main()
