from collections.abc import Callable
from pathlib import Path
import threading
import time
from typing import Any

import cv2

from camera.webcam import Webcam
from control.runtime_manager import (
    KEYBOARD_GESTURE_CALIBRATION,
    KEYBOARD_GESTURE_OVERLAY,
    KEYBOARD_GESTURE_SPEED_FAST,
    KEYBOARD_GESTURE_SPEED_NORMAL,
    KEYBOARD_GESTURE_SPEED_SLOW,
    KEYBOARD_GESTURE_STOP,
    KEYBOARD_GESTURE_TOGGLE_ENABLED,
    RuntimeManager,
    apply_calibration_result as _apply_calibration_result,
)
from control.scroll_engine import ACTION_NO_ACTION, ScrollEngine
from control.scroll_loop import run_scroll_loop
from vision.face_mesh import FaceMeshDetector
from vision.gaze_detector import (
    BlinkGestureDetector,
    DOUBLE_BLINK,
    LONG_BLINK,
    NO_GESTURE,
    TRIPLE_BLINK,
)
from vision.iris_tracker import IrisTracker
from vision.blink_calibration import (
    BlinkCalibrator,
)
from utils.config_loader import DEFAULT_SETTINGS_PATH, load_settings, merge_settings
from utils.debug_overlay import DebugOverlay
from utils.frame_rate import FrameRateLimiter
from utils.preview_frame import resize_preview_frame


WINDOW_NAME = "LazyScroll AI - Webcam Preview"


