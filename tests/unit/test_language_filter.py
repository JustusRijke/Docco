"""
Unit tests for language filtering.
"""

import pytest
from docco.content.language_filter import LanguageFilter


class TestLanguageFilter:
    """Tests for LanguageFilter class."""

    def test_filter_single_language_block(self):
        """Test filtering with a single language block."""
        filter = LanguageFilter()
        content = '''
Common text

<!-- lang:NL -->
Nederlandse tekst
<!-- /lang -->

<!-- lang:EN -->
English text
<!-- /lang -->
'''

        result_nl = filter.filter_for_language(content, "NL")
        result_en = filter.filter_for_language(content, "EN")

        # NL version should have common text and Dutch text
        assert "Common text" in result_nl
        assert "Nederlandse tekst" in result_nl
        assert "English text" not in result_nl

        # EN version should have common text and English text
        assert "Common text" in result_en
        assert "English text" in result_en
        assert "Nederlandse tekst" not in result_en

    def test_filter_preserves_untagged_content(self):
        """Test that untagged content is preserved in all languages."""
        filter = LanguageFilter()
        content = '''
# Common heading

<!-- lang:DE -->
Deutsche Sektion
<!-- /lang -->

More common text
'''

        result_de = filter.filter_for_language(content, "DE")
        result_en = filter.filter_for_language(content, "EN")

        # Both should have common content
        assert "# Common heading" in result_de
        assert "More common text" in result_de
        assert "# Common heading" in result_en
        assert "More common text" in result_en

        # Only DE should have German text
        assert "Deutsche Sektion" in result_de
        assert "Deutsche Sektion" not in result_en

    def test_filter_multiple_language_blocks(self):
        """Test filtering with multiple blocks of the same language."""
        filter = LanguageFilter()
        content = '''
<!-- lang:NL -->
Eerste Nederlandse sectie
<!-- /lang -->

Common text

<!-- lang:NL -->
Tweede Nederlandse sectie
<!-- /lang -->

<!-- lang:EN -->
English section
<!-- /lang -->
'''

        result_nl = filter.filter_for_language(content, "NL")

        # Should include both Dutch sections
        assert "Eerste Nederlandse sectie" in result_nl
        assert "Tweede Nederlandse sectie" in result_nl
        assert "Common text" in result_nl
        assert "English section" not in result_nl

    def test_filter_multiline_content(self):
        """Test filtering with multiline language blocks."""
        filter = LanguageFilter()
        content = '''<!-- lang:EN -->
# English Section
Paragraph 1
Paragraph 2
## Subsection
More content
<!-- /lang -->'''

        result_en = filter.filter_for_language(content, "EN")
        result_nl = filter.filter_for_language(content, "NL")

        # EN should have all content
        assert "# English Section" in result_en
        assert "Paragraph 1" in result_en
        assert "Paragraph 2" in result_en
        assert "## Subsection" in result_en
        assert "More content" in result_en

        # NL should not have any of it
        assert "# English Section" not in result_nl
        assert "Paragraph 1" not in result_nl

    def test_filter_removes_language_tags(self):
        """Test that language tags are removed from output."""
        filter = LanguageFilter()
        content = '<!-- lang:NL -->Nederlandse tekst<!-- /lang -->'

        result = filter.filter_for_language(content, "NL")

        # Should have content but not the tags
        assert "Nederlandse tekst" in result
        assert "<!-- lang:NL -->" not in result
        assert "<!-- /lang -->" not in result

    def test_filter_empty_language_block(self):
        """Test filtering with empty language blocks."""
        filter = LanguageFilter()
        content = '''
Text before
<!-- lang:EN -->
<!-- /lang -->
Text after
'''

        result_en = filter.filter_for_language(content, "EN")
        result_nl = filter.filter_for_language(content, "NL")

        # Both should have text before and after
        assert "Text before" in result_en
        assert "Text after" in result_en
        assert "Text before" in result_nl
        assert "Text after" in result_nl

    def test_filter_whitespace_in_tags(self):
        """Test that whitespace in tags is handled correctly."""
        filter = LanguageFilter()
        content = '''
<!--   lang:NL   -->
Nederlandse tekst
<!--   /lang   -->
'''

        result = filter.filter_for_language(content, "NL")

        assert "Nederlandse tekst" in result
        assert "<!-- lang:" not in result

    def test_filter_no_language_tags(self):
        """Test filtering content with no language tags."""
        filter = LanguageFilter()
        content = '''
# All Common Content
Paragraph 1
Paragraph 2
'''

        result_nl = filter.filter_for_language(content, "NL")
        result_en = filter.filter_for_language(content, "EN")

        # All content should be in all languages
        assert result_nl == content
        assert result_en == content

    def test_filter_case_sensitive_language_codes(self):
        """Test that language codes are case-sensitive."""
        filter = LanguageFilter()
        content = '''
<!-- lang:NL -->
Nederlandse tekst
<!-- /lang -->
'''

        result_nl = filter.filter_for_language(content, "NL")
        result_nl_lower = filter.filter_for_language(content, "nl")

        # NL should match
        assert "Nederlandse tekst" in result_nl

        # nl (lowercase) should not match
        assert "Nederlandse tekst" not in result_nl_lower
