"""
Inline directive processing for markdown documents.

Allows users to define reusable markdown templates invoked via HTML comment syntax.
"""

import re
from pathlib import Path


class InlineProcessor:
    """
    Processes inline directives in markdown content.

    Inline syntax:
    - Block: <!-- inline: name arg="val" -->content<!-- /inline -->
    - Self-closing: <!-- inline: name arg="val" /-->

    Templates are markdown files in inlines/ folder with {{variable}} placeholders.
    Supports recursive inlining with depth limit to prevent infinite recursion.
    """

    def __init__(self, base_dir: Path, max_depth: int = 10):
        """
        Initialize inline processor.

        Args:
            base_dir: Directory to search for inlines/ folder
            max_depth: Maximum recursion depth for nested inlines
        """
        self.base_dir = base_dir
        self.inlines_dir = base_dir / "inlines"
        self._template_cache = {}
        self.max_depth = max_depth

    def process(self, content: str) -> str:
        """
        Process all inline directives in content.

        Args:
            content: Markdown content with inline directives

        Returns:
            Content with inlines expanded
        """
        return self._process_recursive(content, depth=0)

    def _process_recursive(self, content: str, depth: int) -> str:
        """
        Recursively process inline directives.

        Args:
            content: Content to process
            depth: Current recursion depth

        Returns:
            Content with inlines expanded
        """
        if depth >= self.max_depth:
            return content

        # Pattern for self-closing inlines: <!-- inline: name arg="val" /-->
        self_closing_pattern = re.compile(
            r'<!--\s*inline:\s*(\w+)\s*(.*?)\s*/-->',
            re.DOTALL
        )

        # Pattern for block inlines: <!-- inline: name arg="val" -->...<!-- /inline -->
        block_pattern = re.compile(
            r'<!--\s*inline:\s*(\w+)\s*(.*?)-->(.*?)<!--\s*/inline\s*-->',
            re.DOTALL
        )

        # Process block inlines first (they may contain self-closing inlines)
        def expand_block(match: re.Match) -> str:
            inline_name = match.group(1)
            args_str = match.group(2)
            content_inner = match.group(3).strip()

            args = self._parse_args(args_str)
            args['content'] = content_inner

            return self._render_inline(inline_name, args, match.group(0), depth + 1)

        def expand_self_closing(match: re.Match) -> str:
            inline_name = match.group(1)
            args_str = match.group(2)

            args = self._parse_args(args_str)

            return self._render_inline(inline_name, args, match.group(0), depth + 1)

        content = block_pattern.sub(expand_block, content)
        content = self_closing_pattern.sub(expand_self_closing, content)

        # Check if there are more inlines to process
        if block_pattern.search(content) or self_closing_pattern.search(content):
            return self._process_recursive(content, depth + 1)

        return content

    def _parse_args(self, args_str: str) -> dict:
        """
        Parse command arguments from attribute-style string.

        Args:
            args_str: String like 'icon="idea.svg" type="info"'

        Returns:
            Dictionary of argument names to values
        """
        args = {}

        # Pattern: arg="value" or arg='value'
        arg_pattern = re.compile(r'(\w+)=(["\'])(.*?)\2')

        for match in arg_pattern.finditer(args_str):
            arg_name = match.group(1)
            arg_value = match.group(3)
            args[arg_name] = arg_value

        return args

    def _render_inline(self, inline_name: str, args: dict, original: str, depth: int) -> str:
        """
        Render an inline by loading template and substituting variables.

        Args:
            inline_name: Name of inline (corresponds to template file)
            args: Dictionary of arguments
            original: Original inline text (returned if rendering fails)
            depth: Current recursion depth

        Returns:
            Rendered markdown or original text if error
        """
        template = self._load_template(inline_name)

        if template is None:
            # Template not found - leave inline unexpanded
            return original

        # Substitute variables: {{var}} → args['var']
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            return args.get(var_name, '')

        var_pattern = re.compile(r'\{\{(\w+)\}\}')
        rendered = var_pattern.sub(replace_var, template)

        # Process nested inlines recursively
        if depth < self.max_depth:
            rendered = self._process_recursive(rendered, depth)

        return rendered

    def _load_template(self, inline_name: str) -> str | None:
        """
        Load inline template from inlines/ folder.

        Args:
            inline_name: Name of inline

        Returns:
            Template content or None if not found
        """
        # Check cache first
        if inline_name in self._template_cache:
            return self._template_cache[inline_name]

        # Look for template file
        template_path = self.inlines_dir / f"{inline_name}.md"

        if not template_path.exists():
            return None

        try:
            template = template_path.read_text(encoding='utf-8')
            self._template_cache[inline_name] = template
            return template
        except Exception:
            return None


# Backward compatibility: keep old class name as alias
CommandProcessor = InlineProcessor
