import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def tmp_file(suffix: str = "", content: str | bytes | None = None) -> Iterator[Path]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        path = Path(f.name)
        if isinstance(content, bytes):
            f.write(content)
        elif isinstance(content, str):
            f.write(content.encode("utf-8"))
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)
