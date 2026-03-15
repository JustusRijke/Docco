import logging
from copy import deepcopy
from pathlib import Path
from typing import cast

import polib
import pytest

from docco.context import ContentType, Context
from docco.plugins.translation import (
    FilterStage,
    Stage,
    _apply_po,
    _check_sync,
    _clean_po,
    _extract_pot,
    _merge_po,
    _po_stats,
    _strip_covered_msgids,
    _strip_pot,
)

HTML = "<html><body><h1>Hello</h1><p>World</p></body></html>"

BASE_CONFIG: dict = {
    "translation": {
        "languages": ["de"],
        "base_language": "en",
    },
}


def _make_md_context(tmp_path, content="# Hello\n\nWorld\n", config=None):
    src = tmp_path / "doc.md"
    src.write_text(content, encoding="utf-8")
    cfg = deepcopy(BASE_CONFIG) if config is None else deepcopy(config)
    return Context.from_file(src, tmp_path / "out", cfg)


def _make_html_context(
    tmp_path, html=HTML, config=None, langcode=None, original_stem="doc"
):
    src = tmp_path / "doc.md"
    src.write_text("# Hello\n", encoding="utf-8")
    cfg = deepcopy(config or BASE_CONFIG)
    ctx = Context(
        source_path=src,
        output_dir=tmp_path / "out",
        config=cfg,
        content=html,
        content_type=ContentType.HTML,
    )
    if langcode:
        ctx.artifacts["translation_langcode"] = langcode
        ctx.artifacts["translation_original_stem"] = original_stem
    return ctx


def _make_po(path: Path, translations: dict[str, str]) -> None:
    pf = polib.POFile()
    pf.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    for msgid, msgstr in translations.items():
        entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
        pf.append(entry)
    pf.save(str(path))


# --- Unit tests for helpers ---


def test_extract_pot(tmp_path):
    pot_path = tmp_path / "doc.pot"
    _extract_pot(HTML, pot_path, "doc")
    assert pot_path.exists()
    content = pot_path.read_text(encoding="utf-8")
    assert "Hello" in content
    assert "World" in content


def test_strip_covered_msgids_warns_when_no_translated_entries(tmp_path, caplog):
    pot_path = tmp_path / "doc.pot"
    _extract_pot(HTML, pot_path, "doc")
    lib_po = tmp_path / "empty.po"
    _make_po(lib_po, {})  # no translated entries
    with caplog.at_level(logging.WARNING):
        _strip_covered_msgids(pot_path, [lib_po])
    assert "empty.po" in caplog.text
    # POT should be unchanged
    content = pot_path.read_text(encoding="utf-8")
    assert "Hello" in content


def test_strip_pot_removes_stem(tmp_path):
    pot_path = tmp_path / "doc.pot"
    _extract_pot(HTML, pot_path, "doc")
    _strip_pot(pot_path, "Hello", ignore_numbers=False)
    content = pot_path.read_text(encoding="utf-8")
    assert "Hello" not in content
    assert "World" in content


def test_strip_pot_removes_numbers(tmp_path):
    pot_path = tmp_path / "doc.pot"
    html = "<html><body><p>42</p><p>3.14</p><p>Hello</p></body></html>"
    _extract_pot(html, pot_path, "doc")
    _strip_pot(pot_path, "nostem", ignore_numbers=True)
    content = pot_path.read_text(encoding="utf-8")
    assert '"42"' not in content
    assert '"3.14"' in content  # floats kept: decimal separator varies by locale
    assert "Hello" in content


def test_strip_pot_keeps_numbers_when_disabled(tmp_path):
    pot_path = tmp_path / "doc.pot"
    html = "<html><body><p>42</p><p>Hello</p></body></html>"
    _extract_pot(html, pot_path, "doc")
    _strip_pot(pot_path, "nostem", ignore_numbers=False)
    content = pot_path.read_text(encoding="utf-8")
    assert '"42"' in content


