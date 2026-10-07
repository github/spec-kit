"""Execution wiring for the community workflow step submission flow."""

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys

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


def test_step_metadata_setup_failures_allow_blocker_reporting():
    _, _, source, compiled = _agentic_workflow("add-community-workflow-step")
    for name in ("Set up Python for step metadata validation", "Install metadata parser"):
        for steps in (source["steps"], compiled["jobs"]["agent"]["steps"]):
            assert _workflow_step(steps, name)["continue-on-error"] is True


@pytest.fixture
def verifier():
    path = REPO_ROOT / ".github/scripts/validate_community_workflow_step.py"
    spec = importlib.util.spec_from_file_location("step_submission_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def file_submission():
    base = "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/"
    return {
        "step_id": "deploy-preview",
        "repository": "https://github.com/example/steps",
        "version": "1.2.3",
        "release_tag": "deploy-v1.2.3",
        "file": "__init__.py",
        "catalog_entry": {
            "step_yml_url": base + "step.yml",
            "init_url": base + "__init__.py",
            "sha256": {
                "step.yml": "0" * 64,
                "__init__.py": hashlib.sha256(b"fixture bytes").hexdigest(),
            },
        },
    }


@pytest.mark.parametrize("step_id", [
    "con", "prn", "aux", "nul", "com1", "com9", "lpt1", "lpt9",
])
def test_submission_rejects_ids_accepted_by_old_regex(verifier, file_submission, step_id):
    assert re.fullmatch(r"[a-z][a-z0-9-]*", step_id)
    file_submission["step_id"] = step_id
    with pytest.raises(verifier.SubmissionMismatch, match="Invalid step id"):
        verifier.validate_identity(file_submission)


@pytest.mark.parametrize("step_id", ["deploy-preview", "com10", "lpt10", "console"])
def test_submission_accepts_installable_ids(verifier, file_submission, step_id):
    file_submission["step_id"] = step_id
    assert verifier.validate_identity(file_submission) == (
        "example", "steps", "deploy-v1.2.3",
    )


def test_file_fetch_passes_one_validated_url_argument_and_hashes_bytes(
    verifier, file_submission, tmp_path, monkeypatch,
):
    output = tmp_path / "download"
    calls = []

    def curl(args, **kwargs):
        calls.append((args, kwargs))
        output.write_bytes(b"fixture bytes")
        return subprocess.CompletedProcess(args, 0, "200", "")

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    result = verifier.fetch_file(file_submission, output)
    assert result == {
        "file": "__init__.py",
        "sha256": hashlib.sha256(b"fixture bytes").hexdigest(),
    }
    assert calls == [([
        "curl", "--proto", "=https", "--max-time", "60",
        "--max-filesize", "10485760", "--silent", "--show-error",
        "--write-out", "%{http_code}", "--output", str(output),
        file_submission["catalog_entry"]["init_url"],
    ], {"capture_output": True, "text": True, "check": False})]


@pytest.mark.parametrize("url", [
    "https://evil.example/__init__.py",
    "https://raw.githubusercontent.com/other/steps/deploy-v1.2.3/package/__init__.py",
    "https://raw.githubusercontent.com/example/steps/main/package/__init__.py",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/other/__init__.py",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/../__init__.py",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/%2e%2e/__init__.py",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/__init__.py?x=1",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/__init__.py#x",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/$(touch injected)",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/`touch injected`",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/x; touch injected",
    "https://raw.githubusercontent.com/example/steps/deploy-v1.2.3/package/x\n--output injected",
    "--output=injected",
])
def test_invalid_file_urls_are_rejected_before_fetch(
    verifier, file_submission, tmp_path, monkeypatch, url,
):
    file_submission["catalog_entry"]["init_url"] = url

    def unexpected_fetch(*args, **kwargs):
        pytest.fail("Invalid URL reached curl")

    monkeypatch.setattr(verifier.subprocess, "run", unexpected_fetch)
    with pytest.raises(verifier.SubmissionMismatch):
        verifier.fetch_file(file_submission, tmp_path / "download")
    assert not (tmp_path / "injected").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="executable fixture uses a POSIX shebang")
