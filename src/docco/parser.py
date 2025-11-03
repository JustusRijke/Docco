"""Main parser orchestrator for markdown to PDF conversion."""

import os
import re
from docco.frontmatter import parse_frontmatter
from docco.inline import process_inlines
from docco.translation import build_from_po
from docco.toc import process_toc
from docco.page_layout import process_page_layout
from docco.html import markdown_to_html, wrap_html
from docco.pdf import collect_css_files, html_to_pdf
from docco.header_footer import process_header_footer
from docco.utils import setup_logger
from docco.directive_utils import extract_code_blocks

logger = setup_logger(__name__)
MAX_ITERATIONS = 10


def has_directives(content):
    """Check if content contains inline or python directives (excluding code blocks)."""
    # Protect code blocks before checking for directives
    protected_content, _ = extract_code_blocks(content)
    return bool(
        re.search(r"<!--\s*inline\s*:", protected_content)
        or re.search(r"<!--\s*python\s*-->", protected_content)
    )


def process_directives_iteratively(content, base_dir, allow_python):
    """
    Iteratively process inline and python directives until none remain.

    Processing order per iteration:
    1. Inline expansion
    2. Python execution (handled within process_inlines)

    Args:
        content: Markdown content
        base_dir: Base directory for inline resolution
        allow_python: Allow python directive execution

    Returns:
        str: Processed content with no inline/python directives

    Raises:
        ValueError: If max iterations exceeded
    """
    iteration = 0
    while has_directives(content) and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info(f"Directive processing iteration {iteration}")

        # Inline expansion (which also handles Python)
        content = process_inlines(content, base_dir, allow_python)

    if iteration >= MAX_ITERATIONS and has_directives(content):
        raise ValueError(
            f"Max iterations ({MAX_ITERATIONS}) exceeded in directive processing"
        )

    logger.info(f"Directive processing completed in {iteration} iteration(s)")
    return content


def parse_markdown(
    input_file, output_dir, css_file=None, keep_intermediate=False, allow_python=False, po_file=None
):
    """
    Convert markdown file to PDF through full pipeline.

    Pipeline flow:
    1. Read markdown file
    2. Parse frontmatter
    3. Iteratively process inline/python directives
    4. Apply PO translations if provided
    5. Convert markdown to HTML
    6. Process TOC and page layout directives
    7. Convert HTML to PDF
    8. Clean up intermediate files (unless keep_intermediate=True)

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output files
        css_file: CSS file for PDF styling (optional)
        keep_intermediate: Keep intermediate HTML/MD files if True
        allow_python: Allow python code execution in directives
        po_file: Path to PO file for translations (optional)

    Returns:
        list: Paths to generated PDF files
    """
    logger.info(f"Processing markdown: {input_file}")

    # Read file
    with open(input_file, "r") as f:
        content = f.read()

    # Step 1: Parse frontmatter
    metadata, body = parse_frontmatter(content)
    logger.info(f"Parsed frontmatter: {metadata}")

    # Determine base directory for inline resolution
    base_dir = os.path.dirname(os.path.abspath(input_file))

    # Step 2: Iteratively process directives
    body = process_directives_iteratively(body, base_dir, allow_python)

    # Step 3: Apply translations if PO file provided
    if po_file:
        logger.info(f"Applying translations from {po_file}")
        body = build_from_po(body, po_file)

    # Step 4: Process header and footer (if specified)
    header_html = None
    footer_html = None
    if "header" in metadata:
        header_html = process_header_footer(
            metadata["header"],
            base_dir,
            allow_python,
            directive_processor=process_directives_iteratively,
        )
    if "footer" in metadata:
        footer_html = process_header_footer(
            metadata["footer"],
            base_dir,
            allow_python,
            directive_processor=process_directives_iteratively,
        )

    # Generate filenames
    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    md_filename = f"{input_basename}_intermediate.md"
    html_filename = f"{input_basename}.html"
    pdf_filename = f"{input_basename}.pdf"

    # Collect CSS files from frontmatter and CLI argument
    css_files = collect_css_files(input_file, metadata, css_file)

    # Write intermediate MD
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w") as f:
        f.write(body)
    logger.info(f"Wrote intermediate: {md_filename}")

    # Step 5: Convert to HTML
    html_content = markdown_to_html(body)

    # Step 6: Process TOC and page layout directives
    html_content = process_toc(html_content)
    html_content = process_page_layout(html_content)
    html_wrapped = wrap_html(html_content, header_html, footer_html)

    html_path = os.path.join(output_dir, html_filename)
    with open(html_path, "w") as f:
        f.write(html_wrapped)
    logger.info(f"Wrote HTML: {html_filename}")

    # Step 7: Convert to PDF
    pdf_path = os.path.join(output_dir, pdf_filename)
    html_to_pdf(html_wrapped, pdf_path, css_files, base_url=base_dir)

    # Clean up intermediate files if not keeping them
    if not keep_intermediate:
        if os.path.exists(md_path):
            os.remove(md_path)
            logger.info(f"Removed intermediate: {os.path.basename(md_path)}")
        if os.path.exists(html_path):
            os.remove(html_path)
            logger.info(f"Removed intermediate: {os.path.basename(html_path)}")

    return [pdf_path]
