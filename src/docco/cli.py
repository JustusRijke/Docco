"""
Command-line interface for Docco.
"""

from pathlib import Path
import re
import click
import yaml
from docco.rendering.pdf_renderer import PDFRenderer
from docco.rendering.headers_footers import HeaderFooterProcessor, modify_css_for_running_elements
from docco.content.language_filter import LanguageFilter


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
    help="Output PDF path (default: output/<filename>.pdf)",
)
def build(markdown_file: Path, css_file: Path, output: Path | None):
    """
    Build a PDF document from Markdown and CSS files.

    MARKDOWN_FILE can contain optional YAML frontmatter with languages and no_headers_first_page.

    CSS_FILE should contain all styling for the PDF layout.

    Example:

        docco build examples/document.md examples/style.css --output my_doc.pdf
    """
    click.echo(f"Building document from: {markdown_file}")
    click.echo(f"Using stylesheet: {css_file}")

    # Default output path using input filename
    if output is None:
        output = Path("output") / f"{markdown_file.stem}.pdf"

    try:
        # Parse markdown file
        markdown_content = markdown_file.read_text(encoding="utf-8")
        metadata, content = _parse_frontmatter(markdown_content)

        # Parse languages from frontmatter
        languages_str = metadata.get("languages", "")
        if languages_str:
            languages = [lang.strip() for lang in languages_str.split()]
        else:
            languages = [None]  # Single unnamed language (backward compatible)

        # Parse no_headers_first_page flag (default: True)
        no_headers_first_page = metadata.get("no_headers_first_page", True)

        # Read CSS
        css = css_file.read_text(encoding="utf-8")

        # Initialize header/footer processor
        hf_processor = HeaderFooterProcessor(markdown_file)

        # Check if any header/footer templates exist (for CSS modification)
        # Try first language to determine if headers/footers should be injected into CSS
        first_lang = languages[0]
        sample_header, sample_footer = hf_processor.load_templates(first_lang)

        # Modify CSS for running elements (done once, applies to all languages)
        css, css_warnings = modify_css_for_running_elements(
            css, has_header=sample_header is not None, has_footer=sample_footer is not None,
            no_headers_first_page=no_headers_first_page
        )
        for warning in css_warnings:
            click.echo(warning, err=True)

        # Generate PDF for each language
        language_filter = LanguageFilter()
        for language in languages:
            # Load language-specific header/footer templates
            header_template, footer_template = hf_processor.load_templates(language)

            # Replace variables in templates
            header_html = None
            footer_html = None
            if header_template:
                header_html = hf_processor.replace_variables(header_template, language)
                # Determine which file was actually loaded
                if language and (hf_processor.base_dir / f"header.{language}.html").exists():
                    click.echo(f"Using header.{language}.html")
                else:
                    click.echo("Using header.html")
            if footer_template:
                footer_html = hf_processor.replace_variables(footer_template, language)
                # Determine which file was actually loaded
                if language and (hf_processor.base_dir / f"footer.{language}.html").exists():
                    click.echo(f"Using footer.{language}.html")
                else:
                    click.echo("Using footer.html")

            # Filter content for this language
            if language:
                filtered_content = language_filter.filter_for_language(content, language)
            else:
                filtered_content = content  # No filtering for single unnamed language

            # Build HTML from filtered content
            html = _build_html_from_markdown(
                content=filtered_content,
                markdown_file_path=markdown_file,
            )

            # Inject running elements into HTML
            html = hf_processor.inject_running_elements(html, header_html, footer_html)

            # Determine output path
            if language and len(languages) > 1:
                # Add language suffix for multiple languages
                output_path = output.parent / f"{output.stem}_{language}{output.suffix}"
                debug_html_path = output.parent / f"debug_{language}.html"
            else:
                # No suffix for single language (backward compatible)
                output_path = output
                debug_html_path = output.parent / "debug.html"

            # Save debug HTML
            output_path.parent.mkdir(parents=True, exist_ok=True)
            debug_html_path.write_text(html, encoding="utf-8")
            if language:
                click.echo(f"[{language}] Debug HTML saved to: {debug_html_path}")
            else:
                click.echo(f"Debug HTML saved to: {debug_html_path}")

            # Render PDF
            PDFRenderer.render(html, css, output_path)

            if language:
                click.echo(f"✓ [{language}] PDF generated: {output_path}")
            else:
                click.echo(f"✓ PDF generated: {output_path}")

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
    markdown_file_path: Path | None = None,
) -> str:
    """
    Build complete HTML document from markdown content.

    Parses markdown for:
    - Headings (for TOC generation)
    - HTML comment directives (<!-- landscape -->, <!-- portrait -->, <!-- addendum -->, <!-- TOC -->, <!-- pagebreak -->)
    - HTML img tags (for caption wrapping and path resolution)

    Args:
        content: Markdown content
        markdown_file_path: Path to markdown file (for resolving image paths)

    Returns:
        Complete HTML document string
    """
    # Check if content has <!-- TOC --> directive
    toc_placeholder = "___DOCCO_TOC_PLACEHOLDER___"
    has_toc_directive = "<!-- TOC -->" in content

    if has_toc_directive:
        # Replace directive with placeholder that survives markdown conversion
        content = content.replace("<!-- TOC -->", f"<!-- {toc_placeholder} -->")

    # Replace page break directives with placeholder
    pagebreak_placeholder = "___DOCCO_PAGEBREAK_PLACEHOLDER___"
    content = content.replace("<!-- pagebreak -->", f"<!-- {pagebreak_placeholder} -->")

    # Parse content into sections with directives
    sections = _parse_sections(content, markdown_file_path)

    # Build TOC
    toc_html = _build_toc(sections)

    # Build sections HTML with orientation wrappers
    sections_html = []
    for section in sections:
        orientation_class = section["orientation"]
        section_html = f'<div class="section-wrapper {orientation_class}">\n{section["html"]}\n</div>'

        # Replace TOC placeholder if present in this section
        if has_toc_directive and toc_placeholder in section_html:
            section_html = section_html.replace(f"<!-- {toc_placeholder} -->", toc_html)

        # Replace page break placeholders with actual page break elements
        if pagebreak_placeholder in section_html:
            section_html = section_html.replace(f"<!-- {pagebreak_placeholder} -->", '<div class="pagebreak"></div>')

        sections_html.append(section_html)

    # Build complete document
    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        "<title>Document</title>",
        "</head>",
        "<body>",
    ]

    # Only add TOC at beginning if no directive was found
    if not has_toc_directive:
        html_parts.append(toc_html)

    html_parts.extend([
        '<div class="content">',
        "\n".join(sections_html),
        "</div>",
        "</body>",
        "</html>",
    ])

    return "\n".join(html_parts)


