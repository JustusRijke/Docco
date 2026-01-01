"""Core utilities: logging, frontmatter parsing, HTML wrapping."""

import logging

import frontmatter
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin

logger = logging.getLogger(__name__)

# Known frontmatter keys that docco understands
KNOWN_FRONTMATTER_KEYS = {
    "css",
    "dpi",
    "multilingual",
    "base_language",
}


def _validate_frontmatter(metadata):
    """
    Warn about unknown frontmatter keys.

    Args:
        metadata: Parsed frontmatter metadata dict
    """
    unknown_keys = set(metadata.keys()) - KNOWN_FRONTMATTER_KEYS
    if unknown_keys:
        logger.warning(
            f"Unknown frontmatter declaration(s): {', '.join(sorted(unknown_keys))}"
        )


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
        _validate_frontmatter(post.metadata)
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
