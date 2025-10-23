"""
Integration tests for markdown-based document generation.
"""

import pytest
from pathlib import Path
from docco import Document, Orientation


class TestMarkdownDocument:
    """Integration tests for loading documents from markdown files."""

    @pytest.fixture
    def sample_markdown(self, tmp_path):
        """Create a sample markdown file for testing."""
        md_file = tmp_path / "sample.md"
        md_file.write_text("""# Introduction
This is the **introduction** section with markdown formatting.

## Background
Some background information here.

<!-- landscape -->
## System Architecture
This section is in landscape mode.

| Component | Technology |
|-----------|------------|
| Engine    | WeasyPrint |
| Parser    | markdown-it-py |

<!-- portrait -->
## Implementation Details
Back to portrait orientation.

<!-- addendum -->
# Appendix A
This is an appendix section.

<!-- notoc -->
## Internal Notes
This section won't appear in the table of contents.
""", encoding="utf-8")
        return md_file

    def test_load_from_markdown(self, sample_markdown):
        """Test loading a document from markdown file."""
        doc = Document(title="Test Document")
        doc.load_from_markdown(sample_markdown)

        # Should have 6 sections
        assert len(doc) == 6

        # Check first section
        assert doc.sections[0].level == 1
        assert doc.sections[0].title == "Introduction"
        assert "introduction" in doc.sections[0].content.lower()

        # Check subsection
        assert doc.sections[1].level == 2
        assert doc.sections[1].title == "Background"

    def test_markdown_with_orientation_directives(self, sample_markdown):
        """Test that orientation directives are respected."""
        doc = Document(title="Test Document")
        doc.load_from_markdown(sample_markdown)

        # Find landscape and portrait sections
        landscape_section = doc.sections[2]  # System Architecture
        portrait_section = doc.sections[3]  # Implementation Details

        assert landscape_section.title == "System Architecture"
        assert landscape_section.orientation == Orientation.LANDSCAPE

        assert portrait_section.title == "Implementation Details"
        assert portrait_section.orientation == Orientation.PORTRAIT

    def test_markdown_with_addendum_directive(self, sample_markdown):
        """Test that addendum directive creates level 0 sections."""
        doc = Document(title="Test Document")
        doc.load_from_markdown(sample_markdown)

        # Find appendix section
        appendix_section = doc.sections[4]

        assert appendix_section.title == "Appendix A"
        assert appendix_section.level == 0  # Addendum level

    def test_markdown_with_notoc_directive(self, sample_markdown):
        """Test that notoc directive excludes sections from TOC."""
        doc = Document(title="Test Document")
        doc.load_from_markdown(sample_markdown)

        # Find hidden section
        hidden_section = doc.sections[5]

        assert hidden_section.title == "Internal Notes"
        assert hidden_section.exclude_from_toc is True

    def test_build_html_from_markdown(self, sample_markdown):
        """Test building HTML from markdown-loaded document."""
        doc = Document(
            title="Test Document",
            subtitle="From Markdown",
            date="2025-10-23"
        )
        doc.load_from_markdown(sample_markdown)

        html = doc.build_html()

        # Check document structure
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Document</title>" in html

        # Check title page
        assert '<div class="title-page">' in html
        assert "Test Document" in html

        # Check TOC
        assert "Table of Contents" in html

        # Check content sections are present
        assert "Introduction" in html
        assert "System Architecture" in html

    def test_toc_excludes_notoc_sections(self, sample_markdown):
        """Test that TOC doesn't include sections marked with notoc."""
        doc = Document(title="Test Document")
        doc.load_from_markdown(sample_markdown)

        html = doc.build_html()

        # TOC should not contain "Internal Notes"
        toc_start = html.find("Table of Contents")
        toc_end = html.find('<div class="content">')
        toc_section = html[toc_start:toc_end]

        assert "Internal Notes" not in toc_section

        # But content should still contain it
        assert "Internal Notes" in html

    def test_automatic_numbering_from_markdown(self, sample_markdown):
        """Test that sections from markdown get numbered correctly."""
        doc = Document(title="Test Document")
        doc.load_from_markdown(sample_markdown)

        # Trigger numbering
        doc._ensure_numbered()

        # Check numbering
        assert doc.sections[0].number == "1"  # Introduction
        assert doc.sections[1].number == "1.1"  # Background
        assert doc.sections[2].number == "1.2"  # System Architecture
        assert doc.sections[3].number == "1.3"  # Implementation Details
        assert doc.sections[4].number == "A"  # Appendix A (addendum)

    def test_render_pdf_from_markdown(self, sample_markdown, tmp_path):
        """Test complete workflow from markdown to PDF."""
        doc = Document(
            title="Test Document",
            subtitle="Integration Test",
            date="2025-10-23"
        )
        doc.load_from_markdown(sample_markdown)

        output_pdf = tmp_path / "output.pdf"
        result_path = doc.render_pdf(output_pdf)

        # Check PDF was created
        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_mixed_markdown_and_manual_sections(self, sample_markdown):
        """Test combining markdown-loaded sections with manually added ones."""
        doc = Document(title="Test Document")

        # Add manual section first
        doc.add_section(level=1, title="Manual Section", content="Manual content.")

        # Load from markdown
        doc.load_from_markdown(sample_markdown)

        # Add another manual section
        doc.add_section(level=1, title="Final Section", content="Final content.")

        # Should have manual + markdown + manual sections
        assert doc.sections[0].title == "Manual Section"
        assert doc.sections[1].title == "Introduction"
        assert doc.sections[-1].title == "Final Section"

    def test_method_chaining(self, sample_markdown, tmp_path):
        """Test that load_from_markdown supports method chaining."""
        output_pdf = tmp_path / "chained.pdf"

        # Chain load_from_markdown with render_pdf
        doc = (Document(title="Chained Document")
               .load_from_markdown(sample_markdown)
               .render_pdf(output_pdf))

        assert output_pdf.exists()

    def test_multiple_markdown_files(self, tmp_path):
        """Test loading from multiple markdown files."""
        md1 = tmp_path / "part1.md"
        md1.write_text("""# Part One
Content for part one.
""", encoding="utf-8")

        md2 = tmp_path / "part2.md"
        md2.write_text("""# Part Two
Content for part two.
""", encoding="utf-8")

        doc = Document(title="Multi-Part Document")
        doc.load_from_markdown(md1)
        doc.load_from_markdown(md2)

        assert len(doc) == 2
        assert doc.sections[0].title == "Part One"
        assert doc.sections[1].title == "Part Two"
