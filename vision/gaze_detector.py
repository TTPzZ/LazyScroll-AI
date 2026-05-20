from collections.abc import Callable
import time


SINGLE_BLINK = "SINGLE_BLINK"
DOUBLE_BLINK = "DOUBLE_BLINK"
LONG_BLINK = "LONG_BLINK"
NO_GESTURE = "NO_GESTURE"


class BlinkGestureDetector:
    """Detects blink gestures from eye openness transitions."""

    def __init__(
        self,
        closed_threshold: float = 0.18,
        double_blink_window_ms: int = 800,
        long_blink_ms: int = 700,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        # Temporary Phase 4 default. Full calibration belongs to a later phase.
        self.closed_threshold = closed_threshold
        self.double_blink_window_ms = double_blink_window_ms
        self.long_blink_ms = long_blink_ms
        self._time_provider = time_provider or (lambda: time.monotonic() * 1000)
        self._was_closed = False
        self._closed_started_ms: int | None = None
        self._long_blink_emitted = False
        self._pending_single_blink_ms: int | None = None

    def update(
        self, eye_open: float | None, timestamp_ms: int | None = None
    ) -> tuple[str, bool]:
        timestamp_ms = int(timestamp_ms if timestamp_ms is not None else self._time_provider())

        if eye_open is None:
            self._reset()
            return NO_GESTURE, False

        closed = float(eye_open) < self.closed_threshold
        if closed:
            return self._handle_closed(timestamp_ms)

        gesture, closed = self._handle_open(timestamp_ms)
        if gesture != NO_GESTURE:
            return gesture, closed

        return self._confirm_pending_single_blink(timestamp_ms)

    def _handle_closed(self, timestamp_ms: int) -> tuple[str, bool]:
        if not self._was_closed:
            if self._pending_single_has_expired(timestamp_ms):
                self._pending_single_blink_ms = None
            self._was_closed = True
            self._closed_started_ms = timestamp_ms
            self._long_blink_emitted = False

        if (
            self._closed_started_ms is not None
            and not self._long_blink_emitted
            and timestamp_ms - self._closed_started_ms >= self.long_blink_ms
        ):
            self._long_blink_emitted = True
            self._pending_single_blink_ms = None
            return LONG_BLINK, True

        return NO_GESTURE, True

    def _handle_open(self, timestamp_ms: int) -> tuple[str, bool]:
        if not self._was_closed:
            return NO_GESTURE, False

        closed_started_ms = self._closed_started_ms
        closed_duration_ms = (
            timestamp_ms - closed_started_ms
            if closed_started_ms is not None
            else 0
        )
        long_blink_already_emitted = self._long_blink_emitted
        self._was_closed = False
        self._closed_started_ms = None
        self._long_blink_emitted = False

        if long_blink_already_emitted:
            return NO_GESTURE, False

        if closed_duration_ms >= self.long_blink_ms:
            self._pending_single_blink_ms = None
            return LONG_BLINK, False

        if self._is_second_blink(timestamp_ms):
            self._pending_single_blink_ms = None
            return DOUBLE_BLINK, False

        self._pending_single_blink_ms = timestamp_ms
        return NO_GESTURE, False

    def _is_second_blink(self, timestamp_ms: int) -> bool:
        return (
            self._pending_single_blink_ms is not None
            and timestamp_ms - self._pending_single_blink_ms <= self.double_blink_window_ms
        )

    def _confirm_pending_single_blink(self, timestamp_ms: int) -> tuple[str, bool]:
        if self._pending_single_has_expired(timestamp_ms):
            self._pending_single_blink_ms = None
            return SINGLE_BLINK, False

        return NO_GESTURE, False

    def _pending_single_has_expired(self, timestamp_ms: int) -> bool:
        return (
            self._pending_single_blink_ms is not None
            and timestamp_ms - self._pending_single_blink_ms > self.double_blink_window_ms
        )

    def _reset(self) -> None:
        self._was_closed = False
        self._closed_started_ms = None
        self._long_blink_emitted = False
        self._pending_single_blink_ms = None
