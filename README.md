# LazyScroll AI

Eye-controlled auto scrolling for PC using webcam + gaze tracking.

LazyScroll AI is a local desktop application that uses a webcam to detect the user's eye direction and automatically scroll the active window.

## Main Idea

- Look down → scroll down
- Look up → scroll up
- Look center → stop scrolling
- Hotkey → enable/disable scrolling
- User can adjust scroll speed and sensitivity

## Core Workflow

```text
Webcam
↓
OpenCV Capture
↓
MediaPipe Face Mesh
↓
Eye / Iris Landmark Extraction
↓
Iris Position Calculation
↓
Gaze Direction Detection
↓
Noise Filtering / Smoothing
↓
Action Trigger System
↓
PyAutoGUI Scroll
```

## Tech Stack

- Python
- OpenCV
- MediaPipe Face Mesh
- NumPy
- PyAutoGUI
- keyboard
- PySide6
- PyInstaller

## Project Structure

```text
lazyscroll-ai/
├── main.py
├── requirements.txt
├── README.md
├── PLAN.md
├── AGENTS.md
├── camera/
│   └── webcam.py
├── vision/
│   ├── face_mesh.py
│   ├── iris_tracker.py
│   ├── gaze_detector.py
│   └── calibration.py
├── control/
│   ├── scroll_engine.py
│   └── hotkeys.py
├── config/
│   ├── settings.json
│   └── calibration.json
├── utils/
│   ├── smoothing.py
│   ├── config_loader.py
│   └── logger.py
└── ui/
    └── main_window.py
```

## MVP Scope

The first working version should only include:

- webcam preview
- face mesh detection
- iris tracking
- gaze classification: LOOK_UP / LOOK_CENTER / LOOK_DOWN / UNKNOWN
- smoothing
- hold duration
- cooldown
- PyAutoGUI scrolling
- hotkey toggle

Do not add cloud services, login, database, mobile app, or unrelated features during MVP.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Packaging

Only package after MVP works:

```bash
pyinstaller --onefile main.py
```
