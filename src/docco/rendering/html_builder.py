"""
HTML document construction from sections.
"""

from typing import Optional
from docco.core.section import Section
from docco.content.markdown import MarkdownConverter


class HTMLBuilder:
    """
    Builds HTML documents from sections and metadata.

    Generates:
    - Title page
    - Table of contents
    - Content sections with proper IDs and anchors
    """

    def __init__(self, markdown_converter: Optional[MarkdownConverter] = None):
        """
        Initialize HTML builder.

        Args:
            markdown_converter: Markdown converter instance (creates one if not provided)
        """
        self.md_converter = markdown_converter or MarkdownConverter()

    def build_title_page(
        self, title: str, subtitle: Optional[str] = None, date: Optional[str] = None
    ) -> str:
        """
        Build title page HTML.

        Args:
            title: Document title
            subtitle: Optional subtitle
            date: Optional date string

        Returns:
            HTML string for title page
        """
        parts = ['<div class="title-page">', f"<h1>{self._escape_html(title)}</h1>"]

        if subtitle:
            parts.append(f'<p class="subtitle">{self._escape_html(subtitle)}</p>')

        if date:
            parts.append(f'<p class="date">{self._escape_html(date)}</p>')

        parts.append("</div>")
        return "\n".join(parts)

    def build_toc(self, sections: list[Section]) -> str:
        """
        Build table of contents HTML.

        Args:
            sections: List of numbered sections

        Returns:
            HTML string for TOC
        """
        parts = ['<div class="toc-page">', "<h1>Table of Contents</h1>", '<nav class="toc">']

        for section in sections:
            section_id = self._make_section_id(section.number)
            indent_class = f"toc-level-{section.level}" if section.level > 0 else "toc-level-addendum"

            parts.append(
                f'<div class="{indent_class}">'
                f'<a href="#{section_id}">{section.number} {self._escape_html(section.title)}</a>'
                f"</div>"
            )

        parts.extend(["</nav>", "</div>"])
        return "\n".join(parts)

    def build_section(self, section: Section) -> str:
        """
        Build HTML for a single section.

        Args:
            section: Section with content

        Returns:
            HTML string for the section
        """
        section_id = self._make_section_id(section.number)

        # Determine heading tag (addendums use h1)
        h_tag = f"h{section.level}" if section.level > 0 else "h1"

        # Wrap section in div with orientation class (use .value to get string)
        parts = [f'<div class="section-wrapper {section.orientation.value}">']

        # Build section header with number and title
        parts.append(
            f'<{h_tag} class="section" id="{section_id}">'
            f"{section.number} {self._escape_html(section.title)}"
            f"</{h_tag}>"
        )

        # Convert and add content
        if section.content and section.content.strip():
            html_content = self.md_converter.convert(section.content)
            parts.append(html_content)

        parts.append("</div>")

        return "\n".join(parts)

    def build_document(
        self,
        sections: list[Section],
        title: str,
        subtitle: Optional[str] = None,
        date: Optional[str] = None,
    ) -> str:
        """
        Build complete HTML document.

        Args:
            sections: List of numbered sections
            title: Document title
            subtitle: Optional subtitle
            date: Optional date

        Returns:
            Complete HTML document string
        """
        parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            f"<title>{self._escape_html(title)}</title>",
            "</head>",
            "<body>",
            # Title page
            self.build_title_page(title, subtitle, date),
            # Table of contents
            self.build_toc(sections),
            # Content sections
            '<div class="content">',
        ]

        # Add each section
        for section in sections:
            parts.append(self.build_section(section))

        parts.extend(
            [
                "</div>",  # content
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(parts)

    @staticmethod
    def _make_section_id(number: str) -> str:
        """
        Generate HTML ID from section number.

        Args:
            number: Section number (e.g., "1.2.3" or "A")

        Returns:
            Valid HTML ID (e.g., "section-1-2-3" or "section-a")
        """
        return f"section-{number.lower().replace('.', '-')}"

    @staticmethod
    def _escape_html(text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            HTML-safe string
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )
