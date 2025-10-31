# CLAUDE.md

Guidance for working with this repository.

## Project Overview

**Docco** is a CLI tool that converts Markdown (with YAML frontmatter) into PDFs. Features:
- Markdown parsing with YAML frontmatter
- Inline file embedding with placeholder substitution
- Multi-language support with automatic content splitting
- HTML and PDF generation with CSS styling
- Table of Contents (TOC) generation with automatic numbering
- Page layout and formatting options

Target audience: users with basic knowledge of Python, HTML, and CSS.

`examples/Feature_Showcase.md` showcases all Docco features.

## Architecture

Processing pipeline:

1. **Frontmatter Parsing** (`frontmatter.py`): Extracts YAML metadata and document body
2. **Inline Processing** (`inline.py`): Embeds external markdown via `<!-- inline:"path" -->` directives (recursive, max depth 10)
3. **Language Splitting** (`language.py`): Splits content by language tags (`<!-- lang:CODE -->...<!-- /lang -->`) if `languages` field in frontmatter
4. **TOC Generation** (`toc.py`): Generates table of contents with automatic heading numbering
5. **HTML Conversion** (`html.py`): Converts markdown to HTML with styling
6. **PDF Generation** (`pdf.py`, `page_layout.py`): Renders HTML to PDF with CSS support

Main entry point: `parse_markdown()` in `parser.py`. CLI orchestration in `cli.py`.

## Development Commands

### Setup and Running

```bash
# Install in development mode
pip install -e ".[dev]"

# Run CLI
docco input.md -o output_dir
docco input.md -o output_dir --css style.css  # With custom CSS
docco input.md -o output_dir -v               # Verbose logging
docco input.md -o output_dir --keep-intermediate  # Debug: keep intermediate files
```

### Testing

```bash
# Ruff check 
ruff check .

# Run all tests
pytest

# Run specific test file
pytest tests/test_frontmatter.py

# Run with coverage report
pytest --cov=src/docco --cov-report=term-missing

# Generate the Feature Showcase PDF
docco examples/Feature_Showcase.md --allow-python
```

## Dependencies

- **pyyaml**: YAML frontmatter parsing
- **markdown-it-py**: Markdown parsing for HTML generation
- **weasyprint**: HTML to PDF conversion with CSS support
- **pytest**: Testing framework
- **pytest-cov**: Coverage measurement

## Coding Guidelines

- Test-driven development: write tests first, then implementation
- Minimize code: use KISS & DRY principles, reduce LOC, use libraries when beneficial
- Sparse comments (complex code only), minimal function/class descriptions
- Achieve 100% test coverage
- Short, concise git commits (1-2 lines, no "Generated with Claude" messages)
- No edge case tests unless critical
- References: [markdown-it docs](https://markdown-it-py.readthedocs.io/) and [weasyprint docs](https://doc.courtbouillon.org/weasyprint/stable/)
- Any feature change/addition/removal must be kept in sync with the Feature Showcase document.
- Before committing any code, do a sanity check by running the Docco CLI on all examples and update the regression test baseline pdf files.