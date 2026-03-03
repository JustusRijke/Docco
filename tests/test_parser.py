"""Integration tests for the parser module."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import fitz  # PyMuPDF
import pytest
from PIL import Image

from docco.logging_config import redirect_to_debug
from docco.parser import (
    MAX_ITERATIONS,
    BuildConfig,
    apply_variables,
    parse_markdown,
    preprocess_document,
    process_directives_iteratively,
    process_filter_directives,
)


@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return str(Path(__file__).parent / "fixtures")


def test_end_to_end_simple(fixture_dir):
    """Test simple markdown parsing and PDF output."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs, _ = parse_markdown(input_file, Path(tmpdir))
        assert len(outputs) == 1
        assert outputs[0].name.endswith(".pdf")
        assert outputs[0].exists()


def test_end_to_end_with_frontmatter(fixture_dir):
    """Test parsing with frontmatter."""
    input_file = Path(fixture_dir) / "with_frontmatter.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs, _ = parse_markdown(input_file, Path(tmpdir))
        assert len(outputs) == 1
        assert outputs[0].name.endswith(".pdf")
        assert outputs[0].exists()


def test_end_to_end_with_inline(fixture_dir):
    """Test parsing with inline directives."""
    # Create a temp file with inline
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "with_inline.md"
        # Copy inline target to tmpdir so it's relative to the markdown file
        inline_target = str(Path(tmpdir) / "inline_target.md")
        with Path(inline_target).open("w", encoding="utf-8") as f:
            f.write("Inlined: {{name}}")

        with Path(input_file).open("w", encoding="utf-8") as f:
            f.write("""# Document

Before

<!-- inline:"inline_target.md" name="Test" -->

After""")

        outputs, _ = parse_markdown(input_file, Path(tmpdir))
        assert len(outputs) == 1
        assert outputs[0].name.endswith(".pdf")
        assert outputs[0].exists()


def test_output_file_naming_simple(fixture_dir):
    """Test that output files are named correctly for simple docs."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs, _ = parse_markdown(input_file, Path(tmpdir))
        basename = outputs[0].name
        assert basename == "simple.pdf"


def test_keep_intermediate_false(fixture_dir):
    """Test that intermediate files are removed by default."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(keep_intermediate=False)
        )
        # Should only have PDF files
        all_files = [f.name for f in Path(tmpdir).iterdir()]
        assert any(f.endswith(".pdf") for f in all_files)
        assert not any(f.endswith("_intermediate.md") for f in all_files)
        assert not any(f.endswith(".html") for f in all_files)


def test_keep_intermediate_true(fixture_dir):
    """Test that intermediate files are kept when flag is True."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(keep_intermediate=True)
        )
        all_files = [f.name for f in Path(tmpdir).iterdir()]
        # Should have PDF, HTML, and intermediate MD files
        assert any(f.endswith(".pdf") for f in all_files)
        assert any(f.endswith("_intermediate.md") for f in all_files)
        assert any(f.endswith(".html") for f in all_files)


def test_skip_identical_skips_when_unchanged(fixture_dir):
    """skip_identical=True keeps existing PDF when content is visually identical."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        # First build
        outputs, _ = parse_markdown(input_file, out, config=BuildConfig())
        pdf_path = outputs[0]
        mtime_before = pdf_path.stat().st_mtime

        # Second build with skip_identical — diffpdf returns True (identical)
        with patch("docco.parser.diffpdf", return_value=True) as mock_diff:
            outputs2, skipped = parse_markdown(
                input_file, out, config=BuildConfig(skip_identical=True)
            )
            mock_diff.assert_called_once()

        assert outputs2[0] == pdf_path
        assert pdf_path.stat().st_mtime == mtime_before
        assert skipped == 1


def test_skip_identical_overwrites_when_changed(fixture_dir):
    """skip_identical=True replaces PDF when content differs."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        # First build
        outputs, _ = parse_markdown(input_file, out, config=BuildConfig())
        pdf_path = outputs[0]
        mtime_before = pdf_path.stat().st_mtime

        # Second build with skip_identical — diffpdf returns False (changed)
        with patch("docco.parser.diffpdf", return_value=False):
            outputs2, skipped = parse_markdown(
                input_file, out, config=BuildConfig(skip_identical=True)
            )

        assert outputs2[0] == pdf_path
        assert pdf_path.exists()
        assert pdf_path.stat().st_mtime > mtime_before
        assert skipped == 0


def test_skip_identical_false_always_overwrites(fixture_dir):
    """skip_identical=False (default) always overwrites the PDF."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        parse_markdown(input_file, out, config=BuildConfig())
        pdf_path = out / "simple.pdf"
        mtime_before = pdf_path.stat().st_mtime

        with patch("docco.parser.diffpdf") as mock_diff:
            parse_markdown(input_file, out, config=BuildConfig(skip_identical=False))
            mock_diff.assert_not_called()

        assert pdf_path.stat().st_mtime > mtime_before


