# dpi plugin

Downscales images in the rendered PDF and warns about images still below the target DPI.

## Configuration

```toml
[dpi]
max = 300       # Max image DPI; images exceeding this are downscaled (default: 300)
level = "warning"  # Log level for low-DPI images: "info", "warning", or "error" (default: "warning")
```

## Example

See [`src/docco/plugins/dpi/example/`](../example/) for a working example with a high-res and a low-res image, configured to downscale to 50 DPI.
