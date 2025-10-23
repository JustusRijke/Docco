"""
Section data model and automatic numbering logic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


class Orientation(str, Enum):
    """Page orientation options for sections."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class Section:
    """
    Represents a document section with hierarchical numbering.

    Attributes:
        level: Heading level (1-3 for regular sections, 0 for addendums)
        title: Section title
        content: Markdown content
        number: Auto-generated section number (e.g., "1.2.3" or "A")
        orientation: Page orientation (Orientation.PORTRAIT or Orientation.LANDSCAPE)
    """

    level: int
    title: str
    content: str
    number: Optional[str] = None
    orientation: Union[Orientation, str] = Orientation.PORTRAIT

    def __post_init__(self):
        """Validate section attributes."""
        if self.level < 0 or self.level > 3:
            raise ValueError(f"Section level must be 0-3, got {self.level}")
        if not self.title:
            raise ValueError("Section title cannot be empty")
        # Convert string to Orientation if needed (for backward compatibility)
        if isinstance(self.orientation, str):
            try:
                self.orientation = Orientation(self.orientation)
            except ValueError:
                raise ValueError(
                    f"Orientation must be Orientation.PORTRAIT or Orientation.LANDSCAPE, got {self.orientation}"
                )


class SectionNumberer:
    """
    Manages hierarchical section numbering.

    Supports:
    - Hierarchical numbering: 1, 1.1, 1.1.1, 1.1.2, 1.2, 2
    - Addendum lettering: A, B, C (for level=0)
    """

    def __init__(self):
        """Initialize counters for hierarchical numbering."""
        self.counters = [0, 0, 0]  # Support up to 3 levels
        self.addendum_counter = 0  # For A, B, C, etc.

    def number_section(self, section: Section) -> str:
        """
        Generate section number based on level and update internal counters.

        Args:
            section: Section to number

        Returns:
            Section number string (e.g., "1.2", "2.1.3", or "A")
        """
        if section.level == 0:
            # Addendum sections use letters
            self.addendum_counter += 1
            return chr(64 + self.addendum_counter)  # A=65, B=66, etc.

        # Increment counter at current level
        level_idx = section.level - 1
        self.counters[level_idx] += 1

        # Reset deeper level counters
        for i in range(level_idx + 1, len(self.counters)):
            self.counters[i] = 0

        # Generate number string (e.g., "1.2.3")
        number_parts = [str(c) for c in self.counters[: section.level] if c > 0]
        return ".".join(number_parts)

    def number_sections(self, sections: list[Section]) -> list[Section]:
        """
        Number a list of sections in place and return the list.

        Args:
            sections: List of sections to number

        Returns:
            Same list with section.number populated
        """
        for section in sections:
            section.number = self.number_section(section)
        return sections

    def reset(self):
        """Reset all counters to initial state."""
        self.counters = [0, 0, 0]
        self.addendum_counter = 0
