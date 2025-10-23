"""
Basic documentation example - demonstrates Docco usage.

This example generates a simple multi-section PDF document with:
- Title page
- Table of contents
- Hierarchical sections
- Markdown formatting

Run with:
    python examples/basic_document.py
    or
    docco build examples/basic_document.py
"""

from pathlib import Path
from docco import Document

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    """Generate a basic PDF document."""
    print("Building document...")

    # Create document with metadata
    doc = Document(
        title="Product Documentation",
        subtitle="Technical Specification",
        date="October 2025"
    )

    # Add sections with markdown content
    doc.add_section(
        level=1,
        title="Introduction",
        content="""
This is the **introduction** section. It demonstrates:

- Basic markdown formatting
- Automatic numbering
- Table of contents generation

The goal is to validate WeasyPrint's built-in TOC capabilities.
""",
    )

    doc.add_section(
        level=2,
        title="Purpose",
        content="""
This subsection explains the *purpose* of the documentation system.

We're testing hierarchical section numbering and whether page numbers
appear correctly in the generated table of contents.
""",
    )

    doc.add_section(
        level=2,
        title="Scope",
        content="""
Phase 1 scope includes:

1. Single portrait A4 pages
2. Markdown conversion
3. Section numbering
4. **Automatic TOC generation**

Additional content to push this to a second page and verify
page numbering works correctly in the table of contents.
""",
    )

    doc.add_section(
        level=1,
        title="Technical Details",
        content="""
This section contains technical information about the system.

| Component | Technology |
|-----------|------------|
| PDF Engine | WeasyPrint |
| Markdown | markdown-it-py |
| Layout | CSS Paged Media |

The table above demonstrates basic table support.
""",
    )

    # Render PDF (and save HTML for debugging)
    pdf_path = OUTPUT_DIR / "final.pdf"
    doc.render_pdf(pdf_path, save_html=True)

    print(f"HTML saved to: {OUTPUT_DIR / 'debug.html'}")
    print(f"PDF generated: {pdf_path}")
    print("\nDocument generation complete!")


if __name__ == "__main__":
    main()
