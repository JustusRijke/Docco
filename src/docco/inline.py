"""Process inline markdown file directives."""

import os
import re
import io
import sys
from docco.core import setup_logger
from docco.directive_utils import (
    build_md_directive_pattern,
    extract_code_blocks,
    restore_code_blocks,
)

logger = setup_logger(__name__)


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
    pattern = build_md_directive_pattern(r'inline\s*:\s*"([^"]+)"(.*?)-->')
    # Pattern to match python directives
    python_pattern = build_md_directive_pattern(
        r"python\s*-->(.*?)<!--\s*/python\s*-->"
    )

    def replace_inline(match):
        filepath = match.group(1)
        args_str = match.group(2).strip()

        # Resolve file path relative to base_dir
        full_path = os.path.join(base_dir, filepath)

        # Check if file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Inline file not found: {filepath}")

        # Read file content
        with open(full_path, "r") as f:
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

        return output

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
