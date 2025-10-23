"""
Integration tests for Document class.
"""

import pytest
from pathlib import Path
from docco import Document


class TestDocument:
    """Integration tests for full document workflow."""

    def test_document_creation(self):
        """Test creating a document with metadata."""
        doc = Document(title="Test Doc", subtitle="Subtitle", date="2025-10-23")

        assert doc.title == "Test Doc"
        assert doc.subtitle == "Subtitle"
        assert doc.date == "2025-10-23"
        assert len(doc) == 0

    def test_add_section(self):
        """Test adding sections to document."""
        doc = Document(title="Test")
        doc.add_section(level=1, title="Introduction", content="Content here")
        doc.add_section(level=2, title="Details", content="More content")

        assert len(doc) == 2
        assert doc.sections[0].title == "Introduction"
        assert doc.sections[1].title == "Details"

    def test_method_chaining(self):
        """Test that add_section returns self for chaining."""
        doc = Document(title="Test")
        result = doc.add_section(level=1, title="S1", content="C1").add_section(
            level=2, title="S2", content="C2"
        )

        assert result is doc
        assert len(doc) == 2

    def test_automatic_numbering(self):
        """Test that sections are automatically numbered."""
        doc = Document(title="Test")
        doc.add_section(level=1, title="First", content="")
        doc.add_section(level=2, title="First.One", content="")
        doc.add_section(level=1, title="Second", content="")

        html = doc.build_html()

        assert "1 First" in html
        assert "1.1 First.One" in html
        assert "2 Second" in html

    def test_manual_numbering(self):
        """Test providing manual section numbers."""
        doc = Document(title="Test")
        doc.add_section(level=1, title="Custom", content="", number="X.1")

        html = doc.build_html()

        assert "X.1 Custom" in html

    def test_build_html(self, simple_document):
        """Test HTML generation."""
        html = simple_document.build_html()

        assert "<!DOCTYPE html>" in html
        assert "<title>Test Document</title>" in html
        assert "Test Subtitle" in html
        assert "2025-10-23" in html
        assert "Introduction" in html

    def test_build_html_with_save(self, simple_document, tmp_output_dir):
        """Test saving HTML to file."""
        save_path = tmp_output_dir / "test.html"
        html = simple_document.build_html(save_path=save_path)

        assert save_path.exists()
        content = save_path.read_text(encoding="utf-8")
        assert content == html
        assert "<!DOCTYPE html>" in content

    def test_render_pdf(self, simple_document, tmp_output_dir):
        """Test PDF generation."""
        pdf_path = tmp_output_dir / "test.pdf"
        result = simple_document.render_pdf(pdf_path)

        assert result == pdf_path
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0  # PDF should have content

    def test_render_pdf_with_string_path(self, simple_document, tmp_output_dir):
        """Test PDF generation with string path."""
        pdf_path = tmp_output_dir / "test.pdf"
        result = simple_document.render_pdf(str(pdf_path))

        assert result == pdf_path
        assert pdf_path.exists()

    def test_render_pdf_with_html_debug(self, simple_document, tmp_output_dir):
        """Test PDF generation with HTML debug output."""
        pdf_path = tmp_output_dir / "test.pdf"
        simple_document.render_pdf(pdf_path, save_html=True)

        html_path = tmp_output_dir / "debug.html"
        assert html_path.exists()
        html_content = html_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content

    def test_clear_sections(self):
        """Test clearing all sections."""
        doc = Document(title="Test")
        doc.add_section(level=1, title="S1", content="C1")
        doc.add_section(level=1, title="S2", content="C2")

        result = doc.clear_sections()

        assert result is doc
        assert len(doc) == 0

    def test_clear_resets_numbering(self):
        """Test that clear resets numbering."""
        doc = Document(title="Test")
        doc.add_section(level=1, title="First", content="")
        doc.add_section(level=1, title="Second", content="")
        doc.clear_sections()
        doc.add_section(level=1, title="New First", content="")

        html = doc.build_html()

        assert "1 New First" in html  # Should be 1, not 3

    def test_document_repr(self):
        """Test document string representation."""
        doc = Document(title="My Doc")
        doc.add_section(level=1, title="S1", content="")

        assert "My Doc" in repr(doc)
        assert "sections=1" in repr(doc)

    def test_custom_header_text(self, tmp_output_dir):
        """Test custom header text in CSS."""
        doc = Document(title="Doc Title", header_text="Custom Header")
        doc.add_section(level=1, title="Section", content="Content")

        pdf_path = tmp_output_dir / "test.pdf"
        doc.render_pdf(pdf_path)

        # PDF should be generated successfully
        assert pdf_path.exists()

    def test_addendum_sections(self, tmp_output_dir):
        """Test document with addendum sections."""
        doc = Document(title="Test with Addendums")
        doc.add_section(level=1, title="Main Section", content="Main content")
        doc.add_section(level=0, title="Appendix A", content="Appendix content")
        doc.add_section(level=0, title="Appendix B", content="More appendix content")

        html = doc.build_html()

        assert "1 Main Section" in html
        assert "A Appendix A" in html
        assert "B Appendix B" in html

    def test_complex_document(self, tmp_output_dir):
        """Test generating a complex multi-level document."""
        doc = Document(
            title="Complex Document",
            subtitle="Testing Multi-Level Sections",
            date="2025-10-23"
        )

        doc.add_section(level=1, title="Introduction", content="Introduction content")
        doc.add_section(level=2, title="Background", content="Background info")
        doc.add_section(level=3, title="History", content="Historical context")
        doc.add_section(level=2, title="Motivation", content="Why this matters")
        doc.add_section(level=1, title="Methods", content="Our approach")
        doc.add_section(level=2, title="Design", content="Design details")
        doc.add_section(level=1, title="Results", content="What we found")

        pdf_path = tmp_output_dir / "complex.pdf"
        doc.render_pdf(pdf_path, save_html=True)

        assert pdf_path.exists()
        assert (tmp_output_dir / "debug.html").exists()

        # Verify numbering in HTML
        html = (tmp_output_dir / "debug.html").read_text()
        assert "1 Introduction" in html
        assert "1.1 Background" in html
        assert "1.1.1 History" in html
        assert "1.2 Motivation" in html
        assert "2 Methods" in html
        assert "2.1 Design" in html
        assert "3 Results" in html
