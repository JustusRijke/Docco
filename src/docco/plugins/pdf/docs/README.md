# pdf

Renders HTML to PDF using Playwright (headless Chromium).

## Configuration

```toml
[pdf]
title = "<filename>"  # PDF document title; "<filename>" uses the source filename stem
author = "Jane Doe"   # PDF document author
keep_html = true      # Write intermediate HTML to output directory for debugging
png = true            # Also export each page as <stem>-<page>.png in the output directory
png_dpi = 150         # Resolution of the exported PNGs (default: 150)
```

## How it works

1. Playwright loads the HTML document (`networkidle` wait).
2. If the document contains paged.js (via the `toc` stage or the built-in template), rendering waits until `window.pagedJsRenderingComplete === true`.
3. `page.pdf()` is called with `print_background=true` and `prefer_css_page_size=true`.
4. If `png` is set, each PDF page is rasterized with PyMuPDF to `<stem>-001.png`, `<stem>-002.png`, ...

## Requirements

- Playwright Chromium must be installed:
  ```bash
  uv run playwright install chromium --only-shell
  ```

## Notes

- Console output from Chromium is forwarded to the Docco logger (`docco.plugins.pdf`).
- Image DPI downscaling lives in the separate [dpi](../../dpi/docs/README.md) plugin.
