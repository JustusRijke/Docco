import logging
import tomllib
from pathlib import Path
from typing import Any

log = logging.getLogger("docco.config")

Normalizers = dict[str, Any]  # section_name -> callable(section, base_dir) -> section


def find_project_config(start: Path, stop_at: Path | None = None) -> Path | None:
    """Walk up from start directory to find docco.toml, stopping at stop_at (inclusive)."""
    current = start.resolve()
    ceiling = (stop_at or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        candidate = directory / "docco.toml"
        if candidate.is_file():
            log.info("Found project config: %s", candidate)
            return candidate
        if directory == ceiling:
            break
    return None


def find_document_config(source_path: Path) -> Path | None:
    """Find sidecar .toml for a markdown file (e.g., mydoc.toml for mydoc.md)."""
    sidecar = source_path.with_suffix(".toml")
    if sidecar.is_file():
        log.info("Found document config: %s", sidecar)
        return sidecar
    return None


def _apply_normalizers(
    config: dict[str, Any], base_dir: Path, normalizers: Normalizers
) -> dict[str, Any]:
    result = dict(config)
    for section, fn in normalizers.items():
        if section in result:
            result[section] = fn(result[section], base_dir)
    return result


def _merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override into base. Lists are appended, dicts are recursively merged."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], list) and isinstance(value, list):
            merged[key] = [*merged[key], *value]
        elif (
            key in merged and isinstance(merged[key], dict) and isinstance(value, dict)
        ):
            merged[key] = _merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _validate_config(config: dict[str, Any]) -> None:
    if not config:
        msg = "No docco.toml found. A project config file is required."
        raise ValueError(msg)


def load_project_config(
    *,
    config_path: Path | None = None,
    start: Path | None = None,
    normalizers: Normalizers | None = None,
) -> tuple[dict[str, Any], Path]:
    """Load the project-level docco.toml.

    If config_path is given, use it directly.
    Otherwise, walk up from start (defaults to cwd).

    Returns (config, config_dir).
    """
    if config_path is not None:
        resolved = config_path.resolve()
        config_dir = resolved.parent
        project_config = _load_toml(resolved)
    else:
        found = find_project_config(start or Path.cwd())
        config_dir = found.parent if found else Path.cwd()
        project_config = _load_toml(found) if found else {}

    if normalizers:
        project_config = _apply_normalizers(project_config, config_dir, normalizers)

    _validate_config(project_config)
    return project_config, config_dir


def load_config(
    source_path: Path,
    project_config: dict[str, Any],
    normalizers: Normalizers | None = None,
) -> dict[str, Any]:
    """Merge project config with document sidecar config."""
    doc_config_path = find_document_config(source_path)
    if doc_config_path:
        doc_config = _load_toml(doc_config_path)
        if normalizers:
            doc_config = _apply_normalizers(
                doc_config, doc_config_path.parent, normalizers
            )
    else:
        doc_config = {}
    return _merge_configs(project_config, doc_config)
