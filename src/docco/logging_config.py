import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import colorlog

PLAIN_FORMAT = "%(levelname)-8s [%(shortname)s] %(message)s"
COLOR_FORMAT = "%(log_color)s%(levelname)-8s%(reset)s [%(shortname)s] %(message)s"
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


class _ShortNameFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.shortname = record.name.removeprefix("docco.")
        return True


class LogCounter(logging.Handler):
    warning_count: int = 0
    error_count: int = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno == logging.WARNING:
            self.warning_count += 1
        elif record.levelno >= logging.ERROR:
            self.error_count += 1


class _RedirectToDebug(logging.Handler):
    def __init__(self, target_logger: logging.Logger) -> None:
        super().__init__()
        self._target = target_logger

    def emit(self, record: logging.LogRecord) -> None:
        record = logging.makeLogRecord(record.__dict__)
        record.levelno = logging.DEBUG
        record.levelname = "DEBUG"
        self._target.handle(record)


@contextmanager
def redirect_to_debug(logger_name: str) -> Generator[None]:
    target = logging.getLogger("docco")
    handler = _RedirectToDebug(target)
    redirected = logging.getLogger(logger_name)
    original_handlers = redirected.handlers[:]
    original_propagate = redirected.propagate

    redirected.handlers = [handler]
    redirected.propagate = False
    try:
        yield
    finally:
        redirected.handlers = original_handlers
        redirected.propagate = original_propagate


def setup_logging(
    *,
    verbose: bool = False,
    log_file: Path | None = None,
    level: str | None = None,
) -> LogCounter:
    effective_level = (
        logging.getLevelNamesMapping()[level.upper()]
        if level
        else (logging.DEBUG if verbose else logging.INFO)
    )

    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(
        colorlog.ColoredFormatter(COLOR_FORMAT, log_colors=LOG_COLORS)
    )

    counter = LogCounter()

    short_name = _ShortNameFilter()
    console_handler.addFilter(short_name)

    root = logging.getLogger("docco")
    for handler in root.handlers:
        handler.close()
    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(counter)
    root.propagate = False

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(PLAIN_FORMAT))
        file_handler.addFilter(short_name)
        root.addHandler(file_handler)

    root.setLevel(effective_level)
    return counter
