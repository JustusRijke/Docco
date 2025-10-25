"""
Regression tests for PDF output stability.

These tests ensure that code changes (refactoring, library updates, etc.)
don't unexpectedly change PDF output. Baselines are committed to git.
"""

import hashlib
from pathlib import Path
from click.testing import CliRunner
from docco.cli import cli


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class TestRegressionExamples:
    """Regression tests comparing generated PDFs against committed baselines."""

    def test_feature_showcase_regression(self, tmp_path):
        """Test that Feature Showcase.md generates identical PDF."""
        # Setup
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        baselines_dir = Path(__file__).parent.parent / "baselines"

        md_file = examples_dir / "Feature Showcase.md"
        css_file = examples_dir / "style.css"
        output_pdf = tmp_path / "Feature Showcase.pdf"
        baseline_pdf = baselines_dir / "Feature Showcase.pdf"

        # Generate PDF
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"PDF generation failed: {result.output}"
        assert output_pdf.exists(), "PDF was not created"
        assert baseline_pdf.exists(), f"Baseline PDF not found at {baseline_pdf}"

        # Compare hashes
        generated_hash = get_file_hash(output_pdf)
        baseline_hash = get_file_hash(baseline_pdf)

        assert generated_hash == baseline_hash, (
            f"PDF output changed! Generated hash: {generated_hash}, "
            f"Baseline hash: {baseline_hash}"
        )

    def test_multilingual_example_regression(self, tmp_path):
        """Test that Multilingual Example.md generates identical PDFs for all languages."""
        # Setup
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        baselines_dir = Path(__file__).parent.parent / "baselines"

        md_file = examples_dir / "Multilingual Example.md"
        css_file = examples_dir / "style.css"
        output_pdf = tmp_path / "Multilingual Example.pdf"
        baseline_dir = baselines_dir

        # Generate PDFs
        runner = CliRunner()
        result = runner.invoke(
            cli, ["build", str(md_file), str(css_file), "-o", str(output_pdf)]
        )

        # Verify success
        assert result.exit_code == 0, f"PDF generation failed: {result.output}"

        # Check each language variant
        languages = ["EN", "DE", "NL"]
        for lang in languages:
            generated_pdf = tmp_path / f"Multilingual Example_{lang}.pdf"
            baseline_pdf = baseline_dir / f"Multilingual Example_{lang}.pdf"

            assert generated_pdf.exists(), f"Generated {lang} PDF not created"
            assert baseline_pdf.exists(), f"Baseline {lang} PDF not found"

            # Compare hashes
            generated_hash = get_file_hash(generated_pdf)
            baseline_hash = get_file_hash(baseline_pdf)

            assert generated_hash == baseline_hash, (
                f"[{lang}] PDF output changed! Generated hash: {generated_hash}, "
                f"Baseline hash: {baseline_hash}"
            )
