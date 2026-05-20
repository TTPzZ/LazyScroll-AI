import unittest


class MediaPipeRuntimeTests(unittest.TestCase):
    def test_mediapipe_01035_exposes_tasks_api_without_solutions_dependency(self):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision

        self.assertEqual(mp.__version__, "0.10.35")
        self.assertFalse(hasattr(mp, "solutions"))
        self.assertTrue(hasattr(mp, "Image"))
        self.assertTrue(hasattr(mp.ImageFormat, "SRGB"))
        self.assertTrue(callable(BaseOptions))
        self.assertTrue(hasattr(vision, "FaceLandmarker"))
        self.assertTrue(hasattr(vision, "FaceLandmarkerOptions"))
        self.assertTrue(hasattr(vision, "FaceLandmarksConnections"))


if __name__ == "__main__":
    unittest.main()
