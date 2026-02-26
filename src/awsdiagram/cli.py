"""Click CLI: render, validate, import."""

import sys

import click

from .errors import AwsDiagramError
from .parser import parse
from .renderer import render as render_diagram
from .resolver import validate_all_types


@click.group()
def main() -> None:
    """awsdiagram - Generate AWS architecture diagrams from YAML."""


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output PNG path (default: <diagram-name>.png)")
def render(file: str, output: str | None) -> None:
    """Render a YAML diagram definition to PNG."""
    try:
        diagram = parse(file)
        if output is None:
            output = diagram.name.lower().replace(" ", "-") + ".png"
        result = render_diagram(diagram, output)
        click.echo(f"Rendered: {result}")
    except AwsDiagramError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
def validate(file: str) -> None:
    """Validate a YAML diagram definition without rendering."""
    try:
        diagram = parse(file)
        validate_all_types(diagram.services)
        click.echo(f"Valid: {file}")
    except AwsDiagramError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group(name="import")
def import_group() -> None:
    """Import infrastructure definitions from external tools."""


@import_group.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-o", "--output", default="infra.yaml", help="Output YAML path")
def terraform(file: str, output: str) -> None:
    """Import a Terraform JSON plan/state into YAML DSL."""
    from .terraform.importer import import_terraform

    try:
        yaml_content = import_terraform(file)
        with open(output, "w") as f:
            f.write(yaml_content)
        click.echo(f"Imported: {output}")
    except AwsDiagramError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
