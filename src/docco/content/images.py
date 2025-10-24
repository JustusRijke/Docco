"""
Image processing and validation utilities.
"""

from pathlib import Path
import re
from typing import Optional, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from PIL import Image as PILImage


class ImageProcessor:
    """
    Handles image validation, optimization, and path resolution for PDF rendering.

    Supports formats: PNG, JPEG, SVG, GIF, WebP, AVIF
    """

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.avif'}
    SIZE_WARNING_THRESHOLD = 1 * 1024 * 1024  # 1MB
    SIZE_RESIZE_THRESHOLD = 2 * 1024 * 1024   # 2MB

    def __init__(self, markdown_file_path: Path):
        """
        Initialize image processor with base path for resolving relative image paths.

        Args:
            markdown_file_path: Path to the markdown file (used to resolve relative image paths)
        """
        self.base_dir = markdown_file_path.parent

    def process_image(self, image_path: str, resize: bool = True) -> dict:
        """
        Process an image: validate, check size, optionally resize.

        Args:
            image_path: Relative path to image (from markdown file location)
            resize: Whether to auto-resize oversized images

        Returns:
            Dict with keys:
                - resolved_path: Absolute Path object to the image
                - file_url: file:// URL for WeasyPrint
                - width: Image width in pixels (None for SVG)
                - height: Image height in pixels (None for SVG)
                - format: Image format (e.g., 'PNG', 'JPEG', 'SVG')

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image format is not supported
        """
        # Resolve path relative to markdown file
        resolved_path = (self.base_dir / image_path).resolve()

        # Check if file exists
        if not resolved_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path} (resolved to {resolved_path})")

        # Check format
        suffix = resolved_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Check file size
        file_size = resolved_path.stat().st_size
        if file_size > self.SIZE_WARNING_THRESHOLD:
            warnings.warn(
                f"Large image file: {image_path} ({file_size / 1024 / 1024:.2f}MB). "
                "This may increase PDF file size."
            )

        # Get image info
        format_name = suffix[1:].upper()  # Remove dot and uppercase
        if format_name == 'JPG':
            format_name = 'JPEG'

        width, height = None, None

        # For raster formats, get dimensions and optionally resize
        if suffix in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif'}:
            try:
                from PIL import Image

                with Image.open(resolved_path) as img:
                    width, height = img.size

                    # Auto-resize if too large
                    if resize and file_size > self.SIZE_RESIZE_THRESHOLD:
                        resized_path = self._resize_image(resolved_path, img)
                        if resized_path:
                            resolved_path = resized_path
                            # Reopen to get new dimensions
                            with Image.open(resolved_path) as resized_img:
                                width, height = resized_img.size
            except ImportError:
                warnings.warn(
                    "Pillow not installed. Skipping image dimension detection and resizing. "
                    "Install with: pip install Pillow"
                )

        # Build file:// URL for WeasyPrint
        file_url = resolved_path.as_uri()

        return {
            'resolved_path': resolved_path,
            'file_url': file_url,
            'width': width,
            'height': height,
            'format': format_name
        }

    def _resize_image(self, image_path: Path, img: 'PILImage.Image') -> Optional[Path]:
        """
        Resize an oversized image to reduce file size.

        Creates a resized copy in a .docco_cache folder next to the original.

        Args:
            image_path: Path to original image
            img: PIL Image object (already opened)

        Returns:
            Path to resized image, or None if resize failed
        """
        try:
            from PIL import Image

            # Create cache directory
            cache_dir = image_path.parent / '.docco_cache'
            cache_dir.mkdir(exist_ok=True)

            # Determine resize factor (target max 1920px width)
            max_dimension = 1920
            width, height = img.size

            if width > max_dimension or height > max_dimension:
                scale = max_dimension / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)

                # Resize with high-quality resampling
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Save resized image
                resized_path = cache_dir / f"resized_{image_path.name}"

                # Preserve format and transparency
                if img.mode in ('RGBA', 'LA', 'P'):
                    resized.save(resized_path, format=img.format, optimize=True)
                else:
                    resized.save(resized_path, format=img.format, optimize=True, quality=85)

                warnings.warn(
                    f"Resized {image_path.name} from {width}x{height} to {new_width}x{new_height} "
                    f"to reduce file size. Cached at {resized_path}"
                )

                return resized_path
        except Exception as e:
            warnings.warn(f"Failed to resize image {image_path}: {e}")

        return None


def parse_image_directive(directive_content: str) -> Optional[dict]:
    """
    Parse an image directive from HTML comment.

    Expected format:
        img "path/to/image.png" "style"
        img "path/to/image.png" "class:diagram"

    Args:
        directive_content: Content inside <!-- ... --> comment

    Returns:
        Dict with keys:
            - path: Image path (str)
            - style: CSS style string (str) or None
            - css_class: CSS class name (str) or None
        Returns None if not a valid image directive
    """
    # Match: img "path" "style/class"
    pattern = re.compile(r'img\s+"([^"]+)"\s+"([^"]+)"', re.IGNORECASE)
    match = pattern.match(directive_content.strip())

    if not match:
        return None

    path = match.group(1)
    style_or_class = match.group(2)

    # Check if it's a class directive (starts with "class:")
    if style_or_class.startswith('class:'):
        css_class = style_or_class[6:].strip()  # Remove "class:" prefix
        return {
            'path': path,
            'style': None,
            'css_class': css_class
        }
    else:
        # Treat as inline CSS
        return {
            'path': path,
            'style': style_or_class,
            'css_class': None
        }
