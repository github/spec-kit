import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"


def test_ai_team_extension_manifest_and_catalog_are_in_sync():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (REPO_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
    )

    assert manifest["extension"]["id"] == "ai-team"
    assert "ai-team" in catalog["extensions"]
    assert (
        catalog["extensions"]["ai-team"]["version"]
        == manifest["extension"]["version"]
    )
    assert catalog["extensions"]["ai-team"]["bundled"] is True


def test_ai_team_extension_command_files_exist():
    manifest = yaml.safe_load(
        (EXTENSION_ROOT / "extension.yml").read_text(encoding="utf-8")
    )

    command_names = {command["name"] for command in manifest["provides"]["commands"]}
    assert command_names == {
        "speckit.ai-team.workspace",
        "speckit.ai-team.start",
        "speckit.ai-team.requirement",
        "speckit.ai-team.impact",
        "speckit.ai-team.handoff",
        "speckit.ai-team.plan-gate",
        "speckit.ai-team.task-gate",
        "speckit.ai-team.feature-review",
        "speckit.ai-team.checks",
        "speckit.ai-team.evidence",
        "speckit.ai-team.pr",
        "speckit.ai-team.review",
        "speckit.ai-team.retrospect",
        "speckit.ai-team.support",
    }

    for command in manifest["provides"]["commands"]:
        command_file = EXTENSION_ROOT / command["file"]
        assert command_file.exists(), command["file"]
        assert command_file.read_text(encoding="utf-8").startswith("---\n")


def test_ai_team_config_template_defines_repository_and_role_contracts():
    config = yaml.safe_load(
        (EXTENSION_ROOT / "config-template.yml").read_text(encoding="utf-8")
    )

    assert set(config["repositories"]) == {
        "requirements_internal",
        "requirements_published",
        "coding",
    }
    assert config["bootstrap"]["use_specify_init"] is True
    assert set(config["agent_tools"]["supported_integrations"]) == {
        "codex",
        "claude",
        "cursor-agent",
        "trae",
    }
    assert (
        config["repositories"]["requirements_internal"]["record_in_coding_repository"]
        is False
    )
    assert (
        config["repositories"]["requirements_published"]["authoritative_reference"]
        == "published_url"
    )
    assert config["repositories"]["coding"]["requirements_submodule_path"] == "requirements"
    assert config["privacy"]["raw_customer_demand_public"] is False
    assert config["privacy"]["coding_repo_may_record_requirements_internal"] is False
    assert config["privacy"]["feature_requires_published_requirement_url"] is True
    assert set(config["roles"]) == {"specify", "plan", "tasks_and_implement"}
    assert all(role["context_isolation"] is True for role in config["roles"].values())


def test_ai_team_support_model_document_exists():
    support_doc = EXTENSION_ROOT / "docs" / "skill-knowledge-memory.md"

    assert support_doc.exists()
    text = support_doc.read_text(encoding="utf-8")
    assert "Skill Layer" in text
    assert "Knowledge Layer" in text
    assert "Memory Layer" in text
    assert "Decision Memory" in text
    assert "Attempt Memory" in text
    assert "Third-party sources to review" in text
    assert "Precedence" in text


def test_ai_team_repository_boundary_document_exists():
    boundary_doc = EXTENSION_ROOT / "docs" / "repository-boundary.md"

    assert boundary_doc.exists()
    text = boundary_doc.read_text(encoding="utf-8")
    assert "requirements-published" in text
    assert "requirements-internal" in text
    assert "Git submodule" in text
    assert "published requirement URL" in text
    assert "not a local submodule path" in text


def test_ai_team_workflow_is_bundled_and_uses_init_step():
    workflow = REPO_ROOT / "workflows" / "ai-team-sdd" / "workflow.yml"
    catalog = json.loads(
        (REPO_ROOT / "workflows" / "catalog.json").read_text(encoding="utf-8")
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert workflow.exists()
    data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    assert data["workflow"]["id"] == "ai-team-sdd"
    assert "ai-team-sdd" in catalog["workflows"]
    assert "workflows/ai-team-sdd" in pyproject
    steps = data["steps"]
    assert steps[0]["type"] == "if"
    assert steps[0]["then"][0]["type"] == "init"
