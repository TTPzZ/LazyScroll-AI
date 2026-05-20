import math
from typing import Any

import cv2


class IrisTracker:
    """Calculates iris vertical position ratios from FaceLandmarker output."""

    RIGHT_EYE_INDICES = (33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246)
    LEFT_EYE_INDICES = (263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466)
    RIGHT_UPPER_EYELID_INDICES = (159, 158, 160)
    RIGHT_LOWER_EYELID_INDICES = (145, 144, 153)
    LEFT_UPPER_EYELID_INDICES = (386, 385, 387)
    LEFT_LOWER_EYELID_INDICES = (374, 373, 380)
    RIGHT_EYE_CORNER_INDICES = (33, 133)
    LEFT_EYE_CORNER_INDICES = (362, 263)
    RIGHT_IRIS_INDICES = (469, 470, 471, 472)
    LEFT_IRIS_INDICES = (474, 475, 476, 477)

    def calculate(self, face_landmarks: list[Any]) -> dict[str, float | None]:
        if not face_landmarks:
            return self._empty_result()

        landmarks = face_landmarks[0]
        left_ratio = self._eye_y_ratio(
            landmarks=landmarks,
            upper_eyelid_indices=self.LEFT_UPPER_EYELID_INDICES,
            lower_eyelid_indices=self.LEFT_LOWER_EYELID_INDICES,
            iris_indices=self.LEFT_IRIS_INDICES,
        )
        right_ratio = self._eye_y_ratio(
            landmarks=landmarks,
            upper_eyelid_indices=self.RIGHT_UPPER_EYELID_INDICES,
            lower_eyelid_indices=self.RIGHT_LOWER_EYELID_INDICES,
            iris_indices=self.RIGHT_IRIS_INDICES,
        )
        available_ratios = [
            ratio for ratio in (left_ratio, right_ratio) if ratio is not None
        ]
        average_ratio = (
            sum(available_ratios) / len(available_ratios)
            if available_ratios
            else None
        )

        return {
            "left_eye_y_ratio": left_ratio,
            "right_eye_y_ratio": right_ratio,
            "average_y_ratio": average_ratio,
        }

    def extract_features(self, face_landmarks: list[Any]) -> dict[str, Any]:
        ratios = self.calculate(face_landmarks)
        features: dict[str, Any] = {
            **ratios,
            "left_iris_y": None,
            "right_iris_y": None,
            "average_iris_y": None,
            "left_eye_openness": None,
            "right_eye_openness": None,
            "average_eye_openness": None,
            "left_eye_center_y": None,
            "right_eye_center_y": None,
            "average_eye_center_y": None,
            "face_center_y": None,
            "feature_vector": None,
        }

        if not face_landmarks:
            return features

        landmarks = face_landmarks[0]
        left_iris_y = self._average_y_for_indices(landmarks, self.LEFT_IRIS_INDICES)
        right_iris_y = self._average_y_for_indices(landmarks, self.RIGHT_IRIS_INDICES)
        left_eye_center_y = self._eye_center_y(
            landmarks,
            self.LEFT_UPPER_EYELID_INDICES,
            self.LEFT_LOWER_EYELID_INDICES,
        )
        right_eye_center_y = self._eye_center_y(
            landmarks,
            self.RIGHT_UPPER_EYELID_INDICES,
            self.RIGHT_LOWER_EYELID_INDICES,
        )
        average_iris_y = self._average_available(left_iris_y, right_iris_y)
        average_eye_center_y = self._average_available(
            left_eye_center_y,
            right_eye_center_y,
        )
        left_eye_openness = self._eye_openness(
            landmarks,
            self.LEFT_UPPER_EYELID_INDICES,
            self.LEFT_LOWER_EYELID_INDICES,
            self.LEFT_EYE_CORNER_INDICES,
        )
        right_eye_openness = self._eye_openness(
            landmarks,
            self.RIGHT_UPPER_EYELID_INDICES,
            self.RIGHT_LOWER_EYELID_INDICES,
            self.RIGHT_EYE_CORNER_INDICES,
        )
        average_eye_openness = self._average_available(
            left_eye_openness,
            right_eye_openness,
        )
        face_center_y = self._face_center_y(landmarks)

        features.update(
            {
                "left_iris_y": left_iris_y,
                "right_iris_y": right_iris_y,
                "average_iris_y": average_iris_y,
                "left_eye_openness": left_eye_openness,
                "right_eye_openness": right_eye_openness,
                "average_eye_openness": average_eye_openness,
                "left_eye_center_y": left_eye_center_y,
                "right_eye_center_y": right_eye_center_y,
                "average_eye_center_y": average_eye_center_y,
                "face_center_y": face_center_y,
            }
        )

        feature_values = (
            ratios["average_y_ratio"],
            average_iris_y,
            average_eye_center_y,
            face_center_y,
        )
        if all(value is not None for value in feature_values):
            features["feature_vector"] = feature_values

        return features

    @staticmethod
    def _empty_result() -> dict[str, None]:
        return {
            "left_eye_y_ratio": None,
            "right_eye_y_ratio": None,
            "average_y_ratio": None,
        }

    def draw_debug_references(self, frame: Any, face_landmarks: list[Any]) -> None:
        if not face_landmarks or not hasattr(frame, "shape"):
            return

        landmarks = face_landmarks[0]
        for upper_indices, lower_indices, iris_indices in (
            (
                self.LEFT_UPPER_EYELID_INDICES,
                self.LEFT_LOWER_EYELID_INDICES,
                self.LEFT_IRIS_INDICES,
            ),
            (
                self.RIGHT_UPPER_EYELID_INDICES,
                self.RIGHT_LOWER_EYELID_INDICES,
                self.RIGHT_IRIS_INDICES,
            ),
        ):
            self._draw_reference_point(frame, landmarks, upper_indices, (255, 0, 0))
            self._draw_reference_point(frame, landmarks, lower_indices, (0, 0, 255))
            self._draw_reference_point(frame, landmarks, iris_indices, (0, 255, 255))

    def _eye_y_ratio(
        self,
        landmarks: list[Any],
        upper_eyelid_indices: tuple[int, ...],
        lower_eyelid_indices: tuple[int, ...],
        iris_indices: tuple[int, ...],
    ) -> float | None:
        upper_eyelid_y = self._average_y_for_indices(landmarks, upper_eyelid_indices)
        lower_eyelid_y = self._average_y_for_indices(landmarks, lower_eyelid_indices)
        iris_center_y = self._average_y_for_indices(landmarks, iris_indices)

        if (
            upper_eyelid_y is None
            or lower_eyelid_y is None
            or iris_center_y is None
        ):
            return None

        eye_height = lower_eyelid_y - upper_eyelid_y
        if eye_height <= 0:
            return None

        return (iris_center_y - upper_eyelid_y) / eye_height

    def _draw_reference_point(
        self,
        frame: Any,
        landmarks: list[Any],
        indices: tuple[int, ...],
        color: tuple[int, int, int],
    ) -> None:
        point = self._average_point_for_indices(landmarks, indices, frame.shape[1], frame.shape[0])
        if point is not None:
            cv2.circle(frame, point, 3, color, -1)

    @staticmethod
    def _y_values_for_indices(landmarks: list[Any], indices: tuple[int, ...]) -> list[float]:
        values: list[float] = []

        for index in indices:
            if index >= len(landmarks):
                continue

            y_value = getattr(landmarks[index], "y", None)
            if y_value is None:
                continue

            values.append(float(y_value))

        return values

    def _average_y_for_indices(
        self,
        landmarks: list[Any],
        indices: tuple[int, ...],
    ) -> float | None:
        values = self._y_values_for_indices(landmarks, indices)

        if len(values) != len(indices):
            return None

        return sum(values) / len(values)

    def _eye_center_y(
        self,
        landmarks: list[Any],
        upper_eyelid_indices: tuple[int, ...],
        lower_eyelid_indices: tuple[int, ...],
    ) -> float | None:
        upper_y = self._average_y_for_indices(landmarks, upper_eyelid_indices)
        lower_y = self._average_y_for_indices(landmarks, lower_eyelid_indices)

        if upper_y is None or lower_y is None:
            return None

        return (upper_y + lower_y) / 2

    def _eye_openness(
        self,
        landmarks: list[Any],
        upper_eyelid_indices: tuple[int, ...],
        lower_eyelid_indices: tuple[int, ...],
        eye_corner_indices: tuple[int, int],
    ) -> float | None:
        upper_y = self._average_y_for_indices(landmarks, upper_eyelid_indices)
        lower_y = self._average_y_for_indices(landmarks, lower_eyelid_indices)
        first_corner = self._point_for_index(landmarks, eye_corner_indices[0])
        second_corner = self._point_for_index(landmarks, eye_corner_indices[1])

        if (
            upper_y is None
            or lower_y is None
            or first_corner is None
            or second_corner is None
        ):
            return None

        eyelid_distance = lower_y - upper_y
        eye_width = math.dist(first_corner, second_corner)
        if eyelid_distance <= 0 or eye_width <= 0:
            return None

        return eyelid_distance / eye_width

    @staticmethod
    def _point_for_index(
        landmarks: list[Any],
        index: int,
    ) -> tuple[float, float] | None:
        if index >= len(landmarks):
            return None

        landmark = landmarks[index]
        x_value = getattr(landmark, "x", None)
        y_value = getattr(landmark, "y", None)
        if x_value is None or y_value is None:
            return None

        return float(x_value), float(y_value)

    @staticmethod
    def _average_available(*values: float | None) -> float | None:
        available_values = [value for value in values if value is not None]

        if not available_values:
            return None

        return sum(available_values) / len(available_values)

    def _face_center_y(self, landmarks: list[Any]) -> float | None:
        y_values = self._all_y_values(landmarks)

        if not y_values:
            return None

        return (min(y_values) + max(y_values)) / 2

    @staticmethod
    def _all_y_values(landmarks: list[Any]) -> list[float]:
        values: list[float] = []

        for landmark in landmarks:
            y_value = getattr(landmark, "y", None)
            if y_value is not None:
                values.append(float(y_value))

        return values

    def _average_point_for_indices(
        self,
        landmarks: list[Any],
        indices: tuple[int, ...],
        width: int,
        height: int,
    ) -> tuple[int, int] | None:
        x_values: list[float] = []
        y_values: list[float] = []

        for index in indices:
            if index >= len(landmarks):
                return None

            landmark = landmarks[index]
            if landmark.x is None or landmark.y is None:
                return None

            x_values.append(float(landmark.x))
            y_values.append(float(landmark.y))

        if not x_values or not y_values:
            return None

        x = min(max(int((sum(x_values) / len(x_values)) * width), 0), width - 1)
        y = min(max(int((sum(y_values) / len(y_values)) * height), 0), height - 1)
        return x, y
