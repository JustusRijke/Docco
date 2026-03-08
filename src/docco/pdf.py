"""Convert HTML to PDF using Playwright/Chromium with CSS styling."""

import logging
from pathlib import Path
from typing import TypedDict

from playwright.sync_api import ConsoleMessage, sync_playwright

from docco.core import absolutize_css_urls

logger = logging.getLogger(__name__)

# Signal set by paged.js template when rendering is complete
PAGED_RENDERING_COMPLETE_FLAG = "pagedJsRenderingComplete"


class CSSContent(TypedDict):
    """CSS content from frontmatter."""

    inline: str
    external: list[str]


class JSContent(TypedDict):
    """JS content from frontmatter."""

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
    md_dir = Path(markdown_file).resolve().parent

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
            abs_path = md_dir / css_path
            if abs_path.exists():
                with abs_path.open("r", encoding="utf-8") as f:
                    raw_css = f.read()
                css_content.append(absolutize_css_urls(raw_css, abs_path))
                logger.debug(f"Using CSS from frontmatter: {css_path}")
            else:
                logger.error(f"CSS file not found: {abs_path}")

    return {"inline": "\n".join(css_content), "external": external_urls}


def collect_js_content(markdown_file: Path, metadata: dict[str, object]) -> JSContent:
    """
    Collect JS content from frontmatter.

    Separates file-based JS (embedded as inline script) from external JS URLs
    (added as <script src="..."> tags). File paths are resolved relative to the
    markdown file directory.

    Args:
        markdown_file: Path to markdown file
        metadata: Parsed frontmatter metadata dict

    Returns:
        dict: {
            "inline": str (concatenated JS content from files),
            "external": list (JS URLs)
        }
    """
    js_content = []
    external_urls = []
    md_dir = Path(markdown_file).resolve().parent

    frontmatter_js_raw = metadata.get("js", [])

    if isinstance(frontmatter_js_raw, str):
        frontmatter_js: list[str] = [frontmatter_js_raw]
    elif isinstance(frontmatter_js_raw, list):
        frontmatter_js = [str(item) for item in frontmatter_js_raw]
    else:
        frontmatter_js = []

    for js_path in frontmatter_js:
        if js_path.startswith("http://") or js_path.startswith("https://"):
            external_urls.append(js_path)
            logger.debug(f"Using external JS: {js_path}")
        else:
            abs_path = md_dir / js_path
            if abs_path.exists():
                with abs_path.open("r", encoding="utf-8") as f:
                    js_content.append(f.read())
                logger.debug(f"Using JS from frontmatter: {js_path}")
            else:
                logger.error(f"JS file not found: {abs_path}")

    return {"inline": "\n".join(js_content), "external": external_urls}


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
    if not gs_cmd:  # pragma: no cover
        logger.warning("Ghostscript not found, skipping image downscaling")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)

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
                pdf_path,
            ],
            check=True,
            capture_output=True,
        )
        shutil.move(tmp_path, pdf_path)
        logger.info(f"Downscaled images in PDF to {target_dpi} DPI")
    except subprocess.CalledProcessError as e:  # pragma: no cover
        logger.error(f"Ghostscript failed: {e.stderr.decode()}")
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    except Exception:  # pragma: no cover
        if tmp_path.exists():
            tmp_path.unlink()
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
        def handle_console(msg: ConsoleMessage) -> None:  # pragma: no cover
            msg_type = msg.type
            msg_text = f"Chromium: {msg.text}"
            if msg_type == "info":
                logger.info(msg_text)
            elif msg_type == "warning":
                logger.warning(msg_text)
            elif msg_type == "error":
                logger.error(msg_text)
            else:
                logger.debug(f"Chromium {msg_type}: {msg_text}")

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
            path=output_path,
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=False,
        )

        browser.close()

    logger.info(f"Generated PDF: {output_path}")

    if dpi:
        _downscale_pdf_images(output_path, dpi)

    return output_path
