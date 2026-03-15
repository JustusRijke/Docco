# htmlhint

Lints the generated HTML using [HTMLHint](https://github.com/htmlhint/htmlhint) before PDF rendering.

Runs in the `RENDER` phase, after all HTML enrichment is complete.

## Requirements

`htmlhint` must be installed and available on `PATH`. See [installation instructions](https://github.com/htmlhint/htmlhint#global-installation-and-usage).

## Configuration

```toml
[htmlhint]
enable = true      # Enable HTML linting (default: false)
level = "error"    # Log level for issues: info, warning, error (default: error)
```

Lint results are stored in `context.artifacts["htmlhint"]` with `returncode` and `output`. Errors are logged as warnings but do not abort the build.

## Custom rules

Place a `.htmlhintrc` file in your project root to configure HTMLHint rules. See the [HTMLHint configuration docs](https://github.com/htmlhint/htmlhint?tab=readme-ov-file#-configuration).
