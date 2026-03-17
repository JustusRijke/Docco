# Edge-case tests only. The happy path is covered by test_regression.py.

import pytest

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.dpi import Stage


def test_invalid_level_raises(tmp_path):
    ctx = make_ctx(
        tmp_path,
        content=b"%PDF-1.4",
        config={"dpi": {"level": "critical"}},
        content_type=ContentType.PDF,
    )
    with pytest.raises(ValueError, match="invalid level"):
        Stage().process(ctx)
