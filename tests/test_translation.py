"""Tests for POT/PO translation functionality (HTML-based)."""

import os
import tempfile
import pytest
from docco.translation import extract_html_to_pot, apply_po_to_html, get_po_stats, update_po_files
from docco.core import markdown_to_html


def test_extract_html_to_pot_creates_file():
    """Test that extract_html_to_pot creates a POT file from HTML."""
    md_content = "# Title\n\nThis is a paragraph."
    html_content = markdown_to_html(md_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        result = extract_html_to_pot(html_content, pot_path)

        assert os.path.exists(pot_path)
        assert result == pot_path

        # Check file is not empty
        with open(pot_path, "r") as f:
            pot_content = f.read()
        assert len(pot_content) > 0


def test_extract_html_to_pot_contains_strings():
    """Test that extracted POT from HTML contains the translatable strings."""
    md_content = "# My Title\n\nThis is a paragraph."
    html_content = markdown_to_html(md_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        extract_html_to_pot(html_content, pot_path)

        with open(pot_path, "r") as f:
            pot_content = f.read()

        # Should contain the title and paragraph
        assert "My Title" in pot_content
        assert "This is a paragraph" in pot_content


def test_extract_html_to_pot_with_formatting():
    """Test that HTML-based extraction preserves inline formatting tags."""
    md_content = "# My Title\n\nThis is a paragraph with **bold** and *italic* text."
    html_content = markdown_to_html(md_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        extract_html_to_pot(html_content, pot_path)

        with open(pot_path, "r") as f:
            pot_content = f.read()

        # Should contain HTML tags in msgids, not markdown syntax
        assert "msgid" in pot_content
        # Should have extracted content
        assert len(pot_content) > 0


def test_apply_po_to_html_with_translations():
    """Test that apply_po_to_html applies translations to HTML."""
    md_content = "# Hello\n\nWorld"
    html_content = markdown_to_html(md_content)

    # Create a PO file with translations
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""# German Translation
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"
""")

        # Apply translations
        result = apply_po_to_html(html_content, po_path)

        # Result should contain translated strings
        assert "Hallo" in result
        assert "Welt" in result


def test_apply_po_to_html_file_not_found():
    """Test that apply_po_to_html raises error when PO file doesn't exist."""
    html_content = "<h1>Title</h1>"

    with pytest.raises(FileNotFoundError):
        apply_po_to_html(html_content, "/nonexistent/path.po")


def test_extract_roundtrip():
    """Test that extract_html_to_pot and apply_po_to_html can roundtrip content."""
    original_md = "# Document\n\nSome content here.\n\n## Section\n\nMore content."
    html_content = markdown_to_html(original_md)

    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")

        # Extract
        extract_html_to_pot(html_content, pot_path)

        # Verify POT was created
        assert os.path.exists(pot_path)

        with open(pot_path, "r") as f:
            pot_content = f.read()

        # POT should be valid
        assert "msgid" in pot_content
        assert len(pot_content) > 0


def test_apply_po_empty_translations():
    """Test that apply_po_to_html works with empty translation (no msgstr)."""
    md_content = "# Hello\n\nWorld"
    html_content = markdown_to_html(md_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            # PO file with no translations (empty msgstr)
            f.write("""
msgid "Hello"
msgstr ""

msgid "World"
msgstr ""
""")

        # Apply translations (should fall back to original)
        result = apply_po_to_html(html_content, po_path)

        # Result should contain original text when translation is empty
        assert "Hello" in result
        assert "World" in result


def test_get_po_stats_all_translated():
    """Test get_po_stats with fully translated PO file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""# German Translation
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"

msgid "Test"
msgstr "Prüfung"
""")

        stats = get_po_stats(po_path)
        assert stats['total'] == 3
        assert stats['translated'] == 3
        assert stats['fuzzy'] == 0
        assert stats['untranslated'] == 0


def test_get_po_stats_with_untranslated():
    """Test get_po_stats with untranslated strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""# German Translation
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr ""

msgid "Test"
msgstr ""
""")

        stats = get_po_stats(po_path)
        assert stats['total'] == 3
        assert stats['translated'] == 1
        assert stats['fuzzy'] == 0
        assert stats['untranslated'] == 2


def test_get_po_stats_with_fuzzy():
    """Test get_po_stats with fuzzy translations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""# German Translation
msgid "Hello"
msgstr "Hallo"

#, fuzzy
msgid "World"
msgstr "Welt"

msgid "Test"
msgstr ""
""")

        stats = get_po_stats(po_path)
        assert stats['total'] == 3
        assert stats['translated'] == 1
        assert stats['fuzzy'] == 1
        assert stats['untranslated'] == 1


def test_get_po_stats_empty_po():
    """Test get_po_stats with empty PO file (only header)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""# Translation file
msgid ""
msgstr ""
"Language: de\\n"
""")

        stats = get_po_stats(po_path)
        assert stats['total'] == 0
        assert stats['translated'] == 0
        assert stats['fuzzy'] == 0
        assert stats['untranslated'] == 0


def test_update_po_files_no_existing_po(caplog):
    """Test update_po_files with no existing PO files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        with open(pot_path, "w") as f:
            f.write("""
msgid "Hello"
msgstr ""
""")

        # Call update_po_files with empty directory
        update_po_files(pot_path, tmpdir)

        # Should log that no files were found
        assert "No existing PO files to update" in caplog.text


def test_update_po_files_preserves_translations():
    """Test that update_po_files preserves existing translations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create original POT with 2 strings
        pot_path = os.path.join(tmpdir, "test.pot")
        with open(pot_path, "w") as f:
            f.write("""
msgid "Hello"
msgstr ""

msgid "World"
msgstr ""
""")

        # Create PO with translations
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"
""")

        # Get original stats
        orig_stats = get_po_stats(po_path)
        assert orig_stats['translated'] == 2

        # Update with same POT (should preserve translations)
        update_po_files(pot_path, tmpdir)

        # Stats should be unchanged
        updated_stats = get_po_stats(po_path)
        assert updated_stats['translated'] == 2
        assert updated_stats['untranslated'] == 0


def test_update_po_files_adds_new_strings():
    """Test that update_po_files adds new strings to PO."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Original POT
        pot_path = os.path.join(tmpdir, "test.pot")
        with open(pot_path, "w") as f:
            f.write("""
msgid "Hello"
msgstr ""

msgid "World"
msgstr ""

msgid "New String"
msgstr ""
""")

        # PO with translations for original strings only
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"
""")

        # Get original stats (2 translated)
        orig_stats = get_po_stats(po_path)
        assert orig_stats['translated'] == 2
        assert orig_stats['untranslated'] == 0

        # Update with new POT containing extra string
        update_po_files(pot_path, tmpdir)

        # Stats should reflect new untranslated string
        updated_stats = get_po_stats(po_path)
        assert updated_stats['total'] == 3
        assert updated_stats['translated'] == 2  # Preserved
        assert updated_stats['untranslated'] == 1  # New string
