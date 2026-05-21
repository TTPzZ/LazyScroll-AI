from collections.abc import Callable
import threading
import time

from control.scroll_engine import ScrollEngine


def run_scroll_loop(
    scroll_engine: ScrollEngine,
    stop_event: threading.Event,
    sleep_interval_s: float = 0.01,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    """Run continuous scrolling independent of webcam and vision work."""
    while not stop_event.is_set():
        scroll_engine.update()
        sleep_fn(sleep_interval_s)
