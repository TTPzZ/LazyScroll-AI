from dataclasses import dataclass
import threading

from control.scroll_constants import (
    ACTION_NO_ACTION,
    DIRECTION_NONE,
)
from vision.gaze_detector import NO_GESTURE


@dataclass(frozen=True)
class RuntimeSnapshot:
    enabled: bool
    auto_scroll: bool
    direction: str
    speed_preset: str
    last_gesture: str
    last_action: str


class RuntimeState:
    """Small locked state shared by the vision and scroll loops."""

    def __init__(
        self,
        enabled: bool = False,
        auto_scroll: bool = False,
        direction: str = DIRECTION_NONE,
        speed_preset: str = "normal",
        last_gesture: str = NO_GESTURE,
        last_action: str = ACTION_NO_ACTION,
    ) -> None:
        self._lock = threading.Lock()
        self._enabled = enabled
        self._auto_scroll = auto_scroll
        self._direction = direction if auto_scroll else DIRECTION_NONE
        self._speed_preset = speed_preset
        self._last_gesture = last_gesture
        self._last_action = last_action

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return RuntimeSnapshot(
                enabled=self._enabled,
                auto_scroll=self._auto_scroll,
                direction=self._direction,
                speed_preset=self._speed_preset,
                last_gesture=self._last_gesture,
                last_action=self._last_action,
            )

    def update(
        self,
        *,
        enabled: bool | None = None,
        auto_scroll: bool | None = None,
        direction: str | None = None,
        speed_preset: str | None = None,
        last_gesture: str | None = None,
        last_action: str | None = None,
    ) -> RuntimeSnapshot:
        with self._lock:
            if enabled is not None:
                self._enabled = enabled
            if auto_scroll is not None:
                self._auto_scroll = auto_scroll
            if direction is not None:
                self._direction = direction
            if speed_preset is not None:
                self._speed_preset = speed_preset
            if last_gesture is not None:
                self._last_gesture = last_gesture
            if last_action is not None:
                self._last_action = last_action

            if not self._auto_scroll:
                self._direction = DIRECTION_NONE

            return RuntimeSnapshot(
                enabled=self._enabled,
                auto_scroll=self._auto_scroll,
                direction=self._direction,
                speed_preset=self._speed_preset,
                last_gesture=self._last_gesture,
                last_action=self._last_action,
            )
