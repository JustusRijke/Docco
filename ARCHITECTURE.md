# Docco v2 Architecture

## Overview

Docco is a plugin-based Markdown-to-PDF converter. Each processing step is an
independent **stage** that receives a `Context`, transforms it, and returns it.
Stages are auto-ordered based on their declared **phase** and soft dependencies.

```
CLI  -->  Config Loader  -->  Pipeline Builder  -->  Pipeline Runner
                                    |
          Discovers active plugins, orders by phase + after constraints
                                    |
          PREPROCESS -> CONVERT -> ENRICH -> RENDER -> POSTPROCESS
          [vars]        [html]    [toc]     [pdf]     [diffpdf]
          [inline]                [page]              [dpi]
          [pdf2svg]               [translation]
          [translation_filter]    [page_bg]
```

## Core Modules

```
src/docco/
    cli.py               # argparse entry point, output writing, summary
    config.py             # TOML discovery, loading, merging
    context.py            # Context dataclass, ContentType enum, Phase enum
    pipeline.py           # Stage ABC, plugin discovery, auto-ordering, execution
    logging_config.py     # Colored logging, LogCounter, redirect_to_debug
    plugins/              # Each plugin is a package with __init__.py, tests.py, docs/
```

### Context (the pipeline data object)

```python
Context:
    source_path: Path            # original input file
    output_dir: Path             # target output directory
    config: dict[str, Any]       # full merged config (read-only for plugins)
    content: str | bytes         # the main artifact, evolving through stages
    content_type: ContentType    # MARKDOWN, HTML, PDF, ANY
    artifacts: dict[str, Any]    # plugin data (skipped, etc.)
```

- `content` is the baton -- each stage transforms it and passes it on.
- `content_type` is validated at stage boundaries (fail-fast on misconfigured pipelines).
- `artifacts` is the extension mechanism for side-channel data between stages.
- Factory methods: `Context.from_file()` (markdown), `Context.from_html_file()` (html input).

### Stage Protocol

```python
class Stage(ABC):
    name: str                         # unique identifier
    consumes: ContentType             # expected input type
    produces: ContentType             # output type
    phase: Phase                      # PREPROCESS, CONVERT, ENRICH, RENDER, POSTPROCESS
    after: tuple[str, ...] = ()       # soft deps: run after these
    config_key: str = ""              # config section key (default: name)
    def process(self, context: Context) -> Context | list[Context]: ...
```

Returning a `list[Context]` forks the pipeline (used by translation for per-language output).

### Phase Enum

```python
class Phase(StrEnum):
    PREPROCESS = "preprocess"     # MD -> MD transforms
    CONVERT = "convert"           # MD -> HTML (exactly one: html)
    ENRICH = "enrich"             # HTML -> HTML transforms
    RENDER = "render"             # HTML -> PDF (exactly one: pdf)
    POSTPROCESS = "postprocess"   # PDF -> PDF transforms
```

### Auto-Ordering

All discovered plugins are always active. The pipeline builder:

1. Groups by phase
2. Topologically sorts within each phase using `after` constraints
3. Alphabetical tie-breaking for determinism
4. Skips PREPROCESS/CONVERT phases when input is HTML

A plugin can set `config_key` to share a config section with another plugin
(used by `translation_filter` which shares `config_key = "translation"`).

### Configuration

Two TOML layers, merged per-key:

1. **Project `docco.toml`** -- discovered by walking up from CWD. Shared settings.
2. **Document sidecar `<name>.toml`** -- next to the markdown file. Document-specific overrides.

Merge rule: document overrides project per-key; lists are appended.
Config sections configure plugins -- all plugins run regardless.

### Plugin Discovery

Plugins register via `pyproject.toml` entry points in the `docco.stages` group:

```toml
[project.entry-points."docco.stages"]
my_stage = "my_package.plugin:Stage"
```

Discovery uses `importlib.metadata.entry_points()`. Installing a plugin and
adding its config section to `docco.toml` activates it.

## Built-in Plugins

| Plugin | Phase | Consumes | Produces | Always | After | Description |
|--------|-------|----------|----------|--------|-------|-------------|
| vars | PREPROCESS | MD | MD | | | `$$varname$$` substitution |
| translation_filter | PREPROCESS | MD | MD | | | `<!-- filter:lang -->` blocks |
| inline | PREPROCESS | MD | MD | | vars | `<!-- inline:"file" -->` embedding |
| pdf2svg | PREPROCESS | MD | MD | | | PDF page to SVG extraction |
| html | CONVERT | MD | HTML | yes | | markdown-it, CSS/JS, template |
| toc | ENRICH | HTML | HTML | | | TOC injection (`<!-- toc -->`) |
| translation | ENRICH | HTML | HTML | | | PO translation, forks per language |
| page_bg | ENRICH | HTML | HTML | yes | | Background image directives |
| page | ENRICH | HTML | HTML | yes | toc, translation, page-bg | Pagebreak, orientation |
| pdf | RENDER | HTML | PDF | yes | | Playwright rendering |
| diffpdf | POSTPROCESS | PDF | PDF | | | Skip identical PDFs |
| dpi | POSTPROCESS | PDF | PDF | | | Image downscaling and DPI validation |

Each plugin lives in `src/docco/plugins/<name>/` with its own `__init__.py`,
`tests.py`, and `docs/README.md`. The `translation` package contains both
`FilterStage` (PREPROCESS) and `Stage` (ENRICH).

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| ABC over Protocol for Stage | Explicit contract; third-party plugins inherit from it |
| Each plugin exports `Stage` (not `VarsStage`) | Consistent; entrypoint already namespaces |
| ContentType StrEnum over bare strings | Eliminates magic strings |
| Phase-based auto-ordering | No manual pipeline definition; plugins self-describe |
| Soft `after` deps (ignored if target inactive) | Plugins can declare ordering without hard coupling |
| `config_key` for multi-phase plugins | Shared activation for filter + translation stages |
| TOML only (no YAML frontmatter) | One syntax, clean separation of content and config |
| No arbitrary code execution | Security: code only runs in trusted installed plugins |
| `pdf` plugin owns `keep_html` | Each plugin manages its own debug output |

## CLI Features

- Multi-file input from CLI args or `file` key in config
- HTML/HTM input (auto-skips PREPROCESS/CONVERT phases)
- `[pdf] keep_html = true` writes the intermediate HTML for debugging
- `[diffpdf]` config skips PDF overwrite when output is visually identical
- Warning/error counter with summary after processing
- `[log]` section for file logging and level override

## Dependencies

| Component | Dependencies |
|-----------|-------------|
| Core | colorlog |
| html plugin | markdown-it-py, mdit-py-plugins |
| pdf plugin | playwright |
| diffpdf plugin | diffpdf |
| dpi plugin | pymupdf |
| translation plugin | polib, translate-toolkit |
