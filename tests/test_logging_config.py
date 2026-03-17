# Edge-case tests only. The happy path is covered by tests/test_regression.py.
import logging

from docco.logging_config import (
    LogCounter,
    _RedirectToDebug,
    redirect_to_debug,
    setup_logging,
)


def test_log_counter_counts_errors():
    counter = setup_logging()
    logging.getLogger("docco").error("test error")
    assert counter.error_count == 1


def test_setup_logging_with_log_file(tmp_path):
    log_file = tmp_path / "test.log"
    setup_logging(log_file=log_file)
    logger = logging.getLogger("docco")
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    logger.info("file test")
    for h in logger.handlers:
        h.flush()
    assert log_file.read_text(encoding="utf-8").strip().endswith("file test")


def test_setup_logging_level_override():
    setup_logging(level="warning")
    assert logging.getLogger("docco").level == logging.WARNING


def test_redirect_to_debug_restores_on_exit():
    redirected = logging.getLogger("test_restore_logger")
    original_handler = logging.NullHandler()
    redirected.addHandler(original_handler)
    redirected.propagate = True
    with redirect_to_debug("test_restore_logger"):
        pass
    assert original_handler in redirected.handlers
    assert redirected.propagate is True


def test_redirect_to_debug_handler_emits():
    docco_logger = logging.getLogger("docco")
    counter = LogCounter()
    docco_logger.addHandler(counter)
    handler = _RedirectToDebug(docco_logger)
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="test msg",
        args=(),
        exc_info=None,
    )
    handler.emit(record)
    assert counter.warning_count == 0
