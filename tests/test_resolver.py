"""Tests for type resolver."""

import pytest

from awsdiagram.errors import GraphvizNotFoundError, TypeResolutionError
from awsdiagram.models import ServiceDef
from awsdiagram.resolver import check_graphviz, resolve_type, validate_all_types


class TestResolveType:
    def test_valid_ec2(self):
        cls = resolve_type("compute.EC2")
        assert cls.__name__ == "EC2"

    def test_valid_rds(self):
        cls = resolve_type("database.RDS")
        assert cls.__name__ == "RDS"

    def test_valid_elb(self):
        cls = resolve_type("network.ELB")
        assert cls is not None

    def test_unknown_category(self):
        with pytest.raises(TypeResolutionError, match="Unknown category"):
            resolve_type("fakecategory.Fake")

    def test_unknown_class(self):
        with pytest.raises(TypeResolutionError, match="Unknown class"):
            resolve_type("compute.FakeService")

    def test_invalid_format(self):
        with pytest.raises(TypeResolutionError, match="Invalid type format"):
            resolve_type("just_a_string")


class TestCheckGraphviz:
    def test_graphviz_available(self):
        # Should not raise on systems with Graphviz installed
        check_graphviz()

    def test_graphviz_missing(self, monkeypatch):
        monkeypatch.setattr("awsdiagram.resolver.shutil.which", lambda _: None)
        with pytest.raises(GraphvizNotFoundError, match="dot"):
            check_graphviz()


class TestValidateAllTypes:
    def test_all_valid(self):
        services = {
            "web": ServiceDef(type="compute.EC2", label="Web"),
            "db": ServiceDef(type="database.RDS", label="DB"),
        }
        type_map = validate_all_types(services)
        assert "web" in type_map
        assert "db" in type_map

    def test_some_invalid(self):
        services = {
            "web": ServiceDef(type="compute.EC2", label="Web"),
            "bad": ServiceDef(type="compute.FakeNode", label="Bad"),
        }
        with pytest.raises(TypeResolutionError, match="FakeNode"):
            validate_all_types(services)
