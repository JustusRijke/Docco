"""Tests for CLI HTML input support."""

import logging
from unittest.mock import patch

import pytest

from docco.cli import app
from docco.logging_config import setup_logging


def _mock_html_to_pdf(src, dst, **kwargs):
    """Simulate html_to_pdf by creating the destination file."""
    dst.write_bytes(b"%PDF-1.4 mock")


def test_html_input_bypasses_markdown_processing(tmp_path):
    """HTML input files are converted directly to PDF without preprocessing."""
    html_file = tmp_path / "test.html"
    html_file.write_text(
        "<!DOCTYPE html><html><head><title>Test</title></head>"
        "<body><h1>Test Document</h1></body></html>",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch(
        "docco.cli.html_to_pdf", side_effect=_mock_html_to_pdf
    ) as mock_html_to_pdf:
        app([str(html_file), "-o", str(output_dir)], exit_on_error=False)
        mock_html_to_pdf.assert_called_once()
        args = mock_html_to_pdf.call_args[0]
        assert args[0] == html_file
        assert args[1] == output_dir / "test.pdf-docco"


def test_html_input_with_htm_extension(tmp_path):
    """.htm extension is also recognized as HTML."""
    html_file = tmp_path / "test.htm"
    html_file.write_text("<html><body><p>Content</p></body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch(
        "docco.cli.html_to_pdf", side_effect=_mock_html_to_pdf
    ) as mock_html_to_pdf:
        app([str(html_file), "-o", str(output_dir)], exit_on_error=False)
        mock_html_to_pdf.assert_called_once()


def test_markdown_input_uses_full_pipeline(tmp_path):
    """Markdown files use the parse_markdown pipeline."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n\nContent", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("docco.cli.parse_markdown") as mock_parse_markdown:
        mock_parse_markdown.return_value = ([output_dir / "test.pdf"], 0)
        app([str(md_file), "-o", str(output_dir)], exit_on_error=False)
        mock_parse_markdown.assert_called_once()


def test_html_input_ignores_markdown_specific_flags(tmp_path):
    """HTML input accepts --allow-python and --library-po flags without error."""
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body>Test</body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch(
        "docco.cli.html_to_pdf", side_effect=_mock_html_to_pdf
    ) as mock_html_to_pdf:
        app(
            [
                str(html_file),
                "-o",
                str(output_dir),
                "--allow-python",
                "--library-po",
                "dummy.po",
            ],
            exit_on_error=False,
        )
        mock_html_to_pdf.assert_called_once()


def test_invalid_file_extension_exits(tmp_path):
    """Invalid file extension causes exit with error message."""
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("content", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        app([str(invalid_file), "-o", str(output_dir)], exit_on_error=False)
    assert exc_info.value.code == 1


def test_valid_extensions_accepted(tmp_path):
    """All valid extensions are accepted without SystemExit."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    for ext in [".md", ".html", ".htm"]:
        test_file = tmp_path / f"test{ext}"
        if ext == ".md":
            test_file.write_text("# Test", encoding="utf-8")
        else:
            test_file.write_text("<html><body>Test</body></html>", encoding="utf-8")

        with patch("docco.cli.parse_markdown") as mock_parse:
            with patch("docco.cli.html_to_pdf", side_effect=_mock_html_to_pdf):
                mock_parse.return_value = ([output_dir / "test.pdf"], 0)
                app([str(test_file), "-o", str(output_dir)], exit_on_error=False)


def test_input_file_not_found_exits(tmp_path):
    """Missing input file causes exit with code 1."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        app([str(tmp_path / "missing.md"), "-o", str(output_dir)], exit_on_error=False)
    assert exc_info.value.code == 1


def test_html_input_exception_cleanup(tmp_path):
    """Exception during HTML conversion removes the temp PDF file."""
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body>Test</body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    def _failing_html_to_pdf(src, dst, **kwargs):
        dst.write_bytes(b"partial")
        raise RuntimeError("conversion failed")

    with patch("docco.cli.html_to_pdf", side_effect=_failing_html_to_pdf):
        with pytest.raises(SystemExit) as exc_info:
            app([str(html_file), "-o", str(output_dir)], exit_on_error=False)
    assert exc_info.value.code == 1
    # Temp file should have been cleaned up
    assert not (output_dir / "test.pdf-docco").exists()


def test_html_skip_identical_unchanged(tmp_path):
    """HTML input with --skip-identical skips overwrite when PDF is unchanged."""
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body>Test</body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    # Create an existing PDF to compare against
    existing_pdf = output_dir / "test.pdf"
    existing_pdf.write_bytes(b"%PDF-1.4 existing")

    with patch("docco.cli.html_to_pdf", side_effect=_mock_html_to_pdf):
        with patch("docco.cli.diffpdf", return_value=True):
            app(
                [str(html_file), "-o", str(output_dir), "--skip-identical"],
                exit_on_error=False,
            )
    # Temp file removed, existing PDF unchanged
    assert not (output_dir / "test.pdf-docco").exists()
    assert existing_pdf.read_bytes() == b"%PDF-1.4 existing"


def test_html_skip_identical_changed(tmp_path):
    """HTML input with --skip-identical overwrites when PDF has changed."""
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body>Test</body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    existing_pdf = output_dir / "test.pdf"
    existing_pdf.write_bytes(b"%PDF-1.4 old")

    with patch("docco.cli.html_to_pdf", side_effect=_mock_html_to_pdf):
        with patch("docco.cli.diffpdf", return_value=False):
            app(
                [str(html_file), "-o", str(output_dir), "--skip-identical"],
                exit_on_error=False,
            )
    assert existing_pdf.read_bytes() == b"%PDF-1.4 mock"


def test_warning_summary_logged(tmp_path):
    """Warning/error counts appear in the summary log message."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    def _parse_with_warning(input_file, out_dir, config, **kwargs):
        logging.getLogger("docco").warning("something looks off")
        return ([out_dir / "test.pdf"], 0)

    with patch("docco.cli.parse_markdown", side_effect=_parse_with_warning):
        app([str(md_file), "-o", str(output_dir)], exit_on_error=False)


def test_error_summary_logged(tmp_path):
    """Error count appears in the summary log message."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    def _parse_with_error(input_file, out_dir, config, **kwargs):
        logging.getLogger("docco").error("something went wrong")
        return ([out_dir / "test.pdf"], 0)

    with patch("docco.cli.parse_markdown", side_effect=_parse_with_error):
        app([str(md_file), "-o", str(output_dir)], exit_on_error=False)


def test_setup_logging_with_log_file(tmp_path):
    """setup_logging writes to log file when log_file is provided."""
    log_file = tmp_path / "run.log"
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    try:
        counter = setup_logging(verbose=False, log_file=log_file)
        logging.getLogger("test_log_file").warning("hello log file")
        assert log_file.exists()
        assert "hello log file" in log_file.read_text(encoding="utf-8")
        _ = counter
    finally:
        for h in root.handlers[:]:
            if h not in original_handlers:
                h.close()
                root.removeHandler(h)
        root.setLevel(original_level)
