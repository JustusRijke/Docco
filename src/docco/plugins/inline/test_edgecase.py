# Edge-case tests only. The happy path is covered by test_regression.py.
import logging

import pytest

from conftest import make_ctx
from docco.plugins.inline import Stage


def test_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing.md"):
        Stage().process(make_ctx(tmp_path, '<!-- inline src="missing.md" -->'))


def test_unused_arg_warning(tmp_path, caplog):
    (tmp_path / "frag.md").write_text("Hello", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.plugins.inline"):
        Stage().process(make_ctx(tmp_path, '<!-- inline src="frag.md" unused="x" -->'))
    assert "Unused" in caplog.text


def test_unfulfilled_placeholder_warning(tmp_path, caplog):
    (tmp_path / "frag.md").write_text("Hello {{name}}", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.plugins.inline"):
        Stage().process(make_ctx(tmp_path, '<!-- inline src="frag.md" -->'))
    assert "Unfulfilled" in caplog.text


def test_max_iterations_exceeded(tmp_path):
    (tmp_path / "loop.md").write_text('<!-- inline src="loop.md" -->', encoding="utf-8")
    with pytest.raises(ValueError, match="Max iterations"):
        Stage().process(make_ctx(tmp_path, '<!-- inline src="loop.md" -->'))


def test_rebase_absolute_path_preserved(tmp_path):
    frag = tmp_path / "frag.md"
    frag.write_text("Fragment", encoding="utf-8")
    inner = tmp_path / "inner.md"
    inner.write_text(f'<!-- inline src="{frag}" -->', encoding="utf-8")
    result = Stage().process(make_ctx(tmp_path, '<!-- inline src="inner.md" -->'))
    assert "Fragment" in result.str_content


def test_malformed_directive_raises(tmp_path):
    with pytest.raises(ValueError, match="Malformed 'inline' directive"):
        Stage().process(make_ctx(tmp_path, '<!-- inline : "frag.md" -->'))
