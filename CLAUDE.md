# CLAUDE.md

Guidance for working with this repository.

## Project Overview

**Docco** is a CLI tool that converts Markdown documents (with YAML frontmatter) into professional PDFs. Key capabilities:

- Markdown parsing with YAML frontmatter configuration
- Inline file inclusion with placeholder substitution
- CSS styling with support for external fonts (Google Fonts, etc.)
- Automatic table of contents with heading numbering
- Page layout control (breaks, orientation, headers, footers)
- Professional translation workflows with POT/PO files
- Dynamic content via Python code execution (opt-in)

Target audience: developers and technical writers familiar with Markdown, HTML, and CSS.

`examples/Feature_Showcase.md` demonstrates all features with detailed explanations.

## Architecture

Processing pipeline:

1. **Frontmatter Parsing** (`core.py`): Extracts YAML metadata and document body, validates frontmatter keys (warns about unknown keys)
2. **Directive Processing** (`parser.py`): Iteratively processes inline directives with file-type aware post-processing
3. **Inline Processing** (`inline.py`): Embeds external files via `<!-- inline:"path" -->` directives; .md files inlined as-is, .html files trimmed, .py files executed (recursive, max depth 10)
4. **HTML Conversion** (`core.py`): Converts markdown to HTML; collects CSS from frontmatter (files are embedded in `<style>` tags, external URLs become `<link>` tags)
5. **Translation Application** (`translation.py`): Optionally applies PO file translations to HTML
6. **TOC Generation** (`toc.py`): Generates table of contents with automatic heading numbering
7. **Page Layout** (`page_layout.py`): Applies page layout directives (pagebreak, landscape/portrait)
8. **PDF Generation** (`pdf.py`): Renders HTML to PDF with CSS support (both embedded and external CSS)
9. **PDF Validation** (`pdf_validation.py`): Optionally validates image DPI in generated PDF (when `dpi` frontmatter is set)

Main entry point: `parse_markdown()` in `parser.py`. CLI orchestration in `cli.py`.

### CSS Handling

The `collect_css_content()` function in `pdf.py` separates CSS sources:

