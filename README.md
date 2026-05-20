LazyScroll AI

Eye-controlled auto scrolling for PC using webcam + gaze tracking.

LazyScroll AI là một ứng dụng desktop sử dụng webcam để theo dõi hướng nhìn của mắt người dùng và tự động thực hiện thao tác cuộn màn hình (scroll) mà không cần chạm chuột hoặc bàn phím.

Dự án được xây dựng nhằm:

nghiên cứu computer vision realtime
thử nghiệm eye tracking
cải thiện trải nghiệm đọc/lướt nội dung handsfree
tạo một hệ thống gaze-controlled interaction đơn giản nhưng thực tế
Ý tưởng dự án

Khi người dùng nhìn xuống cạnh dưới màn hình trong một khoảng thời gian nhất định:

→ ứng dụng tự động cuộn xuống

Khi nhìn lên cạnh trên màn hình:

→ ứng dụng cuộn ngược lên

Khi nhìn ở giữa:

→ dừng cuộn

Ứng dụng hoạt động bằng cách:

sử dụng webcam để quan sát mắt
detect khuôn mặt + iris
tính toán hướng nhìn
phân loại trạng thái mắt
trigger thao tác scroll tương ứng
Mục tiêu MVP

Phiên bản đầu tiên cần đạt được:

 Webcam realtime
 Face tracking
 Eye/Iris detection
 Detect UP / DOWN / CENTER
 Auto scroll bằng mắt
 Adjustable scroll speed
 Toggle enable/disable
 Calibration cơ bản
 Hotkey bật/tắt
Workflow hệ thống
Webcam
↓
OpenCV Capture
↓
MediaPipe Face Mesh
↓
Eye Landmark Extraction
↓
Iris Position Calculation
↓
Gaze Direction Detection
↓
Noise Filtering / Smoothing
↓
Action Trigger System
↓
Auto Scroll Engine
↓
OS Mouse Scroll
Cách hoạt động
1. Camera Input

Ứng dụng mở webcam realtime bằng OpenCV.

Mỗi frame sẽ được:

resize
convert color
đưa vào MediaPipe để detect face mesh
2. Face Mesh Detection

MediaPipe FaceMesh detect:

khuôn mặt
mắt
iris
facial landmarks

Model trả về:

~468 facial landmarks
tọa độ mắt theo thời gian thực
3. Gaze Detection

Ứng dụng tính:

vị trí iris tương đối trong mắt
hướng nhìn theo trục Y

Ví dụ:

Iris gần mí trên  → LOOK_UP
Iris gần giữa     → LOOK_CENTER
Iris gần mí dưới  → LOOK_DOWN
4. Calibration

Người dùng nhìn lần lượt:

lên trên
giữa
xuống dưới

Hệ thống lưu threshold riêng cho từng người.

Ví dụ:

{
  "up_threshold": 0.34,
  "center_threshold": 0.50,
  "down_threshold": 0.68
}
5. Noise Filtering

Mắt người luôn:

rung nhẹ
liếc
chớp mắt
thay đổi liên tục

Do đó hệ thống cần:

smoothing
moving average
hold duration
cooldown trigger

để tránh scroll sai.

6. Action Engine

Khi gaze state được xác định:

LOOK_DOWN
→ scroll xuống

LOOK_UP
→ scroll lên

LOOK_CENTER
→ stop scrolling
Công nghệ sử dụng
Ngôn ngữ
Python

Lý do:

phát triển nhanh
nhiều thư viện AI/computer vision
phù hợp prototype realtime
Computer Vision
OpenCV

Dùng cho:

webcam capture
image processing
frame rendering
debug visualization
MediaPipe

Thành phần quan trọng nhất dự án.

Sử dụng:

Face Mesh
Iris Tracking

Để:

detect mắt
detect iris
facial landmark tracking realtime
Data Processing
NumPy

Dùng:

smoothing
averaging
vector calculation
threshold processing
Automation
PyAutoGUI

Dùng để:

simulate mouse wheel scrolling
điều khiển hệ điều hành

Ví dụ:

pyautogui.scroll(-100)
Keyboard Hotkey
keyboard

