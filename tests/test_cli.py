import logging

import pytest

from docco.cli import _print_summary, _save_intermediate, main, parse_args
from docco.context import ContentType, Context
from docco.logging_config import LogCounter
from docco.pipeline import PipelineError


@pytest.fixture(autouse=True)
def reset_docco_logger():
    log = logging.getLogger("docco")
    original_propagate = log.propagate
    yield
    log.propagate = original_propagate


def test_parse_args_single_input():
    args = parse_args(["input.md", "-o", "out"])
    assert len(args.input) == 1
    assert str(args.input[0]) == "input.md"
    assert str(args.output) == "out"
    assert args.verbose is False
    assert args.config is None


def test_parse_args_multiple_inputs():
    args = parse_args(["a.md", "b.md", "-o", "out"])
    assert len(args.input) == 2
    assert str(args.input[0]) == "a.md"
    assert str(args.input[1]) == "b.md"


def test_parse_args_no_input():
    args = parse_args(["-o", "out"])
    assert args.input == []


def test_parse_args_all_options():
    args = parse_args(["doc.md", "-o", "build", "--verbose", "--config", "my.toml"])
    assert str(args.input[0]) == "doc.md"
    assert str(args.output) == "build"
    assert args.verbose is True
    assert str(args.config) == "my.toml"


def test_main_missing_input_file(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text('file = "x.md"\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["nonexistent.md", "-o", str(tmp_path), "--config", str(config)])


def test_main_no_config_raises(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello", encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main([str(md), "-o", str(tmp_path / "out")])


def test_main_pipeline_error_exits(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello $$undefined_var$$\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text("[vars]\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main([str(md), "-o", str(tmp_path / "out"), "--config", str(config)])


def test_main_pipeline_error_saves_intermediate_by_default(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello $$undefined_var$$\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text("[vars]\n", encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(SystemExit, match="1"):
        main([str(md), "-o", str(out), "--config", str(config)])
    intermediates = list(out.glob("test.intermediate.*"))
    assert len(intermediates) == 1


def test_main_pipeline_error_no_save_intermediate(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello $$undefined_var$$\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(
        "[vars]\n\n[error]\nsave_intermediate = false\n", encoding="utf-8"
    )
    out = tmp_path / "out"
    with pytest.raises(SystemExit, match="1"):
        main([str(md), "-o", str(out), "--config", str(config)])
    assert not list(out.glob("test.intermediate.*"))


def test_main_no_input_no_file_key(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text('[html]\ntemplate = "x"\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["-o", str(tmp_path / "out"), "--config", str(config)])


def test_main_missing_input_file_from_config(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text('file = "missing.md"\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["-o", str(tmp_path / "out"), "--config", str(config)])


def test_main_empty_file_list_from_config(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text("file = []\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["-o", str(tmp_path / "out"), "--config", str(config)])


def test_main_end_to_end(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello\n\nWorld\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text('file = "test.md"\n', encoding="utf-8")
    out = tmp_path / "out"

    main([str(md), "-o", str(out), "--config", str(config)])

    pdf = out / "test.pdf"
    assert pdf.exists()
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_main_file_from_config(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# From config\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(f'file = "{md}"\n', encoding="utf-8")
    out = tmp_path / "out"

    main(["-o", str(out), "--config", str(config)])

    assert (out / "doc.pdf").exists()


def test_main_file_list_from_config(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("# A\n", encoding="utf-8")
    b.write_text("# B\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(
        f'file = ["{a}", "{b}"]\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"

    main(["-o", str(out), "--config", str(config)])

    assert (out / "a.pdf").exists()
    assert (out / "b.pdf").exists()


def test_main_cli_overrides_config_file(tmp_path):
    cli_md = tmp_path / "cli.md"
    config_md = tmp_path / "config.md"
    cli_md.write_text("# CLI\n", encoding="utf-8")
    config_md.write_text("# Config\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(
        f'file = "{config_md}"\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"

    main([str(cli_md), "-o", str(out), "--config", str(config)])

    assert (out / "cli.pdf").exists()
    assert not (out / "config.pdf").exists()


def test_main_log_config(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello\n", encoding="utf-8")
    log_file = tmp_path / "docco.log"
    config = tmp_path / "docco.toml"
    config.write_text(
        f'file = "test.md"\n\n[log]\nfile = "{log_file}"\nlevel = "debug"\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"

    main([str(md), "-o", str(out), "--config", str(config)])

    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    assert len(log_content) > 0


def test_main_html_input_to_pdf(tmp_path):
    html = tmp_path / "test.html"
    html.write_text("<html><body><h1>Hello</h1></body></html>", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text('file = "test.html"\n', encoding="utf-8")
    out = tmp_path / "out"

    main([str(html), "-o", str(out), "--config", str(config)])

    pdf = out / "test.pdf"
    assert pdf.exists()
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_main_htm_input_to_pdf(tmp_path):
    htm = tmp_path / "test.htm"
    htm.write_text("<html><body><p>Htm test</p></body></html>", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text('file = "test.htm"\n', encoding="utf-8")
    out = tmp_path / "out"

    main([str(htm), "-o", str(out), "--config", str(config)])

    assert (out / "test.pdf").exists()


def test_main_diffpdf_identical_skips(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello\n\nWorld\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(
        'file = "test.md"\n\n[diffpdf]\nenable = true\nthreshold = 0.1\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()

    main([str(md), "-o", str(out), "--config", str(config)])
    pdf = out / "test.pdf"
    assert pdf.exists()

    mtime_before = pdf.stat().st_mtime
    main([str(md), "-o", str(out), "--config", str(config)])
    assert pdf.stat().st_mtime == mtime_before


def test_main_diffpdf_different_writes(tmp_path):
    from unittest.mock import patch

    md = tmp_path / "test.md"
    md.write_text("# Hello\n\nWorld\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(
        'file = "test.md"\n\n[diffpdf]\nenable = true\nthreshold = 0.1\n',
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()

    no_diff_config = tmp_path / "nodiff.toml"
    no_diff_config.write_text('file = "test.md"\n', encoding="utf-8")
    main([str(md), "-o", str(out), "--config", str(no_diff_config)])

    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf", return_value=False):
        main([str(md), "-o", str(out), "--config", str(config)])

    new_content = (out / "test.pdf").read_bytes()
    assert new_content[:5] == b"%PDF-"
    assert "skipped" not in str(new_content)


def test_print_summary_no_issues(caplog):
    counter = LogCounter()
    with caplog.at_level(logging.INFO, logger="docco"):
        _print_summary(3, 0, counter)
    assert "Generated 3 file(s)" in caplog.text


def test_print_summary_with_skipped(caplog):
    counter = LogCounter()
    with caplog.at_level(logging.INFO, logger="docco"):
        _print_summary(2, 1, counter)
    assert "skipped 1 unchanged" in caplog.text


def test_print_summary_with_warnings(caplog):
    counter = LogCounter()
    counter.warning_count = 2
    counter.error_count = 1
    with caplog.at_level(logging.INFO, logger="docco"):
        _print_summary(1, 0, counter)
    assert "2 warning(s)" in caplog.text
    assert "1 error(s)" in caplog.text


def test_save_intermediate_bytes(tmp_path):
    ctx = Context(
        source_path=tmp_path / "doc.md",
        output_dir=tmp_path,
        config={},
        content=b"%PDF-fake",
        content_type=ContentType.PDF,
    )
    err = PipelineError("fail", [ctx])
    _save_intermediate(err)
    out = tmp_path / "doc.intermediate.pdf"
    assert out.exists()
    assert out.read_bytes() == b"%PDF-fake"
