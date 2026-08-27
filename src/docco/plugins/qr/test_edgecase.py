# Edge-case tests only. The happy path is covered by tests/test_regression.py.

import pytest

from conftest import make_ctx
from docco.plugins.qr import Stage


def test_skip_if_exists(tmp_path):
    svg = tmp_path / "assets" / "qr.svg"
    svg.parent.mkdir()
    svg.write_text("<svg>old</svg>", encoding="utf-8")
    ctx = make_ctx(tmp_path, '<!-- qr url="https://example.com" out="qr.svg" -->')
    Stage().process(ctx)
    assert svg.read_text(encoding="utf-8") == "<svg>old</svg>"


def test_missing_url_raises(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- qr out="qr.svg" -->')
    with pytest.raises(ValueError, match="Missing 'url'"):
        Stage().process(ctx)


def test_missing_out_raises(tmp_path):
    ctx = make_ctx(tmp_path, '<!-- qr url="https://example.com" -->')
    with pytest.raises(ValueError, match="Missing 'out'"):
        Stage().process(ctx)
