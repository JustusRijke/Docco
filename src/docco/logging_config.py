"""Logging configuration for Docco."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import colorlog


class LogCounter(logging.Handler):
    """Handler that counts warnings and errors."""

    def __init__(self) -> None:
        super().__init__()
        self.warning_count = 0
        self.error_count = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.error_count += 1
        elif record.levelno >= logging.WARNING:
            self.warning_count += 1


class _RedirectToDebug(logging.Handler):
    """Forward all records to a fixed set of handlers, demoted to DEBUG level."""

    def __init__(self, handlers: list[logging.Handler]) -> None:
        super().__init__()
        self._handlers = handlers

    def emit(self, record: logging.LogRecord) -> None:
        record = logging.makeLogRecord(record.__dict__)
        record.levelno = logging.DEBUG
        record.levelname = "DEBUG"
        for h in self._handlers:
            h.handle(record)


@contextmanager
def redirect_to_debug() -> Generator[None, None, None]:
    """Context manager: demote all root-logger output to DEBUG while active.

    Replaces the root logger's handlers with a single redirect handler that
    re-emits every record at DEBUG level through the saved handlers. This
    prevents third-party code (e.g. diffpdf) from logging at ERROR/WARNING
    while still surfacing its output in verbose mode. Saves and restores the
    root logger's level and handler list on exit.
    """
    root = logging.getLogger()
    saved_level = root.level
    saved_handlers = root.handlers[:]
    root.handlers[:] = [_RedirectToDebug(saved_handlers)]
    root.setLevel(logging.DEBUG)
    try:
        yield
    finally:
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> LogCounter:
    """
    Configure logging with colorized output and warning/error counting.

    Args:
        verbose: Enable DEBUG level logging
        log_file: Optional file path to write plain-text log output to

    Returns:
        LogCounter: Counter instance for tracking warnings/errors
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    counter = LogCounter()

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.addHandler(counter)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
        root_logger.addHandler(file_handler)

    root_logger.setLevel(log_level)

    return counter
