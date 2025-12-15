"""CLI interface for Docco."""

import argparse
import os
import sys
import logging
from docco.parser import parse_markdown
from docco.logging_config import setup_logging

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

    # Set up logging and get counter
    counter = setup_logging(verbose=args.verbose)

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

        for output_file in output_files:
            print(output_file)

        # Print summary
        if counter.error_count > 0 or counter.warning_count > 0:
            parts = []
            if counter.error_count > 0:
                parts.append(f"{counter.error_count} error(s)")
            if counter.warning_count > 0:
                parts.append(f"{counter.warning_count} warning(s)")
            logger.warning(f"Completed with {', '.join(parts)}")
        else:
            logger.info(f"Successfully generated {len(output_files)} output file(s)")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
