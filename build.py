"""PyInstaller build script for LazyScroll AI.

Usage:
    python build.py

Creates a --onedir distribution in dist/LazyScrollAI/ containing the
executable, bundled model, and a writable config folder.
"""

import shutil
import subprocess
import sys
from pathlib import Path
import argparse


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_FILE = PROJECT_ROOT / "models" / "face_landmarker.task"
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.json"
DIST_DIR = PROJECT_ROOT / "dist" / "LazyScrollAI"


def build(console: bool = False) -> int:
    if not MODEL_FILE.is_file():
        print(f"Error: model file not found: {MODEL_FILE}")
        print(
            "Download face_landmarker.task from:\n"
            "  https://storage.googleapis.com/mediapipe-models/"
            "face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
        )
        return 1

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name", "LazyScrollAI",
        "--onedir",
        "--noconfirm",
        "--console" if console else "--noconsole",
        "--hidden-import=mediapipe.tasks.c",
        "--collect-binaries=mediapipe.tasks.c",
        f"--add-data={MODEL_FILE}{_sep()}models",
        str(PROJECT_ROOT / "main.py"),
    ]

    print("Running PyInstaller...")
    print(f"  {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        print("Error: PyInstaller build failed.")
        return result.returncode

    # Copy config next to the exe so settings are writable and persist.
    dist_config_dir = DIST_DIR / "config"
    dist_config_dir.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.is_file():
        shutil.copy2(CONFIG_FILE, dist_config_dir / "settings.json")
        print(f"Copied config to {dist_config_dir}")

    print(f"\nBuild complete: {DIST_DIR}")
    print(f"Run the app:   {DIST_DIR / 'LazyScrollAI.exe'}")
    return 0


def _sep() -> str:
    """Return the PyInstaller --add-data separator for the current OS."""
    return ";" if sys.platform == "win32" else ":"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build LazyScroll AI with PyInstaller.")
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build with a console window for startup debugging.",
    )
    args = parser.parse_args()
    raise SystemExit(build(console=args.console))
