# inline

Embeds external Markdown or HTML fragments into the current document using inline directives.

## Usage

```markdown
<!-- inline src="path/to/fragment.md" -->
```

Paths are relative to the file containing the directive. Absolute paths are also supported.

### Placeholders

Pass arguments to fill `{{placeholder}}` variables inside the fragment:

```markdown
<!-- inline src="snippets/greeting.md" name="World" greeting="Hello" -->
```

`snippets/greeting.md`:
```markdown
{{greeting}}, {{name}}!
```

Result:
```markdown
Hello, World!
```

### Nesting

Inlined files may themselves contain inline directives. Processing is iterative (up to 10 levels deep).

## Example

See [`src/docco/plugins/inline/example/`](../example/) for a working example that inlines a nested fragment.

## Notes

- Raises `FileNotFoundError` if the referenced file does not exist.
- Raises `ValueError` if nesting exceeds 10 iterations (circular reference guard).
- Unused arguments and unfulfilled placeholders produce warnings.
