"""
Language filtering for multilingual markdown documents.

Filters content based on language tags to generate language-specific PDFs.
"""

import re


class LanguageFilter:
    """
    Filters markdown content by language tags.

    Language tag syntax:
    - Block: <!-- lang:NL -->content<!-- /lang -->

    Untagged content is included in all language outputs.
    Tagged content is only included for matching languages.
    """

    def filter_for_language(self, content: str, language: str) -> str:
        """
        Filter markdown content for a specific language.

        Keeps:
        - Untagged content (appears in all languages)
        - Content tagged with the target language

        Removes:
        - Content tagged with other languages

        Args:
            content: Markdown content with language tags
            language: Target language code (e.g., "NL", "EN", "DE")

        Returns:
            Filtered markdown content
        """
        # Pattern for language blocks: <!-- lang:XX -->...<!-- /lang -->
        lang_pattern = re.compile(
            r'<!--\s*lang:(\w+)\s*-->(.*?)<!--\s*/lang\s*-->',
            re.DOTALL
        )

        def replace_lang_block(match: re.Match) -> str:
            block_lang = match.group(1)
            block_content = match.group(2)

            # Keep block if language matches, otherwise remove
            if block_lang == language:
                return block_content
            else:
                return ''

        # Replace all language blocks
        filtered = lang_pattern.sub(replace_lang_block, content)

        return filtered
