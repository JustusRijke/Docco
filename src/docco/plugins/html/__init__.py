import re
from pathlib import Path
from urllib.parse import urljoin

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.attrs import attrs_block_plugin, attrs_plugin

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage

TEMPLATE_DIR = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE = TEMPLATE_DIR / "base.html"


def _absolutize_css_urls(css: str, css_path: Path) -> str:
    base_url = css_path.resolve().parent.as_uri()

    def replace_url(m: re.Match) -> str:
        url = m.group(1).strip("'\" ")
        if any(url.startswith(p) for p in ("http://", "https://", "file://", "data:")):
            return m.group(0)
        return f'url("{urljoin(base_url + "/", url)}")'

    return re.sub(r'url\(["\']?([^)]+?)["\']?\)', replace_url, css)


def _to_path_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def _collect_css(html_config: dict) -> str:
    parts: list[str] = []
    for css_path_str in html_config.get("css", []):
        css_path = Path(css_path_str)
        if not css_path.is_file():
            msg = f"CSS file not found: {css_path}"
            raise FileNotFoundError(msg)
        raw_css = css_path.read_text(encoding="utf-8")
        parts.append(_absolutize_css_urls(raw_css, css_path))
        log.debug("Loaded CSS: %s", css_path)
    return "\n".join(parts)


def _collect_js(html_config: dict) -> tuple[list[str], list[str]]:
    js_external: list[str] = html_config.get("js_external", [])
    inline_parts: list[str] = []
    for js_path_str in html_config.get("js", []):
        js_path = Path(js_path_str)
        if not js_path.is_file():
            msg = f"JS file not found: {js_path}"
            raise FileNotFoundError(msg)
        inline_parts.append(js_path.read_text(encoding="utf-8"))
        log.debug("Loaded JS: %s", js_path)
    return inline_parts, js_external


def _load_template(html_config: dict) -> str:
    paths = html_config.get("template", [])
    if paths:
        return Path(paths[-1]).read_text(encoding="utf-8")
    return DEFAULT_TEMPLATE.read_text(encoding="utf-8")


def _render_template(
    template: str,
    body: str,
    css: str,
    js_inline: list[str],
    js_external: list[str],
    title: str,
) -> str:
    script_tags = "".join(f"<script>\n{js}\n</script>\n" for js in js_inline)
    script_tags += "".join(f'<script src="{url}"></script>\n' for url in js_external)
    result = template.replace("{{ body }}", body).replace("{{ css }}", css)
    result = result.replace("<head>", f"<head>\n    <title>{title}</title>", 1)
    if script_tags:
        result = result.replace("</head>", f"{script_tags}</head>", 1)
    return result


class Stage(BaseStage):
    name = "html"
    consumes = ContentType.MARKDOWN
    produces = ContentType.HTML
    phase = Phase.CONVERT
    valid_config_keys = frozenset({"css", "template", "js", "js_external", "title"})

    @classmethod
    def normalize_config_section(cls, section: dict, base_dir: Path) -> dict:
        """Resolve css/js/template paths to absolute, normalizing strings to lists."""
        result = dict(section)
        for key in ("css", "js"):
            items = _to_path_list(result.get(key))
            result[key] = [
                str((base_dir / p).resolve()) if not Path(p).is_absolute() else p
                for p in items
            ]
        if "template" in result:
            items = _to_path_list(result["template"])
            result["template"] = [
                str((base_dir / p).resolve()) if not Path(p).is_absolute() else p
                for p in items
            ]
        return result

    def __init__(self) -> None:
        self._md = (
            MarkdownIt("commonmark", {"html": True})
            .use(anchors_plugin, min_level=1, max_level=6, permalink=False)
            .use(attrs_plugin)
            .use(attrs_block_plugin)
            .enable("table")
        )

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        cfg = self.get_config(context)
        title = cfg.get("title", context.source_path.stem)
        body = self._md.render(context.content)
        css = _collect_css(cfg)
        js_inline, js_external = _collect_js(cfg)
        template = _load_template(cfg)
        html = _render_template(template, body, css, js_inline, js_external, title)
        context.content = html
        context.content_type = ContentType.HTML
        self.log.info("Converted markdown to HTML")
        return context


log = Stage.log
