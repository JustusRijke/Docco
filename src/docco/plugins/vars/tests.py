from datetime import UTC, datetime

from docco.context import ContentType, Context
from docco.plugins.vars import Stage


def make_ctx(tmp_path, content, vars_config=None):
    md = tmp_path / "test.md"
    md.write_text(content, encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", {"vars": vars_config or {}})
    ctx.content = content
    ctx.content_type = ContentType.HTML
    return ctx


def test_basic_substitution(tmp_path):
    ctx = make_ctx(tmp_path, "<p>Hello $$name$$!</p>", {"name": "World"})
    result = Stage().process(ctx)
    assert result.content == "<p>Hello World!</p>"


def test_path_builtin(tmp_path):
    ctx = make_ctx(tmp_path, "<p>path=$$PATH$$</p>")
    result = Stage().process(ctx)
    assert result.content == f"<p>path={tmp_path}</p>"


def test_reserved_var_warning(tmp_path, caplog):
    import logging

    ctx = make_ctx(tmp_path, "<p>$$PATH$$</p>", {"PATH": "override"})
    with caplog.at_level(logging.WARNING, logger="docco.plugins.vars"):
        result = Stage().process(ctx)
    assert "reserved" in caplog.text
    assert result.content == f"<p>{tmp_path}</p>"


def test_no_vars(tmp_path):
    ctx = make_ctx(tmp_path, "<p>No vars here</p>")
    result = Stage().process(ctx)
    assert result.content == "<p>No vars here</p>"


def test_undefined_var_raises(tmp_path):
    import pytest

    ctx = make_ctx(tmp_path, "<p>$$undefined$$</p>")
    with pytest.raises(ValueError, match="undefined"):
        Stage().process(ctx)


def test_date_builtins(tmp_path):
    today = datetime.now(tz=UTC).date()
    ctx = make_ctx(tmp_path, "$$DAY$$/$$MONTH$$/$$YEAR$$")
    result = Stage().process(ctx)
    assert result.content == f"{today.day:02d}/{today.month:02d}/{today.year}"


def test_unused_var_warning(tmp_path, caplog):
    import logging

    ctx = make_ctx(tmp_path, "<p>$$name$$</p>", {"name": "World", "unused": "x"})
    with caplog.at_level(logging.WARNING, logger="docco.plugins.vars"):
        Stage().process(ctx)
    assert "unused" in caplog.text.lower()
    assert "unused" in caplog.text


def test_date_builtins_reserved(tmp_path, caplog):
    import logging

    ctx = make_ctx(tmp_path, "$$YEAR$$", {"YEAR": "2000", "DAY": "1", "MONTH": "1"})
    with caplog.at_level(logging.WARNING, logger="docco.plugins.vars"):
        result = Stage().process(ctx)
    assert caplog.text.count("reserved") == 3
    assert result.content == str(datetime.now(tz=UTC).date().year)
