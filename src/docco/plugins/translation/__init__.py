import re
import shutil
import subprocess
from copy import deepcopy
from io import BytesIO
from pathlib import Path

import polib
from translate.convert import html2po, po2html

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage
from docco.utils import tmp_file

_FILTER_RE = re.compile(
    r"<!--\s*filter\s*:\s*(\S+)\s*-->(.*?)<!--\s*/filter\s*-->",
    re.DOTALL,
)


def _apply_filter(content: str, language: str) -> str:
    lang = language.lower()

    def replace_block(m: re.Match) -> str:
        return m.group(2) if m.group(1).strip().lower() == lang else ""

    return _FILTER_RE.sub(replace_block, content)


def _clean_po(po_path: Path) -> None:
    pf = polib.pofile(str(po_path))
    pf.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    for entry in pf:
        entry.occurrences = []
    pf.sort()
    pf.save(str(po_path))


def _extract_pot(html: str, pot_path: Path, source_name: str) -> None:
    stripped = re.sub(r'\s+id="[^"]*"', "", html).encode("utf-8")
    buf = BytesIO(stripped)
    buf.name = source_name
    with pot_path.open("wb") as f:
        html2po.converthtml(buf, f, None, pot=True, duplicatestyle="merge")
    _clean_po(pot_path)
    log.debug("Extracted POT: %s", pot_path)


def _merge_po(po_paths: list[Path], output_path: Path) -> None:
    merged = polib.POFile()
    merged.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    entries: dict[str, polib.POEntry] = {}
    for path in po_paths:
        for entry in polib.pofile(str(path)).translated_entries():
            entries[entry.msgid] = entry
    for entry in entries.values():
        merged.append(entry)
    merged.save(str(output_path))


def _strip_covered_msgids(pot_path: Path, terms: list[Path]) -> None:
    """Remove from POT any msgids already covered by library PO files."""
    if not terms:
        return
    covered: set[str] = set()
    for path in terms:
        for entry in polib.pofile(str(path)).translated_entries():
            covered.add(entry.msgid)
    if not covered:
        names = ", ".join(p.name for p in terms)
        log.warning("terms configured but contains no translated entries: %s", names)
        return
    pf = polib.pofile(str(pot_path))
    for entry in [e for e in pf if e.msgid in covered]:
        pf.remove(entry)
    pf.save(str(pot_path))


def _strip_pot(pot_path: Path, stem: str, ignore_numbers: bool) -> None:
    pf = polib.pofile(str(pot_path))
    for entry in [
        e
        for e in pf
        if e.msgid == stem or (ignore_numbers and e.msgid.strip().lstrip("-").isdigit())
    ]:
        pf.remove(entry)
    pf.save(str(pot_path))


