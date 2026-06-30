import fitz

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.pdf import Stage


def _make_pdf_ctx(tmp_path, config=None):
    ctx = make_ctx(
        tmp_path,
        "<html><head></head><body><p>Hi</p></body></html>",
        config or {},
        ContentType.HTML,
    )
    ctx.output_dir.mkdir(parents=True, exist_ok=True)
    return ctx


def _metadata(pdf_bytes: bytes) -> dict[str, str]:
    doc = fitz.open("pdf", pdf_bytes)
    assert doc is not None
    meta = doc.metadata
    doc.close()
    assert meta is not None
    return meta


def test_title_defaults_to_stem(tmp_path):
    result = Stage().process(_make_pdf_ctx(tmp_path))
    assert isinstance(result.content, bytes)
    assert _metadata(result.content)["title"] == "test"


def test_empty_title_clears_chromium_default(tmp_path):
    result = Stage().process(
        _make_pdf_ctx(tmp_path, {"pdf": {"title": "", "author": ""}})
    )
    assert isinstance(result.content, bytes)
    assert _metadata(result.content)["title"] == ""


def test_explicit_title_and_author(tmp_path):
    result = Stage().process(
        _make_pdf_ctx(tmp_path, {"pdf": {"title": "My Doc", "author": "Alice"}})
    )
    assert isinstance(result.content, bytes)
    meta = _metadata(result.content)
    assert meta["title"] == "My Doc"
    assert meta["author"] == "Alice"