Dùng:

bật/tắt ứng dụng
pause scrolling
debug mode
Desktop UI
PySide6

Dùng xây:

settings window
calibration UI
preview window
control panel
Build Tool
PyInstaller

Dùng đóng gói:

.exe
standalone desktop app
Cấu trúc dự án đề xuất
lazyscroll-ai/
│
├── main.py
│
├── camera/
│   └── webcam.py
│
├── vision/
│   ├── face_mesh.py
│   ├── iris_tracker.py
│   ├── gaze_detector.py
│   └── calibration.py
│
├── control/
│   ├── scroll_engine.py
│   ├── gesture_controller.py
│   └── hotkeys.py
│
├── ui/
│   ├── main_window.py
│   ├── calibration_window.py
│   └── settings_panel.py
│
├── config/
│   ├── settings.json
│   └── calibration.json
│
├── utils/
│   ├── smoothing.py
│   ├── math_utils.py
│   └── logger.py
│
└── assets/
Trạng thái mắt

Hệ thống hiện tại hỗ trợ:

LOOK_UP
LOOK_DOWN
LOOK_CENTER
UNKNOWN

Trong tương lai có thể thêm:

blink detection
wink gesture
attention tracking
sleep detection
Logic trigger

Ví dụ:

if gaze_state == "DOWN":
    scroll_down()

elif gaze_state == "UP":
    scroll_up()

else:
    stop_scroll()
Chống trigger lỗi

Để tránh scroll loạn:

Hold Duration

Người dùng phải nhìn xuống trong:

0.5s – 1.0s

mới bắt đầu scroll.

Cooldown

Sau mỗi lần đổi hướng:

delay ngắn

để tránh spam action.

Smoothing

Dùng moving average để:

giảm jitter
giảm nhiễu webcam
ổn định gaze detection
UI dự kiến
Main Control Panel
Start / Stop
Webcam preview
Current gaze state
Scroll speed slider
Sensitivity slider
Calibration button
Debug overlay toggle
Roadmap phát triển
Phase 1 — Basic Detection
webcam
face mesh
iris tracking
detect UP/DOWN
Phase 2 — Scroll Integration
auto scroll
cooldown
smoothing
Phase 3 — Calibration System
user calibration
threshold saving
Phase 4 — Desktop UI
settings
preview
controls
Phase 5 — Advanced Features
blink gestures
adaptive AI calibration
heatmap
focus tracking
multi-monitor support
Tính năng tương lai
Attention Tracking

Hiển thị:

người dùng đang tập trung hay không
thời gian nhìn màn hình
Reading Mode

Auto scroll ổn định khi đọc:

manga
webtoon
tài liệu
PDF
TikTok / Reels Mode

Handsfree scrolling:

short video
social feed
infinite scroll
Performance Goals

Mục tiêu realtime:

30–60 FPS
Low latency
Stable gaze detection
Giới hạn hiện tại

Dự án hiện:

chưa dùng deep learning custom
chưa hỗ trợ precise gaze coordinate
chưa hỗ trợ mobile
phụ thuộc ánh sáng webcam
Định hướng kỹ thuật

Dự án ưu tiên:

lightweight
realtime
local processing
không cần cloud
không cần GPU mạnh
Mục tiêu dài hạn

Biến LazyScroll AI thành:

nền tảng gaze interaction
accessibility tool
handsfree navigation system
experimental HCI project
Dev Notes
Không sử dụng head pose làm nguồn chính

Head pose dễ:

nhiễu
sai khi cúi đầu

Hệ thống ưu tiên:

iris relative position

để detect gaze ổn định hơn.

Recommended Dependencies
pip install:
opencv-python
mediapipe
numpy
pyautogui
keyboard
pyside6
pyinstaller
Example Runtime Flow
Start Application
↓
Open Webcam
↓
Detect Face
↓
Track Iris
↓
Calculate Gaze
↓
Apply Smoothing
↓
Determine Eye State
↓
Trigger Scroll Action
↓
Update UI
Project Status
Current Stage:
Planning / Architecture Design
License

Experimental personal project.