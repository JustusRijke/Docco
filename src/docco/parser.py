"""Main parser orchestrator for markdown to PDF conversion."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from docco.core import markdown_to_html, parse_frontmatter, wrap_html
from docco.inline import extract_code_blocks, process_inlines
from docco.page_layout import process_page_layout
from docco.pdf import collect_css_content, collect_js_content, html_to_pdf
from docco.pdf_validation import validate_and_warn_pdf_images
from docco.translation import (
    apply_po_to_html,
    check_po_sync,
    extract_html_to_pot,
    get_po_stats,
    merge_po_files,
    update_po_files,
)

logger = logging.getLogger(__name__)
MAX_ITERATIONS = 10
RESERVED_VARS = {"PATH"}


def apply_variables(content: str, variables: dict[str, str]) -> str:
    """Replace $$varname$$ placeholders in content with their values."""
    for name, value in variables.items():
        content = content.replace(f"$${name}$$", value)
    return content


@dataclass
class BuildConfig:
    keep_intermediate: bool = False
    allow_python: bool = False
    filename_template: str | None = None
    dpi: int | None = None


def preprocess_document(
    content: str, input_file: Path, allow_python: bool = False
) -> tuple[dict[str, object], str, Path]:
    """
    Parse frontmatter and process directives.

    Args:
        content: Markdown content string
        input_file: Path to input file (for base directory resolution)
        allow_python: Allow python directive execution

    Returns:
        tuple: (metadata dict, processed content string, base directory path)
    """
    metadata = parse_frontmatter(content)
    base_dir = input_file.resolve().parent

    # Build variable map: built-ins first, then user-declared (cannot override built-ins)
    variables: dict[str, str] = {"PATH": str(input_file.resolve().parent)}
    user_vars = metadata.get("var") or {}
    if isinstance(user_vars, dict):
        for name, value in user_vars.items():
            if not isinstance(name, str):
                continue
            if name in RESERVED_VARS:
                logger.warning(
                    f"Variable '{name}' is reserved and cannot be redeclared"
                )
            else:
                variables[name] = str(value)

    # Strip frontmatter before variable substitution (variables must not affect frontmatter)
    frontmatter_end = re.search(
        r"^---\s*\n.*?^---\s*\n", content, re.DOTALL | re.MULTILINE
    )
    body = content[frontmatter_end.end() :] if frontmatter_end else content

    body = apply_variables(body, variables)
    processed_content = process_directives_iteratively(
        body, base_dir, allow_python, variables
    )
    return metadata, processed_content, base_dir


def has_directives(content: str) -> bool:
    """Check if content contains inline directives (excluding code blocks)."""
    # Protect code blocks before checking for directives
    protected_content, _ = extract_code_blocks(content)
    return bool(re.search(r"<!--\s*inline\s*:", protected_content))


def process_filter_directives(html: str, language: str) -> str:
    """Remove filter blocks not matching the given language code.

    Blocks matching the language are kept (with the directives stripped).
    Blocks for other languages are removed entirely.
    """
    lang = language.lower()

    def replace_block(m: re.Match) -> str:
        return m.group(2) if m.group(1).strip().lower() == lang else ""

    return re.sub(
        r"<!--\s*filter\s*:\s*(\S+)\s*-->(.*?)<!--\s*/filter\s*-->",
        replace_block,
        html,
        flags=re.DOTALL,
    )


def process_directives_iteratively(
    content: str,
    base_dir: Path,
    allow_python: bool,
    variables: dict[str, str] | None = None,
) -> str:
    """
    Iteratively process inline directives until none remain.

    Inline directives can include .py files that output more inline directives,
    requiring multiple iterations.

    Args:
        content: Markdown content
        base_dir: Base directory for inline resolution
        allow_python: Allow python file execution via inline directive
        variables: Variable map for $$var$$ substitution in inlined files

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
        content = process_inlines(content, base_dir, allow_python, variables)

    if iteration >= MAX_ITERATIONS and has_directives(content):
        raise ValueError(
            f"Max iterations ({MAX_ITERATIONS}) exceeded in directive processing"
        )

    logger.debug(f"Directive processing completed in {iteration} iteration(s)")
    return content


DEFAULT_MULTILINGUAL_FILENAME = "{filename}_{langcode}"


def _apply_filename_template(template: str, filename: str, langcode: str) -> str:
    """Substitute {filename} and {langcode} in a filename template."""
    return template.format(filename=filename, langcode=langcode)


