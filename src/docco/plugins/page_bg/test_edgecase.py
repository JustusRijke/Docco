# Edge-case tests only. The happy path is covered by test_regression.py. Only keep tests for code paths not exercised there.
import pytest

from docco.context import ContentType, Context
from docco.plugins.page_bg import Stage


def make_ctx(tmp_path, content):
    md = tmp_path / "test.md"
    md.write_text("# placeholder", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", {})
    ctx.content = content
    ctx.content_type = ContentType.HTML
    return ctx


def test_missing_image_raises(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- page-bg x="10%" -->')
    with pytest.raises(ValueError, match="Missing 'image'"):
        Stage().process(ctx)


def test_no_directives(tmp_path):
    ctx = make_ctx(tmp_path, "<p>No directives here</p>")
    result = Stage().process(ctx)
    assert result.content == "<p>No directives here</p>"
