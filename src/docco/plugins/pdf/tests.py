import pytest

from docco.context import ContentType, Context
from docco.plugins.pdf import _RENDERING_COMPLETE_JS, Stage


@pytest.fixture
def html_context(tmp_path):
    md = tmp_path / "test.md"
    md.write_text("", encoding="utf-8")
    return Context(
        source_path=md,
        output_dir=tmp_path / "out",
        config={},
        content="<html><head></head><body><h1>Hello</h1></body></html>",
        content_type=ContentType.HTML,
    )


def test_rendering_complete_script_content():
    assert "pagedJsRenderingComplete" in _RENDERING_COMPLETE_JS
    assert "Paged.registerHandlers" in _RENDERING_COMPLETE_JS


def test_pdf_stage(html_context):
    result = Stage().process(html_context)

    assert result.content_type == ContentType.PDF
    assert isinstance(result.content, bytes)
    assert result.content[:5] == b"%PDF-"


def test_pdf_stage_no_head(tmp_path):
    """HTML without <head> falls back to injecting before </body>."""
    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=tmp_path / "out",
        config={},
        content="<html><body><p>No head</p></body></html>",
        content_type=ContentType.HTML,
    )
    result = Stage().process(ctx)
    assert result.content[:5] == b"%PDF-"


def test_pdf_stage_bare_html(tmp_path):
    """HTML without any closing tags appends the script at the end."""
    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=tmp_path / "out",
        config={},
        content="<p>Bare</p>",
        content_type=ContentType.HTML,
    )
    result = Stage().process(ctx)
    assert result.content[:5] == b"%PDF-"


def test_keep_html(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out,
        config={"pdf": {"keep_html": True}},
        content="<html><head></head><body><p>Hi</p></body></html>",
        content_type=ContentType.HTML,
    )
    Stage().process(ctx)
    assert (out / "test.html").exists()
