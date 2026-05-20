from collections.abc import Callable
from typing import Any

import cv2

from camera.webcam import Webcam
from control.scroll_engine import ACTION_NO_ACTION, ScrollEngine
from vision.face_mesh import FaceMeshDetector
from vision.gaze_detector import (
    BlinkGestureDetector,
)
from vision.iris_tracker import IrisTracker


WINDOW_NAME = "LazyScroll AI - Webcam Preview"


def run_webcam_preview(
    camera_index: int = 0,
    webcam: Webcam | None = None,
    face_mesh_detector: FaceMeshDetector | None = None,
    iris_tracker: IrisTracker | None = None,
    blink_detector: BlinkGestureDetector | None = None,
    scroll_engine: ScrollEngine | None = None,
    mirror_frame: Callable[[Any], Any] = lambda frame: cv2.flip(frame, 1),
    imshow: Callable[[str, Any], None] = cv2.imshow,
    wait_key: Callable[[int], int] = cv2.waitKey,
    destroy_windows: Callable[[], None] = cv2.destroyAllWindows,
) -> int:
    webcam = webcam or Webcam(camera_index=camera_index)

    if not webcam.open():
        print("Error: webcam not found or could not be opened.")
        return 1

    detector = face_mesh_detector
    tracker = iris_tracker or IrisTracker()
    blink_gestures = blink_detector or BlinkGestureDetector()
    scrolls = scroll_engine or ScrollEngine()
    print("Webcam preview with blink scrolling started. Press 'q' to quit.")

    try:
        if detector is None:
            try:
                detector = FaceMeshDetector()
            except FileNotFoundError as error:
                print(f"Error: {error}")
                return 1

        while True:
            success, frame = webcam.read_frame()
            if not success:
                print("Error: could not read frame from webcam.")
                return 1

            preview_frame = mirror_frame(frame)
            processed_frame, face_landmarks = detector.process_frame(preview_frame)
            features = tracker.extract_features(face_landmarks)
            tracker.draw_debug_references(processed_frame, face_landmarks)
            eye_open = features.get("average_eye_openness")
            gesture, closed = blink_gestures.update(eye_open)
            gesture_action = scrolls.handle_gesture(gesture)
            scroll_action = scrolls.update()
            action = scroll_action if scroll_action != ACTION_NO_ACTION else gesture_action
            print(
                _format_runtime_debug_line(
                    scrolls.enabled,
                    scrolls.auto_scroll,
                    gesture,
                    action,
                    eye_open,
                    closed,
                )
            )
            imshow(WINDOW_NAME, processed_frame)

            key = wait_key(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        webcam.release()
        if detector is not None:
            detector.close()
        destroy_windows()

    return 0


def main() -> int:
    return run_webcam_preview()


def _format_runtime_debug_line(
    enabled: bool,
    auto_scroll: bool,
    gesture: str,
    action: str,
    eye_open: float | None,
    closed: bool,
) -> str:
    return (
        f"enabled={_format_bool(enabled)} "
        f"auto_scroll={_format_bool(auto_scroll)} "
        f"gesture={gesture} "
        f"action={action} "
        f"eye_open={_format_ratio(eye_open)} "
        f"closed={_format_bool(closed)}"
    )


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "None"

    return f"{value:.4f}"


def _format_bool(value: bool) -> str:
    return str(value).lower()


if __name__ == "__main__":
    raise SystemExit(main())
