"""Tests for HTML conversion."""

import pytest
from docco.html import markdown_to_html, wrap_html


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
