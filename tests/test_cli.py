"""Tests for the CLI."""

import json

import pytest
import yaml
from click.testing import CliRunner

from awsdiagram.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestRenderCommand:
    def test_render_missing_file(self, runner):
        result = runner.invoke(main, ["render", "nonexistent.yaml"])
        assert result.exit_code != 0

    def test_render_invalid_yaml(self, runner, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("not: valid: yaml: [")
        result = runner.invoke(main, ["render", str(p)])
        assert result.exit_code != 0


class TestValidateCommand:
    def test_validate_valid_file(self, runner, yaml_file):
        result = runner.invoke(main, ["validate", str(yaml_file)])
        assert result.exit_code == 0
        assert "Valid" in result.output

    def test_validate_missing_file(self, runner):
        result = runner.invoke(main, ["validate", "nonexistent.yaml"])
        assert result.exit_code != 0

    def test_validate_bad_schema(self, runner, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text(yaml.dump({"diagram": {"name": "Bad"}}))
        result = runner.invoke(main, ["validate", str(p)])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_validate_bad_reference(self, runner, tmp_path):
        data = {
            "diagram": {
                "name": "Test",
                "services": {"web": {"type": "compute.EC2", "label": "Web"}},
                "groups": [{"name": "G", "services": ["web", "ghost"]}],
            }
        }
        p = tmp_path / "badref.yaml"
        p.write_text(yaml.dump(data))
        result = runner.invoke(main, ["validate", str(p)])
        assert result.exit_code != 0
        assert "ghost" in result.output


class TestImportCommand:
    def test_import_terraform(self, runner, terraform_plan_file, tmp_path):
        out = tmp_path / "result.yaml"
        result = runner.invoke(
            main,
            ["import", "terraform", str(terraform_plan_file), "-o", str(out)],
        )
        assert result.exit_code == 0
        assert "Imported" in result.output
        assert out.exists()
        data = yaml.safe_load(out.read_text())
        assert "diagram" in data

    def test_import_terraform_missing_file(self, runner):
        result = runner.invoke(main, ["import", "terraform", "nope.json"])
        assert result.exit_code != 0

    def test_import_terraform_bad_json(self, runner, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json")
        result = runner.invoke(main, ["import", "terraform", str(p)])
        assert result.exit_code != 0


class TestHelp:
    def test_main_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "render" in result.output
        assert "validate" in result.output
        assert "import" in result.output
