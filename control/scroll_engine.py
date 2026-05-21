from collections.abc import Callable
import time

from control.runtime_state import RuntimeSnapshot, RuntimeState
from control.scroll_constants import (
    ACTION_AUTO_SCROLL_TIMEOUT,
    ACTION_DISABLED,
    ACTION_NO_ACTION,
    ACTION_SCROLL_DOWN,
    ACTION_SCROLL_UP,
    ACTION_START_AUTO_SCROLL,
    ACTION_STOP_AUTO_SCROLL,
    ACTION_TOGGLE_ENABLED,
    DIRECTION_DOWN,
    DIRECTION_NONE,
    DIRECTION_UP,
)
from vision.gaze_detector import (
    DOUBLE_BLINK,
    LONG_BLINK,
    NO_GESTURE,
    SINGLE_BLINK,
    TRIPLE_BLINK,
)


class ScrollEngine:
    """Maps blink gestures to safe, non-blocking mouse-wheel scrolling."""

    def __init__(
        self,
        enabled: bool = False,
        auto_scroll: bool = False,
        direction: str = DIRECTION_NONE,
        down_scroll_amount_per_step: int = -120,
        up_scroll_amount_per_step: int = 120,
        scroll_interval_ms: int = 120,
        auto_scroll_timeout_ms: int = 20000,
        speed_preset: str = "normal",
        speed_presets: dict[str, dict[str, int]] | None = None,
        runtime_state: RuntimeState | None = None,
        scroll_fn: Callable[[int], None] | None = None,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        self._state = runtime_state or RuntimeState(
            enabled=enabled,
            auto_scroll=auto_scroll if enabled else False,
            direction=direction if auto_scroll and enabled else DIRECTION_NONE,
            speed_preset=speed_preset,
        )
        self.down_scroll_amount_per_step = down_scroll_amount_per_step
        self.up_scroll_amount_per_step = up_scroll_amount_per_step
        self.scroll_interval_ms = scroll_interval_ms
        self.auto_scroll_timeout_ms = auto_scroll_timeout_ms
        self.speed_presets = speed_presets or {}
        self._scroll_fn = scroll_fn or self.pyautogui_scroll
        self._time_provider = time_provider or (lambda: time.monotonic() * 1000)
        self._last_scroll_step_ms: int | None = None
        self._auto_scroll_started_ms: int | None = None

    @property
    def enabled(self) -> bool:
        return self._state.snapshot().enabled

    @property
    def auto_scroll(self) -> bool:
        return self._state.snapshot().auto_scroll

    @property
    def direction(self) -> str:
        return self._state.snapshot().direction

    @property
    def speed_preset(self) -> str:
        return self._state.snapshot().speed_preset

    def snapshot(self) -> RuntimeSnapshot:
        return self._state.snapshot()

    def handle_gesture(
        self,
        gesture: str,
        timestamp_ms: int | None = None,
    ) -> str:
        timestamp_ms = int(timestamp_ms if timestamp_ms is not None else self._time_provider())

        if gesture == LONG_BLINK:
            self._record_event(gesture, None)
            return self.toggle_enabled()

        if not self.snapshot().enabled:
            self._stop_auto_scroll()
            action = (
                ACTION_DISABLED
                if gesture in (DOUBLE_BLINK, TRIPLE_BLINK)
                else ACTION_NO_ACTION
            )
            self._record_event(gesture, action)
            return action

        if gesture == SINGLE_BLINK:
            if self.snapshot().auto_scroll:
                action = self.stop_auto_scroll()
                self._record_event(gesture, action)
                return action
            self._record_event(gesture, ACTION_NO_ACTION)
            return ACTION_NO_ACTION

        if gesture == DOUBLE_BLINK:
            action = self._toggle_auto_scroll(DIRECTION_DOWN, timestamp_ms)
            self._record_event(gesture, action)
            return action

        if gesture == TRIPLE_BLINK:
            action = self._toggle_auto_scroll(DIRECTION_UP, timestamp_ms)
            self._record_event(gesture, action)
            return action

        return ACTION_NO_ACTION

    def update(self, timestamp_ms: int | None = None) -> str:
        timestamp_ms = int(timestamp_ms if timestamp_ms is not None else self._time_provider())
        snapshot = self.snapshot()

        if not snapshot.enabled:
            if snapshot.auto_scroll:
                self._stop_auto_scroll()
                self._record_event(None, ACTION_DISABLED)
                return ACTION_DISABLED
            return ACTION_NO_ACTION

        if not snapshot.auto_scroll:
            return ACTION_NO_ACTION

        if self._is_auto_scroll_timed_out(timestamp_ms):
            self._stop_auto_scroll()
            self._record_event(None, ACTION_AUTO_SCROLL_TIMEOUT)
            return ACTION_AUTO_SCROLL_TIMEOUT

        if not self._is_scroll_due(timestamp_ms):
            return ACTION_NO_ACTION

        if snapshot.direction == DIRECTION_UP:
            self._scroll_fn(self.up_scroll_amount_per_step)
            self._last_scroll_step_ms = timestamp_ms
            self._record_event(None, ACTION_SCROLL_UP)
            return ACTION_SCROLL_UP

        if snapshot.direction == DIRECTION_DOWN:
            self._scroll_fn(self.down_scroll_amount_per_step)
            self._last_scroll_step_ms = timestamp_ms
            self._record_event(None, ACTION_SCROLL_DOWN)
            return ACTION_SCROLL_DOWN

        self._stop_auto_scroll()
        return ACTION_NO_ACTION

    @staticmethod
    def pyautogui_scroll(amount: int) -> None:
        import pyautogui

        pyautogui.scroll(amount)

    def toggle_enabled(self) -> str:
        enabled = not self.snapshot().enabled
        self._state.update(enabled=enabled)
        if not enabled:
            self._stop_auto_scroll()
        self._record_event(None, ACTION_TOGGLE_ENABLED)
        return ACTION_TOGGLE_ENABLED

    def stop_auto_scroll(self) -> str:
        if not self.snapshot().auto_scroll:
            return ACTION_NO_ACTION

        self._stop_auto_scroll()
        self._record_event(None, ACTION_STOP_AUTO_SCROLL)
        return ACTION_STOP_AUTO_SCROLL

    def set_speed_preset(self, preset_name: str) -> str:
        preset = self.speed_presets.get(preset_name)
        if preset is None:
            return ACTION_NO_ACTION

        self._state.update(speed_preset=preset_name)
        self.down_scroll_amount_per_step = int(preset["down_scroll_amount_per_step"])
        self.up_scroll_amount_per_step = int(preset["up_scroll_amount_per_step"])
        self.scroll_interval_ms = int(preset["scroll_interval_ms"])
        action = f"SET_SPEED_{preset_name.upper()}"
        self._record_event(None, action)
        return action

    def _toggle_auto_scroll(self, direction: str, timestamp_ms: int) -> str:
        snapshot = self.snapshot()
        if snapshot.auto_scroll and snapshot.direction == direction:
            return self.stop_auto_scroll()

        self._state.update(auto_scroll=True, direction=direction)
        self._last_scroll_step_ms = None
        self._auto_scroll_started_ms = timestamp_ms
        return ACTION_START_AUTO_SCROLL

    def _is_scroll_due(self, timestamp_ms: int) -> bool:
        return (
            self._last_scroll_step_ms is None
            or timestamp_ms - self._last_scroll_step_ms >= self.scroll_interval_ms
        )

    def _stop_auto_scroll(self) -> None:
        self._state.update(auto_scroll=False, direction=DIRECTION_NONE)
        self._last_scroll_step_ms = None
        self._auto_scroll_started_ms = None

    def _is_auto_scroll_timed_out(self, timestamp_ms: int) -> bool:
        return (
            self.auto_scroll_timeout_ms > 0
            and self._auto_scroll_started_ms is not None
            and timestamp_ms - self._auto_scroll_started_ms >= self.auto_scroll_timeout_ms
        )

    def _record_event(self, gesture: str | None, action: str | None) -> None:
        updates: dict[str, str] = {}
        if gesture is not None and gesture != NO_GESTURE:
            updates["last_gesture"] = gesture
        if action is not None and action != ACTION_NO_ACTION:
            updates["last_action"] = action

        if updates:
            self._state.update(**updates)
