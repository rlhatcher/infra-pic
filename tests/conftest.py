"""Shared fixtures for tests."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def valid_yaml_dict():
    """Minimal valid YAML DSL as a dict."""
    return {
        "diagram": {
            "name": "Test Diagram",
            "services": {
                "web": {"type": "compute.EC2", "label": "Web Server"},
                "db": {"type": "database.RDS", "label": "Database"},
            },
            "groups": [
                {
                    "name": "VPC",
                    "services": ["web", "db"],
                }
            ],
            "connections": [
                {"from": "web", "to": "db"},
            ],
        }
    }


@pytest.fixture
def nested_yaml_dict():
    """YAML DSL with nested groups."""
    return {
        "diagram": {
            "name": "Nested Test",
            "services": {
                "lb": {"type": "network.ELB", "label": "Load Balancer"},
                "web": {"type": "compute.EC2", "label": "Web Server"},
                "db": {"type": "database.RDS", "label": "Database"},
            },
            "groups": [
                {
                    "name": "AWS Cloud",
                    "children": [
                        {"name": "Public Subnet", "services": ["lb", "web"]},
                        {"name": "Private Subnet", "services": ["db"]},
                    ],
                }
            ],
            "connections": [
                {"from": "lb", "to": "web"},
                {"from": "web", "to": "db", "label": "SQL"},
            ],
        }
    }


@pytest.fixture
def yaml_file(valid_yaml_dict, tmp_path):
    """Write valid YAML to a temp file and return its path."""
    p = tmp_path / "test.yaml"
    p.write_text(yaml.dump(valid_yaml_dict))
    return p


@pytest.fixture
def nested_yaml_file(nested_yaml_dict, tmp_path):
    """Write nested YAML to a temp file and return its path."""
    p = tmp_path / "nested.yaml"
    p.write_text(yaml.dump(nested_yaml_dict))
    return p


@pytest.fixture
def sample_terraform_plan():
    """Minimal Terraform plan JSON as a dict."""
    return {
        "format_version": "1.2",
        "planned_values": {
            "root_module": {
                "resources": [
                    {
                        "address": "aws_instance.web",
                        "type": "aws_instance",
                        "name": "web",
                        "values": {
                            "instance_type": "t3.micro",
                            "subnet_id": "subnet-abc123",
                            "tags": {"Name": "Web Server"},
                        },
                    },
                    {
                        "address": "aws_db_instance.db",
                        "type": "aws_db_instance",
                        "name": "db",
                        "values": {
                            "engine": "postgres",
                            "subnet_id": "subnet-def456",
                            "tags": {"Name": "Database"},
                        },
                    },
                    {
                        "address": "aws_s3_bucket.data",
                        "type": "aws_s3_bucket",
                        "name": "data",
                        "values": {
                            "bucket": "my-data-bucket",
                            "tags": {"Name": "Data Bucket"},
                        },
                    },
                ],
                "child_modules": [],
            }
        },
    }


@pytest.fixture
def terraform_plan_file(sample_terraform_plan, tmp_path):
    """Write Terraform plan to a temp file and return its path."""
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(sample_terraform_plan))
    return p
