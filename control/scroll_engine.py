from collections.abc import Callable
import time

from vision.gaze_detector import DOUBLE_BLINK, LONG_BLINK, SINGLE_BLINK


ACTION_SCROLL_DOWN = "SCROLL_DOWN"
ACTION_START_AUTO_SCROLL = "START_AUTO_SCROLL"
ACTION_STOP_AUTO_SCROLL = "STOP_AUTO_SCROLL"
ACTION_TOGGLE_ENABLED = "TOGGLE_ENABLED"
ACTION_DISABLED = "DISABLED"
ACTION_NO_ACTION = "NO_ACTION"


class ScrollEngine:
    """Maps blink gestures to safe, non-blocking mouse-wheel scrolling."""

    def __init__(
        self,
        enabled: bool = False,
        auto_scroll: bool = False,
        scroll_amount_per_step: int = -120,
        scroll_interval_ms: int = 120,
        scroll_fn: Callable[[int], None] | None = None,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        self.enabled = enabled
        self.auto_scroll = auto_scroll if enabled else False
        self.scroll_amount_per_step = scroll_amount_per_step
        self.scroll_interval_ms = scroll_interval_ms
        self._scroll_fn = scroll_fn or self.pyautogui_scroll
        self._time_provider = time_provider or (lambda: time.monotonic() * 1000)
        self._last_scroll_step_ms: int | None = None

    def handle_gesture(
        self,
        gesture: str,
        timestamp_ms: int | None = None,
    ) -> str:
        if gesture == LONG_BLINK:
            self.enabled = not self.enabled
            if not self.enabled:
                self._stop_auto_scroll()
            return ACTION_TOGGLE_ENABLED

        if not self.enabled:
            self._stop_auto_scroll()
            return ACTION_DISABLED if gesture == DOUBLE_BLINK else ACTION_NO_ACTION

        if gesture == DOUBLE_BLINK:
            if self.auto_scroll:
                self._stop_auto_scroll()
                return ACTION_STOP_AUTO_SCROLL

            self.auto_scroll = True
            self._last_scroll_step_ms = None
            return ACTION_START_AUTO_SCROLL

        if gesture == SINGLE_BLINK and self.auto_scroll:
            self._stop_auto_scroll()
            return ACTION_STOP_AUTO_SCROLL

        return ACTION_NO_ACTION

    def update(self, timestamp_ms: int | None = None) -> str:
        timestamp_ms = int(timestamp_ms if timestamp_ms is not None else self._time_provider())

        if not self.enabled:
            if self.auto_scroll:
                self._stop_auto_scroll()
                return ACTION_DISABLED
            return ACTION_NO_ACTION

        if not self.auto_scroll:
            return ACTION_NO_ACTION

        if not self._is_scroll_due(timestamp_ms):
            return ACTION_NO_ACTION

        self._scroll_fn(self.scroll_amount_per_step)
        self._last_scroll_step_ms = timestamp_ms
        return ACTION_SCROLL_DOWN

    @staticmethod
    def pyautogui_scroll(amount: int) -> None:
        import pyautogui

        pyautogui.scroll(amount)

    def _is_scroll_due(self, timestamp_ms: int) -> bool:
        return (
            self._last_scroll_step_ms is None
            or timestamp_ms - self._last_scroll_step_ms >= self.scroll_interval_ms
        )

    def _stop_auto_scroll(self) -> None:
        self.auto_scroll = False
        self._last_scroll_step_ms = None
