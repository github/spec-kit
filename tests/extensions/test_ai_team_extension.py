import json
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"
WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-sdd" / "workflow.yml"
BUGFIX_WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-bugfix" / "workflow.yml"
MEMORY_ADAPTER_PATH = EXTENSION_ROOT / "scripts" / "memory_adapter.py"


def _load_memory_adapter():
    spec = importlib.util.spec_from_file_location("ai_team_memory_adapter", MEMORY_ADAPTER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _memory_card(tier: str, privacy: str = "department-internal") -> str:
    return f"""---
memory_type: bugfix_lesson
tier: {tier}
privacy: {privacy}
owner: module-maintainer
---

# Retry exhaustion

- Root cause: retry budget was shared across requests.
"""


def _staged_card(tmp_path: Path, name: str, content: str) -> Path:
    source = tmp_path / ".specify" / "ai-team" / "memory" / "staging" / name
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(content, encoding="utf-8")
    return source


def _collect_step_ids(steps: list) -> list[str]:
    """Return step ids from a workflow, including nested control-flow bodies."""
    ids: list[str] = []
    for step in steps:
        step_id = step.get("id")
        if step_id:
            ids.append(step_id)
        for key in ("then", "else", "steps"):
            nested = step.get(key)
            if isinstance(nested, list):
                ids.extend(_collect_step_ids(nested))
    return ids


def _run_ai_team_workflow_to_context_gate(
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
    assert state.step_results["review-context"]["status"] == "paused"
    assert "route" not in state.step_results
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
        "speckit.tasks",
        "speckit.analyze",
        "speckit.implement",
        "speckit.converge",
    }
    assert "before_checklist" not in manifest["hooks"]
    assert "before_tasks" not in manifest["hooks"]
    assert "before_analyze" not in manifest["hooks"]
    assert "before_implement" not in manifest["hooks"]
    assert "before_converge" not in manifest["hooks"]
    assert manifest["hooks"]["before_plan"]["command"] == "speckit.ai-team.handoff-spec-sync"
    assert "after_checklist" not in manifest["hooks"]
    assert "after_analyze" not in manifest["hooks"]
    assert "after_implement" not in manifest["hooks"]

    command_names = {command["name"] for command in manifest["provides"]["commands"]}
    assert command_names == {
        "speckit.ai-team.workspace",
        "speckit.ai-team.start",
        "speckit.ai-team.context",
        "speckit.ai-team.requirement",
        "speckit.ai-team.codegraph",
        "speckit.ai-team.impact",
        "speckit.ai-team.plan-check",
        "speckit.ai-team.handoff",
        "speckit.ai-team.handoff-spec-sync",
        "speckit.ai-team.feature-review",
        "speckit.ai-team.pr",
        "speckit.ai-team.review",
        "speckit.ai-team.retrospect",
        "speckit.ai-team.memory-consolidate",
        "speckit.ai-team.release-archive",
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
    assert config["work_context"]["root"] == ".specify/ai-team/work"
    assert config["work_context"]["context_pack_file"] == "context-pack.md"
    assert config["work_context"]["work_context_file"] == "work-context.yml"
    assert config["memory"]["service"]["default_backend"] == "file"
    assert config["memory"]["service"]["supported_backends"] == ["file", "mem0"]
    assert config["memory"]["service"]["mem0"]["optional_package"] == "mem0ai"
    assert config["memory"]["service"]["store_raw_transcripts_by_default"] is False
    assert config["memory"]["tiers"]["local"]["upload"] is False
    assert config["memory"]["tiers"]["local"]["docs"] is False
    assert config["memory"]["tiers"]["local"]["git_policy"] == "ignore-or-local-only"
    assert config["memory"]["tiers"]["department"]["upload"] is True
    assert config["memory"]["tiers"]["department"]["docs"] is False
    assert (
        config["memory"]["tiers"]["department"]["git_policy"]
        == "internal-only-or-service-sync"
    )
    assert config["memory"]["tiers"]["enterprise"]["upload"] is True
    assert config["memory"]["tiers"]["enterprise"]["docs"] is True
    assert config["memory"]["tiers"]["enterprise"]["git_policy"] == "commit-after-review"
    assert config["release_archive"]["private_root"] == ".specify/ai-team/releases/private"
    assert config["release_archive"]["enterprise_root"] == "docs/ai-team/memory/releases"
    assert config["release_archive"]["default_privacy"] == "department-internal"
    assert config["release_archive"]["default_target_tier"] == "department"
    assert config["release_archive"]["delete_raw_evidence_by_default"] is False
    assert set(config["release_archive"]["enterprise_outputs"]) == {
        "release-summary.md",
        "shipped-work-index.md",
        "bugfix-lessons.md",
        "feature-decisions.md",
        "migration-playbook.md",
    }
    assert set(config["release_archive"]["private_outputs"]) == {
        "evidence-rollup.md",
        "archived-work.yml",
        "privacy-review.md",
    }
    assert "root" not in config["code_graph"]
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


def test_memory_adapter_generates_idempotent_git_ignore_rules(tmp_path):
    adapter = _load_memory_adapter()
    (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")

    adapter.ensure_memory_gitignore(tmp_path)
    adapter.ensure_memory_gitignore(tmp_path)

    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("dist/\n")
    assert text.count(adapter.IGNORE_START) == 1
    for ignored in adapter.IGNORE_PATHS:
        assert ignored in text


def test_memory_adapter_private_paths_are_ignored_by_git(tmp_path):
    adapter = _load_memory_adapter()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    source = _staged_card(tmp_path, "candidate.md", _memory_card("local", "private"))

    result = adapter.persist_memory(
        project_root=tmp_path,
        source=source,
        tier="local",
    )

    destination = tmp_path / result["path"]
    assert destination.exists()
    ignored = subprocess.run(
        ["git", "-C", str(tmp_path), "check-ignore", "-q", str(destination)],
        check=False,
    )
    assert ignored.returncode == 0
    assert result["backend"] == "file"


def test_memory_adapter_writes_enterprise_memory_to_docs(tmp_path):
    adapter = _load_memory_adapter()
    source = _staged_card(
        tmp_path, "reviewed.md", _memory_card("enterprise", "public-safe")
    )

    result = adapter.persist_memory(
        project_root=tmp_path,
        source=source,
        tier="enterprise",
    )

    assert result["path"] == "docs/ai-team/memory/reviewed.md"
    assert (tmp_path / result["index"]).exists()


def test_memory_adapter_mem0_mirrors_sanitized_non_private_card(tmp_path, monkeypatch):
    adapter = _load_memory_adapter()
    source = _staged_card(tmp_path, "department.md", _memory_card("department"))
    config = tmp_path / "config.yml"
    config.write_text(
        """memory:
  service:
    mem0:
      api_key_env: TEST_MEM0_KEY
  tiers:
    department:
      path: .specify/ai-team/memory/department
      namespace: ai-team/example/department
""",
        encoding="utf-8",
    )
    client = MagicMock()
    client.add.return_value = {"id": "memory-123"}
    client_type = MagicMock(return_value=client)
    monkeypatch.setenv("TEST_MEM0_KEY", "secret-not-written")
    monkeypatch.setattr(
        adapter.importlib,
        "import_module",
        lambda _name: SimpleNamespace(MemoryClient=client_type),
    )

    result = adapter.persist_memory(
        project_root=tmp_path,
        source=source,
        tier="department",
        backend="mem0",
        config_path=config,
    )

    client_type.assert_called_once_with(api_key="secret-not-written")
    client.add.assert_called_once()
    assert result["remote"] == {"id": "memory-123"}
    assert "secret-not-written" not in (tmp_path / result["index"]).read_text(
        encoding="utf-8"
    )


def test_memory_adapter_rejects_private_mem0_sync(tmp_path, monkeypatch):
    adapter = _load_memory_adapter()
    source = _staged_card(tmp_path, "private.md", _memory_card("local", "private"))

    with pytest.raises(adapter.MemoryAdapterError, match="cannot be synced"):
        adapter.persist_memory(
            project_root=tmp_path,
            source=source,
            tier="local",
            backend="mem0",
        )


def test_ai_team_support_model_document_exists():
    support_doc = EXTENSION_ROOT / "docs" / "skill-knowledge-memory.md"

    assert support_doc.exists()
    text = support_doc.read_text(encoding="utf-8")
    assert "Skill Layer" in text
    assert "Knowledge Layer" in text
    assert "Memory Layer" in text
    assert "Decision Memory" in text
    assert "Attempt Memory" in text
    assert "Memory Consolidation Flow" in text
    assert "local memory" in text
    assert "department memory" in text
    assert "enterprise memory" in text
    assert "mem0-style memory" in text
    assert "speckit.ai-team.memory-consolidate" in text
    assert "release-summary.md" in text
    assert "bugfix-lessons.md" in text
    assert "Third-party sources to review" in text
    assert "Precedence" in text


def test_ai_team_memory_tiers_document_exists():
    memory_doc = EXTENSION_ROOT / "docs" / "memory-tiers.md"

    assert memory_doc.exists()
    text = memory_doc.read_text(encoding="utf-8")
    assert "AI Team Memory Tiers" in text
    assert "local memory" in text
    assert "department memory" in text
    assert "enterprise memory" in text
    assert "mem0-style memory" in text
    assert "speckit.ai-team.memory-consolidate" in text
    assert "speckit.ai-team.release-archive" in text


def test_ai_team_release_archive_document_exists():
    release_doc = EXTENSION_ROOT / "docs" / "release-archive.md"

    assert release_doc.exists()
    text = release_doc.read_text(encoding="utf-8")
    assert "Release Archive and Knowledge Consolidation" in text
    assert "bugfix-lessons.md" in text
    assert "migration-playbook.md" in text
    assert "speckit.ai-team.memory-consolidate" in text
    assert "speckit.ai-team.release-archive" in text
    assert "not a mandatory pre-release gate" in text
    assert "public-safe" in text


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


def test_ai_team_work_context_document_exists():
    context_doc = EXTENSION_ROOT / "docs" / "work-context-package.md"

    assert context_doc.exists()
    text = context_doc.read_text(encoding="utf-8")
    assert "Work Context Package" in text
    assert ".specify/ai-team/work/<work_slug>/" in text
    assert "work-context.yml" in text
    assert ".specify/workflows/runs/<run-id>/state.json" in text
    assert "specify workflow resume <run-id>" in text
    assert "handoff requirement URL" in text
    assert "coding issue URL" in text
    assert "`archived`" in text
    assert "speckit.ai-team.memory-consolidate" in text
    assert "speckit.ai-team.release-archive" in text


def test_ai_team_work_field_spec_document_exists():
    field_doc = EXTENSION_ROOT / "docs" / "work-field-spec.md"

    assert field_doc.exists()
    text = field_doc.read_text(encoding="utf-8")
    assert "work_slug" in text
    assert "003-user-auth" in text
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
    assert "speckit.ai-team.context work_slug=<work_slug> resume=true" in text
    assert "ai-team-sdd feature path" in text
    assert "ai-team-bugfix path" in text
    assert "ai-team-sdd new-project path" in text
    assert "ai-team-sdd resume path" in text
    assert "ai-team-memory consolidate path" in text
    assert "ai-team-release archive path" in text
    assert "Memory Consolidation" in text
    assert "Release Archive and Knowledge Consolidation" in text


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
    assert "work_slug" in data["inputs"]
    assert "handoff_requirement_url" in data["inputs"]
    assert "published_requirement_url" in data["inputs"]
    assert "resume_from" in data["inputs"]
    assert "bug_slug" not in data["inputs"]
    assert "bug" not in data["inputs"]["work_type"]["enum"]
    assert "new-project" in data["inputs"]["work_type"]["enum"]
    step_ids = _collect_step_ids(steps)
    assert "route" not in step_ids
    assert "review-context" in step_ids
    assert "context-open" in step_ids
    assert "codegraph" in step_ids
    assert "specify" in step_ids
    assert "review-spec" in step_ids
    assert "plan-cycle" in step_ids
    assert "plan" in step_ids
    assert "plan-check" in step_ids
    assert "checklist" not in step_ids
    assert "review-plan" in step_ids
    assert "task-cycle" in step_ids
    assert "tasks" in step_ids
    assert "analyze" in step_ids
    assert "task-gate" not in step_ids
    assert "review-tasks" in step_ids
    assert "implement" in step_ids
    assert "converge" in step_ids
    assert "checks" not in step_ids
    assert "evidence" not in step_ids

    plan_cycle = next(step for step in steps if step["id"] == "plan-cycle")
    assert plan_cycle["type"] == "do-while"
    assert plan_cycle["condition"] == "{{ steps.review-plan.output.choice == 'revise' }}"
    plan_cycle_ids = [s["id"] for s in plan_cycle["steps"]]
    assert plan_cycle_ids == ["plan", "plan-check", "review-plan"]
    plan_if = next(s for s in plan_cycle["steps"] if s["id"] == "plan")
    assert plan_if["type"] == "if"
    assert plan_if["condition"] == "{{ steps.review-plan.output.choice == 'revise' }}"
    plan_revise = plan_if["then"][0]
    plan_initial = plan_if["else"][0]
    assert plan_revise["id"] == "plan-revise"
    assert plan_initial["id"] == "plan-initial"
    assert "Revise plan.md only" in plan_revise["input"]["args"]
    assert "inputs.request" not in plan_revise["input"]["args"]
    assert "{{ inputs.request }}" in plan_initial["input"]["args"]

    task_cycle = next(step for step in steps if step["id"] == "task-cycle")
    assert task_cycle["type"] == "do-while"
    assert task_cycle["condition"] == "{{ steps.review-tasks.output.choice == 'revise' }}"
    task_cycle_ids = [s["id"] for s in task_cycle["steps"]]
    assert task_cycle_ids == ["tasks", "analyze", "review-tasks"]
    tasks_if = next(s for s in task_cycle["steps"] if s["id"] == "tasks")
    assert tasks_if["type"] == "if"
    tasks_revise = tasks_if["then"][0]
    tasks_initial = tasks_if["else"][0]
    assert tasks_revise["id"] == "tasks-revise"
    assert tasks_initial["id"] == "tasks-initial"
    assert "Revise tasks.md only" in tasks_revise["input"]["args"]
    assert "{{ inputs.request }}" in tasks_initial["input"]["args"]
    context_step = next(step for step in steps if step["id"] == "context-open")
    assert context_step["command"] == "speckit.ai-team.context"
    codegraph_step = next(step for step in steps if step["id"] == "codegraph")
    assert codegraph_step["command"] == "speckit.ai-team.codegraph"
    plan_check_step = next(
        step
        for step in plan_cycle["steps"]
        if step["id"] == "plan-check"
    )
    assert plan_check_step["command"] == "speckit.ai-team.plan-check"
    analyze_step = next(
        step for step in task_cycle["steps"] if step["id"] == "analyze"
    )
    assert analyze_step["command"] == "speckit.analyze"
    converge_step = next(step for step in steps if step["id"] == "converge")
    assert converge_step["command"] == "speckit.converge"

    assert BUGFIX_WORKFLOW_PATH.exists()
    bugfix = yaml.safe_load(BUGFIX_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert bugfix["workflow"]["id"] == "ai-team-bugfix"
    assert "work_slug" in bugfix["inputs"]
    assert "bug_slug" not in bugfix["inputs"]
    assert "coding_issue_url" in bugfix["inputs"]
    bugfix_step_ids = [step["id"] for step in bugfix["steps"]]
    assert "review-context" in bugfix_step_ids
    assert "route" not in bugfix_step_ids
    assert "review-impact" in bugfix_step_ids
    assert "bug-assess" in bugfix_step_ids
    assert "review-assessment" in bugfix_step_ids
    assert "bug-fix" in bugfix_step_ids
    assert "review-fix" in bugfix_step_ids
    assert "bug-test" in bugfix_step_ids
    assert "checks" not in bugfix_step_ids
    assert "evidence" not in bugfix_step_ids


def test_ai_team_bugfix_workflow_pauses_at_context_gate(tmp_path):
    run_id = "ai-team-bugfix-bug-project-alpha-123"
    state = _run_ai_team_workflow_to_context_gate(
        tmp_path,
        {
            "request": "Fix upload timeout reported by support",
            "work_slug": "bug-project-alpha-123",
            "coding_issue_url": "https://example.com/org/project/issues/123",
        },
        run_id,
        workflow_path=BUGFIX_WORKFLOW_PATH,
    )

    context_args = state.step_results["context-open"]["input"]["args"]

    assert f"workflow_run_id={run_id}" in context_args
    assert "work_type=bug" in context_args
    assert "work_slug=bug-project-alpha-123" in context_args
    assert "bug_slug=bug-project-alpha-123" in context_args
    assert "coding_issue_url=https://example.com/org/project/issues/123" in context_args


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
                "work_slug": "003-search-export",
                "work_type": "feature",
                "resume_from": "tasks-ready",
                "handoff_requirement_url": "https://example.com/enhancements/rfcs/REQ-2026-015",
            },
            [
                "work_slug=003-search-export",
                "work_type=feature",
                "resume_from=tasks-ready",
                "handoff_requirement_url=https://example.com/enhancements/rfcs/REQ-2026-015",
            ],
        ),
    ],
)
def test_ai_team_workflow_passes_journey_inputs_to_context(
    tmp_path, case_name, inputs, expected_fragments
):
    run_id = "ai-team-" + case_name.replace(" ", "-")
    state = _run_ai_team_workflow_to_context_gate(tmp_path, inputs, run_id)

    context_args = state.step_results["context-open"]["input"]["args"]

    assert f"workflow_run_id={run_id}" in context_args
    for fragment in expected_fragments:
        assert fragment in context_args

    bootstrap_result = state.step_results["bootstrap-if-requested"]["output"][
        "condition_result"
    ]
    assert bootstrap_result is (inputs.get("bootstrap_workspace") is True)
    if inputs.get("bootstrap_workspace") is True:
        assert state.step_results["bootstrap"]["status"] == "completed"
        assert "--integration" in state.step_results["bootstrap"]["output"]["argv"]
