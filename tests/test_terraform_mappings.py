"""Tests for Terraform mappings."""

import pytest

from awsdiagram.resolver import resolve_type
from awsdiagram.terraform.mappings import TERRAFORM_TO_DIAGRAMS


class TestMappings:
    def test_at_least_30_mappings(self):
        assert len(TERRAFORM_TO_DIAGRAMS) >= 30

    def test_all_mappings_resolve(self):
        """Every mapping should resolve to a real diagrams.aws.* class."""
        errors = []
        for tf_type, diagram_type in TERRAFORM_TO_DIAGRAMS.items():
            try:
                cls = resolve_type(diagram_type)
            except Exception as e:
                errors.append(f"{tf_type} -> {diagram_type}: {e}")
        assert not errors, "Failed mappings:\n" + "\n".join(errors)

    def test_common_types_present(self):
        """Key AWS resource types should be mapped."""
        expected = [
            "aws_instance",
            "aws_s3_bucket",
            "aws_db_instance",
            "aws_lambda_function",
            "aws_vpc",
            "aws_lb",
            "aws_sqs_queue",
            "aws_sns_topic",
            "aws_dynamodb_table",
            "aws_iam_role",
        ]
        for tf_type in expected:
            assert tf_type in TERRAFORM_TO_DIAGRAMS, f"Missing mapping for {tf_type}"
