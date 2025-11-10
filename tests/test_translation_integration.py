"""Integration tests for POT/PO translation workflow (HTML-based)."""

import hashlib
import os
import tempfile
import pytest
from docco.parser import parse_markdown
from docco.translation import extract_html_to_pot
from docco.core import parse_frontmatter, markdown_to_html


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
    output_dir = os.path.join(
        os.path.dirname(__file__),
        "output"
    )
    os.makedirs(output_dir, exist_ok=True)
    return {
        "source": os.path.join(examples_dir, "Multilingual_Document_Example.md"),
        "de_po": os.path.join(examples_dir, "Multilingual_Document_Example", "de.po"),
        "nl_po": os.path.join(examples_dir, "Multilingual_Document_Example", "nl.po"),
        "pot": os.path.join(output_dir, "Multilingual_Document_Example.pot"),
    }


@pytest.fixture
def baselines_dir():
    """Path to baseline PDFs directory."""
    return os.path.join(
        os.path.dirname(__file__),
        "baselines"
    )


def test_extract_pot_file_from_html(translation_files):
    """Test that POT file can be extracted from HTML generated from markdown."""
    # Read source markdown
    with open(translation_files["source"], "r") as f:
        content = f.read()

    # Parse frontmatter and convert to HTML
    _, body = parse_frontmatter(content)
    html_content = markdown_to_html(body)

    # Extract POT from HTML
    pot_path = translation_files["pot"]
    result = extract_html_to_pot(html_content, pot_path)

    # Verify POT file was created
    assert os.path.exists(result)
    assert result == pot_path

    # Verify POT file has content
    with open(pot_path, "r") as f:
        pot_content = f.read()

    assert "msgid" in pot_content
    assert "Hello World" in pot_content
    assert len(pot_content) > 0


def test_translation_workflow_all_languages(translation_files, baselines_dir):
    """Test complete multilingual translation workflow.

    This test covers:
    - Multilingual mode activation via frontmatter flag
    - base_language requirement in frontmatter
    - POT extraction from HTML (generated from processed markdown)
    - Automatic PDF generation for base language (en) + all available translations (de, nl)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # With multilingual: true and base_language in frontmatter, parse_markdown generates all language PDFs
        output_files = parse_markdown(
            translation_files["source"],
            tmpdir,
            allow_python=True,
            keep_intermediate=False
        )

        # Should generate 3 PDFs (en base language + de and nl from available .po files)
        assert len(output_files) == 3, f"Expected 3 PDFs for multilingual mode, got {len(output_files)}"

        # Verify each PDF was created with uppercase language codes
        # Output order: base language first (EN), then .po files in sorted order (DE, NL)
        expected_langs = ["EN", "DE", "NL"]
        for pdf_file, lang_code in zip(output_files, expected_langs):
            assert os.path.exists(pdf_file), f"PDF not created for language {lang_code}"
            assert pdf_file.endswith(f"_{lang_code}.pdf"), \
                f"PDF filename should have language suffix: {pdf_file}"


def test_single_language_mode_with_po_file():
    """Test single-language mode with explicit po_file parameter.

    This tests the po_file parameter when multilingual: false (or not set).
    """
    # Create a simple markdown without multilingual flag
    md_content = """---
title: Test
---
# Test

Hello world"""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, "test.md")
        with open(md_path, "w") as f:
            f.write(md_content)

        # Create a simple PO file with HTML-style msgids
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""
msgid "Test"
msgstr "Prueba"

msgid "Hello world"
msgstr "Hola mundo"
""")

        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)

        # Generate PDF with po_file parameter
        output_files = parse_markdown(
            md_path,
            output_dir,
            po_file=po_path,
            allow_python=False
        )

        # Should generate 1 PDF with no language suffix
        assert len(output_files) == 1
        assert os.path.exists(output_files[0])
        assert "test.pdf" in output_files[0]
        assert "_" not in os.path.basename(output_files[0])  # No language suffix


def test_multilingual_without_base_language():
    """Test that multilingual mode fails without base_language in frontmatter."""
    # Create a markdown file with multilingual: true but no base_language
    md_content = """---
multilingual: true
---
# Test

Hello world"""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, "test.md")
        with open(md_path, "w") as f:
            f.write(md_content)

        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)

        # Should raise ValueError because base_language is missing
        with pytest.raises(ValueError) as exc_info:
            parse_markdown(
                md_path,
                output_dir,
                allow_python=False
            )

        assert "base_language" in str(exc_info.value)


def test_multilingual_without_translations():
    """Test that multilingual mode generates base language PDF even without .po files."""
    # Create a markdown file with multilingual: true and base_language, but no .po files
    md_content = """---
multilingual: true
base_language: en
---
# Test

Hello world"""

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, "test.md")
        with open(md_path, "w") as f:
            f.write(md_content)

        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)

        # Should generate PDF for base language even without translations
        output_files = parse_markdown(
            md_path,
            output_dir,
            allow_python=False
        )

        # Should have 1 PDF for base language
        assert len(output_files) == 1
        assert os.path.exists(output_files[0])
        assert "_EN.pdf" in output_files[0]
