"""Tests for frontmatter parsing."""

import pytest
from docco.frontmatter import parse_frontmatter


def test_parse_basic_frontmatter():
    """Test parsing basic frontmatter from content."""
    content = """---
title: My Document
---
# Content"""
    metadata, body = parse_frontmatter(content)
    assert metadata["title"] == "My Document"
    assert body == "# Content"


def test_no_frontmatter():
    """Test file without frontmatter returns empty metadata."""
    content = "# No Frontmatter\n\nThis has no frontmatter."
    metadata, body = parse_frontmatter(content)
    assert metadata == {}
    assert body == content


def test_multiple_metadata_fields():
    """Test parsing multiple metadata fields."""
    content = """---
title: My Document
author: John Doe
css: style.css
---
# Content"""
    metadata, body = parse_frontmatter(content)
    assert metadata["title"] == "My Document"
    assert metadata["author"] == "John Doe"
    assert metadata["css"] == "style.css"
    assert body == "# Content"


def test_invalid_yaml():
    """Test that invalid YAML raises error."""
    content = """---
title: My Document
  invalid: [unclosed
---
# Content"""
    with pytest.raises(ValueError):
        parse_frontmatter(content)


def test_empty_frontmatter():
    """Test empty frontmatter block."""
    content = """---
---
# Content"""
    metadata, body = parse_frontmatter(content)
    assert metadata == {}
    assert body == "# Content"


def test_multiline_content_after_frontmatter():
    """Test that multiline content is preserved after frontmatter."""
    content = """---
title: My Document
---
# Title

Multiple lines
of content here.

With paragraphs."""
    metadata, body = parse_frontmatter(content)
    assert metadata["title"] == "My Document"
    assert "Multiple lines" in body
    assert "With paragraphs" in body


def test_frontmatter_starts_but_no_closing():
    """Test content that starts with --- but has no closing ---."""
    content = """---
title: My Document
# Title
Some content"""
    metadata, body = parse_frontmatter(content)
    # Should return empty metadata and original content
    assert metadata == {}
    assert body == content


def test_frontmatter_single_line():
    """Test content with only opening --- delimiter."""
    content = "---"
    metadata, body = parse_frontmatter(content)
    # Should return empty metadata and original content
    assert metadata == {}
    assert body == content
