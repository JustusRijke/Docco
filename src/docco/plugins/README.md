# Plugin Development

Docco uses a plugin architecture where each processing step is an independent **stage**. Stages are auto-discovered, auto-ordered, and always active.

## Writing a Plugin

Create a package under `src/docco/plugins/<name>/` with the following structure:

```
src/docco/plugins/<name>/
    __init__.py          # Stage class
    test_edgecase.py     # Edge-case tests only
    docs/README.md       # Plugin documentation
    example/
        example.md       # Example input (used by regression tests)
        example.toml     # Example config (if needed)
        example.pdf      # Expected output (committed to repo)
```

The `Stage` class must inherit from `docco.pipeline.Stage` and declare:

- `name` -- unique identifier (matches config section)
- `consumes` -- expected input `ContentType` (MARKDOWN, HTML, PDF, or ANY)
- `produces` -- output `ContentType`
- `phase` -- one of PREPROCESS, CONVERT, ENRICH, RENDER, POSTPROCESS
- `process(context) -> Context | list[Context]` -- the transformation

Optional attributes:

- `after = ("other_plugin",)` -- soft ordering within the same phase
- `config_key` -- share a config section with another stage (default: `name`)
- `valid_config_keys` -- frozenset of allowed keys (enables unknown-key validation)

Register the plugin in `pyproject.toml`:

```toml
[project.entry-points."docco.stages"]
my-stage = "docco.plugins.my_stage:Stage"
```

Then add a commented config section to `docco.example.toml`.

## Pipeline Phases

Stages run in phase order. Within a phase, `after` constraints determine ordering (with alphabetical tie-breaking).

```
PREPROCESS   Markdown -> Markdown transforms (vars, inline, pdf2svg, translation filter)
CONVERT      Markdown -> HTML (html plugin)
ENRICH       HTML -> HTML transforms (toc, translation, page_bg, page)
RENDER       HTML -> PDF (urls, htmlhint, pdf plugin)
POSTPROCESS  PDF -> PDF transforms (diffpdf, dpi)
```

When the input is an HTML file, PREPROCESS and CONVERT phases are skipped.

## Configuration

Plugins read their config via `self.get_config(context)`, which returns the `[<name>]` section from the merged TOML config (or an empty dict if absent).

Override `normalize_config_section(section, base_dir)` to resolve relative paths or coerce types before config merging. Override `validate_config(config)` to check for unknown keys (set `valid_config_keys` for automatic validation).

## Directives

Many plugins use HTML comment directives like `<!-- plugin-name key="value" -->`. Use the built-in `self.get_directives(content)` or `Stage.parse_directives(name, content)` to parse these -- they handle `key="value"` pairs and bare-word flags, and raise on malformed input.

## Testing

### Regression Tests

The happy path for each plugin is tested via `tests/test_regression.py`. This test:

1. Runs your plugin's `example/example.md` through the full pipeline
2. Checks with `git diff` that no files in the `example/` directory changed

This means your `example/` directory serves as a golden test: the committed `example.pdf` is the expected output. When you change plugin behavior, re-run the pipeline on the example and commit the updated output.

To be picked up by the regression test, your plugin needs an `example/example.md` file.

### Edge-Case Tests

`test_edgecase.py` covers only the branches that the example cannot reach -- error paths, invalid config, missing tools, etc. Use the `make_ctx` helper from `conftest.py` to create test contexts:

```python
from conftest import make_ctx
from docco.plugins.my_plugin import Stage

def test_invalid_config_raises(tmp_path):
    ctx = make_ctx(tmp_path, "content", config={"my_plugin": {"bad": "key"}})
    with pytest.raises(ValueError, match="unknown"):
        Stage().process(ctx)
```

A long `test_edgecase.py` is a code smell -- it usually means the production code has too much defensive logic.

### Running Tests

```bash
uv run pytest --no-header -q    # all tests, 100% branch coverage target
```
