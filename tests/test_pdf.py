"""Tests for PDF conversion."""

import os
import pytest
from pathlib import Path
from docco.pdf import collect_css_content, html_to_pdf


def path_to_file_url(file_path):
    """Convert file path to proper file:// URL (cross-platform)."""
    return Path(file_path).as_uri()


def get_pdf_image_info(pdf_path):
    """
    Extract image info from PDF using PyMuPDF.

    Returns list of dicts with keys: width, height, xres, yres
    Returns None if PyMuPDF is not available.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    try:
        doc = fitz.open(str(pdf_path))
        images_info = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]  # xref is the first element
                img_dict = doc.extract_image(xref)

                images_info.append(
                    {
                        "width": img_dict["width"],
                        "height": img_dict["height"],
                        "xres": img_dict["xres"],  # DPI in X direction
                        "yres": img_dict["yres"],  # DPI in Y direction
                    }
                )

        doc.close()
        return images_info
    except Exception:
        return None


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


@pytest.fixture
def highres_image(tmp_path):
    """Create a high-resolution test image (600 DPI, 3000x2000px)."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("PIL/Pillow not available")

    # Create a 3000x2000 pixel image at 600 DPI
    # This simulates a high-res photo that should be downsampled
    img = Image.new("RGB", (3000, 2000), color="blue")
    img_path = tmp_path / "highres.png"
    img.save(str(img_path), dpi=(600, 600))
    return str(img_path)


def test_collect_css_single_frontmatter(tmp_path):
    """Test single CSS file from frontmatter."""
    md_file = tmp_path / "document.md"
    md_file.write_text("# Test")

    css_file = tmp_path / "style.css"
    css_content = "body { color: blue; }"
    css_file.write_text(css_content)

    metadata = {"css": "style.css"}
    result = collect_css_content(str(md_file), metadata)
    assert result["inline"] == css_content
    assert result["external"] == []


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
    result = collect_css_content(str(md_file), metadata)
    assert css1_content in result["inline"]
    assert css2_content in result["inline"]
    # Content should be joined with newlines
    assert result["inline"] == f"{css1_content}\n{css2_content}"
    assert result["external"] == []


def test_collect_css_missing_file(tmp_path, tmp_md):
    """Test that missing CSS files log warning but don't fail."""
    metadata = {"css": "nonexistent.css"}
    result = collect_css_content(tmp_md, metadata)
    assert result["inline"] == ""
    assert result["external"] == []


def test_collect_css_empty_metadata(tmp_md):
    """Test with empty metadata."""
    metadata = {}
    result = collect_css_content(tmp_md, metadata)
    assert result["inline"] == ""
    assert result["external"] == []


def test_html_to_pdf_creates_file(tmp_path):
    """Test that PDF file is created."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    html_path = tmp_path / "test.html"
    output_path = tmp_path / "test.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    result = html_to_pdf(str(html_path), str(output_path))

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
    html_path = tmp_path / "test.html"
    output_path = tmp_path / "test.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    result = html_to_pdf(str(html_path), str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)


def test_html_to_pdf_without_css(tmp_path):
    """Test PDF generation without CSS."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    html_path = tmp_path / "test.html"
    output_path = tmp_path / "test.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    result = html_to_pdf(str(html_path), str(output_path))

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
    html_path = tmp_path / "test.html"
    output_path_with_base = tmp_path / "with_base.pdf"
    output_path_without_base = tmp_path / "without_base.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate PDF with base_url - should succeed and include the image
    result_with_base = html_to_pdf(
        str(html_path), str(output_path_with_base), base_url=str(tmp_path)
    )
    assert os.path.exists(str(output_path_with_base))
    assert result_with_base == str(output_path_with_base)
    size_with_base = os.path.getsize(str(output_path_with_base))

    # When HTML is provided as a file, WeasyPrint uses the file's directory as base_url by default
    # So even without explicit base_url, the relative image will resolve
    html_to_pdf(str(html_path), str(output_path_without_base))
    assert os.path.exists(str(output_path_without_base))
    size_without_base = os.path.getsize(str(output_path_without_base))

    # Both PDFs should contain the image (both have same size) since HTML file location provides base path
    assert size_with_base == size_without_base
    # Verify PDF is not empty (contains image)
    assert size_with_base > 1000


