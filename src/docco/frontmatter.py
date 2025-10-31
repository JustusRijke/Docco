"""Parse YAML frontmatter from markdown files."""

import re
import yaml


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        tuple: (metadata dict, body string)

    Raises:
        ValueError: If frontmatter YAML is invalid
    """
    # Check if content starts with frontmatter delimiter
    if not content.startswith("---"):
        return {}, content

    # Find the closing delimiter
    lines = content.split("\n")
    if len(lines) < 2:
        return {}, content

    # Find end of frontmatter
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        # No closing delimiter found
        return {}, content

    # Extract frontmatter and body
    frontmatter_str = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:])

    # Parse YAML
    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")

    return metadata, body
