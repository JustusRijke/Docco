"""
Minimal documentation builder - Phase 1
Generates A4 PDF with automatic TOC from structured content
"""

from pathlib import Path
from markdown_it import MarkdownIt
from weasyprint import HTML, CSS

# Initialize markdown parser
md = MarkdownIt()

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def md_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML"""
    return md.render(markdown_text)


def build_document() -> str:
    """Build complete HTML document"""

    # Document sections with markdown content
    sections = [
        {
            "level": 1,
            "number": "1",
            "title": "Introduction",
            "content": """
This is the **introduction** section. It demonstrates:

- Basic markdown formatting
- Automatic numbering
- Table of contents generation

The goal is to validate WeasyPrint's built-in TOC capabilities.
""",
        },
        {
            "level": 2,
            "number": "1.1",
            "title": "Purpose",
            "content": """
This subsection explains the *purpose* of the documentation system.

We're testing hierarchical section numbering and whether page numbers
appear correctly in the generated table of contents.
""",
        },
        {
            "level": 2,
            "number": "1.2",
            "title": "Scope",
            "content": """
Phase 1 scope includes:

1. Single portrait A4 pages
2. Markdown conversion
3. Section numbering
4. **Automatic TOC generation**

Additional content to push this to a second page and verify
page numbering works correctly in the table of contents.
""",
        },
        {
            "level": 1,
            "number": "2",
            "title": "Technical Details",
            "content": """
This section contains technical information about the system.

| Component | Technology |
|-----------|------------|
| PDF Engine | WeasyPrint |
| Markdown | markdown-it-py |
| Layout | CSS Paged Media |

The table above demonstrates basic table support.
""",
        },
    ]

    # Start HTML document
    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        "<title>Product Documentation</title>",
        "</head>",
        "<body>",
        # Title page
        '<div class="title-page">',
        "<h1>Product Documentation</h1>",
        '<p class="subtitle">Technical Specification</p>',
        '<p class="date">October 2025</p>',
        "</div>",
        # Table of Contents (WeasyPrint will generate this)
        '<div class="toc-page">',
        "<h1>Table of Contents</h1>",
        '<nav class="toc"></nav>',
        "</div>",
        # Content sections
        '<div class="content">',
    ]

    # Add each section
    for section in sections:
        h_tag = f"h{section['level']}"
        html_parts.append(
            f'<{h_tag} class="section">'
            f'{section["number"]} {section["title"]}'
            f"</{h_tag}>"
        )
        html_parts.append(md_to_html(section["content"]))

    html_parts.extend(
        [
            "</div>",  # content
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(html_parts)


def generate_css() -> str:
    """Generate CSS for PDF layout"""
    return """
/* Page setup */
@page {
    size: A4 portrait;
    margin: 25mm 20mm 25mm 20mm;
    
    @top-center {
        content: "Product Documentation";
        font-size: 9pt;
        color: #666;
        border-bottom: 0.5pt solid #ccc;
        padding-bottom: 3mm;
    }
    
    @bottom-right {
        content: "Page " counter(page);
        font-size: 9pt;
        color: #666;
    }
}

/* No headers/footers on title page */
@page :first {
    @top-center { content: none; }
    @bottom-right { content: none; }
}

/* Base typography */
body {
    font-family: "DejaVu Sans", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

/* Title page */
.title-page {
    page-break-after: always;
    text-align: center;
    padding-top: 100mm;
}

.title-page h1 {
    font-size: 28pt;
    margin-bottom: 10mm;
    color: #1a1a1a;
}

.title-page .subtitle {
    font-size: 16pt;
    color: #666;
    margin-bottom: 5mm;
}

.title-page .date {
    font-size: 12pt;
    color: #999;
}

/* Table of Contents */
.toc-page {
    page-break-after: always;
}

.toc-page h1 {
    font-size: 20pt;
    margin-bottom: 10mm;
    border-bottom: 2pt solid #333;
    padding-bottom: 3mm;
}

/* TOC generation via CSS */
.toc::before {
    content: "";
}

.toc a::after {
    content: leader('.') target-counter(attr(href), page);
    float: right;
}

/* Generate TOC entries from h1, h2 */
h1.section, h2.section {
    bookmark-level: none;
}

h1.section {
    bookmark-label: content();
    bookmark-level: 1;
}

h2.section {
    bookmark-label: content();
    bookmark-level: 2;
}

/* Content sections */
.content {
    margin-top: 0;
}

h1.section {
    font-size: 18pt;
    margin-top: 15mm;
    margin-bottom: 5mm;
    page-break-after: avoid;
    color: #1a1a1a;
    border-bottom: 1pt solid #ccc;
    padding-bottom: 2mm;
}

h2.section {
    font-size: 14pt;
    margin-top: 8mm;
    margin-bottom: 4mm;
    page-break-after: avoid;
    color: #333;
}

/* Paragraphs */
p {
    margin: 0 0 5mm 0;
    text-align: justify;
}

/* Lists */
ul, ol {
    margin: 5mm 0;
    padding-left: 8mm;
}

li {
    margin-bottom: 2mm;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 5mm 0;
    page-break-inside: avoid;
}

th, td {
    border: 0.5pt solid #ccc;
    padding: 3mm;
    text-align: left;
}

th {
    background-color: #f5f5f5;
    font-weight: bold;
}

/* Inline formatting */
strong {
    font-weight: bold;
    color: #1a1a1a;
}

em {
    font-style: italic;
}

code {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 10pt;
    background-color: #f5f5f5;
    padding: 1mm 2mm;
}
"""


def main():
    """Generate PDF documentation"""
    print("Building document...")

    # Generate HTML
    html_content = build_document()

    # Save HTML for debugging
    html_path = OUTPUT_DIR / "debug.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"HTML saved to: {html_path}")

    # Generate CSS
    css_content = generate_css()

    # Render PDF
    print("Rendering PDF...")
    pdf_path = OUTPUT_DIR / "final.pdf"
    HTML(string=html_content).write_pdf(pdf_path, stylesheets=[CSS(string=css_content)])

    print(f"PDF generated: {pdf_path}")
    print("\nPhase 1 complete. Review TOC generation and page numbering.")


if __name__ == "__main__":
    main()
