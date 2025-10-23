"""
Integration tests for end-to-end PDF generation.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
from docco.cli import cli


class TestEndToEndGeneration:
    """End-to-end tests for PDF generation."""

    def test_complete_document_generation(self, tmp_path):
        """Test complete document generation with all features."""
        # Create markdown file with complex content
        md_file = tmp_path / "document.md"
        md_content = """---
title: Complete Test Document
subtitle: Integration Test
date: 2025-10-23
author: Test Suite
---

# Introduction

This is the **introduction** section with various markdown elements.

## Purpose

The purpose includes:
- Lists with *emphasis*
- **Bold text**
- `inline code`

### Sub-section

Even deeper nesting works.

# Technical Details

## Code Examples

Here's a code block:

```python
def hello():
    print("Hello, world!")
```

## Tables

| Feature | Status |
|---------|--------|
| Markdown | ✓ |
| CSS | ✓ |
| PDF | ✓ |

# Conclusion

Final thoughts go here.
"""
        md_file.write_text(md_content, encoding="utf-8")

        # Create CSS file
        css_file = tmp_path / "style.css"
        css_content = """
@page {
    size: A4 portrait;
    margin: 25mm;

    @top-center {
        content: "Test Document";
        font-size: 9pt;
        color: #666;
    }

    @bottom-right {
        content: "Page " counter(page);
        font-size: 9pt;
    }
}

@page :first {
    @top-center { content: none; }
    @bottom-right { content: none; }
}

body {
    font-family: Arial, sans-serif;
    font-size: 11pt;
}

.title-page {
    page-break-after: always;
    text-align: center;
    padding-top: 100mm;
}

.title-page h1 {
    font-size: 24pt;
}

h1 {
    font-size: 18pt;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    page-break-after: avoid;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 5mm 0;
}

th, td {
    border: 1pt solid #ccc;
    padding: 3mm;
}

pre {
    background-color: #f5f5f5;
    padding: 5mm;
}
"""
        css_file.write_text(css_content, encoding="utf-8")

        # Generate PDF
        output_pdf = tmp_path / "output.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output_pdf.exists(), "PDF file was not created"
        assert output_pdf.stat().st_size > 1000, "PDF file is too small"

        # Verify debug HTML was created
        debug_html = output_pdf.parent / "debug.html"
        assert debug_html.exists(), "Debug HTML was not created"

        # Verify debug HTML contains expected content
        html_content = debug_html.read_text(encoding="utf-8")
        assert "Complete Test Document" in html_content
        assert "Introduction" in html_content
        assert "Technical Details" in html_content
        assert "<table>" in html_content
        assert "<code>" in html_content

    def test_minimal_document(self, tmp_path):
        """Test minimal document with only required fields."""
        md_file = tmp_path / "minimal.md"
        md_file.write_text(
            """---
title: Minimal Doc
---

# Section

Content.
""",
            encoding="utf-8",
        )

        css_file = tmp_path / "minimal.css"
        css_file.write_text("@page { size: A4; }", encoding="utf-8")

        output_pdf = tmp_path / "minimal.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        assert result.exit_code == 0
        assert output_pdf.exists()

    def test_default_output_path(self, sample_markdown_file, sample_css_file, tmp_path, monkeypatch):
        """Test that default output path works."""
        # Change to tmp directory so default output/ is created there
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["build", str(sample_markdown_file), str(sample_css_file)])

        assert result.exit_code == 0
        assert (tmp_path / "output" / "document.pdf").exists()

    def test_document_with_images(self, tmp_path):
        """Test document generation with inline images."""
        pytest.importorskip("PIL")  # Skip if Pillow not installed

        from PIL import Image

        # Create images directory
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # Create a test PNG image
        png_file = images_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(png_file, format='PNG')

        # Create a test SVG image
        svg_file = images_dir / "icon.svg"
        svg_file.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            '<circle cx="25" cy="25" r="20" fill="red"/>'
            '</svg>'
        )

        # Create markdown with image directives
        md_file = tmp_path / "document.md"
        md_content = """---
title: Image Test Document
subtitle: Testing Image Support
date: 2025-10-23
---

# Images

Testing inline image support.

## PNG Image with Inline Style

<!-- img "images/test.png" "width:50px; margin:10px auto; display:block;" -->

## SVG Image with CSS Class

<!-- img "images/icon.svg" "class:icon" -->

Done!
"""
        md_file.write_text(md_content, encoding="utf-8")

        # Create CSS with image styles
        css_file = tmp_path / "style.css"
        css_content = """
@page {
    size: A4 portrait;
    margin: 25mm;
}

body {
    font-family: Arial, sans-serif;
}

.title-page {
    page-break-after: always;
    text-align: center;
    padding-top: 100mm;
}

img {
    max-width: 100%;
    height: auto;
}

img.icon {
    width: 50px;
    height: auto;
    display: block;
    margin: 10px auto;
}
"""
        css_file.write_text(css_content, encoding="utf-8")

        # Generate PDF
        output_pdf = tmp_path / "output.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output_pdf.exists(), "PDF file was not created"
        assert output_pdf.stat().st_size > 1000, "PDF file is too small"

        # Verify debug HTML contains image tags
        debug_html = output_pdf.parent / "debug.html"
        assert debug_html.exists()

        html_content = debug_html.read_text(encoding="utf-8")
        assert '<img' in html_content, "No img tags found in HTML"
        assert 'src="file://' in html_content, "Image src not using file:// URL"
        assert 'class="icon"' in html_content, "CSS class not applied to image"
        assert 'width:50px' in html_content, "Inline style not applied"

    def test_document_with_missing_image(self, tmp_path):
        """Test that missing images generate error messages."""
        md_file = tmp_path / "document.md"
        md_content = """---
title: Missing Image Test
---

# Test

<!-- img "nonexistent.png" "width:100px" -->
"""
        md_file.write_text(md_content, encoding="utf-8")

        css_file = tmp_path / "style.css"
        css_file.write_text("@page { size: A4; }", encoding="utf-8")

        output_pdf = tmp_path / "output.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Should still succeed but with error output
        assert result.exit_code == 0
        assert "Image error" in result.output or "Image not found" in result.output

        # Check debug HTML contains error message
        debug_html = output_pdf.parent / "debug.html"
        html_content = debug_html.read_text(encoding="utf-8")
        assert 'image-error' in html_content or 'Image error' in html_content
