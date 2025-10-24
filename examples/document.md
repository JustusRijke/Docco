---
title: Docco Feature Showcase
subtitle: Markdown & PDF Capabilities
date: 2025-10-23
author: Engineering Team
---

# Introduction

This document showcases Docco's **formatting capabilities** and **Markdown syntax**.

Docco converts Markdown files with YAML frontmatter and external CSS into professional A4 PDFs.

## Basic Usage

Generate a PDF with the CLI:

```bash
docco build document.md style.css --output example.pdf
```

This creates:
- `example.pdf` - Your rendered PDF
- `debug.html` - HTML preview for troubleshooting

# Text Formatting

- **Bold text** with `**bold**`
- *Italic text* with `*italic*`
- `Inline code` with backticks

## Lists

Unordered list:
- First item
- Second item
  - Nested item
  - Another nested item

Ordered list:
1. First step
2. Second step
3. Third step

## Code Blocks

Python example:

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```

Shell command:

```bash
docco build document.md style.css --output example.pdf
```

## Tables

Simple table:

| Feature    | Status  |
|------------|---------|
| Markdown   | ✓       |
| CSS        | ✓       |
| PDF Output | ✓       |

Table with alignment:

| Left Aligned  | Center | Right Aligned |
|:--------------|:------:|--------------:|
| Text          | 123    | 45.67         |
| More text     | 456    | 89.01         |

## Links & Quotes

External link: [Markdown Guide](https://www.markdownguide.org/)

> "Simplicity is the ultimate sophistication."
> — Leonardo da Vinci

## Images

Docco supports standard HTML `<img>` tags for inline images.

### Inline Styled Image

This image uses inline CSS styling:

<img src="images/idea.svg" style="width:100px; display:block; margin:20px auto;" />

### Class-Based Image

This image uses a CSS class for styling:

<img src="images/idea.svg" class="icon" />

### Images with Captions

Images with `alt` text are automatically wrapped in `<figure>` elements with `<figcaption>`:

<img src="images/idea.svg" style="width:120px; display:block; margin:20px auto;" alt="Figure 1: Innovation concept illustration" />

Images are resolved relative to the markdown file location.

## Horizontal Rule

---

## Custom Commands

Docco supports **custom commands** that let you create reusable components without writing HTML directly in your markdown.

<!-- cmd: callout icon="idea.svg" -->
Using borderless tables with icons creates effective callout boxes. This technique is useful for highlighting important information or warnings in your documents.
<!-- /cmd -->

Commands are defined as HTML templates in the `commands/` folder and invoked using HTML comment syntax.

## Horizontal Rule

---

<!-- landscape -->
# Landscape Orientation

This section uses **landscape orientation** with the `<!-- landscape -->` directive.

Landscape is useful for wide tables or content that benefits from horizontal space.

## Wide Data Table

| Month | Product A | Product B | Product C | Product D | Product E | Total Revenue | Growth % |
|-------|-----------|-----------|-----------|-----------|-----------|---------------|----------|
| Jan   | $12,500   | $8,300    | $15,600   | $9,200    | $11,400   | $57,000       | -        |
| Feb   | $13,200   | $9,100    | $16,400   | $9,800    | $12,100   | $60,600       | +6.3%    |
| Mar   | $14,800   | $10,500   | $18,200   | $11,300   | $13,900   | $68,700       | +13.4%   |

<!-- portrait -->
# Back to Portrait

This section returns to **portrait orientation** using the `<!-- portrait -->` directive.

Regular portrait content continues here.

<!-- addendum -->
# Appendix: Directives

This section uses the `<!-- addendum -->` directive, which creates an **appendix** with letter-based numbering (A, B, C...).

## Supported Directives

| Directive | Effect |
|-----------|--------|
| `<!-- landscape -->` | Landscape orientation |
| `<!-- portrait -->` | Portrait orientation |
| `<!-- addendum -->` | Appendix numbering |

<!-- addendum -->
# Appendix: YAML Frontmatter

Frontmatter fields at the top of the document:

| Field | Required | Example |
|-------|----------|---------|
| `title` | Yes | `My Document` |
| `subtitle` | No | `Technical Guide` |
| `date` | No | `2025-10-23` |
| `author` | No | `Your Name` |
