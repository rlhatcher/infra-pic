"""Tests for YAML parser."""

import pytest
import yaml

from awsdiagram.errors import (
    SchemaValidationError,
    ServiceReferenceError,
    YamlLoadError,
)
from awsdiagram.parser import load_yaml, parse


class TestLoadYaml:
    def test_file_not_found(self, tmp_path):
        with pytest.raises(YamlLoadError, match="File not found"):
            load_yaml(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(":\n  :\n    - [invalid")
        with pytest.raises(YamlLoadError, match="Invalid YAML"):
            load_yaml(p)

    def test_non_dict_yaml(self, tmp_path):
        p = tmp_path / "list.yaml"
        p.write_text("- item1\n- item2")
        with pytest.raises(YamlLoadError, match="Expected a YAML mapping"):
            load_yaml(p)

    def test_valid_load(self, yaml_file):
        data = load_yaml(yaml_file)
        assert "diagram" in data


class TestParse:
    def test_valid_parse(self, yaml_file):
        diagram = parse(yaml_file)
        assert diagram.name == "Test Diagram"
        assert len(diagram.services) == 2

    def test_schema_error(self, tmp_path):
        p = tmp_path / "bad_schema.yaml"
        p.write_text(yaml.dump({"diagram": {"name": "Bad"}}))
        with pytest.raises(SchemaValidationError):
            parse(p)

    def test_unknown_service_in_group(self, tmp_path):
        data = {
            "diagram": {
                "name": "Test",
                "services": {
                    "web": {"type": "compute.EC2", "label": "Web"},
                },
                "groups": [{"name": "VPC", "services": ["web", "ghost"]}],
            }
        }
        p = tmp_path / "bad_ref.yaml"
        p.write_text(yaml.dump(data))
        with pytest.raises(ServiceReferenceError, match="ghost"):
            parse(p)

    def test_unknown_service_in_connection_from(self, tmp_path):
        data = {
            "diagram": {
                "name": "Test",
                "services": {
                    "web": {"type": "compute.EC2", "label": "Web"},
                },
                "connections": [{"from": "ghost", "to": "web"}],
            }
        }
        p = tmp_path / "bad_conn.yaml"
        p.write_text(yaml.dump(data))
        with pytest.raises(ServiceReferenceError, match="ghost"):
            parse(p)

    def test_unknown_service_in_connection_to(self, tmp_path):
        data = {
            "diagram": {
                "name": "Test",
                "services": {
                    "web": {"type": "compute.EC2", "label": "Web"},
                },
                "connections": [{"from": "web", "to": "ghost"}],
            }
        }
        p = tmp_path / "bad_to.yaml"
        p.write_text(yaml.dump(data))
        with pytest.raises(ServiceReferenceError, match="ghost"):
            parse(p)

    def test_nested_groups(self, nested_yaml_file):
        diagram = parse(nested_yaml_file)
        assert len(diagram.groups) == 1
        assert len(diagram.groups[0].children) == 2
