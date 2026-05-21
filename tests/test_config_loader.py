from pathlib import Path
import json
import tempfile
import unittest

from utils.config_loader import DEFAULT_SETTINGS, load_settings, save_settings


class ConfigLoaderTests(unittest.TestCase):
    def test_load_settings_creates_default_file_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"

            settings = load_settings(path)

            self.assertTrue(path.exists())
            self.assertEqual(settings["closed_threshold"], DEFAULT_SETTINGS["closed_threshold"])
            self.assertEqual(settings["speed_preset"], "normal")
            self.assertEqual(settings["overlay_mode"], "normal")
            self.assertEqual(settings["preview_width"], 640)
            self.assertEqual(settings["preview_height"], 480)
            self.assertEqual(settings["preview_fps_limit"], 30)
            self.assertTrue(settings["audio_feedback"])
            self.assertIn("slow", settings["speed_presets"])
            self.assertIn("normal", settings["speed_presets"])
            self.assertIn("fast", settings["speed_presets"])

    def test_load_settings_merges_missing_fields_with_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text(json.dumps({"closed_threshold": 0.2}), encoding="utf-8")

            settings = load_settings(path)

            self.assertEqual(settings["closed_threshold"], 0.2)
            self.assertEqual(settings["multi_blink_window_ms"], DEFAULT_SETTINGS["multi_blink_window_ms"])
            self.assertEqual(settings["auto_scroll_timeout_ms"], 20000)
            self.assertEqual(settings["overlay_mode"], "normal")
            self.assertEqual(settings["preview_width"], 640)

    def test_save_settings_persists_calibrated_closed_threshold(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            settings = load_settings(path)
            settings["closed_threshold"] = 0.23

            save_settings(settings, path)
            loaded_settings = load_settings(path)

            self.assertEqual(loaded_settings["closed_threshold"], 0.23)
            self.assertEqual(loaded_settings["speed_preset"], "normal")


if __name__ == "__main__":
    unittest.main()
