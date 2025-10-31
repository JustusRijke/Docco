"""Tests for language splitting and filtering."""

from docco.language import split_by_language


def test_no_languages_single_output():
    """Test that content without languages tag produces single output."""
    content = """# Document

Some content here.

More content."""
    results = split_by_language(content, {})
    assert len(results) == 1
    assert results[None] == content


def test_multiple_languages_split():
    """Test that languages tag creates multiple outputs."""
    content = """# Document

Shared content."""
    metadata = {"languages": "EN DE NL"}
    results = split_by_language(content, metadata)
    assert len(results) == 3
    assert "EN" in results
    assert "DE" in results
    assert "NL" in results


def test_language_filtering():
    """Test that language-specific content is filtered correctly."""
    content = """# Document

Shared content.

<!-- lang:EN -->
English only.
<!-- /lang -->

<!-- lang:DE -->
Deutsch nur.
<!-- /lang -->

Final shared."""
    metadata = {"languages": "EN DE"}
    results = split_by_language(content, metadata)

    assert "English only" in results["EN"]
    assert "Deutsch nur" not in results["EN"]
    assert "Final shared" in results["EN"]

    assert "Deutsch nur" in results["DE"]
    assert "English only" not in results["DE"]
    assert "Final shared" in results["DE"]


def test_mixed_content():
    """Test that untagged content appears in all languages."""
    content = """# Document

Shared.

<!-- lang:EN -->
English.
<!-- /lang -->

More shared."""
    metadata = {"languages": "EN NL"}
    results = split_by_language(content, metadata)

    assert "Shared" in results["EN"]
    assert "More shared" in results["EN"]
    assert "English" in results["EN"]

    assert "Shared" in results["NL"]
    assert "More shared" in results["NL"]
    assert "English" not in results["NL"]


def test_nested_lang_tags():
    """Test handling of nested language tags."""
    content = """# Document

<!-- lang:EN -->
<!-- lang:DE -->
Nested
<!-- /lang -->
English
<!-- /lang -->"""
    metadata = {"languages": "EN DE"}
    results = split_by_language(content, metadata)
    # Should handle nested tags gracefully
    assert "EN" in results
    assert "DE" in results


def test_unmatched_lang_tag():
    """Test language tag for language not in frontmatter is ignored."""
    content = """# Document

<!-- lang:FR -->
French content.
<!-- /lang -->

Shared content."""
    metadata = {"languages": "EN DE"}
    results = split_by_language(content, metadata)

    # FR content should not appear in EN or DE
    assert "French content" not in results["EN"]
    assert "French content" not in results["DE"]
    assert "Shared content" in results["EN"]


def test_empty_language_block():
    """Test empty language blocks are handled."""
    content = """# Document

<!-- lang:EN -->
<!-- /lang -->

Shared."""
    metadata = {"languages": "EN"}
    results = split_by_language(content, metadata)
    assert "Shared" in results["EN"]


def test_single_language():
    """Test single language in frontmatter."""
    content = """# Document

Content here."""
    metadata = {"languages": "EN"}
    results = split_by_language(content, metadata)
    assert len(results) == 1
    assert "EN" in results


def test_html_comments_in_backticks():
    """Test that HTML comments inside backticks are not treated as lang tags."""
    content = """# Document

Shared.

<!-- lang:EN -->
Use `<!-- lang:EN -->...<!-- /lang -->` to mark English-only content.
<!-- /lang -->

<!-- lang:DE -->
Verwenden Sie `<!-- lang:DE -->...<!-- /lang -->`, um nur auf Deutsch verfügbare Inhalte zu markieren.
<!-- /lang -->

Final shared."""
    metadata = {"languages": "EN DE"}
    results = split_by_language(content, metadata)

    # Check that English version doesn't have German content
    assert "English-only" in results["EN"]
    assert "Verwenden Sie" not in results["EN"]
    assert "Final shared" in results["EN"]

    # Check that German version doesn't have English content
    assert "mark English-only" not in results["DE"]
    assert "Verwenden Sie" in results["DE"]
    assert "Final shared" in results["DE"]


def test_lang_tags_mid_line_not_matched():
    """Test that lang tags can now appear anywhere (unless in code blocks)."""
    content = """# Document

This text has <!-- lang:EN -->English<!-- /lang --> content inline.

Final text."""
    metadata = {"languages": "EN DE"}
    results = split_by_language(content, metadata)

    # NEW BEHAVIOR: Mid-line lang tags ARE now processed
    assert "English" in results["EN"]
    assert "English" not in results["DE"]
    assert "<!-- lang:EN -->" not in results["EN"]
    assert "<!-- lang:EN -->" not in results["DE"]
