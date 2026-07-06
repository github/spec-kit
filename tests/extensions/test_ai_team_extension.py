import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"


def test_ai_team_extension_manifest_and_catalog_are_in_sync():
    manifest = yaml.safe_load((EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8"))
    catalog = json.loads((REPO_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8"))

    assert manifest["extension"]["id"] == "ai-team"
    assert "ai-team" in catalog["extensions"]
    assert catalog["extensions"]["ai-team"]["version"] == manifest["extension"]["version"]
    assert catalog["extensions"]["ai-team"]["bundled"] is True


def test_ai_team_extension_command_files_exist():
    manifest = yaml.safe_load((EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8"))

    command_names = {command["name"] for command in manifest["provides"]["commands"]}
    assert command_names == {
        "speckit.ai-team.workspace",
        "speckit.ai-team.handoff",
        "speckit.ai-team.plan-gate",
        "speckit.ai-team.task-gate",
        "speckit.ai-team.evidence",
    }

    for command in manifest["provides"]["commands"]:
        command_file = EXTENSION_ROOT / command["file"]
        assert command_file.exists(), command["file"]
        assert command_file.read_text(encoding="utf-8").startswith("---\n")


def test_ai_team_config_template_defines_repository_and_role_contracts():
    config = yaml.safe_load((EXTENSION_ROOT / "config-template.yml").read_text(encoding="utf-8"))

    assert set(config["repositories"]) == {"enhancement", "coding"}
    assert config["repositories"]["enhancement"]["visibility"] == "private"
    assert config["privacy"]["raw_customer_demand_public"] is False
    assert set(config["roles"]) == {"specify", "plan", "tasks_and_implement"}
    assert all(role["context_isolation"] is True for role in config["roles"].values())
