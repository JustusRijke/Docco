"""
Unit tests for image processing functionality.
"""

from pathlib import Path
import pytest
from docco.content.images import ImageProcessor, parse_image_directive


class TestParseImageDirective:
    """Tests for image directive parsing."""

    def test_parse_inline_style(self):
        """Test parsing image directive with inline style."""
        directive = 'img "path/to/image.png" "width:50%; margin:10px;"'
        result = parse_image_directive(directive)

        assert result is not None
        assert result['path'] == 'path/to/image.png'
        assert result['style'] == 'width:50%; margin:10px;'
        assert result['css_class'] is None

    def test_parse_css_class(self):
        """Test parsing image directive with CSS class."""
        directive = 'img "images/diagram.svg" "class:diagram"'
        result = parse_image_directive(directive)

        assert result is not None
        assert result['path'] == 'images/diagram.svg'
        assert result['style'] is None
        assert result['css_class'] == 'diagram'

    def test_parse_class_with_spaces(self):
        """Test parsing class directive with extra spaces."""
        directive = 'img "test.png" "class:  my-class  "'
        result = parse_image_directive(directive)

        assert result is not None
        assert result['css_class'] == 'my-class'

    def test_parse_invalid_directive(self):
        """Test that invalid directive returns None."""
        assert parse_image_directive('not an image directive') is None
        assert parse_image_directive('img missing quotes') is None
        assert parse_image_directive('') is None

    def test_parse_case_insensitive(self):
        """Test that directive parsing is case-insensitive."""
        directive = 'IMG "test.png" "width:100px"'
        result = parse_image_directive(directive)

        assert result is not None
        assert result['path'] == 'test.png'


class TestImageProcessor:
    """Tests for ImageProcessor class."""

    def test_init(self, tmp_path):
        """Test ImageProcessor initialization."""
        md_file = tmp_path / "document.md"
        md_file.touch()

        processor = ImageProcessor(md_file)
        assert processor.base_dir == tmp_path

    def test_process_image_not_found(self, tmp_path):
        """Test processing non-existent image raises FileNotFoundError."""
        md_file = tmp_path / "document.md"
        md_file.touch()

        processor = ImageProcessor(md_file)

        with pytest.raises(FileNotFoundError) as exc_info:
            processor.process_image("nonexistent.png")

        assert "Image not found" in str(exc_info.value)

    def test_process_image_unsupported_format(self, tmp_path):
        """Test processing unsupported image format raises ValueError."""
        md_file = tmp_path / "document.md"
        md_file.touch()

        # Create a file with unsupported extension
        unsupported_file = tmp_path / "image.bmp"
        unsupported_file.touch()

        processor = ImageProcessor(md_file)

        with pytest.raises(ValueError) as exc_info:
            processor.process_image("image.bmp")

        assert "Unsupported image format" in str(exc_info.value)

    def test_process_svg_image(self, tmp_path):
        """Test processing SVG image."""
        md_file = tmp_path / "document.md"
        md_file.touch()

        # Create a simple SVG file
        svg_file = tmp_path / "test.svg"
        svg_file.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')

        processor = ImageProcessor(md_file)
        result = processor.process_image("test.svg", resize=False)

        assert result['format'] == 'SVG'
        assert result['resolved_path'] == svg_file.resolve()
        assert result['file_url'].startswith('file://')
        assert result['width'] is None  # SVG doesn't have raster dimensions
        assert result['height'] is None

    def test_process_png_image(self, tmp_path):
        """Test processing PNG image with Pillow."""
        pytest.importorskip("PIL")  # Skip if Pillow not installed

        from PIL import Image

        md_file = tmp_path / "document.md"
        md_file.touch()

        # Create a small PNG image
        png_file = tmp_path / "test.png"
        img = Image.new('RGB', (100, 50), color='red')
        img.save(png_file, format='PNG')

        processor = ImageProcessor(md_file)
        result = processor.process_image("test.png", resize=False)

        assert result['format'] == 'PNG'
        assert result['resolved_path'] == png_file.resolve()
        assert result['width'] == 100
        assert result['height'] == 50

    def test_process_jpeg_image(self, tmp_path):
        """Test processing JPEG image."""
        pytest.importorskip("PIL")

        from PIL import Image

        md_file = tmp_path / "document.md"
        md_file.touch()

        # Create a small JPEG image
        jpg_file = tmp_path / "test.jpg"
        img = Image.new('RGB', (200, 150), color='blue')
        img.save(jpg_file, format='JPEG')

        processor = ImageProcessor(md_file)
        result = processor.process_image("test.jpg", resize=False)

        assert result['format'] == 'JPEG'
        assert result['width'] == 200
        assert result['height'] == 150

    def test_process_image_with_subdirectory(self, tmp_path):
        """Test processing image in subdirectory."""
        md_file = tmp_path / "document.md"
        md_file.touch()

        # Create images subdirectory
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        svg_file = images_dir / "icon.svg"
        svg_file.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')

        processor = ImageProcessor(md_file)
        result = processor.process_image("images/icon.svg", resize=False)

        assert result['format'] == 'SVG'
        assert result['resolved_path'] == svg_file.resolve()

    def test_supported_formats(self):
        """Test that all expected formats are supported."""
        expected_formats = {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.avif'}
        assert ImageProcessor.SUPPORTED_FORMATS == expected_formats

    def test_file_url_format(self, tmp_path):
        """Test that file URL is correctly formatted."""
        md_file = tmp_path / "document.md"
        md_file.touch()

        svg_file = tmp_path / "test.svg"
        svg_file.write_text('<svg></svg>')

        processor = ImageProcessor(md_file)
        result = processor.process_image("test.svg", resize=False)

        # file:// URL should contain the absolute path
        assert result['file_url'].startswith('file://')
        assert str(svg_file.resolve()) in result['file_url']
