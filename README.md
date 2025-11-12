# Docco

**A CLI tool for generating professional A4 PDFs from Markdown with CSS styling.**

Docco converts Markdown documents into styled PDFs using WeasyPrint. Specify your content in Markdown, configure styling with CSS, and generate beautiful PDFs with automatic table of contents, section numbering, headers, footers, and multilingual support.

## Features

- **Markdown to PDF**: Convert Markdown to professional A4 PDFs
- **CSS Styling**: Complete layout control via CSS (including external fonts like Google Fonts)
- **Table of Contents**: Automatically generated and numbered
- **Page Layout**: Control page breaks and orientation (portrait/landscape)
- **Headers & Footers**: Customizable page headers and footers
- **Multilingual Support**: Generate language-specific PDFs from POT/PO translation files
- **Dynamic Content**: Inline file inclusion and Python code execution
- **YAML Frontmatter**: Configure document settings (CSS, multilingual mode, etc.)

## Installation

### Linux

```bash
# Install WeasyPrint (system package)
# Debian/Ubuntu:
sudo apt install weasyprint

# Arch:
sudo pacman -S python-weasyprint

# Fedora:
sudo dnf install weasyprint

# Install Docco
pip install -e .
```

### Windows

Download the WeasyPrint executable from [GitHub releases](https://github.com/Kozea/WeasyPrint/releases), extract it, and add to PATH.

```bash
# Install Docco
pip install -e .
```

Docco will automatically use the WeasyPrint executable if the Python library is unavailable.

## Quick Start

```bash
# Build a PDF
docco build examples/Feature_Showcase.md -o output/

# Extract translatable strings
docco extract document.md -o translations/

# Build with translation
docco build document.md --po translations/de.po -o output/
```

## Learn by Example

See `examples/` for complete working examples:

- **Feature_Showcase.md** - Demonstrates all features with detailed explanations
- **Multilingual_Document_Example.md** - Multilingual document setup
- **css/** - Stylesheet examples for layout, headers, footers, and typography

The examples directory includes:
- CSS files for page styling
- HTML templates for headers and footers
- Inline content templates for reusable components

## Documentation

- **CLAUDE.md** - Complete technical documentation
- **examples/** - Working examples with inline documentation

## License

MIT
