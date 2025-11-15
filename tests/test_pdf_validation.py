"""Tests for PDF validation module."""

import os
import tempfile
import pytest

# Import the module to test
from docco.pdf_validation import check_pdf_image_dpi, validate_and_warn_pdf_images

try:
    import fitz  # PyMuPDF  # noqa: F401
    from PIL import Image

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="PyMuPDF or PIL not available")
def test_check_pdf_image_dpi_with_low_dpi_images():
    """Test detection of low DPI images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small low-res image
        img = Image.new("RGB", (100, 100), color="red")
        img_path = os.path.join(tmpdir, "lowres.png")
        img.save(img_path)

        # Create HTML with image
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
<img src="file://{img_path}" alt="test">
</body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        from weasyprint import HTML

        HTML(html_path).write_pdf(pdf_path)

        # Check DPI
        result = check_pdf_image_dpi(pdf_path, threshold=300)

        assert result is not None
        assert result["total_images"] >= 1
        assert len(result["low_dpi_images"]) >= 1

        # Verify structure of low DPI image info
        low_img = result["low_dpi_images"][0]
        assert "page" in low_img
        assert "index" in low_img
        assert "width_px" in low_img
        assert "height_px" in low_img
        assert "min_dpi" in low_img
        assert low_img["min_dpi"] < 300


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="PyMuPDF or PIL not available")
def test_check_pdf_image_dpi_with_high_dpi_images():
    """Test that high DPI images are not flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a high-res image
        img = Image.new("RGB", (3000, 2000), color="blue")
        img_path = os.path.join(tmpdir, "highres.png")
        img.save(img_path, dpi=(600, 600))

        # Create HTML with CSS constraints
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<img src="file://{img_path}" alt="test">
</body>
</html>""")

        # Generate PDF with DPI limit
        pdf_path = os.path.join(tmpdir, "test.pdf")
        from weasyprint import HTML

        HTML(html_path).write_pdf(pdf_path, dpi=300)

        # Check DPI
        result = check_pdf_image_dpi(pdf_path, threshold=300)

        assert result is not None
        assert result["total_images"] >= 1
        # All images should meet the threshold
        assert len(result["low_dpi_images"]) == 0


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="PyMuPDF or PIL not available")
def test_check_pdf_image_dpi_no_images():
    """Test PDF with no images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create HTML without images
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body><p>No images here</p></body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        from weasyprint import HTML

        HTML(html_path).write_pdf(pdf_path)

        # Check DPI
        result = check_pdf_image_dpi(pdf_path, threshold=300)

        assert result is not None
        assert result["total_images"] == 0
        assert len(result["low_dpi_images"]) == 0


def test_check_pdf_image_dpi_invalid_pdf():
    """Test behavior with invalid PDF file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an invalid PDF (just text file)
        invalid_pdf = os.path.join(tmpdir, "invalid.pdf")
        with open(invalid_pdf, "w") as f:
            f.write("This is not a PDF")

        # Should raise an exception when PDF cannot be opened
        with pytest.raises(Exception):
            check_pdf_image_dpi(invalid_pdf)


def test_check_pdf_image_dpi_nonexistent_file():
    """Test behavior with nonexistent file."""
    # Should raise an exception when file doesn't exist
    with pytest.raises(Exception):
        check_pdf_image_dpi("/nonexistent/file.pdf")


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="PyMuPDF or PIL not available")
def test_validate_and_warn_pdf_images_with_warnings(caplog):
    """Test that warnings are logged for low DPI images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small low-res image
        img = Image.new("RGB", (100, 100), color="yellow")
        img_path = os.path.join(tmpdir, "lowres.png")
        img.save(img_path)

        # Create HTML with image
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
<img src="file://{img_path}" alt="test">
</body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        from weasyprint import HTML

        HTML(html_path).write_pdf(pdf_path)

        # Validate
        validate_and_warn_pdf_images(pdf_path, threshold=300)

        # Should have warnings
        assert "below 300 DPI" in caplog.text
        assert "Page" in caplog.text
        assert "Image #" in caplog.text


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="PyMuPDF or PIL not available")
def test_validate_and_warn_pdf_images_no_warnings(caplog):
    """Test that no warnings are logged when all images meet threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a high-res image
        img = Image.new("RGB", (3000, 2000), color="green")
        img_path = os.path.join(tmpdir, "highres.png")
        img.save(img_path, dpi=(600, 600))

        # Create HTML with CSS constraints
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<img src="file://{img_path}" alt="test">
</body>
</html>""")

        # Generate PDF with DPI limit
        pdf_path = os.path.join(tmpdir, "test.pdf")
        from weasyprint import HTML

        HTML(html_path).write_pdf(pdf_path, dpi=300)

        # Clear caplog before validation
        caplog.clear()

        # Validate
        validate_and_warn_pdf_images(pdf_path, threshold=300)

        # Should have debug message but no warnings
        assert "below 300 DPI" not in caplog.text
        # Check for debug message (if logging level allows)
        if any(record.levelname == "DEBUG" for record in caplog.records):
            assert "meet 300 DPI threshold" in caplog.text