def test_skip_identical_no_existing_pdf(fixture_dir):
    """skip_identical=True generates PDF normally when no existing PDF."""
    input_file = Path(fixture_dir) / "simple.md"
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        with patch("docco.parser.diffpdf") as mock_diff:
            outputs, _ = parse_markdown(
                input_file, out, config=BuildConfig(skip_identical=True)
            )
            mock_diff.assert_not_called()

        assert outputs[0].exists()


def test_redirect_to_debug_restores_root_logger():
    """redirect_to_debug restores root logger level and handlers after exit."""
    root = logging.getLogger()
    dummy = logging.NullHandler()
    root.addHandler(dummy)
    saved_level = root.level
    saved_handler_count = len(root.handlers)

    def _corrupt_root():
        # Simulate what diffpdf.logger.setup_logging does
        root.setLevel(logging.WARNING)
        root.addHandler(logging.NullHandler())

    with redirect_to_debug():
        _corrupt_root()

    assert root.level == saved_level
    assert len(root.handlers) == saved_handler_count

    root.removeHandler(dummy)


def test_redirect_to_debug_demotes_error_to_debug():
    """redirect_to_debug prevents ERROR records from reaching handlers at ERROR level."""
    emitted: list[tuple[int, str]] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            emitted.append((record.levelno, record.getMessage()))

    root = logging.getLogger()
    capture = _Capture()
    root.addHandler(capture)
    root.setLevel(logging.DEBUG)

    with redirect_to_debug():
        logging.getLogger().error("diffpdf error output")

    root.removeHandler(capture)

    assert len(emitted) == 1
    assert emitted[0][0] == logging.DEBUG
    assert "diffpdf error output" in emitted[0][1]


def test_max_iterations_exceeded_self_referencing():
    """Test that ValueError is raised when inline creates infinite recursion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a markdown file that references itself
        self_ref_file = str(Path(tmpdir) / "self_ref.md")
        with Path(self_ref_file).open("w", encoding="utf-8") as f:
            f.write('# Self Reference\n<!-- inline:"self_ref.md" -->')

        # Create content that inlines the self-referencing file
        content = '# Main\n<!-- inline:"self_ref.md" -->'

        with pytest.raises(
            ValueError, match=f"Max iterations \\({MAX_ITERATIONS}\\) exceeded"
        ):
            process_directives_iteratively(content, Path(tmpdir), False)


def test_multilingual_build_logs_translation_warnings(caplog):
    """Test that incomplete translations trigger warnings in multilingual mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        translations_dir = Path(tmpdir) / "test"
        translations_dir.mkdir(exist_ok=True, parents=True)
        de_po = translations_dir / "de.po"

        input_file = Path(tmpdir) / "test.md"
        with input_file.open("w", encoding="utf-8") as f:
            f.write("""---
base_language: en
translations:
  de: test/de.po
---

# Hello

This is a test document.
""")

        # Create PO file with incomplete translation (fuzzy)
        # Note: When multilingual mode runs, it auto-updates the PO file,
        # so we need to create a PO file that will result in fuzzy/untranslated
        # entries after being merged with the actual POT content
        with de_po.open("w", encoding="utf-8") as f:
            f.write("""# German translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

#, fuzzy
msgid "<h1>Hello</h1>"
msgstr "<h1>Hallo</h1>"
""")

        # Build multilingual PDF
        outputs, _ = parse_markdown(input_file, Path(tmpdir))

        # Should generate PDFs for EN and DE
        assert len(outputs) == 2

        # Should have logged warning about incomplete translation
        # After auto-update, the PO file will have fuzzy and/or untranslated strings
        assert "Translation incomplete for DE" in caplog.text


def test_multilingual_po_sync_warning(caplog):
    """Test that out-of-sync PO files trigger sync warnings in multilingual mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        translations_dir = Path(tmpdir) / "test"
        translations_dir.mkdir(exist_ok=True, parents=True)
        de_po = translations_dir / "de.po"

        input_file = Path(tmpdir) / "test.md"
        with input_file.open("w", encoding="utf-8") as f:
            f.write("""---
base_language: en
translations:
  de: test/de.po
---

# New Content

