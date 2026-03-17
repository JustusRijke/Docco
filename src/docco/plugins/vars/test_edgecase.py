# Edge-case tests only. The happy path is covered by test_regression.py.

import pytest

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.vars import Stage


def test_reserved_var_raises(tmp_path):
    ctx = make_ctx(
        tmp_path,
        "<p>$$PATH$$</p>",
        config={"vars": {"PATH": "override"}},
        content_type=ContentType.HTML,
    )
    with pytest.raises(ValueError, match="reserved"):
        Stage().process(ctx)


def test_undefined_var_raises(tmp_path):
    ctx = make_ctx(tmp_path, "<p>$$undefined$$</p>", content_type=ContentType.HTML)
    with pytest.raises(ValueError, match="undefined"):
        Stage().process(ctx)


def test_unused_var_warning(tmp_path, caplog):
    ctx = make_ctx(
        tmp_path,
        "<p>$$name$$</p>",
        config={"vars": {"name": "World", "unused": "x"}},
        content_type=ContentType.HTML,
    )
    Stage().process(ctx)
    assert "unused" in caplog.text.lower()
