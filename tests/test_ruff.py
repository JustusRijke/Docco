import subprocess
import pytest


def test_ruff():
    result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        pytest.fail("Ruff lint errors found")
