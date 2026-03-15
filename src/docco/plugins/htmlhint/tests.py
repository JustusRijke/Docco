from unittest.mock import patch

import pytest

from docco.context import ContentType, Context
from docco.plugins.htmlhint import Stage

BASE_HTML = "<!DOCTYPE html><html><head></head><body><h1>Test</h1></body></html>"


def make_ctx(tmp_path, html=BASE_HTML, config=None):
    md = tmp_path / "test.md"
    md.write_text("# placeholder", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", config or {})
    ctx.content = html
    ctx.content_type = ContentType.HTML
    return ctx


def test_disabled_by_default(tmp_path):
    ctx = make_ctx(tmp_path)
    with patch("docco.plugins.htmlhint.shutil.which") as mock_which:
        result = Stage().process(ctx)
        mock_which.assert_not_called()
    assert "htmlhint" not in result.artifacts


def test_htmlhint_not_found_raises(tmp_path):
    ctx = make_ctx(tmp_path, config={"htmlhint": {"enable": True}})
    with (
        patch("docco.plugins.htmlhint.shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="htmlhint not found"),
    ):
        Stage().process(ctx)


def test_no_issues(tmp_path):
    ctx = make_ctx(tmp_path, config={"htmlhint": {"enable": True}})
    mock_result = type(
        "R", (), {"returncode": 0, "stdout": "No errors", "stderr": ""}
    )()
    with (
        patch("docco.plugins.htmlhint.shutil.which", return_value="/usr/bin/htmlhint"),
        patch("docco.plugins.htmlhint.subprocess.run", return_value=mock_result),
    ):
        result = Stage().process(ctx)
    assert result.artifacts["htmlhint"]["returncode"] == 0
    assert result.artifacts["htmlhint"]["output"] == "No errors"
    assert result.content == BASE_HTML


def test_issues_found_logs_at_error_by_default(tmp_path):
    ctx = make_ctx(tmp_path, config={"htmlhint": {"enable": True}})
    mock_result = type(
        "R", (), {"returncode": 1, "stdout": "L1: error", "stderr": ""}
    )()
    with (
        patch("docco.plugins.htmlhint.shutil.which", return_value="/usr/bin/htmlhint"),
        patch("docco.plugins.htmlhint.subprocess.run", return_value=mock_result),
        patch.object(Stage, "log") as mock_log,
    ):
        result = Stage().process(ctx)
    assert result.artifacts["htmlhint"]["returncode"] == 1
    mock_log.error.assert_called_once()
    mock_log.warning.assert_not_called()
    mock_log.info.assert_not_called()


def test_issues_found_logs_at_configured_level(tmp_path):
    for level in ("info", "warning", "error"):
        ctx = make_ctx(tmp_path, config={"htmlhint": {"enable": True, "level": level}})
        mock_result = type(
            "R", (), {"returncode": 1, "stdout": "issue", "stderr": ""}
        )()
        with (
            patch(
                "docco.plugins.htmlhint.shutil.which", return_value="/usr/bin/htmlhint"
            ),
            patch("docco.plugins.htmlhint.subprocess.run", return_value=mock_result),
            patch.object(Stage, "log") as mock_log,
        ):
            Stage().process(ctx)
        getattr(mock_log, level).assert_called_once()


def test_invalid_level_raises(tmp_path):
    ctx = make_ctx(tmp_path, config={"htmlhint": {"enable": True, "level": "critical"}})
    with (
        patch("docco.plugins.htmlhint.shutil.which", return_value="/usr/bin/htmlhint"),
        pytest.raises(ValueError, match="invalid level"),
    ):
        Stage().process(ctx)
