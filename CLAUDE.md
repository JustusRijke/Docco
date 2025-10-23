# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Docco** is a Python-based PDF documentation generator that uses HTML/CSS for layout and WeasyPrint for rendering. The system generates professional A4 PDFs with automatic table of contents, hierarchical section numbering, and support for mixed portrait/landscape orientations.

### Core Architecture

The system follows a **3-stage pipeline**:

1. **Asset Preparation**: Optimize images with Pillow, save to `output/optimized_images/`
2. **Document Assembly**: Build complete HTML document via Python string construction
   - Manage hierarchical numbering (sections: `1.1.2`, addendums: `A`, `B`)
   - Convert Markdown fragments to HTML using markdown-it-py
   - Concatenate all content into single HTML string
3. **PDF Rendering**: Pass HTML + CSS to WeasyPrint for final PDF generation

### Key Design Principles

- **Simplicity First**: Keep code explicit and readable with no unnecessary abstraction layers
- **Single-Script Architecture**: Currently implemented as `main.py` with supporting content modules
- **CSS-Driven Layout**: All layout, typography, headers/footers defined via CSS (print styling)
- **Python String Construction**: HTML generation uses direct string concatenation/f-strings, not templating engines
- **Programmatic Numbering**: Section numbers (`1`, `1.1`, `1.1.1`) and addendum letters (`A:`, `B:`) managed by Python logic

## Development Commands

### Running the Generator

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Generate PDF from current document definition
python main.py
```

Output files are created in the `output/` directory:
- `output/debug.html` - Intermediate HTML for browser debugging
- `output/final.pdf` - Generated A4 PDF

### Environment Setup

```bash
# Install system dependencies (Debian/Ubuntu)
apt install weasyprint

# Install Python dependencies
pip install weasyprint markdown-it-py pillow

# Or if requirements.txt exists
pip install -r requirements.txt
```

### Debugging Layout Issues

1. Run `python main.py` to generate both HTML and PDF
2. Open `output/debug.html` in a browser to verify layout before PDF conversion
3. Modify CSS in `generate_css()` function (main.py:132)
4. Re-run to see changes

## Project Structure

```
/home/justusr/Repos/Docco/
├── main.py              # Main script: content → HTML → PDF pipeline
├── output/              # Generated files (HTML debug, PDF output, optimized images)
├── README.md            # Full technical specification
└── .venv/               # Python virtual environment
```

### Planned Structure (Not Yet Implemented)

The README.md describes a future architecture with:
- `content/` - Reusable content modules (disclaimers, standard sections)
- `assets/style.css` - Separate CSS file
- `assets/images/` - Source images for documents

Currently everything is in `main.py` as Phase 1 implementation.

## Current Implementation Status

**Phase 1** (Current): Minimal working example
- Single portrait A4 pages
- Basic Markdown conversion
- Section numbering (manual in data structure)
- PDF output with headers/footers
- WeasyPrint TOC generation (CSS-based)

**Not Yet Implemented**:
- Phase 2: Image optimization/embedding, mixed orientations
- Phase 3: Addendum sections, reusable content modules
- Phase 4: Refactoring into separate modules

## Content Authoring

### Adding Sections

Sections are defined in the `sections` list within `build_document()` (main.py:27-85):

```python
{
    "level": 1,        # Heading level (1-3)
    "number": "1.2",   # Section number (manually assigned)
    "title": "Section Title",
    "content": """
Markdown content here with **bold**, *italic*, lists, tables, etc.
"""
}
```

### Markdown Support

Content uses markdown-it-py for parsing. Supported features:
- Bold, italic, links
- Ordered and unordered lists
- Tables (basic, nested tables planned)
- Code blocks

### CSS Customization

CSS is defined in `generate_css()` (main.py:132-304) and includes:
- `@page` rules for A4 setup, headers/footers
- `.title-page` - Title page styling
- `.toc-page` - Table of contents
- `.content` sections with h1/h2 styling
- Table, list, and inline formatting

## Important Technical Details

### WeasyPrint TOC Generation

The system uses WeasyPrint's built-in CSS Paged Media support for automatic TOC:
- Sections must have class="section" and appropriate heading level
- `bookmark-level` and `bookmark-label` properties control TOC entries
- `target-counter(attr(href), page)` generates page numbers (currently not fully working in Phase 1)

### Section Numbering Strategy

Section numbers are **manually managed** in the current Phase 1 implementation. Future phases will implement:
- Hierarchical counter tracking (e.g., `[1, 1, 2]` for section 1.1.2)
- Separate letter-based counter for addendum sections
- Automatic number injection into HTML heading tags

### Mixed Orientations (Planned)

Documents must support both portrait and landscape pages (e.g., for technical drawings in addendums). This will be implemented via CSS `@page` selectors targeting specific sections.

### Image Handling (Planned)

- Resize images to ~300px width using Pillow
- Optimize before embedding to control PDF file size
- Support captions via `<figure>` and `<figcaption>` HTML tags

## Design Constraints

- Documents are small (~50 pages max), so performance optimization is not a priority
- Focus on maintainability over automation complexity
- Code should be understandable years later
- All dependencies must be open source with permissive licenses
- Target rendering time: <10 seconds for ~50 page documents
