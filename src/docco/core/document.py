"""
Document class - main orchestrator for PDF generation.
"""

from pathlib import Path
from typing import Optional
from docco.core.section import Section, SectionNumberer
from docco.content.markdown import MarkdownConverter
from docco.rendering.html_builder import HTMLBuilder
from docco.rendering.css_builder import CSSBuilder
from docco.rendering.pdf_renderer import PDFRenderer


class Document:
    """
    Main document class for building PDF documentation.

    Usage:
        doc = Document(title="My Documentation")
        doc.add_section(level=1, title="Introduction", content="...")
        doc.render_pdf("output/doc.pdf")
    """

    def __init__(
        self,
        title: str,
        subtitle: Optional[str] = None,
        date: Optional[str] = None,
        header_text: Optional[str] = None,
    ):
        """
        Initialize a new document.

        Args:
            title: Document title
            subtitle: Optional subtitle
            date: Optional date string
            header_text: Optional custom text for page headers (defaults to title)
        """
        self.title = title
        self.subtitle = subtitle
        self.date = date
        self.header_text = header_text or title

        self.sections: list[Section] = []
        self._numbered = False

        # Initialize components
        self.numberer = SectionNumberer()
        self.md_converter = MarkdownConverter()
        self.html_builder = HTMLBuilder(self.md_converter)

    def add_section(
        self,
        level: int,
        title: str,
        content: str,
        number: Optional[str] = None,
    ) -> "Document":
        """
        Add a section to the document.

        Args:
            level: Heading level (1-3 for regular, 0 for addendum)
            title: Section title
            content: Markdown content
            number: Optional manual number (auto-numbered if not provided)

        Returns:
            self (for method chaining)
        """
        section = Section(level=level, title=title, content=content, number=number)
        self.sections.append(section)
        self._numbered = False  # Mark as needing renumbering
        return self

    def _ensure_numbered(self):
        """Ensure all sections are numbered."""
        if not self._numbered:
            # Only number sections that don't have manual numbers
            for section in self.sections:
                if section.number is None:
                    section.number = self.numberer.number_section(section)
            self._numbered = True

    def build_html(self, save_path: Optional[Path] = None) -> str:
        """
        Build HTML document from sections.

        Args:
            save_path: Optional path to save HTML for debugging

        Returns:
            Complete HTML document string
        """
        self._ensure_numbered()

        html = self.html_builder.build_document(
            sections=self.sections,
            title=self.title,
            subtitle=self.subtitle,
            date=self.date,
        )

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(html, encoding="utf-8")

        return html

    def render_pdf(
        self,
        output_path: Path | str,
        css: Optional[str] = None,
        save_html: bool = False,
    ) -> Path:
        """
        Render document to PDF.

        Args:
            output_path: Path where PDF will be saved
            css: Optional custom CSS (uses default if not provided)
            save_html: If True, saves HTML to output_path.parent/debug.html

        Returns:
            Path to generated PDF
        """
        output_path = Path(output_path)

        # Generate HTML
        html_debug_path = output_path.parent / "debug.html" if save_html else None
        html = self.build_html(save_path=html_debug_path)

        # Generate CSS
        if css is None:
            css = CSSBuilder.generate_custom_css(header_text=self.header_text)

        # Render PDF
        PDFRenderer.render(html, css, output_path)

        return output_path

    def clear_sections(self) -> "Document":
        """
        Remove all sections from the document.

        Returns:
            self (for method chaining)
        """
        self.sections.clear()
        self.numberer.reset()
        self._numbered = False
        return self

    def __len__(self) -> int:
        """Return number of sections in document."""
        return len(self.sections)

    def __repr__(self) -> str:
        """Return string representation of document."""
        return f"Document(title='{self.title}', sections={len(self.sections)})"
