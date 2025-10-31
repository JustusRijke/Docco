"""Tests for PDF conversion."""

import os
import pytest
from docco.pdf import collect_css_files, html_to_pdf


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
    css_file.write_text("body {}")

    metadata = {"css": "style.css"}
    found = collect_css_files(str(md_file), metadata)
    assert len(found) == 1
    assert found[0] == str(css_file)


def test_collect_css_multiple_frontmatter(tmp_path):
    """Test multiple CSS files from frontmatter."""
    md_file = tmp_path / "document.md"
    md_file.write_text("# Test")

    css1 = tmp_path / "page.css"
    css1.write_text("@page {}")
    css2 = tmp_path / "style.css"
    css2.write_text("body {}")

    metadata = {"css": ["page.css", "style.css"]}
    found = collect_css_files(str(md_file), metadata)
    assert len(found) == 2
    assert found[0] == str(css1)
    assert found[1] == str(css2)


def test_collect_css_with_cli_arg(tmp_path):
    """Test that CLI CSS argument is added last."""
    md_file = tmp_path / "document.md"
    md_file.write_text("# Test")

    css1 = tmp_path / "style.css"
    css1.write_text("body {}")
    css2 = tmp_path / "override.css"
    css2.write_text("body { color: red; }")

    metadata = {"css": "style.css"}
    found = collect_css_files(str(md_file), metadata, str(css2))
    assert len(found) == 2
    assert found[0] == str(css1)
    assert found[1] == str(css2)  # CLI arg should be last


def test_collect_css_missing_file(tmp_path, tmp_md):
    """Test that missing CSS files log warning but don't fail."""
    metadata = {"css": "nonexistent.css"}
    found = collect_css_files(tmp_md, metadata)
    assert len(found) == 0


def test_collect_css_empty_metadata(tmp_md):
    """Test with empty metadata."""
    metadata = {}
    found = collect_css_files(tmp_md, metadata)
    assert len(found) == 0


def test_collect_css_cli_only(tmp_path, tmp_md, tmp_css):
    """Test with only CLI CSS argument."""
    metadata = {}
    found = collect_css_files(tmp_md, metadata, tmp_css)
    assert len(found) == 1
    assert found[0] == tmp_css


def test_html_to_pdf_creates_file(tmp_path):
    """Test that PDF file is created."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_with_css(tmp_path, tmp_css):
    """Test PDF generation with CSS styling."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path), [tmp_css])

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_with_multiple_css(tmp_path):
    """Test PDF generation with multiple CSS files."""
    css1 = tmp_path / "style1.css"
    css1.write_text("@page { size: A4; }")
    css2 = tmp_path / "style2.css"
    css2.write_text("body { margin: 0; }")

    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path), [str(css1), str(css2)])

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_without_css(tmp_path):
    """Test PDF generation without CSS."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    output_path = tmp_path / "test.pdf"

    result = html_to_pdf(html_content, str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)
