import logging

from docco.logging_config import (
    LogCounter,
    _RedirectToDebug,
    redirect_to_debug,
    setup_logging,
)


def test_setup_logging_default():
    counter = setup_logging()
    logger = logging.getLogger("docco")
    assert logger.level == logging.INFO
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    assert isinstance(counter, LogCounter)


def test_setup_logging_verbose():
    setup_logging(verbose=True)
    logger = logging.getLogger("docco")
    assert logger.level == logging.DEBUG


def test_setup_logging_clears_existing_handlers():
    logger = logging.getLogger("docco")
    logger.addHandler(logging.NullHandler())
    setup_logging()
    # NullHandler removed; only console + counter remain
    assert not any(isinstance(h, logging.NullHandler) for h in logger.handlers)


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
    logger = logging.getLogger("docco")
    assert logger.level == logging.WARNING


def test_setup_logging_level_overrides_verbose():
    setup_logging(verbose=True, level="warning")
    logger = logging.getLogger("docco")
    assert logger.level == logging.WARNING


def test_log_counter_counts_warnings():
    counter = setup_logging()
    logger = logging.getLogger("docco")
    logger.warning("test warning")
    assert counter.warning_count == 1
    assert counter.error_count == 0


def test_log_counter_counts_errors():
    counter = setup_logging()
    logger = logging.getLogger("docco")
    logger.error("test error")
    assert counter.warning_count == 0
    assert counter.error_count == 1


def test_log_counter_ignores_info():
    counter = setup_logging()
    logger = logging.getLogger("docco")
    logger.info("not counted")
    assert counter.warning_count == 0
    assert counter.error_count == 0


def test_redirect_to_debug_demotes_level(caplog):
    setup_logging(verbose=True)
    redirected = logging.getLogger("test_redirect_target")
    redirected.handlers = []
    redirected.propagate = False

    with (
        redirect_to_debug("test_redirect_target"),
        caplog.at_level(logging.DEBUG, logger="docco"),
    ):
        redirected.warning("should become debug")

    # After context: handlers restored
    assert redirected.propagate is False


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
    # WARNING demoted to DEBUG — counter should NOT increment
    assert counter.warning_count == 0
