"""
Markdown-based documentation example - demonstrates loading documents from .md files.

This example shows how to:
- Load document content from a markdown file
- Use HTML comment directives for special features
- Generate PDFs from markdown with automatic section numbering

The content is defined in content.md, while document metadata (title, subtitle, date)
and rendering options are specified here.

Run with:
    python examples/markdown_document.py
    or
    docco build examples/markdown_document.py
"""

from pathlib import Path
from docco import Document

# Output directory
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Path to markdown content
CONTENT_FILE = Path(__file__).parent / "content.md"


def main():
    """Generate a PDF document from a markdown file."""
    print("Building document from markdown...")
    print(f"Loading content from: {CONTENT_FILE}")

    # Create document with metadata
    # Title, subtitle, date, and headers are defined here
    # All content sections come from the markdown file
    doc = Document(
        title="Docco Markdown Documentation",
        subtitle="Markdown-Based Document Generation",
        date="October 2025"
    )

    # Load all sections from markdown file
    # The markdown file contains:
    # - Headings that become sections (# ## ###)
    # - HTML comment directives for special features
    # - Regular markdown content (tables, lists, code blocks, etc.)
    doc.load_from_markdown(CONTENT_FILE)

    # Render PDF (and save HTML for debugging)
    pdf_path = OUTPUT_DIR / "markdown_document.pdf"
    doc.render_pdf(pdf_path, save_html=True)

    print(f"\nGenerated files:")
    print(f"  HTML: {OUTPUT_DIR / 'debug.html'}")
    print(f"  PDF:  {pdf_path}")
    print(f"\nDocument structure:")
    print(f"  Total sections: {len(doc)}")

    # Show section breakdown
    doc._ensure_numbered()
    for section in doc.sections:
        orientation_marker = "📄" if section.orientation.value == "portrait" else "📃"
        toc_marker = "" if not section.exclude_from_toc else " [hidden from TOC]"
        level_indent = "  " * (section.level if section.level > 0 else 0)
        print(f"  {orientation_marker} {level_indent}{section.number} {section.title}{toc_marker}")

    print("\nDocument generation complete!")


if __name__ == "__main__":
    main()
