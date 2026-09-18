"""Static checks for repository GitHub Actions workflows."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.conftest import requires_bash

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
# Match both the dedicated-step form (`        uses: x@sha`) and the
# inline shorthand (`      - uses: x@sha`) used in catalog-assign.yml.
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<ref>\S+)", re.MULTILINE)
PINNED_SHA_RE = re.compile(r"@[0-9a-f]{40}$", re.IGNORECASE)
PUBLISH_WORKFLOW = WORKFLOWS_DIR / "publish-pypi.yml"
PUBLISH_VALIDATION_STEPS = (
    "Verify tag format",
    "Verify tag matches package version",
)
FEATURE_ASSESS_WORKFLOW = WORKFLOWS_DIR / "feature-assess.md"
FEATURE_ASSESS_COMPILED_WORKFLOW = WORKFLOWS_DIR / "feature-assess.lock.yml"
FEATURE_ASSESS_LABELS = {
    "feature-go",
    "feature-needs-clarification",
    "feature-kill",
    "feature-invalid",
}
COMMUNITY_SUBMISSION_WORKFLOWS = (
    (
        "bundle",
        "bundle-submission",
        "bundles/catalog.community.json",
        "docs/community/bundles.md",
        "Modify only `bundles/catalog.community.json`",
    ),
    (
        "extension",
        "extension-submission",
        "extensions/catalog.community.json",
        "docs/community/extensions.md",
        "Do not modify any other files",
    ),
    (
        "preset",
        "preset-submission",
        "presets/catalog.community.json",
        "docs/community/presets.md",
        "Do not modify any other files",
    ),
)


def _publish_workflow_steps() -> dict[str, dict[str, object]]:
    workflow = yaml.safe_load(PUBLISH_WORKFLOW.read_text(encoding="utf-8"))
    return {step["name"]: step for step in workflow["jobs"]["build"]["steps"]}


def _run_publish_validation_step(
    step_name: str, tag: str, working_directory: Path
) -> subprocess.CompletedProcess[str]:
    step = _publish_workflow_steps()[step_name]
    env = os.environ.copy()
    env["TAG"] = tag
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        ["bash", "-euo", "pipefail", "-c", step["run"]],
        cwd=working_directory,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_project_version(working_directory: Path, version: str) -> None:
    (working_directory / "pyproject.toml").write_text(
        f'[project]\nversion = "{version}"\n', encoding="utf-8"
    )


def _create_pull_request_allowed_files(source_text: str) -> list[str]:
    create_pr_match = re.search(
        r"(?m)^  create-pull-request:\n(?P<body>(?:^    [^\n]*\n?)+)",
        source_text,
    )
    assert create_pr_match is not None

    allowed_files_match = re.search(
        r"(?m)^    allowed-files:\n(?P<files>(?:^      - [^\n]+\n?)+)",
        create_pr_match.group("body"),
    )
    assert allowed_files_match is not None

    return [
        line.strip().removeprefix("- ")
        for line in allowed_files_match.group("files").splitlines()
        if line.strip()
    ]


def _workflow_frontmatter(source_text: str) -> dict[str, object]:
    _, frontmatter, _ = source_text.split("---", maxsplit=2)
    return yaml.safe_load(frontmatter)


def _gh_aw_metadata(compiled_text: str) -> dict[str, object]:
    metadata_prefix = "# gh-aw-metadata: "
    first_line = compiled_text.splitlines()[0]
    assert first_line.startswith(metadata_prefix)
    return json.loads(first_line.removeprefix(metadata_prefix))


def _workflow_step(steps: list[dict[str, object]], name: str) -> dict[str, object]:
    return next(step for step in steps if step.get("name") == name)


def _agentic_workflow(name: str) -> tuple[str, str, dict, dict]:
    source_text = (WORKFLOWS_DIR / f"{name}.md").read_text(encoding="utf-8")
    compiled_text = (WORKFLOWS_DIR / f"{name}.lock.yml").read_text(encoding="utf-8")
    return (
        source_text,
        compiled_text,
        _workflow_frontmatter(source_text),
        yaml.safe_load(compiled_text),
    )


def _safe_output_config(compiled: dict) -> dict:
    step = _workflow_step(
        compiled["jobs"]["safe_outputs"]["steps"], "Process Safe Outputs"
    )
    return json.loads(step["env"]["GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG"])


def test_github_actions_are_pinned_to_full_commit_shas():
    unpinned_refs = []

    workflows = sorted(
        list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml"))
    )
    assert workflows

    for workflow in workflows:
        workflow_text = workflow.read_text(encoding="utf-8")
        for match in USES_RE.finditer(workflow_text):
            uses_ref = match.group("ref")
            if uses_ref.startswith(("./", "../")):
                continue
            if PINNED_SHA_RE.search(uses_ref):
                continue
            unpinned_refs.append(f"{workflow.relative_to(REPO_ROOT)}: {uses_ref}")

    assert unpinned_refs == []


def test_publish_tag_validation_uses_environment_variable():
    steps = _publish_workflow_steps()

    for step_name in PUBLISH_VALIDATION_STEPS:
        step = steps[step_name]
        assert step["env"]["TAG"] == "${{ inputs.tag }}"
        assert "${{ inputs.tag }}" not in step["run"]


@requires_bash
def test_publish_tag_validation_accepts_valid_tag(tmp_path):
    _write_project_version(tmp_path, "1.2.3")

    for step_name in PUBLISH_VALIDATION_STEPS:
        result = _run_publish_validation_step(step_name, "v1.2.3", tmp_path)
        assert result.returncode == 0, result.stderr


@requires_bash
def test_publish_tag_validation_rejects_invalid_tag(tmp_path):
    for invalid_tag in ("1.2.3", "v1.2", "v1.2.3-rc1"):
        result = _run_publish_validation_step(
            "Verify tag format", invalid_tag, tmp_path
        )
        assert result.returncode != 0
        assert "is not a valid release tag" in result.stdout

    injected_file = tmp_path / "interpolated"
    injected_tag = f'v1.2.3"; touch "{injected_file}"; #'
    result = _run_publish_validation_step("Verify tag format", injected_tag, tmp_path)
    assert result.returncode != 0
    assert not injected_file.exists()


@requires_bash
def test_publish_tag_validation_rejects_version_mismatch(tmp_path):
    _write_project_version(tmp_path, "1.2.3")

    result = _run_publish_validation_step(
        "Verify tag matches package version", "v1.2.4", tmp_path
    )

    assert result.returncode != 0
    assert "does not match pyproject.toml version" in result.stdout


def test_pinned_action_ref_accepts_uppercase_hex_sha():
    assert PINNED_SHA_RE.search(
        "actions/example@0123456789ABCDEF0123456789ABCDEF01234567"
    )


def test_feature_assess_upgrade_preserves_positive_execution_path():
    source_text = FEATURE_ASSESS_WORKFLOW.read_text(encoding="utf-8")
    compiled_text = FEATURE_ASSESS_COMPILED_WORKFLOW.read_text(encoding="utf-8")
    source = _workflow_frontmatter(source_text)
    compiled = yaml.safe_load(compiled_text)

    metadata = _gh_aw_metadata(compiled_text)
    assert metadata["compiler_version"] == "v0.88.7"
    assert metadata["engine_versions"] == {"copilot": "1.0.80"}

    source_steps = source["steps"]
    compiled_steps = compiled["jobs"]["agent"]["steps"]
    expected_step_names = [
        "Setup uv",
        "Set up Python",
        "Install Spec Kit CLI",
        "Initialize Spec Kit and install the assess extension",
    ]
    compiled_step_names = [step.get("name") for step in compiled_steps]
    assert [
        compiled_step_names.index(step_name) for step_name in expected_step_names
    ] == sorted(compiled_step_names.index(step_name) for step_name in expected_step_names)

    for source_step in source_steps:
        compiled_step = _workflow_step(compiled_steps, source_step["name"])
        for field in ("continue-on-error", "uses", "with", "working-directory", "run"):
            if field in source_step:
                assert compiled_step[field] == source_step[field]

    install_step = _workflow_step(compiled_steps, "Install Spec Kit CLI")
    assert 'PIP_SUBCOMMAND=pip' in install_step["run"]
    assert '"$UV_BIN" "$PIP_SUBCOMMAND" install --system .' in install_step["run"]


def test_feature_assess_upgrade_preserves_negative_guards():
    source_text = FEATURE_ASSESS_WORKFLOW.read_text(encoding="utf-8")
    compiled_text = FEATURE_ASSESS_COMPILED_WORKFLOW.read_text(encoding="utf-8")
    source = _workflow_frontmatter(source_text)
    compiled = yaml.safe_load(compiled_text)

    assert (source.get("on") or source[True]) == {
        "issues": {"types": ["labeled"], "names": ["feature-assess"]},
        "skip-bots": ["github-actions", "copilot", "dependabot"],
    }
    assert (compiled.get("on") or compiled[True]) == {
        "issues": {"types": ["labeled"]},
    }

    activation_condition = compiled["jobs"]["activation"]["if"]
    pre_activation = compiled["jobs"]["pre_activation"]
    expected_guard = (
        "github.event_name != 'issues' || github.event.action != 'labeled' || "
        "github.event.label.name == 'feature-assess'"
    )
    assert " ".join(pre_activation["if"].split()) == expected_guard
    assert " ".join(activation_condition.split()) == (
        f"needs.pre_activation.outputs.activated == 'true' && ({expected_guard})"
    )
    assert pre_activation["steps"][-1]["env"]["GH_AW_SKIP_BOTS"] == (
        "github-actions,copilot-swe-agent,Copilot,copilot,"
        "@app/copilot-swe-agent,dependabot"
    )

    agent = compiled["jobs"]["agent"]
    assert agent["permissions"] == {"contents": "read", "issues": "read"}
    assert compiled["jobs"]["safe_outputs"]["permissions"] == {
        "issues": "write",
        "pull-requests": "write",
    }

    safe_outputs_step = _workflow_step(
        compiled["jobs"]["safe_outputs"]["steps"], "Process Safe Outputs"
    )
    safe_outputs = json.loads(
        safe_outputs_step["env"]["GH_AW_SAFE_OUTPUTS_HANDLER_CONFIG"]
    )
    assert safe_outputs["add_comment"] == {"max": 5}
    assert safe_outputs["add_labels"]["max"] == 1
    assert set(safe_outputs["add_labels"]["allowed"]) == FEATURE_ASSESS_LABELS
    assert set(safe_outputs["remove_labels"]["allowed"]) == FEATURE_ASSESS_LABELS
    assert not {
        "create_issue",
        "create_pull_request",
        "push_to_pull_request",
    } & safe_outputs.keys()

    assert re.search(r"without applying any verdict\s+label", source_text)
    assert "never stage,\n  commit, or push" in source_text

    unpinned_refs = [
        match.group("ref")
        for match in USES_RE.finditer(compiled_text)
        if not match.group("ref").startswith(("./", "../"))
        and not PINNED_SHA_RE.search(match.group("ref"))
    ]
    assert unpinned_refs == []


def test_community_submission_automation_is_wired_to_allowed_files():
    assignment = WORKFLOWS_DIR / "catalog-assign.yml"
    assignment_text = assignment.read_text(encoding="utf-8")

    for workflow, label, catalog_file, docs_file, instruction in (
        COMMUNITY_SUBMISSION_WORKFLOWS
    ):
        source = WORKFLOWS_DIR / f"add-community-{workflow}.md"
        compiled = WORKFLOWS_DIR / f"add-community-{workflow}.lock.yml"

        assert source.is_file()
        assert compiled.is_file()
        source_text = source.read_text(encoding="utf-8")
        compiled_text = compiled.read_text(encoding="utf-8")

        assert f"names: [{label}]" in source_text
        assert catalog_file in source_text
        assert docs_file in source_text
        assert instruction in source_text
        assert _create_pull_request_allowed_files(source_text) == [
            catalog_file,
            docs_file,
        ]
        assert _safe_output_config(yaml.safe_load(compiled_text))[
            "create_pull_request"
        ]["allowed_files"] == [catalog_file, docs_file]
        assert label in assignment_text


@pytest.mark.parametrize("kind", [item[0] for item in COMMUNITY_SUBMISSION_WORKFLOWS])
def test_community_upgrade_uses_established_runtime_defaults(kind):
    _, compiled_text, source, compiled = _agentic_workflow(f"add-community-{kind}")
    metadata = _gh_aw_metadata(compiled_text)
    assert metadata["compiler_version"] == "v0.88.7"
    assert metadata["engine_versions"] == {"copilot": "1.0.80"}
    assert metadata["strict"] is True
    assert "engine" not in source

    info = _workflow_step(
        compiled["jobs"]["activation"]["steps"], "Generate agentic run info"
    )["env"]
    assert info["GH_AW_INFO_MODEL"] == (
        "${{ vars.GH_AW_MODEL_AGENT_COPILOT || "
        "vars.GH_AW_DEFAULT_MODEL_COPILOT || 'auto' }}"
    )
    assert info["GH_AW_INFO_AWF_VERSION"] == "v0.28.14"
    manifest_prefix = "# gh-aw-manifest: "
    manifest = json.loads(compiled_text.splitlines()[1].removeprefix(manifest_prefix))
    assert {container["image"] for container in manifest["containers"]} == {
        "ghcr.io/github/gh-aw-firewall/agent:0.28.14",
        "ghcr.io/github/gh-aw-firewall/api-proxy:0.28.14",
        "ghcr.io/github/gh-aw-firewall/squid:0.28.14",
        "ghcr.io/github/gh-aw-mcpg:v0.4.18",
        "ghcr.io/github/gh-aw-node",
        "ghcr.io/github/github-mcp-server:v1.11.0",
    }
    for container in manifest["containers"]:
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", container["digest"])
        assert container["pinned_image"] == (
            f"{container['image']}@{container['digest']}"
        )
    refs = {match.group("ref") for match in USES_RE.finditer(compiled_text)}
    assert refs
    assert all(PINNED_SHA_RE.search(ref) for ref in refs)
    assert {ref for ref in refs if ref.startswith("github/gh-aw-actions/")} == {
        "github/gh-aw-actions/setup@5e508589e03a7757a7e05b26e834292f5445bfb6"
    }


@pytest.mark.parametrize("kind", [item[0] for item in COMMUNITY_SUBMISSION_WORKFLOWS])
def test_community_upgrade_preserves_activation_and_permission_guards(kind):
    _, _, source, compiled = _agentic_workflow(f"add-community-{kind}")
    label = f"{kind}-submission"
    assert (source.get("on") or source[True]) == {
        "issues": {"types": ["labeled"], "names": [label]},
        "skip-bots": ["github-actions", "copilot", "dependabot"],
    }
    assert (compiled.get("on") or compiled[True]) == {
        "issues": {"types": ["labeled"]}
    }
    guard = (
        "github.event_name != 'issues' || github.event.action != 'labeled' || "
        f"github.event.label.name == '{label}'"
    )
    pre_activation = compiled["jobs"]["pre_activation"]
    assert " ".join(pre_activation["if"].split()) == guard
    assert " ".join(compiled["jobs"]["activation"]["if"].split()) == (
        f"needs.pre_activation.outputs.activated == 'true' && ({guard})"
    )
    assert pre_activation["outputs"]["activated"] == (
        "${{ steps.check_membership.outputs.is_team_member == 'true' && "
        "steps.check_skip_bots.outputs.skip_bots_ok == 'true' }}"
    )
    assert _workflow_step(
        pre_activation["steps"], "Check team membership for workflow"
    )["env"]["GH_AW_REQUIRED_ROLES"] == "admin,maintainer,write"
    assert _workflow_step(pre_activation["steps"], "Check skip-bots")["env"][
        "GH_AW_SKIP_BOTS"
    ] == "github-actions,copilot-swe-agent,Copilot,copilot,@app/copilot-swe-agent,dependabot"

    agent = compiled["jobs"]["agent"]
    assert agent["needs"] == "activation"
    assert agent["if"] == "needs.activation.outputs.daily_ai_credits_exceeded != 'true'"
    assert compiled["permissions"] == {}
    assert source["permissions"] == agent["permissions"] == {
        "contents": "read", "issues": "read"
    }
    assert source["tools"]["github"] == {
        "toolsets": ["issues", "repos"], "min-integrity": "none"
    }
    assert source["checkout"] == {"fetch-depth": 0}
    assert _workflow_step(agent["steps"], "Checkout repository")["with"] == {
        "persist-credentials": False, "fetch-depth": 0
    }
    output_permissions = {
        "contents": "write", "issues": "write", "pull-requests": "write"
    }
    assert compiled["jobs"]["safe_outputs"]["permissions"] == output_permissions
    assert compiled["jobs"]["conclusion"]["permissions"] == {
        **output_permissions, "actions": "read"
    }


@pytest.mark.parametrize(
    "kind,label,catalog_file,docs_file,instruction", COMMUNITY_SUBMISSION_WORKFLOWS
)
def test_community_upgrade_preserves_scoped_draft_pr_contract(
    kind, label, catalog_file, docs_file, instruction
):
    source_text, _, source, compiled = _agentic_workflow(f"add-community-{kind}")
    assert instruction in source_text
    outputs = _safe_output_config(compiled)
    expected_outputs = {
        "add_comment", "add_labels", "create_pull_request", "noop",
        "create_report_incomplete_issue", "missing_data", "missing_tool",
        "report_incomplete",
    }
    expected_source_outputs = {
        "add-comment", "add-labels", "create-pull-request", "noop", "threat-detection"
    }
    if kind == "bundle":
        expected_outputs.add("remove_labels")
        expected_source_outputs.add("remove-labels")
        assert outputs["remove_labels"]["allowed"] == source["safe-outputs"][
            "remove-labels"
        ]["allowed"] == ["validation-passed", "validation-failed", "needs-info"]
    assert set(outputs) == expected_outputs
    assert set(source["safe-outputs"]) == expected_source_outputs
    assert outputs["add_comment"] == source["safe-outputs"]["add-comment"] == {"max": 2}
    assert outputs["add_labels"] == source["safe-outputs"]["add-labels"] == {
        "allowed": [label, "validation-passed", "validation-failed", "needs-info"],
        "max": 3,
    }
    assert source["safe-outputs"]["noop"] == {"report-as-issue": False}
    assert outputs["noop"] == {"max": 1, "report-as-issue": "false"}
    assert source["safe-outputs"]["create-pull-request"] == {
        "title-prefix": f"[{kind}] ",
        "labels": [label, "automated"],
        "draft": True,
        "max": 1,
        "allowed-files": [catalog_file, docs_file],
        "protected-files": {
            "policy": "blocked", "exclude": ["README.md", "CHANGELOG.md"]
        },
    }
    create_pr = outputs["create_pull_request"]
    assert create_pr["allowed_files"] == [catalog_file, docs_file]
    assert create_pr["draft"] is True
    assert create_pr["title_prefix"] == f"[{kind}] "
    assert create_pr["labels"] == [label, "automated"]
    assert create_pr["max"] == 1
    assert create_pr["max_patch_files"] == 100
    assert create_pr["max_patch_size"] == 4096
    assert create_pr["protected_files_policy"] == "blocked"
    assert create_pr["protect_top_level_dot_folders"] is True
    assert not create_pr.get("protected_dot_folder_excludes")
    assert "AGENTS.md" in create_pr["protected_files"]
    assert not {"README.md", "CHANGELOG.md", "CLAUDE.md", "GEMINI.md"} & set(
        create_pr["protected_files"]
    )


# Full clauses from the catalog download-URL checks (issue #4185). Assert the
# complete sentences so independent keywords cannot drift apart.
_CATALOG_DOWNLOAD_URL_CLAUSES = (
    (
        "The download URL MUST belong to the submitted repository\n"
        "  (`https://github.com/<owner>/<repo>/...` with the same `<owner>/<repo>` as\n"
        "  the Repository URL). Reject URLs for any other GitHub repository."
    ),
    (
        "If the download URL path contains `releases/latest/`, reject with an\n"
        "  explanation — this URL is floating and not acceptable. Mark this pinning\n"
        "  check failed and skip the HTTP request for this URL, then continue the\n"
        "  remaining validations."
    ),
    (
        "The `<tag>` segment in the URL MUST correspond to the submitted version.\n"
        "  Accept `vX.Y.Z`, `X.Y.Z`, and scoped tags whose version suffix matches\n"
        "  (for example `aide-v1.0.0` for version `1.0.0`). Reject a tag whose\n"
        "  embedded semver does not equal the submitted version."
    ),
    (
        "Only after all pinning checks pass, fetch the download URL and perform the\n"
        "  remaining artifact checks:\n"
        "  - Verify the URL returns HTTP 200.\n"
        "  - If `sha256` is included, verify it matches the downloaded archive. Requiring\n"
        "    `sha256` on every catalog entry is follow-up work and MUST NOT fail this\n"
        "    check when the field is absent."
    ),
)


def test_community_submission_workflows_require_tag_pinned_download_urls():
    """Catalog agents must reject floating releases/latest URLs (issue #4185)."""
    for workflow, *_ in COMMUNITY_SUBMISSION_WORKFLOWS:
        source_text = (WORKFLOWS_DIR / f"add-community-{workflow}.md").read_text(
            encoding="utf-8"
        )

        assert "should follow the pattern" not in source_text.lower()
        for clause in _CATALOG_DOWNLOAD_URL_CLAUSES:
            assert clause in source_text, f"missing clause in {workflow}: {clause!r}"

        if workflow == "bundle":
            assert (
                "`https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>.zip`."
                in source_text
            )
            assert "archive/refs/tags/" not in source_text
        else:
            assert (
                "`https://github.com/<owner>/<repo>/archive/refs/tags/<tag>.zip`"
                in source_text
            )
            assert (
                "`https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>.zip`"
                in source_text
            )


def test_community_submission_allowed_files_do_not_include_other_catalogs_or_docs():
    allowed_by_workflow = {
        workflow: set(
            _create_pull_request_allowed_files(
                (WORKFLOWS_DIR / f"add-community-{workflow}.md").read_text(
                    encoding="utf-8"
                )
            )
        )
        for workflow, *_ in COMMUNITY_SUBMISSION_WORKFLOWS
    }

    workflow_allowed_files = list(allowed_by_workflow.items())

    for index, (workflow, allowed_files) in enumerate(workflow_allowed_files):
        for other_workflow, other_allowed_files in workflow_allowed_files[index + 1 :]:
            overlapping_files = allowed_files & other_allowed_files
            assert overlapping_files == set(), (
                f"{workflow} and {other_workflow} share allowed files: "
                f"{sorted(overlapping_files)}"
            )


def _frontmatter(source_text: str) -> dict:
    if not source_text.startswith("---"):
        raise AssertionError("workflow source is missing YAML frontmatter")
    _, frontmatter, _ = source_text.split("---", 2)
    return yaml.safe_load(frontmatter)


def test_community_submission_threat_detection_is_fail_closed():
    for workflow, *_ in COMMUNITY_SUBMISSION_WORKFLOWS:
        source = WORKFLOWS_DIR / f"add-community-{workflow}.md"
        compiled = WORKFLOWS_DIR / f"add-community-{workflow}.lock.yml"

        assert source.is_file()
        assert compiled.is_file()

        safe_outputs = _frontmatter(source.read_text(encoding="utf-8")).get(
            "safe-outputs", {}
        )
        threat_detection = safe_outputs.get("threat-detection")
        assert threat_detection is not None, (
            f"add-community-{workflow}.md must configure "
            "safe-outputs.threat-detection"
        )
        assert threat_detection.get("continue-on-error") is False, (
            f"add-community-{workflow}.md must set threat-detection "
            "continue-on-error: false so detections block safe outputs"
        )

        compiled_text = compiled.read_text(encoding="utf-8")
        assert 'GH_AW_DETECTION_CONTINUE_ON_ERROR: "false"' in compiled_text, (
            f"add-community-{workflow}.lock.yml must compile threat detection "
            "in fail-closed mode"
        )
        jobs = yaml.safe_load(compiled_text)["jobs"]
        detection = jobs["detection"]
        assert detection["needs"] == ["activation", "agent"]
        assert detection["if"] == "always() && needs.agent.result != 'skipped'"
        guard = _workflow_step(detection["steps"], "Check if detection needed")
        assert guard["id"] == "detection_guard"
        assert guard["env"] == {
            "OUTPUT_TYPES": "${{ needs.agent.outputs.output_types }}",
            "HAS_PATCH": "${{ needs.agent.outputs.has_patch }}",
        }
        execution = _workflow_step(detection["steps"], "Execute threat detection with AWF")
        assert execution["id"] == "detection_agentic_execution"
        assert execution["if"] == (
            "always() && steps.detection_guard.outputs.run_detection == 'true'"
        )
        assert execution["env"]["GH_AW_DETECTION_CONTINUE_ON_ERROR"] == "false"
        conclusion = _workflow_step(detection["steps"], "Conclude threat detection")
        assert conclusion["id"] == "detection_conclusion"
        assert conclusion["if"] == "always()"
        assert not conclusion.get("continue-on-error", False)
        assert conclusion["env"] == {
            "RUN_DETECTION": "${{ steps.detection_guard.outputs.run_detection }}",
            "DETECTION_AGENTIC_EXECUTION_OUTCOME": (
                "${{ steps.detection_agentic_execution.outcome }}"
            ),
            "GH_AW_DETECTION_CONTINUE_ON_ERROR": "false",
        }
        assert conclusion["run"].strip() == (
            'bash "${RUNNER_TEMP}/gh-aw/actions/conclude_threat_detection.sh" '
            "/tmp/gh-aw/threat-detection/detection_result.json"
        )
        assert _workflow_step(detection["steps"], "Setup Scripts")["uses"] == (
            "github/gh-aw-actions/setup@5e508589e03a7757a7e05b26e834292f5445bfb6"
        )
        assert jobs["safe_outputs"]["needs"] == ["activation", "agent", "detection"]
        assert jobs["safe_outputs"]["if"] == (
            "(!cancelled()) && needs.agent.result != 'skipped' && "
            "needs.detection.result == 'success'"
        )


def test_bug_test_workflow_provisions_python_dependencies():
    _, compiled_text, source, compiled = _agentic_workflow("bug-test")
    steps = compiled["jobs"]["agent"]["steps"]

    assert source["network"] == {
        "allowed": ["defaults", "github.com", "pypi.org", "files.pythonhosted.org"]
    }
    assert '"pypi.org"' in compiled_text
    assert '"files.pythonhosted.org"' in compiled_text
    expected_names = [
        "Checkout repository",
        "Setup uv",
        "Set up Python",
        "Install Python test dependencies",
        "Execute GitHub Copilot CLI",
    ]
    names = [step.get("name") for step in steps]
    positions = [names.index(name) for name in expected_names]
    assert positions == sorted(positions)
    assert _workflow_step(steps, "Setup uv")["uses"] == (
        "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d"
    )
    python_step = _workflow_step(steps, "Set up Python")
    assert python_step["uses"] == (
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
    )
    assert python_step["with"] == {"python-version": "3.14"}
    assert [step["name"] for step in source["steps"]] == expected_names[1:-1]
    for source_step in source["steps"]:
        compiled_step = _workflow_step(steps, source_step["name"])
        assert not source_step.get("continue-on-error", False)
        assert not compiled_step.get("continue-on-error", False)
        for field, value in source_step.items():
            if field == "run":
                assert compiled_step[field].rstrip() == value.rstrip()
            else:
                assert compiled_step[field] == value

    install = _workflow_step(steps, "Install Python test dependencies")["run"]
    assert 'UV_BIN="$(command -v uv)"' in install
    assert "PIP_SUBCOMMAND=pip" in install
    assert '"$UV_BIN" "$PIP_SUBCOMMAND" install --system -e ".[test]"' in install


def test_bug_test_network_allows_only_required_github_host():
    _, _, _, compiled = _agentic_workflow("bug-test")
    steps = compiled["jobs"]["agent"]["steps"]
    domains = set(
        _workflow_step(steps, "Ingest agent output")["env"][
            "GH_AW_ALLOWED_DOMAINS"
        ].split(",")
    )
    assert {"github.com", "pypi.org", "files.pythonhosted.org"} <= domains
    assert all("*" not in domain for domain in domains)
    assert not {
        "gitlab.com", "example.com", "localhost",
        "127.0.0.1", "::1", "10.0.0.1", "172.16.0.1", "192.168.0.1",
        "169.254.169.254", "metadata.google.internal", "metadata.azure.com",
    } & domains
    firewall_step = next(
        step for step in steps if r'\"allowDomains\":[' in step.get("run", "")
    )
    network_match = re.search(
        r'\\"network\\":(\{.*?\}),\\"apiProxy\\"', firewall_step["run"]
    )
    assert network_match is not None
    network = json.loads(network_match[1].replace(r'\"', '"'))
    assert set(network["allowDomains"]) == domains
    assert network["isolation"] is True


def test_bug_test_distinguishes_missing_fix_from_failed_discovery():
    source_text, _, _, _ = _agentic_workflow("bug-test")
    selection = " ".join(
        source_text.split("## Step 2", 1)[1].split("## Step 3", 1)[0].split()
    )
    for clause in (
        (
            "Only after successful discovery establishes that neither a linked "
            "PR nor a named fix branch exists, test the **currently checked-out commit**"
        ),
        (
            "If discovery, fetch, or checkout fails, report the error as an "
            "**environment/setup failure** with an `inconclusive` result "
            "instead of testing another revision."
        ),
    ):
        assert clause in selection


def test_bug_test_requires_original_exit_code_before_log_filtering():
    source_text, _, _, _ = _agentic_workflow("bug-test")
    execution = " ".join(
        source_text.split("## Step 4", 1)[1].split("## Step 5", 1)[0].split()
    )
    assert (
        "For all commands, capture the original exit code **before** filtering "
        "output; successful log filtering must not hide command failure."
    ) in execution


@pytest.mark.parametrize("name", ["bug-fix", "bug-test"])
def test_bug_workflow_upgrade_preserves_runtime_and_negative_guards(name):
    _, compiled_text, source, compiled = _agentic_workflow(name)
    metadata = _gh_aw_metadata(compiled_text)
    assert metadata["compiler_version"] == "v0.88.7"
    assert metadata["engine_versions"] == {"copilot": "1.0.80"}
    assert metadata["strict"] is True
    assert (source.get("on") or source[True]) == {
        "issues": {"types": ["labeled"], "names": [name]},
        "skip-bots": ["github-actions", "copilot", "dependabot"],
    }
    assert (compiled.get("on") or compiled[True]) == {
        "issues": {"types": ["labeled"]}
    }
    guard = (
        "github.event_name != 'issues' || github.event.action != 'labeled' || "
        f"github.event.label.name == '{name}'"
    )
    pre_activation = compiled["jobs"]["pre_activation"]
    assert " ".join(pre_activation["if"].split()) == guard
    assert " ".join(compiled["jobs"]["activation"]["if"].split()) == (
        f"needs.pre_activation.outputs.activated == 'true' && ({guard})"
    )
    assert pre_activation["outputs"]["activated"] == (
        "${{ steps.check_membership.outputs.is_team_member == 'true' && "
        "steps.check_skip_bots.outputs.skip_bots_ok == 'true' }}"
    )
    assert _workflow_step(
        pre_activation["steps"], "Check team membership for workflow"
    )["env"]["GH_AW_REQUIRED_ROLES"] == "admin,maintainer,write"
    assert _workflow_step(pre_activation["steps"], "Check skip-bots")["env"][
        "GH_AW_SKIP_BOTS"
    ] == "github-actions,copilot-swe-agent,Copilot,copilot,@app/copilot-swe-agent,dependabot"

    permissions = {"contents": "read", "issues": "read"}
    output_permissions = {"issues": "write", "pull-requests": "write"}
    labels = ["needs-assessment", "needs-reproduction", "fix-proposed", "fix-blocked"]
    toolsets = ["issues", "repos"]
    if name == "bug-test":
        permissions["pull-requests"] = "read"
        labels = ["tests-passing", "tests-failing", "tests-inconclusive"]
        toolsets.append("pull_requests")
        assert "edit" not in source["tools"]
    else:
        output_permissions["contents"] = "write"
        assert "edit" in source["tools"]
    assert source["tools"]["github"] == {
        "toolsets": toolsets, "min-integrity": "none"
    }
    assert source["permissions"] == permissions
    assert compiled["permissions"] == {}
    agent = compiled["jobs"]["agent"]
    assert agent["permissions"] == permissions
    assert source["checkout"] == {"fetch-depth": 0}
    assert _workflow_step(agent["steps"], "Checkout repository")["with"] == {
        "persist-credentials": False, "fetch-depth": 0
    }
    assert compiled["jobs"]["safe_outputs"]["permissions"] == output_permissions
    assert compiled["jobs"]["conclusion"]["permissions"] == {
        **output_permissions, "actions": "read"
    }

    outputs = _safe_output_config(compiled)
    expected_outputs = {
        "add_comment", "add_labels", "noop", "create_report_incomplete_issue",
        "missing_data", "missing_tool", "report_incomplete",
    }
    expected_source_outputs = {"add-comment", "add-labels", "noop"}
    if name == "bug-fix":
        expected_outputs.add("create_pull_request")
        expected_source_outputs.add("create-pull-request")
    assert set(outputs) == expected_outputs
    assert set(source["safe-outputs"]) == expected_source_outputs
    assert outputs["add_comment"] == source["safe-outputs"]["add-comment"] == {"max": 1}
    assert outputs["add_labels"] == source["safe-outputs"]["add-labels"] == {
        "allowed": labels, "max": 1
    }
    assert source["safe-outputs"]["noop"] == {"report-as-issue": False}
    assert outputs["noop"] == {"max": 1, "report-as-issue": "false"}

    refs = {match.group("ref") for match in USES_RE.finditer(compiled_text)}
    assert refs
    assert all(PINNED_SHA_RE.search(ref) for ref in refs)
    expected_actions = {
        "github/gh-aw-actions/setup@5e508589e03a7757a7e05b26e834292f5445bfb6"
    }
    if name == "bug-test":
        expected_actions.add(
            "github/gh-aw-actions/setup-cli@5e508589e03a7757a7e05b26e834292f5445bfb6"
        )
    assert {
        ref for ref in refs if ref.startswith("github/gh-aw-actions/")
    } == expected_actions


def test_bug_fix_upgrade_preserves_scoped_draft_pr_contract():
    source_text, _, source, compiled = _agentic_workflow("bug-fix")
    create_pr = _safe_output_config(compiled)["create_pull_request"]
    assert source["safe-outputs"]["create-pull-request"] == {
        "title-prefix": "[bug-fix] ",
        "labels": ["bug-fix", "automated"],
        "draft": True,
        "max": 1,
        "protected-files": {
            "policy": "blocked", "exclude": ["README.md", "CHANGELOG.md"]
        },
    }
    assert create_pr["draft"] is True
    assert create_pr["title_prefix"] == "[bug-fix] "
    assert create_pr["labels"] == ["bug-fix", "automated"]
    assert create_pr["max"] == 1
    assert create_pr["max_patch_files"] == 100
    assert create_pr["max_patch_size"] == 4096
    assert create_pr["protected_files_policy"] == "blocked"
    assert create_pr["protect_top_level_dot_folders"] is True
    assert not create_pr.get("protected_dot_folder_excludes")
    assert set(create_pr["protected_files"]) == {
        "package.json", "bun.lockb", "bunfig.toml", "deno.json", "deno.jsonc",
        "deno.lock", "global.json", "NuGet.Config", "Directory.Packages.props",
        "mix.exs", "mix.lock", "go.mod", "go.sum", "stack.yaml", "stack.yaml.lock",
        "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
        "settings.gradle.kts", "gradle.properties", "package-lock.json",
        "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json", "requirements.txt",
        "Pipfile", "Pipfile.lock", "pyproject.toml", "setup.py", "setup.cfg",
        "Gemfile", "Gemfile.lock", "uv.lock", "CODEOWNERS", "DESIGN.md",
        "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "AGENTS.md",
    }
    text = " ".join(source_text.split())
    for clause in (
        (
            "Find the **most recent** such assessment comment that appears "
            "**workflow-authored**: the author is a **bot/service account**"
        ),
        (
            "**Valid** (or **Likely valid, needs reproduction** with no blocking "
            "clarifications) — continue."
        ),
        "Implement the **preferred** remediation from the assessment",
        "**Stay within the files the assessment named**",
        "record it explicitly in the PR body under **Deviations from Assessment**",
        "Use the `create-pull-request` safe output to open a **draft** PR",
        "Use `Refs` (not `Closes`)",
        "Add **exactly one** status label per run when the label exists",
    ):
        assert clause in text


def test_bug_fix_upgrade_preserves_missing_and_blocked_assessment_responses():
    source_text, _, _, _ = _agentic_workflow("bug-fix")
    text = " ".join(source_text.split())
    missing = text.split("If **no** assessment comment exists on the issue:", 1)[1]
    missing = missing.split("## Step 2", 1)[0]
    for clause in (
        "Add **one** comment explaining that a fix cannot be proposed",
        "apply the `bug-assess` label first",
        "If the `needs-assessment` label already exists",
        "**Stop.** Do not read the codebase, do not edit files, do not open a PR.",
    ):
        assert clause in missing
    blocked = text.split("Before changing any code, check the assessment's verdict:", 1)[1]
    blocked = blocked.split("Restate, in", 1)[0]
    for clause in (
        "**Invalid** — there is nothing to fix. Add **one** comment",
        "`fix-blocked` label exists",
        "Then **stop**. Do not open a PR.",
        "**Likely valid, needs reproduction** with unresolved `[NEEDS CLARIFICATION]`",
        "Add **one** comment listing the open questions",
        "`needs-reproduction` label exists",
        "**Stop.** (There is no human in this automated run",
    ):
        assert clause in blocked
    assert "Revert your partial edits, add a comment summarizing the new finding." in text
    assert "Recommend re-running `bug-assess`, and **stop** without opening a PR." in text
    assert "do not also add `fix-proposed` in those cases" in text


def test_bug_test_upgrade_preserves_fix_selection_and_no_fix_reporting():
    source_text, _, _, _ = _agentic_workflow("bug-test")
    text = " ".join(source_text.split())
    choices = [
        "**Linked pull request (preferred).**",
        "**Fix branch (fallback).**",
        "**Current checkout (last resort).**",
    ]
    positions = [text.index(choice) for choice in choices]
    assert positions == sorted(positions)
    for clause in (
        (
            '`git fetch origin "pull/<PR_NUMBER>/head:bug-test-fix"` then '
            "`git checkout bug-test-fix`"
        ),
        "Record the PR number and head SHA.",
        '`git fetch origin "<branch>:bug-test-fix"` then `git checkout bug-test-fix`',
        "Only check out branches from **this** repository's `origin`.",
        "test the **currently checked-out commit**",
        (
            "no dedicated fix artifact was found, so the result reflects the base "
            "branch, not a proposed fix."
        ),
        'FIX_SOURCE = "current checkout (no fix artifact found)"',
        "Never check out, fetch, or execute code referenced by a non-`origin` URL",
        "**Wrap every test invocation in a timeout**",
        "**environment/setup failure** distinct from test failures",
        "**Read-only on repository source.** Never modify, create, or delete tracked files",
        "post an `inconclusive` report that clearly explains why",
        (
            "`tests-inconclusive` when the run could not produce a clear pass/fail "
            "(setup failure, no stack detected, or no fix artifact found)"
        ),
    ):
        assert clause in text


@requires_bash
@pytest.mark.parametrize("compiled_step", [False, True], ids=["source", "compiled"])
@pytest.mark.parametrize("exit_code", [0, 17], ids=["success", "install-failure"])
def test_bug_test_install_preserves_editable_extras_and_failure(compiled_step, exit_code):
    _, _, source, compiled = _agentic_workflow("bug-test")
    steps = compiled["jobs"]["agent"]["steps"] if compiled_step else source["steps"]
    script = _workflow_step(steps, "Install Python test dependencies")["run"]
    fake_uv = f'uv() {{ printf "%s\\n" "$@"; return {exit_code}; }}\n'
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", fake_uv + script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.splitlines() == ["pip", "install", "--system", "-e", ".[test]"]
    assert result.returncode == exit_code, result.stderr
