"""Process header and footer HTML files with directive support."""

import os
from docco.utils import setup_logger

logger = setup_logger(__name__)


def process_header_footer(config, base_dir, allow_python=False, directive_processor=None):
    """
    Process header or footer HTML file with placeholder and directive support.

    Args:
        config: Dict with 'file' key and optional placeholder arguments
                Example: {file: "footer.html", title: "My Doc", author: "Jane"}
        base_dir: Base directory for resolving file path
        allow_python: Allow python directive execution
        directive_processor: Function to process directives (for DRY with main content)

    Returns:
        str: Processed HTML content

    Raises:
        ValueError: If 'file' key missing or config invalid
        FileNotFoundError: If file not found
    """
    if not config or not isinstance(config, dict):
        raise ValueError("Header/footer config must be a dict")

    if 'file' not in config:
        raise ValueError("Header/footer config must contain 'file' key")

    filepath = config['file']
    full_path = os.path.join(base_dir, filepath)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Header/footer file not found: {filepath}")

    # Read file content
    with open(full_path, "r") as f:
        content = f.read()

    logger.info(f"Processing header/footer: {filepath}")

    # Replace placeholders with config values (excluding 'file' key)
    for key, value in config.items():
        if key != 'file':
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

    # Process directives using the same pipeline as main content
    if directive_processor:
        content = directive_processor(content, base_dir, allow_python)

    return content
