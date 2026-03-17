# translation

Multilingual support: language filter directives and PO-based HTML translation.

This plugin provides two stages:
- **translation_filter** (PREPROCESS): filters `<!-- filter:lang -->` blocks in markdown
- **translation** (ENRICH): translates HTML using PO files, forks pipeline per language

Both activate from the `[translation]` config section.

## Single-language mode

Filter markdown content by language without PO translation:

```toml
[translation]
language = "en"
```

Wrap language-specific content in filter directives:

```markdown
<!-- filter:en -->English content.<!-- /filter -->
<!-- filter:de -->Deutscher Inhalt.<!-- /filter -->
```

## Multi-language mode

```toml
[translation]
base_language = "en"
languages = ["de", "fr"]
terms = ["shared/terms.po"]             # Optional: terms (strings that will not be translated)
ignore_numbers = true                   # Discard numeric-only msgids (default: true)
filename_template = "{filename}_{langcode}"  # Default output naming
```

The document title stem is always stripped from the POT. Integer-only msgids are stripped by default via `ignore_numbers` (decimals/floats are kept, as the decimal separator varies by locale). Use `terms` to filter out other shared strings by providing their translations there.

### PO file resolution

The document PO is auto-discovered next to the source file using `filename_template`:

- `doc.md` with `filename_template = "{filename}_{langcode}"` -> `doc_DE.po`, `doc_FR.po`

Use `[translation.po]` to specify **extra** PO files merged alongside the document PO (document wins):

```toml
[translation.po]
de = "copyright_de.po"
fr = ["copyright_fr.po", "shared_fr.po"]  # multiple extras; later wins
```

The document PO (`doc_de.po`) is always required. Missing it produces a warning and skips that language.

## How it works

1. Filter directives are applied per language in the PREPROCESS phase.
2. After HTML conversion, a POT file is extracted from the HTML.
3. Existing PO files are checked for drift and updated with `pot2po`.
4. The pipeline forks: one Context per language.
   - Base language: untranslated HTML, filename `{stem}_{BASE_LANG}`.
   - Each target language: translated HTML using `po2html`, filename `{stem}_{LANG}`.
5. If `terms` is set, shared term entries are merged (document PO wins).

## Output naming

With `base_language = "en"` and `languages = ["de"]`:

- `doc_EN.pdf` -- base language
- `doc_DE.pdf` -- German translation

## Notes

- Requires `translate-toolkit` and `pot2po` CLI tool (installed with the package).
- Warns about out-of-sync PO files and incomplete translations (untranslated or fuzzy).
- Missing PO files produce a warning and the language is skipped.
- Language codes in filter directives are case-insensitive.
