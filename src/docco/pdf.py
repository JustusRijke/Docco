"""Convert HTML to PDF using Playwright/Chromium with CSS styling."""

import logging
import os
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class CSSContent(TypedDict):
    """CSS content from frontmatter."""

    inline: str
    external: list[str]


def _check_file_writable(file_path: str | Path) -> None:  # pragma: no cover
    """
    Check if output file can be written (not open in another process).
    Works on Windows and Linux.

    Raises:
        RuntimeError: If file is locked or inaccessible
    """
    try:
        with open(file_path, "w"):
            pass
    except (PermissionError, OSError):
        raise RuntimeError(
            f"Cannot write to PDF file: {file_path}\n"
            "The file may be open in another application. "
            "Please close it and try again."
        )
    except Exception as e:
        raise RuntimeError(f"Error accessing PDF file {file_path}: {e}")


def collect_css_content(
    markdown_file: str | Path, metadata: dict[str, object]
) -> CSSContent:
    """
    Collect CSS content from frontmatter.

    Separates file-based CSS from external CSS URLs. File paths are resolved
    relative to the markdown file directory. External URLs (http:// or https://)
    are kept separate for HTML link tags.

    Args:
        markdown_file: Path to markdown file
        metadata: Parsed frontmatter metadata dict

    Returns:
        dict: {
            "inline": str (concatenated CSS content from files),
            "external": list (CSS URLs like https://fonts.googleapis.com/...)
        }
    """
    css_content = []
    external_urls = []
    md_dir = os.path.dirname(os.path.abspath(markdown_file))

    # Extract CSS from frontmatter
    frontmatter_css_raw = metadata.get("css", [])

    # Handle both string and list format
    if isinstance(frontmatter_css_raw, str):
        frontmatter_css: list[str] = [frontmatter_css_raw]
    elif isinstance(frontmatter_css_raw, list):
        frontmatter_css = [str(item) for item in frontmatter_css_raw]
    else:
        frontmatter_css = []

    # Separate URLs from file paths
    for css_path in frontmatter_css:
        if css_path.startswith("http://") or css_path.startswith(
            "https://"
        ):  # pragma: no cover
            external_urls.append(css_path)
            logger.debug(f"Using external CSS: {css_path}")
        else:
            abs_path = os.path.join(md_dir, css_path)
            if os.path.exists(abs_path):
                with open(abs_path, "r", encoding="utf-8") as f:
                    css_content.append(f.read())
                logger.debug(f"Using CSS from frontmatter: {css_path}")
            else:
                logger.warning(f"CSS file not found: {abs_path}")

    return {"inline": "\n".join(css_content), "external": external_urls}


def html_to_pdf(
    html_path: str | Path,
    output_path: str | Path,
    dpi: int | None = None,
) -> str:
    """
    Convert HTML file to PDF.

    CSS should be embedded in the HTML via <style> tags. Use <base> tag in HTML
    for resolving relative paths.

    Args:
        html_path: Path to HTML file to convert
        output_path: Path for output PDF file
        dpi: Maximum image resolution in DPI (ignored, Chromium uses 96 DPI)

    Returns:
        str: Path to generated PDF file
    """
    _check_file_writable(output_path)

    logger.info("Using Playwright/Chromium for PDF generation")

    # Convert to absolute path for file:// URL
    abs_html_path = os.path.abspath(html_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load HTML file and wait for network idle (important for Paged.js)
        page.goto(f"file://{abs_html_path}", wait_until="networkidle")

        # Generate PDF
        page.pdf(
            path=str(output_path),
            print_background=True,  # Essential for CSS backgrounds/colors
            prefer_css_page_size=True,  # Use @page size from CSS
            display_header_footer=False,  # Headers/footers handled by HTML/CSS
        )

        browser.close()

    logger.info(f"Generated PDF: {output_path}")
    return str(output_path)
