import unittest

from camera.webcam import Webcam


class FakeCapture:
    def __init__(self, opened=True, frames=None):
        self.opened = opened
        self.frames = list(frames or [])
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True
        self.opened = False


class WebcamTests(unittest.TestCase):
    def test_open_uses_camera_index_and_reports_success(self):
        created_indexes = []

        def capture_factory(index):
            created_indexes.append(index)
            return FakeCapture(opened=True)

        webcam = Webcam(camera_index=2, capture_factory=capture_factory)

        self.assertTrue(webcam.open())
        self.assertEqual(created_indexes, [2])
        self.assertTrue(webcam.is_open)

    def test_open_reports_failure_when_camera_is_unavailable(self):
        webcam = Webcam(capture_factory=lambda index: FakeCapture(opened=False))

        self.assertFalse(webcam.open())
        self.assertFalse(webcam.is_open)

    def test_read_frame_returns_frame_when_camera_is_open(self):
        frame = object()
        webcam = Webcam(capture_factory=lambda index: FakeCapture(frames=[frame]))
        webcam.open()

        success, result = webcam.read_frame()

        self.assertTrue(success)
        self.assertIs(result, frame)

    def test_read_frame_fails_gracefully_before_open(self):
        webcam = Webcam(capture_factory=lambda index: FakeCapture(frames=[object()]))

        success, frame = webcam.read_frame()

        self.assertFalse(success)
        self.assertIsNone(frame)

    def test_release_closes_camera(self):
        capture = FakeCapture(opened=True)
        webcam = Webcam(capture_factory=lambda index: capture)
        webcam.open()

        webcam.release()

        self.assertTrue(capture.released)
        self.assertFalse(webcam.is_open)


if __name__ == "__main__":
    unittest.main()
