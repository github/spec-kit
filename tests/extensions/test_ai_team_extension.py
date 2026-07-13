import json
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "extensions" / "ai-team"
WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-sdd" / "workflow.yml"
INTAKE_WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-intake" / "workflow.yml"
BUGFIX_WORKFLOW_PATH = REPO_ROOT / "workflows" / "ai-team-bugfix" / "workflow.yml"
MEMORY_ADAPTER_PATH = EXTENSION_ROOT / "scripts" / "memory_adapter.py"
WORK_ITEM_GATE = EXTENSION_ROOT / "scripts" / "check-work-item.py"
INTAKE_ROUTER = EXTENSION_ROOT / "scripts" / "intake_router.py"


def _load_intake_router():
    spec = importlib.util.spec_from_file_location("ai_team_intake_router", INTAKE_ROUTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        for nested in step.get("cases", {}).values():
            ids.extend(_collect_step_ids(nested))
    return ids


def _find_step(steps: list, step_id: str) -> dict:
    for step in steps:
        if step.get("id") == step_id:
            return step
        for key in ("then", "else", "steps"):
            nested = step.get(key)
            if isinstance(nested, list):
                try:
                    return _find_step(nested, step_id)
                except LookupError:
                    pass
        for nested in step.get("cases", {}).values():
            try:
                return _find_step(nested, step_id)
            except LookupError:
                pass
    raise LookupError(step_id)


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
    assert state.step_results["permission-analysis"]["status"] == "completed"
    assert state.step_results["review-context"]["status"] == "paused"
    assert "route" not in state.step_results
    return state


def _run_work_item_gate(tmp_path: Path, inputs: dict, run_id: str = "test-run"):
    run_dir = tmp_path / ".specify" / "workflows" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "inputs.json").write_text(
        json.dumps({"inputs": inputs}), encoding="utf-8"
    )
    return subprocess.run(
        [
            sys.executable,
            str(WORK_ITEM_GATE),
            "--run-id",
            run_id,
            "--project-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


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
        "speckit.ai-team.intake",
        "speckit.ai-team.context",
        "speckit.ai-team.permissions",
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


def test_ai_team_start_is_a_thin_plain_language_router():
    text = (
        EXTENSION_ROOT / "commands" / "speckit.ai-team.start.md"
    ).read_text(encoding="utf-8")

    assert "thin router" in text
    assert "does not" in text
    assert "No work item -> `ai-team-intake`" in text
    assert "ai-team-intake" in text
    assert "do not decide whether this is a bug or feature here" in text
    assert "Work Context Package:" not in text
    assert "likely modules:" not in text


def test_ai_team_intake_command_keeps_pre_work_item_analysis_read_only():
    text = (
        EXTENSION_ROOT / "commands" / "speckit.ai-team.intake.md"
    ).read_text(encoding="utf-8")

    assert ".specify/ai-team/intake/<intake_slug>/" in text
    assert "does not approve features" in text
    assert "issue-draft.md" in text
    assert "AI recommends" in text
    assert "Technical Committee" in text
    assert "It does not approve features" in text
    assert "AI Team Intake Result:" in text
    assert "intake_router.py" not in text


def test_ai_team_command_responsibilities_are_non_overlapping():
    readme = (EXTENSION_ROOT / "README.md").read_text(encoding="utf-8")
    requirement = (
        EXTENSION_ROOT / "commands" / "speckit.ai-team.requirement.md"
    ).read_text(encoding="utf-8")
    feature_review = (
        EXTENSION_ROOT / "commands" / "speckit.ai-team.feature-review.md"
    ).read_text(encoding="utf-8")
    codegraph = (
        EXTENSION_ROOT / "commands" / "speckit.ai-team.codegraph.md"
    ).read_text(encoding="utf-8")
    impact = (
        EXTENSION_ROOT / "commands" / "speckit.ai-team.impact.md"
    ).read_text(encoding="utf-8")

    assert "Each command owns one phase" in readme
    assert "classification without a work item" in readme
    assert "Feature acceptance" in readme
    assert "it does not\naccept the Feature" in requirement
    assert "does not author the\nrequirement" in feature_review
    assert ".specify/ai-team/intake/<intake_slug>/codegraph/" in codegraph
    assert "does not generate the\nnormalized graph" in impact


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
    assert "change_package_file" not in config["work_context"]
    assert (
        config["work_context"]["permission_envelope_file"]
        == "permission-envelope.yml"
    )
    assert config["permissions"]["default_enforcement_mode"] == "policy-only"
    assert set(config["permissions"]["supported_enforcement_modes"]) == {
        "policy-only",
        "agent-native",
        "wrapper-enforced",
    }
    assert config["permissions"]["require_envelope"] is True
    assert config["permissions"]["require_analysis_review"] is True
    assert config["permissions"]["require_implementation_review"] is True
    assert config["gates"]["require_work_item_anchor"] is True
    assert config["gates"]["allow_same_root_cause_issue_grouping"] is True
    assert config["planning"]["default_mode"] == "standard"
    assert config["planning"]["supported_modes"] == ["standard", "compact"]
    assert config["planning"]["compact_requires_explicit_user_selection"] is True
    assert config["planning"]["compact_requires_post_impact_human_gate"] is True
    assert config["planning"]["compact_for_new_project"] is False
    assert config["issue_publishing"]["default_adapter"] == "github-cli"
    assert config["issue_publishing"]["require_verified_issue_url"] is True
    assert config["issue_publishing"]["require_approved_intake_gates"] is True
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


def test_work_item_gate_accepts_same_repository_issue_group(tmp_path):
    result = _run_work_item_gate(
        tmp_path,
        {
            "work_type": "bug",
            "coding_issue_url": "https://example.com/org/project/issues/123",
            "also_resolves_issue_urls": (
                "https://example.com/org/project/issues/456,"
                "https://example.com/org/project/issues/789"
            ),
        },
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["also_resolves_count"] == 2


@pytest.mark.parametrize(
    ("inputs", "error"),
    [
        ({"work_type": "auto"}, "must be resolved after intake classification"),
        ({"work_type": "bug"}, "primary coding_issue_url"),
        (
            {
                "work_type": "feature",
                "coding_issue_url": "https://example.com/org/project/issues/1",
                "handoff_requirement_url": "https://internal.example.com/req/1",
            },
            "exactly one primary anchor",
        ),
        (
            {
                "work_type": "bug",
                "coding_issue_url": "https://example.com/org/project/issues/1",
                "also_resolves_issue_urls": "https://example.com/org/other/issues/2",
            },
            "primary coding repository",
        ),
        (
            {
                "work_type": "new-project",
                "planning_mode": "compact",
                "handoff_requirement_url": "https://internal.example.com/req/2",
            },
            "requires standard planning mode",
        ),
        ({"work_type": "new-project"}, "requires a coding issue/project charter"),
    ],
)
def test_work_item_gate_rejects_inconsistent_anchors(tmp_path, inputs, error):
    result = _run_work_item_gate(tmp_path, inputs)

    assert result.returncode == 2
    assert error in result.stderr


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
    assert "change-package.yml" not in text
    assert "permission-envelope.yml" in text
    assert ".specify/workflows/runs/<run-id>/state.json" in text
    assert "specify workflow resume <run-id>" in text
    assert "handoff requirement URL" in text
    assert "coding issue URL" in text
    assert "`archived`" in text
    assert "speckit.ai-team.memory-consolidate" in text
    assert "speckit.ai-team.release-archive" in text
    assert "after a stable Issue, charter, or handoff exists" in text
    assert "intake-<intake_slug>" not in text


def test_ai_team_reuses_native_sdd_artifacts_without_change_manifest():
    assert not (EXTENSION_ROOT / "docs" / "change-package.md").exists()
    readme = (EXTENSION_ROOT / "README.md").read_text(encoding="utf-8")
    assert "`spec.md` owns behavior" in readme
    assert "workflow state owns gate decisions" in readme
    assert "change-package.yml" not in readme


def test_ai_team_permission_envelope_document_exists():
    permission_doc = EXTENSION_ROOT / "docs" / "permission-envelope.md"

    assert permission_doc.exists()
    text = permission_doc.read_text(encoding="utf-8")
    assert "permission-envelope.yml" in text
    assert "policy-only" in text
    assert "agent-native" in text
    assert "wrapper-enforced" in text
    assert "do not sandbox shell commands" in text


def test_ai_team_compact_planning_document_matches_bundled_runtime():
    compact_doc = EXTENSION_ROOT / "docs" / "compact-planning.md"

    assert compact_doc.exists()
    text = compact_doc.read_text(encoding="utf-8")
    assert "Status: bundled" in text
    assert "AI may recommend compact planning" in text
    assert "`planning_mode=compact`" in text
    assert "one combined Plan/Tasks review" in text
    assert "Mandatory Fallback" in text
    assert "Zero-to-one projects use the Standard path" in text


def test_ai_team_work_field_spec_document_exists():
    field_doc = EXTENSION_ROOT / "docs" / "work-field-spec.md"

    assert field_doc.exists()
    text = field_doc.read_text(encoding="utf-8")
    assert "work_slug" in text
    assert "003-user-auth" in text
    assert "bug_slug" in text
    assert "coding_issue_url" in text
    assert "also_resolves_issue_urls" in text
    assert "different symptoms of the same root cause" in text
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
    assert "ai-team-intake" in catalog["workflows"]
    assert "ai-team-bugfix" in catalog["workflows"]
    assert "workflows/ai-team-sdd" in pyproject
    assert "workflows/ai-team-intake" in pyproject
    assert "workflows/ai-team-bugfix" in pyproject
    steps = data["steps"]
    assert steps[0]["type"] == "if"
    assert steps[0]["then"][0]["type"] == "init"
    assert "work_slug" in data["inputs"]
    assert data["inputs"]["planning_mode"]["default"] == "standard"
    assert data["inputs"]["planning_mode"]["enum"] == ["standard", "compact"]
    assert "also_resolves_issue_urls" in data["inputs"]
    assert "handoff_requirement_url" in data["inputs"]
    assert "published_requirement_url" in data["inputs"]
    assert "resume_from" in data["inputs"]
    assert "bug_slug" not in data["inputs"]
    assert "bug" not in data["inputs"]["work_type"]["enum"]
    assert "new-project" in data["inputs"]["work_type"]["enum"]
    step_ids = _collect_step_ids(steps)
    assert "route" not in step_ids
    assert "review-context" in step_ids
    assert "validate-work-item" in step_ids
    assert "context-open" in step_ids
    assert "codegraph" in step_ids
    assert "permission-analysis" in step_ids
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
    assert "permission-implementation" in step_ids
    assert "review-permissions" in step_ids
    assert "implement" in step_ids
    assert "converge" in step_ids
    assert "checks" not in step_ids
    assert "evidence" not in step_ids

    planning_path = next(step for step in steps if step["id"] == "planning-path")
    assert planning_path["type"] == "switch"
    assert planning_path["expression"] == "{{ inputs.planning_mode }}"
    assert set(planning_path["cases"]) == {"standard", "compact"}

    plan_cycle = _find_step(planning_path["cases"]["standard"], "plan-cycle")
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

    task_cycle = _find_step(planning_path["cases"]["standard"], "task-cycle")
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
    compact_steps = planning_path["cases"]["compact"]
    assert [step["id"] for step in compact_steps] == [
        "review-compact-eligibility",
        "compact-cycle",
    ]
    compact_cycle = _find_step(compact_steps, "compact-cycle")
    assert [step["id"] for step in compact_cycle["steps"]] == [
        "compact-plan",
        "compact-plan-check",
        "handoff-plan-to-tasks",
        "compact-tasks",
        "compact-analyze",
        "review-compact-plan-tasks",
    ]
    assert "planning_mode=compact" in compact_cycle["steps"][0]["input"]["args"]
    assert compact_cycle["steps"][2]["command"] == "speckit.ai-team.handoff"
    assert compact_cycle["steps"][-1]["type"] == "gate"

    context_step = next(step for step in steps if step["id"] == "context-open")
    assert context_step["command"] == "speckit.ai-team.context"
    permission_analysis_step = next(
        step for step in steps if step["id"] == "permission-analysis"
    )
    assert permission_analysis_step["command"] == "speckit.ai-team.permissions"
    assert "mode=analysis" in permission_analysis_step["input"]["args"]
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
    permission_implementation_step = next(
        step for step in steps if step["id"] == "permission-implementation"
    )
    assert (
        permission_implementation_step["command"]
        == "speckit.ai-team.permissions"
    )
    assert "mode=implementation" in permission_implementation_step["input"]["args"]
    assert step_ids.index("permission-analysis") < step_ids.index("codegraph")
    assert step_ids.index("context-open") < step_ids.index("validate-work-item")
    assert step_ids.index("impact") < step_ids.index("validate-work-item")
    assert step_ids.index("validate-work-item") < step_ids.index("specify")
    assert step_ids.index("permission-implementation") < step_ids.index("implement")
    assert step_ids.index("review-permissions") < step_ids.index("implement")
    converge_step = next(step for step in steps if step["id"] == "converge")
    assert converge_step["command"] == "speckit.converge"

    assert BUGFIX_WORKFLOW_PATH.exists()
    bugfix = yaml.safe_load(BUGFIX_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert bugfix["workflow"]["id"] == "ai-team-bugfix"
    assert "work_slug" in bugfix["inputs"]
    assert "bug_slug" not in bugfix["inputs"]
    assert "coding_issue_url" in bugfix["inputs"]
    assert bugfix["inputs"]["coding_issue_url"]["required"] is True
    assert "also_resolves_issue_urls" in bugfix["inputs"]
    bugfix_step_ids = [step["id"] for step in bugfix["steps"]]
    assert "review-context" in bugfix_step_ids
    assert "validate-work-item" in bugfix_step_ids
    assert "permission-analysis" in bugfix_step_ids
    assert "route" not in bugfix_step_ids
    assert "review-impact" in bugfix_step_ids
    assert "bug-assess" in bugfix_step_ids
    assert "review-assessment" in bugfix_step_ids
    assert "permission-implementation" in bugfix_step_ids
    assert "review-permissions" in bugfix_step_ids
    assert "bug-fix" in bugfix_step_ids
    assert "review-fix" in bugfix_step_ids
    assert "bug-test" in bugfix_step_ids
    assert "checks" not in bugfix_step_ids
    assert "evidence" not in bugfix_step_ids
    assert bugfix_step_ids.index("permission-analysis") < bugfix_step_ids.index(
        "codegraph"
    )
    assert bugfix_step_ids.index("validate-work-item") < bugfix_step_ids.index(
        "context-open"
    )
    assert bugfix_step_ids.index(
        "permission-implementation"
    ) < bugfix_step_ids.index("bug-fix")
    assert bugfix_step_ids.index("review-permissions") < bugfix_step_ids.index(
        "bug-fix"
    )


def test_ai_team_intake_workflow_is_read_only_until_issue_approval():
    from specify_cli.workflows.engine import WorkflowDefinition

    assert INTAKE_WORKFLOW_PATH.exists()
    WorkflowDefinition.from_yaml(INTAKE_WORKFLOW_PATH)
    data = yaml.safe_load(INTAKE_WORKFLOW_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(
        (REPO_ROOT / "workflows" / "catalog.json").read_text(encoding="utf-8")
    )

    assert data["workflow"]["id"] == "ai-team-intake"
    assert "ai-team-intake" in catalog["workflows"]
    assert data["inputs"]["work_type"]["enum"] == [
        "auto",
        "bug",
        "feature",
        "new-project",
    ]
    assert data["inputs"]["planning_preference"]["enum"] == [
        "auto",
        "standard",
        "compact",
    ]

    steps = data["steps"]
    step_ids = [step["id"] for step in steps]
    assert step_ids == [
        "workspace",
        "intake-boundary-cycle",
        "codegraph",
        "impact",
        "issue-draft-cycle",
        "publish-issue",
        "launch-formal-workflow",
    ]
    nested_ids = _collect_step_ids(steps)
    assert "review-intake-boundary" in nested_ids
    assert "review-issue-draft" in nested_ids
    boundary_cycle = _find_step(steps, "intake-boundary-cycle")
    draft_cycle = _find_step(steps, "issue-draft-cycle")
    assert boundary_cycle["condition"] == "{{ steps.review-intake-boundary.output.choice == 'revise' }}"
    assert draft_cycle["condition"] == "{{ steps.review-issue-draft.output.choice == 'revise' }}"
    assert _find_step(steps, "publish-issue")["type"] == "shell"
    assert _find_step(steps, "launch-formal-workflow")["type"] == "shell"
    assert "intake_router.py publish" in _find_step(steps, "publish-issue")["run"]
    assert "intake_router.py route" in _find_step(steps, "launch-formal-workflow")["run"]
    permission_step = _find_step(steps, "permission-analysis")
    assert "intake_mode=true" in permission_step["input"]["args"]
    assert "work_slug=intake-" not in permission_step["input"]["args"]


def _write_approved_intake(tmp_path: Path, *, work_type: str, accepted: bool = True):
    run_id = "intake-run"
    slug = "csv-export"
    run_dir = tmp_path / ".specify" / "workflows" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "inputs.json").write_text(
        json.dumps({"inputs": {"request": "Add CSV export"}}), encoding="utf-8"
    )
    (run_dir / "state.json").write_text(
        json.dumps(
            {
                "step_results": {
                    "review-intake-boundary": {"output": {"choice": "approve"}},
                    "review-issue-draft": {"output": {"choice": "approve"}},
                }
            }
        ),
        encoding="utf-8",
    )
    intake_dir = tmp_path / ".specify" / "ai-team" / "intake" / slug
    intake_dir.mkdir(parents=True)
    intake = {
        "work_type": work_type,
        "privacy_class": "public-safe",
        "planning_mode": "compact" if work_type == "feature" else "standard",
        "feature_decision_evidence": "accepted" if accepted else "unreviewed",
        "feature_approver": "tc-member" if accepted and work_type != "bug" else None,
        "feature_approver_role": "technical-committee" if accepted and work_type != "bug" else None,
    }
    (intake_dir / "intake.yml").write_text(
        yaml.safe_dump(intake, sort_keys=False), encoding="utf-8"
    )
    (intake_dir / "issue-draft.md").write_text(
        f"""---
title: Add CSV export
type_label: {"type/bug" if work_type == "bug" else "type/feature"}
target_repository: example/project
---

## Requested behavior

Add CSV export with the visible columns.
""",
        encoding="utf-8",
    )
    return run_id, slug


def test_intake_router_publishes_and_launches_accepted_feature(tmp_path):
    router = _load_intake_router()
    run_id, slug = _write_approved_intake(tmp_path, work_type="feature")
    publish_runner = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="https://github.com/example/project/issues/42\n", stderr=""
        )
    )

    published = router.publish_issue(
        project_root=tmp_path,
        run_id=run_id,
        intake_slug=slug,
        runner=publish_runner,
    )
    route_runner = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Workflow paused at review-context", stderr=""
        )
    )
    routed = router.route_formal_workflow(
        project_root=tmp_path,
        run_id=run_id,
        intake_slug=slug,
        runner=route_runner,
    )

    assert published["route_status"] == "ready"
    assert routed["route_status"] == "launched"
    command = route_runner.call_args.args[0]
    assert command[:4] == ["specify", "workflow", "run", "ai-team-sdd"]
    assert "work_type=feature" in command
    assert "planning_mode=compact" in command
    assert "coding_issue_url=https://github.com/example/project/issues/42" in command


