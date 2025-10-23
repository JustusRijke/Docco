---
title: Docco Documentation Generator
subtitle: Complete Feature Demonstration
date: 2025-10-23
author: Engineering Team
---

# Introduction

This document demonstrates **all features** of Docco, a pure CLI tool that converts Markdown + CSS into professional A4 PDFs.

Docco is designed for *expert users* who want complete control over document layout and styling. Content is written in **Markdown** with YAML frontmatter, while all styling is handled by external **CSS** files.

## Key Features

The system supports:
- **YAML frontmatter** for metadata (title, subtitle, date, author)
- **Full Markdown syntax** (headings, lists, tables, code blocks, emphasis)
- **External CSS** for complete styling control
- **Debug HTML output** for troubleshooting layout issues
- **Automatic heading hierarchy** (H1, H2, H3)
- **CSS Paged Media** for headers, footers, and page numbering

## Why Docco?

Unlike traditional document generators, Docco keeps things simple:
- No complex Python API to learn
- No embedded templates or styling
- Pure separation of content (Markdown) and presentation (CSS)
- Professional PDF output via WeasyPrint

# Installation

To install Docco, follow these steps:

## System Requirements

The following system requirements must be met:

| Component       | Minimum    | Recommended |
|-----------------|------------|-------------|
| Python          | 3.10+      | 3.11+       |
| RAM             | 4 GB       | 8 GB        |
| Storage         | 1 GB       | 2 GB        |
| OS              | Linux/macOS| Linux       |

## Installation Steps

1. Install system dependencies:
   ```bash
   apt install weasyprint  # Debian/Ubuntu
   ```

2. Clone the repository:
   ```bash
   git clone <repo-url>
   cd Docco
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

4. Verify installation:
   ```bash
   docco version
   ```

## Configuration

After installation, you can start creating documents immediately. No additional configuration is required.

# Usage

This section covers how to use Docco to generate PDFs.

## Basic Workflow

The workflow consists of three simple steps:

1. **Create a Markdown file** with YAML frontmatter
2. **Create a CSS file** with your desired styling
3. **Run the CLI command** to generate the PDF

### Step 1: Create Markdown File

Create a file named `document.md`:

```markdown
---
title: My Document
subtitle: Technical Guide
date: 2025-10-23
author: Your Name
---

# Introduction

Your content here...
```

### Step 2: Create CSS File

Create a file named `style.css`:

```css
@page {
    size: A4 portrait;
    margin: 25mm;

    @top-center {
        content: "My Document";
        font-size: 9pt;
    }

    @bottom-right {
        content: "Page " counter(page);
        font-size: 9pt;
    }
}

body {
    font-family: Arial, sans-serif;
    font-size: 11pt;
}
```

### Step 3: Generate PDF

Run the CLI command:

```bash
docco build document.md style.css --output my_doc.pdf
```

Output files:
- `my_doc.pdf` - Final rendered PDF
- `debug.html` - Intermediate HTML for debugging

## Advanced Usage

### Custom Output Paths

Specify a custom output location:

```bash
docco build input.md style.css --output reports/2025/quarterly.pdf
```

### Default Output

Omit the `--output` flag to use the default location (`output/document.pdf`):

```bash
docco build input.md style.css
```

### Debug HTML

The debug HTML is always generated alongside the PDF. Open it in a browser to verify layout before PDF rendering.

# Markdown Features

Docco supports the full Markdown specification via `markdown-it-py`.

## Text Formatting

- **Bold text** using `**bold**`
- *Italic text* using `*italic*`
- `Inline code` using backticks
- ~~Strikethrough~~ using `~~strikethrough~~`

## Lists

### Unordered Lists

Shopping list:
- Apples
- Bananas
- Oranges
  - Navel oranges
  - Blood oranges

### Ordered Lists

Installation steps:
1. Download the package
2. Extract the archive
3. Run the installer
4. Restart the system

## Code Blocks

Python example:

```python
from docco import MarkdownConverter

converter = MarkdownConverter()
html = converter.convert("**Hello World**")
print(html)
```

Shell commands:

```bash
docco build examples/document.md examples/style.css
ls -la output/
```

YAML configuration:

```yaml
database:
  host: localhost
  port: 5432
  name: production
  pool_size: 10
