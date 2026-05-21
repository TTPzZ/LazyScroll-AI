import threading
import unittest
from typing import Any
from unittest.mock import MagicMock

from ui.preview_state import PreviewState
from ui.tray import TrayIcon, _create_icon_image


class FakeScrollEngine:
    def __init__(self) -> None:
        self.toggle_enabled_calls = 0

    def toggle_enabled(self) -> str:
        self.toggle_enabled_calls += 1
        return "TOGGLE_ENABLED"


class FakePystray:
    class MenuItem:
        def __init__(self, text: str, callback: Any) -> None:
            self.text = text
            self.callback = callback

    class Menu:
        SEPARATOR = "---"

        def __init__(self, *items: Any) -> None:
            self.items = items

    class Icon:
        def __init__(self, name: str, icon: Any, title: str, menu: Any) -> None:
            self.name = name
            self.icon = icon
            self.title = title
            self.menu = menu
            self.running = False

        def run(self) -> None:
            self.running = True

        def stop(self) -> None:
            self.running = False


class FailingRunPystray(FakePystray):
    class Icon(FakePystray.Icon):
        def run(self) -> None:
            raise RuntimeError("tray loop failed")


class TrayIconTests(unittest.TestCase):
    def test_create_icon_image_returns_64_square_rgba_image(self) -> None:
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")

        image = _create_icon_image()

        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.size, (64, 64))
        self.assertEqual(image.mode, "RGBA")

    def test_start_creates_icon(self) -> None:
        tray = self._make_tray()[0]

        tray.start()

        self.assertTrue(tray.running)
        tray.stop()

    def test_running_false_before_start(self) -> None:
        tray = self._make_tray()[0]

        self.assertFalse(tray.running)

    def test_toggle_preview_changes_state(self) -> None:
        tray, _, _, preview = self._make_tray()

        tray._on_toggle_preview(None, None)
        self.assertFalse(preview.visible)
        tray._on_toggle_preview(None, None)
        self.assertTrue(preview.visible)

    def test_toggle_enabled_calls_engine(self) -> None:
        tray, _, engine, _ = self._make_tray()

        tray._on_toggle_enabled(None, None)

        self.assertEqual(engine.toggle_enabled_calls, 1)

    def test_quit_sets_stop_event(self) -> None:
        tray, stop_event, _, _ = self._make_tray()
        tray.start()

        tray._on_quit()

        self.assertTrue(stop_event.is_set())
        self.assertFalse(tray.running)

    def test_update_tooltip(self) -> None:
        tray = self._make_tray()[0]
        tray.start()

        tray.update_tooltip("Scrolling DOWN")

        self.assertEqual(tray._icon.title, "Scrolling DOWN")
        tray.stop()

    def test_update_tooltip_noop_when_not_running(self) -> None:
        tray = self._make_tray()[0]

        tray.update_tooltip("test")

    def test_stop_clears_icon(self) -> None:
        tray = self._make_tray()[0]
        tray.start()

        tray.stop()

        self.assertFalse(tray.running)

    def test_double_stop_is_safe(self) -> None:
        tray = self._make_tray()[0]
        tray.start()

        tray.stop()
        tray.stop()

    def test_callbacks_accept_pystray_arguments(self) -> None:
        tray, stop_event, engine, preview = self._make_tray()

        tray._on_toggle_preview("icon", "item")
        tray._on_toggle_enabled("icon", "item")
        tray._on_quit("icon", "item")

        self.assertFalse(preview.visible)
        self.assertEqual(engine.toggle_enabled_calls, 1)
        self.assertTrue(stop_event.is_set())

    def test_tray_runtime_failure_is_logged(self) -> None:
        stop_event = threading.Event()
        logger = MagicMock()
        tray = TrayIcon(
            stop_event=stop_event,
            scroll_engine=FakeScrollEngine(),
            preview_state=PreviewState(visible=True),
            pystray_module=FailingRunPystray(),
            icon_image=MagicMock(),
            logger=logger,
        )

        tray.start()
        self.assertIsNotNone(tray._thread)
        tray._thread.join(timeout=1.0)

        logger.warning.assert_called_once()
        self.assertFalse(tray.running)

    def _make_tray(self) -> tuple[TrayIcon, threading.Event, FakeScrollEngine, PreviewState]:
        stop_event = threading.Event()
        engine = FakeScrollEngine()
        preview = PreviewState(visible=True)
        tray = TrayIcon(
            stop_event=stop_event,
            scroll_engine=engine,
            preview_state=preview,
            pystray_module=FakePystray(),
            icon_image=MagicMock(),
        )
        return tray, stop_event, engine, preview


if __name__ == "__main__":
    unittest.main()
