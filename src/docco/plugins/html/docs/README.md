# html

Converts Markdown to a self-contained HTML document using [markdown-it-py](https://github.com/executablebooks/markdown-it-py).

## Configuration

```toml
[html]
css = ["style.css"]                        # CSS files to embed (relative to source file or absolute)
template = "custom.html"                   # Custom HTML template (relative to source file or absolute)
js = ["app.js"]                            # JS files to inline in <head> (relative to source file or absolute)
js_external = ["https://example.com/lib.js"]  # External JS (<script src>)
```

## Template

The built-in template (`base.html`) renders:

- `{{ css }}` — all collected CSS inlined in a `<style>` block
- `{{ body }}` — rendered HTML body
Provide `template` to use a custom HTML file with the same placeholders.

## Markdown features

- CommonMark + raw HTML
- Auto-generated heading IDs (anchors plugin)
- Inline attribute syntax: `{.class #id attr=val}` (attrs plugin)
- Block attribute syntax (attrs_block plugin)
- Tables

## Notes

- paged.js is always loaded from unpkg CDN (required for print layout and TOC rendering).
- URL absolutization and validation is handled by the `urls` plugin (RENDER phase).
