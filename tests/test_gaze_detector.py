import unittest

from vision.gaze_detector import (
    DOUBLE_BLINK,
    LONG_BLINK,
    NO_GESTURE,
    SINGLE_BLINK,
    TRIPLE_BLINK,
    BlinkGestureDetector,
)


class BlinkGestureDetectorTests(unittest.TestCase):
    def test_returns_no_gesture_while_eye_stays_open(self):
        detector = BlinkGestureDetector(closed_threshold=0.18)

        gesture, closed = detector.update(0.25, timestamp_ms=1000)

        self.assertEqual(gesture, NO_GESTURE)
        self.assertFalse(closed)

    def test_single_blink_emits_immediately_after_open_transition(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            multi_blink_window_ms=800,
        )

        detector.update(0.25, timestamp_ms=1000)
        closed_gesture, closed = detector.update(0.08, timestamp_ms=1040)
        held_gesture, held_closed = detector.update(0.07, timestamp_ms=1080)
        reopen_gesture, reopened_closed = detector.update(0.24, timestamp_ms=1120)
        repeated_gesture, repeated_closed = detector.update(0.25, timestamp_ms=1200)

        self.assertEqual(closed_gesture, NO_GESTURE)
        self.assertTrue(closed)
        self.assertEqual(held_gesture, NO_GESTURE)
        self.assertTrue(held_closed)
        self.assertEqual(reopen_gesture, SINGLE_BLINK)
        self.assertFalse(reopened_closed)
        self.assertEqual(repeated_gesture, NO_GESTURE)
        self.assertFalse(repeated_closed)

    def test_double_blink_emits_single_then_double_within_window(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            multi_blink_window_ms=800,
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

        self.assertEqual(first_gesture, SINGLE_BLINK)
        self.assertEqual(second_gesture, DOUBLE_BLINK)
        self.assertEqual(gestures.count(SINGLE_BLINK), 1)
        self.assertEqual(gestures.count(DOUBLE_BLINK), 1)

    def test_triple_blink_emits_single_double_then_triple_within_window(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            multi_blink_window_ms=800,
        )

        detector.update(0.25, timestamp_ms=1000)
        detector.update(0.08, timestamp_ms=1040)
        first_gesture, _ = detector.update(0.25, timestamp_ms=1100)
        detector.update(0.08, timestamp_ms=1260)
        second_gesture, _ = detector.update(0.25, timestamp_ms=1320)
        detector.update(0.08, timestamp_ms=1480)
        third_gesture, third_closed = detector.update(0.25, timestamp_ms=1540)
        next_gesture, _ = detector.update(0.25, timestamp_ms=1600)

        self.assertEqual(first_gesture, SINGLE_BLINK)
        self.assertEqual(second_gesture, DOUBLE_BLINK)
        self.assertEqual(third_gesture, TRIPLE_BLINK)
        self.assertFalse(third_closed)
        self.assertEqual(next_gesture, NO_GESTURE)

    def test_second_blink_after_window_starts_new_single_blink_sequence(self):
        detector = BlinkGestureDetector(
            closed_threshold=0.18,
            multi_blink_window_ms=800,
        )

        detector.update(0.25, timestamp_ms=1000)
        detector.update(0.08, timestamp_ms=1040)
        first_gesture, _ = detector.update(0.25, timestamp_ms=1100)
        detector.update(0.08, timestamp_ms=2000)
        second_gesture, _ = detector.update(0.25, timestamp_ms=2060)

        self.assertEqual(first_gesture, SINGLE_BLINK)
        self.assertEqual(second_gesture, SINGLE_BLINK)

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
        self.assertNotIn(DOUBLE_BLINK, gestures)
        self.assertNotIn(TRIPLE_BLINK, gestures)
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
