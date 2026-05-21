# LazyScroll AI

Webcam-based eye tracking desktop app for hands-free scrolling using blink gestures.

LazyScroll AI runs locally on your PC. It watches your eyes through a webcam, detects blink patterns, and scrolls the active window automatically. No cloud services, no accounts — just your camera and your blinks.

## How It Works

```text
Webcam Capture
    ↓
MediaPipe Face Mesh (landmark detection)
    ↓
Eye Openness Tracking (eyelid distance ratio)
    ↓
Blink Gesture Detection (single / double / triple / long)
    ↓
Auto-Scroll Engine
```

| Gesture | Action |
|---------|--------|
| Double blink | Start/stop scroll down |
| Triple blink | Start/stop scroll up |
| Single blink | Stop scrolling |
| Long blink (~700ms) | Toggle enable/disable |

## Setup

```bash
pip install -r requirements.txt
```

### Model Download

Download `face_landmarker.task` from:

```
https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
```

Place it in `models/face_landmarker.task`.

## Run

```bash
python main.py
```

A preview window opens showing the webcam feed with debug overlay. Blink to control scrolling.

## Controls

### Blink Gestures

| Gesture | Action |
|---------|--------|
| Double blink | Start/stop scroll down |
| Triple blink | Start/stop scroll up |
| Single blink | Stop scrolling |
| Long blink (~700ms) | Toggle enable/disable |

### Keyboard Shortcuts (preview window focused)

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `p` | Toggle preview visibility |
| `e` | Toggle enable/disable |
| `s` | Stop auto-scroll |
| `k` | Start blink calibration |
| `o` | Cycle overlay mode (normal / minimal / hidden) |
| `1` | Slow speed preset |
| `2` | Normal speed preset |
| `3` | Fast speed preset |
| `d` | Simulate double blink |
| `t` | Simulate triple blink |
| `l` | Simulate long blink |

## System Tray

- A system tray icon appears on startup (disable with `tray_enabled: false` in settings)
- Tray menu options: Show/Hide Preview, Enable/Disable Scrolling, Quit
- Closing the preview window (X button) minimizes to tray instead of quitting (when tray is enabled)
- Press `q` to fully quit the application
- Set `start_minimized: true` in `settings.json` to launch with the preview hidden

## Configuration

Settings are stored in `config/settings.json`. The file is auto-created with defaults if missing.

### Key Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `closed_threshold` | Eye openness ratio below which a blink is detected | `0.18` |
| `scroll_interval_ms` | Milliseconds between scroll steps | `120` |
| `speed_preset` | Active speed preset (`slow` / `normal` / `fast`) | `normal` |
| `overlay_mode` | Debug overlay mode (`normal` / `minimal` / `hidden`) | `normal` |
| `start_minimized` | Start with preview hidden | `false` |
| `tray_enabled` | Show system tray icon | `true` |
| `auto_scroll_timeout_ms` | Auto-stop scrolling after this duration | `20000` |
| `preview_fps_limit` | Max preview frame rate | `30` |
| `audio_feedback` | Play beep sounds on blink events | `true` |

### Speed Presets

| Preset | Scroll Amount | Interval |
|--------|--------------|----------|
| Slow | 80 | 180ms |
| Normal | 120 | 120ms |
| Fast | 220 | 70ms |

## Build Executable

```bash
python build.py
```

Creates `dist/LazyScrollAI/` folder with the executable. Requires the model file to be present in `models/`. Uses `--onedir` mode for MediaPipe compatibility.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Webcam not found | Check camera connection, try different `camera_index` in code |
| No face detected | Ensure good lighting, face the camera directly |
| Blink not detected | Run calibration (`k` key), adjust `closed_threshold` in settings |
| Model file not found | Download `face_landmarker.task` to `models/` folder |
| Tray icon not showing | Install pystray and Pillow: `pip install pystray Pillow` |

## Performance Tips

- Hide preview (`p` key or tray menu) to reduce CPU usage
- Use `overlay_mode: hidden` for less rendering work
- Lower `preview_fps_limit` in settings (default: 30)
- Reduce `preview_width` / `preview_height` for a smaller preview window

## Tech Stack

- **Python** — core language
- **OpenCV** — webcam capture and image display
- **MediaPipe Face Mesh** — face landmark detection
- **NumPy** — numerical operations
- **PyAutoGUI** — scroll automation
- **pystray** — system tray icon
- **Pillow** — tray icon image
- **PyInstaller** — executable packaging

## Project Structure

```text
lazyscroll-ai/
├── main.py                     # App entry point and main loop
├── build.py                    # PyInstaller build script
├── requirements.txt
├── models/
│   └── face_landmarker.task    # MediaPipe model (downloaded separately)
├── camera/
│   └── webcam.py               # Webcam capture wrapper
├── vision/
│   ├── face_mesh.py            # MediaPipe Face Mesh integration
│   ├── iris_tracker.py         # Iris and eyelid tracking, blink detection
│   ├── gaze_detector.py        # Gaze direction classification
│   └── blink_calibration.py    # Blink threshold calibration
├── control/
│   ├── scroll_engine.py        # Scroll logic and speed presets
│   ├── scroll_loop.py          # Threaded scroll loop
│   ├── scroll_constants.py     # Scroll direction constants
│   ├── runtime_state.py        # Thread-safe runtime state
│   └── runtime_manager.py      # Blink event → action routing
├── utils/
│   ├── config_loader.py        # JSON config loading with deep merge
│   ├── debug_overlay.py        # On-screen debug info rendering
│   ├── audio_feedback.py       # System beep sounds
│   ├── frame_rate.py           # Frame rate limiter
│   ├── preview_frame.py        # Preview frame utilities
│   └── resource_path.py        # Path resolution for dev/frozen modes
├── ui/
│   ├── tray.py                 # System tray icon (pystray)
│   └── preview_state.py        # Preview window visibility state
├── config/
│   └── settings.json           # App settings (auto-created)
└── tests/                      # Unit tests for all modules
```

## License

MIT
