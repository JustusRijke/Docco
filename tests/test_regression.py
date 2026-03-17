import subprocess
import sys
from pathlib import Path

import pytest

from docco.cli import main

PLUGINS_DIR = Path(__file__).parent.parent / "src" / "docco" / "plugins"
_examples = sorted(p.parent for p in PLUGINS_DIR.glob("*/example/example.md"))


@pytest.mark.skipif(
    sys.platform == "win32", reason="PDF rendering diffs too large for reliable testing"
)
@pytest.mark.parametrize(
    "example_dir", _examples, ids=[p.parent.name for p in _examples]
)
def test_plugin_example(monkeypatch, example_dir):
    monkeypatch.chdir(Path(__file__).parent)
    main([str(example_dir / "example.md"), "--config", "assets/docco.toml"])
    result = subprocess.run(
        ["git", "diff", "--name-only", str(example_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", f"Files changed:\n{result.stdout}"
