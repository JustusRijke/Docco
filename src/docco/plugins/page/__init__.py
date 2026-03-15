import re
from enum import StrEnum
from pathlib import Path

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage

_LANDSCAPE_HANDLER_JS = (
    Path(__file__).parent / "scripts" / "landscape_handler.js"
).read_text(encoding="utf-8")

_PAGEDJS_SCREEN_CSS = (
    Path(__file__).parent / "styles" / "pagedjs_screen.css"
).read_text(encoding="utf-8")

_PAGE_CSS = (Path(__file__).parent / "styles" / "page.css").read_text(encoding="utf-8")

_BODY_RE = re.compile(r"(<body[^>]*>)(.*?)(</body>)", re.DOTALL)


class Arg(StrEnum):
    BREAK = "break"
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


def _orientation(attrs: dict) -> str | None:
    if Arg.LANDSCAPE in attrs:
        return "landscape"
    if Arg.PORTRAIT in attrs:
        return "portrait"
    return None


def _process_body(body: str, directives: list[tuple[str, dict[str, str]]]) -> str:
    # First pass: replace pagebreaks
    for full_match, attrs in directives:
        if attrs.get(Arg.BREAK) == "true":
            body = body.replace(full_match, '<div class="pagebreak"></div>', 1)

    # Collect orientation directives present in body (after pagebreak replacements)
    orientation_directives = [
        (full_match, attrs)
        for full_match, attrs in directives
        if _orientation(attrs) is not None and full_match in body
    ]

    if not orientation_directives:
        return body

    sections: list[tuple[str, str]] = []
    current_pos = 0
    current_orientation = "portrait"

    for full_match, attrs in orientation_directives:
        idx = body.find(full_match)
        if idx > current_pos:
            section_content = body[current_pos:idx].strip()
            if section_content:
                sections.append((current_orientation, section_content))
        current_orientation = _orientation(attrs) or current_orientation
        current_pos = idx + len(full_match)

    if current_pos < len(body):
        remaining = body[current_pos:].strip()
        if remaining:
            sections.append((current_orientation, remaining))

    result = "\n".join(
        f'<div class="section-wrapper {orientation}">\n{content}\n</div>'
        for orientation, content in sections
    )
    # Remove any leftover orientation directive matches
    for full_match, attrs in orientation_directives:
        result = result.replace(full_match, "")
    return result


class Stage(BaseStage):
    name = "page"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH
    after = ("toc", "translation", "page-bg")
    valid_config_keys = frozenset({"add_pagedjs_screen_css"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        directives = self.get_directives(context.content, frozenset(Arg))
        has_directives = bool(directives)

        def replace_body(m: re.Match) -> str:
            return (
                m.group(1)
                + "\n"
                + _process_body(m.group(2), directives)
                + "\n"
                + m.group(3)
            )

        context.content = _BODY_RE.sub(replace_body, context.content)
        page_config = self.get_config(context)
        inject = f"<style>\n{_PAGE_CSS}</style>\n"
        if has_directives:
            inject += f"<script>\n{_LANDSCAPE_HANDLER_JS}</script>\n"
        if page_config.get("add_pagedjs_screen_css", True):
            inject += f"<style>\n{_PAGEDJS_SCREEN_CSS}</style>\n"
        context.content = context.content.replace("</head>", f"{inject}</head>", 1)
        if has_directives:
            self.log.info("Processed page layout directives")
        else:
            self.log.info("No page layout directives found")
        return context
