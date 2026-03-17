# Edge-case tests only. The happy path is covered by tests/test_regression.py.
import pytest

from conftest import make_ctx
from docco.plugins.html import Stage


def test_css_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="CSS file not found"):
        Stage().process(
            make_ctx(tmp_path, "Hello", {"html": {"css": ["/nonexistent/style.css"]}})
        )


def test_css_absolute_url_passthrough(tmp_path):
    css = tmp_path / "style.css"
    css.write_text(
        "body { background: url('https://cdn.example.com/bg.png'); }", encoding="utf-8"
    )
    result = Stage().process(make_ctx(tmp_path, "Hello", {"html": {"css": [str(css)]}}))
    assert "https://cdn.example.com/bg.png" in result.str_content


def test_js_inline(tmp_path):
    js = tmp_path / "app.js"
    js.write_text("console.log('hi');", encoding="utf-8")
    result = Stage().process(make_ctx(tmp_path, "Hello", {"html": {"js": [str(js)]}}))
    assert "console.log('hi');" in result.str_content
    assert "<script>" in result.str_content


def test_js_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="JS file not found"):
        Stage().process(
            make_ctx(tmp_path, "Hello", {"html": {"js": ["/nonexistent/app.js"]}})
        )


def test_custom_template(tmp_path):
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        "<html><head></head><body>{{ css }}{{ body }}</body></html>", encoding="utf-8"
    )
    cfg = {"html": Stage.normalize_config_section({"template": str(tpl)}, tmp_path)}
    result = Stage().process(make_ctx(tmp_path, "Hello", cfg))
    assert "<p>Hello</p>" in result.str_content


def test_normalize_config_template(tmp_path):
    result = Stage.normalize_config_section({"template": "tpl.html"}, tmp_path)
    assert result["template"] == [str((tmp_path / "tpl.html").resolve())]
