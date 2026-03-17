# Edge-case tests only. The happy path is covered by tests/test_regression.py.
from unittest.mock import patch

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.diffpdf import Stage


def test_disabled_by_default(tmp_path):
    result = Stage().process(
        make_ctx(tmp_path, b"%PDF-new", content_type=ContentType.PDF)
    )
    assert "skipped" not in result.artifacts


def test_no_existing_file(tmp_path):
    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf") as mock_diff:
        result = Stage().process(
            make_ctx(
                tmp_path, b"%PDF-new", {"diffpdf": {"enable": True}}, ContentType.PDF
            )
        )
        mock_diff.assert_not_called()
    assert "skipped" not in result.artifacts


def test_differs_keeps_new(tmp_path):
    ctx = make_ctx(
        tmp_path, b"%PDF-new", {"diffpdf": {"enable": True}}, ContentType.PDF
    )
    ctx.output_dir.mkdir(parents=True, exist_ok=True)
    (ctx.output_dir / "test.pdf").write_bytes(b"%PDF-old")
    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf", return_value=False):
        result = Stage().process(ctx)
    assert "skipped" not in result.artifacts
    assert result.content == b"%PDF-new"
