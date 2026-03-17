import logging
from pathlib import Path

import pytest

from docco.context import Context


@pytest.fixture(autouse=True)
def reset_docco_logger():
    log = logging.getLogger("docco")
    original_propagate = log.propagate
    original_level = log.level
    original_handlers = log.handlers[:]
    yield
    for h in log.handlers:
        if h not in original_handlers:
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


@pytest.fixture
def project_toml(tmp_path):
    toml = tmp_path / "docco.toml"
    toml.write_text('file = "test.md"\n', encoding="utf-8")
    return toml


@pytest.fixture
def output_dir(tmp_path) -> Path:
    out = tmp_path / "output"
    out.mkdir()
    return out
