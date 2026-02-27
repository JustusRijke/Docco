"""Tests for .docco config file integration via CLI."""

from pathlib import Path
from unittest.mock import patch

import pytest

from docco.cli import app
from docco.parser import _apply_filename_template


@pytest.fixture
def fixture_dir():
    return Path(__file__).parent / "fixtures"


# --- .docco config tests ---


def test_cli_uses_config_file(fixture_dir, monkeypatch):
    """CLI picks up 'file' from .docco when no argument given."""
    monkeypatch.chdir(fixture_dir)
    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [fixture_dir / "simple.pdf"]
        app([], exit_on_error=False)
        call_input = mock_parse.call_args[0][0]
        assert call_input.name == "simple.md"


def test_cli_arg_overrides_config(fixture_dir, tmp_path, monkeypatch):
    """Positional input_file overrides 'file' in .docco config."""
    (tmp_path / ".docco").write_text(
        f"file = '{fixture_dir / 'simple.md'}'\n", encoding="utf-8"
    )
    other = tmp_path / "other.md"
    other.write_text("# Other", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "other.pdf"]
        app([str(other)], exit_on_error=False)
        assert mock_parse.call_args[0][0].name == "other.md"


def test_cli_no_input_no_config_exits(tmp_path, monkeypatch):
    """Exits with error when no input_file and no .docco config."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        app([], exit_on_error=False)
    assert exc_info.value.code != 0


def test_cli_config_in_parent_directory(fixture_dir, monkeypatch):
    """CLI finds .docco in a parent directory when run from a subdirectory."""
    subdir = fixture_dir / "subdir_for_config_test"
    subdir.mkdir(exist_ok=True)
    monkeypatch.chdir(subdir)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [fixture_dir / "simple.pdf"]
        app([], exit_on_error=False)
        assert mock_parse.call_args[0][0].name == "simple.md"


def test_cli_allow_python_from_config(tmp_path, monkeypatch):
    """allow-python from config is passed to parse_markdown."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    (tmp_path / ".docco").write_text(
        "file = 'doc.md'\nallow-python = true\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        app([], exit_on_error=False)
        assert mock_parse.call_args[1]["allow_python"] is True


def test_cli_allow_python_flag_overrides_config(tmp_path, monkeypatch):
    """--allow-python CLI flag works regardless of config."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    (tmp_path / ".docco").write_text(
        "file = 'doc.md'\nallow-python = false\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        app(["--allow-python"], exit_on_error=False)
        assert mock_parse.call_args[1]["allow_python"] is True


def test_cli_output_path_from_config(tmp_path, monkeypatch):
    """output path from config is used when -o not given."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    out = tmp_path / "myout"
    (tmp_path / ".docco").write_text(
        f"file = 'doc.md'\noutput = '{out}'\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [out / "doc.pdf"]
        app([], exit_on_error=False)
        assert mock_parse.call_args[0][1] == out


def test_cli_output_flag_overrides_config(tmp_path, monkeypatch):
    """-o CLI flag overrides config output path."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    cli_out = tmp_path / "cli_out"
    cli_out.mkdir()
    (tmp_path / ".docco").write_text(
        "file = 'doc.md'\noutput = 'config_out'\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [cli_out / "doc.pdf"]
        app(["-o", str(cli_out)], exit_on_error=False)
        assert mock_parse.call_args[0][1] == cli_out


def test_cli_keep_intermediate_from_config(tmp_path, monkeypatch):
    """keep-intermediate from config is passed to parse_markdown."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    (tmp_path / ".docco").write_text(
        "file = 'doc.md'\nkeep-intermediate = true\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        app([], exit_on_error=False)
        assert mock_parse.call_args[1]["keep_intermediate"] is True


def test_cli_createdir_creates_subdir(tmp_path, monkeypatch):
    """createdir = true routes output to {output}/{stem}/."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    out = tmp_path / "out"
    (tmp_path / ".docco").write_text(
        f"file = 'doc.md'\noutput = '{out}'\ncreatedir = true\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [out / "doc" / "doc.pdf"]
        app([], exit_on_error=False)
        assert mock_parse.call_args[0][1] == out / "doc"
        assert (out / "doc").exists()


# --- filename template tests ---


def test_apply_filename_template_default():
    assert _apply_filename_template("{filename}_{langcode}", "doc", "EN") == "doc_EN"


def test_apply_filename_template_custom():
    assert (
        _apply_filename_template("{langcode}-{filename}", "report", "DE") == "DE-report"
    )
