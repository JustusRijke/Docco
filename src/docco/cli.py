"""CLI interface for Docco."""

import argparse
import os
import sys
import logging
import colorlog
from docco.parser import parse_markdown

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with POT/PO translation support"
    )

    parser.add_argument("input_file", help="Input markdown file")
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

    # Set up colorized logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    try:
        input_file = args.input_file

        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            sys.exit(1)

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        # Convert markdown to PDF
        output_files = parse_markdown(
            input_file,
            args.output,
            keep_intermediate=args.keep_intermediate,
            allow_python=args.allow_python,
            po_file=args.po,
        )

        logger.info(f"Generated {len(output_files)} output file(s)")
        for output_file in output_files:
            print(output_file)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
