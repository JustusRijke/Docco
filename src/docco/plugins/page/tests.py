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


def test_landscape_handler_injected_with_directive(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>A</p>\n<!-- page landscape -->\n<p>B</p>"))
    result = Stage().process(ctx)
    assert "LandscapeHandler" in result.str_content


def test_landscape_handler_not_injected_without_directives(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>Simple</p>"))
    result = Stage().process(ctx)
    assert "LandscapeHandler" not in result.str_content


def test_pagebreak(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>A</p>\n<!-- page break -->\n<p>B</p>"))
    result = Stage().process(ctx)
    assert '<div class="pagebreak"></div>' in result.str_content


def test_landscape_section(tmp_path):
    ctx = make_ctx(
        tmp_path,
        wrap("<p>Portrait</p>\n<!-- page landscape -->\n<p>Wide</p>"),
    )
    result = Stage().process(ctx)
    assert "section-wrapper portrait" in result.str_content
    assert "section-wrapper landscape" in result.str_content


def test_no_directives_passthrough(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>Simple</p>"))
    result = Stage().process(ctx)
    assert "<p>Simple</p>" in result.str_content


def test_portrait_returns_to_portrait(tmp_path):
    ctx = make_ctx(
        tmp_path,
        wrap(
            "<p>A</p>\n<!-- page landscape -->\n<p>B</p>\n<!-- page portrait -->\n<p>C</p>"
        ),
    )
    result = Stage().process(ctx)
    assert "landscape" in result.str_content
    assert "section-wrapper" in result.str_content


def test_empty_content_after_orientation(tmp_path):
    ctx = make_ctx(
        tmp_path,
        wrap("<!-- page landscape -->\n<!-- page portrait -->\n<p>Only portrait</p>"),
    )
    result = Stage().process(ctx)
    assert "<p>Only portrait</p>" in result.str_content


def test_empty_trailing_content(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>Content</p>\n<!-- page landscape -->\n   "))
    result = Stage().process(ctx)
    assert "<p>Content</p>" in result.str_content


def test_directive_at_exact_end(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>A</p>\n<!-- page landscape -->"))
    result = Stage().process(ctx)
    assert "<p>A</p>" in result.str_content


def test_pagedjs_screen_css_injected_by_default(tmp_path):
    ctx = make_ctx(tmp_path, wrap("<p>Hi</p>"))
    result = Stage().process(ctx)
    assert "pagedjs_page" in result.str_content


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
