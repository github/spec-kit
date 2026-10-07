"""Execution wiring for the community workflow step submission flow."""

import json
import shutil
import subprocess

import pytest
import yaml

from tests.test_github_workflows import (
    REPO_ROOT,
    REPOSITORY_OWNED_DRAFT_PR_EXEMPTION,
    WORKFLOWS_DIR,
    _agentic_workflow,
    _safe_output_config,
    _workflow_step,
)


def test_step_submission_form_and_compiled_workflow_contract():
    form = yaml.safe_load(
        (REPO_ROOT / ".github/ISSUE_TEMPLATE/workflow_step_submission.yml").read_text()
    )
    text, compiled_text, source, compiled = _agentic_workflow("add-community-workflow-step")
    assert form["title"].startswith("[Workflow Step]:")
    assert form["labels"] == ["enhancement", "needs-triage"]
    assert "workflow-step-submission" in form["body"][0]["attributes"]["value"]
    assert (source.get("on") or source[True]) == {
        "issues": {"types": ["labeled"], "names": ["workflow-step-submission"]},
        "skip-bots": ["github-actions", "copilot", "dependabot"],
    }
    for field in form["body"]:
        if field["type"] in ("input", "textarea"):
            assert field["validations"]["required"] is True
            assert f'`{field["id"]}`' in text
        elif field["type"] == "checkboxes":
            assert all(item["required"] for item in field["attributes"]["options"])
    assert source["permissions"] == compiled["jobs"]["agent"]["permissions"] == {
        "contents": "read", "issues": "read",
    }
    guard = (
        "github.event_name != 'issues' || github.event.action != 'labeled' || "
        "github.event.label.name == 'workflow-step-submission'"
    )
    activation = compiled["jobs"]["pre_activation"]
    assert " ".join(activation["if"].split()) == guard
    assert _workflow_step(activation["steps"], "Check team membership for workflow")[
        "env"
    ]["GH_AW_REQUIRED_ROLES"] == "admin,maintainer,write"
    assert (compiled.get("on") or compiled[True]) == {"issues": {"types": ["labeled"]}}
    assert source["safe-outputs"]["threat-detection"]["continue-on-error"] is False
    outputs = _safe_output_config(compiled)
    assert outputs["create_pull_request"]["allowed_files"] == [
        "workflows/step-catalog.community.json", "docs/community/workflow-steps.md",
    ]
    assert outputs["create_pull_request"]["draft"] is True
    assert outputs["create_pull_request"]["max"] == 1
    assert outputs["add_labels"]["issue_intent"] is False
    assert outputs["remove_labels"]["allowed"] == [
        "validation-passed", "validation-failed", "needs-info",
    ]
    assert REPOSITORY_OWNED_DRAFT_PR_EXEMPTION in " ".join(text.split())
    assert "{{#runtime-import .github/workflows/add-community-workflow-step.md}}" in compiled_text
    conclusion = compiled["jobs"]["conclusion"]
    step = source["jobs"]["conclusion"]["pre-steps"][0]
    assert _workflow_step(conclusion["steps"], step["name"]) == step
    assert step["if"] == (
        "needs.safe_outputs.result == 'success' && "
        "needs.safe_outputs.outputs.created_pr_number != ''"
    )
    assert conclusion["permissions"]["issues"] == "write"
    assert compiled["jobs"]["safe_outputs"]["outputs"]["created_pr_number"] == (
        "${{ steps.process_safe_outputs.outputs.created_pr_number }}"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
@pytest.mark.parametrize(("action", "labels", "event_label", "expected"), [
    ("opened", ["workflow-step-submission"], "", True),
    ("labeled", ["workflow-step-submission"], "workflow-step-submission", True),
    ("opened", ["needs-triage"], "", False),
    ("labeled", ["workflow-step-submission"], "unrelated", False),
    ("closed", ["workflow-step-submission"], "", False),
    ("opened", ["extension-submission"], "", True),
    ("labeled", ["preset-submission"], "preset-submission", True),
    ("labeled", ["bundle-submission"], "bundle-submission", True),
])
def test_catalog_notification_trigger(action, labels, event_label, expected):
    workflow = yaml.safe_load((WORKFLOWS_DIR / "catalog-assign.yml").read_text())
    condition = workflow["jobs"]["notify"]["if"].replace(
        "github.event.issue.labels.*.name", "issueLabels"
    )
    script = """
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const contains = (values, value) => values.includes(value);
const github = {event: {action: input.action, label: {name: input.event_label}}};
const result = new Function('github', 'issueLabels', 'contains',
  `return ${input.condition}`)(github, input.labels, contains);
console.log(JSON.stringify(result));
"""
    result = subprocess.run(
        ["node", "-e", script],
        input=json.dumps({
            "condition": condition, "action": action,
            "labels": labels, "event_label": event_label,
        }),
        capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) is expected
