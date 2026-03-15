from docco.context import ContentType, Context
from docco.plugins.page_bg import Stage


def make_ctx(tmp_path, content):
    md = tmp_path / "test.md"
    md.write_text("# placeholder", encoding="utf-8")
    config = {}
    ctx = Context.from_file(md, tmp_path / "out", config)
    ctx.content = content
    ctx.content_type = ContentType.HTML
    return ctx


def test_basic_replacement(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- page-bg image="bg.jpg" -->')
    result = Stage().process(ctx)
    assert "<style>" in result.str_content
    assert 'class="page_bg_0"' in result.str_content
    assert 'url("bg.jpg")' in result.str_content


def test_unique_class_per_directive(tmp_path):
    ctx = make_ctx(
        tmp_path, '<!-- page-bg image="a.jpg" --> <!-- page-bg image="b.jpg" -->'
    )
    result = Stage().process(ctx)
    assert 'class="page_bg_0"' in result.str_content
    assert 'class="page_bg_1"' in result.str_content


def test_default_attributes(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- page-bg image="bg.jpg" -->')
    result = Stage().process(ctx)
    assert "background-position: 50% 0;" in result.str_content
    assert "background-size: contain;" in result.str_content


def test_all_attributes(tmp_path):
    ctx = make_ctx(
        tmp_path, '<!-- page-bg image="bg.jpg" x="10%" y="20%" size="cover" -->'
    )
    result = Stage().process(ctx)
    assert "background-position: 10% 20%;" in result.str_content
    assert "background-size: cover;" in result.str_content


def test_no_directives(tmp_path):
    html = "<p>No directives here</p>"
    ctx = make_ctx(tmp_path, html)
    result = Stage().process(ctx)
    assert result.content == html


def test_css_selector_correct(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- page-bg image="bg.jpg" -->')
    result = Stage().process(ctx)
    assert "div.pagedjs_page_content:has(.page_bg_0)" in result.str_content


def test_unknown_arg_raises(tmp_path):
    import pytest

    ctx = make_ctx(tmp_path, '<!-- page-bg image="bg.jpg" badattr="x" -->')
    with pytest.raises(ValueError, match="Unknown arg"):
        Stage().process(ctx)


def test_missing_image_raises(tmp_path):
    import pytest

    ctx = make_ctx(tmp_path, '<!-- page-bg x="10%" -->')
    with pytest.raises(ValueError, match="Missing 'image'"):
        Stage().process(ctx)