This has changed.
""")

        # Create a PO file with old content that won't match new POT
        with de_po.open("w", encoding="utf-8") as f:
            f.write("""# German translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "<h1>Old Content</h1>"
msgstr "<h1>Alter Inhalt</h1>"
""")

        with patch("subprocess.run"):
            # Build multilingual PDF
            parse_markdown(input_file, Path(tmpdir))

            # Should have logged warning about out-of-sync PO file
            assert (
                "out of sync for DE" in caplog.text or "Failed to update" in caplog.text
            )


def test_multilingual_missing_base_language():
    """Test that multilingual mode requires base_language in frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        de_po = Path(tmpdir) / "de.po"
        de_po.write_text('msgid ""\nmsgstr ""\n', encoding="utf-8")

        input_file = Path(tmpdir) / "test.md"
        with input_file.open("w", encoding="utf-8") as f:
            f.write("""---
translations:
  de: de.po
---

# Test Document

This should fail.
""")

        # Should raise ValueError
        with pytest.raises(
            ValueError, match="Multilingual mode requires 'base_language'"
        ):
            parse_markdown(input_file, Path(tmpdir))


def test_dpi_parameter(fixture_dir):
    """Test that DPI parameter is passed through and used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test_dpi.md"
        with Path(input_file).open("w", encoding="utf-8") as f:
            f.write("""# Test Document

This document has a DPI setting.
""")

        outputs, _ = parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(dpi=300)
        )
        assert len(outputs) == 1
        assert outputs[0].exists()
        assert outputs[0].name.endswith("test_dpi.pdf")


def test_dpi_with_image():
    """Test DPI parameter with actual image downsampling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a high-resolution test image
        img = Image.new("RGB", (3000, 2000), color="red")
        img_path = str(Path(tmpdir) / "test_image.png")
        img.save(img_path, dpi=(600, 600))

        # Create CSS file with image sizing
        css_path = str(Path(tmpdir) / "style.css")
        with Path(css_path).open("w", encoding="utf-8") as f:
            f.write("img { max-width: 100%; height: auto; }")

        # Create markdown with image
        input_file = Path(tmpdir) / "test.md"
        with Path(input_file).open("w", encoding="utf-8") as f:
            f.write("""---
css: style.css
---

# Image Test

![Test Image](test_image.png)
""")

        # Generate PDF with DPI=300
        outputs_300, _ = parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(dpi=300)
        )
        assert len(outputs_300) == 1

        # Generate PDF without DPI
        input_file_no_dpi = Path(tmpdir) / "test_no_dpi.md"
        with input_file_no_dpi.open("w", encoding="utf-8") as f:
            f.write("""---
css: style.css
---

# Image Test

![Test Image](test_image.png)
""")

        outputs_no_dpi, _ = parse_markdown(input_file_no_dpi, Path(tmpdir))
        assert len(outputs_no_dpi) == 1

        # Extract and compare image dimensions using PyMuPDF
        def get_image_dims(pdf_path):
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    images = page.get_images()
                    if images:  # pragma: no branch
                        xref = images[0][0]
                        img_dict = doc.extract_image(xref)
                        return img_dict["width"], img_dict["height"]
            raise AssertionError("No images found in PDF")  # pragma: no cover

        width_300, height_300 = get_image_dims(outputs_300[0])
        width_no_dpi, height_no_dpi = get_image_dims(outputs_no_dpi[0])

        # Image with DPI=300 should be downsampled compared to no-DPI version
        assert width_300 < width_no_dpi
        assert height_300 < height_no_dpi


def test_dpi_validation_warns_on_low_dpi_images(caplog):
    """Test that low DPI images trigger warnings when DPI is set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small low-resolution image
        img = Image.new("RGB", (100, 100), color="blue")
        img_path = str(Path(tmpdir) / "lowres.png")
        img.save(img_path)

        # Create markdown with image
        input_file = Path(tmpdir) / "test.md"
        with Path(input_file).open("w", encoding="utf-8") as f:
            f.write("""# Test

