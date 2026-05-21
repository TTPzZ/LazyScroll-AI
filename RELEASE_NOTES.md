# LazyScroll AI — Release Notes

## Prototype v0.1.0

Initial working prototype. Blink-gesture-based scrolling via webcam.

### Features Implemented

**Core Vision Pipeline**
- Webcam capture with OpenCV
- MediaPipe Face Mesh landmark detection (face_landmarker.task model)
- Iris and eyelid tracking with eye openness ratio calculation
- Gaze direction classification (up / center / down / unknown)

**Blink Gesture System**
- Single blink detection → stop scrolling
- Double blink detection → start/stop scroll down
- Triple blink detection → start/stop scroll up
- Long blink detection (~700ms) → toggle enable/disable
- Multi-blink window with configurable timing (800ms default)
- Blink calibration system (press `k` to calibrate closed_threshold)

**Scroll Engine**
- Auto-scroll with PyAutoGUI
- Speed presets: slow, normal, fast (keys `1`, `2`, `3`)
- Configurable scroll amount and interval per preset
- Auto-scroll timeout safety (20s default, prevents runaway scrolling)
- Scroll loop runs in a separate daemon thread

**User Interface**
- OpenCV preview window with camera feed
- Debug overlay with three modes: normal, minimal, hidden
- Last blink event display with timed fade
- System tray icon via pystray (show/hide preview, enable/disable, quit)
- Preview visibility toggle (hide to save CPU)
- Start minimized mode (launch with preview hidden)
- Close-to-tray behavior (X button minimizes instead of quitting)

**Feedback**
- Audio feedback via Windows system beeps (winsound)
- Visual feedback through debug overlay text

**Configuration**
- JSON config file (`config/settings.json`)
- Auto-created with defaults if missing
- Deep merge: user values preserved, new defaults added on update
- All thresholds, intervals, and presets are configurable

**Build & Distribution**
- PyInstaller build script (`python build.py`)
- `--onedir` mode for MediaPipe compatibility
- Resource path handling for both development and frozen (exe) modes
- Model file bundled via `--add-data`
- Config copied to dist folder for persistence

**Keyboard Shortcuts** (preview window focused)
- `q` quit, `p` toggle preview, `e` toggle enable, `s` stop scroll
- `k` calibrate, `o` cycle overlay, `1`/`2`/`3` speed presets
- `d`/`t`/`l` simulate double/triple/long blink (for testing)

### Architecture

- Modular package structure: `camera`, `vision`, `control`, `utils`, `ui`
- Thread-safe `RuntimeState` for shared state across threads
- `RuntimeManager` routes blink events to scroll actions
- Scroll loop runs in a separate daemon thread
- Tray icon runs in a separate daemon thread
- All major components accept injected dependencies for testability
- Frame rate limiter to cap CPU usage

### Known Limitations

- Audio feedback uses `winsound` (Windows only)
- Single webcam support only
- No PySide6 UI yet (OpenCV window used for preview, PySide6 GUI planned)
- PyInstaller packaging requires `--onedir` mode for MediaPipe to work
- Keyboard shortcuts only work when the preview window has focus (no global hotkeys yet)
- No auto-update mechanism
- No calibration persistence across sessions beyond `closed_threshold` in settings

### Testing

- 18 test files covering all modules
- Fake/mock injection pattern for unit tests (no real webcam needed)
- Tests cover: webcam, face mesh, iris tracker, gaze detector, blink calibration, scroll engine, scroll loop, runtime state, runtime manager, config loader, debug overlay, audio feedback, preview utilities
- Run tests: `python -m unittest discover -s tests`
