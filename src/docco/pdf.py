"""Convert HTML to PDF using WeasyPrint with CSS styling."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from docco.utils import setup_logger

logger = setup_logger(__name__)

# Check if WeasyPrint Python library is available
try:
    from weasyprint import HTML, CSS

    USE_EXECUTABLE = False
except ImportError:
    USE_EXECUTABLE = True


def collect_css_files(markdown_file, metadata, cli_css_arg=None):
    """
    Collect CSS files from frontmatter and CLI argument.

    CSS files from frontmatter are resolved relative to the markdown file directory.
    CLI CSS argument is added last (highest priority for overrides).

    Args:
        markdown_file: Path to markdown file
        metadata: Parsed frontmatter metadata dict
        cli_css_arg: CSS file from CLI argument (optional)

    Returns:
        list: List of CSS file paths (may be empty)
    """
    css_files = []
    md_dir = os.path.dirname(os.path.abspath(markdown_file))

    # Extract CSS from frontmatter
    frontmatter_css = metadata.get("css", [])

    # Handle both string and list format
    if isinstance(frontmatter_css, str):
        frontmatter_css = [frontmatter_css]
    elif not isinstance(frontmatter_css, list):
        frontmatter_css = []

    # Resolve CSS paths relative to markdown file
    for css_path in frontmatter_css:
        abs_path = os.path.join(md_dir, css_path)
        if os.path.exists(abs_path):
            css_files.append(abs_path)
            logger.info(f"Using CSS from frontmatter: {css_path}")
        else:
            logger.warning(f"CSS file not found: {abs_path}")

    # Add CLI CSS argument last (highest priority)
    if cli_css_arg:
        if os.path.exists(cli_css_arg):
            css_files.append(cli_css_arg)
            logger.info(f"Using CSS from CLI: {cli_css_arg}")
        else:
            logger.warning(f"CLI CSS file not found: {cli_css_arg}")

    if not css_files:
        logger.warning("No CSS files found for styling")

    return css_files


def html_to_pdf(html_content, output_path, css_files=None):
    """
    Convert HTML to PDF with optional CSS styling.

    Args:
        html_content: HTML content string
        output_path: Path for output PDF file
        css_files: List of CSS file paths (optional)

    Returns:
        str: Path to generated PDF file
    """
    if USE_EXECUTABLE:
        logger.info("Using weasyprint executable for PDF generation")
        _html_to_pdf_with_executable(html_content, output_path, css_files)
    else:
        logger.info("Using WeasyPrint Python module for PDF generation")
        html_obj = HTML(string=html_content)

        stylesheets = []
        if css_files:
            for css_file in css_files:
                stylesheets.append(CSS(filename=css_file))

        html_obj.write_pdf(output_path, stylesheets=stylesheets)

    logger.info(f"Generated PDF: {output_path}")
    return output_path


def _html_to_pdf_with_executable(html_content, output_path, css_files=None):
    """
    Convert HTML to PDF using weasyprint executable (fallback for Windows).

    Args:
        html_content: HTML content string
        output_path: Path for output PDF file
        css_files: List of CSS file paths (optional)

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
        cmd = [weasyprint_cmd, html_tmp_path, str(output_path)]

        # Add CSS stylesheets if provided
        if css_files:
            for css_file in css_files:
                cmd.extend(["-s", css_file])

        # Call weasyprint executable
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    finally:
        # Clean up temp file
        Path(html_tmp_path).unlink(missing_ok=True)