def _update_po(pot_path: Path, po_path: Path) -> None:
    tmp = po_path.with_suffix(".po.new")
    try:
        result = subprocess.run(
            ["pot2po", "-t", po_path, "-i", pot_path, "-o", tmp],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:  # pragma: no cover
            log.error("pot2po failed for %s: %s", po_path.name, result.stderr)
            tmp.unlink(missing_ok=True)
            return
        shutil.move(tmp, po_path)
        _clean_po(po_path)
    except FileNotFoundError:  # pragma: no cover
        log.error("pot2po not found; install translate-toolkit")
        tmp.unlink(missing_ok=True)


def _check_sync(pot_path: Path, po_path: Path) -> bool:
    from translate.storage import po as po_mod

    pot_ids = {
        u.source
        for u in po_mod.pofile.parsefile(str(pot_path)).units
        if u.istranslatable()
    }
    po_ids = {
        u.source
        for u in po_mod.pofile.parsefile(str(po_path)).units
        if u.istranslatable()
    }
    return pot_ids == po_ids


def _po_stats(po_path: Path) -> dict[str, int]:
    from translate.storage import po as po_mod

    units = [
        u for u in po_mod.pofile.parsefile(str(po_path)).units if u.istranslatable()
    ]
    translated = sum(1 for u in units if u.istranslated() and not u.isfuzzy())
    fuzzy = sum(1 for u in units if u.isfuzzy())
    untranslated = sum(1 for u in units if not u.istranslated() and not u.isfuzzy())
    return {
        "total": len(units),
        "translated": translated,
        "fuzzy": fuzzy,
        "untranslated": untranslated,
    }


def _apply_po(html: str, po_path: Path) -> str:
    with tmp_file(".html", html) as tmp_html_path:
        out = BytesIO()
        with po_path.open("rb") as pf, tmp_html_path.open("rb") as hf:
            po2html.converthtml(pf, out, hf)
        return out.getvalue().decode("utf-8")


def _resolve_paths(raw: str | list, base_dir: Path) -> list[Path]:
    items = [raw] if isinstance(raw, str) else list(raw)
    return [(base_dir / str(p)).resolve() for p in items]


_TRANSLATION_STATIC_KEYS = frozenset(
    {
        "language",
        "languages",
        "base_language",
        "filename_template",
        "terms",
        "po",
        "ignore_numbers",
    }
)


def _validate_translation_config(config: dict) -> None:
    cfg = config.get("translation", {})
    unknown = sorted(
        k for k in cfg if k not in _TRANSLATION_STATIC_KEYS and not k.startswith("po_")
    )
    if unknown:
        msg = f"[translation] unknown config key(s): {', '.join(unknown)}"
        raise ValueError(msg)


# --- Filter stage (PREPROCESS): fork per language at markdown level ---


class FilterStage(BaseStage):
    name = "translation_filter"
    consumes = ContentType.MARKDOWN
    produces = ContentType.MARKDOWN
    phase = Phase.PREPROCESS
    config_key = "translation"

    def validate_config(self, config: dict) -> None:
        _validate_translation_config(config)

    def process(self, context: Context) -> Context | list[Context]:
        assert isinstance(context.content, str)
        cfg = self.get_config(context)

        languages: list[str] = cfg.get("languages", [])
        base_language: str = cfg.get("base_language", "")
        filename_template: str = cfg.get("filename_template", "{filename}_{langcode}")

        # Single-language mode: filter only, no fork
        language: str | None = cfg.get("language")
        if language:
            context.content = _apply_filter(context.content, language)
            self.log.debug("Applied filter directives for language '%s'", language)
            return context

        # Multi-language mode: fork here, one context per language
        if not languages and not base_language:
            return context

        if not languages or not base_language:
            msg = "translation plugin requires both 'languages' and 'base_language' in [translation] config"
            raise ValueError(msg)

        stem = context.source_path.stem
        results: list[Context] = []

        def _make_context(langcode: str, content: str) -> Context:
            new_stem = filename_template.format(
                filename=stem, langcode=langcode.upper()
            )
            ctx = deepcopy(context)
            ctx.content = content
            ctx.source_path = context.source_path.with_name(
                new_stem + context.source_path.suffix
            )
            ctx.artifacts["translation_langcode"] = langcode.lower()
            ctx.artifacts["translation_original_stem"] = stem
            return ctx

        # Base language
        base_content = _apply_filter(context.content, base_language)
        results.append(_make_context(base_language.upper(), base_content))
        self.log.info("Filtered for base language: %s", base_language.upper())

        # Target languages
        for lang in sorted(languages):
            filtered = _apply_filter(context.content, lang)
            results.append(_make_context(lang.upper(), filtered))
            self.log.info("Filtered for language: %s", lang.upper())

        return results


# --- Translation stage (ENRICH): apply PO to per-language HTML ---


class Stage(BaseStage):
    name = "translation"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH
    after = ("vars",)

    def validate_config(self, config: dict) -> None:
        _validate_translation_config(config)

    def _apply_translation(
        self, context: Context, po_path: Path, langcode: str
    ) -> None:
        stats = _po_stats(po_path)
        if stats["fuzzy"] > 0:
            self.log.warning(
                "Translation has %d fuzzy entries for %s",
                stats["fuzzy"],
                langcode.upper(),
            )
        if stats["untranslated"] > 0:
            self.log.warning(
                "Translation has %d untranslated entries for %s",
                stats["untranslated"],
                langcode.upper(),
            )
        assert isinstance(context.content, str)
        context.content = _apply_po(context.content, po_path)

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        cfg = self.get_config(context)

        langcode: str | None = context.artifacts.get("translation_langcode")
        base_language: str = cfg.get("base_language", "")

        # No multi-language config or not forked -> passthrough
        if not langcode or not base_language:
            return context

        # Base language: extract POT for sync checking, no translation needed
        base_dir = context.source_path.parent
        # Recover original stem by reversing the filename template
        # The stem was set by FilterStage; the original is in source_path parent
        # Use the langcode suffix to find PO paths relative to original file
        # We stored langcode in artifacts; resolve PO relative to output_dir parent
        # Actually source_path is already renamed (doc_DE.md), so use parent + stem logic

        original_stem: str = context.artifacts.get(
            "translation_original_stem", context.source_path.stem
        )

        ignore_numbers: bool = cfg.get("ignore_numbers", True)

        if langcode == base_language.lower():
            pot_path = base_dir / f"{original_stem}.pot"
            _extract_pot(context.content, pot_path, original_stem)
            _strip_pot(pot_path, context.source_path.stem, ignore_numbers)
            self.log.debug("Extracted POT for base language")
            return context

        # Target language: resolve PO paths and apply translation
        terms_raw: str | list = cfg.get("terms", [])
        terms: list[Path] = _resolve_paths(terms_raw, base_dir) if terms_raw else []

        # Default doc PO is always included; [translation.po] entries are extras merged alongside
        filename_template: str = cfg.get("filename_template", "{filename}_{langcode}")
        lang_stem = filename_template.format(
            filename=original_stem, langcode=langcode.upper()
        )
        doc_po = base_dir / f"{lang_stem}.po"
        extra_raw = cfg.get(f"po_{langcode}") or cfg.get("po", {}).get(langcode)
        extra_po: list[Path] = _resolve_paths(extra_raw, base_dir) if extra_raw else []

        if not doc_po.exists():
            msg = f"PO file missing for '{langcode.upper()}': {doc_po}"
            raise FileNotFoundError(msg)

        # Extract per-language POT and check sync against the doc PO
        pot_path = base_dir / f"{lang_stem}.pot"
        _extract_pot(context.content, pot_path, original_stem)
        _strip_pot(pot_path, context.source_path.stem, ignore_numbers)
        _strip_covered_msgids(pot_path, [*terms, *extra_po])
        if not _check_sync(pot_path, doc_po):
            self.log.warning(
                "PO out of sync for '%s' -- document has changed, updating",
                langcode.upper(),
            )
        _update_po(pot_path, doc_po)

        all_po = [*terms, *extra_po, doc_po]
        if len(all_po) == 1:
            self._apply_translation(context, all_po[0], langcode)
        else:
            with tmp_file(".po") as merged_path:
                _merge_po(all_po, merged_path)
                self._apply_translation(context, merged_path, langcode)

        self.log.info("Applied translation: %s", langcode.upper())
        return context


log = Stage.log
