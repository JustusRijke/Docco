import pytest

from docco.context import ContentType, Context
from docco.plugins.toc import Stage

BASE_HTML = (
    "<!DOCTYPE html><html><head></head><body><!-- toc --><h1>Title</h1></body></html>"
)


def make_ctx(tmp_path, html=BASE_HTML, toc_config=None):
    md = tmp_path / "test.md"
    md.write_text("# placeholder", encoding="utf-8")
    config: dict = {}
    if toc_config:
        config["toc"] = toc_config
    ctx = Context.from_file(md, tmp_path / "out", config)
    ctx.content = html
    ctx.content_type = ContentType.HTML
    return ctx


def test_injects_nav(tmp_path):
    ctx = make_ctx(tmp_path)
    result = Stage().process(ctx)
    assert "<nav" in result.str_content
    assert "data-toc-start" in result.str_content


def test_toc_directive_replaced(tmp_path):
    ctx = make_ctx(tmp_path)
    result = Stage().process(ctx)
    assert "<!-- toc -->" not in result.str_content


def test_injects_scripts(tmp_path):
    ctx = make_ctx(tmp_path)
    result = Stage().process(ctx)
    assert "createToc" in result.str_content
    assert "TocHandler" in result.str_content


def test_custom_levels(tmp_path):
    ctx = make_ctx(tmp_path, toc_config={"start": 2, "end": 4})
    result = Stage().process(ctx)
    assert 'data-toc-start="2"' in result.str_content
    assert 'data-toc-end="4"' in result.str_content


def test_default_levels(tmp_path):
    ctx = make_ctx(tmp_path)
    result = Stage().process(ctx)
    assert 'data-toc-start="1"' in result.str_content
    assert 'data-toc-end="6"' in result.str_content


def test_no_toc_directive_skips(tmp_path):
    html = "<!DOCTYPE html><html><head></head><body><h1>Title</h1></body></html>"
    ctx = make_ctx(tmp_path, html=html)
    result = Stage().process(ctx)
    assert result.str_content == html
    assert "createToc" not in result.str_content


def test_unknown_arg_raises(tmp_path):
    ctx = make_ctx(
        tmp_path,
        html='<!DOCTYPE html><html><head></head><body><!-- toc badarg="x" --></body></html>',
    )
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage().process(ctx)
