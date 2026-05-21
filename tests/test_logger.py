import tempfile
import unittest
from pathlib import Path

from utils.logger import close_startup_logging, log_exception, setup_startup_logging


class LoggerTests(unittest.TestCase):
    def test_setup_startup_logging_writes_to_requested_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "lazyscroll.log"

            logger = setup_startup_logging(path)
            try:
                logger.info("camera init")
                content = path.read_text(encoding="utf-8")
            finally:
                close_startup_logging(logger)

        self.assertIn("Logging initialized", content)
        self.assertIn("camera init", content)

    def test_log_exception_writes_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "lazyscroll.log"
            logger = setup_startup_logging(path)
            try:
                try:
                    raise RuntimeError("startup failed")
                except RuntimeError as error:
                    log_exception(logger, "Uncaught exception", error)

                content = path.read_text(encoding="utf-8")
            finally:
                close_startup_logging(logger)

        self.assertIn("Uncaught exception", content)
        self.assertIn("RuntimeError: startup failed", content)
        self.assertIn("Traceback", content)


if __name__ == "__main__":
    unittest.main()
