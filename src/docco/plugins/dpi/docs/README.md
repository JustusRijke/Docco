# dpi plugin

Downscales images in the rendered PDF and warns about images still below the target DPI.

## Configuration

```toml
[dpi]
max = 300   # Max image DPI; images below this are flagged with a warning (default: 300)
```

Requires Ghostscript (`gs` or `gswin64c`) for downscaling.
