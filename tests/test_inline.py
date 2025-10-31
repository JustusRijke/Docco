"""Tests for inline file processing."""

import os
import pytest
from docco.inline import process_inlines


@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


def test_simple_inline(fixture_dir):
    """Test simple inline without arguments."""
    content = """# Document

Start

<!-- inline:"tests/fixtures/inline_target.md" -->

End"""
    result = process_inlines(content, ".")
    assert "# Inlined Content" in result
    assert "This file is meant to be inlined" in result


def test_inline_with_one_arg(fixture_dir):
    """Test inline with single argument substitution."""
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" name="TestName" -->"""
    result = process_inlines(content, ".")
    assert "TestName" in result
    assert "{{name}}" not in result


def test_inline_with_multiple_args(fixture_dir):
    """Test inline with multiple argument substitutions."""
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" name="TestName" value="TestValue" -->"""
    result = process_inlines(content, ".")
    assert "TestName" in result
    assert "TestValue" in result
    assert "{{name}}" not in result
    assert "{{value}}" not in result


def test_nested_inline_two_levels(fixture_dir):
    """Test that inline processor does one pass (nesting handled by parser iteration)."""
    content = """# Document

<!-- inline:"tests/fixtures/nested_inline_1.md" -->"""
    result = process_inlines(content, ".")
    # Should contain first level of inlining
    assert "# Document" in result
    assert "# Document with Nested Inline" in result
    # Second level directive is still present (needs another iteration)
    assert '<!-- inline:"tests/fixtures/nested_inline_2.md" -->' in result
    # Full nested content requires iterative processing in parser.py


def test_recursion_limit_exceeded(fixture_dir):
    """Test that inline processor does one pass (iteration handled by parser)."""
    # Recursion is now handled by iterative loop in parser.py
    # The inline processor just does one pass
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" -->"""
    # Should NOT raise - just does one pass
    result = process_inlines(content, ".")
    assert "# Inlined Content" in result


def test_missing_inline_file(fixture_dir):
    """Test that missing inline file raises error."""
    content = """# Document

<!-- inline:"tests/fixtures/nonexistent.md" -->"""
    with pytest.raises(FileNotFoundError):
        process_inlines(content, ".")


def test_inline_path_resolution(fixture_dir):
    """Test that inline paths are resolved relative to project root."""
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" -->"""
    result = process_inlines(content, ".")
    # Should find and inline the file
    assert "# Inlined Content" in result


def test_inline_preserves_non_inline_content(fixture_dir):
    """Test that non-inline content is preserved."""
    content = """# Document

Before inline

<!-- inline:"tests/fixtures/inline_target.md" -->

After inline"""
    result = process_inlines(content, ".")
    assert "Before inline" in result
    assert "After inline" in result


def test_multiple_inlines_in_content(fixture_dir):
    """Test multiple inline directives in same content."""
    content = """# Document

First:
<!-- inline:"tests/fixtures/inline_target.md" name="First" -->

Second:
<!-- inline:"tests/fixtures/inline_target.md" name="Second" -->"""
    result = process_inlines(content, ".")
    assert result.count("# Inlined Content") == 2
    assert "First" in result
    assert "Second" in result


def test_inline_not_processed_mid_line(fixture_dir):
    """Test that inline directives can now appear anywhere (unless in code blocks)."""
    content = """# Document

Some text <!-- inline:"tests/fixtures/inline_target.md" --> more text"""
    result = process_inlines(content, ".")
    # NEW BEHAVIOR: Mid-line directives ARE now processed
    assert '<!-- inline:"tests/fixtures/inline_target.md" -->' not in result
    assert "# Inlined Content" in result


def test_inline_processed_with_leading_spaces(fixture_dir):
    """Test that inline directives with leading whitespace are processed."""
    content = """# Document

    <!-- inline:"tests/fixtures/inline_target.md" -->"""
    result = process_inlines(content, ".")
    assert "# Inlined Content" in result


def test_inline_with_spaces_around_keyword(fixture_dir):
    """Test that inline directive accepts spaces around 'inline' and colon."""
    content = """# Document

<!--   inline   :   "tests/fixtures/inline_target.md"   -->"""
    result = process_inlines(content, ".")
    assert "# Inlined Content" in result


def test_python_directive_not_allowed_by_default(fixture_dir):
    """Test that python directives raise error if not explicitly allowed."""
    content = """# Document

<!-- python -->
for i in range(3):
    print(i)
<!-- /python -->"""
    with pytest.raises(ValueError, match="Python code execution not allowed"):
        process_inlines(content, ".", allow_python=False)


def test_python_directive_simple_loop(fixture_dir):
    """Test python directive with simple loop."""
    content = """# Document

<!-- python -->
for i in range(10):
    print(i, end='')
<!-- /python -->"""
    result = process_inlines(content, ".", allow_python=True)
    assert "0123456789" in result
    assert "<!-- python -->" not in result
    assert "<!-- /python -->" not in result


def test_python_directive_with_output(fixture_dir):
    """Test python directive captures output."""
    content = """# Document

Before

<!-- python -->
print("Hello from Python")
<!-- /python -->

After"""
    result = process_inlines(content, ".", allow_python=True)
    assert "Hello from Python" in result
    assert "Before" in result
    assert "After" in result


def test_python_directive_execution_error(fixture_dir):
    """Test that python execution errors raise ValueError."""
    content = """# Document

<!-- python -->
undefined_variable
<!-- /python -->"""
    with pytest.raises(ValueError, match="Python execution error"):
        process_inlines(content, ".", allow_python=True)


def test_python_directive_with_multiple_statements(fixture_dir):
    """Test python directive with multiple statements."""
    content = """# Document

<!-- python -->
x = 5
y = 10
print(x + y)
<!-- /python -->"""
    result = process_inlines(content, ".", allow_python=True)
    assert "15" in result


def test_python_and_inline_directives_together(fixture_dir):
    """Test that python directives work with inline directives."""
    content = """# Document

<!-- python -->
for i in range(3):
    print(i, end='')
<!-- /python -->

<!-- inline:"tests/fixtures/inline_target.md" -->"""
    result = process_inlines(content, ".", allow_python=True)
    assert "012" in result
    assert "# Inlined Content" in result
