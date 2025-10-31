"""Utilities for processing HTML comment directives with code block protection."""

import re


def extract_code_blocks(content):
    """
    Extract code blocks from content to prevent directive processing inside them.

    Handles both inline code (`...`) and fenced code blocks (```...```).

    Args:
        content: Markdown content

    Returns:
        tuple: (content_with_placeholders, code_blocks_dict)
    """
    code_blocks = {}
    counter = [0]

    def replace_fenced(match):
        original = match.group(0)
        # Store the code block content (strip the captured newlines from match)
        # We'll preserve them in the replacement
        has_leading_newline = original.startswith('\n')
        has_trailing_newline = original.endswith('\n')

        placeholder = f"___FENCED_CODE_BLOCK_{counter[0]}___"
        code_blocks[placeholder] = original.strip('\n')  # Store without the captured newlines
        counter[0] += 1

        # Preserve the structural newlines in the replacement
        result = placeholder
        if has_leading_newline:
            result = '\n' + result
        if has_trailing_newline:
            result = result + '\n'
        return result

    def replace_inline(match):
        placeholder = f"___INLINE_CODE_{counter[0]}___"
        code_blocks[placeholder] = match.group(0)
        counter[0] += 1
        return placeholder

    # First protect fenced code blocks (```...```)
    # Must start on a new line and end on a new line
    # Use DOTALL to match across newlines
    temp_content = re.sub(r'(?:^|\n)```.*?```(?:\n|$)', replace_fenced, content, flags=re.DOTALL | re.MULTILINE)

    # Then protect inline code
    # Markdown inline code: n backticks open, content (can contain < n backticks), n backticks close
    # Match 1, 2, 3, or 4+ backticks (handle common cases explicitly for correctness)
    temp_content = re.sub(r'````[^`]*````', replace_inline, temp_content)  # 4 backticks
    temp_content = re.sub(r'```(?!`).*?```(?!`)', replace_inline, temp_content)  # 3 backticks (not 4)
    temp_content = re.sub(r'``(?!`).*?``(?!`)', replace_inline, temp_content)  # 2 backticks (not 3)
    temp_content = re.sub(r'`(?!`).*?`(?!`)', replace_inline, temp_content)  # 1 backtick (not 2)

    return temp_content, code_blocks


def restore_code_blocks(content, code_blocks):
    """
    Restore code blocks that were extracted.

    Args:
        content: Content with placeholders
        code_blocks: Dict mapping placeholders to original code

    Returns:
        str: Content with code blocks restored
    """
    result = content
    for placeholder, original in code_blocks.items():
        result = result.replace(placeholder, original)
    return result


def build_md_directive_pattern(directive_spec):
    """
    Build regex pattern for markdown directive.

    Args:
        directive_spec: Directive-specific pattern part (after <!--)

    Returns:
        str: Complete regex pattern
    """
    return r'<!--\s*' + directive_spec


def build_html_directive_pattern(directive_spec):
    """
    Build regex pattern for HTML directive (requires re.MULTILINE flag).

    Note: HTML directives still require line-start for proper HTML structure.

    Args:
        directive_spec: Directive-specific pattern part (after <!--)

    Returns:
        str: Complete regex pattern with line-start anchor
    """
    return r'^\s*<!--\s*' + directive_spec