![Low res](lowres.png)
""")

        # Generate PDF
        outputs, _ = parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(dpi=300)
        )
        assert len(outputs) == 1

        # Should have warned about low DPI
        assert "below 300 DPI" in caplog.text


def test_dpi_validation_multilingual_base_only(caplog):
    """Test that DPI validation only runs for base language in multilingual mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small low-resolution image
        img = Image.new("RGB", (100, 100), color="green")
        img.save(str(Path(tmpdir) / "lowres.png"))

        translations_dir = Path(tmpdir) / "test"
        translations_dir.mkdir(exist_ok=True, parents=True)
        de_po = translations_dir / "de.po"
        de_po.write_text(
            'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n',
            encoding="utf-8",
        )

        # Create markdown with translations dict
        input_file = Path(tmpdir) / "test.md"
        with input_file.open("w", encoding="utf-8") as f:
            f.write("""---
base_language: en
translations:
  de: test/de.po
---

# Test Document

![Low res](lowres.png)
""")

        # Generate PDFs (EN and DE)
        outputs, _ = parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(dpi=300)
        )
        assert len(outputs) == 2  # EN and DE

        # Should only warn once (for base language EN)
        warning_count = caplog.text.count("below 300 DPI")
        assert warning_count == 1  # Only base language validated


def test_filter_directives_keeps_matching_language():
    """Matching language block is kept with directives stripped."""
    html = "<p>Shared</p>\n<!-- filter: nl -->\n<p>Dutch</p>\n<!-- /filter -->"
    result = process_filter_directives(html, "nl")
    assert "<p>Dutch</p>" in result
    assert "filter" not in result


def test_filter_directives_removes_other_language():
    """Non-matching language block is removed entirely."""
    html = "<!-- filter: de --><p>German</p><!-- /filter --><p>Common</p>"
    result = process_filter_directives(html, "nl")
    assert "<p>German</p>" not in result
    assert "<p>Common</p>" in result


def test_filter_directives_case_insensitive():
    """Language matching is case-insensitive."""
    html = "<!-- filter: NL --><p>Dutch</p><!-- /filter -->"
    assert "<p>Dutch</p>" in process_filter_directives(html, "nl")
    assert "<p>Dutch</p>" in process_filter_directives(html, "NL")
    assert "<p>Dutch</p>" in process_filter_directives(html, "Nl")


def test_filter_directives_multiple_blocks():
    """Multiple filter blocks: only matching language kept."""
    html = (
        "<!-- filter: en --><p>English</p><!-- /filter -->"
        "<!-- filter: de --><p>German</p><!-- /filter -->"
        "<!-- filter: nl --><p>Dutch</p><!-- /filter -->"
    )
    result = process_filter_directives(html, "de")
    assert "<p>German</p>" in result
    assert "<p>English</p>" not in result
    assert "<p>Dutch</p>" not in result


def test_filter_applied_in_multilingual_pdf():
    """Filter directives are applied per language when generating multilingual PDFs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        translations_dir = Path(tmpdir) / "test"
        translations_dir.mkdir()
        (translations_dir / "de.po").write_text(
            'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n',
            encoding="utf-8",
        )

        input_file = Path(tmpdir) / "test.md"
        input_file.write_text(
            """---
base_language: en
translations:
  de: test/de.po
---

<!-- filter: en -->
English only content.
<!-- /filter -->

<!-- filter: de -->
German only content.
<!-- /filter -->

Shared content.
""",
            encoding="utf-8",
        )

        outputs, _ = parse_markdown(
            input_file, Path(tmpdir), config=BuildConfig(keep_intermediate=True)
        )
        assert len(outputs) == 2  # EN and DE

        en_html = (Path(tmpdir) / "test_EN.html").read_text(encoding="utf-8")
        de_html = (Path(tmpdir) / "test_DE.html").read_text(encoding="utf-8")

        assert "English only content" in en_html
        assert "German only content" not in en_html
        assert "German only content" in de_html
        assert "English only content" not in de_html
        assert "Shared content" in en_html
        assert "Shared content" in de_html


def test_apply_variables_basic():
    """Variable placeholders are replaced in content."""
    result = apply_variables("Hello $$name$$!", {"name": "world"})
    assert result == "Hello world!"


def test_apply_variables_no_match():
    """Content without placeholders is returned unchanged."""
    result = apply_variables("No placeholders here.", {"name": "world"})
    assert result == "No placeholders here."


def test_apply_variables_multiple():
    """Multiple variables are replaced."""
    result = apply_variables("$$a$$ and $$b$$", {"a": "foo", "b": "bar"})
    assert result == "foo and bar"


def test_apply_variables_escaped():
    """$$$$varname$$$$ is left as $$varname$$ without substitution."""
    result = apply_variables("$$$$name$$$$", {"name": "world"})
    assert result == "$$name$$"


def test_apply_variables_escaped_mixed():
    """Escaped and unescaped placeholders work in the same string."""
    result = apply_variables("$$$$name$$$$ vs $$name$$", {"name": "world"})
    assert result == "$$name$$ vs world"


def test_frontmatter_vars_substituted_in_body():
    """Variables declared in frontmatter are substituted in the document body."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.md"
        input_file.write_text(
            """---
var:
  greeting: hello
---

$$greeting$$ world
""",
            encoding="utf-8",
        )
        metadata, body, _ = preprocess_document(input_file.read_text(), input_file)
        assert "hello world" in body
        assert "$$greeting$$" not in body


