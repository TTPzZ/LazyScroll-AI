import unittest

from control.scroll_constants import (
    ACTION_START_AUTO_SCROLL,
    ACTION_STOP_AUTO_SCROLL,
    ACTION_TOGGLE_ENABLED,
)
from utils.audio_feedback import AudioFeedback
from vision.blink_calibration import CALIBRATION_ACTION_SAVED


class AudioFeedbackTests(unittest.TestCase):
    def test_notify_action_plays_distinct_enabled_and_disabled_beeps(self):
        beeps = []
        feedback = AudioFeedback(enabled=True, beep_fn=lambda frequency, duration: beeps.append((frequency, duration)))

        feedback.notify_action(ACTION_TOGGLE_ENABLED, enabled=True)
        feedback.notify_action(ACTION_TOGGLE_ENABLED, enabled=False)

        self.assertEqual(beeps, [(880, 80), (440, 80)])

    def test_notify_action_plays_scroll_start_stop_and_calibration_success(self):
        beeps = []
        feedback = AudioFeedback(enabled=True, beep_fn=lambda frequency, duration: beeps.append((frequency, duration)))

        feedback.notify_action(ACTION_START_AUTO_SCROLL)
        feedback.notify_action(ACTION_STOP_AUTO_SCROLL)
        feedback.notify_action(CALIBRATION_ACTION_SAVED)

        self.assertEqual(beeps, [(660, 60), (330, 60), (880, 60), (1040, 60)])

    def test_disabled_feedback_is_silent(self):
        beeps = []
        feedback = AudioFeedback(enabled=False, beep_fn=lambda frequency, duration: beeps.append((frequency, duration)))

        feedback.notify_action(ACTION_START_AUTO_SCROLL)

        self.assertEqual(beeps, [])


if __name__ == "__main__":
    unittest.main()
