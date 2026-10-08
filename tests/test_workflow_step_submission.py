"""Execution wiring for the community workflow step submission flow."""

import hashlib
import importlib.util
import json
import builtins
import copy
import re
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

from tests.test_github_workflows import (
    REPO_ROOT,
    REPOSITORY_OWNED_DRAFT_PR_EXEMPTION,
    WORKFLOWS_DIR,
    _agentic_workflow,
    _community_submission_agent_run,
    _safe_output_config,
    _workflow_step,
)


def test_step_submission_form_and_compiled_workflow_contract():
    form = yaml.safe_load(
        (REPO_ROOT / ".github/ISSUE_TEMPLATE/workflow_step_submission.yml").read_text()
    )
    text, compiled_text, source, compiled = _agentic_workflow("add-community-workflow-step")
    assert form["title"].startswith("[Workflow Step]:")
    assert form["labels"] == ["triage-must-have"]
    assert "workflow-step-submission" in form["body"][0]["attributes"]["value"]
    assert (source.get("on") or source[True]) == {
        "issues": {"types": ["labeled"], "names": ["workflow-step-submission"]},
        "skip-bots": ["github-actions", "copilot", "dependabot"],
    }
    for field in form["body"]:
        if field["type"] in ("input", "textarea", "dropdown"):
            assert bool(field.get("validations", {}).get("required")) == (
                field["id"] not in {"changelog", "additional-context"}
            )
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
    assert outputs["add_labels"]["allowed"] == [
        "workflow-step-submission", "validation-failed", "needs-info",
    ]
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


@pytest.mark.parametrize("kind", ["source", "compiled"])
def test_agent_cannot_add_success_label_before_publication(kind):
    _, _, source, compiled = _agentic_workflow("add-community-workflow-step")
    config = (
        source["safe-outputs"]["add-labels"]
        if kind == "source" else _safe_output_config(compiled)["add_labels"]
    )
    assert "validation-passed" not in config["allowed"]
    assert {"validation-failed", "needs-info"} <= set(config["allowed"])


def test_tagged_license_rest_endpoint_is_reachable_through_enabled_tools():
    _, _, source, compiled = _agentic_workflow("add-community-workflow-step")
    assert source["engine"]["args"] == [
        "--allow-url=https://github.com",
        "--allow-url=https://raw.githubusercontent.com",
        "--allow-url=https://api.github.com",
    ]
    assert source["network"]["allowed"] == [
        "defaults", "github.com", "raw.githubusercontent.com", "api.github.com",
    ]
    assert "web-fetch" in source["tools"]
    agent_run = _community_submission_agent_run("workflow-step")
    assert "--allow-url=https://api.github.com" in agent_run
    assert "--allow-tool web_fetch" in agent_run
    match = re.search(r'\\"network\\":(\{.*?\}),\\"apiProxy\\"', agent_run)
    assert match is not None
    network = json.loads(match[1].replace(r'\"', '"'))
    assert isinstance(network["allowDomains"], list)
    assert any(domain == "api.github.com" for domain in network["allowDomains"])
    assert network["isolation"] is True
    assert not any("*" in domain for domain in network["allowDomains"])
    assert not {"localhost", "127.0.0.1", "169.254.169.254"} & set(network["allowDomains"])
    domains = _workflow_step(
        compiled["jobs"]["agent"]["steps"], "Ingest agent output"
    )["env"]["GH_AW_ALLOWED_DOMAINS"].split(",")
    assert any(domain == "api.github.com" for domain in domains)


