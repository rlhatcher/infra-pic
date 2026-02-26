"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from awsdiagram.models import (
    ConnectionDef,
    DiagramDef,
    GroupDef,
    RootModel,
    ServiceDef,
)


class TestServiceDef:
    def test_valid_type(self):
        s = ServiceDef(type="compute.EC2", label="Web")
        assert s.type == "compute.EC2"

    def test_invalid_type_no_dot(self):
        with pytest.raises(ValidationError, match="category.ClassName"):
            ServiceDef(type="EC2", label="Web")

    def test_invalid_type_lowercase_class(self):
        with pytest.raises(ValidationError, match="category.ClassName"):
            ServiceDef(type="compute.ec2", label="Web")

    def test_invalid_type_uppercase_category(self):
        with pytest.raises(ValidationError, match="category.ClassName"):
            ServiceDef(type="Compute.EC2", label="Web")

    def test_label_required(self):
        with pytest.raises(ValidationError):
            ServiceDef(type="compute.EC2")


class TestGroupDef:
    def test_basic_group(self):
        g = GroupDef(name="VPC", services=["web", "db"])
        assert g.name == "VPC"
        assert g.services == ["web", "db"]

    def test_nested_children(self):
        g = GroupDef(
            name="AWS Cloud",
            children=[
                GroupDef(name="Public", services=["web"]),
                GroupDef(name="Private", services=["db"]),
            ],
        )
        assert len(g.children) == 2
        assert g.children[0].name == "Public"

    def test_empty_defaults(self):
        g = GroupDef(name="Empty")
        assert g.services == []
        assert g.children == []


class TestConnectionDef:
    def test_from_key_remapping(self):
        c = ConnectionDef.model_validate({"from": "web", "to": "db"})
        assert c.from_ == "web"
        assert c.to == "db"

    def test_to_as_list(self):
        c = ConnectionDef.model_validate({"from": "lb", "to": ["web1", "web2"]})
        assert c.to == ["web1", "web2"]

    def test_with_label(self):
        c = ConnectionDef.model_validate({"from": "web", "to": "db", "label": "SQL"})
        assert c.label == "SQL"

    def test_label_optional(self):
        c = ConnectionDef.model_validate({"from": "web", "to": "db"})
        assert c.label is None


class TestRootModel:
    def test_valid_full(self, valid_yaml_dict):
        root = RootModel.model_validate(valid_yaml_dict)
        assert root.diagram.name == "Test Diagram"
        assert "web" in root.diagram.services
        assert len(root.diagram.connections) == 1

    def test_missing_diagram_key(self):
        with pytest.raises(ValidationError):
            RootModel.model_validate({"name": "Bad"})

    def test_empty_services(self):
        with pytest.raises(ValidationError):
            RootModel.model_validate(
                {"diagram": {"name": "Bad", "services": {}}}
            )
