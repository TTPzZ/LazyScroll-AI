import contextlib
import io
from pathlib import Path
import threading
from types import SimpleNamespace
import tempfile
import unittest

import numpy as np

from main import (
    KEYBOARD_GESTURE_CALIBRATION,
    KEYBOARD_GESTURE_STOP,
    KEYBOARD_GESTURE_TOGGLE_ENABLED,
    _apply_calibration_result,
    _handle_calibration_debug_key,
    _handle_keyboard_debug_key,
    _should_print_runtime_debug,
    run_webcam_preview,
)
from control.scroll_engine import ACTION_NO_ACTION, ACTION_SCROLL_DOWN
from utils.config_loader import DEFAULT_SETTINGS, load_settings
from vision.blink_calibration import (
    CALIBRATION_ACTION_FAILED,
    CALIBRATION_ACTION_SAVED,
    CALIBRATION_ACTION_STARTED,
    BlinkCalibrationResult,
)
from vision.gaze_detector import DOUBLE_BLINK, NO_GESTURE, TRIPLE_BLINK


class FakeWebcam:
    def __init__(self, frames, opens=True):
        self.frames = list(frames)
        self.opens = opens
        self.released = False

    def open(self):
        return self.opens

    def read_frame(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True


class FakeFaceMeshDetector:
    def __init__(self):
        self.frames = []
        self.closed = False

    def process_frame(self, frame):
        self.frames.append(frame)
        return f"annotated-{frame}", ["landmarks"]

    def close(self):
        self.closed = True


class IntermittentFaceMeshDetector(FakeFaceMeshDetector):
    def __init__(self):
        super().__init__()
        self.failures = 0

    def process_frame(self, frame):
        if self.failures == 0:
            self.failures += 1
            raise RuntimeError("landmarker failed")

        return super().process_frame(frame)


class FakeIrisTracker:
    def __init__(self):
        self.landmark_sets = []
        self.debug_frames = []

    def extract_features(self, face_landmarks):
        self.landmark_sets.append(face_landmarks)
        return {
            "left_eye_y_ratio": 0.25,
            "right_eye_y_ratio": 0.75,
            "average_y_ratio": 0.50,
            "left_eye_openness": 0.21,
            "right_eye_openness": 0.23,
            "average_eye_openness": 0.22,
            "average_iris_y": 0.40,
            "average_eye_center_y": 0.45,
            "face_center_y": 0.55,
            "feature_vector": (0.50, 0.40, 0.45, 0.55),
        }

    def draw_debug_references(self, frame, face_landmarks):
        self.debug_frames.append((frame, face_landmarks))


class FakeBlinkDetector:
    def __init__(self):
        self.eye_open_values = []
        self.closed_threshold = 0.18

    def update(self, eye_open, timestamp_ms=None):
        self.eye_open_values.append(eye_open)
        return "DOUBLE_BLINK", False


class FakeLongBlinkDetector(FakeBlinkDetector):
    def update(self, eye_open, timestamp_ms=None):
        self.eye_open_values.append(eye_open)
        return "LONG_BLINK", True


class FakeScrollEngine:
    def __init__(self):
        self.enabled = True
        self.auto_scroll = True
        self.direction = "DOWN"
        self.speed_preset = "normal"
        self.gestures = []
        self.update_calls = 0

    def handle_gesture(self, gesture, timestamp_ms=None):
        self.gestures.append(gesture)
        return "START_AUTO_SCROLL"

    def update(self, timestamp_ms=None):
        self.update_calls += 1
        return "SCROLL_DOWN"

    def snapshot(self):
        return SimpleNamespace(
            enabled=self.enabled,
            auto_scroll=self.auto_scroll,
            direction=self.direction,
            speed_preset=self.speed_preset,
            last_gesture="DOUBLE_BLINK",
            last_action="START_AUTO_SCROLL",
        )


class FakeKeyboardScrollEngine:
    def __init__(self):
        self.enabled = False
        self.auto_scroll = False
        self.direction = "NONE"
        self.speed_preset = "normal"
        self.handled_gestures = []
        self.stop_calls = 0
        self.toggle_calls = 0
        self.speed_presets = []

    def handle_gesture(self, gesture):
        self.handled_gestures.append(gesture)
        return f"HANDLE_{gesture}"

    def stop_auto_scroll(self):
        self.stop_calls += 1
        return "STOP_AUTO_SCROLL"

    def toggle_enabled(self):
        self.toggle_calls += 1
        self.enabled = not self.enabled
        return "TOGGLE_ENABLED"

    def set_speed_preset(self, preset_name):
        self.speed_presets.append(preset_name)
        self.speed_preset = preset_name
        return f"SET_SPEED_{preset_name.upper()}"


class FakeBlinkCalibrator:
    def __init__(self):
        self.started_at = []
        self.status = "Calibration: idle"

    def start(self, timestamp_ms):
        self.started_at.append(timestamp_ms)
        self.status = "Calibration: keep eyes open"
        return CALIBRATION_ACTION_STARTED

    @property
    def running(self):
        return False

    def update(self, eye_open, timestamp_ms):
        return None


class RunningBlinkCalibrator(FakeBlinkCalibrator):
    @property
    def running(self):
        return True


class MainPreviewTests(unittest.TestCase):
    def test_preview_displays_face_mesh_processed_frame(self):
        webcam = FakeWebcam(frames=["frame"])
        detector = FakeFaceMeshDetector()
        shown_frames = []

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                start_scroll_loop=False,
                mirror_frame=lambda frame: f"mirrored-{frame}",
                imshow=lambda window_name, frame: shown_frames.append(frame),
                wait_key=lambda delay_ms: ord("q"),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(detector.frames, ["mirrored-frame"])
        self.assertEqual(shown_frames, ["annotated-mirrored-frame"])
        self.assertTrue(webcam.released)
        self.assertTrue(detector.closed)

    def test_preview_releases_webcam_when_open_fails(self):
        webcam = FakeWebcam(frames=[], opens=False)
        windows_closed = []

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=FakeFaceMeshDetector(),
                start_scroll_loop=False,
                destroy_windows=lambda: windows_closed.append(True),
            )

        self.assertEqual(exit_code, 1)
        self.assertTrue(webcam.released)
        self.assertEqual(windows_closed, [True])
        self.assertIn("Error: webcam not found or could not be opened.", stdout.getvalue())

    def test_preview_prints_startup_status_messages(self):
        webcam = FakeWebcam(frames=["frame"])
        detector = FakeFaceMeshDetector()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                start_scroll_loop=False,
                mirror_frame=lambda frame: frame,
                imshow=lambda window_name, frame: None,
                wait_key=lambda delay_ms: ord("q"),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("Initializing camera...", output)
        self.assertIn("Loading FaceLandmarker...", output)
        self.assertIn("Ready", output)

    def test_preview_resizes_frame_before_detection(self):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        webcam = FakeWebcam(frames=[frame])
        detector = FakeFaceMeshDetector()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                settings={"preview_width": 320, "preview_height": 240},
                start_scroll_loop=False,
                mirror_frame=lambda frame: frame,
                imshow=lambda window_name, frame: None,
                wait_key=lambda delay_ms: ord("q"),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(detector.frames[0].shape, (240, 320, 3))

    def test_preview_continues_after_face_landmarker_failure(self):
        webcam = FakeWebcam(frames=["bad-frame", "good-frame"])
        detector = IntermittentFaceMeshDetector()
        wait_keys = [0, ord("q")]

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                start_scroll_loop=False,
                mirror_frame=lambda frame: frame,
                imshow=lambda window_name, frame: None,
                wait_key=lambda delay_ms: wait_keys.pop(0),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(detector.frames, ["good-frame"])
        self.assertIn("Warning: FaceLandmarker failed; retrying.", stdout.getvalue())

    def test_preview_exits_gracefully_after_repeated_frame_failures(self):
        webcam = FakeWebcam(frames=[])

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=FakeFaceMeshDetector(),
                settings={"max_frame_failures": 1},
                start_scroll_loop=False,
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 1)
        self.assertTrue(webcam.released)
        self.assertIn("Warning: no frame received from webcam.", stdout.getvalue())

    def test_preview_prints_blink_debug_line(self):
        webcam = FakeWebcam(frames=["frame"])
        detector = FakeFaceMeshDetector()
        iris_tracker = FakeIrisTracker()
        blink_detector = FakeBlinkDetector()
        scroll_engine = FakeScrollEngine()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                iris_tracker=iris_tracker,
                blink_detector=blink_detector,
                scroll_engine=scroll_engine,
                start_scroll_loop=False,
                mirror_frame=lambda frame: frame,
                imshow=lambda window_name, frame: None,
                wait_key=lambda delay_ms: ord("q"),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(iris_tracker.landmark_sets, [["landmarks"]])
        self.assertEqual(iris_tracker.debug_frames, [("annotated-frame", ["landmarks"])])
        self.assertEqual(blink_detector.eye_open_values, [0.22])
        self.assertEqual(scroll_engine.gestures, ["DOUBLE_BLINK"])
        self.assertEqual(scroll_engine.update_calls, 0)
        self.assertIn(
            "enabled=true auto_scroll=true direction=DOWN gesture=DOUBLE_BLINK action=START_AUTO_SCROLL",
            stdout.getvalue(),
        )
        self.assertIn("eye_open=0.2200", stdout.getvalue())
        self.assertIn("closed=false", stdout.getvalue())

    def test_preview_stops_scroll_thread_on_quit(self):
        webcam = FakeWebcam(frames=["frame"])
        detector = FakeFaceMeshDetector()
        scroll_engine = FakeScrollEngine()
        runner_started = threading.Event()
        runner_stopped = threading.Event()

        def scroll_loop_runner(engine, stop_event):
            runner_started.set()
            stop_event.wait(timeout=1.0)
            if stop_event.is_set():
                runner_stopped.set()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                scroll_engine=scroll_engine,
                scroll_loop_runner=scroll_loop_runner,
                mirror_frame=lambda frame: frame,
                imshow=lambda window_name, frame: None,
                wait_key=lambda delay_ms: ord("q"),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(runner_started.is_set())
        self.assertTrue(runner_stopped.is_set())

    def test_preview_suppresses_scroll_gestures_during_calibration(self):
        webcam = FakeWebcam(frames=["frame"])
        detector = FakeFaceMeshDetector()
        iris_tracker = FakeIrisTracker()
        blink_detector = FakeLongBlinkDetector()
        scroll_engine = FakeScrollEngine()

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run_webcam_preview(
                webcam=webcam,
                face_mesh_detector=detector,
                iris_tracker=iris_tracker,
                blink_detector=blink_detector,
                blink_calibrator=RunningBlinkCalibrator(),
                scroll_engine=scroll_engine,
                start_scroll_loop=False,
                mirror_frame=lambda frame: frame,
                imshow=lambda window_name, frame: None,
                wait_key=lambda delay_ms: ord("q"),
                destroy_windows=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(scroll_engine.gestures, [NO_GESTURE])

    def test_runtime_debug_prints_only_on_meaningful_changes(self):
        last_signature = None

        should_print_first, last_signature = _should_print_runtime_debug(
            last_signature=last_signature,
            enabled=True,
            auto_scroll=False,
            direction="NONE",
            gesture=NO_GESTURE,
            action=ACTION_NO_ACTION,
        )
        should_print_gesture, last_signature = _should_print_runtime_debug(
            last_signature=last_signature,
            enabled=True,
            auto_scroll=True,
            direction="DOWN",
            gesture=DOUBLE_BLINK,
            action=ACTION_SCROLL_DOWN,
        )
        should_print_same_scroll, last_signature = _should_print_runtime_debug(
            last_signature=last_signature,
            enabled=True,
            auto_scroll=True,
            direction="DOWN",
            gesture=NO_GESTURE,
            action=ACTION_SCROLL_DOWN,
        )
        should_print_stop_state, last_signature = _should_print_runtime_debug(
            last_signature=last_signature,
            enabled=True,
            auto_scroll=False,
            direction="NONE",
            gesture=NO_GESTURE,
            action=ACTION_NO_ACTION,
        )

        self.assertFalse(should_print_first)
        self.assertTrue(should_print_gesture)
        self.assertFalse(should_print_same_scroll)
        self.assertTrue(should_print_stop_state)

    def test_keyboard_debug_keys_map_to_scroll_controls(self):
        scroll_engine = FakeKeyboardScrollEngine()

        toggle = _handle_keyboard_debug_key(ord("e"), scroll_engine)
        stop = _handle_keyboard_debug_key(ord("s"), scroll_engine)
        slow = _handle_keyboard_debug_key(ord("1"), scroll_engine)
        normal = _handle_keyboard_debug_key(ord("2"), scroll_engine)
        fast = _handle_keyboard_debug_key(ord("3"), scroll_engine)
        double = _handle_keyboard_debug_key(ord("d"), scroll_engine)
        triple = _handle_keyboard_debug_key(ord("t"), scroll_engine)
        long = _handle_keyboard_debug_key(ord("l"), scroll_engine)
        ignored = _handle_keyboard_debug_key(ord("x"), scroll_engine)

        self.assertEqual(toggle, (KEYBOARD_GESTURE_TOGGLE_ENABLED, "TOGGLE_ENABLED"))
        self.assertEqual(stop, (KEYBOARD_GESTURE_STOP, "STOP_AUTO_SCROLL"))
        self.assertEqual(slow, ("KEY_SPEED_SLOW", "SET_SPEED_SLOW"))
        self.assertEqual(normal, ("KEY_SPEED_NORMAL", "SET_SPEED_NORMAL"))
        self.assertEqual(fast, ("KEY_SPEED_FAST", "SET_SPEED_FAST"))
        self.assertEqual(double, (DOUBLE_BLINK, "HANDLE_DOUBLE_BLINK"))
        self.assertEqual(triple, (TRIPLE_BLINK, "HANDLE_TRIPLE_BLINK"))
        self.assertEqual(long, ("LONG_BLINK", "HANDLE_LONG_BLINK"))
        self.assertIsNone(ignored)
        self.assertEqual(scroll_engine.toggle_calls, 1)
        self.assertEqual(scroll_engine.stop_calls, 1)
        self.assertEqual(scroll_engine.speed_presets, ["slow", "normal", "fast"])
        self.assertEqual(
            scroll_engine.handled_gestures,
            ["DOUBLE_BLINK", "TRIPLE_BLINK", "LONG_BLINK"],
        )

    def test_calibration_debug_key_starts_blink_calibration(self):
        calibrator = FakeBlinkCalibrator()

        event = _handle_calibration_debug_key(ord("k"), calibrator, timestamp_ms=1234)
        ignored = _handle_calibration_debug_key(ord("x"), calibrator, timestamp_ms=1500)

        self.assertEqual(event, (KEYBOARD_GESTURE_CALIBRATION, CALIBRATION_ACTION_STARTED))
        self.assertIsNone(ignored)
        self.assertEqual(calibrator.started_at, [1234])

    def test_apply_calibration_result_saves_threshold_and_updates_detector(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings = load_settings(settings_path)
            detector = FakeBlinkDetector()
            result = BlinkCalibrationResult(
                success=True,
                closed_threshold=0.24,
                open_average=0.34,
                closed_average=0.14,
                reason="saved",
            )

            action = _apply_calibration_result(
                result,
                settings,
                settings_path,
                detector,
            )

            self.assertEqual(action, CALIBRATION_ACTION_SAVED)
            self.assertEqual(detector.closed_threshold, 0.24)
            self.assertEqual(load_settings(settings_path)["closed_threshold"], 0.24)

    def test_apply_calibration_result_keeps_existing_threshold_on_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings = load_settings(settings_path)
            detector = FakeBlinkDetector()
            result = BlinkCalibrationResult(
                success=False,
                closed_threshold=None,
                open_average=None,
                closed_average=None,
                reason="not enough samples",
            )

            action = _apply_calibration_result(
                result,
                settings,
                settings_path,
                detector,
            )

            self.assertEqual(action, CALIBRATION_ACTION_FAILED)
            self.assertEqual(detector.closed_threshold, 0.18)
            self.assertEqual(
                load_settings(settings_path)["closed_threshold"],
                DEFAULT_SETTINGS["closed_threshold"],
            )


if __name__ == "__main__":
    unittest.main()
