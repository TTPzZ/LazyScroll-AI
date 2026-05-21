from dataclasses import dataclass
from pathlib import Path
from typing import Any

from control.scroll_constants import ACTION_NO_ACTION
from control.scroll_engine import ScrollEngine
from utils.audio_feedback import AudioFeedback
from utils.config_loader import DEFAULT_SETTINGS_PATH, merge_settings, save_settings
from utils.debug_overlay import (
    OVERLAY_MODE_NORMAL,
    OVERLAY_MODES,
)
from vision.blink_calibration import (
    CALIBRATION_ACTION_FAILED,
    CALIBRATION_ACTION_SAVED,
    BlinkCalibrationResult,
    BlinkCalibrator,
)
from vision.gaze_detector import (
    BlinkGestureDetector,
    DOUBLE_BLINK,
    LONG_BLINK,
    NO_GESTURE,
    TRIPLE_BLINK,
)


KEYBOARD_GESTURE_TOGGLE_ENABLED = "KEY_TOGGLE_ENABLED"
KEYBOARD_GESTURE_STOP = "KEY_STOP_AUTO_SCROLL"
KEYBOARD_GESTURE_SPEED_SLOW = "KEY_SPEED_SLOW"
KEYBOARD_GESTURE_SPEED_NORMAL = "KEY_SPEED_NORMAL"
KEYBOARD_GESTURE_SPEED_FAST = "KEY_SPEED_FAST"
KEYBOARD_GESTURE_CALIBRATION = "KEY_CALIBRATION"
KEYBOARD_GESTURE_OVERLAY = "KEY_OVERLAY_MODE"


@dataclass(frozen=True)
class RuntimeFrameResult:
    gesture: str
    closed: bool
    action: str
    state: Any
    calibration_status: str
    overlay_mode: str


@dataclass(frozen=True)
class RuntimeKeyResult:
    gesture: str
    action: str
    state: Any
    calibration_status: str
    overlay_mode: str


