"""Integration tests for POT/PO translation workflow."""

import hashlib
import os
import tempfile
import pytest
from docco.parser import parse_markdown
from docco.translation import extract_to_pot


def get_file_checksum(filepath):
    """Calculate MD5 checksum of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


@pytest.fixture
def translation_files():
    """Path to translation files in examples directory."""
    examples_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "examples"
    )
    return {
        "source": os.path.join(examples_dir, "Multilingual_Document_Example.md"),
        "de_po": os.path.join(examples_dir, "translations", "de.po"),
        "nl_po": os.path.join(examples_dir, "translations", "nl.po"),
    }


@pytest.fixture
def baselines_dir():
    """Path to baseline PDFs directory."""
    return os.path.join(
        os.path.dirname(__file__),
        "baselines"
    )


def test_extract_pot_file(translation_files):
    """Test that POT file can be extracted from source markdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Read source markdown
        with open(translation_files["source"], "r") as f:
            content = f.read()

        # Extract to POT
        pot_path = os.path.join(tmpdir, "test.pot")
        result = extract_to_pot(content, pot_path)

        # Verify POT file was created
        assert os.path.exists(result)
        assert result == pot_path

        # Verify POT file has content
        with open(pot_path, "r") as f:
            pot_content = f.read()

        assert "msgid" in pot_content
        assert "Document Example" in pot_content
        assert len(pot_content) > 100


def test_translation_workflow_all_languages(translation_files, baselines_dir):
    """Test complete translation workflow: extract POT and build all language PDFs.

    This test covers:
    - POT extraction from source markdown
    - PDF generation for English (source)
    - PDF generation with German translation
    - PDF generation with Dutch translation
    - Baseline validation for all languages
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Extract POT from source
        with open(translation_files["source"], "r") as f:
            source_content = f.read()

        pot_path = os.path.join(tmpdir, "document.pot")
        extract_to_pot(source_content, pot_path)

        assert os.path.exists(pot_path), "POT file not created"

        # Step 2: Generate PDFs for all languages
        languages = {
            "EN": None,  # No PO file for source language
            "DE": translation_files["de_po"],
            "NL": translation_files["nl_po"],
        }

        for lang_code, po_file in languages.items():
            output_files = parse_markdown(
                translation_files["source"],
                tmpdir,
                po_file=po_file,
                allow_python=True,
                keep_intermediate=False
            )

            assert len(output_files) == 1, f"Expected 1 PDF for {lang_code}"

            pdf_file = output_files[0]
            baseline_pdf = os.path.join(
                baselines_dir,
                f"Multilingual_Document_Example_{lang_code}.pdf"
            )

            assert os.path.exists(baseline_pdf), \
                f"Baseline missing for {lang_code}: {baseline_pdf}"

            actual_checksum = get_file_checksum(pdf_file)
            baseline_checksum = get_file_checksum(baseline_pdf)

            assert actual_checksum == baseline_checksum, \
                f"{lang_code} PDF mismatch"


def test_po_file_missing(translation_files):
    """Test that missing PO file raises appropriate error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_po = os.path.join(tmpdir, "nonexistent.po")

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            parse_markdown(
                translation_files["source"],
                tmpdir,
                po_file=missing_po,
                allow_python=True
            )
