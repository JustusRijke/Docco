# Edge-case tests only. The happy path is covered by test_regression.py. Only keep tests for code paths not exercised there.

import pytest

from docco.context import ContentType, Context
from docco.plugins.page import Stage


def wrap(body):
    return f"<html><head></head><body>{body}</body></html>"


def make_ctx(tmp_path, content, config=None):
    md = tmp_path / "test.md"
    md.write_text("# placeholder", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", config or {})
    ctx.content = content
    ctx.content_type = ContentType.HTML
    return ctx


def test_no_directives(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>Simple</p>"))
    result = Stage().process(ctx)
    assert "LandscapeHandler" not in result.str_content


def test_pagedjs_screen_css_disabled(tmp_path):
    ctx = make_ctx(
        tmp_path, wrap("<p>Hi</p>"), {"page": {"add_pagedjs_screen_css": False}}
    )
    result = Stage().process(ctx)
    assert "pagedjs_page" not in result.str_content


def test_unknown_arg_raises(tmp_path):
    ctx = make_ctx(tmp_path, wrap('<!-- page badarg="x" -->'))
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage().process(ctx)