@pytest.mark.parametrize("layer", ["firewall", "ingestion"])
@pytest.mark.parametrize("lookalike", [
    "api.github.com.attacker.example", "attacker-api.github.com",
])
def test_license_rest_host_requires_an_exact_domain_entry(monkeypatch, layer, lookalike):
    module = sys.modules[__name__]
    if layer == "firewall":
        agent_run = _community_submission_agent_run("workflow-step")
        monkeypatch.setattr(
            module, "_community_submission_agent_run",
            lambda _: agent_run.replace(r'\"api.github.com\"', rf'\"{lookalike}\"'),
        )
    else:
        text, lock, source, compiled = _agentic_workflow("add-community-workflow-step")
        env = _workflow_step(
            compiled["jobs"]["agent"]["steps"], "Ingest agent output"
        )["env"]
        env["GH_AW_ALLOWED_DOMAINS"] = env["GH_AW_ALLOWED_DOMAINS"].replace(
            "api.github.com", lookalike,
        )
        monkeypatch.setattr(module, "_agentic_workflow", lambda _: (text, lock, source, compiled))
    with pytest.raises(AssertionError):
        test_tagged_license_rest_endpoint_is_reachable_through_enabled_tools()


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
        "download_url": "https://github.com/example/steps/releases/download/deploy-v1.2.3/deploy-preview-1.2.3.zip",
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


@pytest.mark.parametrize(("version", "tag"), [
    ("1.2", "v1.2"),
    ("1.2rc1", "deploy-v1.2rc1"),
    ("1.2.post1", "v1.2.post1"),
    ("1.2.dev1", "deploy-v1.2.dev1"),
    ("1.2+cpu", "v1.2+cpu"),
    ("1!2.0", "v1!2.0"),
    ("1!2.0+cpu", "deploy-v1!2.0+cpu"),
])
def test_canonical_form_pep440_versions_are_supported(verifier, file_submission, version, tag):
    file_submission.update({
        "version": version,
        "release_tag": tag,
        "download_url": f"https://github.com/example/steps/releases/download/{tag}/step-{version}.zip",
    })
    assert verifier.validate_identity(file_submission) == ("example", "steps", tag)


@pytest.mark.parametrize("tag", ["1!2.0", "v1!2.0", "deploy-v1!2.0"])
@pytest.mark.parametrize("route", ["releases/download", "archive/refs/tags"])
def test_epoch_release_urls_and_catalog_files_are_supported(
    verifier, file_submission, tag, route,
):
    file_submission["version"] = "1!2.0"
    file_submission["release_tag"] = tag
    suffix = "/step-1!2.0.zip" if route == "releases/download" else ".tar.gz"
    file_submission["download_url"] = f"https://github.com/example/steps/{route}/{tag}{suffix}"
    entry = file_submission["catalog_entry"]
    for key in ("step_yml_url", "init_url"):
        entry[key] = entry[key].replace("deploy-v1.2.3", tag)
    assert verifier.validate_file(file_submission) == (
        "__init__.py", entry["init_url"], entry["sha256"]["__init__.py"],
    )


def test_epoch_version_does_not_match_non_epoch_tag(verifier, file_submission):
    file_submission["version"] = "1!1.2.3"
    with pytest.raises(verifier.SubmissionMismatch, match="Release Tag must match Version"):
        verifier.validate_identity(file_submission)


@pytest.mark.parametrize("version", ["main", "not-a-version", "1..2", "1.2/3"])
def test_invalid_pep440_versions_are_rejected(verifier, file_submission, version):
    file_submission["version"] = version
    with pytest.raises(verifier.SubmissionMismatch, match="invalid PEP 440"):
        verifier.validate_identity(file_submission)


@pytest.mark.parametrize("suffix", [".zip", ".tar.gz", ".tgz"])
@pytest.mark.parametrize("route", ["releases/download/deploy-v1.2.3/package", "archive/refs/tags/deploy-v1.2.3"])
def test_canonical_archive_formats_match_github_routes(verifier, file_submission, suffix, route):
    file_submission["download_url"] = "https://github.com/example/steps/" + route + suffix
    if route.startswith("archive/") and suffix == ".tgz":
        with pytest.raises(verifier.SubmissionMismatch, match="Download URL"):
            verifier.validate_identity(file_submission)
    else:
        assert verifier.validate_identity(file_submission) == ("example", "steps", "deploy-v1.2.3")


