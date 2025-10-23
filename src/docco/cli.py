"""
Command-line interface for Docco.
"""

from pathlib import Path
import click
import yaml
from docco.rendering.pdf_renderer import PDFRenderer


@click.group()
@click.version_option(version="0.3.0", prog_name="docco")
def cli():
    """
    Docco - PDF documentation generator using HTML/CSS.

    Build professional PDF documentation from Markdown + CSS.
    """
    pass


@cli.command()
@click.argument("markdown_file", type=click.Path(exists=True, path_type=Path))
@click.argument("css_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output PDF path (default: output/document.pdf)",
)
def build(markdown_file: Path, css_file: Path, output: Path | None):
    """
    Build a PDF document from Markdown and CSS files.

    MARKDOWN_FILE should contain YAML frontmatter with metadata (title, subtitle, date, author).

    CSS_FILE should contain all styling for the PDF layout.

    Example:

        docco build examples/document.md examples/style.css --output my_doc.pdf
    """
    click.echo(f"Building document from: {markdown_file}")
    click.echo(f"Using stylesheet: {css_file}")

    # Default output path
    if output is None:
        output = Path("output/document.pdf")

    try:
        # Parse markdown file
        markdown_content = markdown_file.read_text(encoding="utf-8")
        metadata, content = _parse_frontmatter(markdown_content)

        # Validate required metadata
        if "title" not in metadata:
            raise click.ClickException("Markdown file must contain 'title' in YAML frontmatter")

        # Read CSS
        css = css_file.read_text(encoding="utf-8")

        # Build HTML (convert date to string if it's a datetime object)
        date_value = metadata.get("date")
        if date_value is not None and not isinstance(date_value, str):
            date_value = str(date_value)

        html = _build_html_from_markdown(
            content=content,
            title=metadata.get("title", "Document"),
            subtitle=metadata.get("subtitle"),
            date=date_value,
            author=metadata.get("author"),
            markdown_file_path=markdown_file,
        )

        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        # Save debug HTML if requested
        debug_html = output.parent / "debug.html"
        debug_html.write_text(html, encoding="utf-8")
        click.echo(f"Debug HTML saved to: {debug_html}")

        # Render PDF
        PDFRenderer.render(html, css, output)

        click.echo(f"✓ PDF generated: {output}")
    except Exception as e:
        click.echo(f"✗ Error building document: {e}", err=True)
        raise click.Abort()


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (metadata dict, markdown content without frontmatter)
    """
    lines = content.split("\n")

    # Check for frontmatter delimiter
    if not lines or lines[0].strip() != "---":
        return {}, content

    # Find closing delimiter
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, content

    # Parse YAML
    yaml_content = "\n".join(lines[1:end_idx])
    try:
        metadata = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML frontmatter: {e}")

    # Return metadata and remaining content
    remaining_content = "\n".join(lines[end_idx + 1 :])
    return metadata, remaining_content


def _build_html_from_markdown(
    content: str,
    title: str,
    subtitle: str | None = None,
    date: str | None = None,
    author: str | None = None,
    markdown_file_path: Path | None = None,
) -> str:
    """
    Build complete HTML document from markdown content and metadata.

    Parses markdown for:
    - Headings (for TOC generation)
    - HTML comment directives (<!-- landscape -->, <!-- portrait -->, <!-- img ... -->)

    Args:
        content: Markdown content
        title: Document title
        subtitle: Optional subtitle
        date: Optional date
        author: Optional author
        markdown_file_path: Path to markdown file (for resolving image paths)

    Returns:
        Complete HTML document string
    """
    # Build title page
    title_parts = ['<div class="title-page">', f"<h1>{_escape_html(title)}</h1>"]
    if subtitle:
        title_parts.append(f'<p class="subtitle">{_escape_html(subtitle)}</p>')
    if date:
        title_parts.append(f'<p class="date">{_escape_html(date)}</p>')
    if author:
        title_parts.append(f'<p class="author">{_escape_html(author)}</p>')
    title_parts.append("</div>")
    title_page = "\n".join(title_parts)

    # Parse content into sections with directives
    sections = _parse_sections(content, markdown_file_path)

    # Build TOC
    toc_html = _build_toc(sections)

    # Build sections HTML with orientation wrappers
    sections_html = []
    for section in sections:
        orientation_class = section["orientation"]
        section_html = f'<div class="section-wrapper {orientation_class}">\n{section["html"]}\n</div>'
        sections_html.append(section_html)

    # Build complete document
    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        f"<title>{_escape_html(title)}</title>",
        "</head>",
        "<body>",
        title_page,
        toc_html,
        '<div class="content">',
        "\n".join(sections_html),
        "</div>",
        "</body>",
        "</html>",
    ]

    return "\n".join(html_parts)


def _process_image_directives(content: str, image_processor, image_pattern) -> str:
    """
    Process image directives in content and replace with HTML img tags.

    Args:
        content: Markdown content with image directives
        image_processor: ImageProcessor instance
        image_pattern: Compiled regex pattern for image directives

    Returns:
        Content with image directives replaced by HTML img tags
    """
    from docco.content.images import parse_image_directive

    def replace_image(match):
        directive_content = match.group(1)
        img_directive = parse_image_directive(directive_content)

        if not img_directive:
            # Invalid directive, leave as-is
            return match.group(0)

        try:
            # Process image
            img_info = image_processor.process_image(img_directive['path'])

            # Build img tag
            img_attrs = [f'src="{img_info["file_url"]}"']

            if img_directive['css_class']:
                img_attrs.append(f'class="{img_directive["css_class"]}"')

            if img_directive['style']:
                img_attrs.append(f'style="{img_directive["style"]}"')

            # Add alt text (use filename without extension)
            alt_text = Path(img_directive['path']).stem
            img_attrs.append(f'alt="{alt_text}"')

            img_tag = f'<img {" ".join(img_attrs)} />'
            return img_tag

        except (FileNotFoundError, ValueError) as e:
            # Image processing failed, show error in output
            click.echo(f"✗ Image error: {e}", err=True)
            return f'<span class="image-error">[Image error: {e}]</span>'

    # Replace all image directives
    return image_pattern.sub(replace_image, content)


def _parse_sections(content: str, markdown_file_path: Path | None = None) -> list[dict]:
    """
    Parse markdown content into sections with orientation and addendum directives.

    Supports HTML comment directives:
    - <!-- landscape --> : Next section uses landscape orientation
    - <!-- portrait --> : Next section uses portrait orientation
    - <!-- addendum --> : Next section is an appendix (lettered A, B, C...)
    - <!-- img "path" "style/class" --> : Inline image

    Args:
        content: Markdown content
        markdown_file_path: Path to markdown file (for resolving image paths)

    Returns:
        List of section dicts with keys: html, orientation, title, level, id, number, is_addendum
    """
    import re
    from docco.content.markdown import MarkdownConverter
    from docco.content.images import ImageProcessor, parse_image_directive

    converter = MarkdownConverter()
    sections = []

    # Initialize image processor if markdown file path provided
    image_processor = ImageProcessor(markdown_file_path) if markdown_file_path else None

    # Find all headings (H1, H2, H3)
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    directive_pattern = re.compile(r"<!--\s*(landscape|portrait|addendum)\s*-->", re.IGNORECASE)

    # Pattern for image directives (will be processed separately)
    image_directive_pattern = re.compile(r"<!--\s*(img\s+[^>]+)\s*-->", re.IGNORECASE)

    headings = list(heading_pattern.finditer(content))

    if not headings:
        # No headings - treat entire content as single section
        # Process image directives
        processed_content = content
        if image_processor:
            processed_content = _process_image_directives(content, image_processor, image_directive_pattern)

        html = converter.convert(processed_content)
        sections.append({
            "html": html,
            "orientation": "portrait",
            "title": None,
            "level": 0,
            "id": None,
            "number": None,
            "is_addendum": False
        })
        return sections

    # Numbering state
    counters = [0, 0, 0]  # For levels 1, 2, 3
    addendum_counter = 0  # For appendix sections (A, B, C...)

    # Process each heading
    for i, heading_match in enumerate(headings):
        heading_level = len(heading_match.group(1))  # Count # symbols
        heading_title = heading_match.group(2).strip()
        heading_start = heading_match.start()

        # Determine content range
        if i < len(headings) - 1:
            content_end = headings[i + 1].start()
        else:
            content_end = len(content)

        # Look for directives BEFORE this heading
        directives_start = headings[i - 1].end() if i > 0 else 0
        directives_text = content[directives_start:heading_start]

        # Parse directives
        orientation = "portrait"  # default
        is_addendum = False

        directive_matches = list(directive_pattern.finditer(directives_text))
        for match in directive_matches:
            directive = match.group(1).lower()
            if directive in ("landscape", "portrait"):
                orientation = directive
            elif directive == "addendum":
                is_addendum = True

        # Calculate section number
        if is_addendum:
            addendum_counter += 1
            section_number = chr(64 + addendum_counter)  # A, B, C...
            level = 0  # Addendums are level 0
        else:
            level = heading_level
            # Increment counter at this level
            counters[level - 1] += 1
            # Reset all deeper level counters
            for j in range(level, 3):
                counters[j] = 0
            # Build number string (e.g., "1.2.3")
            section_number = ".".join(str(counters[k]) for k in range(level) if counters[k] > 0)

        # Extract content AFTER heading (not including heading line)
        heading_end = content.find("\n", heading_start)
        if heading_end == -1:
            heading_end = heading_start + len(heading_match.group(0))
        section_content = content[heading_end + 1:content_end].strip()

        # Process image directives in section content
        if section_content and image_processor:
            section_content = _process_image_directives(section_content, image_processor, image_directive_pattern)

        # Convert section content to HTML (without heading)
        content_html = converter.convert(section_content) if section_content else ""

        # Build heading with number
        h_tag = f"h{level}" if level > 0 else "h1"
        numbered_title = f"{section_number} {heading_title}"
        heading_html = f'<{h_tag} id="{_make_section_id(section_number)}">{_escape_html(numbered_title)}</{h_tag}>'

        # Combine heading + content
        section_html = heading_html + "\n" + content_html

        sections.append({
            "html": section_html,
            "orientation": orientation,
            "title": heading_title,
            "level": level,
            "id": _make_section_id(section_number),
            "number": section_number,
            "is_addendum": is_addendum
        })

    return sections


def _make_section_id(number: str) -> str:
    """
    Generate HTML ID from section number.

    Args:
        number: Section number (e.g., "1.2.3" or "A")

    Returns:
        Valid HTML ID (e.g., "section-1-2-3" or "section-a")
    """
    import re
    return f"section-{re.sub(r'[^a-z0-9]+', '-', number.lower()).strip('-')}"


def _build_toc(sections: list[dict]) -> str:
    """
    Build table of contents HTML from sections.

    Args:
        sections: List of section dicts with title, level, id, number, is_addendum keys

    Returns:
        HTML string for TOC page
    """
    # Filter sections that have titles (headings)
    toc_sections = [s for s in sections if s["title"]]

    if not toc_sections:
        return ""  # No TOC if no headings

    parts = [
        '<div class="toc-page">',
        '<h1>Table of Contents</h1>',
        '<nav class="toc">'
    ]

    for section in toc_sections:
        level = section["level"]
        title = section["title"]
        section_id = section["id"]
        number = section["number"]
        is_addendum = section.get("is_addendum", False)

        # Use addendum class for appendices, otherwise use level
        if is_addendum:
            indent_class = "toc-level-addendum"
        else:
            indent_class = f"toc-level-{level}"

        # Include number in TOC entry
        numbered_title = f"{number} {title}"

        parts.append(
            f'<div class="{indent_class}">'
            f'<a href="#{section_id}">{_escape_html(numbered_title)}</a>'
            f'</div>'
        )

    parts.extend(["</nav>", "</div>"])
    return "\n".join(parts)


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


@cli.command()
def version():
    """Show Docco version."""
    click.echo("Docco version 0.3.0")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