def test_intake_router_draft_feature_stops_after_issue_creation(tmp_path):
    router = _load_intake_router()
    run_id, slug = _write_approved_intake(
        tmp_path, work_type="feature", accepted=False
    )
    runner = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="https://github.com/example/project/issues/43\n", stderr=""
        )
    )

    router.publish_issue(
        project_root=tmp_path,
        run_id=run_id,
        intake_slug=slug,
        runner=runner,
    )
    route_runner = MagicMock()
    result = router.route_formal_workflow(
        project_root=tmp_path,
        run_id=run_id,
        intake_slug=slug,
        runner=route_runner,
    )

    assert result["route_status"] == "awaiting-feature-acceptance"
    route_runner.assert_not_called()


def test_intake_router_launches_new_project_in_standard_mode(tmp_path):
    router = _load_intake_router()
    run_id, slug = _write_approved_intake(tmp_path, work_type="new-project")
    publish_runner = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="https://github.com/example/project/issues/44\n",
            stderr="",
        )
    )
    router.publish_issue(
        project_root=tmp_path,
        run_id=run_id,
        intake_slug=slug,
        runner=publish_runner,
    )
    route_runner = MagicMock(
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Workflow paused", stderr=""
        )
    )

    router.route_formal_workflow(
        project_root=tmp_path,
        run_id=run_id,
        intake_slug=slug,
        runner=route_runner,
    )

    command = route_runner.call_args.args[0]
    assert "work_type=new-project" in command
    assert "planning_mode=standard" in command


