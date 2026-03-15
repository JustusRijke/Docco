"""Integration test: TOC stage produces a functional table of contents in the PDF."""

import fitz

from docco.context import Context
from docco.plugins.html import Stage as HtmlStage
from docco.plugins.pdf import Stage as PdfStage
from docco.plugins.toc import Stage as TocStage

MD = "# Introduction\n\n## Section One\n\nHello.\n\n<!-- toc -->\n"


def _render_toc_pdf(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text(MD, encoding="utf-8")
    config = {}
    ctx = Context.from_file(md, tmp_path / "out", config)
    ctx = HtmlStage().process(ctx)
    ctx = TocStage().process(ctx)
    return PdfStage().process(ctx)


def test_toc_headings_numbered(tmp_path):
    result = _render_toc_pdf(tmp_path)
    doc = fitz.open(stream=result.content, filetype="pdf")
    text = "".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    assert "1 Introduction" in text
    assert "1.1 Section One" in text


def test_toc_nav_list_present(tmp_path):
    result = _render_toc_pdf(tmp_path)
    doc = fitz.open(stream=result.content, filetype="pdf")
    text = "".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    assert "Introduction" in text
    assert "Section One" in text