def run_webcam_preview(
    camera_index: int = 0,
    webcam: Webcam | None = None,
    face_mesh_detector: FaceMeshDetector | None = None,
    iris_tracker: IrisTracker | None = None,
    blink_detector: BlinkGestureDetector | None = None,
    blink_calibrator: BlinkCalibrator | None = None,
    scroll_engine: ScrollEngine | None = None,
    runtime_manager: RuntimeManager | None = None,
    debug_overlay: DebugOverlay | None = None,
    settings: dict[str, Any] | None = None,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
    start_scroll_loop: bool = True,
    scroll_loop_runner: Callable[[ScrollEngine, threading.Event], None] = run_scroll_loop,
    time_provider: Callable[[], float] = lambda: time.monotonic() * 1000,
    sleep_fn: Callable[[float], None] | None = None,
    mirror_frame: Callable[[Any], Any] = lambda frame: cv2.flip(frame, 1),
    imshow: Callable[[str, Any], None] = cv2.imshow,
    wait_key: Callable[[int], int] = cv2.waitKey,
    destroy_windows: Callable[[], None] = cv2.destroyAllWindows,
) -> int:
    webcam = webcam or Webcam(camera_index=camera_index)

    print("Initializing camera...")
    if not webcam.open():
        print("Error: webcam not found or could not be opened.")
        webcam.release()
        destroy_windows()
        return 1

    detector = face_mesh_detector
    tracker = iris_tracker or IrisTracker()
    app_settings = merge_settings(settings if settings is not None else load_settings(settings_path))
    active_speed_settings = _active_speed_settings(app_settings)
    blink_gestures = blink_detector or BlinkGestureDetector(
        closed_threshold=float(app_settings["closed_threshold"]),
        multi_blink_window_ms=int(app_settings["multi_blink_window_ms"]),
        long_blink_ms=int(app_settings["long_blink_ms"]),
    )
    calibrator = blink_calibrator or BlinkCalibrator()
    scrolls = scroll_engine or ScrollEngine(
        down_scroll_amount_per_step=int(active_speed_settings["down_scroll_amount_per_step"]),
        up_scroll_amount_per_step=int(active_speed_settings["up_scroll_amount_per_step"]),
        scroll_interval_ms=int(active_speed_settings["scroll_interval_ms"]),
        auto_scroll_timeout_ms=int(app_settings["auto_scroll_timeout_ms"]),
        speed_preset=str(app_settings["speed_preset"]),
        speed_presets=app_settings["speed_presets"],
    )
    overlay = debug_overlay or DebugOverlay(
        hold_ms=int(app_settings["last_event_display_ms"]),
        mode=str(app_settings["overlay_mode"]),
    )
    manager = runtime_manager or RuntimeManager(
        settings=app_settings,
        settings_path=settings_path,
        blink_detector=blink_gestures,
        blink_calibrator=calibrator,
        scroll_engine=scrolls,
    )
    frame_limiter = FrameRateLimiter(
        fps_limit=int(app_settings["preview_fps_limit"]),
        time_provider=time_provider,
        sleep_fn=sleep_fn,
    )
    stop_event = threading.Event()
    scroll_thread: threading.Thread | None = None
    if start_scroll_loop:
        scroll_thread = threading.Thread(
            target=scroll_loop_runner,
            args=(scrolls, stop_event),
            daemon=True,
        )
        scroll_thread.start()

    last_print_signature = None
    last_overlay_event_signature = None
    print("Webcam preview with blink scrolling started. Press 'q' to quit.")

    try:
        print("Loading FaceLandmarker...")
        if detector is None:
            try:
                detector = FaceMeshDetector()
            except FileNotFoundError as error:
                print(f"Error: {error}")
                return 1
            except Exception as error:
                print(f"Error: FaceLandmarker could not be loaded: {error}")
                return 1
        print("Ready")

        consecutive_frame_failures = 0
        while True:
            success, frame = webcam.read_frame()
            if not success:
                consecutive_frame_failures += 1
                print("Warning: no frame received from webcam.")
                if consecutive_frame_failures >= int(app_settings["max_frame_failures"]):
                    print("Error: webcam frame stream unavailable.")
                    return 1
                frame_limiter.wait()
                continue
            consecutive_frame_failures = 0

            resized_frame = resize_preview_frame(
                frame,
                width=int(app_settings["preview_width"]),
                height=int(app_settings["preview_height"]),
            )
            preview_frame = mirror_frame(resized_frame)
            try:
                processed_frame, face_landmarks = detector.process_frame(preview_frame)
            except Exception:
                print("Warning: FaceLandmarker failed; retrying.")
                processed_frame = preview_frame
                face_landmarks = []
            features = tracker.extract_features(face_landmarks)
            tracker.draw_debug_references(processed_frame, face_landmarks)
            eye_open = features.get("average_eye_openness")
            timestamp_ms = int(time_provider())
            runtime_result = manager.process_eye_open(eye_open, timestamp_ms)
            state = runtime_result.state
            event_gesture = state.last_gesture
            event_action = (
                runtime_result.action
                if runtime_result.action != ACTION_NO_ACTION
                else state.last_action
            )
            overlay_signature = (event_gesture, event_action)
            if overlay_signature != last_overlay_event_signature:
                overlay.record_event(event_gesture, event_action, timestamp_ms)
                last_overlay_event_signature = overlay_signature
            snapshot = overlay.snapshot(
                enabled=state.enabled,
                auto_scroll=state.auto_scroll,
                direction=state.direction,
                speed_preset=state.speed_preset,
                current_gesture=runtime_result.gesture,
                current_action=runtime_result.action,
                timestamp_ms=timestamp_ms,
                calibration_status=runtime_result.calibration_status,
                overlay_mode=runtime_result.overlay_mode,
            )
            overlay.draw(processed_frame, snapshot)

            line = _format_runtime_debug_line(
                state.enabled,
                state.auto_scroll,
                state.direction,
                runtime_result.gesture,
                runtime_result.action,
                eye_open,
                runtime_result.closed,
            )
            should_print, last_print_signature = _should_print_runtime_debug(
                last_print_signature,
                state.enabled,
                state.auto_scroll,
                state.direction,
                runtime_result.gesture,
                runtime_result.action,
            )
            if should_print:
                print(line)

            imshow(WINDOW_NAME, processed_frame)

            key = wait_key(1) & 0xFF
            if key == ord("q"):
                break

            key_result = manager.handle_key(
                key,
                timestamp_ms=int(time_provider()),
            )
            if key_result is not None:
                keyboard_timestamp_ms = int(time_provider())
                state = key_result.state
                overlay.record_event(
                    state.last_gesture if state.last_gesture != NO_GESTURE else key_result.gesture,
                    state.last_action if state.last_action != ACTION_NO_ACTION else key_result.action,
                    keyboard_timestamp_ms,
                )
                last_overlay_event_signature = (
                    state.last_gesture if state.last_gesture != NO_GESTURE else key_result.gesture,
                    state.last_action if state.last_action != ACTION_NO_ACTION else key_result.action,
                )
                keyboard_line = _format_runtime_debug_line(
                    state.enabled,
                    state.auto_scroll,
                    state.direction,
                    key_result.gesture,
                    key_result.action,
                    eye_open,
                    runtime_result.closed,
                )
                should_print, last_print_signature = _should_print_runtime_debug(
                    last_print_signature,
                    state.enabled,
                    state.auto_scroll,
                    state.direction,
                    key_result.gesture,
                    key_result.action,
                )
                if should_print:
                    print(keyboard_line)

            frame_limiter.wait()
    finally:
        stop_event.set()
        if scroll_thread is not None:
            scroll_thread.join(timeout=1.0)
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
    direction: str,
    gesture: str,
    action: str,
    eye_open: float | None,
    closed: bool,
) -> str:
    return (
        f"enabled={_format_bool(enabled)} "
        f"auto_scroll={_format_bool(auto_scroll)} "
        f"direction={direction} "
        f"gesture={gesture} "
        f"action={action} "
        f"eye_open={_format_ratio(eye_open)} "
        f"closed={_format_bool(closed)}"
    )


