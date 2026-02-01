"""Regression tests comparing generated PDFs against baseline PDFs."""

import logging
import platform
import shutil
import tempfile
from pathlib import Path

import pytest
from diffpdf import diffpdf

from docco.parser import parse_markdown

logger = logging.getLogger(__name__)


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="PDF rendering differences on Windows prevent reliable regression tests",
)
def test_regression_example_pdfs():
    """Test that generated example PDFs match baseline PDFs using diffpdf.

    Outputs all files (PDF + HTML) to tests/output for inspection.
    """
    examples_dir = Path(__file__).parent / ".." / "examples"
    baselines_dir = Path(__file__).parent / "baselines"
    output_dir = Path(__file__).parent / "output"

    # Ensure output and baselines directories exist
    output_dir.mkdir(exist_ok=True, parents=True)
    baselines_dir.mkdir(exist_ok=True, parents=True)

    # Find all example markdown files
    md_files = list(examples_dir.glob("*.md"))

    assert len(md_files) > 0, "No example markdown files found"

    for md_file in md_files:
        # Parse and generate PDFs (keep intermediate HTML for debugging)
        output_files = parse_markdown(
            md_file, output_dir, allow_python=True, keep_intermediate=True
        )

        # Check each generated PDF against baseline
        for pdf_file in output_files:
            filename = pdf_file.name
            baseline_pdf = baselines_dir / filename

            assert baseline_pdf.exists(), (
                f"Baseline missing for {filename} (generated from {md_file.name})"
            )

            # Compare PDFs using diffpdf
            with tempfile.TemporaryDirectory() as diff_dir:  # pragma: no cover
                if diffpdf(
                    str(baseline_pdf), pdf_file, threshold=0.1, output_dir=diff_dir
                ):
                    logger.info(f"✓ Pass: {filename}")
                    continue

                # PDF comparison failed - copy diff files for debugging
                diff_output_dir = output_dir / f"{filename}_diff"
                diff_output_dir.mkdir(exist_ok=True, parents=True)
                for item in Path(diff_dir).iterdir():
                    if item.is_file():
                        shutil.copy2(str(item), str(diff_output_dir / item.name))
                    elif item.is_dir():
                        shutil.copytree(
                            str(item),
                            str(diff_output_dir / item.name),
                            dirs_exist_ok=True,
                        )

                pytest.fail(
                    f"PDF mismatch for {filename} (from {Path(md_file).name}). "
                    f"Diff files saved to {diff_output_dir}"
                )
