import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build


class BuildScriptTests(unittest.TestCase):
    def test_pyinstaller_command_uses_onedir_noconfirm_and_noconsole_by_default(self) -> None:
        commands = []

        def fake_run(command, cwd):
            commands.append((command, cwd))

            class Result:
                returncode = 0

            return Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model = root / "models" / "face_landmarker.task"
            config = root / "config" / "settings.json"
            model.parent.mkdir(parents=True)
            config.parent.mkdir(parents=True)
            model.write_bytes(b"model")
            config.write_text("{}", encoding="utf-8")

            with patch.object(build, "PROJECT_ROOT", root):
                with patch.object(build, "MODEL_FILE", model):
                    with patch.object(build, "CONFIG_FILE", config):
                        with patch.object(build, "DIST_DIR", root / "dist" / "LazyScrollAI"):
                            with patch.object(build.subprocess, "run", fake_run):
                                exit_code = build.build()

        self.assertEqual(exit_code, 0)
        command = commands[0][0]
        self.assertIn("--onedir", command)
        self.assertIn("--noconfirm", command)
        self.assertIn("--noconsole", command)
        self.assertNotIn("--console", command)
        self.assertIn("--hidden-import=mediapipe.tasks.c", command)
        self.assertIn("--collect-binaries=mediapipe.tasks.c", command)
        self.assertIn(str(root / "main.py"), command)

    def test_console_build_uses_console_option(self) -> None:
        commands = []

        def fake_run(command, cwd):
            commands.append((command, cwd))

            class Result:
                returncode = 0

            return Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model = root / "models" / "face_landmarker.task"
            config = root / "config" / "settings.json"
            model.parent.mkdir(parents=True)
            config.parent.mkdir(parents=True)
            model.write_bytes(b"model")
            config.write_text("{}", encoding="utf-8")

            with patch.object(build, "PROJECT_ROOT", root):
                with patch.object(build, "MODEL_FILE", model):
                    with patch.object(build, "CONFIG_FILE", config):
                        with patch.object(build, "DIST_DIR", root / "dist" / "LazyScrollAI"):
                            with patch.object(build.subprocess, "run", fake_run):
                                exit_code = build.build(console=True)

        self.assertEqual(exit_code, 0)
        command = commands[0][0]
        self.assertIn("--console", command)
        self.assertNotIn("--noconsole", command)


if __name__ == "__main__":
    unittest.main()
