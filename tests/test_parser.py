"""Integration tests for the parser module."""

import os
import tempfile
import pytest
from docco.parser import parse_markdown, process_directives_iteratively, MAX_ITERATIONS


@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


def test_end_to_end_simple(fixture_dir):
    """Test simple markdown parsing and PDF output."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert outputs[0].endswith(".pdf")
        assert os.path.exists(outputs[0])


def test_end_to_end_with_frontmatter(fixture_dir):
    """Test parsing with frontmatter."""
    input_file = os.path.join(fixture_dir, "with_frontmatter.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert outputs[0].endswith(".pdf")
        assert os.path.exists(outputs[0])


def test_end_to_end_with_inline(fixture_dir):
    """Test parsing with inline directives."""
    # Create a temp file with inline
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "with_inline.md")
        # Copy inline target to tmpdir so it's relative to the markdown file
        inline_target = os.path.join(tmpdir, "inline_target.md")
        with open(inline_target, "w") as f:
            f.write("Inlined: {{name}}")

        with open(input_file, "w") as f:
            f.write("""# Document

Before

<!-- inline:"inline_target.md" name="Test" -->

After""")

        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert outputs[0].endswith(".pdf")
        assert os.path.exists(outputs[0])




def test_output_file_naming_simple(fixture_dir):
    """Test that output files are named correctly for simple docs."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs = parse_markdown(input_file, tmpdir)
        basename = os.path.basename(outputs[0])
        assert basename == "simple.pdf"


def test_keep_intermediate_false(fixture_dir):
    """Test that intermediate files are removed by default."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        parse_markdown(input_file, tmpdir, keep_intermediate=False)
        # Should only have PDF files
        all_files = os.listdir(tmpdir)
        assert any(f.endswith(".pdf") for f in all_files)
        assert not any(f.endswith("_intermediate.md") for f in all_files)
        assert not any(f.endswith(".html") for f in all_files)


def test_keep_intermediate_true(fixture_dir):
    """Test that intermediate files are kept when flag is True."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        parse_markdown(input_file, tmpdir, keep_intermediate=True)
        all_files = os.listdir(tmpdir)
        # Should have PDF, HTML, and intermediate MD files
        assert any(f.endswith(".pdf") for f in all_files)
        assert any(f.endswith("_intermediate.md") for f in all_files)
        assert any(f.endswith(".html") for f in all_files)


def test_max_iterations_exceeded_self_referencing():
    """Test that ValueError is raised when inline creates infinite recursion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a markdown file that references itself
        self_ref_file = os.path.join(tmpdir, "self_ref.md")
        with open(self_ref_file, "w") as f:
            f.write("# Self Reference\n<!-- inline:\"self_ref.md\" -->")

        # Create content that inlines the self-referencing file
        content = "# Main\n<!-- inline:\"self_ref.md\" -->"

        with pytest.raises(ValueError, match=f"Max iterations \\({MAX_ITERATIONS}\\) exceeded"):
            process_directives_iteratively(content, tmpdir, False)


def test_multilingual_build_logs_translation_warnings(caplog):
    """Test that incomplete translations trigger warnings in multilingual mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create markdown file with multilingual frontmatter
        input_file = os.path.join(tmpdir, "test.md")
        with open(input_file, "w") as f:
            f.write("""---
multilingual: true
base_language: en
---

# Hello

This is a test document.
""")

        # Create translations directory and incomplete PO file
        translations_dir = os.path.join(tmpdir, "test")
        os.makedirs(translations_dir, exist_ok=True)

        # Create PO file with incomplete translation (fuzzy and untranslated)
        de_po = os.path.join(translations_dir, "de.po")
        with open(de_po, "w") as f:
            f.write("""
msgid "Hello"
msgstr "Hallo"

#, fuzzy
msgid "This is a test document."
msgstr "Dies ist ein Testdokument."

msgid "New string not yet translated"
msgstr ""
""")

        # Build multilingual PDF
        outputs = parse_markdown(input_file, tmpdir)

        # Should generate PDFs for EN and DE
        assert len(outputs) == 2

        # Should have logged warning about incomplete translation
        assert "Translation incomplete for DE" in caplog.text
        assert "1 untranslated" in caplog.text
        assert "1 fuzzy" in caplog.text
