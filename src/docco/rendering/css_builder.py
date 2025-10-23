"""
CSS generation for PDF layout.
"""


class CSSBuilder:
    """
    Generates CSS for PDF rendering with WeasyPrint.

    Future enhancements:
    - Template-based CSS loading
    - Customizable themes
    - Per-document style overrides
    """

    @staticmethod
    def generate_default_css() -> str:
        """
        Generate default CSS for A4 PDF documents.

        Returns:
            CSS string with print layout rules
        """
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

/* TOC entries */
.toc > div {
    margin: 2mm 0;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.toc a {
    text-decoration: none;
    color: #333;
    flex-grow: 1;
}

.toc a::after {
    content: leader('.') target-counter(attr(href), page);
    margin-left: 3mm;
}

/* TOC indentation levels */
.toc-level-1 {
    font-weight: bold;
    margin-top: 3mm;
}

.toc-level-2 {
    margin-left: 8mm;
    font-weight: normal;
}

.toc-level-3 {
    margin-left: 16mm;
    font-weight: normal;
    font-size: 10pt;
}

.toc-level-addendum {
    font-weight: bold;
    margin-top: 5mm;
    color: #555;
}

/* PDF Bookmarks from sections */
h1.section {
    bookmark-label: content();
    bookmark-level: 1;
}

h2.section {
    bookmark-label: content();
    bookmark-level: 2;
}

h3.section {
    bookmark-label: content();
    bookmark-level: 3;
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

h3.section {
    font-size: 12pt;
    margin-top: 6mm;
    margin-bottom: 3mm;
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

/* Code blocks */
pre {
    background-color: #f5f5f5;
    padding: 5mm;
    margin: 5mm 0;
    border-left: 3pt solid #ccc;
    overflow-x: auto;
    page-break-inside: avoid;
}

pre code {
    background-color: transparent;
    padding: 0;
}

/* Images (future phase) */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 5mm auto;
}

figure {
    margin: 5mm 0;
    page-break-inside: avoid;
}

figcaption {
    text-align: center;
    font-size: 10pt;
    color: #666;
    margin-top: 2mm;
}
"""

    @staticmethod
    def generate_custom_css(
        header_text: str = "Product Documentation",
        font_family: str = '"DejaVu Sans", Arial, sans-serif',
    ) -> str:
        """
        Generate CSS with custom parameters.

        Args:
            header_text: Text to display in page headers
            font_family: CSS font-family value

        Returns:
            Customized CSS string
        """
        css = CSSBuilder.generate_default_css()

        # Replace header text
        css = css.replace('"Product Documentation"', f'"{header_text}"')

        # Replace font family
        css = css.replace(
            'font-family: "DejaVu Sans", Arial, sans-serif;', f"font-family: {font_family};"
        )

        return css
