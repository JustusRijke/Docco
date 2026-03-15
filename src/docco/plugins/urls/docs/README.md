# urls

Absolutizes relative URLs in HTML and optionally validates that they resolve.

Runs in the RENDER phase after `page`, before `htmlhint` and `pdf`.

## What it does

1. Rewrites relative `src`/`href` attributes to absolute `file://` paths
2. Rewrites relative `url()` references in `<style>` blocks to absolute `file://` paths
3. Optionally validates that all referenced URLs exist/respond (`test = true`)

## Configuration

```toml
[urls]
enable = true      # Enable URL absolutization and validation (default: true)
test = true        # Validate that URLs exist/respond (default: true)
local_only = true  # Only validate file:// URLs, skip http(s):// checks (default: true)
```

## Validation (`test = true`)

- `file://` URLs: raises `FileNotFoundError` if the path does not exist
- `http://`/`https://` URLs (only when `local_only = false`): raises `ValueError` if the server returns HTTP 400+
- Unreachable hosts: logged as a warning (not a hard failure)
