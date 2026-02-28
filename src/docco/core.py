"""Core utilities: logging, frontmatter parsing, HTML wrapping."""

import logging
import re
from pathlib import Path
from typing import cast
from urllib.parse import urljoin

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

logger = logging.getLogger(__name__)

# Known frontmatter keys that docco understands
KNOWN_FRONTMATTER_KEYS = {
    "css",
    "js",
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


def absolutize_css_urls(css_content: str, css_file_path: Path) -> str:
    """
    Convert relative URLs in CSS to absolute file:// URLs.

    Preserves absolute URLs (http://, https://, file://) and data URLs.
    """
    css_dir = css_file_path.resolve().parent
    base_url = css_dir.as_uri()

    def replace_url(match: re.Match) -> str:
        url = match.group(1).strip("'\" ")
        if (
            url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("file://")
            or url.startswith("data:")
        ):
            return match.group(0)
        return f'url("{urljoin(base_url + "/", url)}")'

    return re.sub(r'url\(["\']?([^)]+?)["\']?\)', replace_url, css_content)


def _fix_style_block_urls(html_content: str, base_dir: Path) -> str:
    """
    Absolutize url() references inside all <style> blocks and validate file existence.

    Raises:
        FileNotFoundError: If a referenced local file does not exist
    """
    # Sentinel path so absolutize_css_urls resolves relative to base_dir
    sentinel = base_dir / "_"

    def replace_style(match: re.Match) -> str:
        absolutized = absolutize_css_urls(match.group(1), sentinel)
        # Validate all file:// URLs
        for url_match in re.finditer(r'url\("(file://[^"]+)"\)', absolutized):
            from urllib.request import url2pathname

            file_path = Path(url2pathname(url_match.group(1)[7:]))  # strip "file://"
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Asset not found (referenced in CSS): {file_path}"
                )
        return f"<style>{absolutized}</style>"

    return re.sub(r"<style>(.*?)</style>", replace_style, html_content, flags=re.DOTALL)


def _absolutize_html_urls(html_content: str, base_dir: Path) -> str:
    """
    Convert relative URLs in HTML to absolute file:// URLs.

    Converts src and href attributes while preserving:
    - Anchor links (#section)
    - Absolute URLs (http://, https://, file://)
    - Data URLs (data:)

    Args:
        html_content: HTML content string
        base_dir: Base directory for resolving relative paths

    Returns:
        str: HTML with absolutized URLs
    """
    import re
    from urllib.parse import urljoin

    base_url = base_dir.resolve().as_uri()

    def replace_url(match: re.Match) -> str:
        attr = match.group(1)
        quote = match.group(2)
        url = match.group(3)

        # Preserve anchor links, absolute URLs, and data URLs
        if (
            url.startswith("#")
            or url.startswith("http://")
            or url.startswith("https://")
            or url.startswith("file://")
            or url.startswith("data:")
        ):
            return match.group(0)

        # Convert relative URL to absolute file:// URL
        abs_url = urljoin(base_url + "/", url)
        return f"{attr}={quote}{abs_url}{quote}"

    # Match src="..." or href="..." with single or double quotes
    pattern = r'((?:src|href))=(["\'])(.*?)\2'
    return re.sub(pattern, replace_url, html_content)


def wrap_html(
    html_content: str,
    css_content: str = "",
    external_css: list[str] | None = None,
    js_content: str = "",
    external_js: list[str] | None = None,
    base_dir: Path | None = None,
) -> str:
    """
    Wrap HTML content in a complete HTML document.

    Args:
        html_content: Raw HTML body content
        css_content: CSS content to embed in <style> tag (optional)
        external_css: List of external CSS URLs (optional)
        js_content: JS content to embed in <script> tag (optional)
        external_js: List of external JS URLs (optional)
        base_dir: Base directory for resolving relative paths (optional)

    Returns:
        str: Complete HTML document
    """
    # Convert relative URLs to absolute if base_dir provided
    if base_dir:
        html_content = _absolutize_html_urls(html_content, base_dir)

    style_tag = f"<style>\n{css_content}\n</style>\n" if css_content.strip() else ""

    # Generate <link> tags for external CSS URLs
    external_css = external_css or []
    link_tags = "\n".join(
        f'<link rel="stylesheet" href="{url}">' for url in external_css
    )
    link_tags = f"{link_tags}\n" if link_tags else ""

    script_tag = f"<script>\n{js_content}\n</script>\n" if js_content.strip() else ""

    # Generate <script src="..."> tags for external JS URLs
    external_js = external_js or []
    script_src_tags = "\n".join(f'<script src="{url}"></script>' for url in external_js)
    script_src_tags = f"{script_src_tags}\n" if script_src_tags else ""

    head_content = f"{link_tags}{style_tag}{script_tag}{script_src_tags}"

    # Load template and replace placeholders
    template_path = Path(__file__).parent / "templates" / "base.html"
    template = template_path.read_text()
    wrapped = template.replace("{HEAD_CONTENT}", head_content).replace(
        "{BODY_CONTENT}", html_content
    )

    if base_dir:
        wrapped = _fix_style_block_urls(wrapped, base_dir)

    return wrapped
