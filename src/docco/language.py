"""Split markdown content by language."""

import re
from docco.utils import setup_logger
from docco.directive_utils import build_md_directive_pattern, extract_code_blocks, restore_code_blocks

logger = setup_logger(__name__)


def split_by_language(content, metadata):
    """
    Split markdown content by language tags.

    If no languages in metadata, returns single output.
    Otherwise filters content by language tags.

    Language tag format:
    <!-- lang:EN -->
    Content for EN
    <!-- /lang -->

    Args:
        content: Markdown content to process
        metadata: Document metadata (contains 'languages' if multilingual)

    Returns:
        dict: {language_code: filtered_content, ...}
              or {None: content} if no languages
    """
    # Check if multilingual
    languages_str = metadata.get("languages", "")
    if not languages_str:
        logger.info("No languages tag found, treating as single language")
        return {None: content}

    # Parse languages
    languages = languages_str.split()
    logger.info(f"Processing languages: {languages}")

    results = {}
    for lang in languages:
        filtered = filter_content_by_language(content, lang)
        results[lang] = filtered
        logger.info(f"Filtered content for {lang}")

    return results


def filter_content_by_language(content, target_lang):
    """
    Filter content for specific language.

    Removes language blocks for other languages.
    Removes the lang tags but keeps the content for matching language.

    Args:
        content: Full content
        target_lang: Language code to keep

    Returns:
        str: Filtered content
    """
    # Protect code blocks from directive processing
    protected_content, code_blocks = extract_code_blocks(content)

    # Pattern to match language blocks
    pattern = build_md_directive_pattern(r'lang:(\w+)\s*-->(.*?)<!--\s*/lang\s*-->')

    def replace_lang_block(match):
        lang = match.group(1)
        body = match.group(2)

        if lang == target_lang:
            return body
        else:
            return ''

    # Use DOTALL flag to match across newlines
    result = re.sub(pattern, replace_lang_block, protected_content, flags=re.DOTALL)

    # Restore code blocks
    result = restore_code_blocks(result, code_blocks)

    # Clean up multiple consecutive newlines
    result = re.sub(r'\n\n\n+', '\n\n', result)

    return result.strip() + "\n" if result.strip() else ""
