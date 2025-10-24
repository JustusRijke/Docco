"""
Unit tests for custom command processing.
"""

import pytest
from pathlib import Path
from docco.content.commands import CommandProcessor


@pytest.fixture
def temp_commands_dir(tmp_path):
    """Create a temporary commands directory with sample templates."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    # Simple template
    (commands_dir / "callout.html").write_text(
        '<div class="callout"><img src="{{icon}}" />{{content}}</div>'
    )

    # Template with multiple variables
    (commands_dir / "alert.html").write_text(
        '<div class="alert alert-{{type}}">{{title}}: {{message}}</div>'
    )

    return tmp_path


class TestCommandProcessor:
    """Tests for CommandProcessor class."""

    def test_block_command_basic(self, temp_commands_dir):
        """Test basic block command expansion."""
        processor = CommandProcessor(temp_commands_dir)
        content = '<!-- cmd: callout icon="test.svg" -->Hello World<!-- /cmd -->'

        result = processor.process(content)

        assert '<div class="callout">' in result
        assert '<img src="test.svg" />' in result
        assert 'Hello World' in result
        assert '<!-- cmd:' not in result

    def test_self_closing_command(self, temp_commands_dir):
        """Test self-closing command syntax."""
        processor = CommandProcessor(temp_commands_dir)
        content = '<!-- cmd: alert type="warning" title="Note" message="Test" /-->'

        result = processor.process(content)

        assert '<div class="alert alert-warning">' in result
        assert 'Note: Test' in result
        assert '<!-- cmd:' not in result

    def test_multiple_arguments(self, temp_commands_dir):
        """Test command with multiple arguments."""
        processor = CommandProcessor(temp_commands_dir)
        content = '<!-- cmd: alert type="info" title="Info" message="Details here" /-->'

        result = processor.process(content)

        assert 'alert-info' in result
        assert 'Info: Details here' in result

    def test_missing_template(self, temp_commands_dir):
        """Test command with non-existent template leaves content unchanged."""
        processor = CommandProcessor(temp_commands_dir)
        original = '<!-- cmd: nonexistent arg="val" -->content<!-- /cmd -->'

        result = processor.process(original)

        assert result == original

    def test_missing_variable(self, temp_commands_dir):
        """Test that missing variables are replaced with empty strings."""
        processor = CommandProcessor(temp_commands_dir)
        content = '<!-- cmd: callout -->No icon specified<!-- /cmd -->'

        result = processor.process(content)

        assert '<div class="callout">' in result
        assert 'No icon specified' in result
        # Icon variable should be empty string
        assert '<img src="" />' in result

    def test_multiline_content(self, temp_commands_dir):
        """Test command with multiline content."""
        processor = CommandProcessor(temp_commands_dir)
        content = '''<!-- cmd: callout icon="test.svg" -->
Line 1
Line 2
Line 3
<!-- /cmd -->'''

        result = processor.process(content)

        assert 'Line 1' in result
        assert 'Line 2' in result
        assert 'Line 3' in result

    def test_multiple_commands(self, temp_commands_dir):
        """Test processing multiple commands in one document."""
        processor = CommandProcessor(temp_commands_dir)
        content = '''
Text before
<!-- cmd: callout icon="a.svg" -->First callout<!-- /cmd -->
Text between
<!-- cmd: callout icon="b.svg" -->Second callout<!-- /cmd -->
Text after
'''

        result = processor.process(content)

        assert result.count('<div class="callout">') == 2
        assert 'a.svg' in result
        assert 'b.svg' in result
        assert 'First callout' in result
        assert 'Second callout' in result

    def test_single_quotes_in_args(self, temp_commands_dir):
        """Test arguments with single quotes."""
        processor = CommandProcessor(temp_commands_dir)
        content = "<!-- cmd: callout icon='test.svg' -->Content<!-- /cmd -->"

        result = processor.process(content)

        assert 'test.svg' in result

    def test_template_caching(self, temp_commands_dir):
        """Test that templates are cached after first load."""
        processor = CommandProcessor(temp_commands_dir)

        # First call loads template
        processor.process('<!-- cmd: callout icon="a.svg" -->Test<!-- /cmd -->')

        # Check cache
        assert 'callout' in processor._template_cache

        # Second call should use cache
        result = processor.process('<!-- cmd: callout icon="b.svg" -->Test 2<!-- /cmd -->')
        assert 'b.svg' in result

    def test_no_commands_dir(self, tmp_path):
        """Test behavior when commands directory doesn't exist."""
        processor = CommandProcessor(tmp_path)
        original = '<!-- cmd: test arg="val" -->content<!-- /cmd -->'

        result = processor.process(original)

        # Should leave content unchanged
        assert result == original

    def test_whitespace_handling(self, temp_commands_dir):
        """Test that whitespace in command syntax is handled correctly."""
        processor = CommandProcessor(temp_commands_dir)

        # Extra whitespace
        content = '<!--   cmd:   callout   icon="test.svg"   -->Content<!--   /cmd   -->'

        result = processor.process(content)

        assert 'test.svg' in result
        assert 'Content' in result
