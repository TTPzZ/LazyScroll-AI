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

    def test_load_settings_includes_start_minimized_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"

            settings = load_settings(path)

            self.assertIn("start_minimized", settings)
            self.assertFalse(settings["start_minimized"])

    def test_load_settings_includes_tray_enabled_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"

            settings = load_settings(path)

            self.assertIn("tray_enabled", settings)
            self.assertTrue(settings["tray_enabled"])

    def test_load_settings_preserves_existing_start_minimized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text(json.dumps({"start_minimized": True}), encoding="utf-8")

            settings = load_settings(path)

            self.assertTrue(settings["start_minimized"])

    def test_load_settings_preserves_existing_tray_enabled_false(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            path.write_text(json.dumps({"tray_enabled": False}), encoding="utf-8")

            settings = load_settings(path)

            self.assertFalse(settings["tray_enabled"])

    def test_default_settings_contains_phase11_keys(self):
        self.assertIn("start_minimized", DEFAULT_SETTINGS)
        self.assertIn("tray_enabled", DEFAULT_SETTINGS)
        self.assertFalse(DEFAULT_SETTINGS["start_minimized"])
        self.assertTrue(DEFAULT_SETTINGS["tray_enabled"])


if __name__ == "__main__":
    unittest.main()
