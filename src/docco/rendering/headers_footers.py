"""
Header and footer template system for PDF documents.
"""

from pathlib import Path
import re


class HeaderFooterProcessor:
    """Processes header.html and footer.html templates with variable replacements."""

    def __init__(self, markdown_file_path: Path):
        """
        Initialize processor.

        Args:
            markdown_file_path: Path to the markdown file (determines where to look for header/footer files)
        """
        self.base_dir = markdown_file_path.parent
        self.filename = markdown_file_path.stem  # filename without extension

    def load_templates(self, language: str | None = None) -> tuple[str | None, str | None]:
        """
        Load header.html and footer.html from the markdown file's directory.

        Supports language-specific templates:
        - If language is provided, tries header.{language}.html first, then header.html
        - Same for footer templates

        Args:
            language: Optional language code (e.g., "EN", "NL", "DE")

        Returns:
            Tuple of (header_html, footer_html) where each is None if file doesn't exist
        """
        def load_template(base_name: str) -> str | None:
            if language:
                # Try language-specific file first
                lang_path = self.base_dir / f"{base_name}.{language}.html"
                if lang_path.exists():
                    return lang_path.read_text(encoding="utf-8")

            # Fall back to generic file
            generic_path = self.base_dir / f"{base_name}.html"
            return generic_path.read_text(encoding="utf-8") if generic_path.exists() else None

        header_html = load_template("header")
        footer_html = load_template("footer")

        return header_html, footer_html

    def replace_variables(self, template: str, language: str | None = None) -> str:
        """
        Replace {{variables}} in template with values.

        Supported variables:
        - {{filename}} - markdown filename without extension
        - {{language}} - language code (if provided)

        Args:
            template: HTML template string
            language: Optional language code

        Returns:
            Template with variables replaced
        """
        result = template.replace("{{filename}}", self.filename)
        if language:
            result = result.replace("{{language}}", language)
        else:
            result = result.replace("{{language}}", "")
        return result

    def inject_running_elements(self, html: str, header_content: str | None, footer_content: str | None) -> str:
        """
        Inject running header/footer elements into HTML document.

        Running elements use CSS position: running() to appear in @page margins.

        Args:
            html: Complete HTML document
            header_content: Processed header HTML (or None)
            footer_content: Processed footer HTML (or None)

        Returns:
            HTML with running elements injected after <body> tag
        """
        running_elements = []

        if header_content:
            running_elements.append(
                f'<div id="header-running" style="position: running(header);">{header_content}</div>'
            )

        if footer_content:
            running_elements.append(
                f'<div id="footer-running" style="position: running(footer);">{footer_content}</div>'
            )

        if not running_elements:
            return html

        # Inject after <body> tag
        running_html = "\n".join(running_elements)
        return html.replace("<body>", f"<body>\n{running_html}\n", 1)


def modify_css_for_running_elements(css: str, has_header: bool, has_footer: bool, no_headers_first_page: bool = True) -> tuple[str, list[str]]:
    """
    Modify CSS to use element(header) and element(footer) in @page rules.

    Detects existing @page content rules and replaces/warns about conflicts.

    Args:
        css: Original CSS content
        has_header: Whether header.html exists
        has_footer: Whether footer.html exists
        no_headers_first_page: Whether to skip headers/footers on first page (default: True)

    Returns:
        Tuple of (modified_css, warnings_list)
    """
    warnings = []

    if not has_header and not has_footer:
        return css, warnings

    # Parse @page blocks
    page_blocks = list(re.finditer(r'@page\s+([^{]*)\{', css))

    modified_css = css

    for match in reversed(page_blocks):  # Reverse to preserve positions
        page_selector = match.group(1).strip()  # e.g., "", "landscape", ":first"

        # Skip @page :first if no_headers_first_page is enabled
        if no_headers_first_page and ":first" in page_selector:
            continue

        block_start = match.end()

        # Find matching closing brace
        brace_count = 1
        pos = block_start
        block_end = None
        while pos < len(css) and brace_count > 0:
            if css[pos] == '{':
                brace_count += 1
            elif css[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    block_end = pos
                    break
            pos += 1

        if block_end is None:
            continue

        block_content = css[block_start:block_end]

        # Check for existing @top-center or @bottom-right with content
        has_top_content = bool(re.search(r'@top-center\s*\{[^}]*content\s*:', block_content))
        has_bottom_content = bool(re.search(r'@bottom-right\s*\{[^}]*content\s*:', block_content))

        # Warn about conflicts
        if has_header and has_top_content:
            warnings.append(
                f"Warning: @page {page_selector or '(default)'} already has @top-center content. "
                "Replacing with header.html"
            )

        if has_footer and has_bottom_content:
            warnings.append(
                f"Warning: @page {page_selector or '(default)'} already has @bottom-right content. "
                "Replacing with footer.html"
            )

        # Remove existing @top-center and @bottom-right blocks if we're replacing them
        new_block_content = block_content
        if has_header:
            new_block_content = re.sub(r'@top-center\s*\{[^}]*\}', '', new_block_content)
        if has_footer:
            new_block_content = re.sub(r'@bottom-right\s*\{[^}]*\}', '', new_block_content)

        # Inject new margin rules
        injections = []
        if has_header:
            injections.append("    @top-center { content: element(header); }")
        if has_footer:
            injections.append("    @bottom-right { content: element(footer); }")

        if injections:
            new_block_content = "\n".join(injections) + "\n" + new_block_content

        # Replace block content
        modified_css = modified_css[:block_start] + new_block_content + modified_css[block_end:]

    return modified_css, warnings
