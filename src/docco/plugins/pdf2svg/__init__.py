from enum import StrEnum
from pathlib import Path

import fitz

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage


class Arg(StrEnum):
    SRC = "src"
    PAGE = "page"
    OUT = "out"
    QUIET = "quiet"


def _extract_svg(pdf_path: Path, page_num_1indexed: int) -> str:
    doc = fitz.open(pdf_path)
    try:
        page_idx = page_num_1indexed - 1
        if page_idx < 0 or page_idx >= len(doc):
            msg = f"Page {page_num_1indexed} out of range; PDF has {len(doc)} page(s)"
            raise ValueError(msg)

        page = doc[page_idx]
        crop_box = page.rect

        try:
            text_blocks = page.get_text("dict")["blocks"]
            drawings = page.get_drawings()
            images = page.get_images()

            if text_blocks or drawings or images:
                bounds = [block["bbox"] for block in text_blocks]
                bounds.extend(drawing["rect"] for drawing in drawings)
                bounds.extend(page.get_image_bbox(img[7]) for img in images)

                x0 = min(b[0] for b in bounds)
                y0 = min(b[1] for b in bounds)
                x1 = max(b[2] for b in bounds)
                y1 = max(b[3] for b in bounds)
                crop_box = fitz.Rect(x0, y0, x1, y1)
        except Exception as e:  # noqa: BLE001  # pragma: no cover
            log.warning("Could not calculate tight bounds, using full page: %s", e)

        page.set_cropbox(crop_box)
        return page.get_svg_image(matrix=fitz.Identity)
    finally:
        doc.close()


class Stage(BaseStage):
    name = "pdf2svg"
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
            src_str = attrs.get(Arg.SRC)
            page_str = attrs.get(Arg.PAGE)
            if not src_str:
                raise ValueError(f"Missing 'src' in pdf2svg directive: {full_match!r}")
            if not page_str:
                raise ValueError(f"Missing 'page' in pdf2svg directive: {full_match!r}")
            if not page_str.isdigit():
                raise ValueError(
                    f"Non-numeric 'page' in pdf2svg directive: {full_match!r}"
                )

            page_num = int(page_str)
            out_name = attrs.get(Arg.OUT) or f"{Path(src_str).stem}_p{page_num}.svg"
            quiet = attrs.get(Arg.QUIET, "") == "true"

            pdf_path = (doc_dir / src_str).resolve()
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            if pdf_path.suffix.lower() != ".pdf":
                raise ValueError(f"Source file is not a PDF: {pdf_path}")

            svg_dir = doc_dir / svg_dir_name
            svg_path = svg_dir / out_name

            if skip_if_exists and svg_path.exists():
                log.debug("SVG already exists, skipping: %s", svg_path)
            else:
                svg_dir.mkdir(parents=True, exist_ok=True)
                svg_content = _extract_svg(pdf_path, page_num)
                svg_path.write_text(svg_content, encoding="utf-8")
                log.info("Written SVG: %s", svg_path)

            replacement = "" if quiet else f"{svg_dir_name}/{out_name}"
            content = content.replace(full_match, replacement, 1)

        context.content = content
        return context


log = Stage.log
