"""Core utilities: logging, frontmatter parsing, HTML wrapping."""

import logging
import frontmatter
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin


def setup_logger(name=__name__, level=logging.INFO):
    """Set up logger for Docco."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        tuple: (metadata dict, body string)

    Raises:
        ValueError: If frontmatter YAML is invalid
    """
    try:
        post = frontmatter.loads(content)
        return post.metadata, post.content
    except Exception as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")


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
    logger = setup_logger(__name__)
    logger.info("Converted markdown to HTML")
    return html


def wrap_html(html_content, css_content=""):
    """
    Wrap HTML content in a complete HTML document.

    Args:
        html_content: Raw HTML body content
        css_content: CSS content to embed in <style> tag (optional)

    Returns:
        str: Complete HTML document
    """
    style_tag = f"<style>\n{css_content}\n</style>\n" if css_content.strip() else ""

    wrapped = f"""<!DOCTYPE html>
<html>
<head>
{style_tag}</head>
<body>
{html_content}
</body>
</html>"""

    return wrapped
