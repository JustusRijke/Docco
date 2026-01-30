"""Tests for HTML conversion."""

from docco.core import _absolutize_html_urls, markdown_to_html, wrap_html


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


def test_absolutize_html_urls_converts_relative_image():
    """Test relative image URLs are converted to absolute file:// URLs."""
    html = '<img src="images/test.png" alt="test">'
    base_dir = "/path/to/docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'src="file:///path/to/docs/images/test.png"' in result


def test_absolutize_html_urls_preserves_anchor_links():
    """Test anchor links (#section) are preserved."""
    html = '<a href="#section1">Link</a>'
    base_dir = "/path/to/docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'href="#section1"' in result


def test_absolutize_html_urls_preserves_absolute_urls():
    """Test absolute URLs (http, https, file) are preserved."""
    html = """
        <img src="http://example.com/img.png">
        <a href="https://example.com">Link</a>
        <link href="file:///etc/style.css">
    """
    base_dir = "/path/to/docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'src="http://example.com/img.png"' in result
    assert 'href="https://example.com"' in result
    assert 'href="file:///etc/style.css"' in result


def test_absolutize_html_urls_preserves_data_urls():
    """Test data URLs are preserved."""
    html = '<img src="data:image/png;base64,abc123">'
    base_dir = "/path/to/docs"
    result = _absolutize_html_urls(html, base_dir)
    assert 'src="data:image/png;base64,abc123"' in result


def test_wrap_html_absolutizes_urls_when_base_url_provided():
    """Test wrap_html converts relative URLs when base_url is provided."""
    html_content = '<img src="test.png">'
    wrapped = wrap_html(html_content, base_url="/path/to/docs")
    assert 'src="file:///path/to/docs/test.png"' in wrapped


def test_wrap_html_no_base_tag():
    """Test wrap_html does not include base tag."""
    html_content = "<p>Hello</p>"
    wrapped = wrap_html(html_content, base_url="/path/to/docs")
    assert "<base" not in wrapped
