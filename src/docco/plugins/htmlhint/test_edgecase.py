# Edge-case tests only. The happy path is covered by tests/test_regression.py.
import logging
from unittest.mock import patch

import pytest

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.htmlhint import Stage

HTML = "<html></html>"
CFG_ENABLED = {"htmlhint": {"enable": True}}


def test_disabled_by_default(tmp_path):
    result = Stage().process(make_ctx(tmp_path, HTML, content_type=ContentType.HTML))
    assert "htmlhint" not in result.artifacts


def test_not_found_raises(tmp_path):
    with (
        patch("docco.plugins.htmlhint.shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="htmlhint not found"),
    ):
        Stage().process(make_ctx(tmp_path, HTML, CFG_ENABLED, ContentType.HTML))


def test_invalid_level_raises(tmp_path):
    cfg = {"htmlhint": {"enable": True, "level": "critical"}}
    with pytest.raises(ValueError, match="invalid level"):
        Stage().process(make_ctx(tmp_path, HTML, cfg, ContentType.HTML))


def test_issues_found_logs_at_level(tmp_path, caplog):
    cfg = {"htmlhint": {"enable": True, "level": "warning"}}
    bad_html = "<p><b>unclosed"
    with caplog.at_level(logging.WARNING, logger="docco.plugins.htmlhint"):
        result = Stage().process(make_ctx(tmp_path, bad_html, cfg, ContentType.HTML))
    assert result.artifacts["htmlhint"]["returncode"] != 0
    assert "htmlhint" in caplog.text.lower()
