from unittest.mock import patch

from docco.context import ContentType, Context
from docco.plugins.diffpdf import Stage


def test_diffpdf_identical_sets_skipped(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "test.pdf"
    existing.write_bytes(b"%PDF-existing")

    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out_dir,
        config={"diffpdf": {"enable": True, "threshold": 0.1, "dpi": 96}},
        content=b"%PDF-new",
        content_type=ContentType.PDF,
    )

    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf", return_value=True):
        result = Stage().process(ctx)

    assert result.artifacts.get("skipped") is True
    assert result.content == b"%PDF-existing"


def test_diffpdf_different_keeps_new(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "test.pdf"
    existing.write_bytes(b"%PDF-old")

    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out_dir,
        config={"diffpdf": {"enable": True, "threshold": 0.1}},
        content=b"%PDF-new",
        content_type=ContentType.PDF,
    )

    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf", return_value=False):
        result = Stage().process(ctx)

    assert "skipped" not in result.artifacts
    assert result.content == b"%PDF-new"


def test_diffpdf_no_existing_file(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out_dir,
        config={"diffpdf": {"enable": True}},
        content=b"%PDF-new",
        content_type=ContentType.PDF,
    )

    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf") as mock_diff:
        result = Stage().process(ctx)
        mock_diff.assert_not_called()

    assert "skipped" not in result.artifacts


def test_diffpdf_store_passes_output_dir(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "test.pdf"
    existing.write_bytes(b"%PDF-existing")

    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out_dir,
        config={"diffpdf": {"enable": True, "store": True}},
        content=b"%PDF-new",
        content_type=ContentType.PDF,
    )

    with patch(
        "docco.plugins.diffpdf.diffpdf_lib.diffpdf", return_value=False
    ) as mock_diff:
        Stage().process(ctx)

    _, kwargs = mock_diff.call_args
    assert kwargs["output_dir"] == out_dir / "diffpdf"


def test_diffpdf_store_false_passes_no_output_dir(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "test.pdf"
    existing.write_bytes(b"%PDF-existing")

    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out_dir,
        config={"diffpdf": {"enable": True, "store": False}},
        content=b"%PDF-new",
        content_type=ContentType.PDF,
    )

    with patch(
        "docco.plugins.diffpdf.diffpdf_lib.diffpdf", return_value=False
    ) as mock_diff:
        Stage().process(ctx)

    _, kwargs = mock_diff.call_args
    assert kwargs["output_dir"] is None


def test_diffpdf_disabled_by_default(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "test.pdf").write_bytes(b"%PDF-existing")

    ctx = Context(
        source_path=tmp_path / "test.md",
        output_dir=out_dir,
        config={},
        content=b"%PDF-new",
        content_type=ContentType.PDF,
    )

    with patch("docco.plugins.diffpdf.diffpdf_lib.diffpdf") as mock_diff:
        result = Stage().process(ctx)
        mock_diff.assert_not_called()

    assert "skipped" not in result.artifacts
    assert result.content == b"%PDF-new"
