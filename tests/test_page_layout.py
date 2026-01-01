# type: ignore
"""Tests for page layout directive processing."""

from docco.page_layout import process_page_layout


def test_pagebreak_directive():
    """Test that pagebreak directive is converted to div."""
    html = "<p>Before</p>\n<!-- pagebreak -->\n<p>After</p>"
    result = process_page_layout(html)
    assert '<div class="pagebreak"></div>' in result
    assert "<!-- pagebreak -->" not in result


def test_landscape_orientation():
    """Test landscape orientation directive wraps content."""
    html = "<p>Before</p>\n<!-- landscape -->\n<p>Landscape content</p>\n<!-- portrait -->\n<p>After</p>"
    result = process_page_layout(html)
    assert 'class="section-wrapper landscape"' in result
    assert "Landscape content" in result


def test_portrait_orientation():
    """Test portrait orientation directive wraps content."""
    html = "<p>Portrait</p>"
    result = process_page_layout(html)
    assert 'class="section-wrapper portrait"' in result
    assert "Portrait" in result


def test_multiple_orientation_switches():
    """Test multiple orientation switches."""
    html = """<p>Start</p>
<!-- landscape -->
<p>Landscape 1</p>
<!-- portrait -->
<p>Portrait</p>
<!-- landscape -->
<p>Landscape 2</p>"""
    result = process_page_layout(html)
    assert result.count('class="section-wrapper landscape"') == 2
    assert result.count('class="section-wrapper portrait"') == 2


def test_default_portrait():
    """Test that content defaults to portrait orientation."""
    html = "<p>Content</p>"
    result = process_page_layout(html)
    assert 'class="section-wrapper portrait"' in result


def test_pagebreak_with_orientation():
    """Test pagebreak directive works with orientation directives."""
    html = """<p>Content</p>
<!-- pagebreak -->
<!-- landscape -->
<p>Landscape</p>"""
    result = process_page_layout(html)
    assert '<div class="pagebreak"></div>' in result
    assert 'class="section-wrapper landscape"' in result


def test_multiple_pagebreaks():
    """Test multiple pagebreak directives."""
    html = """<p>Page 1</p>
<!-- pagebreak -->
<p>Page 2</p>
<!-- pagebreak -->
<p>Page 3</p>"""
    result = process_page_layout(html)
    assert result.count('<div class="pagebreak"></div>') == 2


def test_empty_sections():
    """Test that empty sections are not created."""
    html = "<!-- landscape --><!-- portrait --><p>Content</p>"
    result = process_page_layout(html)
    # Should handle gracefully without creating empty divs
    assert "<p>Content</p>" in result


def test_whitespace_handling():
    """Test that directives with whitespace are handled correctly."""
    html = "<p>Content</p>\n<!--  pagebreak  -->\n<p>More</p>"
    result = process_page_layout(html)
    assert '<div class="pagebreak"></div>' in result
    assert "<!--  pagebreak  -->" not in result
