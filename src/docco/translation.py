"""POT/PO translation support for Docco using translate-toolkit."""

import os
import tempfile
from translate.convert import html2po, po2html
from docco.utils import setup_logger

logger = setup_logger(__name__)


def extract_html_to_pot(html_content, output_path):
    """
    Extract translatable strings from HTML content to POT file.

    Args:
        html_content: HTML content to extract from
        output_path: Path to write POT file to

    Returns:
        str: Path to generated POT file
    """
    logger.info(f"Extracting translatable strings from HTML to {output_path}")

    # Create temporary HTML file for translate-toolkit
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_tmp:
        html_tmp.write(html_content)
        html_tmp_path = html_tmp.name

    try:
        # Convert HTML to POT using file objects
        with open(html_tmp_path, 'rb') as html_file, open(output_path, 'wb') as pot_file:
            html2po.converthtml(html_file, pot_file, None, pot=True)

        logger.info(f"Extracted to POT: {output_path}")
        return output_path
    finally:
        # Clean up temporary file
        os.unlink(html_tmp_path)


def apply_po_to_html(html_content, po_path):
    """
    Apply PO file translations to HTML content.

    Args:
        html_content: HTML content to translate
        po_path: Path to PO file with translations

    Returns:
        str: HTML content with translations applied
    """
    logger.info(f"Applying translations from {po_path}")

    if not os.path.exists(po_path):
        raise FileNotFoundError(f"PO file not found: {po_path}")

    # Create temporary files for translate-toolkit
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_tmp:
        html_tmp.write(html_content)
        html_tmp_path = html_tmp.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as out_tmp:
        out_tmp_path = out_tmp.name

    try:
        # Convert PO to HTML using file objects
        with open(po_path, 'rb') as po_file, open(html_tmp_path, 'rb') as html_file, open(out_tmp_path, 'wb') as out_file:
            po2html.converthtml(po_file, out_file, html_file)

        # Read the translated HTML
        with open(out_tmp_path, 'r', encoding='utf-8') as f:
            translated_html = f.read()

        logger.info(f"Applied translations from {po_path}")
        return translated_html
    finally:
        # Clean up temporary files
        os.unlink(html_tmp_path)
        os.unlink(out_tmp_path)