def _handle_keyboard_debug_key(
    key: int,
    scroll_engine: ScrollEngine,
) -> tuple[str, str] | None:
    if key == ord("e"):
        return KEYBOARD_GESTURE_TOGGLE_ENABLED, scroll_engine.toggle_enabled()

    if key == ord("s"):
        return KEYBOARD_GESTURE_STOP, scroll_engine.stop_auto_scroll()

    if key == ord("1"):
        return KEYBOARD_GESTURE_SPEED_SLOW, scroll_engine.set_speed_preset("slow")

    if key == ord("2"):
        return KEYBOARD_GESTURE_SPEED_NORMAL, scroll_engine.set_speed_preset("normal")

    if key == ord("3"):
        return KEYBOARD_GESTURE_SPEED_FAST, scroll_engine.set_speed_preset("fast")

    if key == ord("d"):
        return DOUBLE_BLINK, scroll_engine.handle_gesture(DOUBLE_BLINK)

    if key == ord("t"):
        return TRIPLE_BLINK, scroll_engine.handle_gesture(TRIPLE_BLINK)

    if key == ord("l"):
        return LONG_BLINK, scroll_engine.handle_gesture(LONG_BLINK)

    return None


def _handle_calibration_debug_key(
    key: int,
    calibrator: BlinkCalibrator,
    timestamp_ms: int,
) -> tuple[str, str] | None:
    if key == ord("k"):
        return KEYBOARD_GESTURE_CALIBRATION, calibrator.start(timestamp_ms)

    return None


def _active_speed_settings(settings: dict[str, Any]) -> dict[str, Any]:
    speed_presets = settings.get("speed_presets", {})
    speed_preset = settings.get("speed_preset")
    preset = speed_presets.get(speed_preset) if isinstance(speed_presets, dict) else None

    if isinstance(preset, dict):
        return preset

    return settings


def _should_print_runtime_debug(
    last_signature: tuple[tuple[bool, bool, str], str | None, str | None] | None,
    enabled: bool,
    auto_scroll: bool,
    direction: str,
    gesture: str,
    action: str,
) -> tuple[bool, tuple[tuple[bool, bool, str], str | None, str | None]]:
    state_signature = (enabled, auto_scroll, direction)
    if last_signature is None:
        last_state_signature = state_signature
        last_action: str | None = None
        last_gesture: str | None = None
    else:
        last_state_signature, last_action, last_gesture = last_signature

    meaningful_gesture = gesture != NO_GESTURE
    meaningful_action = action != ACTION_NO_ACTION
    state_changed = state_signature != last_state_signature
    action_changed = meaningful_action and action != last_action
    gesture_changed = meaningful_gesture and gesture != last_gesture
    should_print = state_changed or action_changed or gesture_changed

    next_action = action if meaningful_action else last_action
    next_gesture = gesture if meaningful_gesture else last_gesture
    return should_print, (state_signature, next_action, next_gesture)


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "None"

    return f"{value:.4f}"


def _format_bool(value: bool) -> str:
    return str(value).lower()


if __name__ == "__main__":
    raise SystemExit(main())
