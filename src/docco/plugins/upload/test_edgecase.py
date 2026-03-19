# Edge-case tests only. The happy path is covered by test_regression.py.

from unittest.mock import MagicMock, patch

import pytest

from conftest import make_ctx
from docco.context import ContentType
from docco.plugins.upload import Stage


def test_no_config_is_noop(tmp_path):
    ctx = make_ctx(tmp_path, content=b"%PDF-1.4", content_type=ContentType.PDF)
    with patch("paramiko.SSHClient") as mock_ssh:
        result = Stage().process(ctx)
    assert result is ctx
    mock_ssh.assert_not_called()


def test_disabled_skips_upload(tmp_path):
    ctx = make_ctx(
        tmp_path,
        content=b"%PDF-1.4",
        config={
            "upload": {
                "enable": False,
                "host": "sftp.example.com",
                "user": "u",
                "password": "p",
                "path": "/out",
            }
        },
        content_type=ContentType.PDF,
    )
    with patch("paramiko.SSHClient") as mock_ssh:
        result = Stage().process(ctx)
    assert result is ctx
    mock_ssh.assert_not_called()


def test_missing_key_raises(tmp_path):
    ctx = make_ctx(
        tmp_path,
        content=b"%PDF-1.4",
        config={"upload": {"host": "sftp.example.com", "user": "u", "path": "/out"}},
        content_type=ContentType.PDF,
    )
    with pytest.raises(ValueError, match="missing required config key: password"):
        Stage().process(ctx)


def test_upload(tmp_path):
    ctx = make_ctx(
        tmp_path,
        content=b"%PDF-1.4",
        config={
            "upload": {
                "host": "sftp.example.com",
                "port": 2222,
                "user": "myuser",
                "password": "secret",
                "path": "/remote/uploads",
            }
        },
        content_type=ContentType.PDF,
    )
    mock_sftp = MagicMock()
    mock_ssh = MagicMock()
    mock_ssh.__enter__ = lambda s: s
    mock_ssh.__exit__ = MagicMock(return_value=False)
    mock_ssh.open_sftp.return_value.__enter__ = lambda s: mock_sftp
    mock_ssh.open_sftp.return_value.__exit__ = MagicMock(return_value=False)

    with patch("paramiko.SSHClient", return_value=mock_ssh):
        result = Stage().process(ctx)

    assert result is ctx
    mock_ssh.connect.assert_called_once_with(
        "sftp.example.com", port=2222, username="myuser", password="secret"
    )
    mock_sftp.putfo.assert_called_once()
    call_args = mock_sftp.putfo.call_args
    assert call_args[0][0].read() == b"%PDF-1.4"
    assert call_args[0][1] == "/remote/uploads/test.pdf"
