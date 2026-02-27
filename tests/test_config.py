"""Tests for config file discovery and loading."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from docco.cli import main
from docco.config import find_config, load_config
from docco.parser import _apply_filename_template


@pytest.fixture
def fixture_dir():
    return Path(__file__).parent / "fixtures"


# --- find_config tests ---


def test_find_config_returns_none_when_missing(tmp_path):
    """find_config returns None when no .docco exists in the tree."""
    result = find_config(tmp_path)
    assert result is None


def test_find_config_finds_in_cwd(tmp_path):
    """find_config finds .docco in the start directory."""
    config = tmp_path / ".docco"
    config.write_text("[input]\nfile = 'a.md'\n", encoding="utf-8")
    assert find_config(tmp_path) == config


def test_find_config_finds_in_parent(tmp_path):
    """find_config finds .docco in a parent directory."""
    config = tmp_path / ".docco"
    config.write_text("[input]\nfile = 'a.md'\n", encoding="utf-8")
    subdir = tmp_path / "sub" / "dir"
    subdir.mkdir(parents=True)
    assert find_config(subdir) == config


# --- load_config tests ---


def test_load_config_string_file(tmp_path):
    """load_config normalizes string file to list[Path]."""
    config = tmp_path / ".docco"
    config.write_text("[input]\nfile = 'doc.md'\n", encoding="utf-8")
    result = load_config(config)
    assert result["input"]["file"] == [tmp_path / "doc.md"]


def test_load_config_list_file(tmp_path):
    """load_config normalizes list of strings to list[Path]."""
    config = tmp_path / ".docco"
    config.write_text('[input]\nfile = ["a.md", "b.md"]\n', encoding="utf-8")
    result = load_config(config)
    assert result["input"]["file"] == [tmp_path / "a.md", tmp_path / "b.md"]


def test_load_config_warns_unknown_section(tmp_path, caplog):
    """load_config warns on unknown sections."""
    config = tmp_path / ".docco"
    config.write_text("[unknown]\nfoo = 'bar'\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.config"):
        load_config(config)
    assert "Unknown config section" in caplog.text


def test_load_config_warns_unknown_key(tmp_path, caplog):
    """load_config warns on unknown keys in [input]."""
    config = tmp_path / ".docco"
    config.write_text("[input]\nfile = 'a.md'\nunknown_key = 'x'\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.config"):
        load_config(config)
    assert "Unknown config key in [input]" in caplog.text


def test_load_config_empty_file(tmp_path):
    """load_config returns empty dict for config with no [input] section."""
    config = tmp_path / ".docco"
    config.write_text("", encoding="utf-8")
    result = load_config(config)
    assert result == {}


def test_load_config_output_path(tmp_path):
    """load_config resolves output path relative to config file."""
    config = tmp_path / ".docco"
    config.write_text("[output]\npath = 'out'\n", encoding="utf-8")
    result = load_config(config)
    assert result["output"]["path"] == tmp_path / "out"


def test_load_config_output_unknown_key(tmp_path, caplog):
    """load_config warns on unknown keys in [output]."""
    config = tmp_path / ".docco"
    config.write_text("[output]\nunknown = 'x'\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.config"):
        load_config(config)
    assert "Unknown config key in [output]" in caplog.text


def test_cli_output_path_from_config(tmp_path, monkeypatch):
    """CLI uses output path from [output] config when -o not given."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    out = tmp_path / "myout"
    config = tmp_path / ".docco"
    config.write_text(
        f"[input]\nfile = 'doc.md'\n[output]\npath = '{out}'\n", encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [out / "doc.pdf"]
        main()
        call_output_dir = mock_parse.call_args[0][1]
        assert call_output_dir == out


def test_cli_output_flag_overrides_config(tmp_path, monkeypatch):
    """-o CLI flag takes precedence over config output path."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    cli_out = tmp_path / "cli_out"
    cli_out.mkdir()
    config = tmp_path / ".docco"
    config.write_text(
        "[input]\nfile = 'doc.md'\n[output]\npath = 'config_out'\n", encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["docco", "-o", str(cli_out)])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [cli_out / "doc.pdf"]
        main()
        call_output_dir = mock_parse.call_args[0][1]
        assert call_output_dir == cli_out


def test_load_config_createdir(tmp_path):
    """load_config parses [output] createdir key."""
    config = tmp_path / ".docco"
    config.write_text("[output]\ncreatedir = true\n", encoding="utf-8")
    result = load_config(config)
    assert result["output"]["createdir"] is True


def test_cli_createdir_creates_subdir(tmp_path, monkeypatch):
    """createdir = true routes output to {path}/{stem}/."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    out = tmp_path / "out"
    config = tmp_path / ".docco"
    config.write_text(
        f"[input]\nfile = 'doc.md'\n[output]\npath = '{out}'\ncreatedir = true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [out / "doc" / "doc.pdf"]
        main()
        call_output_dir = mock_parse.call_args[0][1]
        assert call_output_dir == out / "doc"
        assert call_output_dir.exists()


def test_load_config_keep_intermediate(tmp_path):
    """load_config parses [output] keep-intermediate key."""
    config = tmp_path / ".docco"
    config.write_text("[output]\nkeep-intermediate = true\n", encoding="utf-8")
    result = load_config(config)
    assert result["output"]["keep-intermediate"] is True


def test_cli_keep_intermediate_from_config(tmp_path, monkeypatch):
    """CLI reads keep_intermediate from [output] config section."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    config = tmp_path / ".docco"
    config.write_text(
        "[input]\nfile = 'doc.md'\n[output]\nkeep-intermediate = true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        main()
        call_kwargs = mock_parse.call_args[1]
        assert call_kwargs["keep_intermediate"] is True


def test_cli_keep_intermediate_flag_overrides_config(tmp_path, monkeypatch):
    """--keep-intermediate CLI flag takes precedence over config false."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    config = tmp_path / ".docco"
    config.write_text(
        "[input]\nfile = 'doc.md'\n[output]\nkeep-intermediate = false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["docco", "--keep-intermediate"])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        main()
        call_kwargs = mock_parse.call_args[1]
        assert call_kwargs["keep_intermediate"] is True


def test_load_config_python_allow(tmp_path):
    """load_config parses [python] allow key."""
    config = tmp_path / ".docco"
    config.write_text("[python]\nallow = true\n", encoding="utf-8")
    result = load_config(config)
    assert result["python"]["allow"] is True


def test_load_config_python_unknown_key(tmp_path, caplog):
    """load_config warns on unknown keys in [python]."""
    config = tmp_path / ".docco"
    config.write_text("[python]\nallow = true\nunknown = 'x'\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.config"):
        load_config(config)
    assert "Unknown config key in [python]" in caplog.text


def test_cli_allow_python_from_config(tmp_path, monkeypatch):
    """CLI reads allow_python from [python] config section."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    config = tmp_path / ".docco"
    config.write_text(
        "[input]\nfile = 'doc.md'\n[python]\nallow = true\n", encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        main()
        call_kwargs = mock_parse.call_args[1]
        assert call_kwargs["allow_python"] is True


def test_cli_allow_python_flag_overrides_config(tmp_path, monkeypatch):
    """--allow-python CLI flag takes precedence; config false doesn't suppress it."""
    md = tmp_path / "doc.md"
    md.write_text("# Doc", encoding="utf-8")
    config = tmp_path / ".docco"
    config.write_text(
        "[input]\nfile = 'doc.md'\n[python]\nallow = false\n", encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["docco", "--allow-python"])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "doc.pdf"]
        main()
        call_kwargs = mock_parse.call_args[1]
        assert call_kwargs["allow_python"] is True


def test_load_config_multilingual_filename(tmp_path):
    """load_config parses [multilingual] filename key."""
    config = tmp_path / ".docco"
    config.write_text(
        '[multilingual]\nfilename = "{filename}_{langcode}"\n', encoding="utf-8"
    )
    result = load_config(config)
    assert result["multilingual"]["filename"] == "{filename}_{langcode}"


def test_load_config_multilingual_unknown_key(tmp_path, caplog):
    """load_config warns on unknown keys in [multilingual]."""
    config = tmp_path / ".docco"
    config.write_text("[multilingual]\nunknown = 'x'\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="docco.config"):
        load_config(config)
    assert "Unknown config key in [multilingual]" in caplog.text


def test_apply_filename_template_default():
    """Default template produces {filename}_{langcode}."""
    assert _apply_filename_template("{filename}_{langcode}", "doc", "EN") == "doc_EN"


def test_apply_filename_template_custom():
    """Custom template is substituted correctly."""
    assert (
        _apply_filename_template("{langcode}-{filename}", "report", "DE") == "DE-report"
    )


# --- CLI integration tests ---


def test_cli_uses_config_when_no_arg(fixture_dir, monkeypatch):
    """CLI picks up input file from .docco config when no arg given."""
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(fixture_dir)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [fixture_dir / "simple.pdf"]
        main()
        mock_parse.assert_called_once()
        call_input = mock_parse.call_args[0][0]
        assert call_input.name == "simple.md"


def test_cli_arg_overrides_config(fixture_dir, tmp_path, monkeypatch):
    """CLI input_file arg takes precedence over .docco config."""
    # Create a config pointing at simple.md
    config = tmp_path / ".docco"
    config.write_text(
        f"[input]\nfile = '{fixture_dir / 'simple.md'}'\n", encoding="utf-8"
    )
    # Create another md file to pass as CLI arg
    other_md = tmp_path / "other.md"
    other_md.write_text("# Other", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["docco", str(other_md)])
    monkeypatch.chdir(tmp_path)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [tmp_path / "other.pdf"]
        main()
        call_input = mock_parse.call_args[0][0]
        assert call_input.name == "other.md"


def test_cli_no_input_no_config_exits(tmp_path, monkeypatch):
    """CLI exits with error when no input_file and no .docco config."""
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code != 0


def test_cli_config_in_parent_directory(fixture_dir, monkeypatch):
    """CLI finds .docco in a parent directory when run from a subdirectory."""
    subdir = fixture_dir / "subdir_for_config_test"
    subdir.mkdir(exist_ok=True)
    monkeypatch.setattr("sys.argv", ["docco"])
    monkeypatch.chdir(subdir)

    with patch("docco.cli.parse_markdown") as mock_parse:
        mock_parse.return_value = [fixture_dir / "simple.pdf"]
        main()
        mock_parse.assert_called_once()
        call_input = mock_parse.call_args[0][0]
        assert call_input.name == "simple.md"