@pytest.mark.parametrize("url", [
    "https://evil.example/steps/releases/download/deploy-v1.2.3/step.zip",
    "https://github.com/other/steps/releases/download/deploy-v1.2.3/step.zip",
    "https://github.com/example/steps/releases/download/v1.2.4/step.zip",
    "https://github.com/example/steps/releases/latest/step.zip",
    "https://github.com/example/steps/releases/download/deploy-v1.2.3/step.zip?x=1",
    "https://github.com/example/steps/releases/download/deploy-v1.2.3/step.zip#x",
    "https://github.com/example/steps/releases/download/deploy-v1.2.3/../step.zip",
    "https://github.com/example/steps/releases/download/deploy-v1.2.3/step%20name.zip",
    "https://github.com/example/steps/releases/download/deploy-v1.2.3/step.zip\n",
    "https://github.com/example/steps/archive/refs/tags/deploy-v1.2.3.tgz",
    "https://[invalid/step.zip",
])
def test_invalid_canonical_download_urls_prevent_file_fetch(
    verifier, file_submission, url, tmp_path, monkeypatch,
):
    file_submission["download_url"] = url

    def unexpected_fetch(*args, **kwargs):
        pytest.fail("Invalid archive provenance reached a file fetch")

    monkeypatch.setattr(verifier.subprocess, "run", unexpected_fetch)
    with pytest.raises(verifier.SubmissionMismatch):
        verifier.fetch_file(file_submission, tmp_path / "download")


def test_canonical_download_url_is_required(verifier, file_submission):
    del file_submission["download_url"]
    with pytest.raises(verifier.SubmissionMismatch, match="download_url"):
        verifier.validate_identity(file_submission)


def test_missing_version_parser_is_blocked(verifier, file_submission, monkeypatch):
    real_import = builtins.__import__

    def missing_packaging(name, *args, **kwargs):
        if name == "packaging.version":
            raise ModuleNotFoundError("No module named packaging.version")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_packaging)
    with pytest.raises(verifier.Blocked, match="packaging.version"):
        verifier.validate_identity(file_submission)


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
        "curl", "--disable", "--proto", "=https", "--max-time", "60",
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
    assert len(args) == 14
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
    (0, "407", "Blocked"),
    (0, "408", "Blocked"),
    (0, "429", "Blocked"),
    (0, "503", "Blocked"),
    (63, "403", "Blocked"),
    (63, "407", "Blocked"),
    (63, "408", "Blocked"),
    (63, "429", "Blocked"),
    (63, "503", "Blocked"),
    (63, "404", "SubmissionMismatch"),
    (63, "302", "SubmissionMismatch"),
    (63, "000", "Blocked"),
    (28, "200", "Blocked"),
])
@pytest.mark.parametrize("remaining_bytes", [None, 1])
def test_fetch_failures_prevent_hashing(
    verifier, file_submission, tmp_path, monkeypatch, status, http, error_type,
    remaining_bytes,
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
    with pytest.raises(getattr(verifier, error_type)) as error:
        verifier.fetch_file(file_submission, output, remaining_bytes=remaining_bytes)
    if http not in ("000", "200"):
        assert "HTTP" in str(error.value)
        assert http in str(error.value)


@pytest.mark.skipif(
    shutil.which("curl") is None or sys.platform == "win32",
    reason="requires real POSIX curl config discovery",
)
@pytest.mark.parametrize("config_source", ["HOME", "CURL_HOME"])
def test_real_curl_ignores_hostile_user_configuration(
    verifier, file_submission, tmp_path, monkeypatch, config_source,
):
    connections = []

    class Proxy(BaseHTTPRequestHandler):
        def do_CONNECT(self):
            connections.append(self.path)
            self.send_response(407)
            self.end_headers()

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Proxy) as proxy:
        thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        thread.start()
        trace = tmp_path / "hostile-config-trace"
        config_directory = tmp_path / "config"
        config_directory.mkdir()
        (config_directory / ".curlrc").write_text(
            "insecure\nlocation\n"
            f'trace-ascii = "{trace.as_posix()}"\n'
            'url = "https://unvalidated.example/extra"\n',
            encoding="utf-8",
        )
        home = tmp_path / "empty-home"
        home.mkdir()
        for key in ("CURL_HOME", "XDG_CONFIG_HOME", "ALL_PROXY", "all_proxy", "https_proxy"):
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv(config_source, str(config_directory))
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{proxy.server_port}")
        monkeypatch.setenv("NO_PROXY", "")
        monkeypatch.setenv("no_proxy", "")
        try:
            with pytest.raises(verifier.Blocked):
                verifier.fetch_file(file_submission, tmp_path / "download")
        finally:
            proxy.shutdown()
            thread.join(timeout=5)
        assert not trace.exists(), "curl loaded the hostile user configuration"
        assert connections == ["raw.githubusercontent.com:443"]


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
        "python3 .github/scripts/validate_community_workflow_step.py snapshot "
        "--submission /tmp/gh-aw/step-submission.json",
        "python3 .github/scripts/validate_community_workflow_step.py generated "
        "--submission /tmp/gh-aw/step-submission.json",
    ]


