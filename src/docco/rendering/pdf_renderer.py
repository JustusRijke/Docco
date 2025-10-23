"""
PDF rendering using WeasyPrint.
"""

from pathlib import Path
from weasyprint import HTML, CSS


class PDFRenderer:
    """
    Wrapper around WeasyPrint for PDF generation.

    Handles:
    - HTML to PDF conversion
    - CSS stylesheet application
    - Output file management
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
            OSError: If output directory doesn't exist or is not writable
            weasyprint errors: For rendering issues
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render PDF
        HTML(string=html_content).write_pdf(output_path, stylesheets=[CSS(string=css_content)])

    @staticmethod
    def render_to_bytes(html_content: str, css_content: str) -> bytes:
        """
        Render HTML and CSS to PDF bytes (in-memory).

        Useful for testing or streaming PDFs without writing to disk.

        Args:
            html_content: Complete HTML document string
            css_content: CSS stylesheet string

        Returns:
            PDF file contents as bytes
        """
        return HTML(string=html_content).write_pdf(stylesheets=[CSS(string=css_content)])
