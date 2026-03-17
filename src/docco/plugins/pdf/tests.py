from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.pdf import _RENDERING_COMPLETE_JS, Stage


def test_rendering_complete_script_content():
    assert "pagedJsRenderingComplete" in _RENDERING_COMPLETE_JS
    assert "Paged.registerHandlers" in _RENDERING_COMPLETE_JS


def test_pdf_stage(tmp_path):
    result = Stage().process(
        make_ctx(
            tmp_path,
            "<html><head></head><body><h1>Hello</h1></body></html>",
            content_type=ContentType.HTML,
        )
    )
    assert result.content_type == ContentType.PDF
    assert result.content[:5] == b"%PDF-"


def test_pdf_stage_no_head(tmp_path):
    result = Stage().process(
        make_ctx(
            tmp_path,
            "<html><body><p>No head</p></body></html>",
            content_type=ContentType.HTML,
        )
    )
    assert result.content[:5] == b"%PDF-"


def test_pdf_stage_bare_html(tmp_path):
    result = Stage().process(
        make_ctx(tmp_path, "<p>Bare</p>", content_type=ContentType.HTML)
    )
    assert result.content[:5] == b"%PDF-"


def test_keep_html(tmp_path):
    ctx = make_ctx(
        tmp_path,
        "<html><head></head><body><p>Hi</p></body></html>",
        {"pdf": {"keep_html": True}},
        ContentType.HTML,
    )
    ctx.output_dir.mkdir(parents=True, exist_ok=True)
    Stage().process(ctx)
    assert (ctx.output_dir / "test.html").exists()
