"""
Tests for CLI functionality.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from docco.cli import cli, _parse_frontmatter, _escape_html


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_with_frontmatter(self):
        """Test parsing markdown with YAML frontmatter."""
        content = """---
languages: en fr
no_headers_first_page: true
---

# Content here
"""
        metadata, markdown = _parse_frontmatter(content)

        assert metadata["languages"] == "en fr"
        assert metadata["no_headers_first_page"] is True
        assert markdown.strip() == "# Content here"

    def test_parse_without_frontmatter(self):
        """Test parsing markdown without frontmatter."""
        content = "# Just markdown"
        metadata, markdown = _parse_frontmatter(content)

        assert metadata == {}
        assert markdown == content

    def test_parse_incomplete_frontmatter(self):
        """Test parsing with incomplete frontmatter (missing closing ---)."""
        content = """---
title: Test
# Missing closing ---
"""
        metadata, markdown = _parse_frontmatter(content)

        # Should return empty metadata and original content
        assert metadata == {}
        assert markdown == content


class TestEscapeHtml:
    """Tests for HTML escaping."""

    def test_escape_special_characters(self):
        """Test escaping HTML special characters."""
        assert _escape_html("<script>") == "&lt;script&gt;"
        assert _escape_html("A & B") == "A &amp; B"
        assert _escape_html('"quoted"') == "&quot;quoted&quot;"
        assert _escape_html("'single'") == "&#39;single&#39;"


class TestCliBuild:
    """Tests for CLI build command."""

    def test_build_command_success(self, sample_markdown_file, sample_css_file, tmp_output_dir):
        """Test successful PDF generation via CLI."""
        runner = CliRunner()
        output_pdf = tmp_output_dir / "test.pdf"

        result = runner.invoke(
            cli,
            ["build", str(sample_markdown_file), str(sample_css_file), "-o", str(output_pdf)],
        )

        assert result.exit_code == 0
        assert output_pdf.exists()
        assert "✓ PDF generated" in result.output

    def test_build_command_no_frontmatter(self, tmp_path, sample_css_file, tmp_output_dir):
        """Test build succeeds even without frontmatter."""
        md_file = tmp_path / "no_frontmatter.md"
        md_file.write_text("# Just content", encoding="utf-8")
        output_pdf = tmp_output_dir / "test.pdf"

        runner = CliRunner()
        result = runner.invoke(cli, ["build", str(md_file), str(sample_css_file), "-o", str(output_pdf)])

        assert result.exit_code == 0
        assert output_pdf.exists()

    def test_build_command_nonexistent_markdown(self, sample_css_file):
        """Test build fails with nonexistent markdown file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["build", "nonexistent.md", str(sample_css_file)])

        assert result.exit_code != 0

    def test_build_command_nonexistent_css(self, sample_markdown_file):
        """Test build fails with nonexistent CSS file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["build", str(sample_markdown_file), "nonexistent.css"])

        assert result.exit_code != 0


class TestParseSections:
    """Tests for section parsing with orientation directives."""

    def test_parse_sections_with_landscape_directive(self):
        """Test parsing markdown with landscape directive."""
        from docco.cli import _parse_sections

        content = """# First Section

Portrait content here.

<!-- landscape -->
# Second Section

Landscape content here.

<!-- portrait -->
# Third Section

Back to portrait.
"""
        sections = _parse_sections(content)

        assert len(sections) == 3
        assert sections[0]["title"] == "First Section"
        assert sections[0]["orientation"] == "portrait"
        assert sections[1]["title"] == "Second Section"
        assert sections[1]["orientation"] == "landscape"
        assert sections[2]["title"] == "Third Section"
        assert sections[2]["orientation"] == "portrait"

    def test_parse_sections_default_portrait(self):
        """Test that sections default to portrait orientation."""
        from docco.cli import _parse_sections

        content = """# Section One

No directive, should be portrait.

# Section Two

Still portrait.
"""
        sections = _parse_sections(content)

        assert all(s["orientation"] == "portrait" for s in sections)

    def test_parse_sections_generates_ids(self):
        """Test that section IDs are generated from section numbers."""
        from docco.cli import _parse_sections

        content = """# My First Section

Content here.

# Another Section!

More content.
"""
        sections = _parse_sections(content)

        assert sections[0]["id"] == "section-1"
        assert sections[1]["id"] == "section-2"

    def test_parse_sections_hierarchical_numbering(self):
        """Test hierarchical section numbering (1, 1.1, 1.1.1, 1.2, 2)."""
        from docco.cli import _parse_sections

        content = """# First Chapter

Content.

## First Section

Subsection content.

### First Subsection

Deep content.

### Second Subsection

More deep content.

## Second Section

Another subsection.

# Second Chapter

