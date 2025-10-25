# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Docco** is a pure CLI tool that converts Markdown files (with YAML frontmatter) and CSS stylesheets into professional A4 PDFs. The system uses markdown-it-py for parsing and WeasyPrint for PDF rendering.

### Core Architecture

The system follows a **simple pipeline**:

1. **Parse Frontmatter**: Extract metadata (languages, no_headers_first_page)
2. **Process Content**: Filter by language, expand custom commands, convert Markdown to HTML
3. **Build Document**: Generate TOC, number sections, wrap with orientation classes, inject headers/footers
4. **Render PDF**: Pass HTML + CSS to WeasyPrint for each language variant

### Key Design Principles

- **Pure CLI Tool**: No Python API - users interact only via command line
- **External Assets**: CSS is completely external (not embedded in code)
- **Expert-Friendly**: Designed for users comfortable with Markdown and CSS
- **Simple Architecture**: Minimal abstractions, easy to understand
- **Separation of Concerns**: Content (Markdown) and layout (CSS) are completely separated
- **Multilingual Support**: Single markdown file generates multiple language-specific PDFs

## Development Commands

### Running the CLI

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install package in editable mode (first time only)
pip install -e .

# Generate PDF from examples
docco build examples/Feature\ Showcase.md examples/style.css

# Generate multilingual PDFs
docco build examples/Multilingual\ Example.md examples/style.css
```

Output files are created in `output/` directory:
- `<filename>.pdf` - Generated A4 PDF (single language)
- `<filename>_EN.pdf`, `<filename>_DE.pdf`, etc. - Language-specific PDFs (multilingual)
- `debug.html` or `debug_EN.html` - Intermediate HTML for browser debugging

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
pytest tests/unit/test_cli.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Debugging Layout Issues

1. Run docco build with your markdown and CSS files
2. Open the generated `debug.html` in a browser to verify layout before PDF conversion
3. Modify your CSS file
4. Re-run docco build to see changes

## Project Structure

```
Docco/
├── src/
│   └── docco/
│       ├── __init__.py              # Package exports
│       ├── cli.py                   # CLI entry point with build command
│       ├── content/
│       │   ├── markdown.py          # Markdown to HTML conversion
│       │   ├── commands.py          # Custom command processor
│       │   └── language_filter.py   # Language filtering for multilingual docs
│       └── rendering/
│           ├── pdf_renderer.py      # WeasyPrint wrapper
│           └── headers_footers.py   # Header/footer template system
├── tests/
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests
│   │   ├── test_cli.py              # CLI tests
│   │   ├── test_markdown.py         # Markdown conversion tests
│   │   ├── test_commands.py         # Command processor tests
│   │   ├── test_language_filter.py  # Language filter tests
│   │   └── test_headers_footers.py  # Header/footer tests
│   └── integration/                 # Integration tests
│       └── test_pdf_generation.py   # End-to-end PDF generation tests
├── examples/
│   ├── Feature Showcase.md          # Example with all features
│   ├── Multilingual Example.md      # Multilingual example
│   ├── style.css                    # Example stylesheet
│   ├── commands/                    # Custom command templates
│   │   └── callout.html             # Callout box template
│   ├── header.html                  # Default header template
│   ├── footer.html                  # Default footer template
│   ├── header.EN.html, etc.         # Language-specific headers
│   ├── footer.EN.html, etc.         # Language-specific footers
│   └── images/                      # Image assets
├── output/                          # Generated files (gitignored)
├── pyproject.toml                   # Package configuration
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
└── README.md                        # User documentation
```

### Module Responsibilities

#### `docco.cli` (cli.py)
- **CLI commands**: `docco build`, `docco version`
- Parses YAML frontmatter (languages, no_headers_first_page)
- Orchestrates multilingual PDF generation loop
- Builds HTML documents with TOC, section numbering, orientation wrappers
- Processes directives: `<!-- TOC -->`, `<!-- pagebreak -->`, `<!-- landscape -->`, `<!-- portrait -->`, `<!-- addendum -->`
- Handles image path resolution and figure/figcaption wrapping
- Helper functions: `_parse_frontmatter()`, `_build_html_from_markdown()`, `_parse_sections()`, `_build_toc()`, `_escape_html()`

#### `docco.content.markdown` (markdown.py)
- **MarkdownConverter class**: Wrapper around markdown-it-py
- Converts Markdown to HTML with inline and block modes

#### `docco.content.commands` (commands.py)
- **CommandProcessor class**: Custom command expansion system
- Parses `<!-- cmd: name args -->` syntax in markdown
- Loads HTML templates from `commands/` folder
- Substitutes `{{variables}}` with command arguments and content

#### `docco.content.language_filter` (language_filter.py)
- **LanguageFilter class**: Filters markdown by language tags
- Processes `<!-- lang:XX -->...<!-- /lang -->` blocks
- Keeps untagged content in all languages, removes non-matching tagged content

#### `docco.rendering.pdf_renderer` (pdf_renderer.py)
- **PDFRenderer class**: WeasyPrint wrapper with executable fallback
- Converts HTML+CSS to PDF files or bytes
- Automatically uses `weasyprint` executable if Python library unavailable (Windows support)

#### `docco.rendering.headers_footers` (headers_footers.py)
- **HeaderFooterProcessor class**: Manages header/footer templates
- Loads `header.html`, `footer.html`, or language-specific variants (e.g., `header.EN.html`)
- Replaces variables (`{{filename}}`, `{{language}}`) in templates
- Injects running elements into HTML document
- **modify_css_for_running_elements()**: Modifies CSS to use element(header) and element(footer)
- Detects conflicts with existing @page content rules and warns
- Respects `no_headers_first_page` flag (default: True)

## Features

### Complete Feature Set

- ✅ CLI interface (`docco build <md> <css>`)
- ✅ YAML frontmatter parsing (languages, no_headers_first_page)
- ✅ Markdown to HTML conversion (headings, bold, italic, lists, tables, code, links)
- ✅ External CSS support (no embedded CSS)
- ✅ PDF output with WeasyPrint
- ✅ Debug HTML generation
- ✅ Table of contents generation with section numbers and `<!-- TOC -->` placement directive
- ✅ Manual page breaks with `<!-- pagebreak -->` directive
- ✅ Automatic section numbering (1, 1.1, 1.2.3, etc.)
- ✅ Addendum sections with letter numbering (A, B, C)
- ✅ Mixed portrait/landscape orientations (`<!-- landscape -->`, `<!-- portrait -->`)
- ✅ Custom commands system (`<!-- cmd: name args -->...<!-- /cmd -->`)
- ✅ Headers and footers system with variable substitution
- ✅ Language-specific headers/footers (header.EN.html, footer.DE.html, etc.)
- ✅ Multilingual document support (`languages: EN DE NL` in frontmatter)
- ✅ Language filtering (`<!-- lang:XX -->...<!-- /lang -->`)
- ✅ Image path resolution and figure/figcaption wrapping
- ✅ Unit and integration tests

## Using Docco

### Basic Example

Create a markdown file with YAML frontmatter:

```markdown
# Introduction

