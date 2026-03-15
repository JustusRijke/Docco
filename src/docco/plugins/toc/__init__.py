from pathlib import Path

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage

_SCRIPTS_DIR = Path(__file__).parent / "scripts"
_CREATE_TOC_JS = (_SCRIPTS_DIR / "create_toc.js").read_text(encoding="utf-8")
_TOC_HANDLER_JS = (_SCRIPTS_DIR / "toc_handler.js").read_text(encoding="utf-8")


def _inject_toc(html: str, nav: str) -> str:
    scripts = (
        f"<script>\n{_CREATE_TOC_JS}</script>\n<script>\n{_TOC_HANDLER_JS}</script>\n"
    )
    html = html.replace("</head>", f"{scripts}</head>", 1)
    for full_match, _ in Stage.parse_directives("toc", html, frozenset()):
        html = html.replace(full_match, nav, 1)
    return html


class Stage(BaseStage):
    name = "toc"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.ENRICH
    valid_config_keys = frozenset({"start", "end"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        if not self.get_directives(context.content, frozenset()):
            self.log.info("No TOC directive found, skipping")
            return context
        cfg = self.get_config(context)
        start: int = cfg.get("start", 1)
        end: int = cfg.get("end", 6)
        nav = f'<nav data-toc-start="{start}" data-toc-end="{end}"></nav>'
        context.content = _inject_toc(context.content, nav)
        self.log.info("Injected TOC (h%d-h%d)", start, end)
        return context
