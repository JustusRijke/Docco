# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Docco** is a pure CLI tool that converts Markdown files (with YAML frontmatter) and CSS stylesheets into professional A4 PDFs. The system uses markdown-it-py for parsing and WeasyPrint for PDF rendering.

### Core Architecture

The system follows a **simple 2-stage pipeline**:

1. **Parse & Convert**:
   - Read Markdown file and parse YAML frontmatter (title, subtitle, date, author)
   - Convert Markdown content to HTML using markdown-it-py
   - Build complete HTML document with title page and content

2. **Render PDF**:
   - Read external CSS file
   - Pass HTML + CSS to WeasyPrint for PDF generation
   - Save debug HTML alongside PDF for troubleshooting

### Key Design Principles

- **Pure CLI Tool**: No Python API - users interact only via command line
- **External Assets**: CSS is completely external (not embedded in code)
- **Expert-Friendly**: Designed for users comfortable with Markdown and CSS
- **Simple Architecture**: Minimal abstractions, easy to understand
- **Separation of Concerns**: Content (Markdown) and layout (CSS) are completely separated

## Development Commands

### Running the CLI

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install package in editable mode (first time only)
pip install -e .

# Generate PDF using the examples
docco build examples/document.md examples/style.css --output output/example.pdf

# Or without output flag (uses default output/document.pdf)
docco build examples/document.md examples/style.css
```

Output files are created in the specified directory (or `output/` by default):
- `<output-path>.pdf` - Generated A4 PDF
- `debug.html` - Intermediate HTML for browser debugging

### Environment Setup

```bash
# Install system dependencies (Debian/Ubuntu)
apt install weasyprint

# Install package with dependencies
pip install -e .

# Install development dependencies (for testing, linting)
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docco --cov-report=html

# Run specific test file
pytest tests/unit/test_cli.py

# Run specific test
pytest tests/unit/test_cli.py::TestCliBuild::test_build_command_success
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Debugging Layout Issues

1. Run docco build with your markdown and CSS files
2. Open the generated `debug.html` in a browser to verify layout before PDF conversion
3. Modify your CSS file
4. Re-run docco build to see changes

## Project Structure

```
Docco/
├── src/
│   └── docco/
│       ├── __init__.py              # Package exports
│       ├── cli.py                   # CLI entry point with build command
│       ├── content/
│       │   └── markdown.py          # Markdown to HTML conversion
│       └── rendering/
│           └── pdf_renderer.py      # WeasyPrint wrapper
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests
│   │   ├── test_cli.py              # CLI tests
│   │   └── test_markdown.py         # Markdown conversion tests
│   └── integration/                 # Integration tests
│       └── test_pdf_generation.py   # End-to-end PDF generation tests
├── examples/
│   ├── document.md                  # Example markdown with frontmatter
│   └── style.css                    # Example stylesheet
├── output/                          # Generated files (gitignored)
├── pyproject.toml                   # Package configuration
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md                        # User documentation
```

### Module Responsibilities

#### `docco.cli` (cli.py)
- **CLI commands**: `docco build`, `docco version`
- Parses YAML frontmatter from markdown files
- Builds HTML documents with title pages
- Orchestrates markdown-to-PDF conversion
- Helper functions: `_parse_frontmatter()`, `_build_html_from_markdown()`, `_escape_html()`

#### `docco.content.markdown` (markdown.py)
- **MarkdownConverter class**: Wrapper around markdown-it-py
- Converts Markdown to HTML with inline and block modes

#### `docco.rendering.pdf_renderer` (pdf_renderer.py)
- **PDFRenderer class**: WeasyPrint wrapper
- Converts HTML+CSS to PDF files or bytes

## Current Implementation Status

**Complete**: Pure CLI tool with external CSS
- ✅ CLI interface (`docco build <md> <css>`)
- ✅ YAML frontmatter parsing
- ✅ Markdown to HTML conversion
- ✅ External CSS support (no embedded CSS)
- ✅ PDF output with WeasyPrint
- ✅ Debug HTML generation
- ✅ Unit and integration tests

**Not Implemented**:
- Image optimization/embedding
- Table of contents generation
- Mixed portrait/landscape orientations
- Reusable content modules

## Using Docco

### Basic Example

Create a markdown file with YAML frontmatter:

```markdown
---
title: My Documentation
subtitle: Technical Guide
date: 2025-10-23
author: Your Name
---

# Introduction

This is the **introduction** with *markdown*.

## Details

- Point 1
- Point 2
```

Create a CSS file:

```css
@page {
    size: A4 portrait;
    margin: 25mm;

    @top-center {
        content: "My Documentation";
        font-size: 9pt;
    }

    @bottom-right {
        content: "Page " counter(page);
        font-size: 9pt;
    }
}

.title-page {
    page-break-after: always;
}
```

Generate PDF:

```bash
docco build document.md style.css --output my_doc.pdf
```

### YAML Frontmatter

Required fields:
- `title`: Document title (required)

Optional fields:
- `subtitle`: Document subtitle
- `date`: Publication date
- `author`: Author name

### Markdown Support

Content uses markdown-it-py for parsing. Supported features:
- Bold, italic, links
- Ordered and unordered lists
- Tables
- Code blocks and inline code
- Paragraphs
- Headings (H1, H2, H3)

### CSS Customization

All layout and styling is controlled via the external CSS file:
- `@page` rules for A4 setup, headers/footers
- `.title-page` - Title page styling
- `.content` - Content wrapper
- Standard HTML selectors (h1, h2, h3, p, table, etc.)

Users provide their own CSS file - there is no default embedded CSS.

## Important Technical Details

### YAML Frontmatter Parsing

The CLI parses YAML frontmatter delimited by `---`:
- Frontmatter must be at the start of the file
- Must have opening and closing `---` delimiters
- Title field is required; others are optional
- Invalid YAML raises an error

### HTML Generation

HTML is built directly in the CLI module using string concatenation:
- Title page is generated from frontmatter metadata
- Markdown content is converted to HTML by MarkdownConverter
- Complete document structure includes `<!DOCTYPE>`, `<html>`, `<head>`, `<body>`
- HTML entities are escaped using `_escape_html()` helper

### PDF Rendering

WeasyPrint converts HTML + CSS to PDF:
- Supports CSS Paged Media (`@page` rules)
- Handles headers, footers, page numbers via CSS
- Title page can omit headers/footers using `@page :first`
- Debug HTML is saved for troubleshooting

### Testing Strategy

**Unit tests** verify individual components:
- YAML frontmatter parsing
- HTML escaping
- CLI command execution
- Error handling

**Integration tests** verify full workflows:
- Complete PDF generation
- Complex markdown documents
- Default output paths

Run tests with `pytest` after installing dev dependencies.

## Design Constraints

- Documents are small (~50 pages max), so performance optimization is not a priority
- Focus on maintainability over automation complexity
- Code should be understandable years later
- All dependencies must be open source with permissive licenses
- Target rendering time: <10 seconds for ~50 page documents
- Test coverage should remain high (aim for >80%)
- Use short/concise git commit messages

## Migration Notes

**v0.2.0 → v0.3.0**: Removed Python API entirely
- Deleted: `Document`, `Section`, `SectionNumberer`, `HTMLBuilder`, `CSSBuilder`
- Deleted: `markdown_parser.py` (was part of Python API)
- Deleted: `src/docco/core/` directory
- CLI now accepts `.md` + `.css` files directly
- No programmatic document building - pure CLI tool
