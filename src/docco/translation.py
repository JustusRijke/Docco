"""POT/PO translation support for Docco using translate-toolkit."""

import glob
import logging
import os
import subprocess
from pathlib import Path

import polib
from translate.convert import html2po, po2html
from translate.storage import po

logger = logging.getLogger(__name__)


def clean_po_file(po_path: str | Path) -> None:
    """
    Remove bloat from PO/POT file for VCS-friendly format.

    Removes unnecessary metadata, location references, and sorts entries.

    Args:
        po_path: Path to PO or POT file to clean
    """
    po_file = polib.pofile(po_path)

    # Clear all metadata and keep only essential
    po_file.metadata = {}
    po_file.metadata["Content-Type"] = "text/plain; charset=UTF-8"

    # Remove location references and sort entries
    for entry in po_file:
        entry.occurrences = []

    po_file.sort()
    po_file.save(po_path)


def extract_html_to_pot(html_path: str | Path, output_path: str | Path) -> str:
    """
    Extract translatable strings from HTML file to POT file.

    Args:
        html_path: Path to HTML file to extract from
        output_path: Path to write POT file to

    Returns:
        str: Path to generated POT file
    """
    logger.debug(f"Extracting translatable strings from {html_path} to {output_path}")

    # Convert HTML to POT using file objects
    with (
        open(html_path, "rb") as html_file,
        open(output_path, "wb") as pot_file,
    ):
        html2po.converthtml(html_file, pot_file, None, pot=True, duplicatestyle="merge")  # type: ignore[no-untyped-call]

    # Clean bloat from POT file for VCS
    clean_po_file(output_path)

    logger.debug(f"Extracted to POT: {output_path}")
    return str(output_path)


def apply_po_to_html(
    html_input_path: str | Path, po_path: str | Path, html_output_path: str | Path
) -> str:
    """
    Apply PO file translations to HTML file.

    Args:
        html_input_path: Path to HTML file to translate
        po_path: Path to PO file with translations
        html_output_path: Path to write translated HTML file

    Returns:
        str: Path to translated HTML file (same as html_output_path)
    """
    logger.debug(f"Applying translations from {po_path}")

    if not os.path.exists(po_path):
        raise FileNotFoundError(f"PO file not found: {po_path}")

    if not os.path.exists(html_input_path):  # pragma: no cover
        raise FileNotFoundError(f"HTML input file not found: {html_input_path}")

    # Convert PO to HTML using file objects
    with (
        open(po_path, "rb") as po_file,
        open(html_input_path, "rb") as html_file,
        open(html_output_path, "wb") as out_file,
    ):
        po2html.converthtml(po_file, out_file, html_file)  # type: ignore[no-untyped-call]

    logger.debug(f"Applied translations from {po_path}")
    return str(html_output_path)


def get_po_stats(po_path: str | Path) -> dict[str, int]:
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
    store = po.pofile.parsefile(po_path)  # type: ignore[no-untyped-call]
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


def check_po_sync(pot_path: str | Path, po_path: str | Path) -> bool:
    """
    Check if PO file msgids match current POT.

    Args:
        pot_path: Path to POT template file
        po_path: Path to PO translation file

    Returns:
        bool: True if in sync, False if out of sync
    """
    pot_store = po.pofile.parsefile(pot_path)  # type: ignore[no-untyped-call]
    po_store = po.pofile.parsefile(po_path)  # type: ignore[no-untyped-call]

    pot_msgids = {u.source for u in pot_store.units if u.istranslatable()}
    po_msgids = {u.source for u in po_store.units if u.istranslatable()}

    return pot_msgids == po_msgids


def update_po_files(pot_path: str | Path, translations_dir: str | Path) -> None:
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
        logger.debug("No existing PO files to update")
        return

    for po_file in po_files:
        lang = os.path.basename(po_file)
        logger.debug(f"Updating {lang} with new POT...")

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

            # Clean bloat from PO file for VCS
            clean_po_file(po_file)

            # Report statistics
            stats = get_po_stats(po_file)
            logger.debug(
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
