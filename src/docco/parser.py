"""Main parser orchestrator for markdown to PDF conversion."""

import os
import re
import glob
import logging
from docco.core import parse_frontmatter, markdown_to_html, wrap_html
from docco.inline import process_inlines, extract_code_blocks
from docco.translation import (
    apply_po_to_html,
    extract_html_to_pot,
    get_po_stats,
    check_po_sync,
    update_po_files,
)
from docco.toc import process_toc
from docco.page_layout import process_page_layout
from docco.pdf import collect_css_content, html_to_pdf
from docco.pdf_validation import validate_and_warn_pdf_images

logger = logging.getLogger(__name__)
MAX_ITERATIONS = 10


def preprocess_document(content, input_file, allow_python=False):
    """
    Parse frontmatter and process directives.

    Args:
        content: Markdown content string
        input_file: Path to input file (for base directory resolution)
        allow_python: Allow python directive execution

    Returns:
        tuple: (metadata dict, processed body string, base directory path)
    """
    metadata, body = parse_frontmatter(content)
    base_dir = os.path.dirname(os.path.abspath(input_file))
    body = process_directives_iteratively(body, base_dir, allow_python)
    return metadata, body, base_dir


def has_directives(content):
    """Check if content contains inline directives (excluding code blocks)."""
    # Protect code blocks before checking for directives
    protected_content, _ = extract_code_blocks(content)
    return bool(re.search(r"<!--\s*inline\s*:", protected_content))


def process_directives_iteratively(content, base_dir, allow_python):
    """
    Iteratively process inline directives until none remain.

    Inline directives can include .py files that output more inline directives,
    requiring multiple iterations.

    Args:
        content: Markdown content
        base_dir: Base directory for inline resolution
        allow_python: Allow python file execution via inline directive

    Returns:
        str: Processed content with no inline directives

    Raises:
        ValueError: If max iterations exceeded
    """
    iteration = 0
    while has_directives(content) and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.debug(f"Directive processing iteration {iteration}")

        # Inline expansion (which also handles Python)
        content = process_inlines(content, base_dir, allow_python)

    if iteration >= MAX_ITERATIONS and has_directives(content):
        raise ValueError(
            f"Max iterations ({MAX_ITERATIONS}) exceeded in directive processing"
        )

    logger.debug(f"Directive processing completed in {iteration} iteration(s)")
    return content


