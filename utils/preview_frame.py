from typing import Any

import cv2


def resize_preview_frame(frame: Any, width: int, height: int) -> Any:
    if width <= 0 or height <= 0 or not hasattr(frame, "shape"):
        return frame

    current_height, current_width = frame.shape[:2]
    if current_width == width and current_height == height:
        return frame

    return cv2.resize(frame, (width, height))
