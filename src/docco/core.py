"""Core utilities: logging, frontmatter parsing, HTML wrapping."""

import logging
import tempfile
from pathlib import Path
from contextlib import contextmanager
import frontmatter
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin


@contextmanager
def html_temp_file(content):
    """
    Write HTML content to temp file, yield path, auto-cleanup.

    Args:
        content: HTML content string

    Yields:
        str: Path to temporary HTML file
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        path = f.name
    try:
        yield path
    finally:
        Path(path).unlink(missing_ok=True)


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
    logger = logging.getLogger(__name__)
    logger.debug("Converted markdown to HTML")
    return html


def wrap_html(html_content, css_content="", external_css=None):
    """
    Wrap HTML content in a complete HTML document.

    Args:
        html_content: Raw HTML body content
        css_content: CSS content to embed in <style> tag (optional)
        external_css: List of external CSS URLs (optional)

    Returns:
        str: Complete HTML document
    """
    style_tag = f"<style>\n{css_content}\n</style>\n" if css_content.strip() else ""

    # Generate <link> tags for external CSS URLs
    external_css = external_css or []
    link_tags = "\n".join(
        f'<link rel="stylesheet" href="{url}">' for url in external_css
    )
    link_tags = f"{link_tags}\n" if link_tags else ""

    wrapped = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
{link_tags}{style_tag}</head>
<body>
{html_content}
</body>
</html>"""

    return wrapped
