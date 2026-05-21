import logging
from pathlib import Path
import sys

from utils.resource_path import log_path as default_log_path


LOGGER_NAME = "lazyscroll"


def setup_startup_logging(path: str | Path | None = None) -> logging.Logger:
    """Configure file logging early enough for packaged startup diagnostics."""
    log_file = Path(path) if path is not None else default_log_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "_lazyscroll_file_handler", False):
            logger.removeHandler(handler)
            handler.close()

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler._lazyscroll_file_handler = True  # type: ignore[attr-defined]
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    logger.info("Logging initialized: %s", log_file)
    sys.excepthook = _make_exception_hook(logger)
    return logger


def log_exception(
    logger: logging.Logger,
    message: str,
    error: BaseException,
) -> None:
    logger.error(message, exc_info=(type(error), error, error.__traceback__))


def close_startup_logging(logger: logging.Logger) -> None:
    """Close LazyScroll file handlers so tests and rebuilds can release the log."""
    for handler in list(logger.handlers):
        if getattr(handler, "_lazyscroll_file_handler", False):
            logger.removeHandler(handler)
            handler.close()


def _make_exception_hook(logger: logging.Logger):
    def _hook(exc_type, exc_value, exc_traceback) -> None:
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    return _hook
