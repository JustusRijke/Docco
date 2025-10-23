# Introduction

This document demonstrates Docco's markdown-based document generation feature.

The content is written in a **single markdown file** with HTML comment directives to control layout and structure.

## Key Features

Supported features include:

- Automatic section numbering from headings
- Mixed portrait and landscape orientations
- Appendix sections (lettered A, B, C)
- Exclusion of sections from table of contents
- Full markdown support (tables, lists, code, etc.)

## Getting Started

To create a document from markdown:

1. Write your content in a `.md` file
2. Use HTML comments for special directives
3. Load the file into a `Document` instance
4. Render to PDF

# Technical Architecture

## System Components

The Docco system consists of several key components:

- **Document**: Main orchestrator for PDF generation
- **MarkdownParser**: Converts markdown files to Section objects
- **HTMLBuilder**: Assembles HTML from sections
- **PDFRenderer**: Converts HTML to PDF using WeasyPrint

## Data Flow

```
Markdown File → Parser → Sections → Document → HTML → PDF
```

<!-- landscape -->
## Component Interaction Diagram

This section is displayed in **landscape orientation** to accommodate the wide table below.

| Component | Input | Processing | Output | Dependencies |
|-----------|-------|------------|--------|--------------|
| MarkdownParser | .md file | Regex parsing, directive extraction | List[Section] | re, pathlib |
| Document | Sections, metadata | Numbering, orchestration | HTML string | SectionNumberer, HTMLBuilder |
| HTMLBuilder | Sections | Template generation | HTML document | MarkdownConverter |
| CSSBuilder | Configuration | Style generation | CSS rules | None |
| PDFRenderer | HTML + CSS | WeasyPrint rendering | PDF bytes | WeasyPrint |

The landscape orientation provides more horizontal space for tables and diagrams.

<!-- portrait -->
## Implementation Details

This section returns to **portrait orientation** (the default).

### Directive Syntax

Directives use HTML comment syntax:

- `<!-- landscape -->` - Switch to landscape orientation
- `<!-- portrait -->` - Switch to portrait orientation
- `<!-- addendum -->` - Mark as appendix section
- `<!-- notoc -->` - Exclude from table of contents

### Automatic Numbering

Sections are numbered based on heading levels:

- `#` headings become level 1 sections (1, 2, 3...)
- `##` headings become level 2 sections (1.1, 1.2...)
- `###` headings become level 3 sections (1.1.1, 1.1.2...)

<!-- addendum -->
# API Reference

This appendix is marked with the `<!-- addendum -->` directive, making it a level 0 section with letter numbering (A).

The API includes methods for loading markdown files and rendering PDFs. See the main documentation for complete details.

<!-- addendum -->
# Configuration Examples

This is appendix B (another addendum section).

## Basic Example

```python
from docco import Document

doc = Document(
    title="Product Documentation",
    subtitle="Technical Guide",
    date="October 2025"
)

doc.load_from_markdown("content.md")
doc.render_pdf("output/doc.pdf", save_html=True)
```

## Advanced Example

```python
from docco import Document, Orientation

# Create document
doc = Document(
    title="Advanced Documentation",
    header_text="Custom Header"
)

# Load from markdown
doc.load_from_markdown("part1.md")

# Add manual sections
doc.add_section(
    level=1,
    title="Manual Section",
    content="This section was added programmatically.",
    orientation=Orientation.LANDSCAPE
)

# Load more markdown
doc.load_from_markdown("part2.md")

# Render
doc.render_pdf("output/advanced.pdf")
```

<!-- notoc -->
## Internal Development Notes

This section is marked with `<!-- notoc -->` so it won't appear in the table of contents, but will still be rendered in the PDF content.

This is useful for:
- Internal notes
- Draft sections
- Supplementary content not part of main document flow

### Implementation Status

- ✅ Markdown parsing
- ✅ Directive processing
- ✅ Orientation support
- ✅ TOC exclusion
- 🚧 Page break directive (planned)
- 🚧 Image optimization (planned)
