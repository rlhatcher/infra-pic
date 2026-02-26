"""Dynamic type resolution: maps 'category.ClassName' to diagrams.aws.* classes."""

import importlib
import shutil

from .errors import GraphvizNotFoundError, TypeResolutionError
from .models import ServiceDef


def resolve_type(type_str: str) -> type:
    """Resolve a type string like 'compute.EC2' to diagrams.aws.compute.EC2."""
    parts = type_str.split(".", 1)
    if len(parts) != 2:
        raise TypeResolutionError(
            f"Invalid type format '{type_str}'. Expected 'category.ClassName'."
        )

    category, classname = parts
    module_path = f"diagrams.aws.{category}"

    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        raise TypeResolutionError(
            f"Unknown category '{category}'. "
            f"No module 'diagrams.aws.{category}' found. "
            f"Check available categories at: diagrams.aws.*"
        )

    cls = getattr(mod, classname, None)
    if cls is None:
        available = [n for n in dir(mod) if not n.startswith("_")]
        raise TypeResolutionError(
            f"Unknown class '{classname}' in diagrams.aws.{category}. "
            f"Available: {', '.join(available)}"
        )

    return cls


def check_graphviz() -> None:
    """Check that Graphviz 'dot' binary is available on PATH."""
    if shutil.which("dot") is None:
        raise GraphvizNotFoundError(
            "Graphviz 'dot' not found on PATH. "
            "Install it with: brew install graphviz (macOS) "
            "or apt-get install graphviz (Ubuntu)"
        )


def validate_all_types(services: dict[str, ServiceDef]) -> dict[str, type]:
    """Resolve all service types upfront. Returns {service_id: class} map."""
    type_map = {}
    errors = []

    for sid, sdef in services.items():
        try:
            type_map[sid] = resolve_type(sdef.type)
        except TypeResolutionError as e:
            errors.append(f"  {sid}: {e}")

    if errors:
        raise TypeResolutionError(
            "Failed to resolve service types:\n" + "\n".join(errors)
        )

    return type_map
