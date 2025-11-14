"""Integration tests for the parser module."""

import os
import tempfile
import pytest
from docco.parser import parse_markdown, process_directives_iteratively, MAX_ITERATIONS

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


def test_end_to_end_simple(fixture_dir):
    """Test simple markdown parsing and PDF output."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert outputs[0].endswith(".pdf")
        assert os.path.exists(outputs[0])


def test_end_to_end_with_frontmatter(fixture_dir):
    """Test parsing with frontmatter."""
    input_file = os.path.join(fixture_dir, "with_frontmatter.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert outputs[0].endswith(".pdf")
        assert os.path.exists(outputs[0])


def test_end_to_end_with_inline(fixture_dir):
    """Test parsing with inline directives."""
    # Create a temp file with inline
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "with_inline.md")
        # Copy inline target to tmpdir so it's relative to the markdown file
        inline_target = os.path.join(tmpdir, "inline_target.md")
        with open(inline_target, "w") as f:
            f.write("Inlined: {{name}}")

        with open(input_file, "w") as f:
            f.write("""# Document

Before

<!-- inline:"inline_target.md" name="Test" -->

After""")

        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert outputs[0].endswith(".pdf")
        assert os.path.exists(outputs[0])




def test_output_file_naming_simple(fixture_dir):
    """Test that output files are named correctly for simple docs."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs = parse_markdown(input_file, tmpdir)
        basename = os.path.basename(outputs[0])
        assert basename == "simple.pdf"


def test_keep_intermediate_false(fixture_dir):
    """Test that intermediate files are removed by default."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        parse_markdown(input_file, tmpdir, keep_intermediate=False)
        # Should only have PDF files
        all_files = os.listdir(tmpdir)
        assert any(f.endswith(".pdf") for f in all_files)
        assert not any(f.endswith("_intermediate.md") for f in all_files)
        assert not any(f.endswith(".html") for f in all_files)


def test_keep_intermediate_true(fixture_dir):
    """Test that intermediate files are kept when flag is True."""
    input_file = os.path.join(fixture_dir, "simple.md")
    with tempfile.TemporaryDirectory() as tmpdir:
        parse_markdown(input_file, tmpdir, keep_intermediate=True)
        all_files = os.listdir(tmpdir)
        # Should have PDF, HTML, and intermediate MD files
        assert any(f.endswith(".pdf") for f in all_files)
        assert any(f.endswith("_intermediate.md") for f in all_files)
        assert any(f.endswith(".html") for f in all_files)


def test_max_iterations_exceeded_self_referencing():
    """Test that ValueError is raised when inline creates infinite recursion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a markdown file that references itself
        self_ref_file = os.path.join(tmpdir, "self_ref.md")
        with open(self_ref_file, "w") as f:
            f.write("# Self Reference\n<!-- inline:\"self_ref.md\" -->")

        # Create content that inlines the self-referencing file
        content = "# Main\n<!-- inline:\"self_ref.md\" -->"

        with pytest.raises(ValueError, match=f"Max iterations \\({MAX_ITERATIONS}\\) exceeded"):
            process_directives_iteratively(content, tmpdir, False)


def test_multilingual_build_logs_translation_warnings(caplog):
    """Test that incomplete translations trigger warnings in multilingual mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create markdown file with multilingual frontmatter
        input_file = os.path.join(tmpdir, "test.md")
        with open(input_file, "w") as f:
            f.write("""---
multilingual: true
base_language: en
---

# Hello

This is a test document.
""")

        # Create translations directory and incomplete PO file
        translations_dir = os.path.join(tmpdir, "test")
        os.makedirs(translations_dir, exist_ok=True)

        # Create PO file with incomplete translation (fuzzy)
        # Note: When multilingual mode runs, it auto-updates the PO file,
        # so we need to create a PO file that will result in fuzzy/untranslated
        # entries after being merged with the actual POT content
        de_po = os.path.join(translations_dir, "de.po")
        with open(de_po, "w", encoding="utf-8") as f:
            f.write("""# German translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

#, fuzzy
msgid "<h1>Hello</h1>"
msgstr "<h1>Hallo</h1>"
""")

        # Build multilingual PDF
        outputs = parse_markdown(input_file, tmpdir)

        # Should generate PDFs for EN and DE
        assert len(outputs) == 2

        # Should have logged warning about incomplete translation
        # After auto-update, the PO file will have fuzzy and/or untranslated strings
        assert "Translation incomplete for DE" in caplog.text


def test_dpi_frontmatter_parameter(fixture_dir):
    """Test that DPI frontmatter parameter is extracted and used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create markdown with DPI setting
        input_file = os.path.join(tmpdir, "test_dpi.md")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("""---
dpi: 300
---

# Test Document

This document has a DPI setting in frontmatter.
""")

        # Generate PDF
        outputs = parse_markdown(input_file, tmpdir)
        assert len(outputs) == 1
        assert os.path.exists(outputs[0])

        # Verify PDF was created
        assert outputs[0].endswith("test_dpi.pdf")


@pytest.mark.skipif(not PYMUPDF_AVAILABLE, reason="PyMuPDF not available")
def test_dpi_frontmatter_with_image():
    """Test DPI frontmatter with actual image downsampling."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("PIL/Pillow not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a high-resolution test image
        img = Image.new('RGB', (3000, 2000), color='red')
        img_path = os.path.join(tmpdir, "test_image.png")
        img.save(img_path, dpi=(600, 600))

        # Create CSS file with image sizing
        css_path = os.path.join(tmpdir, "style.css")
        with open(css_path, "w") as f:
            f.write("img { max-width: 100%; height: auto; }")

        # Create markdown with DPI and image
        input_file = os.path.join(tmpdir, "test.md")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("""---
css: style.css
dpi: 300
---

# Image Test

![Test Image](test_image.png)
""")

        # Generate PDF with DPI=300
        outputs_300 = parse_markdown(input_file, tmpdir)
        assert len(outputs_300) == 1

        # Generate PDF without DPI
        input_file_no_dpi = os.path.join(tmpdir, "test_no_dpi.md")
        with open(input_file_no_dpi, "w", encoding="utf-8") as f:
            f.write("""---
css: style.css
---

# Image Test

![Test Image](test_image.png)
""")

        outputs_no_dpi = parse_markdown(input_file_no_dpi, tmpdir)
        assert len(outputs_no_dpi) == 1

        # Extract and compare image dimensions using PyMuPDF
        def get_image_dims(pdf_path):
            doc = fitz.open(pdf_path)
            for page in doc:
                images = page.get_images()
                if images:
                    xref = images[0][0]
                    img_dict = doc.extract_image(xref)
                    doc.close()
                    return img_dict['width'], img_dict['height']
            doc.close()
            return None, None

        width_300, height_300 = get_image_dims(outputs_300[0])
        width_no_dpi, height_no_dpi = get_image_dims(outputs_no_dpi[0])

        # Image with DPI=300 should be downsampled compared to no-DPI version
        if width_300 and width_no_dpi:
            assert width_300 < width_no_dpi
            assert height_300 < height_no_dpi
