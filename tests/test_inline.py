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


def test_inline_md_file_no_processing(fixture_dir):
    """Test .md files have no post-processing."""
    content = """# Document

<!-- inline:"tests/fixtures/simple.md" -->"""
    result = process_inlines(content, ".")
    # MD files should preserve exact content
    assert "This is a simple markdown document" in result


def test_inline_html_file_trimming(fixture_dir):
    """Test .html files have lines trimmed."""
    content = """# Document

<!-- inline:"tests/fixtures/simple.html" -->"""
    result = process_inlines(content, ".")
    # Lines should be trimmed (no leading spaces)
    assert "<div>" in result
    assert "<p>This is indented HTML</p>" in result
    assert "    <div>" not in result  # Original had leading spaces


def test_inline_html_empty_lines_preserved(fixture_dir):
    """Test .html trimming preserves empty lines."""
    content = """# Document

<!-- inline:"tests/fixtures/simple.html" -->"""
    result = process_inlines(content, ".")
    # Should contain trimmed content with preserved line structure
    lines = result.split('\n')
    assert any(line == '' for line in lines)  # Empty lines preserved


def test_inline_html_with_placeholders(fixture_dir):
    """Test placeholders work before trimming."""
    content = """# Document

<!-- inline:"tests/fixtures/placeholder.html" name="Alice" count="42" -->"""
    result = process_inlines(content, ".")
    # Placeholders should be replaced
    assert "Alice" in result
    assert "42" in result
    assert "{{name}}" not in result
    assert "{{count}}" not in result
    # And lines should be trimmed
    assert "<div>" in result
    assert "    <div>" not in result


def test_inline_py_file_execution(fixture_dir):
    """Test .py files are executed."""
    content = """# Document

<!-- inline:"tests/fixtures/simple.py" -->"""
    result = process_inlines(content, ".", allow_python=True)
    assert "Hello from Python!" in result
    assert "Line 2" in result


def test_inline_py_file_with_arguments(fixture_dir):
    """Test inline arguments passed via sys.argv."""
    content = """# Document

<!-- inline:"tests/fixtures/args.py" count="10" name="test" -->"""
    result = process_inlines(content, ".", allow_python=True)
    # Arguments should be in key=value format
    assert "count=10" in result
    assert "name=test" in result


def test_inline_py_file_requires_allow_python(fixture_dir):
    """Test .py files require --allow-python flag."""
    content = """# Document

<!-- inline:"tests/fixtures/simple.py" -->"""
    with pytest.raises(ValueError, match="Python file execution not allowed"):
        process_inlines(content, ".", allow_python=False)


def test_inline_py_file_execution_error(fixture_dir):
    """Test .py execution errors fail the build."""
    content = """# Document

<!-- inline:"tests/fixtures/error.py" -->"""
    with pytest.raises(ValueError, match="Python execution error"):
        process_inlines(content, ".", allow_python=True)


def test_inline_py_output_contains_directives(fixture_dir):
    """Test .py output can contain inline directives."""
    content = """# Document

<!-- inline:"tests/fixtures/nested.py" -->"""
    result = process_inlines(content, ".", allow_python=True)
    # Should output the directive (to be processed in next iteration)
    assert '<!-- inline:"simple.md" -->' in result


def test_inline_unknown_file_type_warning(fixture_dir, caplog):
    """Test unknown file types issue warning."""
    content = """# Document

<!-- inline:"tests/fixtures/unknown.txt" -->"""
    result = process_inlines(content, ".")
    # Content should be inserted as-is
    assert "This is a text file with unknown type." in result
    # Warning should be logged
    assert "Unknown file type" in caplog.text


def test_inline_unused_arguments_warning(fixture_dir, caplog):
    """Test warning for unused arguments in inline directive."""
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" name="TestName" unused="NotUsed" extra="AlsoNotUsed" -->"""
    result = process_inlines(content, ".")
    # Arguments should still be processed
    assert "TestName" in result
    # Warning should be logged for unused arguments
    assert "Unused arguments" in caplog.text
    assert "extra" in caplog.text
    assert "unused" in caplog.text


def test_inline_unfulfilled_placeholders_warning(fixture_dir, caplog):
    """Test warning for unfulfilled placeholders in inlined file."""
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" name="TestName" -->"""
    result = process_inlines(content, ".")
    # Name should be replaced
    assert "TestName" in result
    # Warning should be logged for unfulfilled placeholder
    assert "Unfulfilled placeholders" in caplog.text
    assert "value" in caplog.text


def test_inline_all_args_used_no_warning(fixture_dir, caplog):
    """Test no warnings when all arguments are used and all placeholders fulfilled."""
    content = """# Document

<!-- inline:"tests/fixtures/inline_target.md" name="TestName" value="TestValue" -->"""
    result = process_inlines(content, ".")
    # Both should be replaced
    assert "TestName" in result
    assert "TestValue" in result
    # No warnings should be logged
    assert "Unused arguments" not in caplog.text
    assert "Unfulfilled placeholders" not in caplog.text
