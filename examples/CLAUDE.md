# Examples Coding Guidelines

This file provides example-specific coding guidelines for maintaining Docco examples.

## Example Maintenance

- After code changes, always run Docco on all the example md files
- If a feature is added, removed or changed, make sure to update all examples
- Keep examples minimal and focused - demonstrate features without bloat
- Follow KISS & DRY principles
- Examples should match current implementation exactly

## Testing Examples

```bash
# Always test examples after code changes
docco build examples/Feature\ Showcase.md examples/style.css
docco build examples/Multilingual\ Example.md examples/style.css
```

Verify output in `output/` directory and check `debug.html` files.
