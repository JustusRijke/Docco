---
css:
  - "css/page.css"
  - "css/toc.css"
  - "css/header_footer.css"
  - "css/fonts.css"
  - "css/fancy.css"
---
<!-- inline:"header.html" title="Docco Feature Showcase" author="Docco Team" -->
<!-- inline:"footer.html" -->

# Docco: Feature Showcase

Welcome to this demonstration of Docco's capabilities. This document showcases all features through practical examples and explanations.

<nav data-toc-start="2" data-toc-end="4"></nav>

## Getting Started

### Frontmatter Configuration

YAML frontmatter at the beginning of the document (between `---` delimiters) configures document processing:

```yaml
---
css:
  - "css/page.css"
  - "css/toc.css"
multilingual: true
base_language: en
---
```

#### Supported Fields

**`css`** - CSS stylesheet(s) for PDF styling. Can be:

- Single file (string): `css: "style.css"`
- Multiple files (inline array): `css: ["page.css", "theme.css"]`
- Multiple files (multiline list):

  ```yaml
  css:
    - "css/page.css"
    - "css/toc.css"
  ```

- External CSS URLs (e.g., Google Fonts):

  ```yaml
  css:
    - "css/page.css"
    - "https://fonts.googleapis.com/css?family=Raleway:400,600&display=swap"
  ```

File paths are relative to the markdown file and are embedded in the generated HTML document within `<style>` tags.
External CSS URLs (starting with `http://` or `https://`) are included as `<link>` tags in the HTML, allowing WeasyPrint to fetch them during PDF generation.
This enables use of web fonts like Google Fonts directly in your PDF documents.

**`multilingual`** - Enable multilingual mode (boolean, default: `false`). When set to `true`, Docco automatically extracts translatable strings to a POT file and generates PDFs for the base language plus all discovered translations.

**`base_language`** - The language code of the source document (required when `multilingual: true`). Example: `base_language: en`. This will be used as the suffix for the base language PDF (e.g., `Document_EN.pdf`).

**`dpi`** - Maximum image resolution in dots per inch (integer, optional). Controls image downsampling in the generated PDF:

- Default (no `dpi` specified): Preserves original image resolution. High-quality images remain full resolution, which is excellent for print but may result in larger file sizes.
- `dpi: 300`: Recommended for professional printing. Images are downsampled to a maximum of 300 DPI, which is the industry standard for high-quality print output while keeping file sizes reasonable.
- `dpi: 150`: Suitable for screen viewing and digital distribution. Produces smaller files with adequate quality for on-screen reading.

Example:

```yaml
---
css: "style.css"
dpi: 300
---
```

**Note:** The DPI setting works most effectively when images have CSS constraints. For optimal file size reduction, include CSS rules like:

```css
img {
    max-width: 100%;
    height: auto;
}
```

**Automatic Validation:** When you specify a `dpi` value, Docco automatically validates the generated PDF and warns if any images fall below the specified DPI threshold.
This helps ensure your PDFs meet quality requirements before printing. For multilingual documents, only the base language PDF is validated.

This setting applies to all raster images (PNG, JPEG, etc.) embedded in the document. It does not affect vector graphics (SVG). If images are already at or below the specified DPI, they remain unchanged.

## Core Concepts

### Understanding Directives

Docco extends markdown with powerful **directives** - special HTML comments that trigger processing. Directives enable:

- File inclusion and composition with file-type awareness (.md, .html, .py)
- Dynamic content generation (via Python files)
- Page layout control
- Placeholder substitution

#### General Directive Rule

**Directives can appear anywhere in the document**, including in the middle of lines. However, directives inside code blocks (both inline `` `code` `` and fenced ``` ``` blocks) are **protected** and will not be processed.
This allows you to show directive syntax as examples in documentation without triggering them.

