# pdf2svg Plugin

Extracts a page from a PDF as an auto-cropped SVG and replaces the directive with the relative path to the output file.

## Directive Syntax

```markdown
<!-- pdf2svg src="path/to/file.pdf" page="1" out="figure.svg" -->
```

- `src` — PDF path relative to the source Markdown file
- `page` — 1-indexed page number
- `out` — (optional) output filename written under `svg_dir`; if omitted, defaults to `{stem}_p{page}.svg` (e.g. `diagram_p2.svg`)
- `quiet` — (optional) bare flag; suppress output — directive is replaced with an empty string instead of the SVG path

The directive is replaced in-place with the relative path (e.g. `assets/figure.svg`), ready for use in a Markdown image link:

```markdown
![My figure](<!-- pdf2svg src="diagram.pdf" page="2" out="diagram.svg" -->)
```

becomes:

```markdown
![My figure](assets/diagram.svg)
```

When `out` is omitted the filename is derived automatically:

```markdown
![My figure](<!-- pdf2svg src="diagram.pdf" page="2" -->)
```

becomes:

```markdown
![My figure](assets/diagram_p2.svg)
```

## Auto-Crop

The plugin calculates tight bounds from all text blocks, vector drawings, and images on the page. The SVG viewport is clipped to this bounding box, removing excess whitespace. Falls back to the full page rect if bounds cannot be determined.

## Configuration

```toml
[pdf2svg]
svg_dir = "assets"      # Output subdirectory relative to source file (default: "assets")
skip_if_exists = true   # Skip conversion if SVG already exists (default: true)
```

### `skip_if_exists`

When `true` (the default), conversion is skipped if the output SVG file already exists. This speeds up repeated builds. Set to `false` to always regenerate.

## Example

See [`example/example.md`](../example/example.md).
