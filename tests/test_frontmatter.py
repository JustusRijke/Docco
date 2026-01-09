"""Tests for frontmatter parsing."""

import logging

import pytest

from docco.core import parse_frontmatter


def test_parse_frontmatter_with_metadata():
    """Test parsing frontmatter with multiple fields and multiline content."""
    content = """---
css:
  - style.css
  - page.css
dpi: 300
---
# Title

Multiple lines
of content here.

With paragraphs."""
    metadata = parse_frontmatter(content)
    assert metadata["css"] == ["style.css", "page.css"]
    assert metadata["dpi"] == 300


def test_parse_frontmatter_without():
    """Test content without frontmatter returns empty metadata."""
    content = "# No Frontmatter\n\nThis has no frontmatter."
    metadata = parse_frontmatter(content)
    assert metadata == {}


def test_parse_frontmatter_invalid_yaml():
    """Test that invalid YAML raises ValueError."""
    content = """---
title: My Document
  invalid: [unclosed
---
# Content"""
    with pytest.raises(ValueError, match="Invalid YAML"):
        parse_frontmatter(content)


def test_parse_frontmatter_unknown_keys(caplog):
    """Test that unknown frontmatter keys trigger a warning."""
    content = """---
css: style.css
unknown_field: value
another_unknown: 123
---
# Content"""
    with caplog.at_level(logging.WARNING):
        metadata = parse_frontmatter(content)
    assert (
        "Unknown frontmatter declaration(s): another_unknown, unknown_field"
        in caplog.text
    )
    assert metadata["unknown_field"] == "value"
    assert metadata["another_unknown"] == 123


def test_parse_frontmatter_known_keys_no_warning(caplog):
    """Test that known frontmatter keys do not trigger warnings."""
    content = """---
css: style.css
dpi: 300
multilingual: true
base_language: en
---
# Content"""
    with caplog.at_level(logging.WARNING):
        metadata = parse_frontmatter(content)
    assert "Unknown frontmatter declaration" not in caplog.text
    assert metadata["css"] == "style.css"
    assert metadata["dpi"] == 300
