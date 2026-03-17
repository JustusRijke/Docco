# dpi plugin

Downscales images in the rendered PDF and warns about images still below the target DPI.

## Configuration

```toml
[dpi]
max = 300   # Max image DPI; images below this are flagged with a warning (default: 300)
```

## Example

See [`src/docco/plugins/dpi/example/`](../example/) for a working example with a high-res and a low-res image, configured to downscale to 50 DPI.
