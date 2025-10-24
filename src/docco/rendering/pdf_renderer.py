"""
PDF rendering using WeasyPrint.
"""

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

# On Windows, always use executable (Python library causes errors)
if platform.system() == "Windows":
    USE_EXECUTABLE = True
else:
    # Check if WeasyPrint Python library is available
    try:
        import weasyprint
        USE_EXECUTABLE = False
    except ImportError:
        USE_EXECUTABLE = True


class PDFRenderer:
    """
    Wrapper around WeasyPrint for PDF generation.

    Handles:
    - HTML to PDF conversion
    - CSS stylesheet application
    - Output file management
    - Fallback to weasyprint executable if Python library unavailable
    """

    @staticmethod
    def render(html_content: str, css_content: str, output_path: Path) -> None:
        """
        Render HTML and CSS to a PDF file.

        Args:
            html_content: Complete HTML document string
            css_content: CSS stylesheet string
            output_path: Path where PDF will be saved

        Raises:
            RuntimeError: If neither Python library nor executable available
            subprocess.CalledProcessError: If executable rendering fails
        """
        if USE_EXECUTABLE:
            PDFRenderer._render_with_executable(html_content, css_content, output_path)
        else:
            from weasyprint import HTML, CSS  # Import again to satisfy type checker
            HTML(string=html_content).write_pdf(output_path, stylesheets=[CSS(string=css_content)])

    @staticmethod
    def _render_with_executable(html_content: str, css_content: str, output_path: Path) -> None:
        """
        Render using weasyprint executable (fallback for Windows).

        Args:
            html_content: Complete HTML document string
            css_content: CSS stylesheet string
            output_path: Path where PDF will be saved

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

        # Create temp files for HTML and CSS
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_tmp:
            html_tmp.write(html_content)
            html_tmp_path = html_tmp.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False, encoding='utf-8') as css_tmp:
            css_tmp.write(css_content)
            css_tmp_path = css_tmp.name

        try:
            # Call weasyprint executable
            subprocess.run(
                [weasyprint_cmd, html_tmp_path, str(output_path), '-s', css_tmp_path],
                check=True,
                capture_output=True,
                text=True
            )
        finally:
            # Clean up temp files
            Path(html_tmp_path).unlink(missing_ok=True)
            Path(css_tmp_path).unlink(missing_ok=True)