def _generate_single_pdf(
    body: str,
    metadata: dict[str, object],
    input_file: Path,
    input_basename: str,
    output_dir: Path,
    base_dir: Path,
    config: BuildConfig,
    lang_suffix: str | None = None,
    po_files: list[Path] | None = None,
    library_po_files: list[Path] | None = None,
    validate_images: bool = True,
) -> Path:
    """
    Generate a single PDF from processed markdown body.

    Args:
        body: Processed markdown body (after directives)
        metadata: Frontmatter metadata
        input_file: Path to input markdown file (for CSS resolution)
        input_basename: Base filename without extension
        output_dir: Directory for output files
        base_dir: Base directory for resource resolution
        config: Build settings (keep_intermediate, allow_python, filename_template, dpi)
        lang_suffix: Optional language suffix for filenames (e.g., "_de")
        po_files: PO files for this language, highest-priority first
        library_po_files: Shared library PO files (lowest priority)
        validate_images: Validate image DPI if DPI frontmatter is set (default: True)

    Returns:
        Path: Path to generated PDF file
    """
    # Generate output stem: use filename template for multilingual, plain basename otherwise
    if lang_suffix:
        lang_code = lang_suffix.lstrip("_")
        template = config.filename_template or DEFAULT_MULTILINGUAL_FILENAME
        output_stem = _apply_filename_template(template, input_basename, lang_code)
    else:
        output_stem = input_basename

    # Generate filenames
    md_filename = f"{output_stem}_intermediate.md"
    html_filename = f"{output_stem}.html"
    pdf_filename = f"{output_stem}.pdf"

    # Collect CSS and JS content from frontmatter
    css_result = collect_css_content(input_file, metadata)
    js_result = collect_js_content(input_file, metadata)

    # Write intermediate MD
    md_path = output_dir / md_filename
    with md_path.open("w", encoding="utf-8") as f:
        f.write(body)
    logger.debug(f"Wrote intermediate: {md_filename}")

    # Convert markdown to body HTML (no layout yet)
    body_html = markdown_to_html(body)

    # Apply language filter directives if a language is set
    if lang_suffix:
        lang_code = lang_suffix.lstrip("_")
        body_html = process_filter_directives(body_html, lang_code)

    # Apply translation if needed (before layout)
    # Merge order (lowest to highest priority): library POs, then po_files reversed
    # so that the first listed PO (index 0) wins.
    all_po_inputs = [*(library_po_files or []), *reversed(po_files or [])]
    merged_po_temp: Path | None = None
    effective_po: Path | None = None
    if len(all_po_inputs) > 1:
        merged_po_temp = output_dir / f"{output_stem}_merged.po"
        merge_po_files(all_po_inputs, merged_po_temp)
        effective_po = merged_po_temp
    elif len(all_po_inputs) == 1:
        effective_po = all_po_inputs[0]

    if effective_po:
        temp_body_path = output_dir / f"{html_filename}.body_temp"
        temp_translated_path = output_dir / f"{html_filename}.translated_temp"

        # Wrap body HTML temporarily for translation
        temp_wrapped = wrap_html(
            body_html, css_content="", external_css=[], base_dir=base_dir
        )
        with temp_body_path.open("w", encoding="utf-8") as f:
            f.write(temp_wrapped)

        # Apply translation
        apply_po_to_html(temp_body_path, effective_po, temp_translated_path)

        # Extract translated body from wrapped HTML
        with temp_translated_path.open("r", encoding="utf-8") as f:
            translated_html = f.read()
        # Extract body content (between <body> and </body>)
        body_match = re.search(r"<body>\s*(.*?)\s*</body>", translated_html, re.DOTALL)
        if body_match:
            body_html = body_match.group(1)

        # Clean up temp files
        temp_body_path.unlink()
        temp_translated_path.unlink()
        if merged_po_temp and merged_po_temp.exists():
            merged_po_temp.unlink()
        logger.debug("Applied translations")

    # Process layout (on potentially translated body HTML)
    body_html = process_page_layout(body_html)

    # Wrap in complete HTML document with CSS and JS
    html_wrapped = wrap_html(
        body_html,
        css_content=css_result["inline"],
        external_css=css_result["external"],
        js_content=js_result["inline"],
        external_js=js_result["external"],
        base_dir=base_dir,
    )

    # Write final HTML to file
    html_path = output_dir / html_filename
    with html_path.open("w", encoding="utf-8") as f:
        f.write(html_wrapped)
    logger.debug(f"Wrote HTML: {html_filename}")

    # Convert to PDF
    pdf_path = output_dir / pdf_filename
    html_to_pdf(html_path, pdf_path, dpi=config.dpi)

    # Validate PDF image quality if DPI was specified and validation enabled
    if validate_images and config.dpi is not None:
        validate_and_warn_pdf_images(pdf_path, threshold=config.dpi)

    # Clean up intermediate files if not keeping them
    if not config.keep_intermediate:
        if md_path.exists():
            md_path.unlink()
        if html_path.exists():
            html_path.unlink()

    return pdf_path


