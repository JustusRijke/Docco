"""Parse YAML frontmatter from markdown files."""

import frontmatter


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
    try:
        post = frontmatter.loads(content)
        return post.metadata, post.content
    except Exception as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}")
