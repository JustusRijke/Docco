"""
Markdown to HTML conversion utilities.
"""

from markdown_it import MarkdownIt


class MarkdownConverter:
    """
    Wrapper around markdown-it-py for converting Markdown to HTML.

    Future enhancements:
    - Custom plugins for special syntax
    - Image path resolution
    - Cross-reference support
    """

    def __init__(self):
        """Initialize the Markdown parser with table support."""
        self.parser = MarkdownIt().enable("table")

    def convert(self, markdown_text: str) -> str:
        """
        Convert Markdown text to HTML.

        Args:
            markdown_text: Markdown-formatted text

        Returns:
            HTML string
        """
        if not markdown_text or not markdown_text.strip():
            return ""

        return self.parser.render(markdown_text)

    def convert_inline(self, markdown_text: str) -> str:
        """
        Convert Markdown to inline HTML (no wrapping <p> tags).

        Useful for titles and short text snippets.

        Args:
            markdown_text: Markdown-formatted text

        Returns:
            HTML string with outer <p> tags stripped if present
        """
        html = self.convert(markdown_text)
        # Strip outer <p> tags if present
        html = html.strip()
        if html.startswith("<p>") and html.endswith("</p>"):
            html = html[3:-4]
        return html