This is the **introduction** with *markdown*.

## Details

- Point 1
- Point 2
```

Create a CSS file:

```css
@page {
    size: A4 portrait;
    margin: 25mm;
}

.toc-page {
    page-break-after: always;
}

.page-number::after {
    content: counter(page);
}
```

Generate PDF:

```bash
docco build document.md style.css --output output/my_doc.pdf
```

### YAML Frontmatter

Optional fields:
- `languages`: Space-separated language codes (e.g., `EN DE NL`) for multilingual PDFs
- `no_headers_first_page`: Boolean (default: true) - whether to skip headers/footers on first page

### Markdown Features

Content uses markdown-it-py for parsing. Supported features:
- Bold, italic, links
- Ordered and unordered lists
- Tables
- Code blocks and inline code
- Paragraphs
- Headings (H1, H2, H3)
- Images with automatic path resolution and figure/figcaption wrapping

### Section Numbering and TOC

- All H1, H2, H3 headings are automatically numbered (1, 1.1, 1.2.3, etc.)
- Table of Contents is automatically generated from headings
- Use `<!-- TOC -->` directive to control where the TOC appears in the document
- If `<!-- TOC -->` is not specified, TOC is automatically inserted at the beginning
- Use `<!-- addendum -->` before a heading to create appendix sections (A, B, C)

**Example TOC placement:**

```markdown
<div class="title-page">
<h1>Document Title</h1>
</div>

<!-- TOC -->

# Introduction
```

### Page Breaks

Insert manual page breaks anywhere in the document:

```markdown
Some content here.

<!-- pagebreak -->

This content starts on a new page.
```

The `<!-- pagebreak -->` directive inserts a page break at that exact location.

### Orientation Control

Use HTML comments to control page orientation:

```markdown
<!-- landscape -->
# Wide Section

This content appears in landscape orientation.

<!-- portrait -->
# Normal Section

Back to portrait orientation.
```

### Custom Commands

Users can define reusable HTML components via template files in a `commands/` folder:

**Syntax:**
```markdown
<!-- cmd: callout icon="idea.svg" -->
Content here (can include markdown)
<!-- /cmd -->
```

Or self-closing: `<!-- cmd: name arg="val" /-->`

**Template location:** `commands/` folder relative to markdown file (e.g., `examples/commands/callout.html`)

**Template format:**
```html
<div class="callout">
  <img src="{{icon}}" />
  {{content}}