@pytest.fixture
def catalog_update(file_submission):
    data = copy.deepcopy(file_submission)
    entry = data["catalog_entry"]
    entry.update({"id": data["step_id"], "version": data["version"], "verified": False})
    previous = copy.deepcopy(entry)
    previous.update({
        "version": "1.1.0", "created_at": "2025-01-01T00:00:00Z",
        "tags": ["retained"], "download_url": "https://example.com/1.1.0/package.zip",
        "extra_files": {"old.py": "https://example.com/1.1.0/old.py"},
    })
    previous["sha256"]["old.py"] = "a" * 64
    historical = {
        key: copy.deepcopy(previous[key])
        for key in ("step_yml_url", "init_url", "extra_files", "sha256", "download_url")
    }
    historical["download_url"] = "https://example.com/1.0.0/package.zip"
    previous["releases"] = {"1.0.0": historical}
    original = {
        "schema_version": "1.0", "catalog_url": "https://example.com/catalog.json",
        "updated_at": "2025-01-01T00:00:00Z",
        "steps": {data["step_id"]: previous, "unrelated": {"retained": True}},
    }
    receipt = {"sha256": copy.deepcopy(entry["sha256"]), "bytes": 42}
    return data, original, receipt


def test_catalog_update_migrates_current_release_and_preserves_history(verifier, catalog_update):
    data, original, receipt = catalog_update
    before = copy.deepcopy(original)
    snapshot = verifier.catalog_snapshot(data, original, receipt)
    generated = snapshot["expected_catalog"]
    verifier.verify_generated_catalog(snapshot, generated)
    entry = generated["steps"][data["step_id"]]
    previous = before["steps"][data["step_id"]]
    assert entry["releases"]["1.0.0"] == previous["releases"]["1.0.0"]
    assert entry["releases"]["1.1.0"] == {
        key: previous[key] for key in verifier.RELEASE_FIELDS if key in previous
    }
    assert "id" not in entry["releases"]["1.1.0"]
    assert "version" not in entry["releases"]["1.1.0"]
    assert "old.py" not in entry.get("extra_files", {})
    assert entry["created_at"] == previous["created_at"]
    assert entry["tags"] == previous["tags"]
    assert generated["steps"]["unrelated"] == before["steps"]["unrelated"]
    assert generated["catalog_url"] == before["catalog_url"]
    assert generated["schema_version"] == before["schema_version"]
    assert original == before


@pytest.mark.parametrize("release", ["current", "historical"])
@pytest.mark.parametrize("bad_digest", [None, {}, {"step.yml": "bad"}])
def test_missing_existing_release_digests_block_snapshot(
    verifier, catalog_update, release, bad_digest,
):
    data, original, receipt = catalog_update
    previous = original["steps"][data["step_id"]]
    record = previous if release == "current" else previous["releases"]["1.0.0"]
    record["sha256"] = bad_digest
    with pytest.raises(verifier.Blocked, match="complete SHA-256"):
        verifier.catalog_snapshot(data, original, receipt)