def test_clean_po(tmp_path):
    po_path = tmp_path / "test.po"
    pf = polib.POFile()
    pf.metadata = {"X-Generator": "test", "Content-Type": "text/plain; charset=UTF-8"}
    entry = polib.POEntry(msgid="Hello", msgstr="Hallo", occurrences=[("foo.html", 1)])
    pf.append(entry)
    pf.save(str(po_path))
    _clean_po(po_path)
    pf2 = polib.pofile(str(po_path))
    assert "X-Generator" not in pf2.metadata
    assert pf2[0].occurrences == []


def test_merge_po(tmp_path):
    po1 = tmp_path / "lib.po"
    po2 = tmp_path / "doc.po"
    _make_po(po1, {"Hello": "Hallo (lib)", "Bye": "Tschuss"})
    _make_po(po2, {"Hello": "Hallo (doc)"})
    merged = tmp_path / "merged.po"
    _merge_po([po1, po2], merged)
    pf = polib.pofile(str(merged))
    entries = {e.msgid: e.msgstr for e in pf}
    assert entries["Hello"] == "Hallo (doc)"
    assert entries["Bye"] == "Tschuss"


def test_check_sync_in_sync(tmp_path):
    pot = tmp_path / "doc.pot"
    po = tmp_path / "doc_DE.po"
    _extract_pot(HTML, pot, "doc")
    pf = polib.pofile(str(pot))
    pf2 = polib.POFile()
    pf2.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    for e in pf.translated_entries() or pf.untranslated_entries():
        pf2.append(polib.POEntry(msgid=e.msgid, msgstr="x"))
    pf2.save(str(po))
    assert _check_sync(pot, po) is True


def test_check_sync_out_of_sync(tmp_path):
    pot = tmp_path / "doc.pot"
    po = tmp_path / "doc_DE.po"
    _extract_pot(HTML, pot, "doc")
    _make_po(po, {"OldString": "Alter Text"})
    assert _check_sync(pot, po) is False


def test_po_stats(tmp_path):
    po_path = tmp_path / "test.po"
    pf = polib.POFile()
    pf.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    pf.append(polib.POEntry(msgid="A", msgstr="X"))
    pf.append(polib.POEntry(msgid="B", msgstr="Y", flags=["fuzzy"]))
    pf.append(polib.POEntry(msgid="C", msgstr=""))
    pf.save(str(po_path))
    stats = _po_stats(po_path)
    assert stats["translated"] == 1
    assert stats["fuzzy"] == 1
    assert stats["untranslated"] == 1
    assert stats["total"] == 3


def test_apply_po(tmp_path):
    po_path = tmp_path / "de.po"
    _make_po(po_path, {"Hello": "Hallo", "World": "Welt"})
    result = _apply_po(HTML, po_path)
    assert "Hallo" in result
    assert "Welt" in result


# --- FilterStage tests ---


FILTER_CONTENT = (
    "<!-- filter:en -->English<!-- /filter --><!-- filter:de -->German<!-- /filter -->"
)


def test_filter_single_language(tmp_path):
    ctx = _make_md_context(
        tmp_path, FILTER_CONTENT, config={"translation": {"language": "en"}}
    )
    result = FilterStage().process(ctx)
    assert isinstance(result, Context)
    assert "English" in result.str_content
    assert "German" not in result.str_content


def test_filter_single_language_case_insensitive(tmp_path):
    ctx = _make_md_context(
        tmp_path,
        "<!-- filter:EN -->Yes<!-- /filter -->",
        config={"translation": {"language": "en"}},
    )
    result = FilterStage().process(ctx)
    assert isinstance(result, Context)
    assert "Yes" in result.str_content


def test_filter_no_config_passthrough(tmp_path):
    ctx = _make_md_context(tmp_path, FILTER_CONTENT, config={})
    result = FilterStage().process(ctx)
    assert isinstance(result, Context)
    assert result.content == FILTER_CONTENT


def _filter_results(tmp_path, content=FILTER_CONTENT, config=None) -> list[Context]:
    ctx = _make_md_context(tmp_path, content, config=config)
    return cast(list[Context], FilterStage().process(ctx))


def test_filter_multi_language_forks(tmp_path):
    results = _filter_results(tmp_path)
    assert len(results) == 2
    stems = {r.source_path.stem for r in results}
    assert "doc_EN" in stems
    assert "doc_DE" in stems


