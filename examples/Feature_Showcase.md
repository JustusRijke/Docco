---
css:
  - "css/page.css"
  - "css/toc.css"
  - "css/header_footer.css"
  - "css/fancy.css"
---
<!-- inline:"header.html" title="Docco Feature Showcase" author="Docco Team" -->
<!-- inline:"footer.html" -->


<!-- toc:exclude -->
# Docco: Feature Showcase

Welcome to this demonstration of Docco's capabilities. This document showcases all features through practical examples and explanations.

<!-- TOC -->

# Getting Started

## Frontmatter Configuration

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

### Supported Fields

**`css`** - CSS stylesheet(s) for PDF styling. Can be:
- Single file (string): `css: "style.css"`
- Multiple files (inline array): `css: ["page.css", "theme.css"]`
- Multiple files (multiline list):
  ```yaml
  css:
    - "css/page.css"
    - "css/toc.css"
  ```

Paths are relative to the markdown file. CSS is embedded in the generated HTML document within `<style>` tags, making the HTML self-contained and independent.

**`multilingual`** - Enable multilingual mode (boolean, default: `false`). When set to `true`, Docco automatically extracts translatable strings to a POT file and generates PDFs for the base language plus all discovered translations.

**`base_language`** - The language code of the source document (required when `multilingual: true`). Example: `base_language: en`. This will be used as the suffix for the base language PDF (e.g., `Document_EN.pdf`).

# Core Concepts

## Understanding Directives

Docco extends markdown with powerful **directives** - special HTML comments that trigger processing. Directives enable:
- File inclusion and composition
- Dynamic content generation
- Page layout control
- Placeholder substitution
- Python code execution

### General Directive Rule

**Directives can appear anywhere in the document**, including in the middle of lines. However, directives inside code blocks (both inline `` `code` `` and fenced ``` ``` blocks) are **protected** and will not be processed. This allows you to show directive syntax as examples in documentation without triggering them.

