"""Process inline markdown file directives."""

import os
import re
import io
import sys
import logging

logger = logging.getLogger(__name__)


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
        has_leading_newline = original.startswith("\n")
        has_trailing_newline = original.endswith("\n")

        placeholder = f"___FENCED_CODE_BLOCK_{counter[0]}___"
        code_blocks[placeholder] = original.strip(
            "\n"
        )  # Store without the captured newlines
        counter[0] += 1

        # Preserve the structural newlines in the replacement
        result = placeholder
        if has_leading_newline:
            result = "\n" + result
        if has_trailing_newline:
            result = result + "\n"
        return result

    def replace_inline(match):
        placeholder = f"___INLINE_CODE_{counter[0]}___"
        code_blocks[placeholder] = match.group(0)
        counter[0] += 1
        return placeholder

    # First protect fenced code blocks (```...```)
    # Must start on a new line and end on a new line
    # Use DOTALL to match across newlines
    temp_content = re.sub(
        r"(?:^|\n)```.*?```(?:\n|$)",
        replace_fenced,
        content,
        flags=re.DOTALL | re.MULTILINE,
    )

    # Then protect inline code
    # Markdown inline code: n backticks open, content (can contain < n backticks), n backticks close
    # Match 1, 2, 3, or 4+ backticks (handle common cases explicitly for correctness)
    temp_content = re.sub(r"````[^`]*````", replace_inline, temp_content)  # 4 backticks
    temp_content = re.sub(
        r"```(?!`).*?```(?!`)", replace_inline, temp_content
    )  # 3 backticks (not 4)
    temp_content = re.sub(
        r"``(?!`).*?``(?!`)", replace_inline, temp_content
    )  # 2 backticks (not 3)
    temp_content = re.sub(
        r"`(?!`).*?`(?!`)", replace_inline, temp_content
    )  # 1 backtick (not 2)

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


def process_inlines(content, base_dir=".", allow_python=False):
    """
    Process inline and python directives (one pass).

    Syntax: <!-- inline:"path/to/file.md" arg1="value1" arg2="value2" -->
    Syntax: <!-- python -->code<!-- /python -->

    Args:
        content: Markdown content to process
        base_dir: Base directory for resolving relative paths
        allow_python: Allow python code execution

    Returns:
        str: Content with inlines processed

    Raises:
        ValueError: If python not allowed or execution error
        FileNotFoundError: If inline file not found
    """
    # Protect code blocks from directive processing
    protected_content, code_blocks = extract_code_blocks(content)

    # Pattern to match inline directives
    pattern = r'<!--\s*inline\s*:\s*"([^"]+)"(.*?)-->'
    # Pattern to match python directives
    python_pattern = r"<!--\s*python\s*-->(.*?)<!--\s*/python\s*-->"

    def replace_inline(match):
        filepath = match.group(1)
        args_str = match.group(2).strip()

        # Resolve file path relative to base_dir
        full_path = os.path.join(base_dir, filepath)

        # Check if file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Inline file not found: {filepath}")

        # Read file content
        with open(full_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        logger.debug(f"Inlining: {filepath}")

        # Parse arguments from the directive
        args = parse_inline_args(args_str)

        # Replace placeholders with argument values
        for key, value in args.items():
            placeholder = f"{{{{{key}}}}}"
            file_content = file_content.replace(placeholder, value)

        return file_content

    def replace_python(match):
        code = match.group(1)
        logger.debug(f"Executing python code: {repr(code[:100])}")

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            exec(code)
            output = sys.stdout.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            raise ValueError(f"Python execution error: {e}\nCode: {repr(code[:200])}")
        finally:
            sys.stdout = old_stdout

        return output.strip()

    # Check if python directives exist when not allowed
    if not allow_python and re.search(
        python_pattern, protected_content, flags=re.DOTALL
    ):
        raise ValueError("Python code execution not allowed. Use --allow-python flag.")

    # Process python directives
    if allow_python:
        result = re.sub(
            python_pattern, replace_python, protected_content, flags=re.DOTALL
        )
    else:
        result = protected_content

    # Then process inline directives
    result = re.sub(pattern, replace_inline, result)

    # Restore code blocks
    result = restore_code_blocks(result, code_blocks)

    return result


def parse_inline_args(args_str):
    """
    Parse arguments from inline directive.

    Format: key1="value1" key2="value2"

    Args:
        args_str: Arguments string from directive

    Returns:
        dict: Parsed arguments
    """
    args = {}
    # Pattern to match key="value" pairs
    pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(pattern, args_str)
    for key, value in matches:
        args[key] = value
    return args
