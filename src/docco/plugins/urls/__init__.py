import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import url2pathname

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage


def _absolutize_css_urls(css: str, css_path: Path) -> str:
    base_url = css_path.resolve().parent.as_uri()

    def replace_url(m: re.Match) -> str:
        url = m.group(1).strip("'\" ")
        if any(url.startswith(p) for p in ("http://", "https://", "file://", "data:")):
            return m.group(0)
        return f'url("{urljoin(base_url + "/", url)}")'

    return re.sub(r'url\(["\']?([^)]+?)["\']?\)', replace_url, css)


def _fix_style_block_urls(html: str, base_dir: Path) -> str:
    sentinel = base_dir / "_"

    def replace_style(m: re.Match) -> str:
        absolutized = _absolutize_css_urls(m.group(1), sentinel)
        for url_match in re.finditer(r'url\("(file://[^"]+)"\)', absolutized):
            file_path = Path(url2pathname(url_match.group(1)[7:]))
            if not file_path.exists():
                msg = f"Asset not found (referenced in CSS): {file_path}"
                raise FileNotFoundError(msg)
        return f"<style>{absolutized}</style>"

    return re.sub(r"<style>(.*?)</style>", replace_style, html, flags=re.DOTALL)


def _absolutize_html_urls(html: str, base_dir: Path) -> str:
    base_url = base_dir.resolve().as_uri()

    def replace_url(m: re.Match) -> str:
        attr, quote, url = m.group(1), m.group(2), m.group(3)
        if any(
            url.startswith(p) for p in ("#", "http://", "https://", "file://", "data:")
        ):
            return m.group(0)
        return f"{attr}={quote}{urljoin(base_url + '/', url)}{quote}"

    return re.sub(r'((?:src|href))=(["\'])(.*?)\2', replace_url, html)


def _extract_file_urls(html: str) -> list[str]:
    attr_urls = re.findall(r'(?:src|href)=["\']?(file://[^"\'>\s]+)', html)
    css_urls = re.findall(r'url\(["\']?(file://[^"\')\s]+)["\']?\)', html)
    return attr_urls + css_urls


def _extract_http_urls(html: str) -> list[str]:
    attr_urls = re.findall(r'(?:src|href)=["\']?(https?://[^"\'>\s]+)', html)
    css_urls = re.findall(r'url\(["\']?(https?://[^"\')\s]+)["\']?\)', html)
    return attr_urls + css_urls


def _check_urls(html: str, base_dir: Path, *, local_only: bool = True) -> None:
    file_urls = _extract_file_urls(html)
    http_urls = [] if local_only else _extract_http_urls(html)
    if file_urls or http_urls:
        log.info("Checking %d URL(s)...", len(file_urls) + len(http_urls))

    for url in file_urls:
        log.debug("Checking: %s", url)
        file_path = Path(url2pathname(url[7:]))
        if not file_path.exists():
            msg = f"URL not found: {url}"
            raise FileNotFoundError(msg)

    for url in http_urls:
        log.debug("Checking: %s", url)
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except urllib.error.URLError as e:
            log.warning("Could not reach %s: %s", url, e)
            continue
        if status >= 400:
            msg = f"URL returned {status}: {url}"
            raise ValueError(msg)


class Stage(BaseStage):
    name = "urls"
    consumes = ContentType.HTML
    produces = ContentType.HTML
    phase = Phase.RENDER
    after = ("page",)
    valid_config_keys = frozenset({"enable", "test", "local_only"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        cfg = self.get_config(context)
        if not cfg.get("enable", True):
            self.log.info("Skipped (disabled)")
            return context
        base_dir = context.source_path.parent
        html = _absolutize_html_urls(context.content, base_dir)
        html = _fix_style_block_urls(html, base_dir)
        if cfg.get("test", True):
            _check_urls(html, base_dir, local_only=cfg.get("local_only", True))
        context.content = html
        return context


log = Stage.log
