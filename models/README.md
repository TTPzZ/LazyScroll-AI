# MediaPipe Models

Place the MediaPipe Face Landmarker task model here:

```text
models/face_landmarker.task
```

Download command for PowerShell:

```powershell
New-Item -ItemType Directory -Force models
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task" -OutFile "models/face_landmarker.task"
```

The app loads this local file at runtime. It does not download models automatically.
