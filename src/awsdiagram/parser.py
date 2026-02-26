"""YAML loading and validation."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from .errors import SchemaValidationError, ServiceReferenceError, YamlLoadError
from .models import DiagramDef, GroupDef, RootModel


def load_yaml(path: str | Path) -> dict:
    """Load a YAML file and return the raw dict."""
    path = Path(path)
    if not path.exists():
        raise YamlLoadError(f"File not found: {path}")

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise YamlLoadError(f"Invalid YAML in {path}: {e}")

    if not isinstance(data, dict):
        raise YamlLoadError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")

    return data


def parse(path: str | Path) -> DiagramDef:
    """Load, validate schema, and cross-reference check. Returns DiagramDef."""
    data = load_yaml(path)

    try:
        root = RootModel.model_validate(data)
    except ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed:\n{e}")

    diagram = root.diagram
    _validate_references(diagram)
    return diagram


def _validate_references(diagram: DiagramDef) -> None:
    """Check that all service references in groups and connections exist."""
    valid_ids = set(diagram.services.keys())
    errors = []

    # Check group service references
    def _walk_groups(groups: list[GroupDef], path: str = "") -> None:
        for group in groups:
            gpath = f"{path}/{group.name}" if path else group.name
            for sid in group.services:
                if sid not in valid_ids:
                    errors.append(
                        f"Group '{gpath}' references unknown service '{sid}'"
                    )
            _walk_groups(group.children, gpath)

    _walk_groups(diagram.groups)

    # Check connection references
    for i, conn in enumerate(diagram.connections):
        if conn.from_ not in valid_ids:
            errors.append(
                f"Connection {i} 'from' references unknown service '{conn.from_}'"
            )
        targets = conn.to if isinstance(conn.to, list) else [conn.to]
        for target in targets:
            if target not in valid_ids:
                errors.append(
                    f"Connection {i} 'to' references unknown service '{target}'"
                )

    if errors:
        raise ServiceReferenceError(
            "Invalid service references:\n  " + "\n  ".join(errors)
        )
