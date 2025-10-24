# Docco

**A pure CLI tool for generating professional A4 PDFs from Markdown and CSS.**

Docco converts Markdown documents into styled PDFs using WeasyPrint. Write your content in Markdown, style it with CSS, and generate beautiful PDFs with automatic table of contents, section numbering, headers, footers, and multilingual support.

## Features

- **Markdown to PDF**: Convert Markdown content to professional A4 PDFs
- **External CSS Styling**: Complete layout control via CSS (no embedded styles)
- **Table of Contents**: Automatically generated with section numbers
- **Multilingual Support**: Generate language-specific PDFs from a single file
- **Custom Commands**: Define reusable HTML components via templates
- **Orientation Control**: Mix portrait and landscape pages
- **Headers & Footers**: Language-specific templates with variable substitution
- **Debug HTML**: Intermediate HTML output for browser-based layout debugging

## Installation (Linux)

### System Dependencies

```bash
# Debian/Ubuntu
sudo apt install weasyprint

# Arch
sudo pacman -S python-weasyprint

# Fedora
sudo dnf install weasyprint
```

### Install Docco

```bash
# Clone repository
git clone <repo-url>
cd Docco

# Install package
pip install -e .

# Verify installation
docco version
```

## Quick Start

```bash
# Generate PDF from examples
docco build examples/Feature\ Showcase.md examples/style.css

# Output will be in output/ directory
# - Feature Showcase.pdf (generated PDF)
# - debug.html (intermediate HTML for debugging)
```

## Basic Usage

```bash
# Generate single PDF
docco build document.md style.css

# Specify output path
docco build document.md style.css --output report.pdf

# Multilingual documents (generates document_EN.pdf, document_DE.pdf, etc.)
docco build multilingual.md style.css
```

## Examples

The `examples/` directory contains complete working examples:

- **Feature Showcase.md** - Demonstrates all features (TOC, numbering, orientation control, images)
- **Multilingual Example.md** - Shows language filtering and multilingual PDF generation
- **style.css** - Production-ready stylesheet with A4 layout, headers, footers
- **commands/** - Custom command templates (callout boxes, etc.)
- **header.html / footer.html** - Header/footer templates with language variants

These examples serve as the primary documentation. Study them to learn:
- How to structure markdown documents
- How to use custom commands (`<!-- cmd: callout -->`)
- How to control orientation (`<!-- landscape -->`, `<!-- portrait -->`)
- How to create addendums (`<!-- addendum -->`)
- How to filter content by language (`<!-- lang:EN -->`)
- How to style with CSS (@page rules, section numbering, etc.)

## Documentation

- **CLAUDE.md** - Complete technical documentation covering architecture, modules, features, and coding guidelines
- **examples/** - Working examples demonstrating all features

## License

MIT