def _generate_single_pdf(
    body,
    metadata,
    input_file,
    input_basename,
    output_dir,
    base_dir,
    keep_intermediate,
    allow_python,
    lang_suffix=None,
    po_file=None,
    validate_images=True,
):
    """
    Generate a single PDF from processed markdown body.

    Args:
        body: Processed markdown body (after directives)
        metadata: Frontmatter metadata
        input_file: Path to input markdown file (for CSS resolution)
        input_basename: Base filename without extension
        output_dir: Directory for output files
        base_dir: Base directory for resource resolution
        keep_intermediate: Keep intermediate HTML/MD files if True
        allow_python: Allow python code execution in directives
        lang_suffix: Optional language suffix for filenames (e.g., "_de")
        po_file: Optional PO file for translations (applied before TOC/layout)
        validate_images: Validate image DPI if DPI frontmatter is set (default: True)

    Returns:
        str: Path to generated PDF file
    """
    suffix = lang_suffix or ""

    # Generate filenames with optional language suffix
    md_filename = f"{input_basename}{suffix}_intermediate.md"
    html_filename = f"{input_basename}{suffix}.html"
    pdf_filename = f"{input_basename}{suffix}.pdf"

    # Collect CSS content from frontmatter
    css_result = collect_css_content(input_file, metadata)

    # Write intermediate MD
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(body)
    logger.debug(f"Wrote intermediate: {md_filename}")

    # Convert markdown to body HTML (no TOC/layout yet)
    body_html = markdown_to_html(body)

    # Apply translation if needed (before TOC generation)
    if po_file:
        temp_body_path = os.path.join(output_dir, f"{html_filename}.body_temp")
        temp_translated_path = os.path.join(
            output_dir, f"{html_filename}.translated_temp"
        )

        # Wrap body HTML temporarily for translation
        temp_wrapped = wrap_html(body_html, css_content="", external_css=[])
        with open(temp_body_path, "w", encoding="utf-8") as f:
            f.write(temp_wrapped)

        # Apply translation
        apply_po_to_html(temp_body_path, po_file, temp_translated_path)

        # Extract translated body from wrapped HTML
        with open(temp_translated_path, "r", encoding="utf-8") as f:
            translated_html = f.read()
        # Extract body content (between <body> and </body>)
        import re

        body_match = re.search(r"<body>\s*(.*?)\s*</body>", translated_html, re.DOTALL)
        if body_match:
            body_html = body_match.group(1)

        # Clean up temp files
        os.remove(temp_body_path)
        os.remove(temp_translated_path)
        logger.debug("Applied translations before TOC")

    # Process TOC and layout (on potentially translated body HTML)
    body_html = process_toc(body_html)
    body_html = process_page_layout(body_html)

    # Wrap in complete HTML document with CSS
    html_wrapped = wrap_html(
        body_html, css_content=css_result["inline"], external_css=css_result["external"]
    )

    # Write final HTML to file
    html_path = os.path.join(output_dir, html_filename)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_wrapped)
    logger.debug(f"Wrote HTML: {html_filename}")

    # Convert to PDF
    pdf_path = os.path.join(output_dir, pdf_filename)
    dpi = metadata.get("dpi")
    html_to_pdf(html_path, pdf_path, base_url=base_dir, dpi=dpi)

    # Validate PDF image quality if DPI was specified and validation enabled
    if validate_images and dpi:
        validate_and_warn_pdf_images(pdf_path, threshold=dpi)

    # Clean up intermediate files if not keeping them
    if not keep_intermediate:
        if os.path.exists(md_path):
            os.remove(md_path)
        if os.path.exists(html_path):
            os.remove(html_path)

    return pdf_path


