"""Core utilities: logging, frontmatter parsing, HTML wrapping."""

import logging
from pathlib import Path
from typing import cast

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

logger = logging.getLogger(__name__)

# Known frontmatter keys that docco understands
KNOWN_FRONTMATTER_KEYS = {
    "css",
    "dpi",
    "multilingual",
    "base_language",
}


def parse_frontmatter(content: str) -> dict[str, object]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        dict: Parsed frontmatter metadata

    Raises:
        ValueError: If frontmatter YAML is invalid
    """
    md = MarkdownIt().use(front_matter_plugin)
    tokens = md.parse(content)
    frontmatter = next((t for t in tokens if t.type == "front_matter"), None)

    if not frontmatter:
        return {}

    try:
        metadata = yaml.safe_load(frontmatter.content) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")

    unknown_keys = set(metadata.keys()) - KNOWN_FRONTMATTER_KEYS
    if unknown_keys:
        logger.warning(
            f"Unknown frontmatter declaration(s): {', '.join(sorted(unknown_keys))}"
        )

    return metadata


def markdown_to_html(markdown_content: str) -> str:
    """
    Convert markdown content to HTML.

    Args:
        markdown_content: Markdown text

    Returns:
        str: HTML content
    """
    md = (
        MarkdownIt()
        .use(front_matter_plugin)
        .use(
            anchors_plugin,
            min_level=1,
            max_level=6,
            permalink=False,
        )
        .use(attrs_plugin)
        .use(attrs_block_plugin)
        .enable("table")
    )

    html = cast(str, md.render(markdown_content))
    logger.debug("Converted markdown to HTML")
    return html


def wrap_html(
    html_content: str, css_content: str = "", external_css: list[str] | None = None
) -> str:
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

    head_content = f"{link_tags}{style_tag}"

    # Load template and replace placeholders
    template_path = Path(__file__).parent / "templates" / "base.html"
    template = template_path.read_text()
    wrapped = template.replace("{HEAD_CONTENT}", head_content).replace(
        "{BODY_CONTENT}", html_content
    )

    return wrapped
