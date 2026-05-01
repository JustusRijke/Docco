# Edge-case tests only. The happy path (multi-language, terms, extra POs, diffpdf)
# is covered by tests_regression.py. Only keep tests for code paths not exercised there.

import logging
from pathlib import Path

import polib
import pytest

from docco.context import ContentType, Context
from docco.plugins.translation import FilterStage, Stage, _strip_covered_msgids

HTML = "<html><body><h1>Hello</h1><p>World</p></body></html>"
BASE_CONFIG: dict = {"translation": {"languages": ["de"], "base_language": "en"}}


def _ctx(tmp_path, config=BASE_CONFIG, langcode=None, config_dir=None):
    src = tmp_path / "doc.md"
    src.write_text("# Hello\n", encoding="utf-8")
    ctx = Context(
        source_path=src,
        output_dir=tmp_path / "out",
        config=dict(config),
        content=HTML,
        content_type=ContentType.HTML,
        config_dir=config_dir or tmp_path,
    )
    if langcode:
        ctx.artifacts["translation_langcode"] = langcode
        ctx.artifacts["translation_original_stem"] = "doc"
    return ctx


def _po(
    path: Path, entries: dict[str, str], flags: dict[str, list] | None = None
) -> None:
    pf = polib.POFile()
    pf.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    for msgid, msgstr in entries.items():
        pf.append(
            polib.POEntry(
                msgid=msgid, msgstr=msgstr, flags=(flags or {}).get(msgid, [])
            )
        )
    pf.save(str(path))


def test_strip_covered_no_terms(tmp_path):
    _strip_covered_msgids(tmp_path / "x.pot", [])


def test_strip_covered_empty_po_warns(tmp_path, caplog):
    from docco.plugins.translation import _extract_pot

    pot = tmp_path / "doc.pot"
    _extract_pot(HTML, pot, "doc")
    lib = tmp_path / "empty.po"
    _po(lib, {})
    with caplog.at_level(logging.WARNING):
        _strip_covered_msgids(pot, [lib])
    assert "empty.po" in caplog.text


def test_filter_passthrough_no_config(tmp_path):
    ctx = _ctx(tmp_path, config={})
    ctx.content_type = ContentType.MARKDOWN
    ctx.content = ""
    assert FilterStage().process(ctx) is ctx


def test_filter_single_language(tmp_path):
    ctx = _ctx(tmp_path, config={"translation": {"language": "en"}})
    ctx.content_type = ContentType.MARKDOWN
    ctx.content = (
        "<!-- filter:en -->Yes<!-- /filter --><!-- filter:de -->No<!-- /filter -->"
    )
    result = FilterStage().process(ctx)
    assert isinstance(result, Context)
    assert "Yes" in result.str_content
    assert "No" not in result.str_content


def test_filter_missing_base_language_raises(tmp_path):
    ctx = _ctx(tmp_path, config={"translation": {"languages": ["de"]}})
    ctx.content_type = ContentType.MARKDOWN
    with pytest.raises(ValueError, match="base_language"):
        FilterStage().process(ctx)


def test_filter_unknown_config_key_raises():
    with pytest.raises(ValueError, match=r"\[translation\] unknown config key"):
        FilterStage().validate_config({"translation": {"bogus": True}})


def test_stage_passthrough_no_langcode(tmp_path):
    assert Stage().process(_ctx(tmp_path)).content == HTML


def test_stage_missing_po_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="PO file missing"):
        Stage().process(_ctx(tmp_path, langcode="de"))


def test_stage_missing_extra_po_raises(tmp_path):
    _po(tmp_path / "doc_DE.po", {"Hello": "Hallo"})
    config = {
        "translation": {
            "languages": ["de"],
            "base_language": "en",
            "po": {"de": "missing.po"},
        }
    }
    with pytest.raises(FileNotFoundError, match="missing.po"):
        Stage().process(_ctx(tmp_path, config=config, langcode="de"))


