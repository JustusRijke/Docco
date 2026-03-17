# vars

Substitutes `$$varname$$` placeholders in HTML with values from the `[vars]` config section.

## Configuration

```toml
[vars]
version = "2.0"
author = "Jane Doe"
```

## Usage

```markdown
Version: $$version$$
Author:  $$author$$
```

## Built-in variables

| Variable | Value |
|----------|-------|
| `$$PATH$$` | Absolute path to the directory containing the source file |
| `$$DAY$$` | Current day of the month, zero-padded (e.g. `07`) |
| `$$MONTH$$` | Current month, zero-padded (e.g. `03`) |
| `$$YEAR$$` | Current year (e.g. `2026`) |

## Notes

- `PATH`, `DAY`, `MONTH`, and `YEAR` are reserved and cannot be redeclared in `[vars]`.

## Example

See [`example/example.md`](../example/example.md).
