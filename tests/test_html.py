"""Tests for HTML conversion."""

import pytest

from docco.core import (
    _absolutize_html_urls,
    absolutize_css_urls,
    markdown_to_html,
    wrap_html,
)


def test_markdown_to_html_returns_string():
    """Test markdown to HTML returns a string."""
    markdown = "# Hello\n\nThis is a paragraph."
    html = markdown_to_html(markdown)
    assert html is not None
    assert isinstance(html, str)
    assert len(html) > 0


def test_wrap_html_wraps_content():
    """Test HTML wrapping produces valid structure."""
    html_content = "<p>Hello</p>"
    wrapped = wrap_html(html_content)
    assert "<!DOCTYPE html>" in wrapped
    assert "<html" in wrapped
    assert html_content in wrapped
    assert "</html>" in wrapped


def test_absolutize_html_urls_converts_relative_image(tmp_path):
    """Test relative image URLs are converted to absolute file:// URLs."""
    html = '<img src="images/test.png" alt="test">'
    base_dir = tmp_path / "docs"
    result = _absolutize_html_urls(html, base_dir)
    # Check that result contains file:// URL and images/test.png
    assert 'src="file://' in result
    assert "images/test.png" in result


def test_absolutize_html_urls_preserves_anchor_links(tmp_path):
    """Test anchor links (#section) are preserved."""
    html = '<a href="#section1">Link</a>'
    base_dir = tmp_path / "docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'href="#section1"' in result


def test_absolutize_html_urls_preserves_absolute_urls(tmp_path):
    """Test absolute URLs (http, https, file) are preserved."""
    html = """
        <img src="http://example.com/img.png">
        <a href="https://example.com">Link</a>
        <link href="file:///etc/style.css">
    """
    base_dir = tmp_path / "docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'src="http://example.com/img.png"' in result
    assert 'href="https://example.com"' in result
    assert 'href="file:///etc/style.css"' in result


def test_absolutize_html_urls_preserves_data_urls(tmp_path):
    """Test data URLs are preserved."""
    html = '<img src="data:image/png;base64,abc123">'
    base_dir = tmp_path / "docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'src="data:image/png;base64,abc123"' in result


def test_wrap_html_absolutizes_urls_when_base_url_provided(tmp_path):
    """Test wrap_html converts relative URLs when base_dir is provided."""
    html_content = '<img src="test.png">'
    base_dir = tmp_path / "docs"
    wrapped = wrap_html(html_content, base_dir=base_dir)
    # Check that result contains file:// URL and test.png
    assert 'src="file://' in wrapped
    assert "test.png" in wrapped


def test_wrap_html_no_base_tag(tmp_path):
    """Test wrap_html does not include base tag."""
    html_content = "<p>Hello</p>"
    base_dir = tmp_path / "docs"
    wrapped = wrap_html(html_content, base_dir=base_dir)
    assert "<base" not in wrapped


def test_wrap_html_inline_js_in_head():
    """Test inline JS is placed as <script> tag in <head>."""
    wrapped = wrap_html("<p>Body</p>", js_content="console.log('hi');")
    head = wrapped[: wrapped.index("<body>")]
    assert "<script>" in head
    assert "console.log('hi');" in head


def test_wrap_html_external_js_in_head():
    """Test external JS URLs become <script src> tags in <head>."""
    wrapped = wrap_html("<p>Body</p>", external_js=["https://example.com/lib.js"])
    head = wrapped[: wrapped.index("<body>")]
    assert '<script src="https://example.com/lib.js"></script>' in head


def test_absolutize_css_urls_converts_relative_font(tmp_path):
    """Test relative font URLs are converted to absolute file:// URLs."""
    css = "@font-face { src: url('./fonts/font.ttf'); }"
    result = absolutize_css_urls(css, tmp_path / "css" / "style.css")
    assert 'url("file://' in result
    assert "fonts/font.ttf" in result


def test_absolutize_css_urls_handles_various_quote_styles(tmp_path):
    """Test CSS url() with different quote styles."""
    css = """
        .a { background: url('./img1.png'); }
        .b { background: url("./img2.png"); }
        .c { background: url(./img3.png); }
    """
    result = absolutize_css_urls(css, tmp_path / "css" / "style.css")
    assert 'url("file://' in result
    assert "img1.png" in result
    assert "img2.png" in result
    assert "img3.png" in result


def test_absolutize_css_urls_preserves_absolute_urls(tmp_path):
    """Test absolute URLs (http, https, file) are preserved."""
    css = """
        @font-face { src: url("https://fonts.com/font.woff2"); }
        .a { background: url("http://example.com/bg.png"); }
        .b { background: url("file:///etc/image.png"); }
    """
    result = absolutize_css_urls(css, tmp_path / "style.css")
    assert 'url("https://fonts.com/font.woff2")' in result
    assert 'url("http://example.com/bg.png")' in result
    assert 'url("file:///etc/image.png")' in result


def test_absolutize_css_urls_preserves_data_urls(tmp_path):
    """Test data URLs are preserved."""
    css = ".icon { background: url('data:image/svg+xml;base64,abc123'); }"
    result = absolutize_css_urls(css, tmp_path / "style.css")
    assert "data:image/svg+xml;base64,abc123" in result


def test_wrap_html_absolutizes_style_block_urls(tmp_path):
    """Test wrap_html absolutizes url() refs in <style> blocks from inlined CSS."""
    font_file = tmp_path / "fonts" / "Open.ttf"
    font_file.parent.mkdir()
    font_file.write_bytes(b"fake")

    css = "@font-face { src: url('./fonts/Open.ttf'); }"
    wrapped = wrap_html("<p>Body</p>", css_content=css, base_dir=tmp_path)
    assert "file://" in wrapped
    assert "Open.ttf" in wrapped
    assert "url('./fonts/Open.ttf')" not in wrapped


def test_wrap_html_style_block_missing_asset_raises(tmp_path):
    """Test wrap_html raises FileNotFoundError for missing assets in <style> blocks."""
    css = "@font-face { src: url('./fonts/Missing.ttf'); }"
    with pytest.raises(FileNotFoundError, match="Missing.ttf"):
        wrap_html("<p>Body</p>", css_content=css, base_dir=tmp_path)


def test_wrap_html_style_block_in_inlined_html(tmp_path):
    """Test url() refs in <style> sections of inlined HTML are absolutized."""
    font_file = tmp_path / "font.ttf"
    font_file.write_bytes(b"fake")

    # Simulate an inlined HTML fragment that contains a <style> block
    body_html = "<style>@font-face { src: url('./font.ttf'); }</style><p>Hello</p>"
    wrapped = wrap_html(body_html, base_dir=tmp_path)
    assert "file://" in wrapped
    assert "font.ttf" in wrapped
    assert "url('./font.ttf')" not in wrapped
