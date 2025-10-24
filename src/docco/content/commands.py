"""
Custom command processing for markdown documents.

Allows users to define reusable HTML templates invoked via HTML comment syntax.
"""

import re
from pathlib import Path


class CommandProcessor:
    """
    Processes custom commands in markdown content.

    Commands syntax:
    - Block: <!-- cmd: name arg="val" -->content<!-- /cmd -->
    - Self-closing: <!-- cmd: name arg="val" /-->

    Templates are HTML files in commands/ folder with {{variable}} placeholders.
    """

    def __init__(self, base_dir: Path):
        """
        Initialize command processor.

        Args:
            base_dir: Directory to search for commands/ folder
        """
        self.base_dir = base_dir
        self.commands_dir = base_dir / "commands"
        self._template_cache = {}

    def process(self, content: str) -> str:
        """
        Process all custom commands in content.

        Args:
            content: Markdown content with command directives

        Returns:
            Content with commands expanded to HTML
        """
        # Pattern for self-closing commands: <!-- cmd: name arg="val" /-->
        self_closing_pattern = re.compile(
            r'<!--\s*cmd:\s*(\w+)\s*(.*?)\s*/-->',
            re.DOTALL
        )

        # Pattern for block commands: <!-- cmd: name arg="val" -->...<!-- /cmd -->
        block_pattern = re.compile(
            r'<!--\s*cmd:\s*(\w+)\s*(.*?)-->(.*?)<!--\s*/cmd\s*-->',
            re.DOTALL
        )

        # Process block commands first (they may contain self-closing commands)
        content = block_pattern.sub(self._expand_block_command, content)

        # Process self-closing commands
        content = self_closing_pattern.sub(self._expand_self_closing_command, content)

        return content

    def _expand_block_command(self, match: re.Match) -> str:
        """Expand a block-style command."""
        command_name = match.group(1)
        args_str = match.group(2)
        content = match.group(3).strip()

        args = self._parse_args(args_str)
        args['content'] = content

        return self._render_command(command_name, args, match.group(0))

    def _expand_self_closing_command(self, match: re.Match) -> str:
        """Expand a self-closing command."""
        command_name = match.group(1)
        args_str = match.group(2)

        args = self._parse_args(args_str)

        return self._render_command(command_name, args, match.group(0))

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

    def _render_command(self, command_name: str, args: dict, original: str) -> str:
        """
        Render a command by loading template and substituting variables.

        Args:
            command_name: Name of command (corresponds to template file)
            args: Dictionary of arguments
            original: Original command text (returned if rendering fails)

        Returns:
            Rendered HTML or original text if error
        """
        template = self._load_template(command_name)

        if template is None:
            # Template not found - leave command unexpanded
            return original

        # Substitute variables: {{var}} → args['var']
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            return args.get(var_name, '')

        var_pattern = re.compile(r'\{\{(\w+)\}\}')
        rendered = var_pattern.sub(replace_var, template)

        return rendered

    def _load_template(self, command_name: str) -> str | None:
        """
        Load command template from commands/ folder.

        Args:
            command_name: Name of command

        Returns:
            Template content or None if not found
        """
        # Check cache first
        if command_name in self._template_cache:
            return self._template_cache[command_name]

        # Look for template file
        template_path = self.commands_dir / f"{command_name}.html"

        if not template_path.exists():
            return None

        try:
            template = template_path.read_text(encoding='utf-8')
            self._template_cache[command_name] = template
            return template
        except Exception:
            return None
