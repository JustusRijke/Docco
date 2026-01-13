"""Process inline markdown file directives."""

import io
import logging
import os
import re
import sys

logger = logging.getLogger(__name__)


def extract_code_blocks(content: str) -> tuple[str, dict[str, str]]:
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

    def replace_fenced(match: re.Match[str]) -> str:
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

    def replace_inline(match: re.Match[str]) -> str:
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


def restore_code_blocks(content: str, code_blocks: dict[str, str]) -> str:
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


def process_inlines(
    content: str, base_dir: str = ".", allow_python: bool = False
) -> str:
    """
    Process inline directives with file-type aware post-processing.

    Syntax: <!-- inline:"path/to/file" arg1="value1" arg2="value2" -->

    File types:
    - .md: No post-processing
    - .html: Trim all lines
    - .py: Execute file (requires allow_python=True), arguments via sys.argv
    - other: Insert as-is with warning

    Args:
        content: Markdown content to process
        base_dir: Base directory for resolving relative paths
        allow_python: Allow python file execution

    Returns:
        str: Content with inlines processed

    Raises:
        ValueError: If python file execution not allowed or execution error
        FileNotFoundError: If inline file not found
    """
    # Protect code blocks from directive processing
    protected_content, code_blocks = extract_code_blocks(content)

    # Pattern to match inline directives
    pattern = r'<!--\s*inline\s*:\s*"([^"]+)"(.*?)-->'

    def replace_inline(match: re.Match[str]) -> str:
        filepath = match.group(1)
        args_str = match.group(2).strip()

        # Resolve file path relative to base_dir
        full_path = os.path.join(base_dir, filepath)

        # Check if file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Inline file not found: {filepath}")

        # Parse arguments from the directive
        args = parse_inline_args(args_str)

        # Determine file type
        file_type = get_file_type(full_path)

        logger.debug(f"Inlining: {filepath}")

        if file_type == ".py":
            # For Python files: execute directly (arguments via sys.argv)
            return execute_python_file(full_path, base_dir, allow_python, args)
        else:
            # For other files: read content
            with open(full_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Find all placeholders in the file
            placeholders = find_placeholders(file_content)

            # Replace placeholders with argument values
            used_args = set()
            for key, value in args.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in file_content:
                    used_args.add(key)
                    file_content = file_content.replace(placeholder, value)

            # Warn about unused arguments
            unused_args = set(args.keys()) - used_args
            if unused_args:
                logger.warning(
                    f"Unused arguments in inline directive for {filepath}: {', '.join(sorted(unused_args))}"
                )

            # Warn about unfulfilled placeholders
            unfulfilled = placeholders - used_args
            if unfulfilled:
                logger.warning(
                    f"Unfulfilled placeholders in {filepath}: {', '.join(sorted(unfulfilled))}"
                )

            # Apply file-type specific post-processing
            return post_process_content(
                file_content, full_path, base_dir, allow_python, args
            )

    # Process inline directives
    result = re.sub(pattern, replace_inline, protected_content)

    # Restore code blocks
    result = restore_code_blocks(result, code_blocks)

    return result


def find_placeholders(content: str) -> set[str]:
    """
    Find all placeholder patterns in content.

    Args:
        content: File content to scan

    Returns:
        set: Set of placeholder names (e.g., {'name', 'value'})
    """
    pattern = r"\{\{(\w+)\}\}"
    matches = re.findall(pattern, content)
    return set(matches)


def parse_inline_args(args_str: str) -> dict[str, str]:
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


def get_file_type(filepath: str) -> str:
    """Extract file extension from filepath."""
    return os.path.splitext(filepath)[1].lower()


def trim_html_lines(content: str) -> str:
    """Trim leading/trailing whitespace from all lines, preserve empty lines."""
    lines = content.split("\n")
    trimmed = [line.strip() for line in lines]
    return "\n".join(trimmed)


def execute_python_file(
    filepath: str, base_dir: str, allow_python: bool, args_dict: dict[str, str]
) -> str:
    """Execute Python file and return stdout."""
    if not allow_python:
        raise ValueError(
            f"Python file execution not allowed: {filepath}. Use --allow-python flag."
        )

    # Build sys.argv list
    argv_list = [filepath]
    for key, value in args_dict.items():
        argv_list.append(f"--{key}={value}")

    logger.debug(f"Executing Python file: {filepath} with args: {args_dict}")

    # Save current sys.argv
    old_argv = sys.argv
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # Set sys.argv
        sys.argv = argv_list

        # Read and execute the file
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        exec(code, {"__file__": filepath})
        output = sys.stdout.getvalue()
    except Exception as e:
        raise ValueError(f"Python execution error in {filepath}: {e}")
    finally:
        # Restore sys.argv and stdout
        sys.argv = old_argv
        sys.stdout = old_stdout

    return output.strip()


def post_process_content(
    content: str,
    file_path: str,
    base_dir: str,
    allow_python: bool,
    args_dict: dict[str, str],
) -> str:
    """Apply file-type specific post-processing for non-Python files."""
    file_type = get_file_type(file_path)

    if file_type == ".md":
        return content
    elif file_type == ".html":
        return trim_html_lines(content)
    else:
        logger.warning(
            f"Unknown file type '{file_type}' for {file_path}, inserting as-is"
        )
        return content
