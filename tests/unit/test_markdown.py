"""
Unit tests for MarkdownConverter.
"""

import pytest
from docco.content.markdown import MarkdownConverter


class TestMarkdownConverter:
    """Tests for Markdown to HTML conversion."""

    def test_convert_bold(self, markdown_converter):
        """Test converting bold text."""
        result = markdown_converter.convert("This is **bold** text")
        assert "<strong>bold</strong>" in result

    def test_convert_italic(self, markdown_converter):
        """Test converting italic text."""
        result = markdown_converter.convert("This is *italic* text")
        assert "<em>italic</em>" in result

    def test_convert_unordered_list(self, markdown_converter):
        """Test converting unordered list."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        result = markdown_converter.convert(markdown)
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result

    def test_convert_ordered_list(self, markdown_converter):
        """Test converting ordered list."""
        markdown = "1. First\n2. Second\n3. Third"
        result = markdown_converter.convert(markdown)
        assert "<ol>" in result
        assert "<li>First</li>" in result

    def test_convert_link(self, markdown_converter):
        """Test converting links."""
        result = markdown_converter.convert("[Click here](https://example.com)")
        assert '<a href="https://example.com">Click here</a>' in result

    def test_convert_code(self, markdown_converter):
        """Test converting inline code."""
        result = markdown_converter.convert("Use `print()` function")
        assert "<code>print()</code>" in result

    def test_convert_table(self, markdown_converter):
        """Test converting table."""
        markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""
        result = markdown_converter.convert(markdown)
        assert "<table>" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "Header 1" in result
        assert "Cell 1" in result

    def test_convert_empty_string(self, markdown_converter):
        """Test converting empty string returns empty."""
        result = markdown_converter.convert("")
        assert result == ""

    def test_convert_whitespace_only(self, markdown_converter):
        """Test converting whitespace-only string returns empty."""
        result = markdown_converter.convert("   \n\n   ")
        assert result == ""

    def test_convert_paragraph(self, markdown_converter):
        """Test paragraph wrapping."""
        result = markdown_converter.convert("This is a paragraph.")
        assert "<p>This is a paragraph.</p>" in result

    def test_convert_inline_strips_p_tags(self, markdown_converter):
        """Test that convert_inline removes outer <p> tags."""
        result = markdown_converter.convert_inline("This is text")
        assert not result.startswith("<p>")
        assert not result.endswith("</p>")
        assert "This is text" in result

    def test_convert_inline_with_formatting(self, markdown_converter):
        """Test convert_inline preserves inner formatting."""
        result = markdown_converter.convert_inline("This is **bold** text")
        assert "<strong>bold</strong>" in result
        assert not result.startswith("<p>")

    def test_convert_inline_empty(self, markdown_converter):
        """Test convert_inline with empty string."""
        result = markdown_converter.convert_inline("")
        assert result == ""