def parse_markdown(
    input_file: Path,
    output_dir: Path,
    config: BuildConfig | None = None,
    library_po_files: list[Path] | None = None,
) -> list[Path]:
    """
    Convert markdown file to PDF through full pipeline.

    Pipeline flow:
    1. Read markdown file
    2. Parse frontmatter
    3. Iteratively process inline/python directives
    4. Convert markdown to HTML
    5. Apply translations from PO file if provided (before layout)
    6. Process page layout directives
    7. Convert HTML to PDF (TOC generated via JavaScript during PDF rendering)
    8. Clean up intermediate files (unless keep_intermediate=True)

    If `translations` is in frontmatter: extract POT, update PO files, generate
    base language PDF + one PDF per listed language.

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output files
        config: Build settings (keep_intermediate, allow_python, filename_template, dpi)
        library_po_files: Shared library PO files (lowest priority, optional)

    Returns:
        list[Path]: Paths to generated PDF files
    """
    config = config or BuildConfig()
    logger.info(f"Processing markdown: {input_file}")

    # Read file
    with input_file.open("r", encoding="utf-8") as f:
        content = f.read()

    # Step 1 & 2: Preprocess document (parse frontmatter and process directives)
    metadata, body, base_dir = preprocess_document(
        content, input_file, config.allow_python
    )
    logger.debug(f"Parsed frontmatter: {metadata}")
    input_basename = input_file.stem

    translations = metadata.get("translations")

    # Multilingual mode: translations dict in frontmatter
    if isinstance(translations, dict) and translations:
        base_language_raw = metadata.get("base_language")
        if not base_language_raw or not isinstance(base_language_raw, str):
            raise ValueError(
                "Multilingual mode requires 'base_language' in frontmatter"
            )
        base_language: str = base_language_raw
        base_lang_code = base_language.upper()

        # POT lives next to the source file
        pot_path = base_dir / f"{input_basename}.pot"

        # Extract POT from rendered HTML
        css_result = collect_css_content(input_file, metadata)
        body_html = markdown_to_html(body)
        html_for_pot = wrap_html(
            body_html,
            css_content=css_result["inline"],
            external_css=css_result["external"],
            base_dir=base_dir,
        )
        extract_html_to_pot(
            html_for_pot.encode("utf-8"), pot_path, source_name=input_basename
        )
        logger.debug(f"Extracted POT: {pot_path}")

        # Resolve PO file paths relative to source file's directory.
        # Each value may be a string or a list of strings (multiple PO files per lang).
        # First entry in the list has highest priority.
        def _resolve_po_list(val: object) -> list[Path]:
            paths = [val] if isinstance(val, str) else list(val)  # type: ignore[arg-type]
            return [(base_dir / str(p)).resolve() for p in paths]

        lang_po_map: dict[str, list[Path]] = {
            str(lang): _resolve_po_list(po_val) for lang, po_val in translations.items()
        }

        # Update only the primary (first) PO per language with new POT content
        primary_po_files = [paths[0] for paths in lang_po_map.values()]
        update_po_files(pot_path, primary_po_files)

        pdf_paths: list[Path] = []
        logger.info(f"Processing base language: {base_lang_code}")

        # Generate base language PDF
        pdf_paths.append(
            _generate_single_pdf(
                body,
                metadata,
                input_file,
                input_basename,
                output_dir,
                base_dir,
                config,
                lang_suffix=f"_{base_lang_code}",
                library_po_files=library_po_files,
                validate_images=True,
            )
        )

        # Generate one PDF per listed translation
        for lang, lang_po_files in sorted(lang_po_map.items()):
            lang_code = lang.upper()
            logger.info(f"Processing language: {lang_code}")

            primary_po = lang_po_files[0]
            if not check_po_sync(pot_path, primary_po):
                logger.warning(
                    f"PO file out of sync for {lang_code}: "
                    f"document has changed. PO files are automatically updated on each build."
                )

            stats = get_po_stats(primary_po)
            if stats["untranslated"] > 0 or stats["fuzzy"] > 0:
                logger.warning(
                    f"Translation incomplete for {lang_code}: "
                    f"{stats['untranslated']} untranslated, {stats['fuzzy']} fuzzy"
                )

            pdf_paths.append(
                _generate_single_pdf(
                    body,
                    metadata,
                    input_file,
                    input_basename,
                    output_dir,
                    base_dir,
                    config,
                    lang_suffix=f"_{lang_code}",
                    po_files=lang_po_files,
                    library_po_files=library_po_files,
                    validate_images=False,
                )
            )

        return pdf_paths

    # Single PDF (with optional library PO fallback)
    pdf_path = _generate_single_pdf(
        body,
        metadata,
        input_file,
        input_basename,
        output_dir,
        base_dir,
        config,
        library_po_files=library_po_files,
    )

    return [pdf_path]