</div>
```

**Variables:**
- `{{content}}` - body between tags
- `{{arg_name}}` - command arguments
- Not HTML-escaped
- Missing variables become empty strings

**Processing:** Commands are expanded before markdown conversion, so content can contain markdown.

### Multilingual Documents

Generate language-specific PDFs from a single markdown file:

**Frontmatter:**
```yaml
---
languages: EN DE NL
---
```

**Language tags in content:**
```markdown
This text appears in all languages.

<!-- lang:EN -->
This text only appears in the English PDF.
<!-- /lang -->

<!-- lang:DE -->
Dieser Text erscheint nur im deutschen PDF.
<!-- /lang -->
```

**Output:**
- `output/document_EN.pdf`
- `output/document_DE.pdf`
- `output/document_NL.pdf`

### Headers and Footers

Headers and footers can be defined using optional `header.html` and `footer.html` files in the same directory as the markdown file.

**File location:** Same directory as the markdown file (e.g., `examples/header.html`)

**Language-specific variants:** `header.EN.html`, `footer.DE.html`, etc. (falls back to `header.html`/`footer.html`)

**Variable replacements:**
- `{{filename}}` - Markdown filename without path/extension
- `{{language}}` - Language code (for multilingual documents)

**Example header.html:**
```html
<div style="font-size: 9pt; color: #666;">
    {{filename}}
</div>
```

**Example footer.html:**
```html
<div class="page-number" style="font-size: 9pt; color: #666;"></div>
```

**Page numbers:** Use the `.page-number` class with a CSS `::after` pseudo-element:
```css
.page-number::after {
    content: counter(page);
}
```

**Behavior:**
- If header.html exists, docco automatically injects `@top-center { content: element(header); }` into all `@page` rules
- If footer.html exists, docco automatically injects `@bottom-right { content: element(footer); }` into all `@page` rules
- Existing `@page` content rules are replaced with warnings
- First page headers/footers controlled by `no_headers_first_page` frontmatter flag (default: true, meaning no headers on first page)

### CSS Customization

All layout and styling is controlled via the external CSS file:
- `@page` rules for A4 setup, margins, orientation
- `.toc-page` - TOC page styling
- `.content` - Content wrapper
- `.section-wrapper.portrait` / `.section-wrapper.landscape` - Orientation-specific styling
- Standard HTML selectors (h1, h2, h3, p, table, figure, figcaption, etc.)

Users provide their own CSS file - there is no default embedded CSS.

## Important Technical Details

### YAML Frontmatter Parsing

The CLI parses YAML frontmatter delimited by `---`:
- Frontmatter must be at the start of the file
- Must have opening and closing `---` delimiters
- All fields are optional
- Invalid YAML raises an error

### HTML Generation

HTML is built in the CLI module using string operations:
- Custom commands are expanded before markdown conversion
- Content is filtered by language (for multilingual docs)
- Markdown content is converted to HTML by MarkdownConverter
- Sections are parsed with orientation directives
- TOC is generated from headings with automatic numbering
- Images are resolved and wrapped in figure/figcaption elements
- Headers/footers are injected as running elements
- Complete document structure includes `<!DOCTYPE>`, `<html>`, `<head>`, `<body>`

### PDF Rendering

WeasyPrint converts HTML + CSS to PDF:
- Supports CSS Paged Media (`@page` rules)
- Handles headers, footers, page numbers via CSS running elements
- First page headers/footers controlled by `no_headers_first_page` flag
- Debug HTML is saved for troubleshooting

### Testing Strategy

**Unit tests** verify individual components:
- YAML frontmatter parsing
- HTML escaping
- Section parsing and numbering
- Language filtering
- Custom command processing
- Header/footer template loading and variable substitution
- CLI command execution
- Error handling

**Integration tests** verify full workflows:
- Complete PDF generation
- Multilingual document generation
- Default output paths

Run tests with `pytest` after installing dev dependencies.

## Coding Guidelines

- Focus on maintainability over automation complexity
- Code should be understandable years later
- All dependencies must be open source with permissive licenses
- Target rendering time: <10 seconds for ~50 page documents
- Test coverage should remain high (aim for >80%)
- Use short/concise git commit messages, try to condense it in 1 or 2 lines
- Do not add generated with / co-authored with claude section to the git commit message
- When rewriting code, always try reduce LOC and bloat
- When adding code or documentation or examples, stick to the bare minimum, do not add more than asked. Keep it light-weight & simple. KISS & DRY all the way.
- Refer to the official [WeasyPrint API documentation](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html) and [WeasyPrint common use cases](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html)
- See `examples/CLAUDE.md` for example-specific guidelines

# IMPORTANT
- Always update README.md and CLAUDE.md after any code change. These files always need to be up-to-date and in-sync with the project.