def test_frontmatter_vars_not_in_frontmatter():
    """Variable substitution does not affect the frontmatter section itself."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.md"
        input_file.write_text(
            """---
var:
  myvar: replaced
css: $$myvar$$.css
---

content
""",
            encoding="utf-8",
        )
        metadata, body, _ = preprocess_document(input_file.read_text(), input_file)
        # css key should be literal (frontmatter not substituted)
        assert metadata.get("css") == "$$myvar$$.css"


def test_builtin_path_variable():
    """Built-in $$PATH$$ variable resolves to the directory of the input file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.md"
        input_file.write_text("The file is at $$PATH$$\n", encoding="utf-8")
        _, body, _ = preprocess_document(input_file.read_text(), input_file)
        assert str(input_file.resolve().parent) in body
        assert "$$PATH$$" not in body


def test_reserved_var_cannot_be_redeclared(caplog):
    """Declaring PATH in frontmatter var triggers a warning and is ignored."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "test.md"
        input_file.write_text(
            """---
var:
  PATH: /fake/path
---

$$PATH$$
""",
            encoding="utf-8",
        )
        _, body, _ = preprocess_document(input_file.read_text(), input_file)
        assert "reserved" in caplog.text
        # PATH should still be the real dir, not /fake/path
        assert "/fake/path" not in body
        assert str(input_file.resolve().parent) in body


def test_vars_substituted_in_inline_path():
    """Variables in inline directive paths are resolved before the file is opened."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file named "hello_world.md"
        target = Path(tmpdir) / "hello_world.md"
        target.write_text("inlined content\n", encoding="utf-8")

        input_file = Path(tmpdir) / "test.md"
        input_file.write_text(
            """---
var:
  suffix: world
---

<!-- inline:"hello_$$suffix$$.md" -->
""",
            encoding="utf-8",
        )
        _, body, _ = preprocess_document(input_file.read_text(), input_file)
        assert "inlined content" in body


def test_vars_substituted_in_inlined_file_content():
    """Variables are substituted inside inlined file content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "snippet.md"
        target.write_text("Value: $$myval$$\n", encoding="utf-8")

        input_file = Path(tmpdir) / "test.md"
        input_file.write_text(
            """---
var:
  myval: 42
---

<!-- inline:"snippet.md" -->
""",
            encoding="utf-8",
        )
        _, body, _ = preprocess_document(input_file.read_text(), input_file)
        assert "Value: 42" in body
        assert "$$myval$$" not in body


def test_preprocess_non_string_var_key_is_skipped(tmp_path):
    """Non-string variable keys in frontmatter var dict are silently skipped."""
    # YAML always produces string keys so we inject a non-string key via mock
    input_file = tmp_path / "test.md"
    input_file.write_text("# Hello $$name$$", encoding="utf-8")

    with patch("docco.parser.parse_frontmatter") as mock_fm:
        mock_fm.return_value = {"var": {1: "numeric_key", "name": "world"}}
        _, body, _ = preprocess_document(input_file.read_text(), input_file)
    # numeric key is skipped; string key still applied
    assert "world" in body


def test_preprocess_non_dict_var_is_ignored(tmp_path):
    """Non-dict var value in frontmatter is silently ignored."""
    input_file = tmp_path / "test.md"
    input_file.write_text("# Hello $$name$$", encoding="utf-8")

    with patch("docco.parser.parse_frontmatter") as mock_fm:
        mock_fm.return_value = {"var": "not_a_dict"}
        _, body, _ = preprocess_document(input_file.read_text(), input_file)
    # No substitution happened, variable stays unexpanded
    assert "$$name$$" in body


def test_html_to_pdf_exception_cleans_up_temp(tmp_path):
    """Exception during PDF generation removes temp PDF and re-raises."""
    input_file = tmp_path / "test.md"
    input_file.write_text("# Test", encoding="utf-8")

    def _raise_after_creating(html_path, output_path, **kwargs):
        output_path.write_bytes(b"partial")
        raise RuntimeError("pdf failed")

    with patch("docco.parser.html_to_pdf", side_effect=_raise_after_creating):
        with pytest.raises(RuntimeError, match="pdf failed"):
            parse_markdown(input_file, tmp_path)

    # No temp .pdf-docco files left behind
    assert not list(tmp_path.glob("*.pdf-docco"))
