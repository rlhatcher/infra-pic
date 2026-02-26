"""Parse Terraform JSON plan/state and produce YAML DSL."""

import json
import re
from pathlib import Path

import yaml

from ..errors import TerraformImportError
from .mappings import TERRAFORM_TO_DIAGRAMS


def import_terraform(path: str | Path) -> str:
    """Read a Terraform JSON file and return YAML DSL string."""
    path = Path(path)
    if not path.exists():
        raise TerraformImportError(f"File not found: {path}")

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise TerraformImportError(f"Failed to read Terraform JSON: {e}")

    resources = _extract_resources(data)
    if not resources:
        raise TerraformImportError(
            "No resources found. Expected Terraform plan "
            "(planned_values.root_module) or state (values.root_module) format."
        )

    return _build_yaml(resources)


def _extract_resources(data: dict) -> list[dict]:
    """Extract resource list from plan or state format."""
    # Plan format: planned_values.root_module.resources
    root = None
    if "planned_values" in data:
        root = data["planned_values"].get("root_module")
    elif "values" in data:
        root = data["values"].get("root_module")

    if root is None:
        return []

    resources = list(root.get("resources", []))
    _collect_child_modules(root, resources)
    return resources


def _collect_child_modules(module: dict, resources: list[dict]) -> None:
    """Recursively flatten child module resources."""
    for child in module.get("child_modules", []):
        resources.extend(child.get("resources", []))
        _collect_child_modules(child, resources)


def _build_yaml(resources: list[dict]) -> str:
    """Build YAML DSL from extracted Terraform resources."""
    services: dict[str, dict] = {}
    vpc_groups: dict[str, list[str]] = {}
    subnet_groups: dict[str, list[str]] = {}
    ungrouped: list[str] = []

    for res in resources:
        res_type = res.get("type", "")
        diagram_type = TERRAFORM_TO_DIAGRAMS.get(res_type)
        if diagram_type is None:
            continue

        # Build a unique service ID
        name = res.get("name", "unnamed")
        sid = _make_service_id(name, res_type, services)

        # Use tags.Name for label if available, else humanize the name
        values = res.get("values") or {}
        tags = values.get("tags") or {}
        label = tags.get("Name") or _humanize(name)

        services[sid] = {"type": diagram_type, "label": label}

        # Infer grouping from vpc_id / subnet_id
        subnet_id = values.get("subnet_id")
        vpc_id = values.get("vpc_id")

        if subnet_id:
            subnet_groups.setdefault(subnet_id, []).append(sid)
        elif vpc_id:
            vpc_groups.setdefault(vpc_id, []).append(sid)
        else:
            ungrouped.append(sid)

    if not services:
        raise TerraformImportError(
            "No mappable AWS resources found in the Terraform plan."
        )

    # Build group structure
    groups = []
    if vpc_groups or subnet_groups:
        children = []
        for vpc_id, sids in vpc_groups.items():
            children.append({"name": f"VPC ({vpc_id[:12]}...)", "services": sids})
        for subnet_id, sids in subnet_groups.items():
            children.append({"name": f"Subnet ({subnet_id[:12]}...)", "services": sids})

        groups.append({"name": "AWS Cloud", "children": children})

    diagram = {
        "diagram": {
            "name": "Imported Infrastructure",
            "services": services,
        }
    }

    if groups:
        diagram["diagram"]["groups"] = groups
    # Connections left empty — Terraform plans don't encode data flow
    diagram["diagram"]["connections"] = []

    return yaml.dump(diagram, default_flow_style=False, sort_keys=False)


def _make_service_id(name: str, res_type: str, existing: dict) -> str:
    """Create a unique, valid service ID."""
    # Sanitize: lowercase, replace non-alphanum with underscore
    sid = re.sub(r"[^a-z0-9]", "_", name.lower()).strip("_")
    if not sid:
        sid = res_type.replace("aws_", "").replace(".", "_")

    # Ensure uniqueness
    if sid not in existing:
        return sid
    counter = 2
    while f"{sid}_{counter}" in existing:
        counter += 1
    return f"{sid}_{counter}"


def _humanize(name: str) -> str:
    """Convert snake_case/kebab-case to a human-readable label."""
    return name.replace("_", " ").replace("-", " ").title()
