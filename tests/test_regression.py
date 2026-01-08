"""Regression tests comparing generated PDFs against baseline PDFs."""

import glob
import logging
import os
import shutil
import tempfile

import pytest
from diffpdf import diffpdf

from docco.parser import parse_markdown

logger = logging.getLogger(__name__)


def test_regression_example_pdfs():
    """Test that generated example PDFs match baseline PDFs using diffpdf.

    Outputs all files (PDF + HTML) to tests/output for inspection.
    """
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
    baselines_dir = os.path.join(os.path.dirname(__file__), "baselines")
    output_dir = os.path.join(os.path.dirname(__file__), "output")

    # Ensure output and baselines directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(baselines_dir, exist_ok=True)

    # Find all example markdown files
    md_files = glob.glob(os.path.join(examples_dir, "*.md"))

    assert len(md_files) > 0, "No example markdown files found"

    for md_file in md_files:
        # Parse and generate PDFs (keep intermediate HTML for debugging)
        output_files = parse_markdown(
            md_file, output_dir, allow_python=True, keep_intermediate=True
        )

        # Check each generated PDF against baseline
        for pdf_file in output_files:
            filename = os.path.basename(pdf_file)
            baseline_pdf = os.path.join(baselines_dir, filename)

            assert os.path.exists(baseline_pdf), (
                f"Baseline missing for {filename} (generated from {os.path.basename(md_file)})"
            )

            # Compare PDFs using diffpdf
            with tempfile.TemporaryDirectory() as diff_dir:
                if diffpdf(baseline_pdf, pdf_file, threshold=0.1, output_dir=diff_dir):
                    logger.info(f"✓ Pass: {filename}")
                    continue

                # PDF comparison failed - copy diff files for debugging
                diff_output_dir = os.path.join(output_dir, f"{filename}_diff")
                os.makedirs(diff_output_dir, exist_ok=True)
                for item in os.listdir(diff_dir):
                    src = os.path.join(diff_dir, item)
                    dst = os.path.join(diff_output_dir, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                    elif os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)

                pytest.fail(
                    f"PDF mismatch for {filename} (from {os.path.basename(md_file)}). "
                    f"Diff files saved to {diff_output_dir}"
                )
