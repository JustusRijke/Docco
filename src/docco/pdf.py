"""Convert HTML to PDF using WeasyPrint with CSS styling."""

import os
import shutil
import subprocess
import logging
from docco.core import html_temp_file

logger = logging.getLogger(__name__)

# Check if WeasyPrint Python library is available
try:
    from weasyprint import HTML

    USE_EXECUTABLE = False
except ImportError:  # pragma: no cover
    USE_EXECUTABLE = True


def collect_css_content(markdown_file, metadata):
    """
    Collect CSS content from frontmatter.

    Separates file-based CSS from external CSS URLs. File paths are resolved
    relative to the markdown file directory. External URLs (http:// or https://)
    are passed separately to WeasyPrint.

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
    frontmatter_css = metadata.get("css", [])

    # Handle both string and list format
    if isinstance(frontmatter_css, str):
        frontmatter_css = [frontmatter_css]

    # Separate URLs from file paths
    for css_path in frontmatter_css:
        if css_path.startswith("http://") or css_path.startswith("https://"):
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


def html_to_pdf(html_content, output_path, base_url=None, dpi=None):
    """
    Convert HTML to PDF.

    CSS should be embedded in the HTML via <style> tags.

    Args:
        html_content: HTML content string
        output_path: Path for output PDF file
        base_url: Base URL for resolving relative paths in HTML (optional)
        dpi: Maximum image resolution in DPI (optional, default: no limit)

    Returns:
        str: Path to generated PDF file
    """
    if USE_EXECUTABLE:  # pragma: no cover
        logger.info("Using weasyprint executable for PDF generation")
        _html_to_pdf_with_executable(html_content, output_path, base_url, dpi)
    else:
        logger.info("Using WeasyPrint Python module for PDF generation")
        html_obj = HTML(string=html_content, base_url=base_url, encoding="utf-8")
        if dpi:
            logger.debug(f"Setting maximum image DPI to {dpi}")
            html_obj.write_pdf(output_path, dpi=dpi)
        else:
            html_obj.write_pdf(output_path)

    logger.info(f"Generated PDF: {output_path}")
    return output_path


def _html_to_pdf_with_executable(
    html_content, output_path, base_url=None, dpi=None
):  # pragma: no cover
    """
    Convert HTML to PDF using weasyprint executable (fallback for Windows).

    Args:
        html_content: HTML content string
        output_path: Path for output PDF file
        base_url: Base URL for resolving relative paths (optional)
        dpi: Maximum image resolution in DPI (optional)

    Raises:
        RuntimeError: If weasyprint executable not found in PATH
        subprocess.CalledProcessError: If rendering fails
    """
    # Check if weasyprint executable is available
    weasyprint_cmd = shutil.which("weasyprint")
    if not weasyprint_cmd:
        raise RuntimeError(
            "WeasyPrint Python library not available and 'weasyprint' executable not found in PATH. "
            "Install WeasyPrint: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
        )

    # Create temp file for HTML
    with html_temp_file(html_content) as html_tmp_path:
        # Build command
        cmd = [weasyprint_cmd]

        # Add base URL if provided
        if base_url:
            cmd.extend(["-u", base_url])

        # Add DPI if provided
        if dpi:
            cmd.extend(["--dpi", str(dpi)])
            logger.debug(f"Setting maximum image DPI to {dpi} (executable mode)")

        cmd.extend([html_tmp_path, str(output_path)])

        # Call weasyprint executable
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stderr:
            logger.error(result.stderr)
