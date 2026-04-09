import argparse
import logging
import sys
from pathlib import Path

from docco.config import load_config, load_project_config
from docco.context import Context
from docco.logging_config import LogCounter, setup_logging
from docco.pipeline import PipelineError, build_pipeline, discover_stages, run_pipeline

log = logging.getLogger("docco.cli")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="docco", description="Markdown to PDF converter"
    )
    parser.add_argument("input", nargs="*", type=Path, help="Input markdown file(s)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: same directory as input)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--config", type=Path, default=None, help="Path to project docco.toml"
    )
    return parser.parse_args(argv)


def _resolve_input_files(cli_inputs: list[Path], project_config: dict) -> list[Path]:
    """Resolve input files from CLI args or project config."""
    if cli_inputs:
        return [p.resolve() for p in cli_inputs]

    raw = project_config.get("file")
    if raw is None:
        log.error("No input files: pass as arguments or set 'file' in docco.toml")
        sys.exit(1)

    files = [raw] if isinstance(raw, str) else raw
    if not files:
        log.error("No input files: 'file' in docco.toml is empty")
        sys.exit(1)
    return [Path(f).resolve() for f in files]


_CONTENT_TYPE_EXT = {"markdown": ".md", "html": ".html", "pdf": ".pdf"}


def _save_intermediate(error: PipelineError) -> None:
    for ctx in error.contexts:
        ext = _CONTENT_TYPE_EXT.get(ctx.content_type, ".tmp")
        out = ctx.output_dir / (ctx.source_path.stem + f".intermediate{ext}")
        if isinstance(ctx.content, bytes):
            out.write_bytes(ctx.content)
        else:
            out.write_text(ctx.content, encoding="utf-8")
        log.info("Intermediate output saved: %s", out)


def _print_summary(generated: int, skipped: int, counter: LogCounter) -> None:
    parts = [f"Generated {generated} file(s)"]
    if skipped:
        parts[0] = f"Generated {generated}, skipped {skipped} unchanged"
    if counter.warning_count or counter.error_count:
        parts.append(
            f"{counter.warning_count} warning(s), {counter.error_count} error(s)"
        )
    log.info(" \u2014 ".join(parts))


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    counter = setup_logging(verbose=args.verbose)

    try:
        available_stages = discover_stages()
        normalizers = {
            (cls.config_key or name): cls.normalize_config_section
            for name, cls in available_stages.items()
            if "normalize_config_section" in cls.__dict__
        }

        project_config, config_dir = load_project_config(
            config_path=args.config, normalizers=normalizers
        )

        # Reconfigure logging from [log] section
        log_section = project_config.get("log", {})
        if log_section:
            counter = setup_logging(
                verbose=args.verbose,
                log_file=Path(log_section["file"]) if "file" in log_section else None,
                level=log_section.get("level"),
            )

        source_files = _resolve_input_files(args.input, project_config)

        generated = 0
        skipped = 0

        for source_path in source_files:
            if not source_path.is_file():
                log.error("Input file not found: %s", source_path)
                sys.exit(1)

            output_dir = args.output.resolve() if args.output else source_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            config = load_config(source_path, project_config, normalizers=normalizers)
            suffix = source_path.suffix.lower()
            if suffix in {".html", ".htm"}:
                context = Context.from_html_file(
                    source_path, output_dir, config, config_dir
                )
            else:
                context = Context.from_file(source_path, output_dir, config, config_dir)
            pipeline = build_pipeline(
                config, available_stages, input_type=context.content_type
            )
            try:
                results = run_pipeline(pipeline, context)
            except PipelineError as e:
                error_cfg = config.get("error", {})
                if error_cfg.get("save_intermediate", True):
                    _save_intermediate(e)
                raise RuntimeError(str(e)) from e

            for ctx in results:
                if ctx.artifacts.get("skipped"):  # pragma: no cover
                    skipped += 1
                    continue
                output_path = ctx.output_dir / (ctx.source_path.stem + ".pdf")
                assert isinstance(ctx.content, bytes)
                output_path.write_bytes(ctx.content)
                generated += 1
                log.info("Written: %s", output_path)

        _print_summary(generated, skipped, counter)
    except RuntimeError:
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        log.error("%s", e)
        sys.exit(1)
