# Docco

**A pure CLI tool for generating professional A4 PDFs from Markdown and CSS.**

Docco converts Markdown documents with YAML frontmatter into styled PDFs using WeasyPrint's CSS Paged Media support.

---

## Features

- **Pure Markdown Input**: Write your documentation in Markdown with YAML frontmatter for metadata
- **External CSS Styling**: Complete control over layout, typography, headers, and footers via CSS
- **Professional PDFs**: A4 output with proper pagination, headers, footers, and page numbering
- **Simple CLI**: Single command to generate PDFs from source files
- **Debug Support**: Generates intermediate HTML for browser-based debugging

---

## Installation

### System Requirements

- Python 3.10+
- WeasyPrint system dependencies (see below)

### Debian/Ubuntu

```bash
# Install system dependencies
apt install weasyprint

# Clone repository
git clone <repo-url>
cd Docco

# Install package
pip install -e .
```

### Dependencies

Docco uses the following libraries:
- **WeasyPrint**: PDF rendering engine with CSS Paged Media support
- **markdown-it-py**: Fast Markdown to HTML conversion
- **PyYAML**: YAML frontmatter parsing
- **Click**: CLI framework

---

## Quick Start

### 1. Create a Markdown file with YAML frontmatter

**document.md**:
```markdown
---
title: My Documentation
subtitle: Technical Guide
date: 2025-10-23
author: Your Name
---

# Introduction

This is the **introduction** section with *markdown* formatting.

## Features

Key features include:
- Item 1
- Item 2
- Item 3

# Details

More content here...
```

### 2. Create a CSS stylesheet

**style.css**:
```css
@page {
    size: A4 portrait;
    margin: 25mm;

    @top-center {
        content: "My Documentation";
        font-size: 9pt;
        color: #666;
    }

    @bottom-right {
        content: "Page " counter(page);
        font-size: 9pt;
    }
}

@page :first {
    @top-center { content: none; }
    @bottom-right { content: none; }
}

body {
    font-family: "DejaVu Sans", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
}

.title-page {
    page-break-after: always;
    text-align: center;
    padding-top: 100mm;
}

.title-page h1 {
    font-size: 28pt;
}

h1 {
    font-size: 18pt;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    page-break-after: avoid;
}
```

### 3. Generate PDF

```bash
docco build document.md style.css --output my_doc.pdf
```

Output:
- `my_doc.pdf` - Final rendered PDF
- `debug.html` - Intermediate HTML (for debugging)

---

## Usage

### CLI Commands

**Build a PDF**:
```bash
docco build <markdown-file> <css-file> [--output <pdf-path>]
```

**Show version**:
```bash
docco version
```

### YAML Frontmatter

The Markdown file must include YAML frontmatter with at least a `title` field:

```yaml
---
title: Document Title       # Required
subtitle: Subtitle          # Optional
date: 2025-10-23           # Optional
author: Author Name        # Optional
---
```

### Markdown Support

Docco uses `markdown-it-py` for parsing, supporting:
- **Bold**, *italic*, `inline code`
- Headings (H1, H2, H3)
- Lists (ordered and unordered)
- Tables
- Code blocks
- Links

### CSS Customization

All layout and styling is controlled via CSS. Key features:
- `@page` rules for page setup (size, margins, headers, footers)
- `@page :first` to customize the title page
- Standard CSS selectors for content styling
- Print-specific properties (page breaks, widows, orphans)

See `examples/style.css` for a complete example.

---

## Examples

Example files are provided in the `examples/` directory:
- `document.md` - Sample markdown document with frontmatter
- `style.css` - Default stylesheet with A4 layout

Generate the example:
```bash
docco build examples/document.md examples/style.css --output output/example.pdf
```

---

## Architecture

Docco follows a simple 2-stage pipeline:

1. **Parse & Convert**: Read Markdown file, parse YAML frontmatter, convert Markdown to HTML
2. **Render PDF**: Pass HTML + CSS to WeasyPrint for PDF generation

### Project Structure

```
Docco/
├── src/
│   └── docco/
│       ├── cli.py                    # CLI entry point
│       ├── content/
│       │   └── markdown.py           # Markdown converter
│       └── rendering/
│           └── pdf_renderer.py       # WeasyPrint wrapper
├── examples/
│   ├── document.md                   # Example markdown file
│   └── style.css                     # Example stylesheet
├── tests/
│   ├── unit/                         # Unit tests
│   └── integration/                  # Integration tests
└── README.md
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docco --cov-report=html

# Run specific test
pytest tests/unit/test_cli.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

---

## Design Principles

- **Simplicity**: No complex abstractions or Python API - just a CLI tool
- **Separation of Concerns**: Content (Markdown) and layout (CSS) are completely separated
- **Expert-Friendly**: Designed for users comfortable with Markdown and CSS
- **Maintainability**: Clean, readable code that's easy to understand and modify
- **Transparency**: Generates debug HTML for easy troubleshooting

---

## Troubleshooting

### PDF Generation Issues

1. **Check debug HTML**: Open `debug.html` in a browser to verify content and layout
2. **Validate CSS**: Ensure your CSS uses valid CSS Paged Media syntax
3. **Check frontmatter**: Verify YAML frontmatter is properly formatted with `title` field

### WeasyPrint Errors

- Ensure WeasyPrint system dependencies are installed
- Check that font names in CSS match available system fonts
- Use `--verbose` flag for detailed error messages (future feature)

---

## License

[License information here]

---

## Contributing

[Contribution guidelines here]
