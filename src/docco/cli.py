"""CLI interface for Docco."""

import argparse
import logging
import sys
from pathlib import Path

from docco.config import find_config, load_config
from docco.logging_config import setup_logging
from docco.parser import parse_markdown
from docco.pdf import html_to_pdf

logger = logging.getLogger(__name__)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with POT/PO translation support"
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default=None,
        help="Input markdown (.md) or HTML (.html, .htm) file",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--po",
        help="PO file for single-language translations (ignored in multilingual mode)",
    )
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep intermediate markdown and HTML files (for debugging)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--allow-python",
        action="store_true",
        help="Allow execution of Python code in directives (security risk)",
    )

    args = parser.parse_args()

    # Set up logging and get counter
    counter = setup_logging(verbose=args.verbose)

    try:
        # Load config file if present
        config_path = find_config(Path.cwd())
        config = load_config(config_path) if config_path else {}

        # Resolve input files: CLI arg takes precedence over config
        config_files: list[Path] = config.get("input", {}).get("file", [])
        if args.input_file:
            input_files = [Path(args.input_file)]
        elif config_files:
            input_files = config_files
        else:
            parser.error(
                "No input file specified (pass as argument or set [input] file in .docco)"
            )

        allow_python = args.allow_python or config.get("python", {}).get("allow", False)
        keep_intermediate = args.keep_intermediate or config.get("output", {}).get(
            "keep-intermediate", False
        )

        if args.output != ".":
            # Explicit CLI flag
            output_dir = Path(args.output)
        elif "path" in config.get("output", {}):
            output_dir = config["output"]["path"]
        else:
            output_dir = Path(args.output)
        po_file = Path(args.po) if args.po else None

        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        all_output_files: list[Path] = []
        for input_file in input_files:
            if not input_file.exists():
                logger.error(f"Input file not found: {input_file}")
                sys.exit(1)

            # Validate file extension
            valid_extensions = {".md", ".html", ".htm"}
            if input_file.suffix.lower() not in valid_extensions:
                logger.error(
                    f"Invalid file type: {input_file.suffix}\n"
                    f"Supported formats: {', '.join(sorted(valid_extensions))}"
                )
                sys.exit(1)

            # Direct HTML to PDF conversion (bypass all processing)
            if input_file.suffix.lower() in [".html", ".htm"]:
                logger.info(f"Processing HTML: {input_file}")
                output_pdf = output_dir / f"{input_file.stem}.pdf"
                html_to_pdf(input_file, output_pdf)
                all_output_files.append(output_pdf)
            else:
                # Convert markdown to PDF
                output_files = parse_markdown(
                    input_file,
                    output_dir,
                    keep_intermediate=keep_intermediate,
                    allow_python=allow_python,
                    po_file=po_file,
                )
                all_output_files.extend(output_files)

        # Print summary
        if counter.error_count > 0 or counter.warning_count > 0:
            parts = []
            if counter.error_count > 0:
                parts.append(f"{counter.error_count} error(s)")
            if counter.warning_count > 0:
                parts.append(f"{counter.warning_count} warning(s)")
            logger.warning(f"Completed with {', '.join(parts)}")
        else:
            logger.info(
                f"Successfully generated {len(all_output_files)} output file(s)"
            )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