@pytest.mark.parametrize("change", [
    "omit_old_current", "drop_history", "alter_history_digest", "alter_created_at",
    "alter_unrelated", "alter_catalog_url", "alter_current_digest",
])
def test_generated_catalog_mutations_prevent_publication(verifier, catalog_update, change):
    data, original, receipt = catalog_update
    snapshot = verifier.catalog_snapshot(data, original, receipt)
    generated = copy.deepcopy(snapshot["expected_catalog"])
    entry = generated["steps"][data["step_id"]]
    if change == "omit_old_current":
        del entry["releases"]["1.1.0"]
    elif change == "drop_history":
        del entry["releases"]["1.0.0"]
    elif change == "alter_history_digest":
        entry["releases"]["1.0.0"]["sha256"]["step.yml"] = "f" * 64
    elif change == "alter_created_at":
        entry["created_at"] = "changed"
    elif change == "alter_unrelated":
        generated["steps"]["unrelated"] = {}
    elif change == "alter_catalog_url":
        generated["catalog_url"] = "changed"
    else:
        entry["sha256"]["step.yml"] = "f" * 64
    with pytest.raises(verifier.GeneratedError, match="differs from validated snapshot"):
        verifier.verify_generated_catalog(snapshot, generated)


def test_new_catalog_entry_gets_no_invented_history(verifier, catalog_update):
    data, original, receipt = catalog_update
    del original["steps"][data["step_id"]]
    snapshot = verifier.catalog_snapshot(data, original, receipt)
    entry = snapshot["expected_catalog"]["steps"][data["step_id"]]
    assert "releases" not in entry
    assert entry["created_at"] == entry["updated_at"]
    verifier.verify_generated_catalog(snapshot, snapshot["expected_catalog"])


@pytest.mark.parametrize("change", ["unapproved", "digest", "url", "approved"])
def test_same_version_repairs_cannot_replace_content(verifier, catalog_update, change):
    data, original, receipt = catalog_update
    previous = original["steps"][data["step_id"]]
    data["catalog_entry"] = {
        key: copy.deepcopy(value) for key, value in previous.items() if key != "releases"
    }
    data["version"] = previous["version"]
    data["release_tag"] = "v1.1.0"
    data["download_url"] = "https://github.com/example/steps/releases/download/v1.1.0/step.zip"
    # URL validation uses the new release metadata; keep original file metadata aligned.
    base = "https://raw.githubusercontent.com/example/steps/v1.1.0/package/"
    for record in (previous, data["catalog_entry"]):
        record["step_yml_url"] = base + "step.yml"
        record["init_url"] = base + "__init__.py"
        record["extra_files"] = {"old.py": base + "old.py"}
        record["download_url"] = data["download_url"]
    if change != "unapproved":
        data["metadata_only"] = True
    if change == "digest":
        data["catalog_entry"]["sha256"]["step.yml"] = "f" * 64
    elif change == "url":
        data["catalog_entry"]["download_url"] = data["download_url"] + "-different"
    receipt["sha256"] = copy.deepcopy(data["catalog_entry"]["sha256"])
    if change == "approved":
        data["catalog_entry"]["description"] = "Corrected metadata"
        snapshot = verifier.catalog_snapshot(data, original, receipt)
        generated = snapshot["expected_catalog"]["steps"][data["step_id"]]
        assert generated["releases"] == previous["releases"]
        assert generated["description"] == "Corrected metadata"
        assert generated["created_at"] == previous["created_at"]
    else:
        with pytest.raises(verifier.SubmissionMismatch, match="same-version"):
            verifier.catalog_snapshot(data, original, receipt)


def test_catalog_downgrade_is_a_submission_failure(verifier, catalog_update):
    data, original, receipt = catalog_update
    original["steps"][data["step_id"]]["version"] = "2.0.0"
    with pytest.raises(verifier.SubmissionMismatch, match="downgrade"):
        verifier.catalog_snapshot(data, original, receipt)


@pytest.mark.parametrize("bad_receipt", [
    {}, {"sha256": {}, "bytes": 42}, {"bytes": True},
    {"bytes": -1}, {"bytes": 50 * 1024 * 1024 + 1},
])
def test_unproven_download_evidence_blocks_catalog_snapshot(
    verifier, catalog_update, bad_receipt,
):
    data, original, receipt = catalog_update
    receipt.update(bad_receipt)
    if not bad_receipt:
        receipt = {}
    with pytest.raises(verifier.Blocked, match="download receipt"):
        verifier.catalog_snapshot(data, original, receipt)


