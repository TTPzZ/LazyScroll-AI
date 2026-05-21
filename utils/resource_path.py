"""Resolve resource paths for both source and PyInstaller frozen modes."""

import sys
from pathlib import Path


def _base_dir() -> Path:
    """Return the base directory for bundled resources.

    In dev mode: the project root directory.
    In frozen (PyInstaller) mode: sys._MEIPASS.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    return Path(__file__).resolve().parents[1]


def resource_path(relative: str) -> Path:
    """Resolve a resource path relative to the project/bundle root."""
    return _base_dir() / relative


def app_dir() -> Path:
    """Return the writable application directory.

    In dev mode this is the project root. In frozen mode this is the
    executable directory, which is the right place for logs and mutable
    config in the --onedir build.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return _base_dir()


def config_dir() -> Path:
    """Return the writable config directory.

    In dev mode: project_root/config/
    In frozen mode: directory next to the .exe so settings persist across runs.
    """
    if getattr(sys, "frozen", False):
        return app_dir() / "config"

    return _base_dir() / "config"


def model_path() -> Path:
    """Return the path to the face_landmarker.task model file."""
    return resource_path("models/face_landmarker.task")


def log_path() -> Path:
    """Return the startup/runtime log path."""
    return app_dir() / "lazyscroll.log"