def _process_html_images(html: str, markdown_file_path: Path | None = None) -> str:
    """
    Post-process HTML img tags to:
    1. Resolve relative image paths to file:// URLs
    2. Wrap images with alt text in <figure> elements with <figcaption>

    Args:
        html: HTML content containing img tags
        markdown_file_path: Path to markdown file (for resolving relative paths)

    Returns:
        HTML with processed img tags
    """
    if not markdown_file_path:
        return html

    base_dir = markdown_file_path.parent

    # Pattern to match img tags and extract attributes
    img_pattern = re.compile(
        r'<img\s+([^>]+)\s*/?>',
        re.IGNORECASE
    )

    def process_img_tag(match):
        attrs_str = match.group(1)

        # Extract src attribute
        src_match = re.search(r'src=(["\'])([^"\']+)\1', attrs_str)
        if not src_match:
            return match.group(0)  # No src, leave as-is

        src_path = src_match.group(2)

        # Skip if already a file:// URL or absolute path
        if src_path.startswith('file://') or src_path.startswith('/'):
            return match.group(0)

        # Resolve relative path to file:// URL
        try:
            resolved_path = (base_dir / src_path).resolve()
            if not resolved_path.exists():
                click.echo(f"✗ Image not found: {src_path}", err=True)
                return f'<span class="image-error">[Image not found: {src_path}]</span>'

            file_url = resolved_path.as_uri()

            # Replace src with file:// URL
            new_attrs = attrs_str.replace(src_match.group(0), f'src="{file_url}"')
            new_img_tag = f'<img {new_attrs} />'

            # Check if img has alt attribute for caption
            alt_match = re.search(r'alt=(["\'])([^"\']+)\1', attrs_str)
            if alt_match and alt_match.group(2).strip():
                alt_text = alt_match.group(2)
                # Wrap in figure with figcaption
                return (
                    f'<figure>\n'
                    f'  {new_img_tag}\n'
                    f'  <figcaption>{_escape_html(alt_text)}</figcaption>\n'
                    f'</figure>'
                )
            else:
                return new_img_tag

        except Exception as e:
            click.echo(f"✗ Image processing error: {e}", err=True)
            return f'<span class="image-error">[Image error: {e}]</span>'

    return img_pattern.sub(process_img_tag, html)


def _parse_sections(content: str, markdown_file_path: Path | None = None) -> list[dict]:
    """
    Parse markdown content into sections with orientation and addendum directives.

    Supports HTML comment directives:
    - <!-- landscape --> : Next section uses landscape orientation
    - <!-- portrait --> : Next section uses portrait orientation
    - <!-- addendum --> : Next section is an appendix (lettered A, B, C...)
    - <!-- pagebreak --> : Insert a page break
    - <!-- TOC --> : Insert table of contents
    - <!-- inline: name args --> : Inline directives from inlines/ folder

    Args:
        content: Markdown content
        markdown_file_path: Path to markdown file (for resolving image paths)

    Returns:
        List of section dicts with keys: html, orientation, title, level, id, number, is_addendum
    """
    from docco.content.markdown import MarkdownConverter
    from docco.content.commands import InlineProcessor

    # Process inline directives before markdown conversion
    if markdown_file_path:
        processor = InlineProcessor(markdown_file_path.parent)
        content = processor.process(content)

    converter = MarkdownConverter()
    sections = []

    # Find all headings (H1, H2, H3)
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    directive_pattern = re.compile(r"<!--\s*(landscape|portrait|addendum)\s*-->", re.IGNORECASE)

    headings = list(heading_pattern.finditer(content))

    if not headings:
        # No headings - treat entire content as single section
        html = converter.convert(content)
        # Post-process HTML images
        html = _process_html_images(html, markdown_file_path)
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

    # Process content before first heading (e.g., title page)
    if headings and headings[0].start() > 0:
        pre_content = content[:headings[0].start()].strip()
        if pre_content:
            html = converter.convert(pre_content)
            html = _process_html_images(html, markdown_file_path)
            sections.append({
                "html": html,
                "orientation": "portrait",
                "title": None,
                "level": 0,
                "id": None,
                "number": None,
                "is_addendum": False
            })

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

        # Convert section content to HTML (without heading)
        content_html = converter.convert(section_content) if section_content else ""
        # Post-process HTML images
        content_html = _process_html_images(content_html, markdown_file_path)

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
