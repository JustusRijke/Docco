# Docco

Plugin-based Markdown to PDF converter.

## Installation

```bash
uv add docco
uv run playwright install chromium --only-shell
```

## Usage

```bash
docco input.md                        # output: input.pdf (next to input file)
docco input.md -o output/             # output: output/input.pdf
docco chapter1.md chapter2.md -o output/
docco page.html -o output/            # HTML input (skips Markdown stages)
docco -o output/                      # uses 'file' key from docco.toml
docco input.md --config path/to/docco.toml
```

## Configuration

Create `docco.toml` in your project root (see `docco.example.toml` for all options). This configuration will apply to all documents parsed by Docco.

Each document can have its own document-specific configuration as well.
Create a `.toml` file with the same name as the document, e.g.:

```bash
my_doc.md
my_doc.toml
```

These config files usually contain variable definitions, like document title and version.

The document specific configuration overrules the project configuration.

## Plugins

| Plugin | Phase | Description |
|--------|-------|-------------|
| [vars](./src/docco/plugins/vars/docs/README.md) | Preprocess | `$$varname$$` substitution |
| [translation](./src/docco/plugins/translation/docs/README.md) (filter) | Preprocess | `<!-- filter:lang -->` language blocks |
| [inline](./src/docco/plugins/inline/docs/README.md) | Preprocess | `<!-- inline:"file" -->` embedding |
| [pdf2svg](./src/docco/plugins/pdf2svg/docs/README.md) | Preprocess | `<!-- pdf2svg -->` PDF page to SVG extraction |
| [html](./src/docco/plugins/html/docs/README.md) | Convert | Markdown to HTML via markdown-it |
| [toc](./src/docco/plugins/toc/docs/README.md) | Enrich | Table of contents (`<!-- toc -->`) |
| [translation](./src/docco/plugins/translation/docs/README.md) | Enrich | PO-based translation, forks pipeline per language |
| [page_bg](./src/docco/plugins/page_bg/docs/README.md) | Enrich | `<!-- page-bg -->` background image injection |
| [page](./src/docco/plugins/page/docs/README.md) | Enrich | `<!-- page pagebreak="true" -->`, `<!-- page orientation="landscape" -->` |
| [pdf](./src/docco/plugins/pdf/docs/README.md) | Render | Playwright/Chromium rendering |
| [htmlhint](./src/docco/plugins/htmlhint/docs/README.md) | Render | HTML linting (opt-in) |
| [diffpdf](./src/docco/plugins/diffpdf/docs/README.md) | Postprocess | Skip identical PDFs |
| [dpi](./src/docco/plugins/dpi/docs/README.md) | Postprocess | Image downscaling and DPI validation |

All plugins run automatically. Config sections in `docco.toml` provide per-plugin settings.

## Error handling

When the pipeline fails, Docco saves the intermediate output (the content at the point of failure, e.g. `.intermediate.html`) to the output directory and logs the filename. This makes it easier to inspect what the document looked like before the error.

To disable this behavior, add to `docco.toml`:

```toml
[error]
save_intermediate = false
```

## Writing plugins

Any Python package can add stages by registering an entry point in the `docco.stages` group:

```toml
[project.entry-points."docco.stages"]
my-stage = "mypackage.plugin:Stage"
```

The `Stage` class must inherit from `docco.pipeline.Stage` and declare `name`,
`consumes`, `produces`, `phase`, and implement `process(context) -> Context`.
Use `after = ("other_plugin",)` for soft ordering constraints.
