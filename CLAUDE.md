# CLAUDE.md

Guidance for working with this repository.

## Project Overview

**Docco** is a CLI tool that converts Markdown (with YAML frontmatter) into PDFs. Features:
- Markdown parsing with YAML frontmatter
- Inline file embedding with placeholder substitution
- Professional translation workflows with POT/PO files
- HTML and PDF generation with CSS styling
- Table of Contents (TOC) generation with automatic numbering
- Page layout and formatting options

Target audience: users with basic knowledge of Python, HTML, and CSS.

`examples/Feature_Showcase.md` showcases all Docco features.

## Architecture

Processing pipeline:

1. **Frontmatter Parsing** (`frontmatter.py`): Extracts YAML metadata and document body
2. **Inline Processing** (`inline.py`): Embeds external markdown via `<!-- inline:"path" -->` directives (recursive, max depth 10)
3. **Directive Processing** (`parser.py`): Iteratively processes inline and python directives
4. **HTML Conversion** (`html.py`): Converts markdown to HTML with styling
5. **Translation Application** (`translation.py`): Optionally applies PO file translations to HTML (before TOC/layout)
6. **TOC Generation** (`toc.py`): Generates table of contents with automatic heading numbering (applied after translation, so headings are numbered in target language)
7. **Page Layout** (`page_layout.py`): Applies page layout formatting
8. **PDF Generation** (`pdf.py`): Renders HTML to PDF with CSS support

Main entry point: `parse_markdown()` in `parser.py`. CLI orchestration in `cli.py`.

### Translation Workflow

For professional translations using POT/PO files:

1. **Extraction**: Use `docco extract input.md -o translations/` to generate a POT file from HTML (markdown is first converted to HTML, then POT is extracted from the HTML)
2. **Translation**: Translators create language-specific PO files (e.g., `de.po`, `fr.po`) using tools like poedit or web-based platforms. **Note**: msgids contain HTML tags (e.g., `"Text with <strong>bold</strong>"`), not markdown syntax. Translators must preserve HTML tags in translations.
3. **Build**: Generate translated PDFs with `docco input.md --po translations/de.po -o output/`

This workflow:
- Extracts strings from final HTML, enabling translation of dynamically-generated content (TOC numbers, page layout elements)
- Applies translations before TOC generation, so headings are numbered in the target language
- Integrates with professional CAT tools and translation management systems that support HTML

**Breaking change**: Existing POT/PO files from the markdown-based workflow (mdpo) are incompatible with the new HTML-based workflow. msgids differ because markdown formatting is converted to HTML tags.

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

# Translation workflow
docco extract input.md -o translations/       # Extract translatable strings to POT
docco input.md --po translations/de.po -o output/  # Build PDF with German translation
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
- **translate-toolkit**: HTML to POT/PO file conversion for translations
- **pytest**: Testing framework
- **pytest-cov**: Coverage measurement

## Coding Guidelines

- Test-driven development: write tests first, then implementation
- Minimize code: use KISS & DRY principles, reduce LOC, use libraries when beneficial
- Sparse comments (complex code only), minimal function/class descriptions
- Achieve 100% test coverage
- Short, concise git commits (1-2 lines, no "Generated with Claude" messages)
- No edge case tests unless critical
- References: [markdown-it docs](https://markdown-it-py.readthedocs.io/), [weasyprint docs](https://doc.courtbouillon.org/weasyprint/stable/) and [translate-toolkit docs](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/).
- Any feature change/addition/removal must be kept in sync with the Feature Showcase document.
- Before committing any code, do a sanity check by running the Docco CLI on all examples and update the regression test baseline pdf files.
 - Prefer fail-fast behavior: avoid over-defensive exception handling, let errors surface.