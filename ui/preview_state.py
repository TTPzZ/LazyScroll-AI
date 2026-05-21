"""Thread-safe preview window visibility state."""

import threading


class PreviewState:
    """Tracks whether the OpenCV preview window should be visible.

    Used by both the main loop and the tray menu to coordinate
    preview visibility without race conditions.
    """

    def __init__(self, visible: bool = True) -> None:
        self._lock = threading.Lock()
        self._visible = visible

    @property
    def visible(self) -> bool:
        with self._lock:
            return self._visible

    def set_visible(self, visible: bool) -> None:
        with self._lock:
            self._visible = visible

    def toggle(self) -> bool:
        """Toggle visibility and return the new value."""
        with self._lock:
            self._visible = not self._visible
            return self._visible
