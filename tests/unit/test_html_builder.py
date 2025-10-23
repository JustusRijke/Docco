"""
Unit tests for HTMLBuilder.
"""

import pytest
from docco.rendering.html_builder import HTMLBuilder
from docco.core.section import Section


class TestHTMLBuilder:
    """Tests for HTML generation."""

    @pytest.fixture
    def html_builder(self):
        """Create HTMLBuilder instance."""
        return HTMLBuilder()

    def test_build_title_page(self, html_builder):
        """Test title page HTML generation."""
        result = html_builder.build_title_page("My Document", "Subtitle", "2025-10-23")

        assert '<div class="title-page">' in result
        assert "<h1>My Document</h1>" in result
        assert '<p class="subtitle">Subtitle</p>' in result
        assert '<p class="date">2025-10-23</p>' in result

    def test_build_title_page_no_optional(self, html_builder):
        """Test title page without subtitle and date."""
        result = html_builder.build_title_page("My Document")

        assert "<h1>My Document</h1>" in result
        assert "subtitle" not in result
        assert "date" not in result

    def test_build_toc(self, html_builder, numbered_sections):
        """Test table of contents generation."""
        result = html_builder.build_toc(numbered_sections)

        assert '<div class="toc-page">' in result
        assert "<h1>Table of Contents</h1>" in result
        assert '<nav class="toc">' in result
        assert 'href="#section-1"' in result
        assert 'href="#section-1-1"' in result
        assert "1 Introduction" in result
        assert "1.1 Purpose" in result

    def test_build_toc_indentation_classes(self, html_builder, numbered_sections):
        """Test TOC has correct indentation classes."""
        result = html_builder.build_toc(numbered_sections)

        assert 'class="toc-level-1"' in result
        assert 'class="toc-level-2"' in result

    def test_build_section(self, html_builder):
        """Test single section HTML generation."""
        section = Section(
            level=1,
            title="Introduction",
            content="This is **bold** text.",
            number="1"
        )

        result = html_builder.build_section(section)

        assert '<h1 class="section" id="section-1">1 Introduction</h1>' in result
        assert "<strong>bold</strong>" in result  # Markdown converted

    def test_build_section_level_2(self, html_builder):
        """Test level 2 section uses h2 tag."""
        section = Section(level=2, title="Subsection", content="Content", number="1.1")

        result = html_builder.build_section(section)

        assert '<h2 class="section" id="section-1-1">' in result
        assert "1.1 Subsection" in result

    def test_build_section_addendum(self, html_builder):
        """Test addendum section (level=0) uses h1."""
        section = Section(level=0, title="Appendix", content="Content", number="A")

        result = html_builder.build_section(section)

        assert '<h1 class="section" id="section-a">' in result
        assert "A Appendix" in result

    def test_build_section_empty_content(self, html_builder):
        """Test section with empty content."""
        section = Section(level=1, title="Empty", content="", number="1")

        result = html_builder.build_section(section)

        assert '<h1 class="section"' in result
        assert "1 Empty" in result

    def test_build_document(self, html_builder, numbered_sections):
        """Test full document generation."""
        result = html_builder.build_document(
            sections=numbered_sections,
            title="Test Doc",
            subtitle="Test Subtitle",
            date="2025-10-23"
        )

        assert "<!DOCTYPE html>" in result
        assert '<html lang="en">' in result
        assert "<title>Test Doc</title>" in result
        assert '<div class="title-page">' in result
        assert '<div class="toc-page">' in result
        assert '<div class="content">' in result
        assert "</html>" in result

    def test_make_section_id(self, html_builder):
        """Test section ID generation."""
        assert html_builder._make_section_id("1") == "section-1"
        assert html_builder._make_section_id("1.2") == "section-1-2"
        assert html_builder._make_section_id("1.2.3") == "section-1-2-3"
        assert html_builder._make_section_id("A") == "section-a"

    def test_escape_html(self, html_builder):
        """Test HTML escaping."""
        assert html_builder._escape_html("a & b") == "a &amp; b"
        assert html_builder._escape_html("a < b") == "a &lt; b"
        assert html_builder._escape_html("a > b") == "a &gt; b"
        assert html_builder._escape_html('"quotes"') == "&quot;quotes&quot;"
        assert html_builder._escape_html("'apostrophe'") == "&#39;apostrophe&#39;"

    def test_escape_html_in_title(self, html_builder):
        """Test that titles are escaped."""
        result = html_builder.build_title_page("Test & Title <script>")
        assert "Test &amp; Title &lt;script&gt;" in result
        assert "<script>" not in result
