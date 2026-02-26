"""Builds Diagram/Cluster/Node/Edge objects and renders to PNG."""

from diagrams import Cluster, Diagram, Edge

from .errors import RenderError
from .models import DiagramDef, GroupDef
from .resolver import check_graphviz, validate_all_types


def render(diagram_def: DiagramDef, output: str) -> str:
    """Render a DiagramDef to a PNG file. Returns the output path."""
    check_graphviz()
    type_map = validate_all_types(diagram_def.services)

    # diagrams library appends the format extension, so strip it
    if output.endswith(".png"):
        output = output[:-4]

    nodes: dict[str, object] = {}

    try:
        with Diagram(
            diagram_def.name,
            filename=output,
            outformat="png",
            show=False,
            direction="TB",
            graph_attr={"fontname": "Inter", "fontsize": "12"},
            node_attr={"fontname": "Inter", "fontsize": "12"},
            edge_attr={"fontname": "Inter", "fontsize": "12"},
        ):
            # Render groups (clusters) and their services
            grouped_ids: set[str] = set()
            _render_groups(diagram_def.groups, diagram_def, type_map, nodes, grouped_ids)

            # Render orphan services (not in any group)
            for sid, sdef in diagram_def.services.items():
                if sid not in grouped_ids:
                    cls = type_map[sid]
                    nodes[sid] = cls(sdef.label)

            # Wire connections
            for conn in diagram_def.connections:
                src = nodes[conn.from_]
                targets = conn.to if isinstance(conn.to, list) else [conn.to]
                for target_id in targets:
                    target = nodes[target_id]
                    if conn.label:
                        src >> Edge(label=conn.label) >> target
                    else:
                        src >> target
    except Exception as e:
        if "graphviz" in str(e).lower() or "dot" in str(e).lower():
            raise RenderError(f"Graphviz rendering failed: {e}")
        raise RenderError(f"Rendering failed: {e}")

    return output + ".png"


def _render_groups(
    groups: list[GroupDef],
    diagram_def: DiagramDef,
    type_map: dict[str, type],
    nodes: dict[str, object],
    grouped_ids: set[str],
) -> None:
    """Recursively render groups as Clusters, instantiating nodes inside them."""
    for group in groups:
        with Cluster(group.name, graph_attr={"fontname": "Inter bold", "fontsize": "12"}):
            for sid in group.services:
                cls = type_map[sid]
                nodes[sid] = cls(diagram_def.services[sid].label)
                grouped_ids.add(sid)
            _render_groups(group.children, diagram_def, type_map, nodes, grouped_ids)
