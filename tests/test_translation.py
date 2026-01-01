"""Tests for POT/PO translation functionality (HTML-based)."""

import os
import tempfile

import pytest

from docco.core import markdown_to_html
from docco.translation import (
    apply_po_to_html,
    check_po_sync,
    extract_html_to_pot,
    get_po_stats,
    update_po_files,
)


def test_extract_html_to_pot_creates_file():
    """Test that extract_html_to_pot creates a POT file from HTML."""
    md_content = "# Title\n\nThis is a paragraph."
    html_content = markdown_to_html(md_content)

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pot_path = os.path.join(tmpdir, "test.pot")
        result = extract_html_to_pot(html_path, pot_path)

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
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pot_path = os.path.join(tmpdir, "test.pot")
        extract_html_to_pot(html_path, pot_path)

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
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pot_path = os.path.join(tmpdir, "test.pot")
        extract_html_to_pot(html_path, pot_path)

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
        html_input_path = os.path.join(tmpdir, "input.html")
        html_output_path = os.path.join(tmpdir, "output.html")
        po_path = os.path.join(tmpdir, "test.po")

        with open(html_input_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        with open(po_path, "w") as f:
            f.write("""# German Translation
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"
""")

        # Apply translations
        result_path = apply_po_to_html(html_input_path, po_path, html_output_path)

        assert result_path == html_output_path
        assert os.path.exists(result_path)

        # Read result and verify translations
        with open(result_path, "r", encoding="utf-8") as f:
            result = f.read()

        assert "Hallo" in result
        assert "Welt" in result


def test_apply_po_to_html_file_not_found():
    """Test that apply_po_to_html raises error when PO file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        html_input_path = os.path.join(tmpdir, "input.html")
        html_output_path = os.path.join(tmpdir, "output.html")

        with open(html_input_path, "w", encoding="utf-8") as f:
            f.write("<h1>Title</h1>")

        with pytest.raises(FileNotFoundError):
            apply_po_to_html(html_input_path, "/nonexistent/path.po", html_output_path)


def test_extract_roundtrip():
    """Test that extract_html_to_pot and apply_po_to_html can roundtrip content."""
    original_md = "# Document\n\nSome content here.\n\n## Section\n\nMore content."
    html_content = markdown_to_html(original_md)

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "test.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        pot_path = os.path.join(tmpdir, "test.pot")

        # Extract
        extract_html_to_pot(html_path, pot_path)

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
        html_input_path = os.path.join(tmpdir, "input.html")
        html_output_path = os.path.join(tmpdir, "output.html")
        po_path = os.path.join(tmpdir, "test.po")

        with open(html_input_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        with open(po_path, "w") as f:
            # PO file with no translations (empty msgstr)
            f.write("""
msgid "Hello"
msgstr ""

msgid "World"
msgstr ""
""")

        # Apply translations (should fall back to original)
        result_path = apply_po_to_html(html_input_path, po_path, html_output_path)

        # Read result
        with open(result_path, "r", encoding="utf-8") as f:
            result = f.read()

        # Result should contain original text when translation is empty
        assert "Hello" in result
        assert "World" in result


def test_get_po_stats_all_translated():
    """Test get_po_stats with fully translated PO file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w", encoding="utf-8") as f:
            f.write("""# German Translation
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"

msgid "Test"
msgstr "Prüfung"
""")

        stats = get_po_stats(po_path)
        assert stats["total"] == 3
        assert stats["translated"] == 3
        assert stats["fuzzy"] == 0
        assert stats["untranslated"] == 0


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
        assert stats["total"] == 3
        assert stats["translated"] == 1
        assert stats["fuzzy"] == 0
        assert stats["untranslated"] == 2


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
        assert stats["total"] == 3
        assert stats["translated"] == 1
        assert stats["fuzzy"] == 1
        assert stats["untranslated"] == 1


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
        assert stats["total"] == 0
        assert stats["translated"] == 0
        assert stats["fuzzy"] == 0
        assert stats["untranslated"] == 0


def test_update_po_files_no_existing_po():
    """Test update_po_files with no existing PO files (should not crash)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        with open(pot_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr ""
"""
            )

        # Call update_po_files with empty directory - should not raise an error
        update_po_files(pot_path, tmpdir)


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
        assert orig_stats["translated"] == 2

        # Update with same POT (should preserve translations)
        update_po_files(pot_path, tmpdir)

        # Stats should be unchanged
        updated_stats = get_po_stats(po_path)
        assert updated_stats["translated"] == 2
        assert updated_stats["untranslated"] == 0


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
        assert orig_stats["translated"] == 2
        assert orig_stats["untranslated"] == 0

        # Update with new POT containing extra string
        update_po_files(pot_path, tmpdir)

        # Stats should reflect new untranslated string
        updated_stats = get_po_stats(po_path)
        assert updated_stats["total"] == 3
        assert updated_stats["translated"] == 2  # Preserved
        assert updated_stats["untranslated"] == 1  # New string


def test_check_po_sync_in_sync():
    """Test check_po_sync returns True when POT and PO match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        po_path = os.path.join(tmpdir, "test.po")

        # Create POT
        with open(pot_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr ""

msgid "World"
msgstr ""
"""
            )

        # Create PO with same strings
        with open(po_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"
"""
            )

        # Should be in sync
        assert check_po_sync(pot_path, po_path) is True


def test_check_po_sync_out_of_sync_new_string():
    """Test check_po_sync returns False when POT has new string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        po_path = os.path.join(tmpdir, "test.po")

        # Create POT with 3 strings
        with open(pot_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr ""

msgid "World"
msgstr ""

msgid "New"
msgstr ""
"""
            )

        # Create PO with only 2 strings
        with open(po_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr "Hallo"

msgid "World"
msgstr "Welt"
"""
            )

        # Should be out of sync
        assert check_po_sync(pot_path, po_path) is False


def test_check_po_sync_out_of_sync_removed_string():
    """Test check_po_sync returns False when string is removed from POT."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        po_path = os.path.join(tmpdir, "test.po")

        # Create POT with 1 string
        with open(pot_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr ""
"""
            )

        # Create PO with 2 strings
        with open(po_path, "w") as f:
            f.write(
                """
msgid "Hello"
msgstr "Hallo"

msgid "Removed"
msgstr "Entfernt"
"""
            )

        # Should be out of sync
        assert check_po_sync(pot_path, po_path) is False


def test_check_po_sync_out_of_sync_changed_string():
    """Test check_po_sync returns False when string content changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        po_path = os.path.join(tmpdir, "test.po")

        # Create POT with modified string
        with open(pot_path, "w") as f:
            f.write(
                """
msgid "Hello World"
msgstr ""

msgid "Test"
msgstr ""
"""
            )

        # Create PO with original string (before change)
        with open(po_path, "w", encoding="utf-8") as f:
            f.write(
                """
msgid "Hello"
msgstr "Hallo"

msgid "Test"
msgstr "Prüfung"
"""
            )

        # Should be out of sync (different strings)
        assert check_po_sync(pot_path, po_path) is False
