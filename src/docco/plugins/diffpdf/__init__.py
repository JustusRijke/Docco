import diffpdf as diffpdf_lib

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage
from docco.utils import tmp_file


class Stage(BaseStage):
    name = "diffpdf"
    consumes = ContentType.PDF
    produces = ContentType.PDF
    phase = Phase.POSTPROCESS
    after = ("dpi",)
    valid_config_keys = frozenset({"enable", "threshold", "dpi", "skip_text", "store"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, bytes)
        cfg = self.get_config(context)
        if not cfg.get("enable", False):
            return context

        existing_path = context.output_dir / (context.source_path.stem + ".pdf")
        if not existing_path.is_file():
            return context
        threshold = cfg.get("threshold", 0.1)
        dpi = cfg.get("dpi", 96)
        skip_text = cfg.get("skip_text", False)
        store = cfg.get("store", False)
        output_dir = existing_path.parent / "diffpdf" if store else None

        with tmp_file(".pdf", context.content) as tmp_path:
            identical = diffpdf_lib.diffpdf(
                existing_path,
                tmp_path,
                threshold=threshold,
                dpi=dpi,
                output_dir=output_dir,
                skip_compare_text=skip_text,
            )

        if identical:
            self.log.info("PDF unchanged, skipping: %s", existing_path)
            context.content = existing_path.read_bytes()
            context.artifacts["skipped"] = True

        return context
