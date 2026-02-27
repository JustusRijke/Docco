# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docco converts Markdown (with YAML frontmatter) to PDF. See `examples/Feature_Showcase.md` for full feature documentation.

## Architecture

Processing pipeline:

1. **Frontmatter Parsing** (`core.py`): Extracts YAML metadata; validates against `KNOWN_FRONTMATTER_KEYS`, warns on unknown keys
2. **Directive Processing** (`parser.py`): Iteratively processes inline directives with file-type aware post-processing
3. **Inline Processing** (`inline.py`): Embeds files via `<!-- inline:"path" -->`; .md inlined as-is, .html trimmed, .py executed (recursive, max depth 10)
4. **HTML Conversion** (`core.py`): Markdown to HTML; CSS files embedded in `<style>`, external URLs as `<link>`
5. **Translation Application** (`translation.py`): Applies PO file translations to HTML
6. **Page Layout** (`page_layout.py`): Applies pagebreak/landscape/portrait directives
7. **PDF Generation** (`pdf.py`): Chromium via Playwright; `collect_css_content()` separates file vs URL CSS
8. **PDF Validation** (`pdf_validation.py`): Validates image DPI when `dpi` is set in `.docco` config

Main entry point: `parse_markdown()` in `parser.py`. CLI orchestration in `cli.py`.

### `.docco` Config File

Flat TOML file; discovered by walking up from CWD (`_find_config_dir()` in `cli.py`). Parsed and merged with CLI args by cyclopts — CLI always takes precedence. Relative `file` paths resolve against the config file's directory.
See `.docco-example` for all supported keys.

### Language Filter Directives

`process_filter_directives()` in `parser.py` — strips `<!-- filter:en -->...<!-- /filter -->` blocks that don't match the current language code.

### Multilingual Mode

POT/PO extraction and merging in `translation.py`. PO files live in `<basename>/` alongside the source. Operates on final HTML (not Markdown).

## Development Commands

### Setup

```bash
uv sync
```

### Running

```bash
# Generate PDF
docco input.md -o output_dir

# Verbose output
docco input.md -o output_dir -v

# Keep intermediate files (for debugging)
docco input.md -o output_dir --keep-intermediate

# With translation (single-language mode)
docco input.md --po translations/de.po -o output/

# Allow Python code execution (security-sensitive)
docco input.md --allow-python -o output/

# Multilingual mode (set multilingual: true in frontmatter)
# Automatically extracts POT, updates PO files, generates all language PDFs
docco input.md -o output/
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
docco examples/Feature_Showcase.md -o output/ --allow-python
docco examples/Multilingual_Document_Example.md -o output/ --allow-python
```

**Regression Testing:**
- Uses `diffpdf` for PDF comparison with fail-fast sequential pipeline
- Comparison stages: hash check → page count → text content → visual check
- Exit code 0 = pass, 1 = fail, 2 = error
- No system dependencies required

## File Structure

```
src/docco/
  cli.py              - CLI argument parsing and commands
  config.py           - .docco config file discovery and loading
  parser.py           - Main pipeline orchestration (includes preprocess_document)
  inline.py           - Inline directive processing with file-type aware handlers (.md, .html, .py)
  core.py             - Frontmatter parsing, validation, markdown/HTML conversion
  pdf.py              - CSS collection and HTML to PDF rendering
  pdf_validation.py   - PDF image DPI validation
  page_layout.py      - Page break and orientation directives
  translation.py      - PO file application and POT extraction
  logging_config.py   - Colored logging configuration
  templates/
    base.html         - HTML template with paged.js polyfill and JavaScript TOC generation

examples/
  Feature_Showcase.md                 - Comprehensive feature demo
  Multilingual_Document_Example.md    - Translation workflow example
  css/                                - Stylesheet examples
  header.html, footer.html            - Page template examples
  inline/                             - Reusable inline content
```

## After Feature Changes

Update `examples/Feature_Showcase.md` to demonstrate new features, then rebuild regression test baselines:

```bash
docco examples/Feature_Showcase.md -o tests/output/ --allow-python
docco examples/Multilingual_Document_Example.md -o tests/output/ --allow-python
cp tests/output/*.pdf tests/baselines/
```

## References

- [markdown-it docs](https://markdown-it-py.readthedocs.io/)
- [Playwright Python docs](https://playwright.dev/python/docs/intro)
- [paged.js docs](https://pagedjs.org/documentation/)
- [CSS Paged Media (W3C)](https://www.w3.org/TR/css-page-3/)
- [translate-toolkit docs](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/)
