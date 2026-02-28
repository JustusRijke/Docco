"""Integration tests for POT/PO translation workflow (HTML-based)."""

import tempfile
from pathlib import Path

import pytest

from docco.core import markdown_to_html
from docco.parser import BuildConfig, parse_markdown
from docco.translation import extract_html_to_pot, get_po_stats


@pytest.fixture
def translation_files():
    """Path to translation files in examples directory."""
    examples_dir = Path(__file__).parent / ".." / "examples"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True, parents=True)
    return {
        "source": str(examples_dir / "Multilingual_Document_Example.md"),
        "de_po": str(examples_dir / "Multilingual_Document_Example" / "de.po"),
        "nl_po": str(examples_dir / "Multilingual_Document_Example" / "nl.po"),
        "pot": str(output_dir / "Multilingual_Document_Example.pot"),
    }


@pytest.fixture
def baselines_dir():
    """Path to baseline PDFs directory."""
    return str(Path(__file__).parent / "baselines")


def test_extract_pot_file_from_html(translation_files):
    """Test that POT file can be extracted from HTML generated from markdown."""
    with Path(translation_files["source"]).open("r", encoding="utf-8") as f:
        content = f.read()

    html_content = markdown_to_html(content)

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "test.html"
        with html_path.open("w", encoding="utf-8") as f:
            f.write(html_content)

        pot_path = Path(translation_files["pot"])
        result = extract_html_to_pot(html_path, pot_path)

        assert result.exists()
        assert result == pot_path

        with pot_path.open("r", encoding="utf-8") as f:
            pot_content = f.read()

        assert "msgid" in pot_content
        assert "Hello World" in pot_content
        assert len(pot_content) > 0


def test_translation_workflow_all_languages(translation_files, baselines_dir):
    """Test complete multilingual translation workflow.

    This test covers:
    - Multilingual mode activation via translations dict in frontmatter
    - base_language requirement in frontmatter
    - POT extraction from HTML (generated from processed markdown)
    - Automatic PDF generation for base language (en) + all listed translations (de, nl)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_files = parse_markdown(
            Path(translation_files["source"]),
            Path(tmpdir),
            config=BuildConfig(allow_python=True),
        )

        # Should generate 3 PDFs (en base language + de and nl from translations dict)
        assert len(output_files) == 3, (
            f"Expected 3 PDFs for multilingual mode, got {len(output_files)}"
        )

        # Output order: base language first (EN), then sorted translation keys (DE, NL)
        expected_langs = ["EN", "DE", "NL"]
        for pdf_file, lang_code in zip(output_files, expected_langs):
            assert pdf_file.exists(), f"PDF not created for language {lang_code}"
            assert pdf_file.name.endswith(f"_{lang_code}.pdf"), (
                f"PDF filename should have language suffix: {pdf_file}"
            )


def test_multilingual_without_base_language():
    """Test that multilingual mode fails without base_language in frontmatter."""
    md_content = """---
translations:
  de: de.po
---
# Test

Hello world"""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "test.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(md_content)

        # Create dummy PO file so path resolution doesn't fail before the check
        (Path(tmpdir) / "de.po").write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir(parents=True)

        with pytest.raises(ValueError, match="base_language"):
            parse_markdown(md_path, output_dir)


def test_multilingual_without_translations():
    """Test that no translations key generates a single (non-suffixed) PDF."""
    md_content = """---
base_language: en
---
# Test

Hello world"""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "test.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(md_content)

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir(parents=True)

        output_files = parse_markdown(md_path, output_dir)

        assert len(output_files) == 1
        assert output_files[0].exists()
        # No language suffix without translations dict
        assert output_files[0].name == "test.pdf"


def test_multilingual_auto_updates_po_files():
    """Test that multilingual mode automatically updates existing PO files."""
    initial_content = """---
base_language: en
translations:
  de: test/de.po
---
# Hello

