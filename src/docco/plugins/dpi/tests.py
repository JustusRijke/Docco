import logging
from unittest.mock import MagicMock, patch

from docco.context import ContentType, Context
from docco.plugins.dpi import Stage, _downscale_pdf_images


def make_ctx(tmp_path, dpi=None):
    md = tmp_path / "test.md"
    md.write_text("# test", encoding="utf-8")
    config = {"dpi": {"max": dpi}} if dpi else {}
    ctx = Context.from_file(md, tmp_path / "out", config)
    ctx.content = b"%PDF"
    ctx.content_type = ContentType.PDF
    return ctx


def _make_page(images):
    page = MagicMock()
    page.get_image_info.return_value = images
    return page


def _mock_doc(images):
    doc = MagicMock()
    doc.__len__ = lambda _: 1
    doc.__getitem__ = lambda _, i: _make_page(images)
    return doc


def test_no_images(tmp_path):
    ctx = make_ctx(tmp_path)
    with (
        patch("docco.plugins.dpi._downscale_pdf_images"),
        patch("docco.plugins.dpi.fitz.open", return_value=_mock_doc([])),
    ):
        result = Stage().process(ctx)
    assert result.content_type == ContentType.PDF


def test_high_dpi_no_warning(tmp_path, caplog):
    ctx = make_ctx(tmp_path, dpi=300)
    img = {"width": 300, "height": 300, "bbox": (0, 0, 72, 72)}
    with (
        patch("docco.plugins.dpi._downscale_pdf_images"),
        patch("docco.plugins.dpi.fitz.open", return_value=_mock_doc([img])),
        caplog.at_level(logging.WARNING, logger="docco.plugins.dpi"),
    ):
        Stage().process(ctx)
    assert "DPI" not in caplog.text


def test_low_dpi_warning(tmp_path, caplog):
    ctx = make_ctx(tmp_path, dpi=300)
    img = {"width": 72, "height": 72, "bbox": (0, 0, 72, 72)}
    with (
        patch("docco.plugins.dpi._downscale_pdf_images"),
        patch("docco.plugins.dpi.fitz.open", return_value=_mock_doc([img])),
        caplog.at_level(logging.WARNING, logger="docco.plugins.dpi"),
    ):
        Stage().process(ctx)
    assert "DPI" in caplog.text


def test_default_dpi(tmp_path):
    ctx = make_ctx(tmp_path)
    doc = MagicMock()
    doc.__len__ = lambda _: 0
    with (
        patch("docco.plugins.dpi._downscale_pdf_images"),
        patch("docco.plugins.dpi.fitz.open", return_value=doc),
    ):
        result = Stage().process(ctx)
    assert result is ctx


def test_downscale_called_with_dpi(tmp_path):
    ctx = make_ctx(tmp_path, dpi=150)
    with (
        patch("docco.plugins.dpi._downscale_pdf_images") as mock_ds,
        patch("docco.plugins.dpi.fitz.open", return_value=_mock_doc([])),
    ):
        Stage().process(ctx)
    assert mock_ds.call_args[0][1] == 150


def test_downscale_function(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF")
    with (
        patch("docco.plugins.dpi.shutil.which", return_value="/usr/bin/gs"),
        patch("docco.plugins.dpi.subprocess.run"),
        patch("docco.plugins.dpi.shutil.move"),
    ):
        _downscale_pdf_images(pdf_path, 150)
