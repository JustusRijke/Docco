"""Main parser orchestrator for markdown to PDF conversion."""

import os
import re
from docco.frontmatter import parse_frontmatter
from docco.inline import process_inlines
from docco.language import filter_content_by_language
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
    """Check if content contains language, inline, or python directives (excluding code blocks)."""
    # Protect code blocks before checking for directives
    protected_content, _ = extract_code_blocks(content)
    return bool(
        re.search(r"<!--\s*lang:\w+\s*-->", protected_content)
        or re.search(r"<!--\s*inline\s*:", protected_content)
        or re.search(r"<!--\s*python\s*-->", protected_content)
    )


def process_directives_iteratively(content, base_dir, target_lang, allow_python):
    """
    Iteratively process lang, inline, and python directives until none remain.

    Processing order per iteration:
    1. Language filtering (if target_lang specified)
    2. Inline expansion
    3. Python execution

    Args:
        content: Markdown content
        base_dir: Base directory for inline resolution
        target_lang: Language code to filter for (None = no filtering)
        allow_python: Allow python directive execution

    Returns:
        str: Processed content with no lang/inline/python directives

    Raises:
        ValueError: If max iterations exceeded
    """
    iteration = 0
    while has_directives(content) and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info(f"Directive processing iteration {iteration}")

        # Step 1: Language filtering
        if target_lang:
            content = filter_content_by_language(content, target_lang)

        # Step 2: Inline expansion
        content = process_inlines(content, base_dir, allow_python)

        # Step 3: Python is handled within process_inlines

    if iteration >= MAX_ITERATIONS and has_directives(content):
        raise ValueError(
            f"Max iterations ({MAX_ITERATIONS}) exceeded in directive processing"
        )

    logger.info(f"Directive processing completed in {iteration} iteration(s)")
    return content


def parse_markdown(
    input_file, output_dir, css_file=None, keep_intermediate=False, allow_python=False
):
    """
    Convert markdown file to PDF through full pipeline.

    New flow:
    1. Read markdown file
    2. Parse frontmatter
    3. Split by language (create in-memory MD files)
    4. For each language: iteratively process lang/inline/python directives
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

    # Step 2: Split by language (create in-memory versions)
    languages_str = metadata.get("languages", "")
    if languages_str:
        languages = languages_str.split()
        logger.info(f"Processing languages: {languages}")
        outputs = {lang: body for lang in languages}
    else:
        logger.info("No languages tag found, treating as single language")
        outputs = {None: body}

    # Step 3: Process each language version
    pdf_files = []
    md_files = []
    input_basename = os.path.splitext(os.path.basename(input_file))[0]

    # Collect CSS files from frontmatter and CLI argument
    css_files = collect_css_files(input_file, metadata, css_file)

    for lang_code, lang_content in outputs.items():
        # Step 4: Iteratively process directives
        lang_content = process_directives_iteratively(
            lang_content, base_dir, lang_code, allow_python
        )

        # Step 4b: Process header and footer (if specified)
        header_html = None
        footer_html = None
        if "header" in metadata:
            header_html = process_header_footer(
                metadata["header"],
                base_dir,
                lang_code,
                allow_python,
                directive_processor=process_directives_iteratively,
            )
        if "footer" in metadata:
            footer_html = process_header_footer(
                metadata["footer"],
                base_dir,
                lang_code,
                allow_python,
                directive_processor=process_directives_iteratively,
            )

        if lang_code is None:
            # Single language case
            md_filename = f"{input_basename}_intermediate.md"
            html_filename = f"{input_basename}.html"
            pdf_filename = f"{input_basename}.pdf"
        else:
            # Multilingual case
            md_filename = f"{input_basename}_{lang_code}.md"
            html_filename = f"{input_basename}_{lang_code}.html"
            pdf_filename = f"{input_basename}_{lang_code}.pdf"

        # Write intermediate MD
        md_path = os.path.join(output_dir, md_filename)
        with open(md_path, "w") as f:
            f.write(lang_content)
        md_files.append(md_path)
        logger.info(f"Wrote intermediate: {md_filename}")

        # Step 5: Convert to HTML
        html_content = markdown_to_html(lang_content)

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
        pdf_files.append(pdf_path)

    # Clean up intermediate files if not keeping them
    if not keep_intermediate:
        for md_path in md_files:
            if os.path.exists(md_path):
                os.remove(md_path)
                logger.info(f"Removed intermediate: {os.path.basename(md_path)}")
        # Also remove HTML files
        for lang_code, _ in outputs.items():
            if lang_code is None:
                html_filename = f"{input_basename}.html"
            else:
                html_filename = f"{input_basename}_{lang_code}.html"
            html_path = os.path.join(output_dir, html_filename)
            if os.path.exists(html_path):
                os.remove(html_path)
                logger.info(f"Removed intermediate: {os.path.basename(html_path)}")

    return pdf_files
