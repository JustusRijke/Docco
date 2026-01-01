# Docco

[![Build](https://github.com/JustusRijke/docco/actions/workflows/build.yml/badge.svg)](https://github.com/JustusRijke/docco/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/JustusRijke/Docco/graph/badge.svg?token=26BSQ0KYAS)](https://codecov.io/gh/JustusRijke/Docco)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


**A CLI tool for generating professional PDFs from Markdown with CSS styling.**

Docco converts Markdown documents into styled PDFs using WeasyPrint. Specify your content in Markdown, configure styling with CSS, and generate beautiful PDFs with automatic table of contents, section numbering, headers, footers, and multilingual support.

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
- WeasyPrint (for PDF generation)

## Installation

```bash
pip install -e .
```

### Note on WeasyPrint

WeasyPrint installation varies by platform. See the [WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) for platform-specific instructions.

On Windows, WeasyPrint is not available via pip. Docco will automatically use the WeasyPrint executable if the Python library is unavailable.

## Quick Start

```bash
# Generate a PDF
docco input.md -o output/

# With verbose output
docco input.md -o output/ -v

# Keep intermediate files for debugging
docco input.md -o output/ --keep-intermediate

# Single-language mode with translation
docco input.md --po translations/de.po -o output/

# Allow Python code execution (security-sensitive)
docco input.md --allow-python -o output/
```

### Multilingual Mode

Set `multilingual: true` in frontmatter to automatically:
- Extract POT file from HTML content
- Update all PO files with new/changed strings
- Generate PDFs for base language + all translations

```yaml
---
multilingual: true
base_language: en
css: style.css
---
```

Then simply run:
```bash
docco input.md -o output/
```

Docco will generate `input_EN.pdf`, `input_DE.pdf`, etc., based on available PO files in the `input/` directory.

## Frontmatter Configuration

Supported frontmatter keys:

- `css`: CSS stylesheet paths or URLs (string or list)
- `dpi`: Maximum image resolution for PDF output (integer)
- `multilingual`: Enable multilingual mode (boolean)
- `base_language`: Base language code for multilingual documents (string)

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
cd examples
docco Feature_Showcase.md --allow-python
```

### Testing

The test suite includes regression tests that verify generated PDFs match baseline versions stored in `tests/baselines/`. Regression tests use [DiffPDF](https://github.com/JustusRijke/DiffPDF) for comprehensive PDF comparison across hash, page count, text content, and visual layers.

When adding features or fixing bugs, update baselines by running:
```bash
cd examples
docco Feature_Showcase.md -o ../tests/baselines/ --allow-python
docco Multilingual_Document_Example.md -o ../tests/baselines/ --allow-python
```

## Documentation

- **CLAUDE.md** - Complete technical documentation for developers
- **examples/** - Working examples with inline documentation
