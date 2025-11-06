"""Convert markdown to HTML using markdown-it-py."""

from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from docco.utils import setup_logger

logger = setup_logger(__name__)


def markdown_to_html(markdown_content):
    """
    Convert markdown content to HTML.

    Args:
        markdown_content: Markdown text

    Returns:
        str: HTML content
    """
    md = MarkdownIt().use(attrs_plugin).use(attrs_block_plugin).enable("table")

    html = md.render(markdown_content)
    logger.info("Converted markdown to HTML")
    return html


def wrap_html(html_content, header_content=None, footer_content=None):
    """
    Wrap HTML content in a complete HTML document with optional header/footer.

    Args:
        html_content: Raw HTML body content
        header_content: Header HTML (for running header in PDF)
        footer_content: Footer HTML (for running footer in PDF)

    Returns:
        str: Complete HTML document
    """
    # Build running elements for header/footer
    running_elements = ""
    if header_content:
        running_elements += f"{header_content}\n"
    if footer_content:
        running_elements += f"{footer_content}\n"

    wrapped = f"""<!DOCTYPE html>
<html>
<head>
</head>
<body>
{running_elements}{html_content}
</body>
</html>"""

    return wrapped
