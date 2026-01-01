"""Process TOC (Table of Contents) directive."""

import logging
import re

logger = logging.getLogger(__name__)


def _strip_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text)


def _generate_id(text):
    """Generate URL-safe ID from heading text."""
    # Remove HTML tags
    text = _strip_html_tags(text)
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")
    return slug or "heading"


def _extract_headings(html_content):
    """
    Extract headings from HTML and ensure they have IDs.

    Headings preceded by <!-- toc:exclude --> are excluded from TOC and numbering.

    Returns:
        tuple: (modified_html, list of (level, id, text) tuples)
    """
    headings = []
    used_ids = set()

    # Find positions of toc:exclude directives and following headings (only at line start, allowing leading whitespace)
    exclude_pattern = r"^\s*<!--\s*toc:exclude\s*-->\s*<(h[1-6])"
    excluded_positions = set()
    for match in re.finditer(exclude_pattern, html_content, flags=re.MULTILINE):
        # Mark the position of the heading tag that follows
        excluded_positions.add(match.end() - 3)  # Position of '<h'

    # Pattern to match h1-h6 tags
    heading_pattern = r"<(h[1-6])(\s+[^>]*)?>(.*?)</\1>"

    def process_heading(match):
        tag = match.group(1)  # h1, h2, etc.
        attrs = match.group(2) or ""  # existing attributes
        text = match.group(3)  # heading content

        level = int(tag[1])  # Extract number from h1-h6

        # Check if this heading should be excluded from TOC
        is_excluded = match.start() in excluded_positions

        # Check if heading already has an id
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        if id_match:
            heading_id = id_match.group(1)
        else:
            # Generate unique ID
            base_id = _generate_id(text)
            heading_id = base_id
            counter = 1
            while heading_id in used_ids:
                heading_id = f"{base_id}-{counter}"
                counter += 1

            # Add id to attributes
            if attrs:
                attrs = f'{attrs} id="{heading_id}"'
            else:
                attrs = f' id="{heading_id}"'

        used_ids.add(heading_id)

        if not is_excluded:
            # Only add to TOC if not excluded
            headings.append((level, heading_id, text))

        # Return modified heading with id (numbering added later)
        return f"<{tag}{attrs}>{text}</{tag}>"

    modified_html = re.sub(heading_pattern, process_heading, html_content)

    # Remove toc:exclude directives from HTML
    modified_html = re.sub(
        r"^\s*<!--\s*toc:exclude\s*-->\s*", "", modified_html, flags=re.MULTILINE
    )

    return modified_html, headings


def _update_counters(counters, level):
    """Update counters for heading numbering and return formatted number."""
    counters[level - 1] += 1
    for i in range(level, 6):
        counters[i] = 0

    number_parts = [str(counters[i]) for i in range(level) if counters[i] > 0]
    number = ".".join(number_parts)
    return number + " " if number else ""


def _close_lists_up_to(toc_lines, current_level, target_level, li_open):
    """Close lists and list items when moving up levels."""
    while current_level > target_level:
        if li_open:
            toc_lines.append("</li>")
        toc_lines.append("</ul>")
        current_level -= 1
        # After closing a nested list, the parent li is still open
        li_open = True if current_level > 0 else False
    return current_level, li_open


def _open_lists_down_to(toc_lines, current_level, target_level):
    """Open nested lists when moving down levels."""
    while current_level < target_level:
        current_level += 1
        toc_lines.append(f'<ul class="toc-level-{current_level}">')
    return current_level


def _build_toc_html(headings):
    """Build hierarchical TOC HTML with numbering."""
    if not headings:
        return '<nav class="toc"><p>No headings found</p></nav>'

    toc_lines = ['<nav class="toc">']
    current_level = 0
    li_open = False
    counters = [0, 0, 0, 0, 0, 0]  # h1-h6

    for level, heading_id, text in headings:
        display_text = _strip_html_tags(text)
        number = _update_counters(counters, level)

        # Handle level changes
        if current_level > level:
            # Moving up levels - close nested lists
            current_level, li_open = _close_lists_up_to(
                toc_lines, current_level, level, li_open
            )

        if current_level == level and li_open:
            # Same level - close previous li
            toc_lines.append("</li>")
            li_open = False

        if current_level == 0:
            # Start first list
            toc_lines.append(f'<ul class="toc-level-{level}">')
            current_level = level
        elif current_level < level:
            # Moving down levels - open nested lists
            current_level = _open_lists_down_to(toc_lines, current_level, level)

        # Wrap number in span for independent CSS styling
        toc_lines.append(
            f'<li><a href="#{heading_id}"><span class="toc-number">{number}</span>{display_text}</a>'
        )
        li_open = True

    # Close remaining open items
    while current_level > 0:
        if li_open:
            toc_lines.append("</li>")
            li_open = False
        toc_lines.append("</ul>")
        current_level -= 1
        # After closing a list, parent li is still open (if not at root)
        if current_level > 0:
            li_open = True

    toc_lines.append("</nav>")
    return "\n".join(toc_lines)


def _number_headings(html_content, headings):
    """
    Add numbers to heading text in HTML based on heading list.

    Args:
        html_content: HTML with headings
        headings: List of (level, id, text) tuples

    Returns:
        str: HTML with numbered headings
    """
    # Build a map of heading ID to number
    counters = [0, 0, 0, 0, 0, 0]  # h1-h6
    heading_numbers = {}

    for level, heading_id, _ in headings:
        number = _update_counters(counters, level)
        heading_numbers[heading_id] = number

    # Replace heading text with numbered text
    def add_number(match):
        tag = match.group(1)
        attrs = match.group(2) or ""
        text = match.group(3)

        # Extract ID
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
        if id_match:
            heading_id = id_match.group(1)
            if heading_id in heading_numbers:
                # Add number to beginning of text, wrapped in span for CSS styling
                number = heading_numbers[heading_id]
                return f'<{tag}{attrs}><span class="heading-number">{number}</span>{text}</{tag}>'

        # Return unchanged if no ID or not in our list
        return match.group(0)

    pattern = r"<(h[1-6])(\s+[^>]*)?>(.*?)</\1>"
    return re.sub(pattern, add_number, html_content)


def process_toc(html_content):
    """
    Process TOC directive by generating table of contents.

    Finds <!-- TOC --> directive and replaces it with generated TOC HTML.
    All h1-h6 headings are given IDs (if they don't have them) and included
    in the TOC with hierarchical structure.

    Args:
        html_content: HTML content to process

    Returns:
        str: HTML with TOC directive replaced by generated TOC
    """
    # Check if TOC directive exists (only at line start, allowing leading whitespace)
    toc_pattern = r"^\s*<!--\s*TOC\s*-->"
    if not re.search(toc_pattern, html_content, flags=re.MULTILINE):
        return html_content

    # Extract and process headings
    modified_html, headings = _extract_headings(html_content)

    # Build TOC HTML
    toc_html = _build_toc_html(headings)

    # Replace TOC directive with generated TOC
    result = re.sub(toc_pattern, toc_html, modified_html, flags=re.MULTILINE)

    # Add numbers to headings in document
    result = _number_headings(result, headings)

    logger.info(f"Generated TOC with {len(headings)} heading(s)")
    return result
