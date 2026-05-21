from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

from control.scroll_engine import (
    ACTION_AUTO_SCROLL_TIMEOUT,
    ACTION_DISABLED,
    ACTION_NO_ACTION,
    ACTION_SCROLL_UP,
    ACTION_SCROLL_DOWN,
    ACTION_START_AUTO_SCROLL,
    ACTION_STOP_AUTO_SCROLL,
    ACTION_TOGGLE_ENABLED,
    DIRECTION_DOWN,
    DIRECTION_NONE,
    DIRECTION_UP,
    ScrollEngine,
)
from vision.gaze_detector import DOUBLE_BLINK, LONG_BLINK, SINGLE_BLINK, TRIPLE_BLINK


class ScrollEngineTests(unittest.TestCase):
    def test_double_blink_starts_continuous_scroll_down_when_enabled(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=True, scroll_fn=scroll_calls.append)

        action = engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)

        self.assertEqual(action, ACTION_START_AUTO_SCROLL)
        self.assertTrue(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_DOWN)
        self.assertEqual(scroll_calls, [])

    def test_update_scrolls_down_with_negative_steps_while_auto_scroll_is_active(self):
        scroll_calls = []
        engine = ScrollEngine(
            enabled=True,
            down_scroll_amount_per_step=-120,
            scroll_interval_ms=120,
            scroll_fn=scroll_calls.append,
        )

        engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)
        first_action = engine.update(timestamp_ms=1000)
        early_action = engine.update(timestamp_ms=1119)
        second_action = engine.update(timestamp_ms=1120)

        self.assertEqual(first_action, ACTION_SCROLL_DOWN)
        self.assertEqual(early_action, ACTION_NO_ACTION)
        self.assertEqual(second_action, ACTION_SCROLL_DOWN)
        self.assertEqual(scroll_calls, [-120, -120])

    def test_triple_blink_starts_continuous_scroll_up_when_enabled(self):
        scroll_calls = []
        engine = ScrollEngine(
            enabled=True,
            up_scroll_amount_per_step=120,
            scroll_interval_ms=120,
            scroll_fn=scroll_calls.append,
        )

        action = engine.handle_gesture(TRIPLE_BLINK, timestamp_ms=1000)
        scroll_action = engine.update(timestamp_ms=1000)

        self.assertEqual(action, ACTION_START_AUTO_SCROLL)
        self.assertTrue(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_UP)
        self.assertEqual(scroll_action, ACTION_SCROLL_UP)
        self.assertEqual(scroll_calls, [120])

    def test_double_blink_stops_continuous_scroll_down_when_already_scrolling_down(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=True, scroll_fn=scroll_calls.append)

        start_action = engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)
        stop_action = engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1100)
        update_action = engine.update(timestamp_ms=1220)

        self.assertEqual(start_action, ACTION_START_AUTO_SCROLL)
        self.assertEqual(stop_action, ACTION_STOP_AUTO_SCROLL)
        self.assertFalse(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_NONE)
        self.assertEqual(update_action, ACTION_NO_ACTION)
        self.assertEqual(scroll_calls, [])

    def test_triple_blink_stops_continuous_scroll_up_when_already_scrolling_up(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=True, scroll_fn=scroll_calls.append)

        start_action = engine.handle_gesture(TRIPLE_BLINK, timestamp_ms=1000)
        stop_action = engine.handle_gesture(TRIPLE_BLINK, timestamp_ms=1100)

        self.assertEqual(start_action, ACTION_START_AUTO_SCROLL)
        self.assertEqual(stop_action, ACTION_STOP_AUTO_SCROLL)
        self.assertFalse(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_NONE)
        self.assertEqual(scroll_calls, [])

    def test_triple_blink_switches_active_down_scroll_to_up(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=True, scroll_fn=scroll_calls.append)

        down_action = engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)
        up_action = engine.handle_gesture(TRIPLE_BLINK, timestamp_ms=1100)

        self.assertEqual(down_action, ACTION_START_AUTO_SCROLL)
        self.assertEqual(up_action, ACTION_START_AUTO_SCROLL)
        self.assertTrue(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_UP)
        self.assertEqual(scroll_calls, [])

    def test_double_or_triple_blink_does_not_start_auto_scroll_when_disabled(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=False, scroll_fn=scroll_calls.append)

        down_action = engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)
        up_action = engine.handle_gesture(TRIPLE_BLINK, timestamp_ms=1100)

        self.assertEqual(down_action, ACTION_DISABLED)
        self.assertEqual(up_action, ACTION_DISABLED)
        self.assertFalse(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_NONE)
        self.assertEqual(scroll_calls, [])

    def test_long_blink_toggles_enabled_and_disabling_stops_auto_scroll(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=False, scroll_fn=scroll_calls.append)

        first_action = engine.handle_gesture(LONG_BLINK, timestamp_ms=1000)
        enabled_after_first_long_blink = engine.enabled
        start_action = engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1100)
        auto_scroll_after_double_blink = engine.auto_scroll
        second_action = engine.handle_gesture(LONG_BLINK, timestamp_ms=2000)

        self.assertEqual(first_action, ACTION_TOGGLE_ENABLED)
        self.assertTrue(enabled_after_first_long_blink)
        self.assertEqual(start_action, ACTION_START_AUTO_SCROLL)
        self.assertTrue(auto_scroll_after_double_blink)
        self.assertEqual(second_action, ACTION_TOGGLE_ENABLED)
        self.assertFalse(engine.enabled)
        self.assertFalse(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_NONE)
        self.assertEqual(scroll_calls, [])

    def test_single_blink_stops_active_auto_scroll(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=True, scroll_fn=scroll_calls.append)

        engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)
        action = engine.handle_gesture(SINGLE_BLINK, timestamp_ms=1000)

        self.assertEqual(action, ACTION_STOP_AUTO_SCROLL)
        self.assertFalse(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_NONE)
        self.assertEqual(scroll_calls, [])

    def test_single_blink_is_no_action_when_auto_scroll_is_inactive(self):
        scroll_calls = []
        engine = ScrollEngine(enabled=True, scroll_fn=scroll_calls.append)

        action = engine.handle_gesture(SINGLE_BLINK, timestamp_ms=1000)

        self.assertEqual(action, ACTION_NO_ACTION)
        self.assertEqual(scroll_calls, [])

    def test_default_scroll_uses_pyautogui_scroll(self):
        scroll_calls = []
        fake_pyautogui = SimpleNamespace(scroll=scroll_calls.append)

        with patch.dict(sys.modules, {"pyautogui": fake_pyautogui}):
            ScrollEngine.pyautogui_scroll(-123)

        self.assertEqual(scroll_calls, [-123])

    def test_auto_scroll_stops_after_timeout(self):
        scroll_calls = []
        engine = ScrollEngine(
            enabled=True,
            auto_scroll_timeout_ms=20000,
            scroll_fn=scroll_calls.append,
        )

        engine.handle_gesture(DOUBLE_BLINK, timestamp_ms=1000)
        before_timeout = engine.update(timestamp_ms=20999)
        timeout_action = engine.update(timestamp_ms=21000)

        self.assertEqual(before_timeout, ACTION_SCROLL_DOWN)
        self.assertEqual(timeout_action, ACTION_AUTO_SCROLL_TIMEOUT)
        self.assertFalse(engine.auto_scroll)
        self.assertEqual(engine.direction, DIRECTION_NONE)

    def test_set_speed_preset_updates_scroll_step_and_interval(self):
        engine = ScrollEngine(
            speed_presets={
                "slow": {
                    "down_scroll_amount_per_step": -60,
                    "up_scroll_amount_per_step": 60,
                    "scroll_interval_ms": 180,
                },
                "fast": {
                    "down_scroll_amount_per_step": -240,
                    "up_scroll_amount_per_step": 240,
                    "scroll_interval_ms": 70,
                },
            }
        )

        action = engine.set_speed_preset("fast")

        self.assertEqual(action, "SET_SPEED_FAST")
        self.assertEqual(engine.speed_preset, "fast")
        self.assertEqual(engine.down_scroll_amount_per_step, -240)
        self.assertEqual(engine.up_scroll_amount_per_step, 240)
        self.assertEqual(engine.scroll_interval_ms, 70)


if __name__ == "__main__":
    unittest.main()