def test_filter_multi_language_content_filtered(tmp_path):
    results = _filter_results(tmp_path)
    en = next(r for r in results if "EN" in r.source_path.stem)
    de = next(r for r in results if "DE" in r.source_path.stem)
    assert "English" in en.str_content
    assert "German" not in en.str_content
    assert "German" in de.str_content
    assert "English" not in de.str_content


def test_filter_stores_langcode_in_artifacts(tmp_path):
    results = _filter_results(tmp_path)
    codes = {r.artifacts["translation_langcode"] for r in results}
    assert codes == {"en", "de"}


def test_filter_stores_original_stem_in_artifacts(tmp_path):
    results = _filter_results(tmp_path)
    for r in results:
        assert r.artifacts["translation_original_stem"] == "doc"


def test_filter_custom_filename_template(tmp_path):
    config = deepcopy(BASE_CONFIG)
    config["translation"]["filename_template"] = "{langcode}_{filename}"
    results = _filter_results(tmp_path, config=config)
    stems = {r.source_path.stem for r in results}
    assert "EN_doc" in stems
    assert "DE_doc" in stems


def test_filter_missing_base_language_raises(tmp_path):
    ctx = _make_md_context(tmp_path, config={"translation": {"languages": ["de"]}})
    with pytest.raises(ValueError, match="base_language"):
        FilterStage().process(ctx)


def test_filter_missing_languages_raises(tmp_path):
    ctx = _make_md_context(tmp_path, config={"translation": {"base_language": "en"}})
    with pytest.raises(ValueError, match="base_language"):
        FilterStage().process(ctx)


# --- Stage (ENRICH) tests ---


def test_stage_passthrough_no_langcode(tmp_path):
    """No translation_langcode in artifacts -> passthrough."""
    ctx = _make_html_context(tmp_path)
    result = Stage().process(ctx)
    assert isinstance(result, Context)
    assert result.content == HTML


def test_stage_base_language_extracts_pot(tmp_path):
    ctx = _make_html_context(tmp_path, langcode="en")
    Stage().process(ctx)
    assert (tmp_path / "doc.pot").exists()


def test_stage_base_language_passthrough(tmp_path):
    ctx = _make_html_context(tmp_path, langcode="en")
    result = Stage().process(ctx)
    assert result.content == HTML


def test_stage_applies_translation(tmp_path):
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo", "World": "Welt"})
    ctx = _make_html_context(tmp_path, langcode="de")
    result = Stage().process(ctx)
    assert "Hallo" in result.str_content
    assert "Welt" in result.str_content


def test_stage_missing_po_raises(tmp_path):
    ctx = _make_html_context(tmp_path, langcode="de")
    with pytest.raises(FileNotFoundError, match="PO file missing"):
        Stage().process(ctx)


def test_stage_out_of_sync_warns(tmp_path, caplog):
    _make_po(tmp_path / "doc_DE.po", {"OldString": "Alter Text"})
    ctx = _make_html_context(tmp_path, langcode="de")
    with caplog.at_level(logging.WARNING, logger="docco.plugins.translation"):
        Stage().process(ctx)
    assert any("sync" in r.message.lower() for r in caplog.records)


def test_stage_fuzzy_warns(tmp_path, caplog):
    pf = polib.POFile()
    pf.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    pf.append(polib.POEntry(msgid="Hello", msgstr="Hallo", flags=["fuzzy"]))
    pf.append(polib.POEntry(msgid="World", msgstr="Welt"))
    pf.save(str(tmp_path / "doc_DE.po"))
    ctx = _make_html_context(tmp_path, langcode="de")
    with caplog.at_level(logging.WARNING, logger="docco.plugins.translation"):
        Stage().process(ctx)
    assert any("fuzzy" in r.message.lower() for r in caplog.records)


def test_stage_untranslated_warns(tmp_path, caplog):
    """Untranslated strings after merging all PO files produce a warning."""
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo", "World": ""})
    ctx = _make_html_context(tmp_path, langcode="de")
    with caplog.at_level(logging.WARNING, logger="docco.plugins.translation"):
        Stage().process(ctx)
    assert any("untranslated" in r.message.lower() for r in caplog.records)


