# Edge-case tests only. The happy path is covered by tests/test_regression.py.
from docco.context import ContentType, Context


def test_str_content(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("hello", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", {})
    assert ctx.str_content == "hello"


def test_from_html_file(tmp_path):
    html = tmp_path / "test.html"
    html.write_text("<p>hi</p>", encoding="utf-8")
    ctx = Context.from_html_file(html, tmp_path / "out", {})
    assert ctx.content_type == ContentType.HTML
    assert ctx.str_content == "<p>hi</p>"
