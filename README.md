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

Create `docco.toml` in your project root (see [docco.example.toml](./docco.example.toml) for all options). This configuration will apply to all documents parsed by Docco.

Each document can have its own document-specific configuration as well.
Create a `.toml` file with the same name as the document, e.g.:

```
my_doc.md
my_doc.toml
```

These config files usually contain variable definitions, like document title and version.

The document-specific configuration overrules the project configuration (per-key override; lists are appended).

## Plugins

All plugins run automatically. Config sections in `docco.toml` provide per-plugin settings.

| Plugin | Description |
|--------|-------------|
| [vars](./src/docco/plugins/vars/docs/README.md) | `$$varname$$` substitution |
| [translation](./src/docco/plugins/translation/docs/README.md) | Language filtering and PO-based translation |
| [inline](./src/docco/plugins/inline/docs/README.md) | `<!-- inline src="file" -->` embedding |
| [pdf2svg](./src/docco/plugins/pdf2svg/docs/README.md) | `<!-- pdf2svg -->` PDF page to SVG extraction |
| [html](./src/docco/plugins/html/docs/README.md) | Markdown to HTML conversion |
| [toc](./src/docco/plugins/toc/docs/README.md) | Table of contents (`<!-- toc -->`) |
| [page_bg](./src/docco/plugins/page_bg/docs/README.md) | `<!-- page-bg -->` background image injection |
| [page](./src/docco/plugins/page/docs/README.md) | Page breaks and orientation changes |
| [urls](./src/docco/plugins/urls/docs/README.md) | URL absolutization and validation |
| [htmlhint](./src/docco/plugins/htmlhint/docs/README.md) | HTML linting (opt-in) |
| [pdf](./src/docco/plugins/pdf/docs/README.md) | PDF rendering via Playwright/Chromium |
| [diffpdf](./src/docco/plugins/diffpdf/docs/README.md) | Skip writing identical PDFs |
| [dpi](./src/docco/plugins/dpi/docs/README.md) | Image DPI downscaling and validation |

For information on writing your own plugins, see the [plugin development guide](./src/docco/plugins/README.md).

## Error Handling

When the pipeline fails, Docco saves the intermediate output (the content at the point of failure, e.g. `.intermediate.html`) to the output directory and logs the filename. This makes it easier to inspect what the document looked like before the error.

To disable this behavior, add to `docco.toml`:

```toml
[error]
save_intermediate = false
```

## Acknowledgements

Docco builds on the following projects:

- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) -- Markdown parsing and HTML conversion
- [mdit-py-plugins](https://github.com/executablebooks/mdit-py-plugins) -- markdown-it extensions (attributes, tables, anchors)
- [Playwright](https://playwright.dev/python/) -- headless Chromium for PDF rendering
- [paged.js](https://pagedjs.org/) -- CSS paged media polyfill (table of contents, page breaks)
- [diffpdf](https://pypi.org/project/diffpdf/) -- visual PDF comparison
- [PyMuPDF](https://pymupdf.readthedocs.io/) -- PDF/SVG manipulation and DPI validation
- [polib](https://github.com/izimobil/polib) -- PO file parsing for translations
- [Translate Toolkit](https://toolkit.translatehouse.org/) -- translation utilities
- [HTMLHint](https://htmlhint.com/) -- HTML linting
