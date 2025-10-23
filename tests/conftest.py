"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path
from docco.core.section import Section, SectionNumberer
from docco.core.document import Document
from docco.content.markdown import MarkdownConverter


@pytest.fixture
def sample_sections():
    """Sample sections for testing."""
    return [
        Section(level=1, title="Introduction", content="This is the **introduction**."),
        Section(level=2, title="Purpose", content="This explains the *purpose*."),
        Section(level=2, title="Scope", content="This defines the scope.\n\n- Item 1\n- Item 2"),
        Section(level=1, title="Details", content="Technical details here."),
    ]


@pytest.fixture
def numbered_sections():
    """Pre-numbered sections for testing."""
    return [
        Section(level=1, title="Introduction", content="Content 1", number="1"),
        Section(level=2, title="Purpose", content="Content 2", number="1.1"),
        Section(level=2, title="Scope", content="Content 3", number="1.2"),
        Section(level=1, title="Details", content="Content 4", number="2"),
    ]


@pytest.fixture
def addendum_sections():
    """Sections including addendums (level=0)."""
    return [
        Section(level=1, title="Main Content", content="Main content here."),
        Section(level=0, title="Appendix One", content="Appendix content."),
        Section(level=0, title="Appendix Two", content="More appendix content."),
    ]


@pytest.fixture
def section_numberer():
    """Fresh SectionNumberer instance."""
    return SectionNumberer()


@pytest.fixture
def markdown_converter():
    """MarkdownConverter instance."""
    return MarkdownConverter()


@pytest.fixture
def simple_document():
    """Simple document with metadata."""
    doc = Document(
        title="Test Document",
        subtitle="Test Subtitle",
        date="2025-10-23"
    )
    doc.add_section(level=1, title="Introduction", content="This is a test.")
    doc.add_section(level=2, title="Details", content="More details here.")
    return doc


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output directory for test files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
