# Edge-case tests only. The happy path is covered by test_regression.py.

import pytest

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.page_bg import Stage


def test_missing_image_raises(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- page-bg x="10%" -->', content_type=ContentType.HTML)
    with pytest.raises(ValueError, match="Missing 'image'"):
        Stage().process(ctx)
