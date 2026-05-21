import unittest

from vision.blink_calibration import BlinkCalibrator


class BlinkCalibratorTests(unittest.TestCase):
    def test_computes_threshold_between_open_and_closed_averages(self):
        calibrator = BlinkCalibrator(sample_duration_ms=1000, min_samples=2)

        start_action = calibrator.start(timestamp_ms=0)
        calibrator.update(0.30, timestamp_ms=0)
        calibrator.update(0.34, timestamp_ms=500)
        transition_result = calibrator.update(0.32, timestamp_ms=1000)
        calibrator.update(0.10, timestamp_ms=1100)
        calibrator.update(0.14, timestamp_ms=1500)
        result = calibrator.update(0.12, timestamp_ms=2000)

        self.assertEqual(start_action, "CALIBRATION_STARTED")
        self.assertIsNone(transition_result)
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.open_average, 0.32)
        self.assertAlmostEqual(result.closed_average, 0.12)
        self.assertAlmostEqual(result.closed_threshold, 0.22)
        self.assertFalse(calibrator.running)

    def test_fails_when_samples_do_not_separate_open_and_closed(self):
        calibrator = BlinkCalibrator(sample_duration_ms=1000, min_samples=2)

        calibrator.start(timestamp_ms=0)
        calibrator.update(0.20, timestamp_ms=0)
        calibrator.update(0.21, timestamp_ms=500)
        calibrator.update(0.20, timestamp_ms=1000)
        calibrator.update(0.24, timestamp_ms=1100)
        calibrator.update(0.25, timestamp_ms=1500)
        result = calibrator.update(0.24, timestamp_ms=2000)

        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertIsNone(result.closed_threshold)
        self.assertIn("failed", calibrator.status.lower())

    def test_fails_safely_when_not_enough_samples_are_available(self):
        calibrator = BlinkCalibrator(sample_duration_ms=1000, min_samples=2)

        calibrator.start(timestamp_ms=0)
        result = calibrator.update(None, timestamp_ms=1000)

        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertIsNone(result.closed_threshold)
        self.assertFalse(calibrator.running)


if __name__ == "__main__":
    unittest.main()
