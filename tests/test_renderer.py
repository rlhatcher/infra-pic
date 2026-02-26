"""Tests for diagram renderer."""

from unittest.mock import MagicMock, call, patch

import pytest

from awsdiagram.models import ConnectionDef, DiagramDef, GroupDef, ServiceDef
from awsdiagram.renderer import render


def _make_diagram(
    name="Test",
    services=None,
    groups=None,
    connections=None,
):
    if services is None:
        services = {
            "web": ServiceDef(type="compute.EC2", label="Web"),
            "db": ServiceDef(type="database.RDS", label="DB"),
        }
    return DiagramDef(
        name=name,
        services=services,
        groups=groups or [],
        connections=connections or [],
    )


def _mock_node_class(label):
    """Return a MagicMock that acts like a diagrams node."""
    node = MagicMock()
    node.label = label
    return node


@patch("awsdiagram.renderer.validate_all_types")
@patch("awsdiagram.renderer.Diagram")
@patch("awsdiagram.renderer.check_graphviz")
class TestRender:
    def test_basic_render(self, mock_check, mock_diagram, mock_validate):
        mock_cls = MagicMock(side_effect=_mock_node_class)
        mock_validate.return_value = {"web": mock_cls, "db": mock_cls}
        diagram = _make_diagram()
        result = render(diagram, "/tmp/test.png")
        assert result == "/tmp/test.png"
        mock_diagram.assert_called_once()
        mock_check.assert_called_once()

    @patch("awsdiagram.renderer.Cluster")
    def test_render_with_groups(self, mock_cluster, mock_check, mock_diagram, mock_validate):
        mock_cls = MagicMock(side_effect=_mock_node_class)
        mock_validate.return_value = {"web": mock_cls, "db": mock_cls}
        diagram = _make_diagram(
            groups=[GroupDef(name="VPC", services=["web", "db"])]
        )
        render(diagram, "/tmp/test.png")
        mock_cluster.assert_called_once_with("VPC")

    def test_render_with_connections(self, mock_check, mock_diagram, mock_validate):
        mock_cls = MagicMock(side_effect=_mock_node_class)
        mock_validate.return_value = {"web": mock_cls, "db": mock_cls}
        conns = [ConnectionDef(from_="web", to="db")]
        diagram = _make_diagram(connections=conns)
        render(diagram, "/tmp/test.png")

    def test_render_with_labeled_connection(self, mock_check, mock_diagram, mock_validate):
        mock_cls = MagicMock(side_effect=_mock_node_class)
        mock_validate.return_value = {"web": mock_cls, "db": mock_cls}
        conns = [ConnectionDef(from_="web", to="db", label="SQL")]
        diagram = _make_diagram(connections=conns)
        render(diagram, "/tmp/test.png")

    def test_render_strips_png_extension(self, mock_check, mock_diagram, mock_validate):
        mock_cls = MagicMock(side_effect=_mock_node_class)
        mock_validate.return_value = {"web": mock_cls, "db": mock_cls}
        diagram = _make_diagram()
        result = render(diagram, "/tmp/output.png")
        call_kwargs = mock_diagram.call_args
        assert call_kwargs[1]["filename"] == "/tmp/output"

    @patch("awsdiagram.renderer.Cluster")
    def test_render_orphan_services(self, mock_cluster, mock_check, mock_diagram, mock_validate):
        """Services not in any group should still be rendered."""
        mock_cls = MagicMock(side_effect=_mock_node_class)
        mock_validate.return_value = {"web": mock_cls, "db": mock_cls}
        diagram = _make_diagram(
            groups=[GroupDef(name="VPC", services=["web"])]
        )
        render(diagram, "/tmp/test.png")
        # db is orphaned — should still be instantiated
        assert mock_cls.call_count == 2
