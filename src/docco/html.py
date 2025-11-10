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


def wrap_html(html_content):
    """
    Wrap HTML content in a complete HTML document.

    Args:
        html_content: Raw HTML body content

    Returns:
        str: Complete HTML document
    """
    wrapped = f"""<!DOCTYPE html>
<html>
<head>
</head>
<body>
{html_content}
</body>
</html>"""

    return wrapped
