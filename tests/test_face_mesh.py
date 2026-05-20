from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import numpy as np

from vision.face_mesh import FaceMeshDetector


class FakeImageFormat:
    SRGB = "SRGB"


class FakeImage:
    created = []

    def __init__(self, image_format, data):
        self.image_format = image_format
        self.data = data
        FakeImage.created.append(self)


class FakeMediaPipe:
    Image = FakeImage
    ImageFormat = FakeImageFormat


class FakeLandmarker:
    def __init__(self, landmarks):
        self.landmarks = landmarks
        self.detect_calls = []
        self.closed = False

    def detect_for_video(self, image, timestamp_ms):
        self.detect_calls.append((image, timestamp_ms))
        return SimpleNamespace(face_landmarks=self.landmarks)

    def close(self):
        self.closed = True


class FakeBaseOptions:
    created_paths = []

    def __init__(self, model_asset_path):
        self.model_asset_path = model_asset_path
        FakeBaseOptions.created_paths.append(model_asset_path)


class FakeFaceLandmarkerOptions:
    created = []

    def __init__(
        self,
        base_options,
        running_mode,
        num_faces,
        min_face_detection_confidence,
        min_face_presence_confidence,
        min_tracking_confidence,
    ):
        self.base_options = base_options
        self.running_mode = running_mode
        self.num_faces = num_faces
        self.min_face_detection_confidence = min_face_detection_confidence
        self.min_face_presence_confidence = min_face_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence
        FakeFaceLandmarkerOptions.created.append(self)


class FakeFaceLandmarkerFactory:
    landmarker = FakeLandmarker(landmarks=[])

    @classmethod
    def create_from_options(cls, options):
        cls.created_options = options
        return cls.landmarker


class FakeRunningMode:
    VIDEO = "VIDEO"


class FakeConnections:
    FACE_LANDMARKS_TESSELATION = [SimpleNamespace(start=0, end=1)]


class FakeVisionModule:
    FaceLandmarker = FakeFaceLandmarkerFactory
    FaceLandmarkerOptions = FakeFaceLandmarkerOptions
    FaceLandmarksConnections = FakeConnections
    RunningMode = FakeRunningMode


class FaceMeshDetectorTests(unittest.TestCase):
    def setUp(self):
        FakeImage.created = []
        FakeBaseOptions.created_paths = []
        FakeFaceLandmarkerOptions.created = []

    def test_creates_tasks_face_landmarker_from_local_model_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "face_landmarker.task"
            model_path.write_bytes(b"fake model")

            FaceMeshDetector(
                model_path=model_path,
                mediapipe_module=FakeMediaPipe,
                vision_module=FakeVisionModule,
                base_options_cls=FakeBaseOptions,
            )

        self.assertEqual(FakeBaseOptions.created_paths, [str(model_path)])
        options = FakeFaceLandmarkerOptions.created[0]
        self.assertEqual(options.running_mode, "VIDEO")
        self.assertEqual(options.num_faces, 1)
        self.assertIs(FakeFaceLandmarkerFactory.created_options, options)

    def test_missing_model_path_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_model_path = Path(temp_dir) / "models" / "face_landmarker.task"

            with self.assertRaisesRegex(FileNotFoundError, "models.*face_landmarker.task"):
                FaceMeshDetector(model_path=missing_model_path)

    def test_process_frame_uses_tasks_image_and_returns_face_landmarks(self):
        landmarks = [
            [
                SimpleNamespace(x=0.25, y=0.25),
                SimpleNamespace(x=0.75, y=0.75),
            ]
        ]
        landmarker = FakeLandmarker(landmarks=landmarks)
        detector = FaceMeshDetector(
            landmarker=landmarker,
            mediapipe_module=FakeMediaPipe,
            connections=[SimpleNamespace(start=0, end=1)],
            timestamp_provider=lambda: 1.0,
        )
        frame = np.zeros((20, 20, 3), dtype=np.uint8)
        frame[0, 0] = [10, 20, 30]

        processed_frame, detected_landmarks = detector.process_frame(frame)

        self.assertEqual(detected_landmarks, landmarks)
        self.assertIs(FakeImage.created[0], landmarker.detect_calls[0][0])
        self.assertEqual(FakeImage.created[0].image_format, "SRGB")
        np.testing.assert_array_equal(FakeImage.created[0].data[0, 0], [30, 20, 10])
        self.assertEqual(landmarker.detect_calls[0][1], 1)
        self.assertIsNot(processed_frame, frame)
        self.assertTrue(np.any(processed_frame != frame))

    def test_timestamp_increases_when_frames_arrive_with_same_clock_value(self):
        landmarker = FakeLandmarker(landmarks=[])
        detector = FaceMeshDetector(
            landmarker=landmarker,
            mediapipe_module=FakeMediaPipe,
            timestamp_provider=lambda: 1.0,
        )
        frame = np.zeros((1, 1, 3), dtype=np.uint8)

        detector.process_frame(frame)
        detector.process_frame(frame)

        self.assertEqual([call[1] for call in landmarker.detect_calls], [1, 2])

    def test_close_releases_landmarker_resources(self):
        landmarker = FakeLandmarker(landmarks=[])
        detector = FaceMeshDetector(
            landmarker=landmarker,
            mediapipe_module=FakeMediaPipe,
        )

        detector.close()

        self.assertTrue(landmarker.closed)


if __name__ == "__main__":
    unittest.main()
