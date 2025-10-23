# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Docco** is a Python-based PDF documentation generator that uses HTML/CSS for layout and WeasyPrint for rendering. The system generates professional A4 PDFs with automatic table of contents, hierarchical section numbering, and support for mixed portrait/landscape orientations.

### Core Architecture

The system follows a **3-stage pipeline**:

1. **Asset Preparation**: Optimize images with Pillow, save to `output/optimized_images/` (planned)
2. **Document Assembly**: Build complete HTML document via modular components
   - Manage hierarchical numbering (sections: `1.1.2`, addendums: `A`, `B`)
   - Convert Markdown fragments to HTML using markdown-it-py
   - Concatenate all content into single HTML string
3. **PDF Rendering**: Pass HTML + CSS to WeasyPrint for final PDF generation

### Key Design Principles

- **Modular Architecture**: Code organized into logical modules with clear responsibilities
- **Testability**: Unit and integration tests using pytest
- **CSS-Driven Layout**: All layout, typography, headers/footers defined via CSS (print styling)
- **Python String Construction**: HTML generation uses direct string concatenation, not templating engines
- **Programmatic Numbering**: Section numbers (`1`, `1.1`, `1.1.1`) and addendum letters (`A`, `B`) automatically managed

## Development Commands

### Running the Generator

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install package in editable mode (first time only)
pip install -e .

# Generate PDF using the example
python examples/basic_document.py

# Or use the CLI
docco build examples/basic_document.py
```

Output files are created in the `output/` directory:
- `output/debug.html` - Intermediate HTML for browser debugging
- `output/final.pdf` - Generated A4 PDF

### Environment Setup

```bash
# Install system dependencies (Debian/Ubuntu)
apt install weasyprint

# Install package with dependencies
pip install -e .

# Install development dependencies (for testing, linting)
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=docco --cov-report=html

# Run specific test file
pytest tests/unit/test_section.py

# Run specific test
pytest tests/unit/test_section.py::TestSectionNumberer::test_hierarchical_numbering
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Debugging Layout Issues

1. Run the example with `python examples/basic_document.py`
2. Open `output/debug.html` in a browser to verify layout before PDF conversion
3. Modify CSS in `src/docco/rendering/css_builder.py`
4. Re-run to see changes

## Project Structure

```
Docco/
├── src/
│   └── docco/
│       ├── __init__.py              # Package exports
│       ├── core/
│       │   ├── document.py          # Document class (main orchestrator)
│       │   └── section.py           # Section model and numbering logic
│       ├── content/
│       │   └── markdown.py          # Markdown to HTML conversion
│       └── rendering/
│           ├── html_builder.py      # HTML document generation
│           ├── css_builder.py       # CSS generation
│           └── pdf_renderer.py      # WeasyPrint wrapper
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests for individual modules
│   │   ├── test_section.py
│   │   ├── test_markdown.py
│   │   └── test_html_builder.py
│   └── integration/                 # Integration tests
│       └── test_document.py
├── examples/
│   └── basic_document.py            # Example document generation
├── output/                          # Generated files (gitignored)
├── pyproject.toml                   # Package configuration
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md                        # Full technical specification
```

### Module Responsibilities

#### `docco.core.document` (document.py)
- **Document class**: Main API for building PDFs
- Coordinates section numbering, HTML building, and PDF rendering
- Methods: `add_section()`, `build_html()`, `render_pdf()`

#### `docco.core.section` (section.py)
- **Section dataclass**: Represents a document section
- **SectionNumberer class**: Automatic hierarchical numbering
- Supports regular sections (1, 1.1, 1.1.1) and addendums (A, B, C)

#### `docco.content.markdown` (markdown.py)
- **MarkdownConverter class**: Wrapper around markdown-it-py
- Converts Markdown to HTML with inline and block modes

#### `docco.rendering.html_builder` (html_builder.py)
- **HTMLBuilder class**: Constructs HTML documents
- Builds title pages, table of contents, and content sections
- Handles HTML escaping and ID generation

