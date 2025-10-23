"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path
from docco.content.markdown import MarkdownConverter


@pytest.fixture
def markdown_converter():
    """MarkdownConverter instance."""
    return MarkdownConverter()


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output directory for test files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file with frontmatter."""
    md_file = tmp_path / "test.md"
    content = """---
title: Test Document
subtitle: Test Subtitle
date: 2025-10-23
author: Test Author
---

# Introduction

This is the **introduction** section.

## Details

More details here with *emphasis*.

- Item 1
- Item 2
"""
    md_file.write_text(content, encoding="utf-8")
    return md_file


@pytest.fixture
def sample_css_file(tmp_path):
    """Create a sample CSS file."""
    css_file = tmp_path / "style.css"
    content = """
@page {
    size: A4;
    margin: 25mm;
}

body {
    font-family: Arial, sans-serif;
}

.title-page {
    page-break-after: always;
}
"""
    css_file.write_text(content, encoding="utf-8")
    return css_file