class RuntimeManager:
    """Coordinates blink gestures, calibration, overlay mode, and feedback."""

    def __init__(
        self,
        settings: dict[str, Any] | None,
        blink_detector: BlinkGestureDetector,
        blink_calibrator: BlinkCalibrator,
        scroll_engine: ScrollEngine,
        settings_path: str | Path | None = None,
        audio_feedback: AudioFeedback | None = None,
        beep_fn: Any | None = None,
    ) -> None:
        self.settings = merge_settings(settings or {})
        self.settings_path = Path(settings_path) if settings_path is not None else None
        self.blink_detector = blink_detector
        self.blink_calibrator = blink_calibrator
        self.scroll_engine = scroll_engine
        self.overlay_mode = self._normalize_overlay_mode(
            str(self.settings.get("overlay_mode", OVERLAY_MODE_NORMAL))
        )
        self.audio_feedback = audio_feedback or AudioFeedback(
            enabled=bool(self.settings.get("audio_feedback", True)),
            beep_fn=beep_fn,
        )

    def process_eye_open(
        self,
        eye_open: float | None,
        timestamp_ms: int,
    ) -> RuntimeFrameResult:
        calibrating_before_update = self.blink_calibrator.running
        gesture, closed = self.blink_detector.update(eye_open, timestamp_ms=timestamp_ms)
        calibration_result = self.blink_calibrator.update(eye_open, timestamp_ms)
        calibrating_this_frame = (
            calibrating_before_update
            or self.blink_calibrator.running
            or calibration_result is not None
        )
        effective_gesture = NO_GESTURE if calibrating_this_frame else gesture
        gesture_action = self.scroll_engine.handle_gesture(
            effective_gesture,
            timestamp_ms=timestamp_ms,
        )
        calibration_action = (
            apply_calibration_result(
                calibration_result,
                self.settings,
                self.settings_path or DEFAULT_SETTINGS_PATH,
                self.blink_detector,
            )
            if calibration_result is not None
            else ACTION_NO_ACTION
        )
        action = (
            calibration_action
            if calibration_action != ACTION_NO_ACTION
            else gesture_action
        )
        state = self.scroll_engine.snapshot()
        self._notify_action(action, state.enabled)
        return RuntimeFrameResult(
            gesture=effective_gesture,
            closed=closed,
            action=action,
            state=state,
            calibration_status=self.blink_calibrator.status,
            overlay_mode=self.overlay_mode,
        )

    def handle_key(
        self,
        key: int,
        timestamp_ms: int,
    ) -> RuntimeKeyResult | None:
        if key == ord("o"):
            mode = self.cycle_overlay_mode()
            return self._key_result(
                KEYBOARD_GESTURE_OVERLAY,
                f"SET_OVERLAY_{mode.upper()}",
            )

        if key == ord("k"):
            return self._key_result(
                KEYBOARD_GESTURE_CALIBRATION,
                self.blink_calibrator.start(timestamp_ms),
            )

        if key == ord("e"):
            return self._key_result(
                KEYBOARD_GESTURE_TOGGLE_ENABLED,
                self.scroll_engine.toggle_enabled(),
            )

        if key == ord("s"):
            return self._key_result(
                KEYBOARD_GESTURE_STOP,
                self.scroll_engine.stop_auto_scroll(),
            )

        if key == ord("1"):
            return self._key_result(
                KEYBOARD_GESTURE_SPEED_SLOW,
                self.scroll_engine.set_speed_preset("slow"),
            )

        if key == ord("2"):
            return self._key_result(
                KEYBOARD_GESTURE_SPEED_NORMAL,
                self.scroll_engine.set_speed_preset("normal"),
            )

        if key == ord("3"):
            return self._key_result(
                KEYBOARD_GESTURE_SPEED_FAST,
                self.scroll_engine.set_speed_preset("fast"),
            )

        if key == ord("d"):
            return self._key_result(
                DOUBLE_BLINK,
                self.scroll_engine.handle_gesture(DOUBLE_BLINK),
            )

        if key == ord("t"):
            return self._key_result(
                TRIPLE_BLINK,
                self.scroll_engine.handle_gesture(TRIPLE_BLINK),
            )

        if key == ord("l"):
            return self._key_result(
                LONG_BLINK,
                self.scroll_engine.handle_gesture(LONG_BLINK),
            )

        return None

    def cycle_overlay_mode(self) -> str:
        index = OVERLAY_MODES.index(self.overlay_mode)
        self.overlay_mode = OVERLAY_MODES[(index + 1) % len(OVERLAY_MODES)]
        self.settings["overlay_mode"] = self.overlay_mode
        self._save_settings_safely()
        return self.overlay_mode

    def _key_result(self, gesture: str, action: str) -> RuntimeKeyResult:
        state = self.scroll_engine.snapshot()
        self._notify_action(action, state.enabled)
        return RuntimeKeyResult(
            gesture=gesture,
            action=action,
            state=state,
            calibration_status=self.blink_calibrator.status,
            overlay_mode=self.overlay_mode,
        )

    def _notify_action(self, action: str, enabled: bool) -> None:
        if action == ACTION_NO_ACTION:
            return

        self.audio_feedback.notify_action(action, enabled=enabled)

    def _save_settings_safely(self) -> None:
        if self.settings_path is None:
            return

        try:
            save_settings(self.settings, self.settings_path)
        except OSError:
            return

    @staticmethod
    def _normalize_overlay_mode(mode: str) -> str:
        return mode if mode in OVERLAY_MODES else OVERLAY_MODE_NORMAL


def apply_calibration_result(
    result: BlinkCalibrationResult,
    settings: dict[str, Any],
    settings_path: str | Path,
    blink_detector: BlinkGestureDetector,
) -> str:
    if not result.success or result.closed_threshold is None:
        return CALIBRATION_ACTION_FAILED

    updated_settings = dict(settings)
    updated_settings["closed_threshold"] = float(result.closed_threshold)
    try:
        save_settings(updated_settings, settings_path)
    except OSError:
        return CALIBRATION_ACTION_FAILED

    settings.update(updated_settings)
    blink_detector.closed_threshold = float(result.closed_threshold)
    return CALIBRATION_ACTION_SAVED
