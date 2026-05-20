# LazyScroll AI - Implementation Plan

## Project Goal

LazyScroll AI is a PC desktop application that uses webcam-based eye tracking to control scrolling.

Main behavior:

- Look down → scroll down
- Look up → scroll up
- Look center → stop scrolling
- Hotkey → enable/disable the system
- User can adjust scroll speed and sensitivity

The project must start as a simple MVP before adding UI and advanced features.

---

# Phase 0 - Project Setup

## Goal

Create the base Python project structure.

## Tasks

1. Create folder structure:

```text
lazyscroll-ai/
├── main.py
├── requirements.txt
├── README.md
├── PLAN.md
├── AGENTS.md
├── camera/
├── vision/
├── control/
├── config/
├── utils/
└── ui/
```

2. Create `requirements.txt`:

```txt
opencv-python
mediapipe
numpy
pyautogui
keyboard
pyside6
pyinstaller
```

3. Add empty `__init__.py` files where needed.

4. Do not build UI yet.

## Expected Result

The project structure exists and dependencies are listed.

---

# Phase 1 - Webcam Preview

## Goal

Open webcam and display realtime video.

## Tasks

1. Implement `camera/webcam.py`
2. Create a `Webcam` class.
3. Support:
   - open camera
   - read frame
   - release camera
4. In `main.py`, show webcam preview using OpenCV.
5. Press `q` to quit.

## Expected Result

Running:

```bash
python main.py
```

shows webcam feed.

---

# Phase 2 - Face Mesh Detection

## Goal

Detect face landmarks using MediaPipe Face Mesh.

## Tasks

1. Implement `vision/face_mesh.py`
2. Create a `FaceMeshDetector` class.
3. Input: OpenCV frame
4. Output:
   - processed frame
   - face landmarks
5. Draw landmarks for debugging.

## Expected Result

Webcam preview shows face/eye landmarks.

---

# Phase 3 - Iris Tracking

## Goal

Extract iris and eye landmark positions.

## Tasks

1. Implement `vision/iris_tracker.py`
2. Extract landmarks for:
   - left eye
   - right eye
   - left iris
   - right iris
3. Calculate iris vertical position relative to eye height.

## Output Example

```python
{
    "left_eye_y_ratio": 0.52,
    "right_eye_y_ratio": 0.50,
    "average_y_ratio": 0.51
}
```

## Expected Result

Terminal prints current eye Y ratio in realtime.

---

# Phase 4 - Gaze Direction Detection

## Goal

Classify eye direction.

## Tasks

1. Implement `vision/gaze_detector.py`
2. Create gaze states:

```python
LOOK_UP
LOOK_CENTER
LOOK_DOWN
UNKNOWN
```

3. Use simple thresholds first:

```python
if y_ratio < up_threshold:
    LOOK_UP
elif y_ratio > down_threshold:
    LOOK_DOWN
else:
    LOOK_CENTER
```

4. Print gaze state in terminal.

## Expected Result

Terminal shows:

```text
LOOK_UP
LOOK_CENTER
LOOK_DOWN
```

---

# Phase 5 - Smoothing and Noise Filtering

## Goal

Prevent unstable gaze detection.

## Tasks

1. Implement `utils/smoothing.py`
2. Add moving average buffer.
3. Smooth the eye Y ratio before classification.
4. Add hold duration logic:
   - user must look up/down for at least 0.5s before triggering action
5. Add cooldown:
   - after action starts/stops, wait briefly before changing state

## Expected Result

Gaze state becomes stable and does not flicker too much.

---

# Phase 6 - Scroll Engine

## Goal

Control desktop scrolling.

## Tasks

1. Implement `control/scroll_engine.py`
2. Use PyAutoGUI to scroll.
3. Support:
   - scroll up
   - scroll down
   - stop
   - configurable speed
4. Do not scroll if app is disabled.

## Expected Logic

```python
if enabled:
    if gaze_state == "LOOK_DOWN":
        scroll_down()
    elif gaze_state == "LOOK_UP":
        scroll_up()
    else:
        stop_scroll()
```

## Expected Result

Looking down scrolls the active window down.

---

# Phase 7 - Hotkey Toggle

## Goal

Allow user to enable/disable LazyScroll quickly.

## Tasks

1. Implement `control/hotkeys.py`
2. Add hotkey:

```text
Ctrl + Alt + S
```

3. Toggle app enabled/disabled.
4. Print current status.

## Expected Result

User can pause/resume auto scroll anytime.

---

# Phase 8 - Configuration Files

## Goal

Save settings and calibration data.

## Tasks

1. Create `config/settings.json`
2. Create `config/calibration.json`

## Example `settings.json`

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

## Example `calibration.json`

```json
{
  "up_threshold": 0.38,
  "down_threshold": 0.62,
  "center_y": 0.50
}
```

3. Implement config load/save utility.

---

# Phase 9 - Calibration System

## Goal

Allow user to calibrate eye thresholds.

## Tasks

1. Implement `vision/calibration.py`
2. Ask user to look:
   - center
   - up
   - down
3. Record average Y ratio for each state.
4. Save thresholds to `config/calibration.json`.

## Expected Result

Detection adapts to the user's webcam, face angle, and eye shape.

---

# Phase 10 - Minimal Desktop UI

## Goal

Build a simple PySide6 control panel.

## Tasks

1. Implement `ui/main_window.py`
2. UI should include:
   - Start / Stop button
   - Current gaze state
   - Scroll speed slider
   - Sensitivity slider
   - Calibration button
   - Debug camera preview toggle

## Important

Do not build UI before the core logic works.

---

# Phase 11 - Packaging

## Goal

Build executable file.

## Tasks

1. Test app normally:

```bash
python main.py
```

2. Build with PyInstaller:

```bash
pyinstaller --onefile main.py
```

3. Test `.exe`.

---

# Development Order

Follow this order strictly:

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
11. Build EXE

Do not skip phases.
Do not build advanced features before MVP works.
