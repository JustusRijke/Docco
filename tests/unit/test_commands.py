"""
Unit tests for inline directive processing.
"""

import pytest
from pathlib import Path
from docco.content.commands import InlineProcessor


@pytest.fixture
def temp_inlines_dir(tmp_path):
    """Create a temporary inlines directory with sample templates."""
    inlines_dir = tmp_path / "inlines"
    inlines_dir.mkdir()

    # Simple template (markdown)
    (inlines_dir / "callout.md").write_text(
        "| | |\n|---|---|\n| ![]({{icon}}) | {{content}} |"
    )

    # Template with multiple variables
    (inlines_dir / "alert.md").write_text(
        "**{{type}} - {{title}}:** {{message}}"
    )

    return tmp_path


class TestInlineProcessor:
    """Tests for InlineProcessor class."""

    def test_block_inline_basic(self, temp_inlines_dir):
        """Test basic block inline expansion."""
        processor = InlineProcessor(temp_inlines_dir)
        content = '<!-- inline: callout icon="test.svg" -->Hello World<!-- /inline -->'

        result = processor.process(content)

        assert '![](test.svg)' in result
        assert 'Hello World' in result
        assert '<!-- inline:' not in result

    def test_self_closing_inline(self, temp_inlines_dir):
        """Test self-closing inline syntax."""
        processor = InlineProcessor(temp_inlines_dir)
        content = '<!-- inline: alert type="warning" title="Note" message="Test" /-->'

        result = processor.process(content)

        assert '**warning - Note:** Test' in result
        assert '<!-- inline:' not in result

    def test_multiple_arguments(self, temp_inlines_dir):
        """Test inline with multiple arguments."""
        processor = InlineProcessor(temp_inlines_dir)
        content = '<!-- inline: alert type="info" title="Info" message="Details here" /-->'

        result = processor.process(content)

        assert '**info - Info:** Details here' in result

    def test_missing_template(self, temp_inlines_dir):
        """Test inline with non-existent template leaves content unchanged."""
        processor = InlineProcessor(temp_inlines_dir)
        original = '<!-- inline: nonexistent arg="val" -->content<!-- /inline -->'

        result = processor.process(original)

        assert result == original

    def test_missing_variable(self, temp_inlines_dir):
        """Test that missing variables are replaced with empty strings."""
        processor = InlineProcessor(temp_inlines_dir)
        content = '<!-- inline: callout -->No icon specified<!-- /inline -->'

        result = processor.process(content)

        assert 'No icon specified' in result
        # Icon variable should be empty string
        assert '![](' in result

    def test_multiline_content(self, temp_inlines_dir):
        """Test inline with multiline content."""
        processor = InlineProcessor(temp_inlines_dir)
        content = '''<!-- inline: callout icon="test.svg" -->
Line 1
Line 2
Line 3
<!-- /inline -->'''

        result = processor.process(content)

        assert 'Line 1' in result
        assert 'Line 2' in result
        assert 'Line 3' in result

    def test_multiple_inlines(self, temp_inlines_dir):
        """Test processing multiple inlines in one document."""
        processor = InlineProcessor(temp_inlines_dir)
        content = '''
Text before
<!-- inline: callout icon="a.svg" -->First callout<!-- /inline -->
Text between
<!-- inline: callout icon="b.svg" -->Second callout<!-- /inline -->
Text after
'''

        result = processor.process(content)

        assert 'a.svg' in result
        assert 'b.svg' in result
        assert 'First callout' in result
        assert 'Second callout' in result

    def test_single_quotes_in_args(self, temp_inlines_dir):
        """Test arguments with single quotes."""
        processor = InlineProcessor(temp_inlines_dir)
        content = "<!-- inline: callout icon='test.svg' -->Content<!-- /inline -->"

        result = processor.process(content)

        assert 'test.svg' in result

    def test_template_caching(self, temp_inlines_dir):
        """Test that templates are cached after first load."""
        processor = InlineProcessor(temp_inlines_dir)

        # First call loads template
        processor.process('<!-- inline: callout icon="a.svg" -->Test<!-- /inline -->')

        # Check cache
        assert 'callout' in processor._template_cache

        # Second call should use cache
        result = processor.process('<!-- inline: callout icon="b.svg" -->Test 2<!-- /inline -->')
        assert 'b.svg' in result

    def test_no_inlines_dir(self, tmp_path):
        """Test behavior when inlines directory doesn't exist."""
        processor = InlineProcessor(tmp_path)
        original = '<!-- inline: test arg="val" -->content<!-- /inline -->'

        result = processor.process(original)

        # Should leave content unchanged
        assert result == original

    def test_whitespace_handling(self, temp_inlines_dir):
        """Test that whitespace in inline syntax is handled correctly."""
        processor = InlineProcessor(temp_inlines_dir)

        # Extra whitespace
        content = '<!--   inline:   callout   icon="test.svg"   -->Content<!--   /inline   -->'

        result = processor.process(content)

        assert 'test.svg' in result
        assert 'Content' in result

    def test_recursive_inlines(self, temp_inlines_dir):
        """Test recursive inline expansion."""
        # Create a template that uses another inline
        inlines_dir = temp_inlines_dir / "inlines"
        (inlines_dir / "wrapper.md").write_text(
            "**Wrapped:** <!-- inline: alert type=\"info\" title=\"Inner\" message=\"{{content}}\" /-->"
        )

        processor = InlineProcessor(temp_inlines_dir)
        content = '<!-- inline: wrapper content="Test content" /-->'

        result = processor.process(content)

        assert '**Wrapped:**' in result
        assert '**info - Inner:** Test content' in result

    def test_recursion_depth_limit(self, temp_inlines_dir):
        """Test that recursion depth limit prevents infinite loops."""
        # Create a self-referencing template
        inlines_dir = temp_inlines_dir / "inlines"
        (inlines_dir / "recursive.md").write_text(
            "Recursive: <!-- inline: recursive /-->"
        )

        processor = InlineProcessor(temp_inlines_dir, max_depth=3)
        content = '<!-- inline: recursive /-->'

        result = processor.process(content)

        # Should stop at max_depth without infinite loop
        assert 'Recursive:' in result
