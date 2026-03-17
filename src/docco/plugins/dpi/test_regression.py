"""Regression test: dpi example produces identical PDFs (diffpdf skips)."""

import subprocess
from pathlib import Path

from docco.cli import main

EXAMPLE_DIR = Path(__file__).parent / "example"


def test_dpi_example_no_diff(monkeypatch):
    monkeypatch.chdir(EXAMPLE_DIR)
    main(["-o", str(EXAMPLE_DIR)])
    result = subprocess.run(
        ["git", "diff", "--name-only", str(EXAMPLE_DIR)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", f"Files changed:\n{result.stdout}"
