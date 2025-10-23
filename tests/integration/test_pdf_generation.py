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
