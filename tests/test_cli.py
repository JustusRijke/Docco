# Edge-case tests only. The happy path is covered by tests/test_regression.py.
import pytest

from docco.cli import _print_summary, _save_intermediate, main, parse_args
from docco.context import ContentType, Context
from docco.logging_config import LogCounter
from docco.pipeline import PipelineError


def test_parse_args_all_options():
    args = parse_args(["doc.md", "-o", "build", "--verbose", "--config", "my.toml"])
    assert args.verbose is True
    assert str(args.config) == "my.toml"


def test_main_no_config_raises(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello", encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main([str(md), "-o", str(tmp_path / "out")])


def test_main_missing_input_file(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text('file = "x.md"\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["nonexistent.md", "-o", str(tmp_path), "--config", str(config)])


def test_main_no_input_no_file_key(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text('[html]\ntemplate = "x"\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["-o", str(tmp_path / "out"), "--config", str(config)])


def test_main_empty_file_list_from_config(tmp_path):
    config = tmp_path / "docco.toml"
    config.write_text("file = []\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["-o", str(tmp_path / "out"), "--config", str(config)])


def test_main_html_input_to_pdf(tmp_path):
    html = tmp_path / "test.html"
    html.write_text("<html><body><h1>Hello</h1></body></html>", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text('file = "test.html"\n', encoding="utf-8")
    main([str(html), "-o", str(tmp_path / "out"), "--config", str(config)])
    assert (tmp_path / "out" / "test.pdf").exists()


def test_main_pipeline_error_saves_intermediate(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("Hello $$undefined_var$$\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text("[vars]\n", encoding="utf-8")
    out = tmp_path / "out"
    with pytest.raises(SystemExit, match="1"):
        main([str(md), "-o", str(out), "--config", str(config)])
    assert len(list(out.glob("test.intermediate.*"))) == 1


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


def test_main_log_config(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello\n", encoding="utf-8")
    log_file = tmp_path / "docco.log"
    config = tmp_path / "docco.toml"
    config.write_text(
        f'file = "test.md"\n\n[log]\nfile = "{log_file.as_posix()}"\nlevel = "debug"\n',
        encoding="utf-8",
    )
    main([str(md), "-o", str(tmp_path / "out"), "--config", str(config)])
    assert log_file.exists()


def test_save_intermediate_str(tmp_path):
    ctx = Context(
        source_path=tmp_path / "doc.md",
        output_dir=tmp_path,
        config={},
        content="<p>hello</p>",
        content_type=ContentType.HTML,
    )
    _save_intermediate(PipelineError("fail", [ctx]))
    out = tmp_path / "doc.intermediate.html"
    assert out.read_text(encoding="utf-8") == "<p>hello</p>"


def test_save_intermediate_bytes(tmp_path):
    ctx = Context(
        source_path=tmp_path / "doc.md",
        output_dir=tmp_path,
        config={},
        content=b"%PDF-1.4",
        content_type=ContentType.PDF,
    )
    _save_intermediate(PipelineError("fail", [ctx]))
    assert (tmp_path / "doc.intermediate.pdf").read_bytes() == b"%PDF-1.4"


def test_main_file_list_from_config(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("# Hello\n", encoding="utf-8")
    config = tmp_path / "docco.toml"
    config.write_text(f'file = ["{md.as_posix()}"]\n', encoding="utf-8")
    main(["-o", str(tmp_path / "out"), "--config", str(config)])


def test_print_summary_with_skipped(caplog):
    import logging

    counter = LogCounter()
    with caplog.at_level(logging.INFO, logger="docco"):
        _print_summary(2, 1, counter)
    assert "skipped 1 unchanged" in caplog.text


def test_print_summary_with_warnings(caplog):
    import logging

    counter = LogCounter()
    counter.warning_count = 2
    counter.error_count = 1
    with caplog.at_level(logging.INFO, logger="docco"):
        _print_summary(1, 0, counter)
    assert "2 warning(s)" in caplog.text
