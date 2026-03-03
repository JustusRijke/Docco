"""CLI interface for Docco."""

import logging
import shutil
import sys
from pathlib import Path
from typing import Annotated

import cyclopts
from cyclopts import Parameter
from diffpdf import diffpdf

from docco.logging_config import redirect_to_debug, setup_logging
from docco.parser import BuildConfig, parse_markdown
from docco.pdf import html_to_pdf

logger = logging.getLogger(__name__)

CONFIG_FILENAME = ".docco"


def _find_config_dir() -> Path | None:
    """Walk up from CWD to find the directory containing .docco."""
    current = Path.cwd().resolve()
    while True:
        if (current / CONFIG_FILENAME).is_file():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


app = cyclopts.App(
    name="docco",
    help="Convert Markdown to PDF with POT/PO translation support",
    config=cyclopts.config.Toml(  # type: ignore[arg-type]
        ".docco",
        search_parents=True,
        must_exist=False,
        allow_unknown=True,
    ),
    result_action="return_value",
)


@app.default
def main(
    input_file: Annotated[Path | None, Parameter(name=["input-file", "file"])] = None,
    *,
    output: Annotated[Path, Parameter(name=["--output", "-o"])] = Path(),
    keep_intermediate: bool = False,
    verbose: Annotated[bool, Parameter(name=["--verbose", "-v"])] = False,
    log_file: Path | None = None,
    allow_python: bool = False,
    createdir: bool = False,
    filename_template: str | None = None,
    dpi: int | None = None,
    library_po: list[Path] | None = None,
    skip_identical: bool = False,
    diffpdf_threshold: float = 0.1,
    diffpdf_dpi: int = 96,
    diffpdf_skip_text: bool = False,
) -> None:
    """Convert Markdown (or HTML) to PDF."""
    counter = setup_logging(verbose=verbose, log_file=log_file)

    try:
        if input_file is None:
            print(
                "error: No input file specified "
                "(pass as argument or set 'file' in .docco)",
                file=sys.stderr,
            )
            raise SystemExit(1)

        input_files = [input_file] if not isinstance(input_file, list) else input_file

        config_dir = _find_config_dir()
        if config_dir is not None:
            input_files = [
                config_dir / p if not p.is_absolute() else p for p in input_files
            ]
            if library_po:
                library_po = [
                    config_dir / p if not p.is_absolute() else p for p in library_po
                ]

        effective_output = output
        if not createdir and not effective_output.exists():
            effective_output.mkdir(parents=True)

        all_output_files: list[Path] = []
        total_skipped = 0
        for ifile in input_files:
            if not ifile.exists():
                logger.error(f"Input file not found: {ifile}")
                raise SystemExit(1)

            valid_extensions = {".md", ".html", ".htm"}
            if ifile.suffix.lower() not in valid_extensions:
                logger.error(
                    f"Invalid file type: {ifile.suffix}\n"
                    f"Supported formats: {', '.join(sorted(valid_extensions))}"
                )
                raise SystemExit(1)

            out_dir = effective_output / ifile.stem if createdir else effective_output
            if not out_dir.exists():
                out_dir.mkdir(parents=True)

            if ifile.suffix.lower() in {".html", ".htm"}:
                logger.info(f"Processing HTML: {ifile}")
                output_pdf = out_dir / f"{ifile.stem}.pdf"
                tmp_pdf = out_dir / f"{ifile.stem}.pdf-docco"
                try:
                    html_to_pdf(ifile, tmp_pdf)
                    if skip_identical and output_pdf.exists():
                        logger.info(f"Comparing PDF to existing: {output_pdf.name}")
                        with redirect_to_debug():
                            identical = diffpdf(
                                output_pdf,
                                tmp_pdf,
                                threshold=diffpdf_threshold,
                                dpi=diffpdf_dpi,
                                skip_compare_text=diffpdf_skip_text,
                            )
                        if identical:
                            logger.info(f"PDF unchanged, skipping: {output_pdf.name}")
                            tmp_pdf.unlink()
                            total_skipped += 1
                        else:
                            logger.info(f"PDF changed, overwriting: {output_pdf.name}")
                            shutil.move(tmp_pdf, output_pdf)
                    else:
                        shutil.move(tmp_pdf, output_pdf)
                except Exception:
                    if tmp_pdf.exists():
                        tmp_pdf.unlink()
                    raise
                all_output_files.append(output_pdf)
            else:
                output_files, skipped = parse_markdown(
                    ifile,
                    out_dir,
                    config=BuildConfig(
                        keep_intermediate=keep_intermediate,
                        allow_python=allow_python,
                        filename_template=filename_template,
                        dpi=dpi,
                        skip_identical=skip_identical,
                        diffpdf_threshold=diffpdf_threshold,
                        diffpdf_dpi=diffpdf_dpi,
                        skip_compare_text=diffpdf_skip_text,
                    ),
                    library_po_files=library_po,
                )
                all_output_files.extend(output_files)
                total_skipped += skipped

        generated = len(all_output_files) - total_skipped
        summary = (
            f"Generated {generated}, skipped {total_skipped} unchanged"
            if total_skipped
            else f"Successfully generated {generated} output file(s)"
        )
        if counter.error_count > 0 or counter.warning_count > 0:
            parts = []
            if counter.error_count > 0:
                parts.append(f"{counter.error_count} error(s)")
            if counter.warning_count > 0:
                parts.append(f"{counter.warning_count} warning(s)")
            logger.warning(f"{summary} — completed with {', '.join(parts)}")
        else:
            logger.info(summary)
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise SystemExit(1)


def entry_point() -> None:
    app()


if __name__ == "__main__":
    entry_point()
