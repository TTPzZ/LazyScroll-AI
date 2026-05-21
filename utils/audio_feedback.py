from collections.abc import Callable

from control.scroll_constants import (
    ACTION_START_AUTO_SCROLL,
    ACTION_STOP_AUTO_SCROLL,
    ACTION_TOGGLE_ENABLED,
)
from vision.blink_calibration import CALIBRATION_ACTION_SAVED


class AudioFeedback:
    """Plays small local system beeps for important runtime actions."""

    def __init__(
        self,
        enabled: bool = True,
        beep_fn: Callable[[int, int], None] | None = None,
    ) -> None:
        self.enabled = enabled
        self._beep_fn = beep_fn or self._system_beep

    def notify_action(self, action: str, enabled: bool | None = None) -> None:
        if not self.enabled:
            return

        for frequency, duration in self._pattern_for_action(action, enabled):
            self._beep_fn(frequency, duration)

    @staticmethod
    def _pattern_for_action(
        action: str,
        enabled: bool | None,
    ) -> list[tuple[int, int]]:
        if action == ACTION_TOGGLE_ENABLED:
            return [(880, 80)] if enabled else [(440, 80)]

        if action == ACTION_START_AUTO_SCROLL:
            return [(660, 60)]

        if action == ACTION_STOP_AUTO_SCROLL:
            return [(330, 60)]

        if action == CALIBRATION_ACTION_SAVED:
            return [(880, 60), (1040, 60)]

        return []

    @staticmethod
    def _system_beep(frequency: int, duration: int) -> None:
        try:
            import winsound

            winsound.Beep(frequency, duration)
        except Exception:
            print("\a", end="")
