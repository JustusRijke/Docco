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

    def load_templates(self) -> tuple[str | None, str | None]:
        """
        Load header.html and footer.html from the markdown file's directory.

        Returns:
            Tuple of (header_html, footer_html) where each is None if file doesn't exist
        """
        header_path = self.base_dir / "header.html"
        footer_path = self.base_dir / "footer.html"

        header_html = header_path.read_text(encoding="utf-8") if header_path.exists() else None
        footer_html = footer_path.read_text(encoding="utf-8") if footer_path.exists() else None

        return header_html, footer_html

    def replace_variables(self, template: str, metadata: dict) -> str:
        """
        Replace {{variables}} in template with values from metadata.

        Supported variables:
        - {{filename}} - markdown filename without extension
        - {{title}} - from frontmatter
        - {{subtitle}} - from frontmatter
        - {{date}} - from frontmatter
        - {{author}} - from frontmatter

        Args:
            template: HTML template string
            metadata: Dictionary with frontmatter values

        Returns:
            Template with variables replaced
        """
        # Build variable context
        context = {
            "filename": self.filename,
            "title": str(metadata.get("title", "")),
            "subtitle": str(metadata.get("subtitle", "")),
            "date": str(metadata.get("date", "")),
            "author": str(metadata.get("author", "")),
        }

        # Replace {{variable}} with values
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", value)

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


def modify_css_for_running_elements(css: str, has_header: bool, has_footer: bool) -> tuple[str, list[str]]:
    """
    Modify CSS to use element(header) and element(footer) in @page rules.

    Detects existing @page content rules and replaces/warns about conflicts.

    Args:
        css: Original CSS content
        has_header: Whether header.html exists
        has_footer: Whether footer.html exists

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

        # Skip @page :first - title page should have no headers/footers
        if ":first" in page_selector:
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