def test_stage_extra_po_resolved_relative_to_config_dir(tmp_path):
    # config_dir differs from source dir; extra PO lives in config_dir
    config_dir = tmp_path / "cfg"
    config_dir.mkdir()
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _po(src_dir / "doc_DE.po", {"Hello": "Hallo", "World": "Welt"})
    _po(config_dir / "extra_de.po", {"Hello": "Hallo"})
    config = {
        "translation": {
            "languages": ["de"],
            "base_language": "en",
            "po": {"de": "extra_de.po"},
        }
    }
    ctx = _ctx(tmp_path, config=config, langcode="de", config_dir=config_dir)
    ctx.source_path = src_dir / "doc_DE.md"
    ctx.source_path.write_text("", encoding="utf-8")
    ctx.artifacts["translation_langcode"] = "de"
    ctx.artifacts["translation_original_stem"] = "doc"
    Stage().process(ctx)  # must not raise FileNotFoundError


def test_parsefile_error_includes_filename(tmp_path):
    from docco.plugins.translation import _parsefile

    bad = tmp_path / "broken.po"
    bad.write_text("garbage\n", encoding="utf-8")
    with pytest.raises(Exception, match="broken.po"):
        _parsefile(bad)


@pytest.mark.parametrize(
    ("entries", "flags", "expected_keyword"),
    [
        ({"OldString": "Alter Text"}, None, "sync"),
        ({"Hello": "Hallo", "World": "Welt"}, {"Hello": ["fuzzy"]}, "fuzzy"),
        ({"Hello": "Hallo", "World": ""}, None, "untranslated"),
    ],
    ids=["out-of-sync", "fuzzy", "untranslated"],
)
def test_stage_warns(tmp_path, caplog, entries, flags, expected_keyword):
    _po(tmp_path / "doc_DE.po", entries, flags=flags)
    with caplog.at_level(logging.WARNING, logger="docco.plugins.translation"):
        Stage().process(_ctx(tmp_path, langcode="de"))
    assert any(expected_keyword in r.message.lower() for r in caplog.records)


def test_stage_single_po_no_merge(tmp_path):
    _po(tmp_path / "doc_DE.po", {"Hello": "Hallo", "World": "Welt"})
    assert "Hallo" in Stage().process(_ctx(tmp_path, langcode="de")).str_content


@pytest.mark.parametrize(
    "date",
    ["01-02-2011", "1-2-2013", "2013-04-04", "01/03/04", "2024.12.31"],
)
def test_strip_pot_ignore_dates(tmp_path, date):
    from docco.plugins.translation import (
        _build_ignore_pattern,
        _extract_pot,
        _strip_pot,
    )

    html = f"<html><body><p>{date}</p></body></html>"
    pot = tmp_path / "doc.pot"
    _extract_pot(html, pot, "doc")
    _strip_pot(
        pot,
        "doc",
        _build_ignore_pattern(
            {"ignore_numbers": False, "ignore_dates": True, "ignore_chars": False}
        ),
    )
    assert all(e.msgid != date for e in polib.pofile(str(pot)))


@pytest.mark.parametrize("char", ["a", "?", "!", ".", " "])
def test_strip_pot_ignore_chars(tmp_path, char):
    from docco.plugins.translation import (
        _build_ignore_pattern,
        _extract_pot,
        _strip_pot,
    )

    html = f"<html><body><p>{char}</p><p>Hello</p></body></html>"
    pot = tmp_path / "doc.pot"
    _extract_pot(html, pot, "doc")
    _strip_pot(
        pot,
        "doc",
        _build_ignore_pattern(
            {"ignore_numbers": False, "ignore_dates": False, "ignore_chars": True}
        ),
    )
    msgids = [e.msgid for e in polib.pofile(str(pot))]
    assert char not in msgids
    assert "Hello" in msgids


def test_strip_pot_ignore_regex(tmp_path):
    from docco.plugins.translation import (
        _build_ignore_pattern,
        _extract_pot,
        _strip_pot,
    )

    html = "<html><body><p>98 x 6,5</p><p>foobar 98 x 6,5</p><p>Hello</p></body></html>"
    pot = tmp_path / "doc.pot"
    _extract_pot(html, pot, "doc")
    _strip_pot(
        pot,
        "doc",
        _build_ignore_pattern(
            {
                "ignore_numbers": False,
                "ignore_dates": False,
                "ignore_chars": False,
                "ignore_regex": r"^\d[\d,.]* x \d[\d,.]*$",
            }
        ),
    )
    msgids = [e.msgid for e in polib.pofile(str(pot))]
    assert "98 x 6,5" not in msgids
    assert "foobar 98 x 6,5" in msgids
    assert "Hello" in msgids