def test_stage_untranslated_covered_by_extra_po_no_warn(tmp_path, caplog):
    """No warning when a second PO file covers the untranslated strings."""
    extra_po = tmp_path / "copyright_de.po"
    _make_po(extra_po, {"World": "Welt"})
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo"})
    config = deepcopy(BASE_CONFIG)
    config["translation"]["po"] = {"de": [str(extra_po)]}
    ctx = _make_html_context(tmp_path, config=config, langcode="de")
    with caplog.at_level(logging.WARNING, logger="docco.plugins.translation"):
        Stage().process(ctx)
    assert not any("untranslated" in r.message.lower() for r in caplog.records)


def test_stage_extra_po_merged_with_doc(tmp_path):
    """[translation.po] entries are extra files merged with the auto-named doc PO."""
    extra_po = tmp_path / "copyright_de.po"
    _make_po(extra_po, {"World": "Welt"})
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo"})
    config = deepcopy(BASE_CONFIG)
    config["translation"]["po"] = {"de": str(extra_po)}
    ctx = _make_html_context(tmp_path, config=config, langcode="de")
    result = Stage().process(ctx)
    assert "Hallo" in result.str_content
    assert "Welt" in result.str_content


def test_stage_with_terms(tmp_path):
    lib_po = tmp_path / "lib.po"
    _make_po(lib_po, {"World": "Welt (lib)"})
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo"})
    config = deepcopy(BASE_CONFIG)
    config["translation"]["terms"] = [str(lib_po)]
    ctx = _make_html_context(tmp_path, config=config, langcode="de")
    result = Stage().process(ctx)
    assert "Hallo" in result.str_content
    assert "Welt" in result.str_content


def test_stage_terms_relative_to_source(tmp_path, monkeypatch):
    """terms relative paths resolve from source_path.parent, not cwd."""
    docs = tmp_path / "docs"
    docs.mkdir()
    lib_po = docs / "lib.po"
    _make_po(lib_po, {"World": "Welt (lib)"})
    _make_po(docs / "doc_DE.po", {"Hello": "Hallo"})

    config = deepcopy(BASE_CONFIG)
    config["translation"]["terms"] = ["lib.po"]
    src = docs / "doc.md"
    src.write_text("# Hello\n", encoding="utf-8")
    ctx = Context(
        source_path=src,
        output_dir=tmp_path / "out",
        config=config,
        content=HTML,
        content_type=ContentType.HTML,
    )
    ctx.artifacts["translation_langcode"] = "de"
    ctx.artifacts["translation_original_stem"] = "doc"

    monkeypatch.chdir(tmp_path)  # cwd differs from source_path.parent
    result = Stage().process(ctx)
    assert "Hallo" in result.str_content
    assert "Welt" in result.str_content


def test_stage_multiple_extra_po_files_merged(tmp_path):
    """Multiple [translation.po] extras are all merged with the doc PO."""
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo"})
    _make_po(tmp_path / "copyright_de.po", {"World": "Welt"})
    config = deepcopy(BASE_CONFIG)
    config["translation"]["po"] = {"de": ["copyright_de.po"]}
    ctx = _make_html_context(tmp_path, config=config, langcode="de")
    result = Stage().process(ctx)
    assert "Hallo" in result.str_content
    assert "Welt" in result.str_content


def test_stage_pot_per_language(tmp_path):
    """Each language gets its own POT file."""
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo", "World": "Welt"})
    ctx = _make_html_context(tmp_path, langcode="de")
    Stage().process(ctx)
    assert (tmp_path / "doc_DE.pot").exists()


def test_stage_stem_stripped_from_pot(tmp_path):
    """Filename stem is always stripped from POT."""
    _make_po(tmp_path / "doc_DE.po", {"Hello": "Hallo"})
    ctx = _make_html_context(tmp_path, langcode="de")
    Stage().process(ctx)
    pot = (tmp_path / "doc_DE.pot").read_text(encoding="utf-8")
    assert "doc" not in pot


def test_unknown_translation_config_key():
    with pytest.raises(ValueError, match=r"\[translation\] unknown config key"):
        FilterStage().validate_config({"translation": {"bogus_key": True}})
