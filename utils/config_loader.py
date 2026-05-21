from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from utils.resource_path import config_dir as _config_dir


DEFAULT_SETTINGS: dict[str, Any] = {
    "closed_threshold": 0.18,
    "multi_blink_window_ms": 800,
    "long_blink_ms": 700,
    "down_scroll_amount_per_step": -120,
    "up_scroll_amount_per_step": 120,
    "scroll_interval_ms": 120,
    "last_event_display_ms": 1500,
    "auto_scroll_timeout_ms": 20000,
    "speed_preset": "normal",
    "overlay_mode": "normal",
    "preview_width": 640,
    "preview_height": 480,
    "preview_fps_limit": 30,
    "audio_feedback": True,
    "max_frame_failures": 30,
    "start_minimized": False,
    "tray_enabled": True,
    "speed_presets": {
        "slow": {
            "down_scroll_amount_per_step": -80,
            "up_scroll_amount_per_step": 80,
            "scroll_interval_ms": 180,
        },
        "normal": {
            "down_scroll_amount_per_step": -120,
            "up_scroll_amount_per_step": 120,
            "scroll_interval_ms": 120,
        },
        "fast": {
            "down_scroll_amount_per_step": -220,
            "up_scroll_amount_per_step": 220,
            "scroll_interval_ms": 70,
        },
    },
}


DEFAULT_SETTINGS_PATH = _config_dir() / "settings.json"


def load_settings(path: str | Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    settings_path = Path(path)

    if not settings_path.exists():
        settings = deepcopy(DEFAULT_SETTINGS)
        _write_settings(settings_path, settings)
        return settings

    try:
        loaded_settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return deepcopy(DEFAULT_SETTINGS)

    if not isinstance(loaded_settings, dict):
        return deepcopy(DEFAULT_SETTINGS)

    return _merge_defaults(loaded_settings, DEFAULT_SETTINGS)


def merge_settings(settings: dict[str, Any]) -> dict[str, Any]:
    return _merge_defaults(settings, DEFAULT_SETTINGS)


def save_settings(
    settings: dict[str, Any],
    path: str | Path = DEFAULT_SETTINGS_PATH,
) -> None:
    settings_path = Path(path)
    _write_settings(settings_path, _merge_defaults(settings, DEFAULT_SETTINGS))


def _write_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _merge_defaults(
    loaded_settings: dict[str, Any],
    default_settings: dict[str, Any],
) -> dict[str, Any]:
    merged = deepcopy(default_settings)

    for key, value in loaded_settings.items():
        if (
            isinstance(value, dict)
            and isinstance(merged.get(key), dict)
        ):
            merged[key] = _merge_defaults(value, merged[key])
        else:
            merged[key] = value

    return merged
