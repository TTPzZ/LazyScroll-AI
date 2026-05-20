from types import SimpleNamespace
import unittest

import numpy as np

from vision.iris_tracker import IrisTracker


def landmark(x=0.0, y=0.0):
    return SimpleNamespace(x=x, y=y)


def landmark_list(size=478):
    return [landmark() for _ in range(size)]


class IrisTrackerTests(unittest.TestCase):
    def test_extracts_eye_and_iris_y_ratios_from_facelandmarker_output(self):
        landmarks = landmark_list()
        for index in IrisTracker.RIGHT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.30)
        for index in IrisTracker.RIGHT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.70)
        for index in IrisTracker.RIGHT_IRIS_INDICES:
            landmarks[index] = landmark(y=0.50)

        for index in IrisTracker.LEFT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.10)
        for index in IrisTracker.LEFT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.50)
        for index in IrisTracker.LEFT_IRIS_INDICES:
            landmarks[index] = landmark(y=0.30)

        ratios = IrisTracker().calculate([landmarks])

        self.assertAlmostEqual(ratios["right_eye_y_ratio"], 0.5)
        self.assertAlmostEqual(ratios["left_eye_y_ratio"], 0.5)
        self.assertAlmostEqual(ratios["average_y_ratio"], 0.5)

    def test_returns_none_ratios_when_no_face_landmarks_are_available(self):
        ratios = IrisTracker().calculate([])

        self.assertEqual(
            ratios,
            {
                "left_eye_y_ratio": None,
                "right_eye_y_ratio": None,
                "average_y_ratio": None,
            },
        )

    def test_returns_none_for_eye_when_required_landmarks_are_missing(self):
        ratios = IrisTracker().calculate([landmark_list(size=100)])

        self.assertEqual(ratios["left_eye_y_ratio"], None)
        self.assertEqual(ratios["right_eye_y_ratio"], None)
        self.assertEqual(ratios["average_y_ratio"], None)

    def test_average_uses_available_eye_ratio_when_only_one_eye_is_available(self):
        landmarks = landmark_list(size=478)
        for index in IrisTracker.RIGHT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.10)
        for index in IrisTracker.RIGHT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.50)
        for index in IrisTracker.RIGHT_IRIS_INDICES:
            landmarks[index] = landmark(y=0.30)

        ratios = IrisTracker().calculate([landmarks])

        self.assertEqual(ratios["left_eye_y_ratio"], None)
        self.assertAlmostEqual(ratios["right_eye_y_ratio"], 0.5)
        self.assertAlmostEqual(ratios["average_y_ratio"], 0.5)

    def test_eyelid_ratio_uses_reference_lids_instead_of_eye_contour_extremes(self):
        landmarks = landmark_list(size=478)
        for index in IrisTracker.RIGHT_EYE_INDICES:
            landmarks[index] = landmark(y=0.95)
        for index in IrisTracker.RIGHT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.30)
        for index in IrisTracker.RIGHT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.70)
        for index in IrisTracker.RIGHT_IRIS_INDICES:
            landmarks[index] = landmark(y=0.54)

        ratios = IrisTracker().calculate([landmarks])

        self.assertAlmostEqual(ratios["right_eye_y_ratio"], 0.6)
        self.assertAlmostEqual(ratios["average_y_ratio"], 0.6)

    def test_debug_drawing_marks_iris_and_eyelid_reference_points(self):
        landmarks = landmark_list(size=478)
        for index in IrisTracker.RIGHT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(x=0.50, y=0.30)
        for index in IrisTracker.RIGHT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(x=0.50, y=0.70)
        for index in IrisTracker.RIGHT_IRIS_INDICES:
            landmarks[index] = landmark(x=0.50, y=0.50)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        IrisTracker().draw_debug_references(frame, [landmarks])

        self.assertGreater(int(frame.sum()), 0)

    def test_extracts_debug_calibration_feature_vector(self):
        landmarks = [landmark(y=0.50) for _ in range(478)]
        for index in IrisTracker.RIGHT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.30)
        for index in IrisTracker.RIGHT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.70)
        for index in IrisTracker.RIGHT_IRIS_INDICES:
            landmarks[index] = landmark(y=0.50)

        for index in IrisTracker.LEFT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.20)
        for index in IrisTracker.LEFT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.60)
        for index in IrisTracker.LEFT_IRIS_INDICES:
            landmarks[index] = landmark(y=0.40)

        landmarks[10] = landmark(y=0.10)
        landmarks[152] = landmark(y=0.90)

        features = IrisTracker().extract_features([landmarks])

        self.assertAlmostEqual(features["average_y_ratio"], 0.5)
        self.assertAlmostEqual(features["average_iris_y"], 0.45)
        self.assertAlmostEqual(features["average_eye_center_y"], 0.45)
        self.assertAlmostEqual(features["face_center_y"], 0.5)
        self.assertEqual(len(features["feature_vector"]), 4)
        for actual, expected in zip(features["feature_vector"], (0.5, 0.45, 0.45, 0.5)):
            self.assertAlmostEqual(actual, expected)

    def test_extracts_eye_openness_from_lid_distance_normalized_by_eye_width(self):
        landmarks = landmark_list(size=478)

        for index in IrisTracker.RIGHT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.30)
        for index in IrisTracker.RIGHT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.40)
        landmarks[33] = landmark(x=0.20, y=0.35)
        landmarks[133] = landmark(x=0.70, y=0.35)

        for index in IrisTracker.LEFT_UPPER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.20)
        for index in IrisTracker.LEFT_LOWER_EYELID_INDICES:
            landmarks[index] = landmark(y=0.35)
        landmarks[362] = landmark(x=0.10, y=0.28)
        landmarks[263] = landmark(x=0.60, y=0.28)

        features = IrisTracker().extract_features([landmarks])

        self.assertAlmostEqual(features["right_eye_openness"], 0.20)
        self.assertAlmostEqual(features["left_eye_openness"], 0.30)
        self.assertAlmostEqual(features["average_eye_openness"], 0.25)

    def test_extract_features_returns_missing_vector_when_no_face_exists(self):
        features = IrisTracker().extract_features([])

        self.assertIsNone(features["feature_vector"])
        self.assertIsNone(features["average_y_ratio"])
        self.assertIsNone(features["average_eye_openness"])


if __name__ == "__main__":
    unittest.main()