Example (this won't execute):

```markdown
<!-- inline:"file.md" -->
<!-- inline:"script.py" -->
```

This protection ensures compatibility with standard markdown parsing and allows you to safely demonstrate directive syntax in tutorials and documentation.

## Docco Directives

### Inline Content

The `inline` directive embeds external markdown or HTML files with optional placeholder substitution.

**Syntax:** `<!-- inline:"path/to/file" key1="value1" key2="value2" -->`

#### Basic Usage

All attributes after the file path become placeholders. For example, `author="Docco Team"` replaces all `{{author}}` occurrences in the inlined file:

<!-- inline:"inline/inlined_content.md" author="Docco Team" date="2025-10-26" -->

#### Recursive Inlining

Inlined files can themselves contain inline directives, enabling multi-level composition (up to 10 levels maximum to prevent infinite recursion). This allows modular document structures where content is composed from nested files.

#### Important: HTML Content and Indentation

When inlining HTML files, be aware that **all content is parsed as markdown**:

- **Leading indentation matters**: Lines starting with 4+ spaces are treated as code blocks. If your inlined HTML has indentation, it will be wrapped in `<code>` tags, breaking the structure.
- **Solution**: HTML files must start at column 0 (no leading indentation). Inline directives themselves should also not be indented.

Correct:

```markdown
<!-- inline:"header.html" -->
```

Incorrect:

```markdown
    <!-- inline:"header.html" -->
```

This follows the CommonMark specification for compatibility with standard markdown parsing.

### Table of Contents

Docco automatically generates a hierarchical, numbered table of contents (1, 1.1, 1.2, 1.2.1, etc.) using JavaScript when a `<nav>` element is present in the document.

#### Basic Usage

Add an empty `<nav>` element where you want the TOC to appear:

```markdown
<nav></nav>
```

By default, this includes all heading levels (h1-h6).

#### Configuring Heading Levels

Control which heading levels appear in the TOC using `data-toc-start` and `data-toc-end` attributes:

```markdown
<nav data-toc-start="2" data-toc-end="4"></nav>
```

This example includes only h2, h3, and h4 headings in the TOC.

#### Excluding Headings

To exclude a heading and all its sub-sections from the TOC, add `class="toc-ignore"`:

```markdown
## Normal Heading {.toc-ignore}
### This subsection is also excluded
## This heading is included
```

Headings outside the configured range (via `data-toc-start`/`data-toc-end`) or marked with `toc-ignore` will not be numbered.

### Page Layout

Control page breaks and orientation within your document using layout directives.

#### Page Breaks

The `<!-- pagebreak -->` directive starts a new page:

<!-- pagebreak -->

This section starts on a **new page** using the `<!-- pagebreak -->` directive. Use page breaks to organize content into logical sections with clear visual separation.

#### Orientation Control

The `<!-- landscape -->` and `<!-- portrait -->` directives control page orientation, useful for wide content like tables:

<!-- landscape -->

This section uses **landscape orientation** with the `<!-- landscape -->` directive, providing more horizontal space. The table overflows to a 2nd page.

{.table-borders}
| Q1 Revenue | Q1 Expenses | Q1 Profit | Q2 Revenue | Q2 Expenses | Q2 Profit | Q3 Revenue | Q3 Expenses | Q3 Profit | Q4 Revenue | Q4 Expenses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |

<!-- portrait -->

This section returns to **portrait orientation** using the `<!-- portrait -->` directive.

### Headers & Footers

Docco supports page headers and footers added via **inline directives**. Headers and footers are processed through the same pipeline as the main document, supporting:

- Placeholder substitution
- Dynamic content via Python files (`.py`)
- File inclusion with `<!-- inline -->` directives

#### Adding Headers & Footers

Include headers and footers at the beginning of your document using inline directives with placeholder attributes:

```markdown
<!-- inline:"header.html" title="Docco Feature Showcase" author="Docco Team" -->
<!-- inline:"footer.html" title="Docco" -->
```

The attributes replace `{{key}}` placeholders in the HTML files. For example, `title="My Title"` replaces all `{{title}}` instances.

#### CSS Requirements

Headers and footers require CSS Paged Media rules to position them on the page:

```css
@page {
    margin-top: 2.5cm;
    margin-bottom: 2.5cm;
    @top-center {
        content: element(header);
    }
    @bottom-center {
        content: element(footer);
    }
}
```

See `examples/css/header_footer.css` for a complete example.

#### Example Files

Docco provides example header and footer HTML files in the `examples/` folder:

- `examples/header.html` - Example page header with placeholder support
- `examples/footer.html` - Example page footer with directive support

Examine these files to understand the structure and create your own headers and footers with placeholders (e.g., `{{title}}`, `{{author}}`) and directives.

### Dynamic Content via Python Files

Python files (`.py`) can be inlined to generate dynamic content. When you inline a Python file, Docco executes it and inserts the stdout output into the document.

**Syntax:** `<!-- inline:"script.py" -->`

**Important:** Python file execution is disabled by default for security reasons. Use the `--allow-python` flag to enable it:

```bash
docco input.md -o output/ --allow-python
```

#### Example

File `examples/counter.py`:

```python
print("_", end='')
for i in range(10):
    print(i, end='')
print("_", end='')
```

Using `<!-- inline:"counter.py" -->` produces:
<!-- inline:"counter.py" -->

The output can contain other directives (markdown, inline files, etc.), enabling complex dynamic content generation.

#### Passing Arguments to Python Scripts

You can pass arguments to Python scripts via the inline directive. Arguments are available in `sys.argv`:

```markdown
<!-- inline:"script.py" count="10" name="test" -->
```

In your Python script:

```python
import sys
## sys.argv = ['script.py', 'count=10', 'name=test']
for arg in sys.argv[1:]:
    key, value = arg.split('=')
    print(f"{key}: {value}")
```

## Document Formatting

Docco relies on [MarkdownIt](https://markdown-it-py.readthedocs.io/en/latest/) for rendering markdown to HTML. It fully supports [CommonMark specs](https://spec.commonmark.org) with table support.
The [(block) attributes](https://mdit-py-plugins.readthedocs.io/en/latest/#attributes) plugin is also installed.

### Images with Styling

Add images using standard Markdown syntax and use `{}` attributes for styling:

`![](images/idea.svg){.icon}` defines an image with CSS class `icon` (styled in `css/fancy.css`):

![](images/idea.svg){.icon}

Or define styles directly: `![](images/idea.svg){style="width:2cm"}`

![](images/idea.svg){style="width:2cm"}

<!-- inline:"inline/callout.html" icon="images/idea.svg" content="Or, add an image with texxt using an inline function `examples/inline/callout.html`"-->

### Tables

Markdown tables organize tabular data with optional styling:

---

{.table-borders}
| A | B | C |
| ---- | ---- | ---- |
| Table | with borders | inside |

---

{.table-borders-outside}
| A | B | C |
| ---- | ---- | ---- |
| Table | with borders | outside |

---

| A | B | C |
| ---- | ---- | ---- |
| Table | without | borders |

---

### More Markdown Features

Explore additional markdown features: [https://markdown-it.github.io/](https://markdown-it.github.io/)

## Styling & Layout

### CSS for PDF Generation

Docco uses Chromium (via Playwright) with the Paged.js polyfill to convert HTML to PDF. This provides full modern CSS support including:

**Fully Supported:**

- All modern CSS features: Flexbox, Grid, Custom Properties, transforms, animations
- CSS Paged Media rules for headers, footers, and page styling
- Media queries and advanced selectors
- Web fonts (Google Fonts, custom fonts via `@font-face`)
- SVG rendering as vector graphics

**Best Practices:**

- Use CSS Paged Media rules (`@page`) for professional print layouts
- Leverage modern CSS features freely (Flexbox, Grid, custom properties)
- External fonts load via standard `<link>` tags in frontmatter CSS
- SVG images render as crisp vector graphics at any resolution

## Multilingual Documents

Create professional multilingual documents with automatic language-specific PDF generation.

### Automatic Multilingual Mode

Use the `multilingual: true` flag in frontmatter with `base_language` to automatically generate PDFs for the base language plus all available translations:

```yaml
---
multilingual: true
base_language: en
---
```

#### How It Works

When enabled, Docco will:

1. Extract a POT file to a `{document_name}/` subfolder
2. Discover all `.po` translation files in that subfolder
3. Generate a PDF for the base language (e.g., `Document_EN.pdf`)
4. Generate translated PDFs for each `.po` file (e.g., `Document_DE.pdf`, `Document_FR.pdf`)

**Example:** See `Multilingual_Document_Example.md` which generates:

- `Multilingual_Document_Example_EN.pdf`
- `Multilingual_Document_Example_DE.pdf`
- `Multilingual_Document_Example_NL.pdf`

### Manual Translation Workflow

For single-language builds with specific translations, use the `--po` flag:

```bash
docco myfile.md --po translations/de.po -o output/
```

This generates a single PDF with the specified translation applied.

### Professional Translation Workflow with POT/PO Files

Docco integrates with professional translation tools and services for enterprise workflows.

#### Step 1: Enable Multilingual Mode

Add to your frontmatter:

```yaml
---
multilingual: true
base_language: en
---
```

#### Step 2: Generate Initial PDFs and POT File

```bash
docco myfile.md -o output/
```

This automatically:

- Generates `myfile_EN.pdf` (base language)
- Creates `myfile/myfile.pot` (translation template)

File structure:

```text
myfile.md
myfile/
  └── myfile.pot        (template)
output/
  └── myfile_EN.pdf
```

#### Step 3: Create Language-Specific Translations

Translators create `.po` files for each language using professional tools:

- **poedit** (desktop application)
- **Weblate** (web-based, collaborative)
- **Crowdin, Lokalise, POEditor** (professional translation platforms)
- Any gettext-compatible tool

Place them in the `myfile/` directory:

```text
myfile.md
myfile/
  ├── myfile.pot        (template)
  ├── de.po             (German translation)
  ├── fr.po             (French translation)
  └── nl.po             (Dutch translation)
```

#### Step 4: Generate Multilingual PDFs

```bash
docco myfile.md -o output/
```

This automatically:

- Updates POT file
- Updates all existing PO files with new/changed strings
- Generates PDFs for all languages

```text
Extracted POT: myfile/myfile.pot
Updated de.po: 40 translated, 2 fuzzy, 5 untranslated
Updated fr.po: 38 translated, 1 fuzzy, 6 untranslated
Updated nl.po: 45 translated, 0 fuzzy, 0 untranslated
Processing base language: EN
Processing language: DE
WARNING - Translation incomplete for DE: 5 untranslated, 2 fuzzy
Processing language: FR
WARNING - Translation incomplete for FR: 6 untranslated, 1 fuzzy
Processing language: NL
Generated 4 output file(s)
```

#### Translation Maintenance

When the source document changes, simply run the same command:

```bash
docco myfile.md -o output/
```

Docco automatically:

- Updates POT file with new content
- Merges changes into all existing PO files
- Preserves existing translations
- Marks new strings as untranslated
- Marks changed strings for review (fuzzy)
- Regenerates all PDFs

This allows translators to focus only on new/modified content rather than re-translating the entire document.

## Conclusion

This document demonstrates all of Docco's core capabilities: configuration, directives, formatting, styling, and multilingual support. Use these features to create professional, multilingual documents with dynamic content and flexible layouts.

For more information, consult the main Docco documentation.
