import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.resource_path import _base_dir, app_dir, config_dir, log_path, model_path, resource_path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ResourcePathTests(unittest.TestCase):
    def test_dev_mode_base_dir_returns_project_root(self) -> None:
        self.assertEqual(_base_dir(), PROJECT_ROOT)

    def test_frozen_mode_base_dir_returns_meipass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            meipass = str(Path(temp_dir) / "_internal")
            with patch.object(sys, "frozen", True, create=True):
                with patch.object(sys, "_MEIPASS", meipass, create=True):
                    self.assertEqual(_base_dir(), Path(meipass))

    def test_resource_path_resolves_relative_in_dev_mode(self) -> None:
        self.assertEqual(
            resource_path("models/face_landmarker.task"),
            PROJECT_ROOT / "models" / "face_landmarker.task",
        )

    def test_resource_path_resolves_relative_in_frozen_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            meipass = str(Path(temp_dir) / "_internal")
            with patch.object(sys, "frozen", True, create=True):
                with patch.object(sys, "_MEIPASS", meipass, create=True):
                    self.assertEqual(
                        resource_path("models/face_landmarker.task"),
                        Path(meipass) / "models" / "face_landmarker.task",
                    )

    def test_config_dir_returns_project_config_in_dev_mode(self) -> None:
        self.assertEqual(config_dir(), PROJECT_ROOT / "config")

    def test_app_dir_returns_project_root_in_dev_mode(self) -> None:
        self.assertEqual(app_dir(), PROJECT_ROOT)

    def test_config_dir_returns_exe_sibling_in_frozen_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_exe = Path(temp_dir) / "dist" / "LazyScrollAI.exe"
            fake_exe.parent.mkdir(parents=True, exist_ok=True)
            fake_exe.touch()
            with patch.object(sys, "frozen", True, create=True):
                with patch.object(sys, "executable", str(fake_exe)):
                    with patch.object(sys, "_MEIPASS", str(Path(temp_dir) / "_internal"), create=True):
                        self.assertEqual(config_dir(), fake_exe.parent / "config")

    def test_log_path_is_next_to_exe_in_frozen_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_exe = Path(temp_dir) / "dist" / "LazyScrollAI.exe"
            fake_exe.parent.mkdir(parents=True, exist_ok=True)
            fake_exe.touch()
            with patch.object(sys, "frozen", True, create=True):
                with patch.object(sys, "executable", str(fake_exe)):
                    self.assertEqual(log_path(), fake_exe.parent / "lazyscroll.log")

    def test_model_path_returns_face_landmarker_path(self) -> None:
        result = model_path()

        self.assertEqual(result, PROJECT_ROOT / "models" / "face_landmarker.task")
        self.assertEqual(result.name, "face_landmarker.task")


if __name__ == "__main__":
    unittest.main()
