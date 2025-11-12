"""Convert HTML to PDF using WeasyPrint with CSS styling."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from docco.core import setup_logger

logger = setup_logger(__name__)

# Check if WeasyPrint Python library is available
try:
    from weasyprint import HTML

    USE_EXECUTABLE = False
except ImportError:  # pragma: no cover
    USE_EXECUTABLE = True


def collect_css_content(markdown_file, metadata):
    """
    Collect CSS content from frontmatter.

    CSS files from frontmatter are resolved relative to the markdown file directory.

    Args:
        markdown_file: Path to markdown file
        metadata: Parsed frontmatter metadata dict

    Returns:
        str: Concatenated CSS content (may be empty string)
    """
    css_content = []
    md_dir = os.path.dirname(os.path.abspath(markdown_file))

    # Extract CSS from frontmatter
    frontmatter_css = metadata.get("css", [])

    # Handle both string and list format
    if isinstance(frontmatter_css, str):
        frontmatter_css = [frontmatter_css]

    # Read CSS file contents
    for css_path in frontmatter_css:
        abs_path = os.path.join(md_dir, css_path)
        if os.path.exists(abs_path):
            with open(abs_path, "r", encoding="utf-8") as f:
                css_content.append(f.read())
            logger.info(f"Using CSS from frontmatter: {css_path}")
        else:
            logger.warning(f"CSS file not found: {abs_path}")

    return "\n".join(css_content)


def html_to_pdf(html_content, output_path, base_url=None):
    """
    Convert HTML to PDF.

    CSS should be embedded in the HTML via <style> tags.

    Args:
        html_content: HTML content string
        output_path: Path for output PDF file
        base_url: Base URL for resolving relative paths in HTML (optional)

    Returns:
        str: Path to generated PDF file
    """
    if USE_EXECUTABLE:  # pragma: no cover
        logger.info("Using weasyprint executable for PDF generation")
        _html_to_pdf_with_executable(html_content, output_path, base_url)
    else:
        logger.info("Using WeasyPrint Python module for PDF generation")
        html_obj = HTML(string=html_content, base_url=base_url)
        html_obj.write_pdf(output_path)

    logger.info(f"Generated PDF: {output_path}")
    return output_path


def _html_to_pdf_with_executable(
    html_content, output_path, base_url=None
):  # pragma: no cover
    """
    Convert HTML to PDF using weasyprint executable (fallback for Windows).

    Args:
        html_content: HTML content string
        output_path: Path for output PDF file
        base_url: Base URL for resolving relative paths (optional)

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
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as html_tmp:
        html_tmp.write(html_content)
        html_tmp_path = html_tmp.name

    try:
        # Build command
        cmd = [weasyprint_cmd]

        # Add base URL if provided
        if base_url:
            cmd.extend(["-u", base_url])

        cmd.extend([html_tmp_path, str(output_path)])

        # Call weasyprint executable
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    finally:
        # Clean up temp file
        Path(html_tmp_path).unlink(missing_ok=True)
