# Edge-case tests only. The happy path is covered by test_regression.py. Only keep tests for code paths not exercised there.

from unittest.mock import patch

import fitz
import pytest

from docco.context import ContentType, Context
from docco.plugins.pdf2svg import Stage, _extract_svg


def _make_pdf(tmp_path, with_text=True):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    if with_text:
        page.insert_text((72, 72), "Hello PDF")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def _make_context(tmp_path, content, config=None):
    md_path = tmp_path / "doc.md"
    md_path.write_text(content, encoding="utf-8")
    return Context(
        source_path=md_path,
        output_dir=tmp_path / "out",
        content=content,
        content_type=ContentType.MARKDOWN,
        config=config or {},
    )


def test_empty_page(tmp_path):
    pdf = _make_pdf(tmp_path, with_text=False)
    assert "<svg" in _extract_svg(pdf, 1)


def test_skip_if_exists(tmp_path):
    pdf = _make_pdf(tmp_path)
    svg = tmp_path / "assets" / "fig.svg"
    svg.parent.mkdir()
    svg.write_text("<svg>old</svg>", encoding="utf-8")
    ctx = _make_context(
        tmp_path, f'<!-- pdf2svg src="{pdf.name}" page="1" out="fig.svg" -->'
    )
    Stage().process(ctx)
    assert svg.read_text(encoding="utf-8") == "<svg>old</svg>"


def test_invalid_page(tmp_path):
    pdf = _make_pdf(tmp_path)
    with pytest.raises(ValueError, match="out of range"):
        _extract_svg(pdf, 99)


def test_crop_fallback(tmp_path):
    pdf = _make_pdf(tmp_path)
    with patch("fitz.open") as mock_open:
        mock_doc = mock_open.return_value
        mock_page = fitz.open(pdf).load_page(0)
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, i: mock_page
        mock_doc.close = lambda: None

        def raising_get_text(*a, **kw):
            raise RuntimeError("crop error")

        mock_page.get_text = raising_get_text
        mock_open.return_value = mock_doc
        _extract_svg(pdf, 1)


def test_missing_src_raises(tmp_path):
    ctx = _make_context(tmp_path, '<!-- pdf2svg page="1" -->')
    with pytest.raises(ValueError, match="Missing 'src'"):
        Stage().process(ctx)


def test_missing_page_raises(tmp_path):
    ctx = _make_context(tmp_path, '<!-- pdf2svg src="f.pdf" -->')
    with pytest.raises(ValueError, match="Missing 'page'"):
        Stage().process(ctx)


def test_non_numeric_page_raises(tmp_path):
    ctx = _make_context(tmp_path, '<!-- pdf2svg src="f.pdf" page="abc" -->')
    with pytest.raises(ValueError, match="Non-numeric 'page'"):
        Stage().process(ctx)


def test_missing_pdf(tmp_path):
    ctx = _make_context(tmp_path, '<!-- pdf2svg src="missing.pdf" page="1" -->')
    with pytest.raises(FileNotFoundError):
        Stage().process(ctx)


def test_non_pdf_source(tmp_path):
    txt_file = tmp_path / "doc.txt"
    txt_file.write_text("hello", encoding="utf-8")
    ctx = _make_context(tmp_path, '<!-- pdf2svg src="doc.txt" page="1" -->')
    with pytest.raises(ValueError, match="not a PDF"):
        Stage().process(ctx)