```

## Tables

### Simple Table

| Feature      | Supported |
|--------------|-----------|
| Markdown     | ✓         |
| CSS          | ✓         |
| Images       | ✗         |
| TOC          | Planned   |

### Complex Table with Alignment

| Component         | Input Type    | Output Type   | Dependencies          |
|:------------------|:-------------:|:-------------:|----------------------:|
| MarkdownConverter | String        | HTML          | markdown-it-py        |
| PDFRenderer       | HTML + CSS    | PDF bytes     | WeasyPrint            |
| CLI               | Files         | PDF file      | Click, PyYAML         |

## Links

- [Docco Repository](https://github.com/example/docco)
- [WeasyPrint Documentation](https://weasyprint.org/)
- [Markdown Guide](https://www.markdownguide.org/)

## Blockquotes

> "Simplicity is the ultimate sophistication."
> — Leonardo da Vinci

> **Note**: Always test your CSS in the debug HTML before generating the final PDF.

## Horizontal Rules

Use three dashes to create a horizontal rule:

---

Content continues after the rule.

# CSS Styling

All document styling is controlled via external CSS files.

## Page Setup

Use `@page` rules to configure page layout:

```css
@page {
    size: A4 portrait;
    margin: 25mm 20mm;
}
```

## Headers and Footers

Add headers and footers using CSS margin boxes:

```css
@page {
    @top-center {
        content: "Document Title";
        font-size: 9pt;
        color: #666;
    }

    @bottom-right {
        content: "Page " counter(page);
        font-size: 9pt;
    }

    @bottom-left {
        content: "Confidential";
        font-size: 9pt;
        color: red;
    }
}
```

## Title Page Customization

Remove headers/footers from the title page:

```css
@page :first {
    @top-center { content: none; }
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}
```

## Typography

Control fonts, sizes, and spacing:

```css
body {
    font-family: "DejaVu Sans", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    font-size: 18pt;
    margin-top: 15mm;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    margin-top: 8mm;
    page-break-after: avoid;
}
```

<!-- landscape -->
# Advanced Features Comparison

This section demonstrates **landscape orientation** using the `<!-- landscape -->` directive placed before the heading.

Landscape pages are useful for wide tables, diagrams, or content that benefits from horizontal space.

## Feature Matrix

| Feature | Docco | Pandoc | LaTeX | Sphinx | MkDocs | Hugo | Jekyll |
|---------|-------|--------|-------|--------|--------|------|--------|
| **Markdown Input** | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| **YAML Frontmatter** | ✓ | ✓ | ✗ | Limited | ✓ | ✓ | ✓ |
| **External CSS** | ✓ | Limited | ✗ | Limited | ✓ | ✓ | ✓ |
| **PDF Output** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| **Mixed Orientations** | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **Table of Contents** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Custom Headers/Footers** | ✓ | Limited | ✓ | Limited | Limited | Limited | Limited |
| **Simple CLI** | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ |
| **No Configuration Files** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Learning Curve** | Low | Medium | High | Medium | Low | Low | Low |

## Use Cases by Tool

| Tool | Best For | Output Formats | Complexity |
|------|----------|----------------|------------|
| **Docco** | Technical documentation with custom PDF styling | PDF | Low |
| **Pandoc** | Document format conversion | PDF, HTML, DOCX, etc. | Medium |
| **LaTeX** | Academic papers, complex typography | PDF | High |
| **Sphinx** | Software documentation with code integration | HTML, PDF | Medium |
| **MkDocs** | Project documentation websites | HTML | Low |
| **Hugo** | Static websites, blogs | HTML | Low |
| **Jekyll** | GitHub Pages, blogs | HTML | Low |

<!-- portrait -->
# Troubleshooting

Common issues and their solutions.

## PDF Generation Fails

**Symptoms**: CLI exits with error, no PDF generated

**Solutions**:
1. Check debug HTML for rendering issues
2. Validate YAML frontmatter syntax
3. Ensure CSS file path is correct
4. Verify WeasyPrint is installed: `weasyprint --version`

## Incorrect Layout

**Symptoms**: Content appears wrong in PDF but correct in debug HTML

**Solutions**:
1. Review CSS `@page` rules
2. Check for conflicting CSS properties
3. Test with minimal CSS first
4. Consult WeasyPrint CSS Paged Media docs

## Missing Fonts

**Symptoms**: Text renders with wrong font

**Solutions**:
1. Use fonts available on your system
2. Check font names with `fc-list` command
3. Fall back to web-safe fonts: Arial, Times New Roman, Courier
4. Use font families with fallbacks: `"DejaVu Sans", Arial, sans-serif`

## Performance Issues

**Symptoms**: PDF generation takes too long

**Solutions**:
1. Reduce document size (split into multiple PDFs)
2. Optimize images (not yet implemented)
3. Simplify CSS (avoid complex selectors)
4. Use simpler fonts

# Best Practices

Recommendations for effective document creation.

## Content Organization

1. **Use clear heading hierarchy**: H1 for chapters, H2 for sections, H3 for subsections
2. **Keep paragraphs concise**: 3-5 sentences maximum
3. **Use lists for enumeration**: Better readability than inline text
4. **Add code blocks for technical content**: Syntax highlighting helps comprehension

## CSS Styling

1. **Start with minimal CSS**: Add complexity incrementally
2. **Test in debug HTML first**: Faster iteration than PDF generation
3. **Use CSS variables**: For consistent theming
4. **Avoid absolute positioning**: Let content flow naturally

## Workflow

1. **Draft in Markdown first**: Focus on content, not styling
2. **Create CSS template**: Reuse across documents
3. **Generate debug HTML frequently**: Catch layout issues early
4. **Version control both files**: Track content and styling changes

# Future Enhancements

Planned features for future releases:

- **Image support**: Embedded images with optimization
- **Template system**: Pre-built CSS templates
- **Custom page sizes**: Beyond A4 (Letter, Legal, etc.)
- **Multi-file input**: Concatenate multiple Markdown files
- **Page number links**: Click TOC entries to jump to pages in PDF

# Conclusion

Docco provides a simple, powerful way to generate professional PDFs from Markdown and CSS.

## Key Takeaways

- **Separation of concerns**: Content in Markdown, styling in CSS
- **Expert-friendly**: Full control over layout and typography
- **Simple workflow**: Three steps to PDF generation
- **Debug support**: HTML output for troubleshooting

## Next Steps

1. Install Docco following the instructions in this document
2. Create your first Markdown + CSS document
3. Generate a PDF and review the output
4. Customize the CSS to match your brand
5. Automate PDF generation in your build pipeline

## Support

For issues, questions, or contributions:
- GitHub: [Repository URL]
- Documentation: [Docs URL]
- Email: support@example.com

---

**Thank you for using Docco!**

*This document itself was generated using Docco from Markdown + CSS.*

<!-- addendum -->
# Quick Reference Guide

This appendix provides a quick reference for Docco's features and directives.

## Supported Directives

Place HTML comment directives **before** a heading to control its behavior:

| Directive | Effect | Example |
|-----------|--------|---------|
| `<!-- landscape -->` | Section displays in landscape orientation | Wide tables |
| `<!-- portrait -->` | Section displays in portrait orientation (default) | Normal content |
| `<!-- addendum -->` | Section becomes an appendix with letter numbering | A, B, C... |

## YAML Frontmatter Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `title` | Yes | Document title | `My Documentation` |
| `subtitle` | No | Document subtitle | `Technical Guide` |
| `date` | No | Publication date | `2025-10-23` |
| `author` | No | Author name | `Engineering Team` |

## CLI Commands

```bash
# Generate PDF
docco build <markdown-file> <css-file> --output <pdf-path>

# Show version
docco version
```

## Markdown Cheat Sheet

| Element | Syntax |
|---------|--------|
| Bold | `**text**` |
| Italic | `*text*` |
| Inline code | `` `code` `` |
| Link | `[text](url)` |
| Heading 1 | `# Title` |
| Heading 2 | `## Title` |
| Heading 3 | `### Title` |
| Unordered list | `- Item` |
| Ordered list | `1. Item` |

<!-- addendum -->
# Common CSS Patterns

This appendix provides reusable CSS patterns for common document layouts.

## Two-Column Layout

```css
.two-column {
    column-count: 2;
    column-gap: 10mm;
}
```

## Custom Page Break

```css
.page-break {
    page-break-before: always;
}
```

## No Page Break Inside

```css
.keep-together {
    page-break-inside: avoid;
}
```

## Different First Page

```css
@page :first {
    margin-top: 50mm;
    @top-center { content: none; }
}
```

## Alternate Header/Footer

```css
@page :left {
    @bottom-left { content: "Chapter " counter(chapter); }
}

@page :right {
    @bottom-right { content: counter(page); }
}
```
