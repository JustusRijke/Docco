# Edge-case tests only. The happy path is covered by test_regression.py. Only keep tests for code paths not exercised there.

import pytest

from docco.context import ContentType, Context
from docco.plugins.vars import Stage


def make_ctx(tmp_path, content, vars_config=None):
    md = tmp_path / "test.md"
    md.write_text(content, encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", {"vars": vars_config or {}})
    ctx.content = content
    ctx.content_type = ContentType.HTML
    return ctx


def test_reserved_var_raises(tmp_path):
    ctx = make_ctx(tmp_path, "<p>$$PATH$$</p>", {"PATH": "override"})
    with pytest.raises(ValueError, match="reserved"):
        Stage().process(ctx)


def test_undefined_var_raises(tmp_path):
    ctx = make_ctx(tmp_path, "<p>$$undefined$$</p>")
    with pytest.raises(ValueError, match="undefined"):
        Stage().process(ctx)


def test_unused_var_warning(tmp_path, caplog):
    ctx = make_ctx(tmp_path, "<p>$$name$$</p>", {"name": "World", "unused": "x"})
    Stage().process(ctx)
    assert "unused" in caplog.text.lower()
