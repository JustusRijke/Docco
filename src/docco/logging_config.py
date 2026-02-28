"""Logging configuration for Docco."""

import logging
from pathlib import Path

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
