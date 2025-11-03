"""Tests for frontmatter parsing."""

import pytest
from docco.frontmatter import parse_frontmatter


def test_parse_frontmatter_with_metadata():
    """Test parsing frontmatter with multiple fields and multiline content."""
    content = """---
title: My Document
author: John Doe
css:
  - style.css
  - page.css
---
# Title

Multiple lines
of content here.

With paragraphs."""
    metadata, body = parse_frontmatter(content)
    assert metadata["title"] == "My Document"
    assert metadata["author"] == "John Doe"
    assert metadata["css"] == ["style.css", "page.css"]
    assert body.strip().startswith("# Title")
    assert "Multiple lines" in body
    assert "With paragraphs" in body


def test_parse_frontmatter_without():
    """Test content without frontmatter returns empty metadata."""
    content = "# No Frontmatter\n\nThis has no frontmatter."
    metadata, body = parse_frontmatter(content)
    assert metadata == {}
    assert body == content


def test_parse_frontmatter_invalid_yaml():
    """Test that invalid YAML raises ValueError."""
    content = """---
title: My Document
  invalid: [unclosed
---
# Content"""
    with pytest.raises(ValueError):
        parse_frontmatter(content)
