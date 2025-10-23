"""
Markdown file parser for document generation.

Parses markdown files with HTML comment directives to create structured documents.
"""

import re
from pathlib import Path
from typing import Union
from docco.core.section import Section, Orientation


class MarkdownDocumentParser:
    """
    Parse markdown files into Section objects.

    Supports HTML comment directives:
    - <!-- landscape --> : Next section uses landscape orientation
    - <!-- portrait --> : Next section uses portrait orientation
    - <!-- addendum --> : Next section is an appendix (level 0)
    - <!-- notoc --> : Next section excluded from table of contents
    - <!-- pagebreak --> : Insert explicit page break (not yet implemented)

    Example:
        parser = MarkdownDocumentParser()
        sections = parser.parse_file("content.md")
    """

    # Regex patterns
    HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    DIRECTIVE_PATTERN = re.compile(r"<!--\s*(\w+)\s*-->")

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse_file(self, file_path: Union[Path, str]) -> list[Section]:
        """
        Parse a markdown file into Section objects.

        Args:
            file_path: Path to markdown file

        Returns:
            List of Section objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If markdown is malformed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        return self.parse_string(content)

    def _is_in_code_block(self, text: str, position: int) -> bool:
        """Check if a position in text is inside a code block."""
        # Find all code block boundaries before this position
        code_block_pattern = re.compile(r"```")
        matches = list(code_block_pattern.finditer(text[:position]))
        # If odd number of ``` before position, we're inside a code block
        return len(matches) % 2 == 1

    def parse_string(self, markdown_content: str) -> list[Section]:
        """
        Parse markdown string into Section objects.

        Args:
            markdown_content: Markdown text

        Returns:
            List of Section objects
        """
        sections = []

        # Find all headings with their positions
        all_headings = list(self.HEADING_PATTERN.finditer(markdown_content))

        # Filter out headings inside code blocks
        headings = [h for h in all_headings if not self._is_in_code_block(markdown_content, h.start())]

        if not headings:
            # No headings found - return empty list
            return sections

        # Process each heading
        for i, heading_match in enumerate(headings):
            # Extract heading info
            heading_level = len(heading_match.group(1))  # Count # symbols
            heading_title = heading_match.group(2).strip()
            heading_start = heading_match.start()

            # Determine content range (from this heading to next or end)
            if i < len(headings) - 1:
                content_end = headings[i + 1].start()
            else:
                content_end = len(markdown_content)

            # Extract content (everything after heading line until next heading)
            heading_end = markdown_content.find("\n", heading_start)
            if heading_end == -1:
                heading_end = heading_start + len(heading_match.group(0))

            section_content = markdown_content[heading_end + 1:content_end].strip()

            # Look for directives BEFORE this heading
            # Only look in the text between previous heading's content end and this heading
            # This prevents picking up directives from earlier in the document
            directives_start = headings[i - 1].end() if i > 0 else 0
            directives_end = heading_start
            directives_text = markdown_content[directives_start:directives_end]

            # Only consider directives that appear after the last newline before this heading
            # This ensures we only get directives immediately before the heading
            last_section_content_end = directives_text.rfind('\n\n')
            if last_section_content_end != -1:
                directives_text = directives_text[last_section_content_end:]

            # Parse directives
            orientation = Orientation.PORTRAIT
            is_addendum = False
            exclude_from_toc = False

            directive_matches = self.DIRECTIVE_PATTERN.findall(directives_text)
            for directive in directive_matches:
                directive_lower = directive.lower()
                if directive_lower == "landscape":
                    orientation = Orientation.LANDSCAPE
                elif directive_lower == "portrait":
                    orientation = Orientation.PORTRAIT
                elif directive_lower == "addendum":
                    is_addendum = True
                elif directive_lower == "notoc":
                    exclude_from_toc = True
                # pagebreak directive would be handled here in future

            # Determine section level
            level = 0 if is_addendum else heading_level

            # Create section
            section = Section(
                level=level,
                title=heading_title,
                content=section_content,
                orientation=orientation,
                exclude_from_toc=exclude_from_toc
            )

            sections.append(section)

        return sections
