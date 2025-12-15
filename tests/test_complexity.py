"""Tests for code complexity using Radon."""

from pathlib import Path
from radon.complexity import cc_visit


MAX_COMPLEXITY = 15  # Maximum allowed cyclomatic complexity


def test_cyclomatic_complexity():
    """Ensure all functions have acceptable cyclomatic complexity."""
    src_dir = Path(__file__).parent.parent / "src" / "docco"
    violations = []

    for py_file in src_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r") as f:
            code = f.read()

        results = cc_visit(code)
        for result in results:
            if result.complexity > MAX_COMPLEXITY:
                violations.append(
                    f"{py_file.name}:{result.lineno} - "
                    f"{result.name} (complexity: {result.complexity})"
                )

    assert not violations, (
        f"Found {len(violations)} function(s) exceeding "
        f"complexity threshold of {MAX_COMPLEXITY}:\n" + "\n".join(violations)
    )
