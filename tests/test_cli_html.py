"""Tests for CLI HTML input support."""

from unittest.mock import patch

import pytest

from docco.cli import app


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

    with patch("docco.cli.html_to_pdf") as mock_html_to_pdf:
        app([str(html_file), "-o", str(output_dir)], exit_on_error=False)
        mock_html_to_pdf.assert_called_once()
        args = mock_html_to_pdf.call_args[0]
        assert args[0] == html_file
        assert args[1] == output_dir / "test.pdf"


def test_html_input_with_htm_extension(tmp_path):
    """.htm extension is also recognized as HTML."""
    html_file = tmp_path / "test.htm"
    html_file.write_text("<html><body><p>Content</p></body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("docco.cli.html_to_pdf") as mock_html_to_pdf:
        app([str(html_file), "-o", str(output_dir)], exit_on_error=False)
        mock_html_to_pdf.assert_called_once()


def test_markdown_input_uses_full_pipeline(tmp_path):
    """Markdown files use the parse_markdown pipeline."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test\n\nContent", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("docco.cli.parse_markdown") as mock_parse_markdown:
        mock_parse_markdown.return_value = [output_dir / "test.pdf"]
        app([str(md_file), "-o", str(output_dir)], exit_on_error=False)
        mock_parse_markdown.assert_called_once()


def test_html_input_ignores_markdown_specific_flags(tmp_path):
    """HTML input accepts --allow-python and --po flags without error."""
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body>Test</body></html>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("docco.cli.html_to_pdf") as mock_html_to_pdf:
        app(
            [
                str(html_file),
                "-o",
                str(output_dir),
                "--allow-python",
                "--po",
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
            with patch("docco.cli.html_to_pdf"):
                mock_parse.return_value = [output_dir / "test.pdf"]
                app([str(test_file), "-o", str(output_dir)], exit_on_error=False)
