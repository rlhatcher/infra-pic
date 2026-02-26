"""Tests for Terraform importer."""

import json

import pytest
import yaml

from awsdiagram.errors import TerraformImportError
from awsdiagram.terraform.importer import import_terraform


class TestImportTerraform:
    def test_basic_import(self, terraform_plan_file):
        result = import_terraform(terraform_plan_file)
        data = yaml.safe_load(result)
        assert "diagram" in data
        assert len(data["diagram"]["services"]) > 0

    def test_uses_tag_names(self, terraform_plan_file):
        result = import_terraform(terraform_plan_file)
        data = yaml.safe_load(result)
        labels = [s["label"] for s in data["diagram"]["services"].values()]
        assert "Web Server" in labels
        assert "Database" in labels

    def test_groups_by_subnet(self, terraform_plan_file):
        result = import_terraform(terraform_plan_file)
        data = yaml.safe_load(result)
        groups = data["diagram"].get("groups", [])
        # Should have groups from subnet inference
        assert len(groups) > 0

    def test_state_format(self, tmp_path):
        """Supports Terraform state format (values.root_module)."""
        state = {
            "values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "aws_instance",
                            "name": "app",
                            "values": {"tags": {"Name": "App Server"}},
                        }
                    ]
                }
            }
        }
        p = tmp_path / "state.json"
        p.write_text(json.dumps(state))
        result = import_terraform(p)
        data = yaml.safe_load(result)
        assert len(data["diagram"]["services"]) == 1

    def test_child_modules(self, tmp_path):
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [],
                    "child_modules": [
                        {
                            "address": "module.app",
                            "resources": [
                                {
                                    "type": "aws_instance",
                                    "name": "web",
                                    "values": {"tags": {"Name": "Nested Web"}},
                                }
                            ],
                        }
                    ],
                }
            }
        }
        p = tmp_path / "nested.json"
        p.write_text(json.dumps(plan))
        result = import_terraform(p)
        data = yaml.safe_load(result)
        assert len(data["diagram"]["services"]) == 1

    def test_file_not_found(self, tmp_path):
        with pytest.raises(TerraformImportError, match="File not found"):
            import_terraform(tmp_path / "nope.json")

    def test_bad_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{{")
        with pytest.raises(TerraformImportError, match="Failed to read"):
            import_terraform(p)

    def test_no_resources(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text(json.dumps({"random_key": {}}))
        with pytest.raises(TerraformImportError, match="No resources found"):
            import_terraform(p)
