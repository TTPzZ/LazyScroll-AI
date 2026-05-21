"""System tray icon for LazyScroll AI using pystray."""

import logging
import threading
from typing import Any

from ui.preview_state import PreviewState


def _create_icon_image() -> Any:
    """Create a simple 64x64 programmatic tray icon with Pillow."""
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Eye shape — blue oval
    draw.ellipse([4, 16, 60, 48], fill=(41, 128, 185), outline=(52, 152, 219), width=2)

    # Green iris
    draw.ellipse([22, 22, 42, 42], fill=(39, 174, 96), outline=(46, 204, 113), width=1)

    # Dark pupil
    draw.ellipse([28, 28, 36, 36], fill=(44, 62, 80))

    # White highlight
    draw.ellipse([30, 26, 34, 30], fill=(255, 255, 255, 200))

    return img


class TrayIcon:
    """Lightweight system tray icon for LazyScroll AI.

    Provides Show/Hide Preview, Enable/Disable Scrolling, and Quit
    menu items.  Runs the pystray event loop in a daemon thread so
    the main camera loop is not blocked.
    """

    def __init__(
        self,
        stop_event: threading.Event,
        scroll_engine: Any,
        preview_state: PreviewState,
        pystray_module: Any | None = None,
        icon_image: Any | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._stop_event = stop_event
        self._scroll_engine = scroll_engine
        self._preview_state = preview_state
        self._pystray = pystray_module
        self._icon_image = icon_image
        self._logger = logger or logging.getLogger("lazyscroll")
        self._icon: Any | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._icon is not None

    def start(self) -> None:
        """Start the tray icon in a daemon thread."""
        pystray = self._pystray or self._import_pystray()

        image = self._icon_image or _create_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem(
                "Show/Hide Preview",
                self._on_toggle_preview,
            ),
            pystray.MenuItem(
                "Enable/Disable Scrolling",
                self._on_toggle_enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                self._on_quit,
            ),
        )

        self._icon = pystray.Icon(
            name="lazyscroll_ai",
            icon=image,
            title="LazyScroll AI",
            menu=menu,
        )
        icon = self._icon

        self._thread = threading.Thread(
            target=self._run_icon,
            args=(icon,),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def update_tooltip(self, text: str) -> None:
        """Update the tray icon tooltip text."""
        if self._icon is not None:
            self._icon.title = text

    def _on_toggle_preview(self, *args: Any) -> None:
        self._preview_state.toggle()

    def _on_toggle_enabled(self, *args: Any) -> None:
        self._scroll_engine.toggle_enabled()

    def _on_quit(self, *args: Any) -> None:
        self._stop_event.set()
        self.stop()

    def _run_icon(self, icon: Any) -> None:
        try:
            icon.run()
        except Exception:
            self._logger.warning("Tray runtime failed", exc_info=True)
            self._icon = None

    @staticmethod
    def _import_pystray() -> Any:
        import pystray

        return pystray
