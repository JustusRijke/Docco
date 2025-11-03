"""Tests for header and footer processing."""

import os
import pytest
from docco.header_footer import process_header_footer


@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


def test_basic_header_with_placeholders(fixture_dir):
    """Test basic header processing with placeholder substitution."""
    config = {
        'file': 'tests/fixtures/header_simple.html',
        'title': 'Test Document',
        'author': 'Test Author'
    }
    result = process_header_footer(config, ".")
    assert 'Test Document' in result
    assert 'Test Author' in result
    assert '{{title}}' not in result
    assert '{{author}}' not in result


def test_basic_footer_with_placeholders(fixture_dir):
    """Test basic footer processing with placeholder substitution."""
    config = {
        'file': 'tests/fixtures/footer_simple.html',
        'title': 'Test Doc'
    }
    result = process_header_footer(config, ".")
    assert 'Test Doc' in result
    assert '{{title}}' not in result


def test_missing_file_key():
    """Test that missing 'file' key raises ValueError."""
    config = {'title': 'Test'}
    with pytest.raises(ValueError, match="must contain 'file' key"):
        process_header_footer(config, ".")


def test_invalid_config_none():
    """Test that None config raises ValueError."""
    with pytest.raises(ValueError, match="must be a dict"):
        process_header_footer(None, ".")


def test_invalid_config_not_dict():
    """Test that non-dict config raises ValueError."""
    with pytest.raises(ValueError, match="must be a dict"):
        process_header_footer("not a dict", ".")


def test_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    config = {'file': 'nonexistent.html'}
    with pytest.raises(FileNotFoundError, match="Header/footer file not found"):
        process_header_footer(config, ".")


def test_with_directive_processor(fixture_dir):
    """Test header/footer with directive processor."""
    config = {
        'file': 'tests/fixtures/header_simple.html',
        'title': 'Test'
    }

    # Mock directive processor that adds suffix
    def mock_processor(content, base_dir, allow_python):
        return content + " [processed]"

    result = process_header_footer(config, ".", directive_processor=mock_processor)
    assert '[processed]' in result


def test_placeholder_replacement_with_numbers(fixture_dir):
    """Test that numeric values are converted to strings."""
    config = {
        'file': 'tests/fixtures/header_simple.html',
        'title': 123,
        'author': 'Test'
    }
    result = process_header_footer(config, ".")
    assert '123' in result


def test_file_key_not_used_as_placeholder(fixture_dir):
    """Test that 'file' key is not used for placeholder substitution."""
    config = {
        'file': 'tests/fixtures/header_with_file_placeholder.html',
        'title': 'Test'
    }
    result = process_header_footer(config, ".")
    # {{file}} should remain unreplaced
    assert '{{file}}' in result


def test_path_resolution(fixture_dir):
    """Test that file paths are resolved relative to base_dir."""
    config = {
        'file': 'fixtures/header_simple.html',
        'title': 'Test',
        'author': 'Test'
    }
    result = process_header_footer(config, "tests")
    assert 'Test' in result


def test_multiple_placeholder_instances(fixture_dir):
    """Test that all instances of a placeholder are replaced."""
    config = {
        'file': 'tests/fixtures/header_multi_placeholder.html',
        'title': 'MyTitle'
    }
    result = process_header_footer(config, ".")
    # All {{title}} occurrences should be replaced
    assert result.count('MyTitle') == result.count('MyTitle')
    assert '{{title}}' not in result
