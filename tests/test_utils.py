from docco.utils import tmp_file


def test_tmp_file_no_content():
    with tmp_file(".txt") as path:
        assert path.exists()
        assert path.suffix == ".txt"
        assert path.read_bytes() == b""
    assert not path.exists()


def test_tmp_file_bytes_content():
    with tmp_file(".bin", b"hello") as path:
        assert path.read_bytes() == b"hello"
    assert not path.exists()


def test_tmp_file_str_content():
    with tmp_file(".html", "<h1>hi</h1>") as path:
        assert path.read_text(encoding="utf-8") == "<h1>hi</h1>"
    assert not path.exists()
