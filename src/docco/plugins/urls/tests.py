import http.client
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from docco.context import Context
from docco.plugins.urls import Stage


def _make_ctx(tmp_path, content, config=None):
    md = tmp_path / "test.md"
    md.write_text("", encoding="utf-8")
    ctx = Context.from_file(md, tmp_path / "out", config or {})
    ctx.content = content
    return ctx


def test_urls_absolutizes_img_src(tmp_path):
    (tmp_path / "image.png").write_bytes(b"PNG")
    ctx = _make_ctx(tmp_path, '<img src="image.png">')
    result = Stage().process(ctx)
    assert "file://" in result.str_content
    assert "image.png" in result.str_content


def test_urls_absolutizes_style_block(tmp_path):
    img = tmp_path / "bg.png"
    img.write_bytes(b"PNG")
    ctx = _make_ctx(tmp_path, "<style>body { background: url('bg.png'); }</style>")
    result = Stage().process(ctx)
    assert "file://" in result.str_content
    assert "bg.png" in result.str_content


def test_urls_style_block_missing_asset(tmp_path):
    ctx = _make_ctx(tmp_path, "<style>body { background: url('missing.png'); }</style>")
    with pytest.raises(FileNotFoundError, match="Asset not found"):
        Stage().process(ctx)


def test_urls_disabled(tmp_path):
    ctx = _make_ctx(tmp_path, '<img src="image.png">', {"urls": {"enable": False}})
    result = Stage().process(ctx)
    assert "file://" not in result.str_content


def test_urls_test_disabled(tmp_path):
    ctx = _make_ctx(
        tmp_path,
        '<img src="file:///nonexistent/image.png">',
        {"urls": {"test": False}},
    )
    # Should not raise even though the file doesn't exist
    result = Stage().process(ctx)
    assert "file://" in result.str_content


def test_urls_file_url_missing(tmp_path):
    ctx = _make_ctx(tmp_path, '<img src="missing.png">')
    with pytest.raises(FileNotFoundError, match="URL not found"):
        Stage().process(ctx)


def test_urls_local_only_skips_http(tmp_path):
    ctx = _make_ctx(tmp_path, '<img src="https://example.com/image.png">')
    # local_only=True (default) — no HTTP request made
    with patch("urllib.request.urlopen") as mock_open:
        Stage().process(ctx)
    mock_open.assert_not_called()


def test_urls_http_url_ok(tmp_path):
    ctx = _make_ctx(
        tmp_path,
        '<img src="https://example.com/image.png">',
        {"urls": {"local_only": False}},
    )
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = Stage().process(ctx)
    assert "https://example.com/image.png" in result.str_content


def test_urls_http_url_404(tmp_path):
    ctx = _make_ctx(
        tmp_path,
        '<img src="https://example.com/missing.png">',
        {"urls": {"local_only": False}},
    )
    err = urllib.error.HTTPError(
        "https://example.com/missing.png",
        404,
        "Not Found",
        http.client.HTTPMessage(),
        None,
    )
    with (
        patch("urllib.request.urlopen", side_effect=err),
        pytest.raises(ValueError, match="404"),
    ):
        Stage().process(ctx)
    err.close()


def test_urls_http_url_500(tmp_path):
    ctx = _make_ctx(
        tmp_path,
        '<img src="https://example.com/error.png">',
        {"urls": {"local_only": False}},
    )
    err = urllib.error.HTTPError(
        "https://example.com/error.png",
        500,
        "Server Error",
        http.client.HTTPMessage(),
        None,
    )
    with (
        patch("urllib.request.urlopen", side_effect=err),
        pytest.raises(ValueError, match="500"),
    ):
        Stage().process(ctx)
    err.close()


def test_urls_http_url_unreachable(tmp_path):
    ctx = _make_ctx(
        tmp_path,
        '<img src="https://unreachable.example/image.png">',
        {"urls": {"local_only": False}},
    )
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        # Unreachable host is a warning, not a hard failure
        result = Stage().process(ctx)
    assert "unreachable.example" in result.str_content


def test_urls_no_urls(tmp_path):
    ctx = _make_ctx(tmp_path, "<p>No URLs here.</p>")
    result = Stage().process(ctx)
    assert "<p>No URLs here.</p>" in result.str_content


def test_urls_already_absolute_passthrough(tmp_path):
    html = (
        '<img src="https://cdn.example.com/img.png">'
        '<a href="#anchor">link</a>'
        "<style>body { background: url('https://cdn.example.com/bg.png'); }</style>"
    )
    ctx = _make_ctx(tmp_path, html, {"urls": {"local_only": False}})
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = Stage().process(ctx)
    assert 'src="https://cdn.example.com/img.png"' in result.str_content
    assert 'href="#anchor"' in result.str_content
    assert "https://cdn.example.com/bg.png" in result.str_content
