# page

Processes page layout directives in HTML: page breaks and orientation sections.

## Directives

### Page break

```html
<!-- page break -->
```

Replaced with `<div class="pagebreak"></div>`. The required CSS (`page-break-after: always`) is injected automatically via `page.css`.

### Orientation

```html
<!-- page landscape -->
...content...
<!-- page portrait -->
...content...
```

Content between orientation directives is wrapped in:

```html
<div class="section-wrapper landscape">...</div>
<div class="section-wrapper portrait">...</div>
```

The required `@page` rules and paged.js named page CSS are injected automatically via `page.css` (A4 portrait by default, landscape where specified).

## Configuration

| Key | Default | Description |
|-----|---------|-------------|
| `add_pagedjs_screen_css` | `true` | Inject screen CSS for paged.js page preview (white pages on grey background) |

## Landscape handler script

When orientation directives are present, a paged.js `LandscapeHandler` script is injected. It runs after rendering and adds the `landscape_page` class to any page paged.js has marked as `pagedjs_landscape_page`, allowing CSS to target landscape pages directly.

## Example

See [`example/example.md`](../example/example.md).

## Notes

- `page.css` is always injected automatically and sets the default page size to A4 portrait.
- Content before the first orientation directive is treated as portrait.
- page directives in the source Markdown must survive the `html` stage as raw HTML (markdown-it passes through HTML comments).
