import logging

import pytest

from docco.context import ContentType, Context


def make_ctx(tmp_path, content, config=None, content_type=ContentType.MARKDOWN):
    md = tmp_path / "test.md"
    md.write_text("# placeholder", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", config or {})
    ctx.content = content
    ctx.content_type = content_type
    return ctx


@pytest.fixture(autouse=True)
def reset_docco_logger():
    log = logging.getLogger("docco")
    original_propagate = log.propagate
    original_level = log.level
    original_handlers = log.handlers[:]
    yield
    for h in log.handlers:
        if h not in original_handlers:  # pragma: no branch
            h.close()
    log.handlers = original_handlers
    log.propagate = original_propagate
    log.level = original_level


@pytest.fixture
def tmp_md(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello\n\nWorld\n", encoding="utf-8")
    return md


@pytest.fixture
def tmp_config():
    return {}


@pytest.fixture
def markdown_context(tmp_md, tmp_path, tmp_config):
    return Context.from_file(tmp_md, tmp_path / "out", tmp_config)
