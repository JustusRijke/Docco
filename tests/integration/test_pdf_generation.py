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
no_headers_first_page: true
---

<div class="title-page">
<h1>Complete Test Document</h1>
<p class="subtitle">Integration Test</p>
<p class="date">2025-10-23</p>
<p class="author">Test Suite</p>
</div>

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
        """Test minimal document without frontmatter."""
        md_file = tmp_path / "minimal.md"
        md_file.write_text(
            """# Section

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
        assert (tmp_path / "output" / "test.pdf").exists()

    def test_document_with_images(self, tmp_path):
        """Test document generation with inline images."""
        # Create images directory
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # Create a test SVG image
        svg_file = images_dir / "icon.svg"
        svg_file.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
            '<circle cx="25" cy="25" r="20" fill="red"/>'
            '</svg>'
        )

        # Create markdown with HTML img tags
        md_file = tmp_path / "document.md"
        md_content = """# Images

<img src="images/icon.svg" style="width:50px; margin:10px auto; display:block;" />

<img src="images/icon.svg" class="icon" alt="Figure 1: Test icon" />
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
        assert '<figure>' in html_content, "Figure element not created for img with alt"
        assert '<figcaption>' in html_content, "Figcaption not created for img with alt"

    def test_document_with_missing_image(self, tmp_path):
        """Test that missing images generate error messages."""
        md_file = tmp_path / "document.md"
        md_content = """# Test

<img src="nonexistent.png" style="width:100px" />
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

    def test_multilingual_document(self, tmp_path):
        """Test multilingual document generation with language tags."""
        md_file = tmp_path / "multilingual.md"
        md_content = """---
languages: NL EN DE
---

# Common Section

This appears in all languages.

<!-- lang:NL -->
# Nederlandse Sectie
Nederlandse inhoud
<!-- /lang -->

<!-- lang:EN -->
# English Section
English content
<!-- /lang -->

<!-- lang:DE -->
# Deutsche Sektion
Deutsche Inhalte
<!-- /lang -->
"""
        md_file.write_text(md_content, encoding="utf-8")

        css_file = tmp_path / "style.css"
        css_file.write_text("@page { size: A4; }", encoding="utf-8")

        output_pdf = tmp_path / "multilingual.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify all three PDFs were created
        assert (tmp_path / "multilingual_NL.pdf").exists(), "Dutch PDF not created"
        assert (tmp_path / "multilingual_EN.pdf").exists(), "English PDF not created"
        assert (tmp_path / "multilingual_DE.pdf").exists(), "German PDF not created"

        # Verify debug HTML files
        debug_nl = tmp_path / "debug_NL.html"
        debug_en = tmp_path / "debug_EN.html"
        debug_de = tmp_path / "debug_DE.html"

        assert debug_nl.exists(), "Dutch debug HTML not created"
        assert debug_en.exists(), "English debug HTML not created"
        assert debug_de.exists(), "German debug HTML not created"

        # Verify content filtering
        nl_content = debug_nl.read_text(encoding="utf-8")
        en_content = debug_en.read_text(encoding="utf-8")
        de_content = debug_de.read_text(encoding="utf-8")

        # NL version should have common and Dutch content only
        assert "Common Section" in nl_content
        assert "Nederlandse inhoud" in nl_content
        assert "English content" not in nl_content
        assert "Deutsche Inhalte" not in nl_content

        # EN version should have common and English content only
        assert "Common Section" in en_content
        assert "English content" in en_content
        assert "Nederlandse inhoud" not in en_content
        assert "Deutsche Inhalte" not in en_content

        # DE version should have common and German content only
        assert "Common Section" in de_content
        assert "Deutsche Inhalte" in de_content
        assert "Nederlandse inhoud" not in de_content
        assert "English content" not in de_content

    def test_single_language_no_suffix(self, tmp_path):
        """Test that single language in frontmatter doesn't add suffix."""
        md_file = tmp_path / "single.md"
        md_content = """---
languages: EN
---

# Content

This is a single language document.
"""
        md_file.write_text(md_content, encoding="utf-8")

        css_file = tmp_path / "style.css"
        css_file.write_text("@page { size: A4; }", encoding="utf-8")

        output_pdf = tmp_path / "single.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Should create file without suffix (backward compatible)
        assert output_pdf.exists(), "PDF not created at expected path"
        assert not (tmp_path / "single_EN.pdf").exists(), "PDF should not have language suffix"

    def test_markdown_blocks_in_html(self, tmp_path):
        """Test markdown content inside HTML tags with markdown attribute."""
        md_file = tmp_path / "markdown_blocks.md"
        md_content = """# Document

Regular markdown content here.

<div class="custom-box" markdown>

## Boxed Heading

This is **bold** and this is *italic* inside a div with markdown attribute.

- List item 1
- List item 2
- List item 3

More content here.

</div>

After the box.
"""
        md_file.write_text(md_content, encoding="utf-8")

        css_file = tmp_path / "style.css"
        css_content = """
@page {
    size: A4 portrait;
    margin: 25mm;
}

body {
    font-family: Arial, sans-serif;
}

.custom-box {
    border: 1pt solid #333;
    padding: 10mm;
    margin: 10mm 0;
}
"""
        css_file.write_text(css_content, encoding="utf-8")

        output_pdf = tmp_path / "output.pdf"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert output_pdf.exists(), "PDF file was not created"
        assert output_pdf.stat().st_size > 1000, "PDF file is too small"

        # Verify debug HTML
        debug_html = output_pdf.parent / "debug.html"
        assert debug_html.exists(), "Debug HTML was not created"

        html_content = debug_html.read_text(encoding="utf-8")
        # Check that markdown was converted to HTML
        assert "<strong>bold</strong>" in html_content, "Bold text not converted"
        assert "<em>italic</em>" in html_content, "Italic text not converted"
        assert "<ul>" in html_content, "List not converted"
        assert "Boxed Heading" in html_content, "Content not in HTML"
        # Check that markdown attribute was removed
        assert 'markdown' not in html_content or 'class="custom-box"' in html_content, "markdown attribute should be removed or box class preserved"
