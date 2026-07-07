import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"
WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-sdd" / "workflow.yml"


def _run_ai_team_workflow_to_route_gate(tmp_path: Path, inputs: dict, run_id: str):
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    definition = WorkflowDefinition.from_yaml(WORKFLOW_PATH)
    engine = WorkflowEngine(tmp_path)
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with (
        patch(
            "specify_cli.workflows.steps.command.shutil.which",
            return_value="/usr/bin/codex",
        ),
        patch(
            "specify_cli.integrations.base.shutil.which",
            return_value="/usr/bin/codex",
        ),
        patch("subprocess.run", return_value=mock_result),
    ):
        state = engine.execute(definition, inputs, run_id=run_id)

    assert state.status == RunStatus.PAUSED
    assert state.step_results["context-open"]["status"] == "completed"
    assert state.step_results["route"]["status"] == "completed"
    assert state.step_results["review-route"]["status"] == "paused"
    return state


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
        "speckit.ai-team.context",
        "speckit.ai-team.requirement",
        "speckit.ai-team.codegraph",
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
    assert config["task_context"]["root"] == ".specify/ai-team/tasks"
    assert config["task_context"]["context_pack_file"] == "context-pack.md"
    assert config["task_context"]["state_file"] == "state.yml"
    assert config["code_graph"]["root"] == ".specify/ai-team/codegraph"
    assert set(config["code_graph"]["normalized_outputs"]) == {
        "nodes.jsonl",
        "edges.jsonl",
        "summary.md",
        "adapter-report.md",
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


def test_ai_team_task_context_document_exists():
    context_doc = EXTENSION_ROOT / "docs" / "task-context-package.md"

    assert context_doc.exists()
    text = context_doc.read_text(encoding="utf-8")
    assert "Task Context Package" in text
    assert ".specify/ai-team/tasks/<task-id>/" in text
    assert "specify workflow resume <run-id>" in text
    assert "published requirement URL" in text


def test_ai_team_code_graph_adapter_document_exists():
    graph_doc = EXTENSION_ROOT / "docs" / "code-graph-adapters.md"

    assert graph_doc.exists()
    text = graph_doc.read_text(encoding="utf-8")
    assert "Adapter Contract" in text
    assert "SCIP" in text
    assert "Joern" in text
    assert "CodeQL" in text
    assert "tree-sitter" in text
    assert "nodes.jsonl" in text
    assert "edges.jsonl" in text


def test_ai_team_user_journeys_document_exists():
    journeys_doc = EXTENSION_ROOT / "docs" / "user-journeys.md"

    assert journeys_doc.exists()
    text = journeys_doc.read_text(encoding="utf-8")
    assert "Existing Project Bug Fix" in text
    assert "Existing Project New Feature" in text
    assert "New Project From Zero" in text
    assert "Resume From The Middle" in text
    assert "speckit.ai-team.context task_id=<task-id> resume=true" in text


def test_ai_team_workflow_is_bundled_and_uses_init_step():
    catalog = json.loads(
        (REPO_ROOT / "workflows" / "catalog.json").read_text(encoding="utf-8")
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert WORKFLOW_PATH.exists()
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert data["workflow"]["id"] == "ai-team-sdd"
    assert "ai-team-sdd" in catalog["workflows"]
    assert "workflows/ai-team-sdd" in pyproject
    steps = data["steps"]
    assert steps[0]["type"] == "if"
    assert steps[0]["then"][0]["type"] == "init"
    assert "task_id" in data["inputs"]
    assert "resume_from" in data["inputs"]
    assert "new-project" in data["inputs"]["work_type"]["enum"]
    step_ids = [step["id"] for step in steps]
    assert "context-open" in step_ids
    assert "codegraph" in step_ids
    context_step = next(step for step in steps if step["id"] == "context-open")
    assert context_step["command"] == "speckit.ai-team.context"
    codegraph_step = next(step for step in steps if step["id"] == "codegraph")
    assert codegraph_step["command"] == "speckit.ai-team.codegraph"


@pytest.mark.parametrize(
    ("case_name", "inputs", "expected_fragments"),
    [
        (
            "existing project bug fix",
            {
                "request": "Fix upload timeout reported by support",
                "work_type": "bug",
                "coding_issue_url": "https://example.com/org/project/issues/123",
            },
            [
                "work_type=bug",
                "coding_issue_url=https://example.com/org/project/issues/123",
                "published_requirement_url=",
            ],
        ),
        (
            "existing project feature",
            {
                "request": "Implement REQ-2026-015 search result export",
                "work_type": "feature",
                "published_requirement_url": "https://example.com/requirements/rfcs/REQ-2026-015",
            },
            [
                "work_type=feature",
                "published_requirement_url=https://example.com/requirements/rfcs/REQ-2026-015",
                "coding_issue_url=",
            ],
        ),
        (
            "new project from zero",
            {
                "request": "Create the initial customer notification service",
                "work_type": "new-project",
                "bootstrap_workspace": True,
                "published_requirement_url": "https://example.com/requirements/rfcs/REQ-2026-020",
            },
            [
                "work_type=new-project",
                "published_requirement_url=https://example.com/requirements/rfcs/REQ-2026-020",
                "resume_from=auto",
            ],
        ),
        (
            "resume from task gate",
            {
                "request": "Continue REQ-2026-015 after task gate approval",
                "task_id": "REQ-2026-015",
                "work_type": "feature",
                "resume_from": "tasks-ready",
                "published_requirement_url": "https://example.com/requirements/rfcs/REQ-2026-015",
            },
            [
                "task_id=REQ-2026-015",
                "work_type=feature",
                "resume_from=tasks-ready",
                "published_requirement_url=https://example.com/requirements/rfcs/REQ-2026-015",
            ],
        ),
    ],
)
def test_ai_team_workflow_routes_core_user_journeys(
    tmp_path, case_name, inputs, expected_fragments
):
    run_id = "ai-team-" + case_name.replace(" ", "-")
    state = _run_ai_team_workflow_to_route_gate(tmp_path, inputs, run_id)

    context_args = state.step_results["context-open"]["input"]["args"]
    route_args = state.step_results["route"]["input"]["args"]

    assert f"workflow_run_id={run_id}" in context_args
    assert f"workflow_run_id={run_id}" in route_args
    for fragment in expected_fragments:
        assert fragment in context_args
        assert fragment in route_args

    bootstrap_result = state.step_results["bootstrap-if-requested"]["output"][
        "condition_result"
    ]
    assert bootstrap_result is (inputs.get("bootstrap_workspace") is True)
    if inputs.get("bootstrap_workspace") is True:
        assert state.step_results["bootstrap"]["status"] == "completed"
        assert "--integration" in state.step_results["bootstrap"]["output"]["argv"]
