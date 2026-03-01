# Docco

[![Build](https://github.com/JustusRijke/docco/actions/workflows/build.yml/badge.svg)](https://github.com/JustusRijke/docco/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/JustusRijke/Docco/graph/badge.svg?token=26BSQ0KYAS)](https://codecov.io/gh/JustusRijke/Docco)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A CLI tool for generating professional PDFs from Markdown with CSS styling.**

Docco converts Markdown documents into styled PDFs using Playwright and paged.js. Specify your content in Markdown, configure styling with CSS, and generate beautiful PDFs.

## Features

- **Markdown to PDF**: Convert Markdown to professional PDFs with CSS styling
- **CSS Styling**: Complete layout control via CSS (including external fonts like Google Fonts)
- **Table of Contents**: Automatically generated with hierarchical numbering
- **Page Layout**: Control page breaks and orientation (portrait/landscape)
- **Headers & Footers**: Customizable page headers and footers via HTML templates
- **Multilingual Support**: Generate language-specific PDFs from POT/PO translation files
- **Dynamic Content**: Inline file inclusion with placeholder substitution and Python code execution
- **YAML Frontmatter**: Configure document settings with validation and warnings for unknown keys
- **DPI Validation**: Automatic validation of image quality in generated PDFs
- **Translation Workflow**: Automatic POT extraction and PO file updates in multilingual mode

## Requirements

- Python ≥ 3.10
- Playwright (for PDF generation)

## Installation

```bash
pip install -e .
playwright install chromium --only-shell
```

The `--only-shell` flag installs only the Chromium headless browser needed for PDF generation.

## Quick Start

```bash
# Generate a PDF
docco input.md -o output/

# With verbose output
docco input.md -o output/ -v

# Log output to file
docco input.md -o output/ --log-file docco.log

# Keep intermediate files for debugging
docco input.md -o output/ --keep-intermediate

# Allow Python code execution (security-sensitive)
docco input.md --allow-python -o output/
```

### Multilingual Mode

Declare `translations` in frontmatter to generate PDFs for multiple languages:

```yaml
---
base_language: en
translations:
  de: locales/de.po
  nl: locales/nl.po
css: style.css
---
```

Each language can reference a single PO file (string) or multiple PO files (list). When multiple files are listed, the first has the highest priority — later files fill in any untranslated strings:

```yaml
translations:
  de:
    - locales/de.po
    - shared/de_boilerplate.po
  nl: locales/nl.po
```

Then run:

```bash
docco input.md -o output/
```

Docco will:
- Extract a POT file from the rendered HTML
- Update all listed PO files with new/changed strings
- Generate `input_EN.pdf`, `input_DE.pdf`, `input_NL.pdf`

PO file paths resolve relative to the markdown file's directory.

### Library PO Files

Share common translations (e.g. company boilerplate) across documents with `library-po` in `.docco` or `--library-po` on the command line:

```toml
# .docco
library-po = ["shared/copyright.po", "shared/address.po"]
```

```bash
docco input.md -o output/ --library-po shared/copyright.po
```

Document-level translations take precedence over library translations when the same string appears in both.

### Language Filter Directive

Use `<!-- filter: <lang> -->` blocks to include content only in a specific language version:

```markdown
<!-- filter: en -->
## English Only Section

This section is only included in the English PDF.
<!-- /filter -->

<!-- filter: de -->
## Nur auf Deutsch

Dieser Abschnitt erscheint nur in der deutschen Version.
<!-- /filter -->
```

The language code is case-insensitive. Filter blocks work in both Markdown and inlined HTML files.

## Global Variables

Define reusable values in frontmatter under `var` and reference them anywhere in the document body (or inlined files) with `$$varname$$`:

```yaml
---
var:
  company: Acme Corp
  version: 2.1
---

# $$company$$ User Guide v$$version$$
```

Variables are substituted before any inline directives are processed, so they also work in inline paths:

```markdown
<!-- inline:"snippets/$$lang$$.md" -->
```

**Built-in variables** (cannot be overridden):

| Variable | Value |
|----------|-------|
| `$$PATH$$` | Absolute path to the source `.md` file |

## Frontmatter Configuration

Supported frontmatter keys:

- `css`: CSS stylesheet paths or URLs (string or list)
- `js`: JavaScript file paths or URLs (string or list) — injected as `<script>` tags in `<head>`
- `translations`: Language-to-PO-file mapping for multilingual mode (`{de: locales/de.po, nl: locales/nl.po}`)
- `base_language`: Base language code for multilingual documents (string)
- `var`: Dictionary of global variables for `$$varname$$` substitution

Unknown keys trigger a warning but don't prevent processing.

## Learn by Example

See `examples/` for complete working examples:

- **Feature_Showcase.md** - Demonstrates all features with detailed explanations ([view PDF](tests/baselines/Feature_Showcase.pdf))
- **Multilingual_Document_Example.md** - Multilingual document setup and translation workflow
- **css/** - Stylesheet examples for page layout, headers, footers, and typography
- **header.html, footer.html** - HTML templates for page headers and footers
- **inline/** - Reusable content templates with placeholder substitution

Build the examples:

```bash
docco examples/Feature_Showcase.md -o output/ --allow-python
docco examples/Multilingual_Document_Example.md -o output/ --allow-python
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/docco --cov-report=term-missing

# Lint code
ruff check .

# Build example PDF
docco examples/Feature_Showcase.md --allow-python
```

### Testing

The test suite includes regression tests that verify generated PDFs match baseline versions stored in `tests/baselines/` using [DiffPDF](https://github.com/JustusRijke/DiffPDF).

**Note:** Regression tests are skipped on Windows due to platform-specific PDF rendering differences that prevent reliable comparison.

When adding features or fixing bugs, update baselines by running:

```bash
docco examples/Feature_Showcase.md -o tests/baselines/ --allow-python
docco examples/Multilingual_Document_Example.md -o tests/baselines/
```

## Documentation

- **CLAUDE.md** - Complete technical documentation for developers
- **examples/** - Working examples with inline documentation
