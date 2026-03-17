# Edge-case tests only. The happy path is covered by test_regression.py. Only keep tests for code paths not exercised there.

import pytest

from docco.context import ContentType, Context
from docco.plugins.toc import Stage


def _ctx(tmp_path, html):
    src = tmp_path / "test.md"
    src.write_text("# placeholder", encoding="utf-8")
    ctx = Context.from_file(src, tmp_path / "out", {})
    ctx.content = html
    ctx.content_type = ContentType.HTML
    return ctx


def test_no_toc_directive_skips(tmp_path):
    html = "<!DOCTYPE html><html><head></head><body><h1>Title</h1></body></html>"
    ctx = _ctx(tmp_path, html)
    assert Stage().process(ctx).str_content == html


def test_unknown_arg_raises(tmp_path):
    ctx = _ctx(
        tmp_path,
        '<!DOCTYPE html><html><head></head><body><!-- toc badarg="x" --></body></html>',
    )
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage().process(ctx)
