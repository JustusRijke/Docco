# diffpdf plugin

Skips writing the PDF if it is visually identical to the existing output file.

## Configuration

```toml
[diffpdf]
threshold = 0.1    # Max allowed per-pixel difference (default: 0.1)
dpi = 96           # Resolution for visual comparison (default: 96)
skip_text = false  # Skip text content check (default: false)
store = false      # Save diff images to ./diffpdf/ next to the output PDF (default: false)
```

When the new PDF is identical to the existing one, the output file is not overwritten and the document is counted as skipped.

When `store = true`, diff images are written to a `diffpdf/` directory next to the output PDF, allowing inspection of visual differences.
