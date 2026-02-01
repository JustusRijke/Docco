"""Convert HTML to PDF using Playwright/Chromium with CSS styling."""

import logging
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# Signal set by paged.js template when rendering is complete
PAGED_RENDERING_COMPLETE_FLAG = "pagedJsRenderingComplete"


class CSSContent(TypedDict):
    """CSS content from frontmatter."""

    inline: str
    external: list[str]


def _check_file_writable(file_path: Path) -> None:  # pragma: no cover
    """
    Check if output file can be written (not open in another process).
    Works on Windows and Linux.

    Raises:
        RuntimeError: If file is locked or inaccessible
    """
    try:
        with file_path.open("w", encoding="utf-8"):
            pass
    except (PermissionError, OSError):
        raise RuntimeError(
            f"Cannot write to PDF file: {file_path}\n"
            "The file may be open in another application. "
            "Please close it and try again."
        )
    except Exception as e:
        raise RuntimeError(f"Error accessing PDF file {file_path}: {e}")


def _absolutize_css_urls(css_content: str, css_file_path: str) -> str:
    """
    Convert relative URLs in CSS to absolute file:// URLs.

    Converts url() references while preserving:
    - Absolute URLs (http://, https://, file://)
    - Data URLs (data:)

    Args:
        css_content: CSS content string
        css_file_path: Path to CSS file for resolving relative paths

    Returns:
        str: CSS with absolutized URLs
    """
    import re
    from urllib.parse import urljoin

    # Ensure absolute path for cross-platform compatibility
    abs_css_path = Path(css_file_path).resolve()
    css_dir = Path(abs_css_path).parent
    base_url = Path(css_dir).as_uri()

    def replace_url(match: re.Match) -> str:
        url = match.group(1).strip("'\" ")

        # Preserve absolute URLs and data URLs
        if (
            url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("file://")
            or url.startswith("data:")
        ):
            return match.group(0)

        # Convert relative URL to absolute file:// URL
        abs_url = urljoin(base_url + "/", url)
        return f'url("{abs_url}")'

    # Match url(...) with various quote styles
    pattern = r'url\(["\']?([^)]+?)["\']?\)'
    return re.sub(pattern, replace_url, css_content)


def collect_css_content(markdown_file: Path, metadata: dict[str, object]) -> CSSContent:
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
    md_dir = Path(Path(markdown_file).resolve()).parent

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
            abs_path = Path(md_dir) / css_path
            if abs_path.exists():
                with abs_path.open("r", encoding="utf-8") as f:
                    raw_css = f.read()
                # Convert relative URLs in CSS to absolute paths
                absolutized_css = _absolutize_css_urls(raw_css, str(abs_path))
                css_content.append(absolutized_css)
                logger.debug(f"Using CSS from frontmatter: {css_path}")
            else:
                logger.warning(f"CSS file not found: {abs_path}")

    return {"inline": "\n".join(css_content), "external": external_urls}


def _downscale_pdf_images(pdf_path: Path, target_dpi: int) -> None:
    """
    Downscale images in PDF to target DPI using Ghostscript.

    Uses threshold=1.0 to downsample any image exceeding target DPI.
    Bicubic downsampling provides highest quality results.

    Args:
        pdf_path: Path to PDF file to modify in-place
        target_dpi: Target maximum DPI for images
    """
    import shutil
    import subprocess
    import tempfile

    gs_cmd = shutil.which("gswin64c") or shutil.which("gs")
    if not gs_cmd:
        logger.warning("Ghostscript not found, skipping image downscaling")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(
            [
                gs_cmd,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dColorImageResolution={target_dpi}",
                f"-dGrayImageResolution={target_dpi}",
                f"-dMonoImageResolution={target_dpi}",
                "-dColorImageDownsampleThreshold=1.0",
                "-dGrayImageDownsampleThreshold=1.0",
                "-dMonoImageDownsampleThreshold=1.0",
                "-dColorImageDownsampleType=/Bicubic",
                "-dGrayImageDownsampleType=/Bicubic",
                "-dMonoImageDownsampleType=/Subsample",
                "-dDownsampleColorImages=true",
                "-dDownsampleGrayImages=true",
                "-dDownsampleMonoImages=true",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={tmp_path}",
                str(pdf_path),
            ],
            check=True,
            capture_output=True,
        )
        Path(tmp_path).replace(str(pdf_path))
        logger.info(f"Downscaled images in PDF to {target_dpi} DPI")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ghostscript failed: {e.stderr.decode()}")
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()
        raise
    except Exception:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()
        raise


def html_to_pdf(
    html_path: Path,
    output_path: Path,
    dpi: int | None = None,
) -> Path:
    """
    Convert HTML file to PDF.

    CSS should be embedded in the HTML via <style> tags. Relative URLs in HTML
    and CSS are converted to absolute file:// paths during HTML generation.

    Args:
        html_path: Path to HTML file to convert
        output_path: Path for output PDF file
        dpi: Maximum image resolution in DPI

    Returns:
        Path: Path to generated PDF file
    """
    _check_file_writable(output_path)

    abs_html_path = html_path.resolve()

    logger.info("Using Playwright/Chromium for PDF generation")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console messages for debugging
        def handle_console(msg: object) -> None:
            msg_type = msg.type  # type: ignore[attr-defined]
            if msg_type in ("error", "warning"):
                logger.warning(f"Chromium {msg_type}: {msg.text}")  # type: ignore[attr-defined]
            elif msg_type == "log":
                logger.debug(f"Chromium log: {msg.text}")  # type: ignore[attr-defined]

        page.on("console", handle_console)

        # Capture page errors
        page.on("pageerror", lambda exc: logger.error(f"Chromium error: {exc}"))

        page.goto(f"file://{abs_html_path}", wait_until="networkidle")

        # Wait for paged.js rendering only if template is used
        with abs_html_path.open("r", encoding="utf-8") as f:
            html_content = f.read()

        if PAGED_RENDERING_COMPLETE_FLAG in html_content:
            page.wait_for_function(
                f"window.{PAGED_RENDERING_COMPLETE_FLAG} === true",
                timeout=5 * 60 * 1000,
            )  # Long timeout (5 minutes) due to slow github runner

        page.pdf(
            path=str(output_path),
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=False,
        )

        browser.close()

    logger.info(f"Generated PDF: {output_path}")

    if dpi:
        _downscale_pdf_images(output_path, dpi)

    return output_path
