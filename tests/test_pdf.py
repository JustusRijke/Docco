"""Tests for PDF conversion."""

import os
import pytest
from docco.pdf import collect_css_content, html_to_pdf


@pytest.fixture
def tmp_css(tmp_path):
    """Create a temporary CSS file."""
    css_file = tmp_path / "test.css"
    css_file.write_text("@page { size: A4; }")
    return str(css_file)


@pytest.fixture
def tmp_md(tmp_path):
    """Create a temporary markdown file."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test")
    return str(md_file)


def test_collect_css_single_frontmatter(tmp_path):
    """Test single CSS file from frontmatter."""
    md_file = tmp_path / "document.md"
    md_file.write_text("# Test")

    css_file = tmp_path / "style.css"
    css_content = "body { color: blue; }"
    css_file.write_text(css_content)

    metadata = {"css": "style.css"}
    content = collect_css_content(str(md_file), metadata)
    assert content == css_content


def test_collect_css_multiple_frontmatter(tmp_path):
    """Test multiple CSS files from frontmatter."""
    md_file = tmp_path / "document.md"
    md_file.write_text("# Test")

    css1_content = "@page { size: A4; }"
    css1 = tmp_path / "page.css"
    css1.write_text(css1_content)

    css2_content = "body { margin: 0; }"
    css2 = tmp_path / "style.css"
    css2.write_text(css2_content)

    metadata = {"css": ["page.css", "style.css"]}
    content = collect_css_content(str(md_file), metadata)
    assert css1_content in content
    assert css2_content in content
    # Content should be joined with newlines
    assert content == f"{css1_content}\n{css2_content}"


def test_collect_css_missing_file(tmp_path, tmp_md):
    """Test that missing CSS files log warning but don't fail."""
    metadata = {"css": "nonexistent.css"}
    content = collect_css_content(tmp_md, metadata)
    assert content == ""


def test_collect_css_empty_metadata(tmp_md):
    """Test with empty metadata."""
    metadata = {}
    content = collect_css_content(tmp_md, metadata)
    assert content == ""


def test_html_to_pdf_creates_file(tmp_path):
    """Test that PDF file is created."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_with_embedded_css(tmp_path):
    """Test PDF generation with embedded CSS in HTML."""
    html_content = """<!DOCTYPE html>
<html>
<head>
<style>
body { color: blue; }
p { font-size: 14px; }
</style>
</head>
<body><p>Test</p></body>
</html>"""
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_without_css(tmp_path):
    """Test PDF generation without CSS."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_with_base_url(tmp_path):
    """Test PDF generation with base_url for relative image paths."""
    try:
        from PIL import Image
        # Create a valid image file
        img = Image.new("RGB", (10, 10), color="red")
        img_file = tmp_path / "test.png"
        img.save(str(img_file))
    except ImportError:
        # Skip test if PIL not available
        pytest.skip("PIL/Pillow not available")

    # HTML with relative image path
    html_content = "<!DOCTYPE html><html><body><img src='test.png'/></body></html>"
    output_path_with_base = tmp_path / "with_base.pdf"
    output_path_without_base = tmp_path / "without_base.pdf"

    # Generate PDF with base_url - should succeed and include the image
    result_with_base = html_to_pdf(html_content, str(output_path_with_base), base_url=str(tmp_path))
    assert os.path.exists(str(output_path_with_base))
    assert result_with_base == str(output_path_with_base)
    size_with_base = os.path.getsize(str(output_path_with_base))

    # Generate PDF without base_url - image won't resolve but PDF should still be created
    html_to_pdf(html_content, str(output_path_without_base))
    assert os.path.exists(str(output_path_without_base))
    size_without_base = os.path.getsize(str(output_path_without_base))

    # PDF with base_url should be larger (contains embedded image)
    assert size_with_base > size_without_base
