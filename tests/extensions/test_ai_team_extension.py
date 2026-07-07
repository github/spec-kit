import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"
WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-sdd" / "workflow.yml"
BUGFIX_WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-bugfix" / "workflow.yml"


def _run_ai_team_workflow_to_route_gate(
    tmp_path: Path,
    inputs: dict,
    run_id: str,
    workflow_path: Path = WORKFLOW_PATH,
):
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    definition = WorkflowDefinition.from_yaml(workflow_path)
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

    assert set(manifest["requires"]["commands"]) == {
        "speckit.specify",
        "speckit.plan",
        "speckit.checklist",
        "speckit.tasks",
        "speckit.analyze",
        "speckit.implement",
        "speckit.converge",
    }
    assert manifest["hooks"]["after_checklist"]["command"] == (
        "speckit.ai-team.plan-gate"
    )
    assert manifest["hooks"]["after_analyze"]["command"] == (
        "speckit.ai-team.task-gate"
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
        "speckit.ai-team.handoff-spec-sync",
        "speckit.ai-team.handoff-spec.resolve",
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
        "enhancement_internal",
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
    assert config["task_context"]["task_context_file"] == "task-context.yml"
    assert config["code_graph"]["root"] == ".specify/ai-team/codegraph"
    assert set(config["code_graph"]["normalized_outputs"]) == {
        "nodes.jsonl",
        "edges.jsonl",
        "summary.md",
        "adapter-report.md",
    }
    assert (
        config["repositories"]["enhancement_internal"][
            "raw_demand_record_in_coding_repository"
        ]
        is False
    )
    assert (
        config["repositories"]["enhancement_internal"]["visibility"]
        == "internal-only"
    )
    assert config["repositories"]["enhancement_internal"]["customer_visible"] is False
    assert config["issue_workflow"]["type_labels"][
        "enhancement_internal_allowed"
    ] == ["type/feature"]
    assert set(config["issue_workflow"]["type_labels"]["coding_allowed"]) == {
        "type/feature",
        "type/bug",
    }
    assert set(config["issue_workflow"]["state_labels"]) == {
        "state/draft",
        "state/accepted",
        "state/working",
        "state/finished",
        "state/rejected",
        "state/closed",
        "state/superseded",
    }
    assert config["issue_workflow"]["enhancement_internal_allows_bugfix"] is False
    assert (
        config["repositories"]["coding"]["enhancement_handoff_submodule_path"] == ""
    )
    assert config["privacy"]["raw_customer_demand_public"] is False
    assert config["privacy"]["coding_repo_may_record_raw_internal_demand"] is False
    assert config["privacy"]["public_feature_may_start_from_coding_issue"] is True
    assert (
        config["privacy"]["internal_feature_requires_handoff_or_public_safe_summary"]
        is True
    )
    assert config["privacy"]["private_handoff_override_file"] == "spec.override.md"
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
    assert "enhancement-internal" in text
    assert "coding issue URL" in text
    assert "Handoff requirement" in text
    assert "Do not use a local path" in text
    assert "type/feature" in text
    assert "type/bug" in text


def test_ai_team_issue_workflow_document_exists():
    issue_doc = EXTENSION_ROOT / "docs" / "issue-workflow.md"

    assert issue_doc.exists()
    text = issue_doc.read_text(encoding="utf-8")
    assert "enhancement_internal" in text
    assert "`type/feature` only" in text
    assert "`type/bug`" in text
    assert "state/draft" in text
    assert "state/finished" in text
    assert "state/superseded" in text


def test_ai_team_task_context_document_exists():
    context_doc = EXTENSION_ROOT / "docs" / "task-context-package.md"

    assert context_doc.exists()
    text = context_doc.read_text(encoding="utf-8")
    assert "Task Context Package" in text
    assert ".specify/ai-team/tasks/<task-id>/" in text
    assert "task-context.yml" in text
    assert ".specify/workflows/runs/<run-id>/state.json" in text
    assert "specify workflow resume <run-id>" in text
    assert "handoff requirement URL" in text
    assert "coding issue URL" in text


def test_ai_team_task_field_spec_document_exists():
    field_doc = EXTENSION_ROOT / "docs" / "task-field-spec.md"

    assert field_doc.exists()
    text = field_doc.read_text(encoding="utf-8")
    assert "BUG-<repo-slug>-<issue-number>" in text
    assert "FEAT-<repo-slug>-<issue-number>" in text
    assert "REQ-YYYY-NNN" in text
    assert "bug_slug" in text
    assert "coding_issue_url" in text
    assert "handoff_requirement_url" in text
    assert "published_requirement_url" in text
    assert "issue.type_label" in text
    assert "issue.state_label" in text


def test_core_templates_exclude_handoff_spec_override():
    """Core command templates must not embed AI Team handoff / override logic."""
    for rel in (
        "templates/commands/plan.md",
        "templates/commands/tasks.md",
        "templates/commands/checklist.md",
        "templates/commands/analyze.md",
        "templates/commands/implement.md",
        "templates/commands/converge.md",
        "templates/plan-template.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "handoff_requirement_url" not in text, rel
        assert "spec.override.md" not in text, rel


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
    assert "Existing Project Public Feature" in text
    assert "Existing Project Confidential Enterprise Feature" in text
    assert "New Project From Zero" in text
    assert "Resume From The Middle" in text
    assert "speckit.ai-team.context task_id=<task-id> resume=true" in text
    assert "ai-team-sdd feature path" in text
    assert "ai-team-bugfix path" in text
    assert "ai-team-sdd new-project path" in text
    assert "ai-team-sdd resume path" in text


def test_ai_team_workflow_is_bundled_and_uses_init_step():
    catalog = json.loads(
        (REPO_ROOT / "workflows" / "catalog.json").read_text(encoding="utf-8")
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert WORKFLOW_PATH.exists()
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert data["workflow"]["id"] == "ai-team-sdd"
    assert "ai-team-sdd" in catalog["workflows"]
    assert "ai-team-bugfix" in catalog["workflows"]
    assert "workflows/ai-team-sdd" in pyproject
    assert "workflows/ai-team-bugfix" in pyproject
    steps = data["steps"]
    assert steps[0]["type"] == "if"
    assert steps[0]["then"][0]["type"] == "init"
    assert "task_id" in data["inputs"]
    assert "handoff_requirement_url" in data["inputs"]
    assert "published_requirement_url" in data["inputs"]
    assert "resume_from" in data["inputs"]
    assert "bug_slug" not in data["inputs"]
    assert "bug" not in data["inputs"]["work_type"]["enum"]
    assert "new-project" in data["inputs"]["work_type"]["enum"]
    step_ids = [step["id"] for step in steps]
    assert "context-open" in step_ids
    assert "codegraph" in step_ids
    assert "specify" in step_ids
    assert "review-spec" in step_ids
    assert "plan" in step_ids
    assert "checklist" in step_ids
    assert "plan-gate" in step_ids
    assert "review-plan" in step_ids
    assert "tasks" in step_ids
    assert "analyze" in step_ids
    assert "task-gate" in step_ids
    assert "review-tasks" in step_ids
    assert "implement" in step_ids
    assert "converge" in step_ids
    assert "checks" in step_ids
    context_step = next(step for step in steps if step["id"] == "context-open")
    assert context_step["command"] == "speckit.ai-team.context"
    codegraph_step = next(step for step in steps if step["id"] == "codegraph")
    assert codegraph_step["command"] == "speckit.ai-team.codegraph"
    checklist_step = next(step for step in steps if step["id"] == "checklist")
    assert checklist_step["command"] == "speckit.checklist"
    analyze_step = next(step for step in steps if step["id"] == "analyze")
    assert analyze_step["command"] == "speckit.analyze"
    converge_step = next(step for step in steps if step["id"] == "converge")
    assert converge_step["command"] == "speckit.converge"

    assert BUGFIX_WORKFLOW_PATH.exists()
    bugfix = yaml.safe_load(BUGFIX_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert bugfix["workflow"]["id"] == "ai-team-bugfix"
    assert "task_id" in bugfix["inputs"]
    assert "bug_slug" in bugfix["inputs"]
    assert "coding_issue_url" in bugfix["inputs"]
    bugfix_step_ids = [step["id"] for step in bugfix["steps"]]
    assert "review-route" in bugfix_step_ids
    assert "review-impact" in bugfix_step_ids
    assert "bug-assess" in bugfix_step_ids
    assert "review-assessment" in bugfix_step_ids
    assert "bug-fix" in bugfix_step_ids
    assert "review-fix" in bugfix_step_ids
    assert "bug-test" in bugfix_step_ids
    assert "checks" in bugfix_step_ids
    assert "evidence" in bugfix_step_ids


def test_ai_team_bugfix_workflow_routes_to_first_gate(tmp_path):
    run_id = "ai-team-bugfix-bug-project-alpha-123"
    state = _run_ai_team_workflow_to_route_gate(
        tmp_path,
        {
            "request": "Fix upload timeout reported by support",
            "task_id": "BUG-project-alpha-123",
            "bug_slug": "bug-project-alpha-123",
            "coding_issue_url": "https://example.com/org/project/issues/123",
        },
        run_id,
        workflow_path=BUGFIX_WORKFLOW_PATH,
    )

    context_args = state.step_results["context-open"]["input"]["args"]
    route_args = state.step_results["route"]["input"]["args"]

    for args in (context_args, route_args):
        assert f"workflow_run_id={run_id}" in args
        assert "work_type=bug" in args
        assert "task_id=BUG-project-alpha-123" in args
        assert "bug_slug=bug-project-alpha-123" in args
        assert "coding_issue_url=https://example.com/org/project/issues/123" in args


@pytest.mark.parametrize(
    ("case_name", "inputs", "expected_fragments"),
    [
        (
            "existing project public feature",
            {
                "request": "Implement public search result export",
                "work_type": "feature",
                "coding_issue_url": "https://example.com/org/project/issues/456",
            },
            [
                "work_type=feature",
                "coding_issue_url=https://example.com/org/project/issues/456",
                "handoff_requirement_url=",
            ],
        ),
        (
            "existing project confidential feature",
            {
                "request": "Implement REQ-2026-015 search result export",
                "work_type": "feature",
                "handoff_requirement_url": "https://example.com/enhancements/rfcs/REQ-2026-015",
            },
            [
                "work_type=feature",
                "handoff_requirement_url=https://example.com/enhancements/rfcs/REQ-2026-015",
                "coding_issue_url=",
            ],
        ),
        (
            "new project from zero",
            {
                "request": "Create the initial customer notification service",
                "work_type": "new-project",
                "bootstrap_workspace": True,
                "handoff_requirement_url": "https://example.com/enhancements/rfcs/REQ-2026-020",
            },
            [
                "work_type=new-project",
                "handoff_requirement_url=https://example.com/enhancements/rfcs/REQ-2026-020",
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
                "handoff_requirement_url": "https://example.com/enhancements/rfcs/REQ-2026-015",
            },
            [
                "task_id=REQ-2026-015",
                "work_type=feature",
                "resume_from=tasks-ready",
                "handoff_requirement_url=https://example.com/enhancements/rfcs/REQ-2026-015",
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
