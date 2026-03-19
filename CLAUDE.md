# Docco - Claude Code Instructions

## Project Overview

Plugin-based Markdown-to-PDF converter.

- [README.md](./README.md) -- user-facing docs
- [ARCHITECTURE.md](./ARCHITECTURE.md) -- design, module structure, decision rationale
- [src/docco/plugins/README.md](./src/docco/plugins/README.md) -- plugin development guide
- Per-plugin docs: `src/docco/plugins/<name>/docs/README.md`

## Quick Reference

- **Python 3.14+**, managed with `uv`
- **Entry point:** `docco` CLI (`src/docco/cli.py:main`)
- **Config:** `docco.toml` (no `pipeline` key -- all plugins always run, config sections provide settings)
- **Plugins:** `src/docco/plugins/<name>/` -- each is a package with `__init__.py`, `tests.py`, `docs/README.md`
- **Tests:** `uv run pytest --no-header -q` (target 100% branch coverage always)
- **Playwright:** `uv run playwright install chromium --only-shell`

## Platform Compatibility

Docco must run on Windows, Linux, and macOS. Use `Path.as_posix()` when embedding paths in TOML strings, and avoid OS-specific assumptions in code and tests.

## Code Conventions

- Every plugin class is named `Stage` and inherits from `docco.pipeline.Stage`
- Each Stage declares `phase`, `consumes`, `produces`, and optionally `after`, `config_key`
- Config sections match plugin names: `[vars]`, `[html]`, `[pdf]`, `[toc]`, etc.
- The `translation` plugin has two stages: `FilterStage` (PREPROCESS) and `Stage` (ENRICH), both using `config_key = "translation"`
- Plugin implementation details must never leak into docco core code. Keep a clear separation of concerns.
- Paths defined in configuration files (i.e. docco.toml / somedocument.toml) are relative to that particular configuration file.

## Testing

- `conftest.py` has shared fixtures: `tmp_md`, `tmp_config`, `markdown_context`, `project_toml`, `output_dir`
- Plugin tests live alongside code: `src/docco/plugins/<name>/test_edgecase.py` (edge cases only) and `test_regression.py` (example-based happy path)
- The happy path is covered by running the plugin's `example/` through the full pipeline (`test_regression.py`); do not duplicate this in `test_edgecase.py`
- `test_edgecase.py` should be short -- only the branches the example cannot reach (e.g. invalid config, missing tool). A long `test_edgecase.py` is a code smell: the production code likely has too much defensive logic or is too complex
- Core tests in `tests/` directory
- pytest discovers both via `python_files = ["test_*.py", "tests*.py"]` and `testpaths = ["tests", "src/docco/plugins"]`
- Coverage config is in `pyproject.toml` under `[tool.pytest.ini_options]`

## Adding a New Plugin

1. Create `src/docco/plugins/<name>/` with `__init__.py`, `test_edgecase.py`, `docs/README.md`, and an `example/` directory
2. Implement `Stage` class with `name`, `consumes`, `produces`, `phase`, `process()`
3. Use `after = ("other_plugin",)` for soft ordering within the same phase
4. Register in `pyproject.toml` under `[project.entry-points."docco.stages"]`
5. Update `docco.example.toml` with config section
6. Run `uv run pytest` -- must stay at 100% coverage
