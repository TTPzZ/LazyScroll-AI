# Codex Prompts for LazyScroll AI

## Phase 0 + 1 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Follow the project rules strictly.

Start with Phase 0 and Phase 1 only:
- create the project structure
- create requirements.txt
- implement webcam preview using OpenCV
- keep main.py minimal
- do not implement MediaPipe yet
- do not build UI yet
- do not add unrelated features

After coding, explain:
1. files created/changed
2. how to run
3. expected result
```

## Phase 2 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Continue with Phase 2 only:
- implement MediaPipe Face Mesh detection
- create vision/face_mesh.py
- draw face landmarks on webcam preview
- keep code modular
- do not implement scrolling yet
- do not build UI yet

After coding, explain:
1. files changed
2. how to run
3. expected result
```

## Phase 3 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Continue with Phase 3 only:
- implement iris tracking in vision/iris_tracker.py
- calculate iris vertical position relative to the eye region
- print left, right, and average y_ratio
- do not implement scrolling yet
- do not build UI yet

After coding, explain:
1. files changed
2. how to run
3. expected result
```

## Phase 4 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Continue with Phase 4 only:
- implement gaze direction detection in vision/gaze_detector.py
- support LOOK_UP, LOOK_CENTER, LOOK_DOWN, UNKNOWN
- use threshold-based detection
- print current gaze state
- do not implement scrolling yet
- do not build UI yet

After coding, explain:
1. files changed
2. how to run
3. expected result
```

## Phase 5 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Continue with Phase 5 only:
- implement smoothing in utils/smoothing.py
- add moving average
- add hold duration logic
- add cooldown logic
- keep behavior configurable
- do not build UI yet

After coding, explain:
1. files changed
2. how to run
3. expected result
```

## Phase 6 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Continue with Phase 6 only:
- implement scroll engine in control/scroll_engine.py
- use PyAutoGUI only for mouse wheel scrolling
- LOOK_DOWN scrolls down
- LOOK_UP scrolls up
- LOOK_CENTER and UNKNOWN stop
- do not click, type, drag, or perform destructive actions
- do not build UI yet

After coding, explain:
1. files changed
2. how to run
3. expected result
```

## Phase 7 Prompt

```txt
Read README.md, PLAN.md, and AGENTS.md first.

Continue with Phase 7 only:
- implement hotkey toggle in control/hotkeys.py
- use Ctrl + Alt + S to enable/disable LazyScroll
- print enabled/disabled status
- do not build UI yet

After coding, explain:
1. files changed
2. how to run
3. expected result
```
