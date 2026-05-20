import contextlib
import io
import unittest

from main import run_webcam_preview


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

    def update(self, eye_open):
        self.eye_open_values.append(eye_open)
        return "DOUBLE_BLINK", False


class FakeScrollEngine:
    def __init__(self):
        self.enabled = True
        self.auto_scroll = True
        self.gestures = []
        self.update_calls = 0

    def handle_gesture(self, gesture):
        self.gestures.append(gesture)
        return "START_AUTO_SCROLL"

    def update(self):
        self.update_calls += 1
        return "SCROLL_DOWN"


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
        self.assertEqual(scroll_engine.update_calls, 1)
        self.assertIn(
            "enabled=true auto_scroll=true gesture=DOUBLE_BLINK action=SCROLL_DOWN",
            stdout.getvalue(),
        )
        self.assertIn("eye_open=0.2200", stdout.getvalue())
        self.assertIn("closed=false", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