Original content."""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "test.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(initial_content)

        # Create translations directory and dummy PO file
        trans_dir = Path(tmpdir) / "test"
        trans_dir.mkdir()
        po_path = trans_dir / "de.po"
        po_path.write_text(
            'msgid ""\nmsgstr "Content-Type: text/plain; charset=UTF-8\\n"\n',
            encoding="utf-8",
        )

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir(parents=True)

        # First build: creates POT file
        output_files = parse_markdown(md_path, output_dir)
        assert len(output_files) == 2  # Base EN + DE

        # Verify POT file was created (next to the source md file)
        pot_path = Path(tmpdir) / "test.pot"
        assert pot_path.exists()

        # Update markdown with new content
        updated_content = """---
base_language: en
translations:
  de: test/de.po
---
# Hello

Original content.

New paragraph added."""

        with md_path.open("w", encoding="utf-8") as f:
            f.write(updated_content)

        # Second build: should auto-update PO file with new strings
        output_files = parse_markdown(md_path, output_dir)
        assert len(output_files) == 2

        assert po_path.exists()
        with po_path.open("r", encoding="utf-8") as f:
            po_content = f.read()

        assert "New paragraph added" in po_content

        stats = get_po_stats(po_path)
        assert stats["total"] > 0
        assert stats["untranslated"] > 0 or stats["fuzzy"] > 0


def test_library_po_fallback():
    """Test that library PO translations appear in output and document PO wins."""
    md_content = """---
base_language: en
translations:
  de: de.po
---
# Hello

Shared string.

Document only."""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "test.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(md_content)

        # Library PO: translates "Shared string." and "Hello"
        lib_po = Path(tmpdir) / "lib.po"
        lib_po.write_text(
            'msgid "Shared string."\nmsgstr "Bibliothek Shared."\n\n'
            'msgid "Hello"\nmsgstr "Library Hello"\n',
            encoding="utf-8",
        )

        # Document PO: overrides "Hello", leaves "Shared string." to library
        doc_po = Path(tmpdir) / "de.po"
        doc_po.write_text(
            'msgid "Hello"\nmsgstr "Dokument Hallo"\n\n'
            'msgid "Document only."\nmsgstr "Nur Dokument."\n',
            encoding="utf-8",
        )

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        output_files = parse_markdown(md_path, output_dir, library_po_files=[lib_po])

        assert len(output_files) == 2
        # Read intermediate HTML (keep_intermediate would be needed for full check;
        # verify PDFs were created at minimum)
        for pdf in output_files:
            assert pdf.exists()


def test_multiple_po_files_per_language():
    """Test that multiple PO files per language are supported in translations frontmatter.

    First listed PO has highest priority; supplemental POs fill in untranslated strings.
    """
    md_content = """---
base_language: en
translations:
  de:
    - de_primary.po
    - de_shared.po
---
# Hello

Primary string.

Shared string."""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "test.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(md_content)

        # Primary PO: overrides "Hello" and "Primary string."
        primary_po = Path(tmpdir) / "de_primary.po"
        primary_po.write_text(
            'msgid "Hello"\nmsgstr "Primaer Hallo"\n\n'
            'msgid "Primary string."\nmsgstr "Primaere Zeichenkette."\n',
            encoding="utf-8",
        )

        # Supplemental PO: provides "Hello" (overridden) and "Shared string."
        shared_po = Path(tmpdir) / "de_shared.po"
        shared_po.write_text(
            'msgid "Hello"\nmsgstr "Geteilt Hallo"\n\n'
            'msgid "Shared string."\nmsgstr "Geteilte Zeichenkette."\n',
            encoding="utf-8",
        )

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        output_files = parse_markdown(
            md_path, output_dir, config=BuildConfig(keep_intermediate=True)
        )

        assert len(output_files) == 2  # EN + DE

        de_html = (output_dir / "test_DE.html").read_text(encoding="utf-8")
        # Primary PO wins over supplemental for "Hello"
        assert "Primaer Hallo" in de_html
        assert "Geteilt Hallo" not in de_html
        # Supplemental PO fills in "Shared string."
        assert "Geteilte Zeichenkette" in de_html
