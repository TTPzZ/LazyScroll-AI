# AGENTS.md - LazyScroll AI Coding Rules

## Project Identity

This project is called LazyScroll AI.

It is a PC desktop application that uses webcam-based eye tracking to control scrolling.

Main goal:

```text
Look down → scroll down
Look up → scroll up
Look center → stop scrolling
```

The project is an experimental local desktop app. It must run locally and must not depend on cloud services.

---

# Core Tech Stack

Use only the following technologies unless explicitly instructed otherwise:

## Language

- Python

## Computer Vision

- OpenCV
- MediaPipe Face Mesh

## Math / Processing

- NumPy

## Desktop Automation

- PyAutoGUI

## Hotkey

- keyboard

## UI

- PySide6

## Packaging

- PyInstaller

Do not replace these technologies without permission.

---

# Architecture Rules

The project must follow this structure:

```text
lazyscroll-ai/
├── main.py
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

Do not put all code into `main.py`.

`main.py` should only coordinate modules.

---

# Development Rules

## 1. Follow the implementation plan

Always follow `PLAN.md`.

Do not skip phases.

Current development priority:

1. Webcam
2. Face Mesh
3. Iris Tracking
4. Gaze Detection
5. Smoothing
6. Scroll Engine
7. Hotkey
8. Config
9. Calibration
10. UI
11. Packaging

Do not build advanced features before the MVP works.

---

## 2. Keep MVP simple

The first working version only needs:

- webcam input
- eye direction detection
- up / center / down classification
- auto scroll
- hotkey toggle

Do not implement:

- deep learning custom model
- cloud API
- user accounts
- database
- mobile app
- browser extension
- complex UI
- multi-monitor support

unless explicitly requested.

---

## 3. Do not invent unrelated features

Do not add random features such as:

- login system
- online dashboard
- analytics cloud
- AI chatbot
- server backend
- Firebase
- MongoDB
- REST API
- authentication
- payment
- update system

This is a local desktop computer vision project.

---

# Gaze Detection Rules

## Main detection method

Use iris position relative to the eye region.

Do not rely primarily on head pose.

Reason:

```text
Head pose is unstable for this use case.
Iris-relative position is better for detecting up/down gaze.
```

---

## Gaze States

Use these states only:

```python
LOOK_UP = "LOOK_UP"
LOOK_CENTER = "LOOK_CENTER"
LOOK_DOWN = "LOOK_DOWN"
UNKNOWN = "UNKNOWN"
```

Do not create unnecessary extra states during MVP.

---

## Detection Logic

Basic logic:

```python
if y_ratio < up_threshold:
    state = LOOK_UP
elif y_ratio > down_threshold:
    state = LOOK_DOWN
else:
    state = LOOK_CENTER
```

Use calibration values if available.

Fallback to default thresholds if calibration file does not exist.

---

# Noise Filtering Rules

Eye tracking is noisy.

Always include:

- smoothing
- hold duration
- cooldown

Do not trigger scroll immediately from a single frame.

Recommended behavior:

```text
User must look up/down continuously for around 500-1000ms before scrolling starts.
```

---

# Scroll Rules

Use PyAutoGUI for scrolling.

Expected behavior:

```text
LOOK_DOWN → scroll down
LOOK_UP → scroll up
LOOK_CENTER → stop
UNKNOWN → stop
```

Do not click, type, drag, or perform destructive actions.

Only scrolling is allowed in MVP.

---

# Safety Rules

The app must never:

- send webcam data to the internet
- save raw camera frames by default
- upload user data
- control keyboard typing
- click buttons automatically
- delete files
- access private documents
- run shell commands without explicit reason

Camera processing must stay local.

---

# Config Rules

Use JSON config files.

## `settings.json`

Stores app behavior:

```json
{
  "enabled": false,
  "scroll_speed": 5,
  "scroll_interval_ms": 80,
  "hold_duration_ms": 700,
  "cooldown_ms": 300,
  "debug": true
}
```

## `calibration.json`

Stores user gaze thresholds:

```json
{
  "up_threshold": 0.38,
  "down_threshold": 0.62,
  "center_y": 0.50
}
```

If config files are missing, create them with default values.

---

# Code Style Rules

Write clean, readable Python.

Use:

- classes for major components
- type hints where useful
- small functions
- clear variable names
- comments only when helpful

Avoid:

- huge functions
- hidden side effects
- global state everywhere
- magic numbers without config
- duplicate logic

---

# Error Handling Rules

Handle common errors gracefully:

- webcam not found
- no face detected
- no iris detected
- config file missing
- invalid config value

If face is not detected:

```text
state = UNKNOWN
scroll = stop
```

Do not crash.

---

# Debugging Rules

During MVP, debug output is allowed.

Useful debug info:

```text
current gaze state
raw y ratio
smoothed y ratio
scroll enabled/disabled
face detected true/false
```

Do not spam excessive logs every frame unless debug mode is enabled.

---

# UI Rules

Do not build UI until core logic works.

When UI is added, it should include only:

- Start / Stop
- current gaze state
- scroll speed slider
- sensitivity slider
- calibration button
- camera preview toggle

Do not overdesign UI.

---

# Packaging Rules

Use PyInstaller only after app works with:

```bash
python main.py
```

Do not focus on `.exe` packaging before MVP is stable.

---

# Forbidden Changes

Do not change project direction to:

- mobile app
- web app
- browser extension
- server-client system
- cloud AI system
- deep learning training project

unless explicitly instructed.

---

# Agent Behavior

When modifying code:

1. Read `README.md`
2. Read `PLAN.md`
3. Read `AGENTS.md`
4. Identify current phase
5. Modify only files related to current phase
6. Keep changes small
7. Explain what changed
8. Mention how to test

Do not rewrite the entire project unless requested.

---

# Testing Instruction

After each phase, provide a simple test command:

```bash
python main.py
```

Also explain expected behavior.

Example:

```text
Expected:
- Webcam window opens
- Face landmarks appear
- Terminal prints LOOK_UP / LOOK_CENTER / LOOK_DOWN
```

---

# Final Principle

Build the simplest working LazyScroll AI first.

Working MVP is more important than beautiful architecture.

Do not be fancy too early.
