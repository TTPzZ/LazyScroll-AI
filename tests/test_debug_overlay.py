import unittest

import numpy as np

from control.scroll_engine import (
    ACTION_NO_ACTION,
    ACTION_SCROLL_DOWN,
    DIRECTION_DOWN,
)
from utils.debug_overlay import DebugOverlay
from utils.debug_overlay import (
    OVERLAY_MODE_HIDDEN,
    OVERLAY_MODE_MINIMAL,
    OVERLAY_MODE_NORMAL,
)
from vision.gaze_detector import DOUBLE_BLINK, NO_GESTURE


class DebugOverlayTests(unittest.TestCase):
    def test_keeps_last_gesture_and_action_visible_for_hold_duration(self):
        overlay = DebugOverlay(hold_ms=1500)

        overlay.record_event(DOUBLE_BLINK, ACTION_SCROLL_DOWN, timestamp_ms=1000)

        recent = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="normal",
            current_gesture=NO_GESTURE,
            current_action=ACTION_NO_ACTION,
            timestamp_ms=2400,
        )
        expired = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="normal",
            current_gesture=NO_GESTURE,
            current_action=ACTION_NO_ACTION,
            timestamp_ms=2601,
        )

        self.assertEqual(recent.last_gesture, DOUBLE_BLINK)
        self.assertEqual(recent.last_action, ACTION_SCROLL_DOWN)
        self.assertEqual(expired.last_gesture, NO_GESTURE)
        self.assertEqual(expired.last_action, ACTION_NO_ACTION)

    def test_draw_modifies_image_frame(self):
        overlay = DebugOverlay()
        frame = np.zeros((160, 320, 3), dtype=np.uint8)
        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="normal",
            current_gesture=DOUBLE_BLINK,
            current_action=ACTION_SCROLL_DOWN,
            timestamp_ms=1000,
        )

        overlay.draw(frame, snapshot)

        self.assertGreater(int(frame.sum()), 0)

    def test_snapshot_includes_calibration_status(self):
        overlay = DebugOverlay()

        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=False,
            direction="NONE",
            speed_preset="normal",
            current_gesture=NO_GESTURE,
            current_action=ACTION_NO_ACTION,
            timestamp_ms=1000,
            calibration_status="Calibration: close eyes",
        )

        self.assertEqual(snapshot.calibration_status, "Calibration: close eyes")
        self.assertIn("calibration: Calibration: close eyes", overlay._lines(snapshot))

    def test_idle_calibration_status_is_hidden(self):
        overlay = DebugOverlay()

        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=False,
            direction="NONE",
            speed_preset="normal",
            current_gesture=NO_GESTURE,
            current_action=ACTION_NO_ACTION,
            timestamp_ms=1000,
            calibration_status="Calibration: idle",
        )

        self.assertNotIn("calibration: Calibration: idle", overlay._lines(snapshot))

    def test_scroll_action_does_not_erase_last_detected_gesture(self):
        overlay = DebugOverlay(hold_ms=1500)

        overlay.record_event(DOUBLE_BLINK, ACTION_SCROLL_DOWN, timestamp_ms=1000)
        overlay.record_event(NO_GESTURE, ACTION_SCROLL_DOWN, timestamp_ms=1100)
        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="fast",
            current_gesture=NO_GESTURE,
            current_action=ACTION_SCROLL_DOWN,
            timestamp_ms=1200,
        )

        self.assertEqual(snapshot.last_gesture, DOUBLE_BLINK)
        self.assertEqual(snapshot.last_action, ACTION_SCROLL_DOWN)
        self.assertEqual(snapshot.speed_preset, "fast")

    def test_draw_ignores_non_image_frame(self):
        overlay = DebugOverlay()
        snapshot = overlay.snapshot(
            enabled=False,
            auto_scroll=False,
            direction="NONE",
            speed_preset="normal",
            current_gesture=NO_GESTURE,
            current_action=ACTION_NO_ACTION,
            timestamp_ms=1000,
        )

        overlay.draw("not-an-image", snapshot)

    def test_normal_overlay_mode_keeps_full_debug_lines(self):
        overlay = DebugOverlay()

        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="normal",
            current_gesture=DOUBLE_BLINK,
            current_action=ACTION_SCROLL_DOWN,
            timestamp_ms=1000,
            overlay_mode=OVERLAY_MODE_NORMAL,
        )

        lines = overlay._lines(snapshot)

        self.assertIn("enabled: true", lines)
        self.assertIn("current gesture: DOUBLE_BLINK", lines)

    def test_minimal_overlay_mode_shows_tiny_status_line_only(self):
        overlay = DebugOverlay()

        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="normal",
            current_gesture=DOUBLE_BLINK,
            current_action=ACTION_SCROLL_DOWN,
            timestamp_ms=1000,
            overlay_mode=OVERLAY_MODE_MINIMAL,
        )

        self.assertEqual(overlay._lines(snapshot), ["ON | SCROLL DOWN | normal"])

    def test_hidden_overlay_mode_draws_no_text(self):
        overlay = DebugOverlay()
        frame = np.zeros((160, 320, 3), dtype=np.uint8)
        snapshot = overlay.snapshot(
            enabled=True,
            auto_scroll=True,
            direction=DIRECTION_DOWN,
            speed_preset="normal",
            current_gesture=DOUBLE_BLINK,
            current_action=ACTION_SCROLL_DOWN,
            timestamp_ms=1000,
            overlay_mode=OVERLAY_MODE_HIDDEN,
        )

        overlay.draw(frame, snapshot)

        self.assertEqual(overlay._lines(snapshot), [])
        self.assertEqual(int(frame.sum()), 0)

    def test_cycle_overlay_mode_advances_through_modes(self):
        overlay = DebugOverlay(mode=OVERLAY_MODE_NORMAL)

        first = overlay.cycle_mode()
        second = overlay.cycle_mode()
        third = overlay.cycle_mode()

        self.assertEqual(first, OVERLAY_MODE_MINIMAL)
        self.assertEqual(second, OVERLAY_MODE_HIDDEN)
        self.assertEqual(third, OVERLAY_MODE_NORMAL)


if __name__ == "__main__":
    unittest.main()
