"""POT/PO translation support for Docco using translate-toolkit."""

import os
import glob
import subprocess
import tempfile
from translate.convert import html2po, po2html
from translate.storage import po
from docco.core import setup_logger

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
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as html_tmp:
        html_tmp.write(html_content)
        html_tmp_path = html_tmp.name

    try:
        # Convert HTML to POT using file objects
        with (
            open(html_tmp_path, "rb") as html_file,
            open(output_path, "wb") as pot_file,
        ):
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
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as html_tmp:
        html_tmp.write(html_content)
        html_tmp_path = html_tmp.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as out_tmp:
        out_tmp_path = out_tmp.name

    try:
        # Convert PO to HTML using file objects
        with (
            open(po_path, "rb") as po_file,
            open(html_tmp_path, "rb") as html_file,
            open(out_tmp_path, "wb") as out_file,
        ):
            po2html.converthtml(po_file, out_file, html_file)

        # Read the translated HTML
        with open(out_tmp_path, "r", encoding="utf-8") as f:
            translated_html = f.read()

        logger.info(f"Applied translations from {po_path}")
        return translated_html
    finally:
        # Clean up temporary files
        os.unlink(html_tmp_path)
        os.unlink(out_tmp_path)


def get_po_stats(po_path):
    """
    Get translation statistics for a PO file.

    Args:
        po_path: Path to PO file

    Returns:
        dict: {
            'total': total translatable units,
            'translated': translated units (not fuzzy),
            'fuzzy': fuzzy units,
            'untranslated': untranslated units
        }
    """
    store = po.pofile.parsefile(po_path)
    units = [u for u in store.units if u.istranslatable()]

    translated = sum(1 for u in units if u.istranslated() and not u.isfuzzy())
    fuzzy = sum(1 for u in units if u.isfuzzy())
    untranslated = sum(1 for u in units if not u.istranslated() and not u.isfuzzy())

    return {
        "total": len(units),
        "translated": translated,
        "fuzzy": fuzzy,
        "untranslated": untranslated,
    }


def update_po_files(pot_path, translations_dir):
    """
    Update existing PO files with new/changed strings from POT file.

    Uses pot2po to merge updates while preserving existing translations.
    Only processes .po files in the translations_dir.

    Args:
        pot_path: Path to POT template file
        translations_dir: Directory containing .po files to update
    """
    po_files = sorted(glob.glob(os.path.join(translations_dir, "*.po")))

    if not po_files:
        logger.info("No existing PO files to update")
        return

    for po_file in po_files:
        lang = os.path.basename(po_file)
        logger.info(f"Updating {lang} with new POT...")

        # Create temporary file for merged PO
        temp_po = f"{po_file}.new"

        try:
            # Use pot2po to merge POT into PO file
            result = subprocess.run(
                ["pot2po", "-t", po_file, "-i", pot_path, "-o", temp_po],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:  # pragma: no cover
                logger.error(f"Failed to update {lang}: {result.stderr}")
                # Clean up temp file
                if os.path.exists(temp_po):
                    os.remove(temp_po)
                continue

            # Replace old PO with merged version
            os.replace(temp_po, po_file)

            # Report statistics
            stats = get_po_stats(po_file)
            logger.info(
                f"Updated {lang}: {stats['translated']} translated, "
                f"{stats['fuzzy']} fuzzy, {stats['untranslated']} untranslated"
            )

        except FileNotFoundError:  # pragma: no cover
            logger.error(
                "pot2po command not found. Ensure translate-toolkit is installed."
            )
        except subprocess.TimeoutExpired:  # pragma: no cover
            logger.error(f"pot2po timeout updating {lang}")
            if os.path.exists(temp_po):
                os.remove(temp_po)
