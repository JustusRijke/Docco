"""Tests for PDF validation module."""

import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

# Import the modules to test
from docco.pdf import html_to_pdf
from docco.pdf_validation import check_pdf_image_dpi, validate_and_warn_pdf_images


def path_to_file_url(file_path):
    """Convert file path to proper file:// URL (cross-platform)."""
    return Path(file_path).as_uri()


def test_check_pdf_image_dpi_with_low_dpi_images():
    """Test detection of low DPI images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small low-res image
        img = Image.new("RGB", (100, 100), color="red")
        img_path = os.path.join(tmpdir, "lowres.png")
        img.save(img_path)

        # Create HTML with image
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
<img src="{path_to_file_url(img_path)}" alt="test">
</body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        html_to_pdf(html_path, pdf_path)

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


def test_check_pdf_image_dpi_with_high_dpi_images():
    """Test that high DPI images are not flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a high-res image
        img = Image.new("RGB", (3000, 2000), color="blue")
        img_path = os.path.join(tmpdir, "highres.png")
        img.save(img_path, dpi=(600, 600))

        # Create HTML with CSS constraints
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<img src="{path_to_file_url(img_path)}" alt="test">
</body>
</html>""")

        # Generate PDF with DPI limit
        pdf_path = os.path.join(tmpdir, "test.pdf")
        html_to_pdf(html_path, pdf_path, dpi=300)

        # Check DPI
        result = check_pdf_image_dpi(pdf_path, threshold=300)

        assert result is not None
        assert result["total_images"] >= 1
        # All images should meet the threshold
        assert len(result["low_dpi_images"]) == 0


def test_check_pdf_image_dpi_no_images():
    """Test PDF with no images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create HTML without images
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body><p>No images here</p></body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        html_to_pdf(html_path, pdf_path)

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
        with open(invalid_pdf, "w", encoding="utf-8") as f:
            f.write("This is not a PDF")

        # Should raise an exception when PDF cannot be opened
        with pytest.raises(RuntimeError):
            check_pdf_image_dpi(invalid_pdf)


def test_check_pdf_image_dpi_nonexistent_file():
    """Test behavior with nonexistent file."""
    # Should raise an exception when file doesn't exist
    with pytest.raises(RuntimeError):
        check_pdf_image_dpi("/nonexistent/file.pdf")


def test_validate_and_warn_pdf_images_with_warnings(caplog):
    """Test that warnings are logged for low DPI images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small low-res image
        img = Image.new("RGB", (100, 100), color="yellow")
        img_path = os.path.join(tmpdir, "lowres.png")
        img.save(img_path)

        # Create HTML with image
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body>
<img src="{path_to_file_url(img_path)}" alt="test">
</body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        html_to_pdf(html_path, pdf_path)

        # Validate
        validate_and_warn_pdf_images(pdf_path, threshold=300)

        # Should have warnings
        assert "below 300 DPI" in caplog.text
        assert "Page" in caplog.text
        assert "Image #" in caplog.text


def test_check_pdf_image_dpi_at_threshold():
    """Test that images exactly at threshold DPI are not flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a 39x39 image (will be rendered at 39x39 in PDF)
        img = Image.new("RGB", (39, 39), color="red")
        img_path = os.path.join(tmpdir, "test.png")
        img.save(img_path)

        # Create HTML with image sized to exactly 0.52 inches (39 pixels / 75 DPI)
        # This should result in exactly 75 DPI
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{ width: 0.52in; height: 0.52in; }}
</style>
</head>
<body>
<img src="{path_to_file_url(img_path)}" alt="test">
</body>
</html>""")

        # Generate PDF
        pdf_path = os.path.join(tmpdir, "test.pdf")
        html_to_pdf(html_path, pdf_path)

        # Check DPI - threshold is 75, image should be at 75 DPI
        result = check_pdf_image_dpi(pdf_path, threshold=75)

        assert result is not None
        assert result["total_images"] >= 1
        # Image at exactly threshold should NOT be flagged
        assert len(result["low_dpi_images"]) == 0, (
            f"Image at exactly {75} DPI should not be flagged. Got: {result['low_dpi_images']}"
        )


def test_validate_and_warn_pdf_images_no_warnings(caplog):
    """Test that no warnings are logged when all images meet threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a high-res image
        img = Image.new("RGB", (3000, 2000), color="green")
        img_path = os.path.join(tmpdir, "highres.png")
        img.save(img_path, dpi=(600, 600))

        # Create HTML with CSS constraints
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<img src="{path_to_file_url(img_path)}" alt="test">
</body>
</html>""")

        # Generate PDF with DPI limit
        pdf_path = os.path.join(tmpdir, "test.pdf")
        html_to_pdf(html_path, pdf_path, dpi=300)

        # Clear caplog before validation
        caplog.clear()

        # Validate
        validate_and_warn_pdf_images(pdf_path, threshold=300)

        # Should have no warnings about low DPI
        assert "below 300 DPI" not in caplog.text