def run_catalog_verifier(tmp_path, operation):
    return subprocess.run(
        [
            sys.executable, str(REPO_ROOT / ".github/scripts/validate_community_workflow_step.py"),
            operation, "--submission", str(tmp_path / "submission.json"),
            "--catalog", str(tmp_path / "catalog.json"),
            "--receipt", str(tmp_path / "receipt.json"),
            "--snapshot", str(tmp_path / "snapshot.json"),
        ],
        capture_output=True, text=True, check=False,
    )


@pytest.fixture
def catalog_files(catalog_update, tmp_path):
    data, original, receipt = catalog_update
    for name, value in (("submission", data), ("catalog", original), ("receipt", receipt)):
        (tmp_path / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
    return tmp_path


def test_catalog_verifier_cli_success_and_generated_repair_exit(catalog_files):
    paths = catalog_files
    result = run_catalog_verifier(paths, "snapshot")
    assert result.returncode == 0, result.stdout + result.stderr
    expected = json.loads((paths / "snapshot.json").read_text())["expected_catalog"]
    (paths / "catalog.json").write_text(json.dumps(expected))
    result = run_catalog_verifier(paths, "generated")
    assert result.returncode == 0, result.stdout + result.stderr
    (paths / "catalog.json").write_text("{not valid JSON")
    result = run_catalog_verifier(paths, "generated")
    assert result.returncode == 3
    assert result.stdout.startswith("GENERATED ERROR:")
    assert not result.stderr


def test_missing_history_digests_cli_blocks_and_discards_stale_snapshot(catalog_files):
    paths = catalog_files
    original = json.loads((paths / "catalog.json").read_text())
    entry = original["steps"]["deploy-preview"]
    del entry["releases"]["1.0.0"]["sha256"]
    (paths / "catalog.json").write_text(json.dumps(original))
    (paths / "snapshot.json").write_text('{"stale":true}')
    result = run_catalog_verifier(paths, "snapshot")
    assert result.returncode == 2
    assert result.stdout.startswith("BLOCKED:")
    assert not result.stderr
    assert not (paths / "snapshot.json").exists()


def add_package_files(submission, paths):
    entry = submission["catalog_entry"]
    base = entry["step_yml_url"].removesuffix("step.yml")
    entry["extra_files"] = {path: base + path for path in paths}
    entry["sha256"].update({path: "0" * 64 for path in paths})


@pytest.mark.parametrize("paths", [
    [f"file-{index}.bin" for index in range(511)],
    [f"nested/file-{index}.bin" for index in range(510)],
    ["/".join(["nested"] * 33 + ["file.bin"])],
])
def test_package_limit_preflight_rejects_uninstallable_metadata(
    verifier, file_submission, paths, tmp_path, monkeypatch,
):
    add_package_files(file_submission, paths)

    def unexpected_fetch(*args, **kwargs):
        pytest.fail("Oversized package metadata reached curl")

    monkeypatch.setattr(verifier.subprocess, "run", unexpected_fetch)
    with pytest.raises(verifier.SubmissionMismatch, match="limit"):
        verifier.fetch_file(file_submission, tmp_path / "download")


@pytest.mark.parametrize("paths", [
    [f"file-{index}.bin" for index in range(510)],
    [f"nested/file-{index}.bin" for index in range(509)],
    ["/".join(["nested"] * 32 + ["file.bin"])],
])
def test_package_limit_preflight_accepts_exact_installer_boundaries(
    verifier, file_submission, paths,
):
    add_package_files(file_submission, paths)
    assert verifier.validate_file(file_submission)[0] == "__init__.py"


@pytest.mark.parametrize("paths", [
    ["../escape.py"], ["nested/../escape.py"], ["/absolute.py"],
    ["nested//file.py"], ["./helper.py"], ["nested/./file.py"],
    [r"nested\file.py"], [".git/config"], ["nested/__pycache__/cached.pyc"],
    ["nested/.DS_Store"], ["STEP.YML"], ["__INIT__.PY"],
    ["helper", "helper/nested.py"],
    ["step.yml/nested.py"], ["__init__.py/nested.py"],
    ["Helper", "helper/module.py"], ["helper/module.py", "Helper"],
    ["Foo.py", "foo.py"], ["Folder/Foo.py", "folder/foo.py"],
    ["folder/Child", "FOLDER/child/module.py"],
    ["STEP.YML/module.py"], ["__INIT__.PY/module.py"],
    [".GIT/config"], ["nested/.Git/config"],
    ["__PYCACHE__/x.py"], ["nested/.ds_store"],
])
def test_package_path_guards_reject_before_fetch(
    verifier, file_submission, paths, tmp_path, monkeypatch,
):
    add_package_files(file_submission, paths)

    def unexpected_fetch(*args, **kwargs):
        pytest.fail("Invalid package path reached curl")

    monkeypatch.setattr(verifier.subprocess, "run", unexpected_fetch)
    with pytest.raises(verifier.SubmissionMismatch):
        verifier.fetch_file(file_submission, tmp_path / "download")


@pytest.mark.parametrize("paths", [
    ["Helper.py", "helper/module.py"],
    ["foo", "foobar/module.py"],
    ["Folder/a.py", "folder/b.py"],
    ["STEP.YML.py", "step.yml-data/file.bin"],
])
def test_package_paths_without_case_insensitive_collisions_are_accepted(
    verifier, file_submission, paths,
):
    add_package_files(file_submission, paths)
    assert verifier.validate_file(file_submission)[0] == "__init__.py"


@pytest.mark.parametrize(("total", "accepted"), [
    (50 * 1024 * 1024 - 1, True),
    (50 * 1024 * 1024, True),
    (50 * 1024 * 1024 + 1, False),
    (60 * 1024 * 1024, False),
])
def test_package_fetch_enforces_cumulative_bytes(
    verifier, file_submission, tmp_path, monkeypatch, total, accepted,
):
    add_package_files(file_submission, [f"file-{index}.bin" for index in range(4)])
    downloaded = []
    file_limit = 10 * 1024 * 1024
    sizes = [min(file_limit, max(0, total - index * file_limit)) for index in range(6)]

    def fetch(data, output, *, remaining_bytes=None):
        size = sizes[len(downloaded)] if len(downloaded) < len(sizes) else 0
        downloaded.append(data["file"])
        with output.open("wb") as stream:
            stream.truncate(size)
        return {"file": data["file"], "sha256": "0" * 64}

    monkeypatch.setattr(verifier, "fetch_file", fetch)
    manifest = tmp_path / "manifest"
    if accepted:
        result = verifier.fetch_package(file_submission, manifest)
        assert result["bytes"] == total
        assert len(result["sha256"]) == 6
        assert manifest.stat().st_size == sizes[0]
    else:
        with pytest.raises(verifier.SubmissionMismatch, match="cumulative"):
            verifier.fetch_package(file_submission, manifest)
        assert not manifest.exists()


def test_package_fetch_validates_all_paths_before_first_download(
    verifier, file_submission, tmp_path, monkeypatch,
):
    add_package_files(file_submission, ["../escape"])

    def unexpected_fetch(*args, **kwargs):
        pytest.fail("Invalid package was partially downloaded")

    monkeypatch.setattr(verifier, "fetch_file", unexpected_fetch)
    with pytest.raises(verifier.SubmissionMismatch):
        verifier.fetch_package(file_submission, tmp_path / "manifest")


def test_complete_package_download_returns_all_hashes_and_retains_manifest(
    verifier, file_submission, tmp_path, monkeypatch,
):
    add_package_files(file_submission, ["data/file.bin"])
    entry = file_submission["catalog_entry"]
    bodies = {
        "step.yml": b"step:\n  type_key: deploy-preview\n",
        "__init__.py": b"# Untrusted file is downloaded, never imported\n",
        "data/file.bin": b"\x00\xffbinary",
    }
    entry["sha256"] = {name: hashlib.sha256(body).hexdigest() for name, body in bodies.items()}
    fetched = []

    def curl(args, **kwargs):
        name = args[-1].split("/package/", 1)[1]
        fetched.append(name)
        Path(args[args.index("--output") + 1]).write_bytes(bodies[name])
        return subprocess.CompletedProcess(args, 0, "200", "")

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    manifest = tmp_path / "manifest"
    result = verifier.fetch_package(file_submission, manifest)
    assert fetched == list(bodies)
    assert result == {
        "sha256": entry["sha256"], "bytes": sum(map(len, bodies.values())),
    }
    assert manifest.read_bytes() == bodies["step.yml"]


def test_six_ten_mib_files_fail_cumulative_budget_before_sixth_hash(
    verifier, file_submission, tmp_path, monkeypatch,
):
    add_package_files(file_submission, [f"file-{index}.bin" for index in range(4)])
    body = b"x" * (10 * 1024 * 1024)
    digest = hashlib.sha256(body).hexdigest()
    entry = file_submission["catalog_entry"]
    entry["sha256"] = {name: digest for name in entry["sha256"]}
    requests = []
    hashed = []
    real_sha256 = hashlib.sha256

    def curl(args, **kwargs):
        requests.append(args)
        limit = int(args[args.index("--max-filesize") + 1])
        if len(body) > limit:
            return subprocess.CompletedProcess(args, 63, "200", "maximum size exceeded")
        Path(args[args.index("--output") + 1]).write_bytes(body)
        return subprocess.CompletedProcess(args, 0, "200", "")

    def sha256(payload):
        hashed.append(len(payload))
        return real_sha256(payload)

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    monkeypatch.setattr(verifier.hashlib, "sha256", sha256)
    manifest = tmp_path / "manifest"
    with pytest.raises(verifier.SubmissionMismatch, match="cumulative"):
        verifier.fetch_package(file_submission, manifest)
    assert len(requests) == 6
    assert requests[-1][requests[-1].index("--max-filesize") + 1] == "1"
    assert hashed == [len(body)] * 5
    assert not manifest.exists()


def test_failed_package_file_does_not_publish_partial_manifest(
    verifier, file_submission, tmp_path, monkeypatch,
):
    entry = file_submission["catalog_entry"]
    entry["sha256"]["step.yml"] = hashlib.sha256(b"manifest").hexdigest()
    requests = []

    def curl(args, **kwargs):
        requests.append(args)
        if len(requests) == 2:
            return subprocess.CompletedProcess(args, 0, "404", "")
        Path(args[args.index("--output") + 1]).write_bytes(b"manifest")
        return subprocess.CompletedProcess(args, 0, "200", "")

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    manifest = tmp_path / "manifest"
    manifest.write_bytes(b"stale prior manifest")
    with pytest.raises(verifier.SubmissionMismatch, match="404"):
        verifier.fetch_package(file_submission, manifest)
    assert not manifest.exists()


@pytest.mark.parametrize("empty_file", ["step.yml", "__init__.py"])
def test_empty_required_package_file_is_rejected(
    verifier, file_submission, tmp_path, monkeypatch, empty_file,
):
    entry = file_submission["catalog_entry"]
    bodies = {
        name: b"" if name == empty_file else b"required file bytes"
        for name in entry["sha256"]
    }
    entry["sha256"] = {name: hashlib.sha256(body).hexdigest() for name, body in bodies.items()}

    def curl(args, **kwargs):
        name = args[-1].split("/package/", 1)[1]
        Path(args[args.index("--output") + 1]).write_bytes(bodies[name])
        return subprocess.CompletedProcess(args, 0, "200", "")

    monkeypatch.setattr(verifier.subprocess, "run", curl)
    manifest = tmp_path / "manifest"
    with pytest.raises(verifier.SubmissionMismatch, match=f"{empty_file} must be nonempty"):
        verifier.fetch_package(file_submission, manifest)
    assert not manifest.exists()