def test_intake_router_refuses_unapproved_draft(tmp_path):
    router = _load_intake_router()
    run_id, slug = _write_approved_intake(tmp_path, work_type="bug")
    state_path = tmp_path / ".specify" / "workflows" / "runs" / run_id / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["step_results"]["review-issue-draft"]["output"]["choice"] = "revise"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(router.IntakeRouteError, match="not approved"):
        router.publish_issue(
            project_root=tmp_path,
            run_id=run_id,
            intake_slug=slug,
            runner=MagicMock(),
        )


def test_ai_team_bugfix_workflow_pauses_at_context_gate(tmp_path):
    run_id = "ai-team-bugfix-bug-project-alpha-123"
    state = _run_ai_team_workflow_to_context_gate(
        tmp_path,
        {
            "request": "Fix upload timeout reported by support",
            "work_slug": "bug-project-alpha-123",
            "coding_issue_url": "https://example.com/org/project/issues/123",
            "also_resolves_issue_urls": "https://example.com/org/project/issues/456",
        },
        run_id,
        workflow_path=BUGFIX_WORKFLOW_PATH,
    )

    context_args = state.step_results["context-open"]["input"]["args"]
    permission_args = state.step_results["permission-analysis"]["input"]["args"]

    assert f"workflow_run_id={run_id}" in context_args
    assert "work_type=bug" in context_args
    assert "work_slug=bug-project-alpha-123" in context_args
    assert "bug_slug=bug-project-alpha-123" in context_args
    assert "coding_issue_url=https://example.com/org/project/issues/123" in context_args
    assert "also_resolves_issue_urls=https://example.com/org/project/issues/456" in context_args
    assert "mode=analysis" in permission_args
    assert "work_slug=bug-project-alpha-123" in permission_args


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
                "planning_mode=standard",
                "coding_issue_url=https://example.com/org/project/issues/456",
                "handoff_requirement_url=",
            ],
        ),
        (
            "existing project compact feature from chat routing",
            {
                "request": "Use AI Team Compact mode for search export",
                "work_type": "feature",
                "planning_mode": "compact",
                "coding_issue_url": "https://example.com/org/project/issues/457",
            },
            [
                "work_type=feature",
                "planning_mode=compact",
                "coding_issue_url=https://example.com/org/project/issues/457",
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
    permission_args = state.step_results["permission-analysis"]["input"]["args"]

    assert f"workflow_run_id={run_id}" in context_args
    for fragment in expected_fragments:
        assert fragment in context_args
    assert "mode=analysis" in permission_args

    bootstrap_result = state.step_results["bootstrap-if-requested"]["output"][
        "condition_result"
    ]
    assert bootstrap_result is (inputs.get("bootstrap_workspace") is True)
    if inputs.get("bootstrap_workspace") is True:
        assert state.step_results["bootstrap"]["status"] == "completed"
        assert "--integration" in state.step_results["bootstrap"]["output"]["argv"]
