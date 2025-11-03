"""POT/PO translation support for Docco."""

import os
from mdpo.md2po import markdown_to_pofile
from mdpo.po2md import pofile_to_markdown
from docco.frontmatter import parse_frontmatter
from docco.utils import setup_logger

logger = setup_logger(__name__)


def extract_to_pot(content, output_path):
    """
    Extract translatable strings from markdown content to POT file.

    Args:
        content: Markdown content with optional frontmatter to extract from
        output_path: Path to write POT file to

    Returns:
        str: Path to generated POT file
    """
    logger.info(f"Extracting translatable strings to {output_path}")

    # Parse and remove frontmatter (only body should be translated)
    _, body = parse_frontmatter(content)

    # Use mdpo to extract markdown to PO format
    po_content = markdown_to_pofile(body)

    # Write PO content to file
    with open(output_path, "w") as f:
        f.write(str(po_content))

    logger.info(f"Extracted to POT: {output_path}")
    return output_path


def build_from_po(content, po_path):
    """
    Apply PO file translations to markdown content.

    Args:
        content: Markdown content with optional frontmatter
        po_path: Path to PO file with translations

    Returns:
        str: Markdown content with translations applied
    """
    logger.info(f"Applying translations from {po_path}")

    if not os.path.exists(po_path):
        raise FileNotFoundError(f"PO file not found: {po_path}")

    # Parse and remove frontmatter (only body should be translated)
    _, body = parse_frontmatter(content)

    # Use mdpo to apply translations to body only
    translated_content = pofile_to_markdown(body, po_path)

    logger.info(f"Applied translations from {po_path}")
    return translated_content