@pytest.mark.parametrize("suffix", [
    "$(touch injected)", "`touch injected`", "; touch injected", "\n--output injected",
])
def test_fetch_keeps_malicious_text_in_one_argument_even_if_validation_is_bypassed(
    verifier, file_submission, tmp_path, monkeypatch, suffix,
):
    curl = tmp_path / "curl"
    arguments = tmp_path / "arguments.json"
    curl.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        f"Path({str(arguments)!r}).write_text(json.dumps(sys.argv[1:]))\n"
        "Path(sys.argv[sys.argv.index('--output') + 1]).write_bytes(b'fixture bytes')\n"
        "print('200', end='')\n"
    )
    curl.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    url = file_submission["catalog_entry"]["init_url"] + suffix
    expected = hashlib.sha256(b"fixture bytes").hexdigest()
    monkeypatch.setattr(
        verifier, "validate_file", lambda _: ("__init__.py", url, expected)
    )
    result = verifier.fetch_file(file_submission, tmp_path / "download")
    args = json.loads(arguments.read_text())
    assert args[-1] == url
    assert len(args) == 13
    assert result["sha256"] == expected
    assert not (tmp_path / "injected").exists()


def test_nested_binary_extra_file_is_hashed(verifier, file_submission, tmp_path, monkeypatch):
    entry = file_submission["catalog_entry"]
    body = b"\x00\xff\nbinary fixture"
    entry["extra_files"] = {
        "data/fixture.bin": entry["step_yml_url"].removesuffix("step.yml") + "data/fixture.bin",
    }
    entry["sha256"]["data/fixture.bin"] = hashlib.sha256(body).hexdigest().upper()
    file_submission["file"] = "data/fixture.bin"
    output = tmp_path / "download"

    def curl(args, **kwargs):
        output.write_bytes(body)
        return subprocess.CompletedProcess(args, 0, "200", "")

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    assert verifier.fetch_file(file_submission, output) == {
        "file": "data/fixture.bin", "sha256": hashlib.sha256(body).hexdigest(),
    }


@pytest.mark.parametrize(("status", "http", "error_type"), [
    (7, "000", "Blocked"),
    (28, "000", "Blocked"),
    (63, "200", "SubmissionMismatch"),
    (0, "404", "SubmissionMismatch"),
    (0, "302", "SubmissionMismatch"),
    (0, "403", "Blocked"),
    (0, "429", "Blocked"),
    (0, "503", "Blocked"),
])
def test_fetch_failures_prevent_hashing(
    verifier, file_submission, tmp_path, monkeypatch, status, http, error_type,
):
    output = tmp_path / "download"
    output.write_bytes(b"stale successful download")
    monkeypatch.setattr(
        verifier.subprocess, "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, status, http, "curl error"),
    )

    def unexpected_hash(*args, **kwargs):
        pytest.fail("Failed download reached hashing")

    monkeypatch.setattr(verifier.hashlib, "sha256", unexpected_hash)
    with pytest.raises(getattr(verifier, error_type)):
        verifier.fetch_file(file_submission, output)


def test_submitted_checksum_mismatch_fails(verifier, file_submission, tmp_path, monkeypatch):
    output = tmp_path / "download"

    def curl(args, **kwargs):
        output.write_bytes(b"different bytes")
        return subprocess.CompletedProcess(args, 0, "200", "")

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    with pytest.raises(verifier.SubmissionMismatch, match="SHA-256 mismatch"):
        verifier.fetch_file(file_submission, output)


def test_missing_metadata_parser_is_blocked(file_submission, tmp_path):
    issue = tmp_path / "submission.json"
    issue.write_text(json.dumps(file_submission))
    result = subprocess.run(
        [sys.executable, "-S", str(REPO_ROOT / ".github/scripts/validate_community_workflow_step.py"),
         "identity", "--submission", str(issue)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert result.stdout.startswith("BLOCKED:")
    assert "yaml" in result.stdout
    assert not result.stderr


def test_workflow_invokes_the_tested_verifier_with_fixed_arguments():
    source, _, _, _ = _agentic_workflow("add-community-workflow-step")
    commands = [
        command.strip() for command in re.findall(r"```bash\n(.*?)\n\s*```", source, re.DOTALL)
    ]
    assert commands == [
        "python3 .github/scripts/validate_community_workflow_step.py identity "
        "--submission /tmp/gh-aw/step-submission.json",
        "python3 .github/scripts/validate_community_workflow_step.py fetch "
        "--submission /tmp/gh-aw/step-submission.json",
    ]
