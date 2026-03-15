# page-bg Plugin

Injects a CSS background image onto a pagedjs page by using a `:has()` selector targeting an
empty marker `<div>`.

## Directive syntax

```html
<!-- page-bg image="path/to/bg.jpg" x="50%" y="0" size="contain" -->
```

All attributes except `image` are optional.

| Attribute | Default | Description |
|-----------|---------|-------------|
| `image` | *(required)* | Path to the background image |
| `x` | `50%` | Horizontal background-position |
| `y` | `0` | Vertical background-position |
| `size` | `contain` | CSS background-size value (e.g. `cover`, `contain`, `100px`) |

## Output

Each directive is replaced with a scoped `<style>` block and an empty `<div>`:

```html
<style>
div.pagedjs_page_content:has(.page_bg_0) {
    background: url("bg.jpg") no-repeat;
    background-position: 50% 0;
    background-size: contain;
}
</style>
<div class="page_bg_0"></div>
```

Multiple directives in the same document each get a unique class (`page_bg_0`, `page_bg_1`, …)
to avoid CSS collisions.

No `[page-bg]` config section is needed — all parameters are supplied inline via the directive.