#### `docco.rendering.css_builder` (css_builder.py)
- **CSSBuilder class**: Generates CSS for PDF layout
- Default A4 portrait styling with customization options

#### `docco.rendering.pdf_renderer` (pdf_renderer.py)
- **PDFRenderer class**: WeasyPrint wrapper
- Converts HTML+CSS to PDF files or bytes

#### `docco.cli` (cli.py)
- **CLI commands**: `docco build`, `docco version`
- Executes Python scripts that build documents

## Current Implementation Status

**Phase 2** (Current): Modular architecture with testing
- ✅ Modular package structure
- ✅ Unit and integration tests
- ✅ CLI interface (`docco build`)
- ✅ Automatic section numbering
- ✅ Addendum sections (level=0)
- ✅ PDF output with headers/footers
- ✅ WeasyPrint TOC generation (CSS-based)

**Not Yet Implemented**:
- Phase 3: Image optimization/embedding, mixed orientations
- Phase 4: Reusable content modules, template system

## Using Docco

### Basic Example

```python
from docco import Document

# Create document
doc = Document(
    title="My Documentation",
    subtitle="Technical Guide",
    date="2025-10-23"
)

# Add sections
doc.add_section(
    level=1,
    title="Introduction",
    content="This is the **introduction** with *markdown*."
)

doc.add_section(
    level=2,
    title="Details",
    content="""
More details here:
- Point 1
- Point 2
"""
)

# Generate PDF
doc.render_pdf("output/my_doc.pdf", save_html=True)
```

### Section Levels

- **Level 1**: Top-level sections (numbered 1, 2, 3, ...)
- **Level 2**: Subsections (numbered 1.1, 1.2, 2.1, ...)
- **Level 3**: Sub-subsections (numbered 1.1.1, 1.1.2, ...)
- **Level 0**: Addendum sections (lettered A, B, C, ...)

### Markdown Support

Content uses markdown-it-py for parsing. Supported features:
- Bold, italic, links
- Ordered and unordered lists
- Tables
- Code blocks and inline code
- Paragraphs

### CSS Customization

CSS is generated by `CSSBuilder.generate_default_css()` and includes:
- `@page` rules for A4 setup, headers/footers
- `.title-page` - Title page styling
- `.toc-page` - Table of contents
- `.content` sections with h1/h2/h3 styling
- Table, list, and inline formatting

Custom CSS can be provided to `render_pdf()`:

```python
from docco.rendering.css_builder import CSSBuilder

custom_css = CSSBuilder.generate_custom_css(
    header_text="My Custom Header",
    font_family='"Times New Roman", serif'
)

doc.render_pdf("output/doc.pdf", css=custom_css)
```

## Important Technical Details

### WeasyPrint TOC Generation

The system uses WeasyPrint's built-in CSS Paged Media support for automatic TOC:
- Sections must have `class="section"` and appropriate heading level
- `bookmark-level` and `bookmark-label` CSS properties control TOC entries
- `target-counter(attr(href), page)` generates page numbers

### Section Numbering Strategy

Section numbering is fully automatic:
- **SectionNumberer** maintains hierarchical counters `[level1, level2, level3]`
- When adding a section, increment counter at that level
- Reset all deeper level counters
- Addendum sections (level=0) use separate letter counter

Example flow:
- Section level=1 → "1" (counters: [1, 0, 0])
- Section level=2 → "1.1" (counters: [1, 1, 0])
- Section level=2 → "1.2" (counters: [1, 2, 0])
- Section level=1 → "2" (counters: [2, 0, 0])
- Section level=0 → "A" (addendum counter: 1)

### Testing Strategy

**Unit tests** verify individual components:
- Section numbering logic
- Markdown conversion
- HTML generation
- CSS generation

**Integration tests** verify full workflows:
- Complete document building
- PDF generation
- Complex multi-level documents

Run tests with `pytest` after installing dev dependencies.

### Mixed Orientations (Planned)

Documents will support both portrait and landscape pages via CSS `@page` selectors targeting specific sections.

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
- Test coverage should remain high (aim for >80%)
