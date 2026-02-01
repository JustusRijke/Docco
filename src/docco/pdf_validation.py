"""PDF validation utilities for checking image quality."""

import logging
from pathlib import Path
from typing import TypedDict, cast

logger = logging.getLogger(__name__)


class ImageInfo(TypedDict):
    """Information about an image in the PDF."""

    page: int
    index: int
    width_px: int
    height_px: int
    width_inches: float
    height_inches: float
    dpi_x: float
    dpi_y: float
    min_dpi: float


class DPICheckResult(TypedDict):
    """Result of PDF image DPI check."""

    total_images: int
    low_dpi_images: list[ImageInfo]


def check_pdf_image_dpi(pdf_path: Path, threshold: int = 300) -> DPICheckResult:
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
    import fitz  # PyMuPDF

    doc = fitz.open(str(pdf_path))

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

                if min_dpi < (
                    threshold * 0.95
                ):  # 5% tolerance to compensate for rounding errors
                    low_dpi_images.append(
                        cast(
                            ImageInfo,
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
                            },
                        )
                    )
    finally:
        doc.close()

    return {
        "total_images": total_images,
        "low_dpi_images": low_dpi_images,
    }


def validate_and_warn_pdf_images(pdf_path: Path, threshold: int = 300) -> None:
    """
    Validate PDF images and log warnings for low DPI images.

    Args:
        pdf_path: Path to PDF file
        threshold: Minimum acceptable DPI (default: 300)
    """
    result = check_pdf_image_dpi(pdf_path, threshold)

    if result["low_dpi_images"]:
        logger.warning(
            f"PDF contains {len(result['low_dpi_images'])} image(s) below {threshold} DPI (expected)"
        )
        for img in result["low_dpi_images"]:
            # Calculate expected resolution in pixels
            expected_width_px = int(img["width_inches"] * threshold)
            expected_height_px = int(img["height_inches"] * threshold)
            logger.warning(
                f"  Page {img['page']}, Image #{img['index']}: "
                f"{img['width_px']}x{img['height_px']} @ {img['min_dpi']:.0f} DPI (actual), "
                f"expected {expected_width_px}x{expected_height_px} @ {threshold} DPI"
            )
    else:
        logger.debug(
            f"All {result['total_images']} image(s) meet {threshold} DPI threshold"
        )
