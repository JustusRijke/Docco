"""Tests for TOC (Table of Contents) processing."""

import re

from docco.toc import _build_toc_html, _extract_headings, _generate_id, process_toc


def test_generate_id_basic():
    """Test ID generation from simple text."""
    assert _generate_id("Hello World") == "hello-world"
    assert _generate_id("Test Heading") == "test-heading"


def test_generate_id_special_chars():
    """Test ID generation removes special characters."""
    assert _generate_id("Hello, World!") == "hello-world"
    assert _generate_id("Test-Heading_123") == "test-heading_123"


def test_generate_id_with_html():
    """Test ID generation strips HTML tags."""
    assert _generate_id("<strong>Bold</strong> Text") == "bold-text"
    assert _generate_id("<em>Italic</em>") == "italic"


def test_toc_directive_replacement():
    """Test that TOC directive is replaced with TOC HTML."""
    html = "<!-- TOC -->\n<h1>Heading</h1>"
    result = process_toc(html)
    assert "<!-- TOC -->" not in result
    assert '<nav class="toc">' in result


def test_no_toc_directive():
    """Test that HTML without TOC directive is unchanged."""
    html = "<h1>Heading</h1>\n<p>Content</p>"
    result = process_toc(html)
    assert result == html


def test_heading_id_generation():
    """Test that headings without IDs get IDs added."""
    html = "<h1>Test Heading</h1>"
    modified_html, headings = _extract_headings(html)
    assert 'id="test-heading"' in modified_html
    assert len(headings) == 1
    assert headings[0] == (1, "test-heading", "Test Heading")


def test_heading_with_existing_id():
    """Test that headings with existing IDs are preserved."""
    html = '<h1 id="custom-id">Test Heading</h1>'
    modified_html, headings = _extract_headings(html)
    assert 'id="custom-id"' in modified_html
    assert headings[0] == (1, "custom-id", "Test Heading")


def test_duplicate_heading_ids():
    """Test that duplicate heading texts get unique IDs."""
    html = "<h1>Heading</h1>\n<h2>Heading</h2>\n<h3>Heading</h3>"
    modified_html, headings = _extract_headings(html)
    assert 'id="heading"' in modified_html
    assert 'id="heading-1"' in modified_html
    assert 'id="heading-2"' in modified_html


def test_hierarchical_toc_structure():
    """Test that TOC builds proper hierarchical structure."""
    headings = [
        (1, "h1", "Chapter 1"),
        (2, "h2", "Section 1.1"),
        (2, "h3", "Section 1.2"),
        (1, "h4", "Chapter 2"),
    ]
    toc_html = _build_toc_html(headings)
    assert '<nav class="toc">' in toc_html
    assert "toc-level-1" in toc_html
    assert "toc-level-2" in toc_html
    assert '<a href="#h1"><span class="toc-number">1 </span>Chapter 1</a>' in toc_html


def test_toc_with_no_headings():
    """Test TOC generation with no headings."""
    html = "<!-- TOC -->\n<p>No headings here</p>"
    result = process_toc(html)
    assert '<nav class="toc">' in result
    assert "No headings found" in result


def test_multiple_heading_levels():
    """Test extraction of all heading levels h1-h6."""
    html = """
    <h1>H1</h1>
    <h2>H2</h2>
    <h3>H3</h3>
    <h4>H4</h4>
    <h5>H5</h5>
    <h6>H6</h6>
    """
    modified_html, headings = _extract_headings(html)
    assert len(headings) == 6
    assert headings[0][0] == 1  # h1
    assert headings[1][0] == 2  # h2
    assert headings[5][0] == 6  # h6


def test_toc_links_to_headings():
    """Test that TOC contains links to heading IDs."""
    html = "<!-- TOC -->\n<h1>Introduction</h1>\n<h2>Background</h2>"
    result = process_toc(html)
    assert (
        '<a href="#introduction"><span class="toc-number">1 </span>Introduction</a>'
        in result
    )
    assert (
        '<a href="#background"><span class="toc-number">1.1 </span>Background</a>'
        in result
    )
    assert 'id="introduction"' in result
    assert 'id="background"' in result


def test_whitespace_in_toc_directive():
    """Test that TOC directive with whitespace is handled."""
    html = "<!--  TOC  -->\n<h1>Heading</h1>"
    result = process_toc(html)
    assert "<!--  TOC  -->" not in result
    assert '<nav class="toc">' in result


def test_toc_strips_html_from_display():
    """Test that TOC display text has HTML tags stripped."""
    html = "<!-- TOC -->\n<h1><strong>Bold</strong> Heading</h1>"
    result = process_toc(html)
    assert (
        '<a href="#bold-heading"><span class="toc-number">1 </span>Bold Heading</a>'
        in result
    )


def test_empty_heading_id():
    """Test that empty headings get default ID."""
    html = "<h1></h1>"
    modified_html, headings = _extract_headings(html)
    assert 'id="heading"' in modified_html


def test_heading_with_attributes_no_id():
    """Test heading with existing attributes gets ID added."""
    html = '<h1 class="title">Heading</h1>'
    modified_html, headings = _extract_headings(html)
    assert 'id="heading"' in modified_html
    assert 'class="title"' in modified_html


def test_skipped_heading_levels():
    """Test TOC handles skipped heading levels (e.g., h1 -> h3)."""
    headings = [
        (1, "h1", "Chapter"),
        (3, "h3", "Subsection"),  # Skips h2
    ]
    toc_html = _build_toc_html(headings)
    assert '<nav class="toc">' in toc_html
    # Should handle gracefully by opening intermediate lists
    assert "toc-level-1" in toc_html
    assert "toc-level-3" in toc_html


