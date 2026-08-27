# qr Plugin

Generates a QR code for a URL as SVG and replaces the directive with the relative path to the output file.

## Directive Syntax

```markdown
<!-- qr url="https://example.com" out="my-qr-code.svg" -->
```

- `url` — the URL to encode
- `out` — output filename written under `svg_dir`
- `quiet` — (optional) bare flag; suppress output — directive is replaced with an empty string instead of the SVG path

The directive is replaced in-place with the relative path (e.g. `assets/my-qr-code.svg`), ready for use in a Markdown image link:

```markdown
![Scan me](<!-- qr url="https://example.com" out="my-qr-code.svg" -->)
```

becomes:

```markdown
![Scan me](assets/my-qr-code.svg)
```

## Configuration

```toml
[qr]
svg_dir = "assets"      # Output subdirectory relative to source file (default: "assets")
skip_if_exists = true   # Skip generation if SVG already exists (default: true)
```

## Example

See [`example/example.md`](../example/example.md).
