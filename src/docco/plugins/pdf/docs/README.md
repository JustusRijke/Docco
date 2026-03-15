# pdf

Renders HTML to PDF using Playwright (headless Chromium).

## Configuration

```toml
[pdf]
dpi = 300       # Downscale embedded images to this DPI using Ghostscript (default: no downscaling)
keep_html = true  # Write intermediate HTML to output directory for debugging
```

## How it works

1. Playwright loads the HTML document (`networkidle` wait).
2. If the document contains paged.js (via the `toc` stage or the built-in template), rendering waits until `window.pagedJsRenderingComplete === true`.
3. `page.pdf()` is called with `print_background=true` and `prefer_css_page_size=true`.
4. If `dpi` is set, Ghostscript (`gs` / `gswin64c`) downscales all images in the PDF.

## Requirements

- Playwright Chromium must be installed:
  ```bash
  uv run playwright install chromium --only-shell
  ```
- Ghostscript is optional (only needed for `dpi` downscaling).

## Notes

- Console output from Chromium is forwarded to the Docco logger (`docco.plugins.pdf`).
- The `dpi` option uses Ghostscript bicubic downsampling for color/grayscale and subsample for mono images.
- If Ghostscript is not found, a warning is logged and downscaling is skipped.
