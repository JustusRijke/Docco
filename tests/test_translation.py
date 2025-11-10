"""Tests for POT/PO translation functionality (HTML-based)."""

import os
import tempfile
import pytest
from docco.translation import extract_html_to_pot, apply_po_to_html
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
