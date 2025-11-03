---
css:
  - "css/page.css"
  - "css/toc.css"
  - "css/header_footer.css"
  - "css/fancy.css"
header:
  file: "header.html"
  title: "Docco Feature Showcase"
  author: "Docco Team"
footer:
  file: "footer_showcase.html"
  title: "Docco"
---

<!-- toc:exclude -->
# Docco: Feature Showcase

Welcome to this demonstration of Docco's capabilities.

<!-- TOC -->

# Key Features

This document demonstrates Docco's core capabilities:
- Inline file inclusion with placeholder substitution
- Table of contents generation
- Page layout directives (page breaks and orientation changes)
- Headers and footers with directive support
- Multi-language support
- Python code execution

## Frontmatter

YAML frontmatter at the beginning of the document (between `---` delimiters) configures document processing:

```yaml
---
css:
  - "css/page.css"
  - "css/toc.css"
languages: EN DE FR
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

Paths are relative to the markdown file. Additional CSS can also be provided via the CLI `--css` argument, which overrides frontmatter styles.

**`languages`** - Space-separated language codes for multi-language document generation. When specified, Docco generates separate PDFs for each language, filtering content by `<!-- lang:CODE -->` tags.

Example:
```yaml
languages: "EN DE"
```

See the [Multilingual Document Example](Multilingual_Document_Example.md) for a complete demonstration.

**`header`** and **`footer`** - HTML files for page headers and footers with placeholder and directive support:
```yaml
header:
  file: "header.html"
  title: "My Document"
  author: "John Doe"
footer:
  file: "footer.html"
  title: "My Document"
```

The `file` key is required and specifies the HTML file path (relative to the markdown file). All other keys are placeholders that replace `{{key}}` in the HTML file. Header/footer files support all directives (lang, inline, python), enabling dynamic content like dates and language-specific text. See the [Headers & Footers](#headers--footers) section for details.

## General Directive Rule

**Directives can appear anywhere in the document**, including in the middle of lines. However, directives inside code blocks (both inline `` `code` `` and fenced ``` ``` blocks) are **protected** and will not be processed. This allows you to show directive syntax as examples in documentation without triggering them.

## Inlined Content

The `inline` directive embeds external markdown files with placeholder substitution.

Syntax: `<!-- inline:"foobar.md" key1="value1" key2="value2" -->`

### Arguments
All attributes after the path are placeholders. For example, `author="Docco Team"` replaces `{{author}}` in the inlined file. Arguments are optional. Spaces around the `inline` keyword and colon are accepted. See example below:

<!-- inline:"inline/inlined_content.md" author="Docco Team" date="2025-10-26" -->

### Recursive Inlining
Inlined markdown files can themselves contain inline directives, allowing for multi-level composition (up to a maximum depth of 10 levels to prevent infinite recursion). This enables modular document structures where content can be composed from multiple nested files.

## Table of Contents

The `<!-- TOC -->` directive generates a hierarchical table of contents with automatic numbering (1, 1.1, 1.2, etc.).

Use `<!-- toc:exclude -->` before a heading to exclude it from the TOC and remove its numbering.


## Page Layout Directives

<!-- pagebreak -->
### Page Breaks

This section starts on a **new page** using the `<!-- page break -->` directive.

<!-- landscape -->
### Landscape Orientation

This section uses **landscape orientation** with the `<!-- landscape -->` directive, providing more horizontal space for wide content.

{.table-borders}
| Q1 Revenue | Q1 Expenses | Q1 Profit | Q2 Revenue | Q2 Expenses | Q2 Profit | Q3 Revenue | Q3 Expenses | Q3 Profit | Q4 Revenue | Q4 Expenses |
|-----------|------------|----------|-----------|------------|----------|-----------|------------|----------|-----------|------------|
| $50,000 | $35,000 | $15,000 | $55,000 | $37,000 | $18,000 | $62,000 | $40,000 | $22,000 | $71,000 | $45,000 | 

<!-- portrait -->
### Back to Portrait

This section returns to **portrait orientation** using the `<!-- portrait -->` directive.

# Headers & Footers

Docco supports page headers and footers using HTML files with full directive support. Headers and footers are processed through the same pipeline as the main document, allowing for:
- Placeholder substitution
- Language-specific content with `<!-- lang:CODE -->` directives
- Dynamic content with `<!-- python -->` directives
- File inclusion with `<!-- inline -->` directives

## Configuration

Headers and footers are configured in the frontmatter:
```yaml
header:
  file: "header.html"
  title: "Docco Feature Showcase"
  author: "Docco Team"
footer:
  file: "footer.html"
  title: "Docco"
```

The `file` key specifies the HTML file path. All other keys are placeholders that replace `{{key}}` in the HTML file.

## CSS Requirements

Headers and footers require CSS to position them on the page using CSS Paged Media. Example:
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

## Example Files

**Header (`header_showcase.html`):**
```html
<div style="text-align: center; color: #666;">
    {{title}} - {{author}}
</div>
```

**Footer (`footer_showcase.html`):**
```html
<div style="display: flex; justify-content: space-between;">
    <span>{{title}} - Generated: <!-- python -->
import datetime
print(datetime.datetime.now().strftime("%Y-%m-%d"))
    <!-- /python --></span>
    <span class="page-number"></span>
</div>
```

For language-aware headers and footers with `<!-- lang:CODE -->` directives, see the [Multilingual Document Example](Multilingual_Document_Example.md).

# Python Code Execution

The `<!-- python -->` directive executes Python code and inserts the stdout output into the markdown. This is useful for generating dynamic content.

The output can contain other directives (markdown, inline files, etc.).

**Important**: Python code execution is disabled by default for security reasons. Use the `--allow-python` flag to enable it.

Syntax: `<!-- python -->code<!-- /python -->`

**Example - a loop that outputs digits**

This code:
```
print("_", end='')
for i in range(10):
    print(i, end='')
print("_", end='')
```

Returns: 
<!-- python -->
print("_", end='')
for i in range(10):
    print(i, end='')
print("_", end='')
<!-- /python -->


# Markdown examples
Docco relies on [MarkdownIt](https://markdown-it-py.readthedocs.io/en/latest/) for rendering markdown to HTML. It fully supports the [Commonmark specs](https://spec.commonmark.org) extend with table support. In addition, the [(block) attributes](https://mdit-py-plugins.readthedocs.io/en/latest/#attributes) plugin is installed.

## Images with styling
Add images using the normal Markdown way, and use `{}` add style(s) to the images. For example:

`![](images/idea.svg){.icon}` 

Defines an image with CSS class `icon`. The style is defined in `css/fancy.css`.
The result:

![](images/idea.svg){.icon}

Or define the style directly: `![](images/idea.svg){style="width:2cm"}`

![](images/idea.svg){style="width:2cm"}

## Tables

Markdown tables are supported for organizing tabular data:

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

## More Markdown Examples

Check 'm out: https://markdown-it.github.io/

# Conclusion

This document demonstrates all Docco's capabilities.
