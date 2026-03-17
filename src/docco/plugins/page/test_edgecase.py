# Edge-case tests only. The happy path is covered by test_regression.py.
# Directive argument validation is tested in tests/test_pipeline.py.

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.page import Stage


def test_pagedjs_screen_css_disabled(tmp_path):
    ctx = make_ctx(
        tmp_path,
        "<html><head></head><body><p>Hi</p></body></html>",
        config={"page": {"add_pagedjs_screen_css": False}},
        content_type=ContentType.HTML,
    )
    result = Stage().process(ctx)
    assert "pagedjs_page" not in result.str_content