- **File-based CSS**: Relative paths are read and embedded in `<style>` tags in the HTML head
- **External CSS URLs**: URLs (http:// or https://) are added as `<link>` tags, allowing WeasyPrint to fetch them (enables Google Fonts and other web fonts)

### Translation Workflow

**Single-language documents:**
- Generate PDF: `docco input.md -o output/`
- With translation: `docco input.md --po translations/de.po -o output/`

**Multilingual documents** (with `multilingual: true` in frontmatter):
- Simply run: `docco input.md -o output/`
- Automatically extracts POT file to `<basename>/<basename>.pot`
- Automatically updates all existing PO files in that directory with new/changed strings
- Generates PDFs for base language + all translated languages
- Reports translation completeness: `Updated de.po: 40 translated, 2 fuzzy, 3 untranslated`
- Warns about incomplete translations: `WARNING - Translation incomplete for DE: 5 untranslated, 2 fuzzy`

**Translation process:**
1. Set `multilingual: true` and `base_language: en` in frontmatter
2. Run `docco input.md -o output/` - generates POT file and base language PDF
3. Translators create/update language-specific PO files (e.g., `de.po`, `fr.po`) in the `<basename>/` directory using CAT tools
4. Run `docco input.md -o output/` again - automatically updates PO files and generates all language PDFs

Notes:
- POT/PO files contain HTML (not Markdown) - translators must preserve HTML tags
- Extracts strings from final HTML, enabling translation of dynamic content (TOC, page elements)
- Applies translations before TOC generation so headings are numbered in target language
- Integrates with CAT tools supporting HTML

### Frontmatter Validation

Known frontmatter keys are validated during parsing:
- `css` - CSS stylesheet paths or URLs (string or list)
- `dpi` - Maximum image resolution for PDF output (integer)
- `multilingual` - Enable multilingual mode (boolean)
- `base_language` - Base language code for multilingual documents (string)

Unknown keys trigger a warning but don't prevent processing. This allows users to include custom metadata while being notified of potential typos.

## Development Commands

### Setup

```bash
pip install -e ".[dev]"
```

### Running

```bash
# Generate PDF
docco input.md -o output_dir

# Verbose output
docco input.md -o output_dir -v

# Keep intermediate files (for debugging)
docco input.md -o output_dir --keep-intermediate

# With translation (single-language mode)
docco input.md --po translations/de.po -o output/

# Allow Python code execution (security-sensitive)
docco input.md --allow-python -o output/

# Multilingual mode (set multilingual: true in frontmatter)
# Automatically extracts POT, updates PO files, generates all language PDFs
docco input.md -o output/
```

### Testing

```bash
# Lint
ruff check .

# Run all tests
pytest

# Run specific test file
pytest tests/test_frontmatter.py

# Run with coverage
pytest --cov=src/docco --cov-report=term-missing

# Build example PDFs
docco examples/Feature_Showcase.md -o output/ --allow-python
docco examples/Multilingual_Document_Example.md -o output/ --allow-python
```

## Dependencies

- **python-frontmatter**: YAML frontmatter parsing
- **pyyaml**: YAML library (used by python-frontmatter)
- **markdown-it-py**: Markdown to HTML conversion
- **mdit-py-plugins**: Markdown-it plugins (attributes support)
- **weasyprint**: HTML to PDF generation
- **translate-toolkit**: HTML to POT/PO file conversion
- **polib**: PO file manipulation
- **colorlog**: Colored terminal output
- **pymupdf**: PDF image DPI validation
- **pytest**: Testing framework
- **pytest-cov**: Coverage measurement
- **ruff**: Code linting

## File Structure

```
src/docco/
  cli.py              - CLI argument parsing and commands
  parser.py           - Main pipeline orchestration (includes preprocess_document)
  inline.py           - Inline directive processing with file-type aware handlers (.md, .html, .py)
  core.py             - Frontmatter parsing, validation, markdown/HTML conversion
  pdf.py              - CSS collection and HTML to PDF rendering
  pdf_validation.py   - PDF image DPI validation
  toc.py              - Table of contents generation with heading numbering
  page_layout.py      - Page break and orientation directives
  translation.py      - PO file application and POT extraction
  logging_config.py   - Colored logging configuration

examples/
  Feature_Showcase.md                 - Comprehensive feature demo
  Multilingual_Document_Example.md    - Translation workflow example
  css/                                - Stylesheet examples
  header.html, footer.html            - Page template examples
  inline/                             - Reusable inline content
```

## Coding Guidelines

- Test-driven development: write tests before implementation
- Minimize code: KISS & DRY principles
- Sparse comments (complex logic only); minimal docstrings
- Target 100% test coverage
- Short, concise commit messages (1-2 lines), omit "Generated with" and "Co-Authored-By" Claude bloat.
- No edge case tests unless critical
- References:
  - [markdown-it docs](https://markdown-it-py.readthedocs.io/)
  - [weasyprint docs](https://doc.courtbouillon.org/weasyprint/stable/)
  - [translate-toolkit docs](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/)
- **Important**: After any feature change, update `examples/Feature_Showcase.md` and rebuild regression test baselines:
  ```bash
  docco examples/Feature_Showcase.md -o tests/output/ --allow-python
  docco examples/Multilingual_Document_Example.md -o tests/output/ --allow-python
  cp tests/output/*.pdf tests/baselines/
  ```
- Prefer fail-fast: avoid over-defensive exception handling. Silently failing code is unacceptable.
- When adding new dependencies (python libraries), make sure they are recently maintained
- Keep git commit messages clean and concise, not more than 2 lines
- When committing, always ask before reverting changes