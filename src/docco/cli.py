"""
Command-line interface for Docco.
"""

import sys
import runpy
from pathlib import Path
import click


@click.group()
@click.version_option(version="0.2.0", prog_name="docco")
def cli():
    """
    Docco - PDF documentation generator using HTML/CSS.

    Build professional PDF documentation from Python scripts.
    """
    pass


@cli.command()
@click.argument("script", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output PDF path (overrides script default)",
)
def build(script: Path, output: Path | None):
    """
    Build a PDF document from a Python script.

    The script should create a Document and call render_pdf().

    Example:

        docco build examples/basic_document.py
    """
    click.echo(f"Building document from: {script}")

    # Add script directory to path so imports work
    script_dir = script.parent.absolute()
    sys.path.insert(0, str(script_dir))

    try:
        # Run the script
        runpy.run_path(str(script), run_name="__main__")
        click.echo("✓ Document built successfully")
    except Exception as e:
        click.echo(f"✗ Error building document: {e}", err=True)
        raise click.Abort()
    finally:
        # Clean up path
        if str(script_dir) in sys.path:
            sys.path.remove(str(script_dir))


@cli.command()
def version():
    """Show Docco version."""
    click.echo("Docco version 0.2.0")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
