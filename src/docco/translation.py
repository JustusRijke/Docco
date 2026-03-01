"""POT/PO translation support for Docco using translate-toolkit."""

import logging
import re
import shutil
import subprocess
from io import BytesIO
from pathlib import Path

import polib
from translate.convert import html2po, po2html
from translate.storage import po

logger = logging.getLogger(__name__)


def clean_po_file(po_path: Path) -> None:
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


def extract_html_to_pot(
    html_content: bytes, output_path: Path, source_name: str = "document"
) -> Path:
    """
    Extract translatable strings from HTML content to POT file.

    Args:
        html_content: HTML bytes to extract from
        output_path: Path to write POT file to
        source_name: Neutral name used as msgctxt source (no path info)

    Returns:
        Path: Path to generated POT file
    """
    logger.debug(f"Extracting translatable strings to {output_path}")

    # Strip id attributes so element IDs (used for TOC anchors) don't become
    # msgctxt values, which would prevent duplicate strings from being merged.
    stripped = re.sub(rb'\s+id="[^"]*"', b"", html_content)

    html_buf = BytesIO(stripped)
    html_buf.name = source_name

    with output_path.open("wb") as pot_file:
        html2po.converthtml(html_buf, pot_file, None, pot=True, duplicatestyle="merge")

    clean_po_file(output_path)

    logger.debug(f"Extracted to POT: {output_path}")
    return output_path


def apply_po_to_html(
    html_input_path: Path, po_path: Path, html_output_path: Path
) -> Path:
    """
    Apply PO file translations to HTML file.

    Args:
        html_input_path: Path to HTML file to translate
        po_path: Path to PO file with translations
        html_output_path: Path to write translated HTML file

    Returns:
        Path: Path to translated HTML file (same as html_output_path)
    """
    logger.debug(f"Applying translations from {po_path}")

    if not po_path.exists():
        raise FileNotFoundError(f"PO file not found: {po_path}")

    if not html_input_path.exists():  # pragma: no cover
        raise FileNotFoundError(f"HTML input file not found: {html_input_path}")

    # Convert PO to HTML using file objects
    with (
        po_path.open("rb") as po_file,
        html_input_path.open("rb") as html_file,
        html_output_path.open("wb") as out_file,
    ):
        po2html.converthtml(po_file, out_file, html_file)

    logger.debug(f"Applied translations from {po_path}")
    return html_output_path


def get_po_stats(po_path: Path) -> dict[str, int]:
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
    store = po.pofile.parsefile(str(po_path))
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


def check_po_sync(pot_path: Path, po_path: Path) -> bool:
    """
    Check if PO file msgids match current POT.

    Args:
        pot_path: Path to POT template file
        po_path: Path to PO translation file

    Returns:
        bool: True if in sync, False if out of sync
    """
    pot_store = po.pofile.parsefile(str(pot_path))
    po_store = po.pofile.parsefile(str(po_path))

    pot_msgids = {u.source for u in pot_store.units if u.istranslatable()}
    po_msgids = {u.source for u in po_store.units if u.istranslatable()}

    return pot_msgids == po_msgids


def merge_po_files(po_paths: list[Path], output_path: Path) -> None:
    """
    Merge multiple PO files into one, with later files winning on conflict.

    Loads each PO file in order; entries from later files overwrite earlier ones
    (document-level PO wins over library PO).

    Args:
        po_paths: PO files to merge, in priority order (lowest first)
        output_path: Path to write the merged PO file
    """
    merged = polib.POFile()
    merged.metadata = {"Content-Type": "text/plain; charset=UTF-8"}

    entries: dict[str, polib.POEntry] = {}
    for path in po_paths:
        pf = polib.pofile(str(path))
        for entry in pf.translated_entries():
            entries[entry.msgid] = entry

    for entry in entries.values():
        merged.append(entry)

    merged.save(str(output_path))


def update_po_files(pot_path: Path, po_files: list[Path]) -> None:
    """
    Update existing PO files with new/changed strings from POT file.

    Uses pot2po to merge updates while preserving existing translations.

    Args:
        pot_path: Path to POT template file
        po_files: PO files to update
    """
    if not po_files:
        logger.debug("No existing PO files to update")
        return

    for po_file in sorted(po_files):
        lang = po_file.name
        logger.debug(f"Updating {lang} with new POT...")

        # Create temporary file for merged PO
        temp_po = po_file.with_suffix(po_file.suffix + ".new")

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
                if temp_po.exists():
                    temp_po.unlink()
                continue

            # Replace old PO with merged version
            shutil.move(temp_po, po_file)

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
            if Path(temp_po).exists():
                Path(temp_po).unlink()
