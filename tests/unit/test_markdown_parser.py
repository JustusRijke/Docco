"""
Unit tests for MarkdownDocumentParser.
"""

import pytest
from pathlib import Path
from docco.content.markdown_parser import MarkdownDocumentParser
from docco.core.section import Orientation


class TestMarkdownDocumentParser:
    """Tests for markdown file parsing."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MarkdownDocumentParser()

    def test_parse_simple_heading(self, parser):
        """Test parsing a single heading."""
        markdown = """# Introduction
This is the introduction content.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 1
        assert sections[0].level == 1
        assert sections[0].title == "Introduction"
        assert "introduction content" in sections[0].content

    def test_parse_multiple_headings(self, parser):
        """Test parsing multiple headings."""
        markdown = """# First Section
Content for first section.

## Second Section
Content for second section.

### Third Section
Content for third section.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 3
        assert sections[0].level == 1
        assert sections[0].title == "First Section"
        assert sections[1].level == 2
        assert sections[1].title == "Second Section"
        assert sections[2].level == 3
        assert sections[2].title == "Third Section"

    def test_parse_landscape_directive(self, parser):
        """Test landscape orientation directive."""
        markdown = """# Normal Section
Portrait content.

<!-- landscape -->
## Wide Section
Landscape content.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 2
        assert sections[0].orientation == Orientation.PORTRAIT
        assert sections[1].orientation == Orientation.LANDSCAPE

    def test_parse_portrait_directive(self, parser):
        """Test explicit portrait directive."""
        markdown = """<!-- landscape -->
# First
Landscape.

<!-- portrait -->
## Second
Back to portrait.
"""
        sections = parser.parse_string(markdown)

        assert sections[0].orientation == Orientation.LANDSCAPE
        assert sections[1].orientation == Orientation.PORTRAIT

    def test_parse_addendum_directive(self, parser):
        """Test addendum directive creates level 0 sections."""
        markdown = """# Normal Section
Regular content.

<!-- addendum -->
# Appendix
Appendix content.
"""
        sections = parser.parse_string(markdown)

        assert sections[0].level == 1
        assert sections[1].level == 0  # Addendum

    def test_parse_notoc_directive(self, parser):
        """Test notoc directive excludes from TOC."""
        markdown = """# Visible Section
In TOC.

<!-- notoc -->
## Hidden Section
Not in TOC.
"""
        sections = parser.parse_string(markdown)

        assert sections[0].exclude_from_toc is False
        assert sections[1].exclude_from_toc is True

    def test_parse_multiple_directives(self, parser):
        """Test multiple directives on same section."""
        markdown = """<!-- landscape -->
<!-- notoc -->
# Special Section
Both landscape and hidden from TOC.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 1
        assert sections[0].orientation == Orientation.LANDSCAPE
        assert sections[0].exclude_from_toc is True

    def test_parse_no_headings(self, parser):
        """Test parsing markdown with no headings."""
        markdown = """Just some text without any headings.
More text here.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 0

    def test_parse_heading_with_formatting(self, parser):
        """Test heading with markdown formatting."""
        markdown = """# Introduction to **Bold** and *Italic*
Content here.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 1
        assert sections[0].title == "Introduction to **Bold** and *Italic*"

    def test_parse_empty_section_content(self, parser):
        """Test section with no content."""
        markdown = """# First Section

# Second Section
Some content.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 2
        assert sections[0].content == ""
        assert "Some content" in sections[1].content

    def test_parse_hierarchical_sections(self, parser):
        """Test hierarchical section structure."""
        markdown = """# Main Section
Main content.

## Subsection One
Sub content 1.

## Subsection Two
Sub content 2.

# Another Main Section
More main content.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 4
        assert sections[0].level == 1
        assert sections[1].level == 2
        assert sections[2].level == 2
        assert sections[3].level == 1

    def test_directive_case_insensitive(self, parser):
        """Test that directives are case insensitive."""
        markdown = """<!-- LANDSCAPE -->
# First

<!-- Notoc -->
## Second
"""
        sections = parser.parse_string(markdown)

        assert sections[0].orientation == Orientation.LANDSCAPE
        assert sections[1].exclude_from_toc is True

    def test_directive_with_whitespace(self, parser):
        """Test directives with extra whitespace."""
        markdown = """<!--  landscape  -->
# Section
Content.
"""
        sections = parser.parse_string(markdown)

        assert sections[0].orientation == Orientation.LANDSCAPE

    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.md")

    def test_parse_file_success(self, parser, tmp_path):
        """Test parsing actual file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("""# Test Section
Test content.
""", encoding="utf-8")

        sections = parser.parse_file(md_file)

        assert len(sections) == 1
        assert sections[0].title == "Test Section"

    def test_directives_only_affect_next_section(self, parser):
        """Test that directives only affect the immediately following section."""
        markdown = """<!-- landscape -->
# First Section
Landscape.

# Second Section
Should be portrait (default).
"""
        sections = parser.parse_string(markdown)

        assert sections[0].orientation == Orientation.LANDSCAPE
        assert sections[1].orientation == Orientation.PORTRAIT

    def test_complex_content_with_code_blocks(self, parser):
        """Test section content with code blocks."""
        markdown = """# Code Example
This section has code:

```python
def hello():
    print("Hello")
```

More text after code.
"""
        sections = parser.parse_string(markdown)

        assert len(sections) == 1
        assert "def hello():" in sections[0].content
        assert "More text" in sections[0].content
