"""CLI interface for Docco."""

import argparse
import os
import sys
from docco.parser import parse_markdown
from docco.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with YAML frontmatter support"
    )
    parser.add_argument(
        "input_file",
        help="Input markdown file"
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "-c", "--css",
        help="CSS file for PDF styling (or auto-detect from markdown filename)"
    )
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep intermediate markdown and HTML files (for debugging)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--allow-python",
        action="store_true",
        help="Allow execution of Python code in directives (security risk)"
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        setup_logger(level=10)  # DEBUG level

    try:
        # Check input file exists
        if not os.path.exists(args.input_file):
            logger.error(f"Input file not found: {args.input_file}")
            sys.exit(1)

        # Create output directory if needed
        if not os.path.exists(args.output):
            os.makedirs(args.output)

        # Parse markdown and convert to PDF
        output_files = parse_markdown(
            args.input_file,
            args.output,
            css_file=args.css,
            keep_intermediate=args.keep_intermediate,
            allow_python=args.allow_python
        )

        logger.info(f"Generated {len(output_files)} output file(s)")
        for output_file in output_files:
            print(output_file)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