def _generate_multilingual_pdfs(
    body,
    metadata,
    input_file,
    output_dir,
    base_dir,
    keep_intermediate,
    allow_python,
):
    """
    Generate PDFs for all languages in multilingual mode.

    Args:
        body: Processed markdown body (after directives)
        metadata: Frontmatter metadata (must include base_language)
        input_file: Path to input markdown file
        output_dir: Directory for output files
        base_dir: Base directory for resource resolution
        keep_intermediate: Keep intermediate HTML/MD files if True
        allow_python: Allow python code execution in directives

    Returns:
        list: Paths to generated PDF files

    Raises:
        ValueError: If base_language not specified in frontmatter
    """
    # Check for required base_language in multilingual mode
    base_language = metadata.get("base_language")
    if not base_language:
        raise ValueError("Multilingual mode requires 'base_language' in frontmatter")

    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    translations_dir = os.path.join(base_dir, input_basename)
    os.makedirs(translations_dir, exist_ok=True)

    pdf_paths = []
    base_lang_code = base_language.upper()
    logger.info(f"Processing base language: {base_lang_code}")

    # Step 1: Generate HTML without TOC for POT extraction
    css_result = collect_css_content(input_file, metadata)
    body_html = markdown_to_html(body)
    html_for_pot = wrap_html(
        body_html, css_content=css_result["inline"], external_css=css_result["external"]
    )

    # Write HTML for POT extraction (without TOC/layout)
    pot_html_path = os.path.join(output_dir, f"{input_basename}_for_pot.html")
    with open(pot_html_path, "w", encoding="utf-8") as f:
        f.write(html_for_pot)

    # Step 2: Extract POT file from pre-TOC HTML to translations subfolder
    pot_path = os.path.join(translations_dir, f"{input_basename}.pot")
    extract_html_to_pot(pot_html_path, pot_path)
    logger.debug(f"Extracted POT for multilingual: {pot_path}")

    # Clean up POT HTML
    os.remove(pot_html_path)

    # Step 3: Update existing PO files with new POT content
    update_po_files(pot_path, translations_dir)

    # Step 4: Generate PDF for base language (with TOC/layout)
    pdf_path = _generate_single_pdf(
        body,
        metadata,
        input_file,
        input_basename,
        output_dir,
        base_dir,
        keep_intermediate=keep_intermediate,
        allow_python=allow_python,
        lang_suffix=f"_{base_lang_code}",
        validate_images=True,
    )
    pdf_paths.append(pdf_path)

    # Step 5: Find and process .po files in translations subfolder
    po_files = sorted(glob.glob(os.path.join(translations_dir, "*.po")))
    for po_file in po_files:
        lang_code = os.path.splitext(os.path.basename(po_file))[0].upper()
        logger.info(f"Processing language: {lang_code}")

        # Check if PO file is in sync with current POT
        if not check_po_sync(pot_path, po_file):
            logger.warning(
                f"PO file out of sync for {lang_code}: "
                f"document has changed. PO files are automatically updated on each build."
            )

        # Check translation status
        stats = get_po_stats(po_file)
        if stats["untranslated"] > 0 or stats["fuzzy"] > 0:
            logger.warning(
                f"Translation incomplete for {lang_code}: "
                f"{stats['untranslated']} untranslated, {stats['fuzzy']} fuzzy"
            )

        # Generate PDF with translation (skip image validation for non-base languages)
        pdf_path = _generate_single_pdf(
            body,
            metadata,
            input_file,
            input_basename,
            output_dir,
            base_dir,
            keep_intermediate,
            allow_python,
            lang_suffix=f"_{lang_code}",
            po_file=po_file,
            validate_images=False,
        )
        pdf_paths.append(pdf_path)

    return pdf_paths


def parse_markdown(
    input_file,
    output_dir,
    keep_intermediate=False,
    allow_python=False,
    po_file=None,
):
    """
    Convert markdown file to PDF through full pipeline.

    Pipeline flow:
    1. Read markdown file
    2. Parse frontmatter
    3. Iteratively process inline/python directives
    4. Convert markdown to HTML
    5. Apply translations from PO file if provided (before TOC/layout)
    6. Process TOC and page layout directives
    7. Convert HTML to PDF
    8. Clean up intermediate files (unless keep_intermediate=True)

    For multilingual mode: extract POT from HTML and generate PDFs for each language.

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output files
        keep_intermediate: Keep intermediate HTML/MD files if True
        allow_python: Allow python code execution in directives
        po_file: Path to PO file for translations (optional, ignored in multilingual mode)

    Returns:
        list: Paths to generated PDF files
    """
    logger.info(f"Processing markdown: {input_file}")

    # Read file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1 & 2: Preprocess document (parse frontmatter and process directives)
    metadata, body, base_dir = preprocess_document(content, input_file, allow_python)
    logger.debug(f"Parsed frontmatter: {metadata}")
    input_basename = os.path.splitext(os.path.basename(input_file))[0]

    # Step 3: Route to appropriate workflow based on multilingual flag
    if metadata.get("multilingual", False):
        # Multilingual mode: ignore po_file parameter
        return _generate_multilingual_pdfs(
            body,
            metadata,
            input_file,
            output_dir,
            base_dir,
            keep_intermediate,
            allow_python,
        )

    # Step 4: Generate single PDF (with optional translation via po_file)
    pdf_path = _generate_single_pdf(
        body,
        metadata,
        input_file,
        input_basename,
        output_dir,
        base_dir,
        keep_intermediate,
        allow_python,
        po_file=po_file,
    )

    return [pdf_path]
