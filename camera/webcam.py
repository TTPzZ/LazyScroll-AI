from collections.abc import Callable
from typing import Any

import cv2


class Webcam:
    """Small wrapper around OpenCV webcam capture."""

    def __init__(
        self,
        camera_index: int = 0,
        capture_factory: Callable[[int], Any] = cv2.VideoCapture,
    ) -> None:
        self.camera_index = camera_index
        self._capture_factory = capture_factory
        self._capture: Any | None = None

    @property
    def is_open(self) -> bool:
        return self._capture is not None and bool(self._capture.isOpened())

    def open(self) -> bool:
        self._capture = self._capture_factory(self.camera_index)

        if not self.is_open:
            self.release()
            return False

        return True

    def read_frame(self) -> tuple[bool, Any | None]:
        if not self.is_open:
            return False, None

        success, frame = self._capture.read()
        if not success:
            return False, None

        return True, frame

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