Example (this won't execute):
```
<!-- inline:"file.md" -->
<!-- python -->print("hello")<!-- /python -->
```

This protection ensures compatibility with standard markdown parsing and allows you to safely demonstrate directive syntax in tutorials and documentation.

# Docco Directives

## Inline Content

The `inline` directive embeds external markdown or HTML files with optional placeholder substitution.

**Syntax:** `<!-- inline:"path/to/file" key1="value1" key2="value2" -->`

### Basic Usage

All attributes after the file path become placeholders. For example, `author="Docco Team"` replaces all `{{author}}` occurrences in the inlined file:

<!-- inline:"inline/inlined_content.md" author="Docco Team" date="2025-10-26" -->

### Recursive Inlining

Inlined files can themselves contain inline directives, enabling multi-level composition (up to 10 levels maximum to prevent infinite recursion). This allows modular document structures where content is composed from nested files.

### Important: HTML Content and Indentation

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

## Table of Contents

The `<!-- TOC -->` directive generates a hierarchical, automatically numbered table of contents (1, 1.1, 1.2, 1.2.1, etc.).

To exclude a heading from the TOC and remove its numbering, use `<!-- toc:exclude -->` before the heading:

```markdown
<!-- toc:exclude -->
## Appendix (not numbered, not in TOC)
```

## Page Layout

Control page breaks and orientation within your document using layout directives.

### Page Breaks

The `<!-- pagebreak -->` directive starts a new page:

<!-- pagebreak -->

This section starts on a **new page** using the `<!-- pagebreak -->` directive. Use page breaks to organize content into logical sections with clear visual separation.

### Orientation Control

The `<!-- landscape -->` and `<!-- portrait -->` directives control page orientation, useful for wide content like tables:

<!-- landscape -->

This section uses **landscape orientation** with the `<!-- landscape -->` directive, providing more horizontal space:

{.table-borders}
| Q1 Revenue | Q1 Expenses | Q1 Profit | Q2 Revenue | Q2 Expenses | Q2 Profit | Q3 Revenue | Q3 Expenses | Q3 Profit | Q4 Revenue | Q4 Expenses |
|-----------|------------|----------|-----------|------------|----------|-----------|------------|----------|-----------|------------|
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 |

<!-- portrait -->

This section returns to **portrait orientation** using the `<!-- portrait -->` directive.

## Headers & Footers

Docco supports page headers and footers added via **inline directives**. Headers and footers are processed through the same pipeline as the main document, supporting:
- Placeholder substitution
- Dynamic content with `<!-- python -->` directives
- File inclusion with `<!-- inline -->` directives

### Adding Headers & Footers

Include headers and footers at the beginning of your document using inline directives with placeholder attributes:

```markdown
<!-- inline:"header.html" title="Docco Feature Showcase" author="Docco Team" -->
<!-- inline:"footer.html" title="Docco" -->
```

The attributes replace `{{key}}` placeholders in the HTML files. For example, `title="My Title"` replaces all `{{title}}` instances.

### CSS Requirements

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

### Example Files

Docco provides example header and footer HTML files in the `examples/` folder:
- `examples/header.html` - Example page header with placeholder support
- `examples/footer.html` - Example page footer with directive support

Examine these files to understand the structure and create your own headers and footers with placeholders (e.g., `{{title}}`, `{{author}}`) and directives.

## Python Code Execution

The `<!-- python -->` directive executes Python code and inserts stdout output into the markdown. Useful for generating dynamic content.

**Syntax:** `<!-- python -->code<!-- /python -->`

**Important:** Python code execution is disabled by default for security reasons. Use the `--allow-python` flag to enable it:

```bash
docco input.md -o output/ --allow-python
```

### Example

This code:
```
print("_", end='')
for i in range(10):
    print(i, end='')
print("_", end='')
```

Produces:
<!-- python -->
print("_", end='')
for i in range(10):
    print(i, end='')
print("_", end='')
<!-- /python -->

The output can contain other directives (markdown, inline files, etc.), enabling complex dynamic content generation.

# Document Formatting

Docco relies on [MarkdownIt](https://markdown-it-py.readthedocs.io/en/latest/) for rendering markdown to HTML. It fully supports [CommonMark specs](https://spec.commonmark.org) with table support. The [(block) attributes](https://mdit-py-plugins.readthedocs.io/en/latest/#attributes) plugin is also installed.

## Images with Styling

Add images using standard Markdown syntax and use `{}` attributes for styling:

`![](images/idea.svg){.icon}`

This defines an image with CSS class `icon` (styled in `css/fancy.css`):

![](images/idea.svg){.icon}

Or define styles directly: `![](images/idea.svg){style="width:2cm"}`

![](images/idea.svg){style="width:2cm"}

## Tables

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

## More Markdown Features

Explore additional markdown features: https://markdown-it.github.io/

# Styling & Layout

## CSS for PDF Generation

WeasyPrint (version 66.0 at time of writing) is used to convert HTML to PDF. It supports CSS up to v2.1, with partial support for modern CSS features:

**Supported:**
- Basic layout: block, inline, float, positioning
- Some modern features: Flexbox, Grid (partially)
- Media queries and custom selectors
- CSS custom properties (`--variables`)

**Not fully supported:**
- Some CSS 3+ features (check WeasyPrint documentation)

For detailed CSS support information, see the [WeasyPrint API reference](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html).

## Best Practices

- Keep CSS focused on print-friendly layouts
- Test CSS features before heavy use
- Reference the WeasyPrint documentation for edge cases
- Use CSS Paged Media rules for headers, footers, and page styling

# Multilingual Documents

Create professional multilingual documents with automatic language-specific PDF generation.

## Automatic Multilingual Mode

Use the `multilingual: true` flag in frontmatter with `base_language` to automatically generate PDFs for the base language plus all available translations:

```yaml
---
multilingual: true
base_language: en
---
```

### How It Works

When enabled, Docco will:
1. Extract a POT file to a `{document_name}/` subfolder
2. Discover all `.po` translation files in that subfolder
3. Generate a PDF for the base language (e.g., `Document_EN.pdf`)
4. Generate translated PDFs for each `.po` file (e.g., `Document_DE.pdf`, `Document_FR.pdf`)

**Example:** See `Multilingual_Document_Example.md` which generates:
- `Multilingual_Document_Example_EN.pdf`
- `Multilingual_Document_Example_DE.pdf`
- `Multilingual_Document_Example_NL.pdf`

## Manual Translation Workflow

For single-language builds with specific translations, use the `--po` flag:

```bash
docco myfile.md --po translations/de.po -o output/
```

This generates a single PDF with the specified translation applied.

## Professional Translation Workflow with POT/PO Files

Docco integrates with professional translation tools and services for enterprise workflows.

### Step 1: Extract Translatable Strings

```bash
docco extract myfile.md -o translations/
```

This generates a `myfile.pot` file containing all translatable strings from the markdown:

```
myfile.md
myfile/
  └── myfile.pot        (template)
```

### Step 2: Create Language-Specific Translations

Translators create `.po` files for each language using professional tools:
- **poedit** (desktop application)
- **Weblate** (web-based, collaborative)
- **Crowdin, Lokalise, POEditor** (professional translation platforms)
- Any gettext-compatible tool

File structure:
```
myfile.md
myfile/
  ├── myfile.pot        (template)
  ├── de.po             (German translation)
  ├── fr.po             (French translation)
  └── nl.po             (Dutch translation)
```

### Step 3: Generate Multilingual PDFs

With `multilingual: true` in frontmatter:
```bash
docco myfile.md -o output/
```

This generates one PDF per language automatically.

Or manually for specific translations:
```bash
docco myfile.md --po translations/de.po -o output/de/
```

### Translation Maintenance

When the source document changes:

```bash
# Re-extract POT
docco extract myfile.md -o translations/

# Merge with existing translations (updates only new/changed strings)
msgmerge -U translations/de.po translations/myfile.pot
```

This allows translators to focus on new content rather than re-translating the entire document.

# Conclusion

This document demonstrates all of Docco's core capabilities: configuration, directives, formatting, styling, and multilingual support. Use these features to create professional, multilingual documents with dynamic content and flexible layouts.

For more information, consult the main Docco documentation.
