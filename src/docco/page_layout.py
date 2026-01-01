"""Process page layout directives (page breaks and orientation)."""

import logging
import re

logger = logging.getLogger(__name__)


def process_page_layout(html_content: str) -> str:
    """
    Process page layout directives.

    Handles:
    - <!-- pagebreak --> : Creates a page break
    - <!-- landscape --> : Starts landscape orientation section
    - <!-- portrait --> : Returns to portrait orientation section

    Wraps content in section-wrapper divs for layout handling.

    Args:
        html_content: HTML content to process

    Returns:
        str: HTML with layout directives processed
    """
    # Replace pagebreak directives with div (only at line start, allowing leading whitespace)
    html_content = re.sub(
        r"^\s*<!--\s*pagebreak\s*-->",
        '<div class="pagebreak"></div>',
        html_content,
        flags=re.MULTILINE,
    )

    # Split content by orientation directives
    # Pattern: capture directive type and content until next directive or end
    sections = []
    current_pos = 0
    current_orientation = "portrait"

    # Find all orientation directives (only at line start, allowing leading whitespace)
    orientation_pattern = r"^\s*<!--\s*(landscape|portrait)\s*-->"

    for match in re.finditer(orientation_pattern, html_content, flags=re.MULTILINE):
        # Save content before this directive
        if match.start() > current_pos:
            section_content = html_content[current_pos : match.start()].strip()
            if section_content:
                sections.append((current_orientation, section_content))

        # Update current orientation
        current_orientation = match.group(1)
        current_pos = match.end()

    # Add remaining content
    if current_pos < len(html_content):
        remaining = html_content[current_pos:].strip()
        if remaining:
            sections.append((current_orientation, remaining))

    # Wrap sections in divs and rebuild content
    wrapped_sections = []
    for orientation, content in sections:
        wrapped = f'<div class="section-wrapper {orientation}">\n{content}\n</div>'
        wrapped_sections.append(wrapped)

    result = "\n".join(wrapped_sections)

    # Remove remaining orientation directives (shouldn't be any left)
    result = re.sub(
        r"^\s*<!--\s*(landscape|portrait)\s*-->",
        "",
        result,
        flags=re.MULTILINE,
    )

    logger.debug("Processed page layout directives")
    return result
