"""PDF validation utilities for checking image quality."""

import logging

logger = logging.getLogger(__name__)


def check_pdf_image_dpi(pdf_path, threshold=300):
    """
    Check all images in a PDF for DPI below threshold.

    Args:
        pdf_path: Path to PDF file
        threshold: Minimum acceptable DPI (default: 300)

    Returns:
        dict with keys:
            - total_images: int
            - low_dpi_images: list of dicts with image details
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:  # pragma: no cover
        logger.debug("PyMuPDF not available, skipping DPI validation")
        return None

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        logger.warning(f"Could not open PDF for validation: {e}")
        return None

    low_dpi_images = []
    total_images = 0

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            img_list = page.get_image_info()

            for img_idx, img_info in enumerate(img_list):
                total_images += 1

                # Get image dimensions
                width_px = img_info["width"]
                height_px = img_info["height"]

                # Get display size on page
                bbox = img_info["bbox"]
                width_points = bbox[2] - bbox[0]
                height_points = bbox[3] - bbox[1]

                # Calculate size in inches (72 points = 1 inch)
                width_inches = width_points / 72
                height_inches = height_points / 72

                # Calculate effective DPI
                effective_dpi_x = width_px / width_inches if width_inches > 0 else 0
                effective_dpi_y = height_px / height_inches if height_inches > 0 else 0
                min_dpi = min(effective_dpi_x, effective_dpi_y)

                if min_dpi < threshold:
                    low_dpi_images.append(
                        {
                            "page": page_num + 1,
                            "index": img_idx + 1,
                            "width_px": width_px,
                            "height_px": height_px,
                            "width_inches": width_inches,
                            "height_inches": height_inches,
                            "dpi_x": effective_dpi_x,
                            "dpi_y": effective_dpi_y,
                            "min_dpi": min_dpi,
                        }
                    )
    finally:
        doc.close()

    return {
        "total_images": total_images,
        "low_dpi_images": low_dpi_images,
    }


def validate_and_warn_pdf_images(pdf_path, threshold=300):
    """
    Validate PDF images and log warnings for low DPI images.

    Args:
        pdf_path: Path to PDF file
        threshold: Minimum acceptable DPI (default: 300)
    """
    result = check_pdf_image_dpi(pdf_path, threshold)

    if result["low_dpi_images"]:
        logger.warning(
            f"PDF contains {len(result['low_dpi_images'])} image(s) below {threshold} DPI"
        )
        for img in result["low_dpi_images"]:
            logger.warning(
                f"  Page {img['page']}, Image #{img['index']}: "
                f"{img['width_px']}x{img['height_px']} @ {img['min_dpi']:.0f} DPI "
                f'(displayed at {img["width_inches"]:.2f}" x {img["height_inches"]:.2f}")'
            )
    else:
        logger.debug(
            f"All {result['total_images']} image(s) meet {threshold} DPI threshold"
        )