def test_toc_exclude_directive():
    """Test that headings with toc:exclude are not in TOC."""
    html = """<!-- TOC -->
    <h1>Chapter 1</h1>
    <!-- toc:exclude -->
    <h2>Excluded Section</h2>
    <h2>Included Section</h2>"""
    result = process_toc(html)

    # TOC should not contain excluded heading
    assert "Excluded Section" not in result.split("<h2")[0]  # Not in TOC
    # But heading still exists in document
    assert "<h2" in result
    assert "Excluded Section" in result
    # Included section should be in TOC
    assert "Included Section" in result.split("</nav>")[0]


def test_toc_exclude_removes_directive():
    """Test that toc:exclude directive is removed from output."""
    html = "<!-- toc:exclude -->\n<h1>Heading</h1>"
    modified_html, headings = _extract_headings(html)
    assert "<!-- toc:exclude -->" not in modified_html
    assert len(headings) == 0  # Excluded heading not in list


def test_toc_numbering_in_html():
    """Test that TOC entries have numbers in HTML."""
    headings = [
        (1, "h1", "Chapter 1"),
        (2, "h2", "Section 1.1"),
        (2, "h3", "Section 1.2"),
        (1, "h4", "Chapter 2"),
    ]
    toc_html = _build_toc_html(headings)
    assert '<a href="#h1"><span class="toc-number">1 </span>Chapter 1</a>' in toc_html
    assert (
        '<a href="#h2"><span class="toc-number">1.1 </span>Section 1.1</a>' in toc_html
    )
    assert (
        '<a href="#h3"><span class="toc-number">1.2 </span>Section 1.2</a>' in toc_html
    )
    assert '<a href="#h4"><span class="toc-number">2 </span>Chapter 2</a>' in toc_html


def test_multiple_toc_excludes():
    """Test multiple excluded headings."""
    html = """
    <h1>Chapter 1</h1>
    <!-- toc:exclude -->
    <h2>Excluded 1</h2>
    <h2>Included</h2>
    <!-- toc:exclude -->
    <h2>Excluded 2</h2>
    """
    modified_html, headings = _extract_headings(html)
    assert len(headings) == 2  # Only Chapter 1 and Included
    assert headings[0][2] == "Chapter 1"
    assert headings[1][2] == "Included"


def test_excluded_heading_not_numbered():
    """Test that excluded headings don't get numbers."""
    html = "<!-- TOC -->\n<!-- toc:exclude -->\n<h1>Excluded</h1><h2>First</h2>"
    result = process_toc(html)
    # Excluded heading should not have a number
    assert '<h1 id="excluded">Excluded</h1>' in result
    # First numbered heading starts at 1
    assert '<h2 id="first"><span class="heading-number">1 </span>First</h2>' in result
    assert len(_extract_headings(html)[1]) == 1  # Only one heading in TOC list


def test_excluded_first_heading_numbering_sync():
    """Test that excluding first heading keeps TOC and document numbering in sync."""
    html = """<!-- TOC -->
    <!-- toc:exclude -->
    <h1>Title</h1>
    <h2>Section 1</h2>
    <h2>Section 2</h2>"""
    result = process_toc(html)

    # TOC should have "1 Section 1" and "2 Section 2"
    assert (
        '<a href="#section-1"><span class="toc-number">1 </span>Section 1</a>' in result
    )
    assert (
        '<a href="#section-2"><span class="toc-number">2 </span>Section 2</a>' in result
    )

    # Document headings should match TOC numbering
    assert '<h1 id="title">Title</h1>' in result  # No number
    assert (
        '<h2 id="section-1"><span class="heading-number">1 </span>Section 1</h2>'
        in result
    )
    assert (
        '<h2 id="section-2"><span class="heading-number">2 </span>Section 2</h2>'
        in result
    )


def test_multilevel_toc_balanced_html_tags():
    """Test that multi-level TOC has properly balanced <li> and <ul> tags."""
    # Complex multi-level structure with various nesting patterns
    headings = [
        (1, "chapter-1", "Chapter 1"),
        (2, "section-11", "Section 1.1"),
        (3, "subsection-111", "Subsection 1.1.1"),
        (2, "section-12", "Section 1.2"),
        (1, "chapter-2", "Chapter 2"),
        (2, "section-21", "Section 2.1"),
        (3, "subsection-211", "Subsection 2.1.1"),
        (3, "subsection-212", "Subsection 2.1.2"),
        (2, "section-22", "Section 2.2"),
        (1, "chapter-3", "Chapter 3"),
    ]

    toc_html = _build_toc_html(headings)

    # Count opening and closing tags
    li_open = len(re.findall(r"<li>", toc_html))
    li_close = len(re.findall(r"</li>", toc_html))
    ul_open = len(re.findall(r"<ul", toc_html))
    ul_close = len(re.findall(r"</ul>", toc_html))

    # Verify all tags are balanced
    assert li_open == li_close, (
        f"<li> tags not balanced: {li_open} open, {li_close} close"
    )
    assert ul_open == ul_close, (
        f"<ul> tags not balanced: {ul_open} open, {ul_close} close"
    )

    # Verify expected tag counts (10 headings = 10 list items)
    assert li_open == 10
    assert li_close == 10

    # Verify structure contains expected nesting
    assert '<nav class="toc">' in toc_html
    assert "toc-level-1" in toc_html
    assert "toc-level-2" in toc_html
    assert "toc-level-3" in toc_html

    # Test specific case: parent with children should have </li> after nested </ul>
    # Example: Chapter 1 has children, so structure should be:
    # <li><a>Chapter 1</a>
    #   <ul>...children...</ul>
    # </li>
    assert (
        '<a href="#chapter-1"><span class="toc-number">1 </span>Chapter 1</a>'
        in toc_html
    )
