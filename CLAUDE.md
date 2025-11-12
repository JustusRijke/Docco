# CLAUDE.md

Guidance for working with this repository.

## Project Overview

**Docco** is a CLI tool that converts Markdown documents (with YAML frontmatter) into professional PDFs. Key capabilities:

- Markdown parsing with YAML frontmatter configuration
- Inline file inclusion with placeholder substitution
- CSS styling with support for external fonts (Google Fonts, etc.)
- Automatic table of contents with heading numbering
- Page layout control (breaks, orientation, headers, footers)
- Professional translation workflows with POT/PO files
- Dynamic content via Python code execution (opt-in)

Target audience: developers and technical writers familiar with Markdown, HTML, and CSS.

`examples/Feature_Showcase.md` demonstrates all features with detailed explanations.

## Architecture

Processing pipeline:

1. **Frontmatter Parsing** (`frontmatter.py`): Extracts YAML metadata and document body
2. **Directive Processing** (`parser.py`): Iteratively processes inline and python directives
3. **Inline Processing** (`inline.py`): Embeds external markdown via `<!-- inline:"path" -->` directives (recursive, max depth 10)
4. **HTML Conversion** (`core.py`): Converts markdown to HTML; collects CSS from frontmatter (files are embedded in `<style>` tags, external URLs become `<link>` tags)
5. **Translation Application** (`translation.py`): Optionally applies PO file translations to HTML
6. **TOC Generation** (`toc.py`): Generates table of contents with automatic heading numbering
7. **Page Layout** (`page_layout.py`): Applies page layout directives (pagebreak, landscape/portrait)
8. **PDF Generation** (`pdf.py`): Renders HTML to PDF with CSS support (both embedded and external CSS)

Main entry point: `parse_markdown()` in `parser.py`. CLI orchestration in `cli.py`.

### CSS Handling

The `collect_css_content()` function in `pdf.py` separates CSS sources:

- **File-based CSS**: Relative paths are read and embedded in `<style>` tags in the HTML head
- **External CSS URLs**: URLs (http:// or https://) are added as `<link>` tags, allowing WeasyPrint to fetch them (enables Google Fonts and other web fonts)

### Translation Workflow

For professional translations using POT/PO files:

1. **Extraction**: `docco extract input.md -o translations/` generates a POT file from final HTML
2. **Translation**: Translators create language-specific PO files (e.g., `de.po`, `fr.po`) using standard translation tools. msgids contain HTML tags (not markdown); translators must preserve them.
3. **Build**: Generate translated PDFs with `docco build input.md --po translations/de.po -o output/`

This workflow:
- Extracts strings from final HTML, enabling translation of dynamic content (TOC numbers, page elements)
- Applies translations before TOC generation so headings are numbered in target language
- Integrates with CAT tools supporting HTML

## Development Commands

### Setup

```bash
pip install -e ".[dev]"
```

### Running

```bash
# Build a single PDF
docco build input.md -o output_dir

# Verbose output
docco build input.md -o output_dir -v

# Keep intermediate files (for debugging)
docco build input.md -o output_dir --keep-intermediate

# Extract translatable strings
docco extract input.md -o translations/

# Build with translation
docco build input.md --po translations/de.po -o output/

# Allow Python code execution (security-sensitive)
docco build input.md --allow-python -o output/
```

### Testing

```bash
# Lint
ruff check .

# Run all tests
pytest

# Run specific test file
pytest tests/test_frontmatter.py

# Run with coverage
pytest --cov=src/docco --cov-report=term-missing

# Build example PDFs
docco build examples/Feature_Showcase.md -o output/ --allow-python
docco build examples/Multilingual_Document_Example.md -o output/ --allow-python
```

## Dependencies

- **pyyaml**: YAML frontmatter parsing
- **markdown-it-py**: Markdown to HTML conversion
- **weasyprint**: HTML to PDF generation
- **translate-toolkit**: HTML to POT/PO file conversion
- **pytest**: Testing framework
- **pytest-cov**: Coverage measurement
- **ruff**: Code linting

## Coding Guidelines

- Test-driven development: write tests before implementation
- Minimize code: KISS & DRY principles
- Sparse comments (complex logic only); minimal docstrings
- Target 100% test coverage
- Short, concise commit messages (1-2 lines)
- No edge case tests unless critical
- References:
  - [markdown-it docs](https://markdown-it-py.readthedocs.io/)
  - [weasyprint docs](https://doc.courtbouillon.org/weasyprint/stable/)
  - [translate-toolkit docs](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/)
- **Important**: After any feature change, update `examples/Feature_Showcase.md` and rebuild regression test baselines:
  ```bash
  docco build examples/Feature_Showcase.md -o tests/output/ --allow-python
  docco build examples/Multilingual_Document_Example.md -o tests/output/ --allow-python
  cp tests/output/*.pdf tests/baselines/
  ```
- Prefer fail-fast: avoid over-defensive exception handling

## File Structure

```
src/docco/
  cli.py              - CLI argument parsing and commands
  parser.py           - Main pipeline orchestration
  frontmatter.py      - YAML frontmatter extraction
  inline.py           - Directive processing (inline, python)
  core.py             - Markdown to HTML conversion and wrapping
  pdf.py              - CSS collection and HTML to PDF rendering
  toc.py              - Table of contents generation
  page_layout.py      - Page break and orientation directives
  translation.py      - PO file application and POT extraction
  directive_utils.py  - Utility functions for directive processing

examples/
  Feature_Showcase.md                 - Comprehensive feature demo
  Multilingual_Document_Example.md    - Translation workflow example
  css/                                - Stylesheet examples
  header.html, footer.html            - Page template examples
  inline/                             - Reusable inline content
```
