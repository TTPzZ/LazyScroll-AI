from collections.abc import Callable, Iterable
from pathlib import Path
import time
from typing import Any

import cv2
import numpy as np

from utils.resource_path import model_path as _resolve_model_path

DEFAULT_MODEL_PATH = _resolve_model_path()


class FaceMeshDetector:
    """MediaPipe Tasks FaceLandmarker wrapper for webcam frames."""

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
        max_num_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        landmarker: Any | None = None,
        mediapipe_module: Any | None = None,
        vision_module: Any | None = None,
        base_options_cls: Any | None = None,
        connections: Iterable[Any] | None = None,
        timestamp_provider: Callable[[], float] | None = None,
    ) -> None:
        self._mp = mediapipe_module or self._import_mediapipe()
        self._timestamp_provider = timestamp_provider or (
            lambda: int(time.monotonic() * 1000)
        )
        self._last_timestamp_ms: int | None = None

        if landmarker is None:
            vision_module, base_options_cls = self._load_tasks_api(
                vision_module=vision_module,
                base_options_cls=base_options_cls,
            )
            model_path = Path(model_path)
            self._validate_model_path(model_path)
            landmarker = self._create_landmarker(
                model_path=model_path,
                vision_module=vision_module,
                base_options_cls=base_options_cls,
                max_num_faces=max_num_faces,
                min_detection_confidence=min_detection_confidence,
                min_presence_confidence=min_presence_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

        self._landmarker = landmarker
        self._connections = list(
            connections
            if connections is not None
            else self._default_connections(vision_module)
        )

    def process_frame(self, frame: Any) -> tuple[Any, list[Any]]:
        annotated_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(rgb_frame),
        )

        result = self._landmarker.detect_for_video(
            mp_image,
            self._next_timestamp_ms(),
        )
        face_landmarks = list(getattr(result, "face_landmarks", []) or [])

        for landmark_list in face_landmarks:
            self._draw_landmarks(annotated_frame, landmark_list)

        return annotated_frame, face_landmarks

    def close(self) -> None:
        close = getattr(self._landmarker, "close", None)
        if close is not None:
            close()

    def _next_timestamp_ms(self) -> int:
        timestamp_ms = int(self._timestamp_provider())

        if self._last_timestamp_ms is not None and timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1

        self._last_timestamp_ms = timestamp_ms
        return timestamp_ms

    def _draw_landmarks(self, frame: Any, landmarks: list[Any]) -> None:
        height, width = frame.shape[:2]

        for connection in self._connections:
            start_index = self._connection_index(connection, "start", 0)
            end_index = self._connection_index(connection, "end", 1)
            if start_index >= len(landmarks) or end_index >= len(landmarks):
                continue

            start_point = self._landmark_to_point(landmarks[start_index], width, height)
            end_point = self._landmark_to_point(landmarks[end_index], width, height)
            if start_point is None or end_point is None:
                continue

            cv2.line(frame, start_point, end_point, (0, 255, 0), 1)

        for landmark in landmarks:
            point = self._landmark_to_point(landmark, width, height)
            if point is not None:
                cv2.circle(frame, point, 1, (0, 128, 255), -1)

    @staticmethod
    def _landmark_to_point(landmark: Any, width: int, height: int) -> tuple[int, int] | None:
        if landmark.x is None or landmark.y is None:
            return None

        x = min(max(int(landmark.x * width), 0), width - 1)
        y = min(max(int(landmark.y * height), 0), height - 1)
        return x, y

    @staticmethod
    def _connection_index(connection: Any, attribute_name: str, tuple_index: int) -> int:
        if hasattr(connection, attribute_name):
            return int(getattr(connection, attribute_name))

        return int(connection[tuple_index])

    @staticmethod
    def _import_mediapipe() -> Any:
        import mediapipe as mp

        return mp

    @staticmethod
    def _load_tasks_api(
        vision_module: Any | None,
        base_options_cls: Any | None,
    ) -> tuple[Any, Any]:
        if vision_module is not None and base_options_cls is not None:
            return vision_module, base_options_cls

        from mediapipe.tasks.python import BaseOptions, vision

        return vision_module or vision, base_options_cls or BaseOptions

    @staticmethod
    def _validate_model_path(model_path: Path) -> None:
        if model_path.is_file():
            return

        raise FileNotFoundError(
            "MediaPipe FaceLandmarker model file not found: "
            f"{model_path}. Download face_landmarker.task into the local "
            "models folder before running python main.py."
        )

    @staticmethod
    def _create_landmarker(
        model_path: Path,
        vision_module: Any,
        base_options_cls: Any,
        max_num_faces: int,
        min_detection_confidence: float,
        min_presence_confidence: float,
        min_tracking_confidence: float,
    ) -> Any:
        options = vision_module.FaceLandmarkerOptions(
            base_options=base_options_cls(model_asset_path=str(model_path)),
            running_mode=vision_module.RunningMode.VIDEO,
            num_faces=max_num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        return vision_module.FaceLandmarker.create_from_options(options)

    @staticmethod
    def _default_connections(vision_module: Any | None) -> list[Any]:
        if vision_module is None:
            return []

        return list(
            getattr(
                vision_module.FaceLandmarksConnections,
                "FACE_LANDMARKS_TESSELATION",
                [],
            )
        )
