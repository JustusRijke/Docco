import pytest

from docco.context import ContentType, Context
from docco.plugins.html import Stage


def test_html_stage_basic(markdown_context):
    stage = Stage()
    result = stage.process(markdown_context)

    assert result.content_type == ContentType.HTML
    assert 'id="hello"' in result.str_content
    assert "<p>World</p>" in result.str_content
    assert "<!DOCTYPE html>" in result.str_content


def test_html_stage_with_css(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Styled", encoding="utf-8")
    css = tmp_path / "style.css"
    css.write_text("body { color: red; }", encoding="utf-8")

    config = {"html": {"css": [str(css)]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert "body { color: red; }" in result.str_content


def test_html_stage_css_not_found(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Test", encoding="utf-8")
    config = {"html": {"css": ["/nonexistent/style.css"]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    with pytest.raises(FileNotFoundError, match="CSS file not found"):
        Stage().process(ctx)


def test_html_stage_custom_template(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    template = tmp_path / "custom.html"
    template.write_text(
        "<html><head></head><body>{{ css }}{{ body }}</body></html>", encoding="utf-8"
    )

    raw = {"html": {"template": str(template)}}
    config = {"html": Stage.normalize_config_section(raw["html"], tmp_path)}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert result.str_content.startswith("<html>")
    assert "<p>Hello</p>" in result.str_content


def test_html_stage_relative_css(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    md = docs / "test.md"
    md.write_text("# Test", encoding="utf-8")
    css = docs / "rel.css"
    css.write_text("h1 { color: blue; }", encoding="utf-8")

    raw = {"html": {"css": ["rel.css"]}}
    config = {"html": Stage.normalize_config_section(raw["html"], docs)}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert "h1 { color: blue; }" in result.str_content


def test_html_stage_relative_template(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    md = docs / "test.md"
    md.write_text("Hello", encoding="utf-8")
    template = docs / "tpl.html"
    template.write_text("<div><head></head>{{ css }}{{ body }}</div>", encoding="utf-8")

    raw = {"html": {"template": "tpl.html"}}
    config = {"html": Stage.normalize_config_section(raw["html"], docs)}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert result.str_content.startswith("<div>")


def test_html_stage_inline_js(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    js = tmp_path / "app.js"
    js.write_text("console.log('hi');", encoding="utf-8")

    config = {"html": {"js": [str(js)]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert "console.log('hi');" in result.str_content


def test_html_stage_js_not_found(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    config = {"html": {"js": ["/nonexistent/app.js"]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    with pytest.raises(FileNotFoundError, match="JS file not found"):
        Stage().process(ctx)


def test_html_stage_external_js(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    config = {"html": {"js_external": ["https://example.com/lib.js"]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert 'src="https://example.com/lib.js"' in result.str_content


def test_html_heading_anchors(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# My Heading\n", encoding="utf-8")
    config = {}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert 'id="my-heading"' in result.str_content


def test_html_no_js_no_script_tags(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    config = {}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    # No JS configured — template rendered without extra script tags
    assert "<!DOCTYPE html>" in result.str_content


def test_html_title_defaults_to_filename(tmp_path):
    md = tmp_path / "my_document.md"
    md.write_text("Hello", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", {})

    result = Stage().process(ctx)
    assert "<title>my_document</title>" in result.str_content


def test_html_title_config_overrides(tmp_path):
    md = tmp_path / "my_document.md"
    md.write_text("Hello", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", {"html": {"title": "Custom Title"}})

    result = Stage().process(ctx)
    assert "<title>Custom Title</title>" in result.str_content


def test_html_stage_relative_js(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    md = docs / "test.md"
    md.write_text("Hello", encoding="utf-8")
    js = docs / "app.js"
    js.write_text("var x = 1;", encoding="utf-8")

    raw = {"html": {"js": ["app.js"]}}
    config = {"html": Stage.normalize_config_section(raw["html"], docs)}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert "var x = 1;" in result.str_content


def test_html_css_relative_url_absolutized(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    css = tmp_path / "style.css"
    css.write_text("body { background: url('bg.png'); }", encoding="utf-8")

    config = {"html": {"css": [str(css)]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert "file://" in result.str_content
    assert "bg.png" in result.str_content


def test_html_css_absolute_url_passthrough(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello", encoding="utf-8")
    css = tmp_path / "style.css"
    css.write_text(
        "body { background: url('https://cdn.example.com/bg.png'); }", encoding="utf-8"
    )

    config = {"html": {"css": [str(css)]}}
    ctx = Context.from_file(md, tmp_path / "out", config)

    result = Stage().process(ctx)
    assert "https://cdn.example.com/bg.png" in result.str_content
