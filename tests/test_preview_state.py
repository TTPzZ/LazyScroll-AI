import threading
import unittest

from ui.preview_state import PreviewState


class PreviewStateTests(unittest.TestCase):
    def test_default_visible(self) -> None:
        state = PreviewState()

        self.assertTrue(state.visible)

    def test_initial_hidden(self) -> None:
        state = PreviewState(visible=False)

        self.assertFalse(state.visible)

    def test_set_visible_true(self) -> None:
        state = PreviewState(visible=False)

        state.set_visible(True)

        self.assertTrue(state.visible)

    def test_set_visible_false(self) -> None:
        state = PreviewState(visible=True)

        state.set_visible(False)

        self.assertFalse(state.visible)

    def test_toggle_returns_new_value(self) -> None:
        state = PreviewState(visible=True)

        self.assertFalse(state.toggle())
        self.assertTrue(state.toggle())
        self.assertFalse(state.toggle())

    def test_thread_safety(self) -> None:
        state = PreviewState(visible=True)
        errors: list[Exception] = []

        def toggle_many(count: int) -> None:
            try:
                for _ in range(count):
                    state.toggle()
            except Exception as error:
                errors.append(error)

        threads = [threading.Thread(target=toggle_many, args=(100,)) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertTrue(state.visible)


if __name__ == "__main__":
    unittest.main()
