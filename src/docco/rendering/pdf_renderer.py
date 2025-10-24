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
            weasyprint errors: For rendering issues
        """
        HTML(string=html_content).write_pdf(output_path, stylesheets=[CSS(string=css_content)])
