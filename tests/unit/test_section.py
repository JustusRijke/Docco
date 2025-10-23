"""
Unit tests for Section and SectionNumberer.
"""

import pytest
from docco.core.section import Section, SectionNumberer


class TestSection:
    """Tests for Section dataclass."""

    def test_section_creation(self):
        """Test creating a valid section."""
        section = Section(level=1, title="Test", content="Content")
        assert section.level == 1
        assert section.title == "Test"
        assert section.content == "Content"
        assert section.number is None

    def test_section_with_number(self):
        """Test creating a section with manual number."""
        section = Section(level=1, title="Test", content="Content", number="1.2")
        assert section.number == "1.2"

    def test_invalid_level_too_low(self):
        """Test that level < 0 raises ValueError."""
        with pytest.raises(ValueError, match="Section level must be 0-3"):
            Section(level=-1, title="Test", content="Content")

    def test_invalid_level_too_high(self):
        """Test that level > 3 raises ValueError."""
        with pytest.raises(ValueError, match="Section level must be 0-3"):
            Section(level=4, title="Test", content="Content")

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Section title cannot be empty"):
            Section(level=1, title="", content="Content")


class TestSectionNumberer:
    """Tests for SectionNumberer."""

    def test_simple_numbering(self, section_numberer):
        """Test basic sequential numbering."""
        s1 = Section(level=1, title="First", content="")
        s2 = Section(level=1, title="Second", content="")

        assert section_numberer.number_section(s1) == "1"
        assert section_numberer.number_section(s2) == "2"

    def test_hierarchical_numbering(self, section_numberer):
        """Test hierarchical section numbering."""
        s1 = Section(level=1, title="First", content="")
        s2 = Section(level=2, title="First.One", content="")
        s3 = Section(level=2, title="First.Two", content="")
        s4 = Section(level=1, title="Second", content="")

        assert section_numberer.number_section(s1) == "1"
        assert section_numberer.number_section(s2) == "1.1"
        assert section_numberer.number_section(s3) == "1.2"
        assert section_numberer.number_section(s4) == "2"

    def test_three_level_numbering(self, section_numberer):
        """Test three-level hierarchical numbering."""
        s1 = Section(level=1, title="One", content="")
        s2 = Section(level=2, title="One.One", content="")
        s3 = Section(level=3, title="One.One.One", content="")
        s4 = Section(level=3, title="One.One.Two", content="")
        s5 = Section(level=2, title="One.Two", content="")

        assert section_numberer.number_section(s1) == "1"
        assert section_numberer.number_section(s2) == "1.1"
        assert section_numberer.number_section(s3) == "1.1.1"
        assert section_numberer.number_section(s4) == "1.1.2"
        assert section_numberer.number_section(s5) == "1.2"

    def test_counter_reset_on_level_change(self, section_numberer):
        """Test that deeper counters reset when going back to higher level."""
        s1 = Section(level=1, title="One", content="")
        s2 = Section(level=2, title="One.One", content="")
        s3 = Section(level=2, title="One.Two", content="")
        s4 = Section(level=1, title="Two", content="")
        s5 = Section(level=2, title="Two.One", content="")

        section_numberer.number_section(s1)
        section_numberer.number_section(s2)
        section_numberer.number_section(s3)
        section_numberer.number_section(s4)
        result = section_numberer.number_section(s5)

        assert result == "2.1"  # Should be 2.1, not 2.3

    def test_addendum_lettering(self, section_numberer):
        """Test that level=0 sections get letter numbering."""
        a1 = Section(level=0, title="Appendix One", content="")
        a2 = Section(level=0, title="Appendix Two", content="")
        a3 = Section(level=0, title="Appendix Three", content="")

        assert section_numberer.number_section(a1) == "A"
        assert section_numberer.number_section(a2) == "B"
        assert section_numberer.number_section(a3) == "C"

    def test_mixed_sections_and_addendums(self, section_numberer):
        """Test numbering with both regular sections and addendums."""
        s1 = Section(level=1, title="Main Section", content="")
        s2 = Section(level=2, title="Subsection", content="")
        a1 = Section(level=0, title="Appendix", content="")

        assert section_numberer.number_section(s1) == "1"
        assert section_numberer.number_section(s2) == "1.1"
        assert section_numberer.number_section(a1) == "A"

    def test_number_sections_list(self, section_numberer, sample_sections):
        """Test numbering a list of sections in place."""
        result = section_numberer.number_sections(sample_sections)

        assert result is sample_sections  # Should modify in place
        assert sample_sections[0].number == "1"
        assert sample_sections[1].number == "1.1"
        assert sample_sections[2].number == "1.2"
        assert sample_sections[3].number == "2"

    def test_reset(self, section_numberer):
        """Test resetting the numberer."""
        s1 = Section(level=1, title="First", content="")
        section_numberer.number_section(s1)

        section_numberer.reset()

        s2 = Section(level=1, title="Second", content="")
        assert section_numberer.number_section(s2) == "1"  # Should start over
