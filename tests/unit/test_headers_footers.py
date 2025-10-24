"""
Tests for header/footer template processing.
"""

from pathlib import Path
import pytest
from docco.rendering.headers_footers import HeaderFooterProcessor, modify_css_for_running_elements


class TestHeaderFooterProcessor:
    """Tests for HeaderFooterProcessor class."""

    def test_load_templates_both_exist(self, tmp_path):
        """Test loading header and footer when both exist."""
        # Create markdown file
        md_file = tmp_path / "document.md"
        md_file.write_text("# Test")

        # Create header and footer
        header_file = tmp_path / "header.html"
        header_file.write_text("<div>Header</div>")
        footer_file = tmp_path / "footer.html"
        footer_file.write_text("<div>Footer</div>")

        processor = HeaderFooterProcessor(md_file)
        header, footer = processor.load_templates()

        assert header == "<div>Header</div>"
        assert footer == "<div>Footer</div>"

    def test_load_templates_only_header(self, tmp_path):
        """Test loading when only header exists."""
        md_file = tmp_path / "document.md"
        md_file.write_text("# Test")

        header_file = tmp_path / "header.html"
        header_file.write_text("<div>Header</div>")

        processor = HeaderFooterProcessor(md_file)
        header, footer = processor.load_templates()

        assert header == "<div>Header</div>"
        assert footer is None

    def test_load_templates_none_exist(self, tmp_path):
        """Test loading when no header/footer exist."""
        md_file = tmp_path / "document.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        header, footer = processor.load_templates()

        assert header is None
        assert footer is None

    def test_replace_variables_all_fields(self, tmp_path):
        """Test variable replacement with all fields present."""
        md_file = tmp_path / "my_document.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        template = "{{filename}} - {{title}} by {{author}} ({{date}})"
        metadata = {
            "title": "My Title",
            "author": "John Doe",
            "date": "2025-10-23"
        }

        result = processor.replace_variables(template, metadata)
        assert result == "my_document - My Title by John Doe (2025-10-23)"

    def test_replace_variables_missing_fields(self, tmp_path):
        """Test variable replacement with missing fields."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        template = "{{filename}} - {{title}} - {{subtitle}}"
        metadata = {"title": "Only Title"}

        result = processor.replace_variables(template, metadata)
        assert result == "test - Only Title - "

    def test_replace_variables_filename_only(self, tmp_path):
        """Test that filename is extracted correctly."""
        md_file = tmp_path / "product_manual.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        template = "File: {{filename}}"
        metadata = {}

        result = processor.replace_variables(template, metadata)
        assert result == "File: product_manual"

    def test_inject_running_elements_both(self, tmp_path):
        """Test injecting both header and footer running elements."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        html = "<html><body><div>Content</div></body></html>"
        header = "<span>Header</span>"
        footer = "<span>Footer</span>"

        result = processor.inject_running_elements(html, header, footer)

        assert '<div id="header-running" style="position: running(header);"><span>Header</span></div>' in result
        assert '<div id="footer-running" style="position: running(footer);"><span>Footer</span></div>' in result
        assert result.startswith("<html><body>\n")

    def test_inject_running_elements_header_only(self, tmp_path):
        """Test injecting only header running element."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        html = "<html><body><div>Content</div></body></html>"
        header = "<span>Header</span>"

        result = processor.inject_running_elements(html, header, None)

        assert '<div id="header-running"' in result
        assert '<div id="footer-running"' not in result

    def test_inject_running_elements_none(self, tmp_path):
        """Test that HTML is unchanged when no header/footer."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        processor = HeaderFooterProcessor(md_file)
        html = "<html><body><div>Content</div></body></html>"

        result = processor.inject_running_elements(html, None, None)
        assert result == html


class TestModifyCSS:
    """Tests for CSS modification function."""

    def test_modify_css_add_header_footer(self):
        """Test adding header and footer to @page rule."""
        css = """
@page {
    size: A4;
    margin: 25mm;
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=True)

        assert "@top-center { content: element(header); }" in modified
        assert "@bottom-right { content: element(footer); }" in modified
        assert len(warnings) == 0

    def test_modify_css_landscape_page(self):
        """Test modifying @page landscape rule."""
        css = """
@page landscape {
    size: A4 landscape;
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=False)

        assert "@top-center { content: element(header); }" in modified
        assert "@bottom-right { content: element(footer); }" not in modified
        assert len(warnings) == 0

    def test_modify_css_conflict_warning_header(self):
        """Test warning when @page already has @top-center content."""
        css = """
@page {
    @top-center {
        content: "Existing Header";
    }
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=False)

        assert len(warnings) == 1
        assert "already has @top-center content" in warnings[0]
        assert "Replacing with header.html" in warnings[0]
        assert "@top-center { content: element(header); }" in modified
        assert 'content: "Existing Header"' not in modified

    def test_modify_css_conflict_warning_footer(self):
        """Test warning when @page already has @bottom-right content."""
        css = """
@page {
    @bottom-right {
        content: "Page " counter(page);
    }
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=False, has_footer=True)

        assert len(warnings) == 1
        assert "already has @bottom-right content" in warnings[0]
        assert "Replacing with footer.html" in warnings[0]
        assert "@bottom-right { content: element(footer); }" in modified

    def test_modify_css_conflict_warning_both(self):
        """Test warnings for both header and footer conflicts."""
        css = """
@page {
    @top-center {
        content: "Header";
    }
    @bottom-right {
        content: "Footer";
    }
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=True)

        assert len(warnings) == 2
        assert any("@top-center" in w for w in warnings)
        assert any("@bottom-right" in w for w in warnings)

    def test_modify_css_multiple_page_rules(self):
        """Test modifying multiple @page rules."""
        css = """
@page {
    size: A4;
}

@page landscape {
    size: A4 landscape;
}

@page :first {
    margin: 0;
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=True)

        # Count occurrences - should appear in all @page rules except :first
        assert modified.count("@top-center { content: element(header); }") == 2
        assert modified.count("@bottom-right { content: element(footer); }") == 2
        # :first should remain unchanged
        assert "@page :first" in modified

    def test_modify_css_no_changes_when_no_templates(self):
        """Test that CSS is unchanged when no header/footer."""
        css = """
@page {
    size: A4;
    margin: 25mm;
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=False, has_footer=False)

        assert modified == css
        assert len(warnings) == 0

    def test_modify_css_preserves_other_content(self):
        """Test that other CSS content is preserved."""
        css = """
@page {
    size: A4;
    margin: 25mm;
}

body {
    font-family: Arial;
}

h1 {
    color: blue;
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=True)

        assert "body {" in modified
        assert "font-family: Arial;" in modified
        assert "h1 {" in modified
        assert "color: blue;" in modified

    def test_modify_css_skips_first_page(self):
        """Test that @page :first is not modified (title page has no header/footer)."""
        css = """
@page {
    size: A4;
}

@page :first {
    @top-center { content: none; }
    @bottom-right { content: none; }
}
"""
        modified, warnings = modify_css_for_running_elements(css, has_header=True, has_footer=True)

        # Default @page should be modified
        assert "@top-center { content: element(header); }" in modified

        # But @page :first should remain unchanged
        assert "content: none;" in modified
        assert len(warnings) == 0
