from collections.abc import Callable
import time


class FrameRateLimiter:
    """Small non-OpenCV FPS limiter for the preview loop."""

    def __init__(
        self,
        fps_limit: int = 30,
        time_provider: Callable[[], float] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.fps_limit = fps_limit
        self._time_provider = time_provider or (lambda: time.monotonic() * 1000)
        self._sleep_fn = sleep_fn or (lambda milliseconds: time.sleep(milliseconds / 1000))
        self._last_frame_ms: float | None = None

    def wait(self) -> None:
        if self.fps_limit <= 0:
            return

        now_ms = float(self._time_provider())
        if self._last_frame_ms is None:
            self._last_frame_ms = now_ms
            return

        frame_interval_ms = 1000 / self.fps_limit
        elapsed_ms = now_ms - self._last_frame_ms
        if elapsed_ms < frame_interval_ms:
            self._sleep_fn(frame_interval_ms - elapsed_ms)
            now_ms = float(self._time_provider())

        self._last_frame_ms = now_ms