New chapter.
"""
        sections = _parse_sections(content)

        assert sections[0]["number"] == "1"
        assert sections[0]["level"] == 1
        assert sections[1]["number"] == "1.1"
        assert sections[1]["level"] == 2
        assert sections[2]["number"] == "1.1.1"
        assert sections[2]["level"] == 3
        assert sections[3]["number"] == "1.1.2"
        assert sections[3]["level"] == 3
        assert sections[4]["number"] == "1.2"
        assert sections[4]["level"] == 2
        assert sections[5]["number"] == "2"
        assert sections[5]["level"] == 1

    def test_parse_sections_with_addendum(self):
        """Test appendix sections with letter numbering."""
        from docco.cli import _parse_sections

        content = """# Regular Section

Normal content.

<!-- addendum -->
# First Appendix

Appendix content.

<!-- addendum -->
# Second Appendix

More appendix content.
"""
        sections = _parse_sections(content)

        assert len(sections) == 3
        assert sections[0]["number"] == "1"
        assert sections[0]["is_addendum"] is False
        assert sections[0]["level"] == 1

        assert sections[1]["number"] == "A"
        assert sections[1]["is_addendum"] is True
        assert sections[1]["level"] == 0

        assert sections[2]["number"] == "B"
        assert sections[2]["is_addendum"] is True
        assert sections[2]["level"] == 0

    def test_parse_sections_mixed_addendum_and_regular(self):
        """Test mixing regular sections and appendices."""
        from docco.cli import _parse_sections

        content = """# Introduction

Content.

## Details

More content.

<!-- addendum -->
# Appendix A Title

Appendix.

<!-- addendum -->
## Appendix B Title

Another appendix (H2 but still lettered).
"""
        sections = _parse_sections(content)

        assert sections[0]["number"] == "1"
        assert sections[1]["number"] == "1.1"
        assert sections[2]["number"] == "A"
        assert sections[2]["is_addendum"] is True
        assert sections[3]["number"] == "B"
        assert sections[3]["is_addendum"] is True

    def test_parse_sections_numbering_in_html(self):
        """Test that section numbers appear in generated HTML."""
        from docco.cli import _parse_sections

        content = """# Introduction

Content here.

## Subsection

More content.
"""
        sections = _parse_sections(content)

        assert "1 Introduction" in sections[0]["html"]
        assert "1.1 Subsection" in sections[1]["html"]
        assert 'id="section-1"' in sections[0]["html"]
        assert 'id="section-1-1"' in sections[1]["html"]


class TestBuildToc:
    """Tests for table of contents generation."""

    def test_build_toc_from_sections(self):
        """Test TOC generation from sections with numbers."""
        from docco.cli import _build_toc

        sections = [
            {"title": "Introduction", "level": 1, "id": "section-1", "number": "1", "is_addendum": False},
            {"title": "Details", "level": 2, "id": "section-1-1", "number": "1.1", "is_addendum": False},
            {"title": "Conclusion", "level": 1, "id": "section-2", "number": "2", "is_addendum": False},
        ]

        toc = _build_toc(sections)

        assert "Table of Contents" in toc
        assert "1 Introduction" in toc
        assert "1.1 Details" in toc
        assert "2 Conclusion" in toc
        assert 'href="#section-1"' in toc
        assert 'href="#section-1-1"' in toc
        assert 'class="toc-level-1"' in toc
        assert 'class="toc-level-2"' in toc

    def test_build_toc_with_addendum(self):
        """Test TOC includes appendix sections with letter numbering."""
        from docco.cli import _build_toc

        sections = [
            {"title": "Introduction", "level": 1, "id": "section-1", "number": "1", "is_addendum": False},
            {"title": "First Appendix", "level": 0, "id": "section-a", "number": "A", "is_addendum": True},
            {"title": "Second Appendix", "level": 0, "id": "section-b", "number": "B", "is_addendum": True},
        ]

        toc = _build_toc(sections)

        assert "1 Introduction" in toc
        assert "A First Appendix" in toc
        assert "B Second Appendix" in toc
        assert 'class="toc-level-addendum"' in toc
        assert 'href="#section-a"' in toc
        assert 'href="#section-b"' in toc

    def test_build_toc_empty_for_no_sections(self):
        """Test that TOC is empty when there are no sections."""
        from docco.cli import _build_toc

        sections = [{"title": None, "level": 0, "id": None, "number": None, "is_addendum": False}]
        toc = _build_toc(sections)

        assert toc == ""

    def test_build_toc_escapes_special_characters_once(self):
        """Test that TOC entries with special characters are escaped only once."""
        from docco.cli import _build_toc

        sections = [
            {"title": "Links & Quotes", "level": 2, "id": "section-2-4", "number": "2.4", "is_addendum": False},
            {"title": "Code <snippet>", "level": 1, "id": "section-3", "number": "3", "is_addendum": False},
        ]

        toc = _build_toc(sections)

        # Should escape once (& -> &amp;), not twice (& -> &amp; -> &amp;amp;)
        assert "2.4 Links &amp; Quotes" in toc
        assert "&amp;amp;" not in toc
        # Should escape angle brackets
        assert "3 Code &lt;snippet&gt;" in toc
        assert "<snippet>" not in toc


class TestCliVersion:
    """Tests for version command."""

    def test_version_command(self):
        """Test version command output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "0.3.0" in result.output
