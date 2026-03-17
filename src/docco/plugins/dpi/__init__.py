import shutil
import subprocess
from pathlib import Path

import fitz  # PyMuPDF

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage
from docco.utils import tmp_file

_LEVELS = frozenset({"info", "warning", "error"})


def _downscale_pdf_images(pdf_path: Path, target_dpi: int) -> None:
    gs_cmd = shutil.which("gswin64c") or shutil.which("gs")
    if not gs_cmd:  # pragma: no cover
        log.warning("Ghostscript not found, skipping image downscaling")
        return

    with tmp_file(".pdf") as tmp_path:
        try:
            subprocess.run(
                [
                    gs_cmd,
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    f"-dColorImageResolution={target_dpi}",
                    f"-dGrayImageResolution={target_dpi}",
                    f"-dMonoImageResolution={target_dpi}",
                    "-dColorImageDownsampleThreshold=1.0",
                    "-dGrayImageDownsampleThreshold=1.0",
                    "-dMonoImageDownsampleThreshold=1.0",
                    "-dColorImageDownsampleType=/Bicubic",
                    "-dGrayImageDownsampleType=/Bicubic",
                    "-dMonoImageDownsampleType=/Subsample",
                    "-dDownsampleColorImages=true",
                    "-dDownsampleGrayImages=true",
                    "-dDownsampleMonoImages=true",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={tmp_path}",
                    str(pdf_path),
                ],
                check=True,
                capture_output=True,
            )
            shutil.move(tmp_path, pdf_path)
            log.info("Downscaled images in PDF to %d DPI", target_dpi)
        except subprocess.CalledProcessError as e:  # pragma: no cover
            log.error("Ghostscript failed: %s", e.stderr.decode())


def _check_image_dpi(pdf_bytes: bytes, threshold: int, level: str) -> None:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_idx, img_info in enumerate(page.get_image_info()):
                width_px: int = img_info["width"]
                height_px: int = img_info["height"]
                bbox = img_info["bbox"]
                width_pts = bbox[2] - bbox[0]
                height_pts = bbox[3] - bbox[1]
                width_in = width_pts / 72
                height_in = height_pts / 72
                dpi_x = width_px / width_in if width_in > 0 else 0
                dpi_y = height_px / height_in if height_in > 0 else 0
                min_dpi = min(dpi_x, dpi_y)

                if min_dpi < threshold * 0.95:
                    expected_w = int(width_in * threshold)
                    expected_h = int(height_in * threshold)
                    getattr(log, level)(
                        "Page %d, Image #%d: %dx%d @ %.0f DPI (actual), expected %dx%d @ %d DPI",
                        page_num + 1,
                        img_idx + 1,
                        width_px,
                        height_px,
                        min_dpi,
                        expected_w,
                        expected_h,
                        threshold,
                    )
    finally:
        doc.close()


class Stage(BaseStage):
    name = "dpi"
    consumes = ContentType.PDF
    produces = ContentType.PDF
    phase = Phase.POSTPROCESS
    valid_config_keys = frozenset({"max", "level"})

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, bytes)
        cfg = self.get_config(context)
        target_dpi: int = cfg.get("max", 300)
        level: str = cfg.get("level", "warning")
        if level not in _LEVELS:
            msg = f"[dpi] invalid level '{level}', must be one of: {', '.join(sorted(_LEVELS))}"
            raise ValueError(msg)

        with tmp_file(".pdf", context.content) as tmp_path:
            _downscale_pdf_images(tmp_path, target_dpi)
            context.content = tmp_path.read_bytes()

        _check_image_dpi(context.content, target_dpi, level)
        self.log.info("Checked image DPI (max %d)", target_dpi)
        return context


log = Stage.log
