from enum import StrEnum

import segno

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage


class Arg(StrEnum):
    URL = "url"
    OUT = "out"
    QUIET = "quiet"


class Stage(BaseStage):
    name = "qr"
    consumes = ContentType.MARKDOWN
    produces = ContentType.MARKDOWN
    phase = Phase.PREPROCESS
    valid_config_keys = frozenset({"svg_dir", "skip_if_exists"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, str)
        cfg = self.get_config(context)
        svg_dir_name: str = cfg.get("svg_dir", "assets")
        skip_if_exists: bool = cfg.get("skip_if_exists", True)

        doc_dir = context.source_path.parent
        content = context.content

        for full_match, attrs in self.get_directives(content, frozenset(Arg)):
            url = attrs.get(Arg.URL)
            out_name = attrs.get(Arg.OUT)
            if not url:
                raise ValueError(f"Missing 'url' in qr directive: {full_match!r}")
            if not out_name:
                raise ValueError(f"Missing 'out' in qr directive: {full_match!r}")
            quiet = attrs.get(Arg.QUIET, "") == "true"

            svg_dir = doc_dir / svg_dir_name
            svg_path = svg_dir / out_name

            if skip_if_exists and svg_path.exists():
                log.debug("SVG already exists, skipping: %s", svg_path)
            else:
                svg_dir.mkdir(parents=True, exist_ok=True)
                segno.make_qr(url).save(svg_path)
                log.info("Written SVG: %s", svg_path)

            replacement = "" if quiet else f"{svg_dir_name}/{out_name}"
            content = content.replace(full_match, replacement, 1)

        context.content = content
        return context


log = Stage.log
