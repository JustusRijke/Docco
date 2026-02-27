"""Config file discovery and loading for .docco files."""

import logging
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

CONFIG_FILENAME = ".docco"
KNOWN_SECTIONS = {"input", "python", "output"}
KNOWN_INPUT_KEYS = {"file"}
KNOWN_PYTHON_KEYS = {"allow"}
KNOWN_OUTPUT_KEYS = {"path", "createdir", "keep-intermediate"}


def find_config(start: Path) -> Path | None:
    """Walk up from start dir looking for .docco."""
    current = start.resolve()
    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_config(path: Path) -> dict:
    """Parse .docco TOML file, return validated dict with known keys only."""
    with path.open("rb") as f:
        raw = tomllib.load(f)

    logger.info(f"Using config: {path}")

    for section in raw:
        if section not in KNOWN_SECTIONS:
            logger.warning(f"Unknown config section: [{section}]")

    result: dict = {}

    if "input" in raw:
        input_section = raw["input"]
        for key in input_section:
            if key not in KNOWN_INPUT_KEYS:
                logger.warning(f"Unknown config key in [input]: {key}")

        if "file" in input_section:
            raw_file = input_section["file"]
            if isinstance(raw_file, str):
                files = [raw_file]
            else:
                files = list(raw_file)
            # Resolve paths relative to the config file's directory
            config_dir = path.parent
            result["input"] = {"file": [config_dir / f for f in files]}
            for f in result["input"]["file"]:
                logger.debug(f"Config input file: {f}")

    if "output" in raw:
        output_section = raw["output"]
        for key in output_section:
            if key not in KNOWN_OUTPUT_KEYS:
                logger.warning(f"Unknown config key in [output]: {key}")
        output_result: dict = {}
        if "path" in output_section:
            # Resolve output path relative to config file's directory
            output_result["path"] = path.parent / output_section["path"]
            logger.debug(f"Config output.path: {output_result['path']}")
        result["output"] = output_result

    if "python" in raw:
        python_section = raw["python"]
        for key in python_section:
            if key not in KNOWN_PYTHON_KEYS:
                logger.warning(f"Unknown config key in [python]: {key}")
        if "allow" in python_section:
            result["python"] = {"allow": bool(python_section["allow"])}
            logger.debug(f"Config python.allow: {result['python']['allow']}")

    return result
