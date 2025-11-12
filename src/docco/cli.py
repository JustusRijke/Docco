"""CLI interface for Docco."""

import argparse
import os
import sys
from docco.parser import parse_markdown, process_directives_iteratively, process_markdown_to_html
from docco.core import parse_frontmatter, setup_logger
from docco.translation import extract_html_to_pot

logger = setup_logger(__name__)


def extract_pot(input_file, output_dir, allow_python):
    """Extract translatable strings from markdown to POT file."""
    with open(input_file, "r") as f:
        content = f.read()

    metadata, body = parse_frontmatter(content)
    base_dir = os.path.dirname(os.path.abspath(input_file))
    body = process_directives_iteratively(body, base_dir, allow_python=allow_python)

    wrapped_html = process_markdown_to_html(body)

    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    pot_path = os.path.join(output_dir, f"{input_basename}.pot")

    extract_html_to_pot(wrapped_html, pot_path)
    logger.info(f"Generated {pot_path}")
    return pot_path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with POT/PO translation support"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # Build command
    build_parser = subparsers.add_parser("build", help="Convert markdown to PDF")
    build_parser.add_argument("input_file", help="Input markdown file")
    build_parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory (default: current directory)",
    )
    build_parser.add_argument(
        "--po",
        help="PO file for translations",
    )
    build_parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep intermediate markdown and HTML files (for debugging)",
    )
    build_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    build_parser.add_argument(
        "--allow-python",
        action="store_true",
        help="Allow execution of Python code in directives (security risk)",
    )

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract", help="Extract translatable strings to POT file"
    )
    extract_parser.add_argument("input_file", help="Input markdown file")
    extract_parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory (default: current directory)",
    )
    extract_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    extract_parser.add_argument(
        "--allow-python",
        action="store_true",
        help="Allow execution of Python code in directives (security risk)",
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        setup_logger(level=10)  # DEBUG level

    try:
        input_file = args.input_file

        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            sys.exit(1)

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        if args.command == "extract":
            pot_path = extract_pot(input_file, args.output, args.allow_python)
            print(pot_path)
        else:
            # Build: markdown to PDF
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
