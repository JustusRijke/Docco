"""Regression tests comparing generated PDFs against baseline checksums."""

import hashlib
import os
import glob
import tempfile
from docco.parser import parse_markdown


def get_file_checksum(filepath):
    """Calculate MD5 checksum of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def test_regression_example_pdfs():
    """Test that generated example PDFs match baseline PDFs by checksum.

    Outputs all files (PDF + HTML) to tests/output for inspection.
    """
    examples_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "examples"
    )
    baselines_dir = os.path.join(
        os.path.dirname(__file__),
        "baselines"
    )
    output_dir = os.path.join(
        os.path.dirname(__file__),
        "output"
    )

    # Ensure output and baselines directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(baselines_dir, exist_ok=True)

    # Find all example markdown files
    md_files = glob.glob(os.path.join(examples_dir, "*.md"))

    assert len(md_files) > 0, "No example markdown files found"

    for md_file in md_files:
        # Parse and generate PDFs (keep intermediate HTML for debugging)
        output_files = parse_markdown(md_file, output_dir, allow_python=True, keep_intermediate=True)

        # Check each generated PDF against baseline
        for pdf_file in output_files:
            filename = os.path.basename(pdf_file)
            baseline_pdf = os.path.join(baselines_dir, filename)

            assert os.path.exists(baseline_pdf), \
                f"Baseline missing for {filename} (generated from {os.path.basename(md_file)})"

            actual_checksum = get_file_checksum(pdf_file)
            baseline_checksum = get_file_checksum(baseline_pdf)

            assert actual_checksum == baseline_checksum, \
                f"PDF mismatch for {filename} (from {os.path.basename(md_file)})"


