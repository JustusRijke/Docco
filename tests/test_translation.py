"""Tests for POT/PO translation functionality."""

import os
import tempfile
import pytest
from docco.translation import extract_to_pot, build_from_po


def test_extract_to_pot_creates_file():
    """Test that extract_to_pot creates a POT file."""
    content = "# Title\n\nThis is a paragraph."
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        result = extract_to_pot(content, pot_path)

        assert os.path.exists(pot_path)
        assert result == pot_path

        # Check file is not empty
        with open(pot_path, "r") as f:
            pot_content = f.read()
        assert len(pot_content) > 0


def test_extract_to_pot_contains_strings():
    """Test that extracted POT contains the translatable strings."""
    content = "# My Title\n\nThis is a paragraph."
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        extract_to_pot(content, pot_path)

        with open(pot_path, "r") as f:
            pot_content = f.read()

        # Should contain the title and paragraph
        assert "My Title" in pot_content
        assert "This is a paragraph" in pot_content


def test_extract_to_pot_strips_frontmatter():
    """Test that frontmatter is not included in POT extraction."""
    content = """---
title: Document Title
author: John Doe
---
# My Title

This is a paragraph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")
        extract_to_pot(content, pot_path)

        with open(pot_path, "r") as f:
            pot_content = f.read()

        # Should contain body content
        assert "My Title" in pot_content
        assert "This is a paragraph" in pot_content
        # Should NOT contain frontmatter
        assert "Document Title" not in pot_content
        assert "John Doe" not in pot_content


def test_build_from_po_with_translations():
    """Test that build_from_po applies translations to markdown."""
    # Create a simple markdown
    md_content = "# Hello\n\nWorld"

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
        result = build_from_po(md_content, po_path)

        # Result should contain translated strings
        assert "Hallo" in result


def test_build_from_po_with_frontmatter():
    """Test that build_from_po handles content with frontmatter (strips it)."""
    # Create markdown with frontmatter
    md_content = """---
title: Document Title
author: John Doe
---
# Hello

World"""

    # Create a PO file with translations
    with tempfile.TemporaryDirectory() as tmpdir:
        po_path = os.path.join(tmpdir, "test.po")
        with open(po_path, "w") as f:
            f.write("""msgid "Hello"
msgstr "Hola"

msgid "World"
msgstr "Mundo"
""")

        # Apply translations (content includes frontmatter, which gets stripped)
        result = build_from_po(md_content, po_path)

        # Result should contain translated strings
        assert "Hola" in result
        assert "Mundo" in result


def test_build_from_po_file_not_found():
    """Test that build_from_po raises error when PO file doesn't exist."""
    md_content = "# Title"

    with pytest.raises(FileNotFoundError):
        build_from_po(md_content, "/nonexistent/path.po")


def test_extract_roundtrip():
    """Test that extract_to_pot and build_from_po can roundtrip content."""
    original = "# Document\n\nSome content here.\n\n## Section\n\nMore content."

    with tempfile.TemporaryDirectory() as tmpdir:
        pot_path = os.path.join(tmpdir, "test.pot")

        # Extract
        extract_to_pot(original, pot_path)

        # Verify POT was created
        assert os.path.exists(pot_path)

        with open(pot_path, "r") as f:
            pot_content = f.read()

        # POT should be valid
        assert "msgid" in pot_content
        assert len(pot_content) > 0
