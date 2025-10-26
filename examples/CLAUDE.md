# Examples Coding Guidelines

This file provides example-specific coding guidelines for maintaining Docco examples.

## Example Maintenance

- Keep examples minimal and focused - demonstrate features without bloat
- Follow KISS & DRY principles
- Examples should match current implementation exactly

## Testing Examples

```bash
# Always test examples after code changes
docco build examples/Feature\ Showcase.md examples/style.css
docco build examples/Multilingual\ Example.md examples/style.css
docco build examples/Full\ Page\ Table.md examples/style.css
```

Verify output in `output/` directory and check `debug.html` files.

## Full Page Box Example

The `Full Page Table.md` example demonstrates how to create a bordered box that spans the entire content area of a page while accounting for:
- A4 page dimensions (210mm × 297mm)
- 25mm margins on all sides = 247mm available height
- Header (~7mm) and footer (~7mm) heights = 14mm total
- H1 heading with margins (~12mm)
- **Net box height: 220mm** (233 - 12 - 1mm safety)

**Key technique:** Use explicit `height: 220mm` with `box-sizing: border-box` and `page-break-inside: avoid`. The CSS comments show the exact calculation for different page layouts.
