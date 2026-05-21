from dataclasses import dataclass
from typing import Any

import cv2

from control.scroll_engine import ACTION_NO_ACTION
from vision.gaze_detector import NO_GESTURE


OVERLAY_MODE_NORMAL = "normal"
OVERLAY_MODE_MINIMAL = "minimal"
OVERLAY_MODE_HIDDEN = "hidden"
OVERLAY_MODES = (
    OVERLAY_MODE_NORMAL,
    OVERLAY_MODE_MINIMAL,
    OVERLAY_MODE_HIDDEN,
)


@dataclass(frozen=True)
class DebugOverlaySnapshot:
    enabled: bool
    auto_scroll: bool
    direction: str
    speed_preset: str
    current_gesture: str
    current_action: str
    last_gesture: str
    last_action: str
    calibration_status: str = ""
    overlay_mode: str = OVERLAY_MODE_NORMAL


class DebugOverlay:
    """Draws the lightweight OpenCV debug overlay for manual testing."""

    def __init__(
        self,
        hold_ms: int = 1500,
        mode: str = OVERLAY_MODE_NORMAL,
    ) -> None:
        self.hold_ms = hold_ms
        self.mode = mode if mode in OVERLAY_MODES else OVERLAY_MODE_NORMAL
        self._last_gesture = NO_GESTURE
        self._last_action = ACTION_NO_ACTION
        self._last_event_ms: int | None = None

    def cycle_mode(self) -> str:
        index = OVERLAY_MODES.index(self.mode)
        self.mode = OVERLAY_MODES[(index + 1) % len(OVERLAY_MODES)]
        return self.mode

    def record_event(
        self,
        gesture: str,
        action: str,
        timestamp_ms: int,
    ) -> None:
        if gesture == NO_GESTURE and action == ACTION_NO_ACTION:
            return

        if gesture != NO_GESTURE:
            self._last_gesture = gesture

        if action != ACTION_NO_ACTION:
            self._last_action = action

        self._last_event_ms = timestamp_ms

    def snapshot(
        self,
        enabled: bool,
        auto_scroll: bool,
        direction: str,
        speed_preset: str,
        current_gesture: str,
        current_action: str,
        timestamp_ms: int,
        calibration_status: str = "",
        overlay_mode: str | None = None,
    ) -> DebugOverlaySnapshot:
        last_gesture = NO_GESTURE
        last_action = ACTION_NO_ACTION
        if (
            self._last_event_ms is not None
            and timestamp_ms - self._last_event_ms <= self.hold_ms
        ):
            last_gesture = self._last_gesture
            last_action = self._last_action

        return DebugOverlaySnapshot(
            enabled=enabled,
            auto_scroll=auto_scroll,
            direction=direction,
            speed_preset=speed_preset,
            current_gesture=current_gesture,
            current_action=current_action,
            last_gesture=last_gesture,
            last_action=last_action,
            calibration_status=calibration_status,
            overlay_mode=overlay_mode or self.mode,
        )

    def draw(self, frame: Any, snapshot: DebugOverlaySnapshot) -> None:
        if not hasattr(frame, "shape"):
            return

        lines = self._lines(snapshot)
        if not lines:
            return

        width = 430
        height = 26 + (len(lines) * 24)
        cv2.rectangle(frame, (8, 8), (width, height), (0, 0, 0), -1)

        y = 34
        for line in lines:
            cv2.putText(
                frame,
                line,
                (18, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            y += 24

    @staticmethod
    def _lines(snapshot: DebugOverlaySnapshot) -> list[str]:
        if snapshot.overlay_mode == OVERLAY_MODE_HIDDEN:
            return []

        if snapshot.overlay_mode == OVERLAY_MODE_MINIMAL:
            enabled = "ON" if snapshot.enabled else "OFF"
            scroll = (
                f"SCROLL {snapshot.direction}"
                if snapshot.auto_scroll
                else "IDLE"
            )
            return [f"{enabled} | {scroll} | {snapshot.speed_preset}"]

        lines = [
            f"enabled: {str(snapshot.enabled).lower()}",
            f"auto_scroll: {str(snapshot.auto_scroll).lower()}",
            f"direction: {snapshot.direction}",
            f"speed: {snapshot.speed_preset}",
            f"current gesture: {snapshot.current_gesture}",
            f"last gesture: {snapshot.last_gesture}",
            f"last action: {snapshot.last_action}",
        ]
        if (
            snapshot.calibration_status
            and snapshot.calibration_status != "Calibration: idle"
        ):
            lines.append(f"calibration: {snapshot.calibration_status}")

        return lines
