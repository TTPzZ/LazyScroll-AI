from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from control.runtime_manager import (
    KEYBOARD_GESTURE_OVERLAY,
    RuntimeManager,
)
from control.scroll_constants import ACTION_START_AUTO_SCROLL, ACTION_TOGGLE_ENABLED
from utils.config_loader import load_settings
from utils.debug_overlay import (
    OVERLAY_MODE_HIDDEN,
    OVERLAY_MODE_MINIMAL,
    OVERLAY_MODE_NORMAL,
)
from vision.blink_calibration import (
    CALIBRATION_ACTION_SAVED,
    BlinkCalibrationResult,
)
from vision.gaze_detector import DOUBLE_BLINK, NO_GESTURE


class FakeBlinkDetector:
    def __init__(self):
        self.closed_threshold = 0.18

    def update(self, eye_open, timestamp_ms=None):
        return DOUBLE_BLINK, False


class FakeCalibrator:
    def __init__(self, result=None):
        self.status = "Calibration: idle"
        self.result = result
        self.started = []

    @property
    def running(self):
        return False

    def start(self, timestamp_ms):
        self.started.append(timestamp_ms)
        self.status = "Calibration: keep eyes open"
        return "CALIBRATION_STARTED"

    def update(self, eye_open, timestamp_ms):
        return self.result


class FakeScrollEngine:
    def __init__(self):
        self.gestures = []
        self.enabled = True
        self.auto_scroll = False
        self.direction = "NONE"
        self.speed_preset = "normal"
        self.last_action = "NO_ACTION"
        self.last_gesture = NO_GESTURE

    def handle_gesture(self, gesture, timestamp_ms=None):
        self.gestures.append(gesture)
        self.last_gesture = gesture
        if gesture == DOUBLE_BLINK:
            self.auto_scroll = True
            self.direction = "DOWN"
            self.last_action = ACTION_START_AUTO_SCROLL
            return ACTION_START_AUTO_SCROLL
        return "NO_ACTION"

    def toggle_enabled(self):
        self.enabled = not self.enabled
        self.last_action = ACTION_TOGGLE_ENABLED
        return ACTION_TOGGLE_ENABLED

    def stop_auto_scroll(self):
        self.auto_scroll = False
        self.direction = "NONE"
        return "STOP_AUTO_SCROLL"

    def set_speed_preset(self, preset_name):
        self.speed_preset = preset_name
        return f"SET_SPEED_{preset_name.upper()}"

    def snapshot(self):
        return SimpleNamespace(
            enabled=self.enabled,
            auto_scroll=self.auto_scroll,
            direction=self.direction,
            speed_preset=self.speed_preset,
            last_gesture=self.last_gesture,
            last_action=self.last_action,
        )


class RuntimeManagerTests(unittest.TestCase):
    def test_overlay_key_cycles_overlay_mode(self):
        manager = RuntimeManager(
            settings={"overlay_mode": OVERLAY_MODE_NORMAL},
            blink_detector=FakeBlinkDetector(),
            blink_calibrator=FakeCalibrator(),
            scroll_engine=FakeScrollEngine(),
        )

        first = manager.handle_key(ord("o"), timestamp_ms=1000)
        second = manager.handle_key(ord("o"), timestamp_ms=1100)
        third = manager.handle_key(ord("o"), timestamp_ms=1200)

        self.assertEqual(first.gesture, KEYBOARD_GESTURE_OVERLAY)
        self.assertEqual(first.action, "SET_OVERLAY_MINIMAL")
        self.assertEqual(manager.overlay_mode, OVERLAY_MODE_NORMAL)
        self.assertEqual([first.overlay_mode, second.overlay_mode, third.overlay_mode], [
            OVERLAY_MODE_MINIMAL,
            OVERLAY_MODE_HIDDEN,
            OVERLAY_MODE_NORMAL,
        ])

    def test_process_eye_open_suppresses_gestures_during_calibration(self):
        calibrator = FakeCalibrator(result=BlinkCalibrationResult(
            success=True,
            closed_threshold=0.24,
            open_average=0.34,
            closed_average=0.14,
            reason="saved",
        ))
        scroll_engine = FakeScrollEngine()

        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings = load_settings(settings_path)
            manager = RuntimeManager(
                settings=settings,
                settings_path=settings_path,
                blink_detector=FakeBlinkDetector(),
                blink_calibrator=calibrator,
                scroll_engine=scroll_engine,
            )

            result = manager.process_eye_open(0.2, timestamp_ms=1000)

            self.assertEqual(result.action, CALIBRATION_ACTION_SAVED)
            self.assertEqual(scroll_engine.gestures, [NO_GESTURE])
            self.assertEqual(load_settings(settings_path)["closed_threshold"], 0.24)

    def test_audio_feedback_runs_for_meaningful_actions(self):
        beeps = []
        scroll_engine = FakeScrollEngine()
        manager = RuntimeManager(
            settings={"audio_feedback": True},
            blink_detector=FakeBlinkDetector(),
            blink_calibrator=FakeCalibrator(),
            scroll_engine=scroll_engine,
            beep_fn=lambda frequency, duration: beeps.append((frequency, duration)),
        )

        manager.process_eye_open(0.2, timestamp_ms=1000)
        manager.handle_key(ord("e"), timestamp_ms=1100)

        self.assertEqual(beeps, [(660, 60), (440, 80)])


if __name__ == "__main__":
    unittest.main()
