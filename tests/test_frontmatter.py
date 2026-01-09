"""Tests for frontmatter parsing."""

import logging

import pytest

from docco.core import parse_frontmatter


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