def test_html_to_pdf_dpi_with_basic_img_tag(tmp_path, highres_image):
    """Test DPI downsampling with basic <img> tag and CSS constraints."""
    # HTML with img tag and CSS that constrains image size
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{
    max-width: 100%;
    height: auto;
}}
</style>
</head>
<body>
<img src="{path_to_file_url(highres_image)}" alt="test">
</body>
</html>"""

    html_path = tmp_path / "test.html"
    output_300dpi = tmp_path / "test_300dpi.pdf"
    output_no_dpi = tmp_path / "test_no_dpi.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate with DPI limit
    html_to_pdf(str(html_path), str(output_300dpi), dpi=300)

    # Generate without DPI limit
    html_to_pdf(str(html_path), str(output_no_dpi))

    # Extract image info
    images_300dpi = get_pdf_image_info(output_300dpi)
    images_no_dpi = get_pdf_image_info(output_no_dpi)

    if images_300dpi is None or images_no_dpi is None:
        pytest.skip("PyMuPDF not available for image verification")

    # Verify DPI=300 downsampled the image
    assert len(images_300dpi) == 1
    assert len(images_no_dpi) == 1

    # Image with DPI=300 should have smaller dimensions than no-DPI version
    # Original is 3000x2000, should be downsampled when DPI is limited
    assert images_300dpi[0]["width"] < images_no_dpi[0]["width"]
    assert images_300dpi[0]["height"] < images_no_dpi[0]["height"]


def test_html_to_pdf_dpi_with_css_styled_images(tmp_path, highres_image):
    """Test DPI downsampling with CSS-styled images in different scenarios."""
    # Test various CSS styling approaches
    test_cases = [
        ("max-width-percent", "max-width: 100%; height: auto;"),
        ("fixed-width", "width: 600px;"),
        ("max-width-px", "max-width: 800px;"),
    ]

    for test_name, css_style in test_cases:
        html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
<img src="{path_to_file_url(highres_image)}" alt="test" style="{css_style}">
</body>
</html>"""

        html_path = tmp_path / f"test_{test_name}.html"
        output_path = tmp_path / f"test_{test_name}.pdf"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        html_to_pdf(str(html_path), str(output_path), dpi=300)

        assert os.path.exists(str(output_path))

        # Verify image was embedded
        images = get_pdf_image_info(output_path)
        assert len(images) >= 1, f"No images found in {test_name} PDF"


def test_html_to_pdf_dpi_with_figure_element(tmp_path, highres_image):
    """Test DPI downsampling with <figure> and <figcaption> elements."""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
figure {{
    margin: 0;
}}
figure img {{
    max-width: 100%;
    height: auto;
}}
</style>
</head>
<body>
<figure>
    <img src="{path_to_file_url(highres_image)}" alt="High-res image">
    <figcaption>This is a test image</figcaption>
</figure>
</body>
</html>"""

    html_path = tmp_path / "test_figure.html"
    output_path = tmp_path / "test_figure.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    html_to_pdf(str(html_path), str(output_path), dpi=300)

    assert os.path.exists(str(output_path))

    # Verify image was embedded and potentially downsampled
    images = get_pdf_image_info(output_path)
    assert len(images) == 1
    # With max-width: 100%, the image should be processed by DPI limit
    assert images[0]["width"] > 0
    assert images[0]["height"] > 0


def test_html_to_pdf_multiple_images_with_dpi(tmp_path, highres_image):
    """Test DPI downsampling with multiple images on same page."""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{
    max-width: 100%;
    height: auto;
}}
</style>
</head>
<body>
<div>
    <img src="{path_to_file_url(highres_image)}" alt="image1">
</div>
<div>
    <img src="{path_to_file_url(highres_image)}" alt="image2">
</div>
<div>
    <img src="{path_to_file_url(highres_image)}" alt="image3">
</div>
</body>
</html>"""

    html_path = tmp_path / "test_multiple.html"
    output_path = tmp_path / "test_multiple.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    html_to_pdf(str(html_path), str(output_path), dpi=300)

    assert os.path.exists(str(output_path))

    # Verify all images were embedded
    images = get_pdf_image_info(output_path)
    if images is not None:
        # Should have 3 images (or 1 if WeasyPrint deduplicates)
        assert len(images) >= 1
        assert len(images) <= 3


def test_html_to_pdf_without_dpi_parameter(tmp_path):
    """Test that PDF generation works without DPI parameter."""
    html_content = "<!DOCTYPE html><html><body><p>Test</p></body></html>"
    html_path = tmp_path / "test_no_dpi.html"
    output_path = tmp_path / "test_no_dpi.pdf"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Test without DPI parameter (default behavior)
    result = html_to_pdf(str(html_path), str(output_path))

    assert os.path.exists(str(output_path))
    assert result == str(output_path)
