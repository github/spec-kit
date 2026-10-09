"""Execute the pinned handler with mocked GitHub I/O, not an LLM policy simulation.

fixtures/gh_aw/replace_label.cjs is an unmodified copy of setup/js/replace_label.cjs
from github/gh-aw-actions at 924af5fdc64061cfbf66fb584c8b07e2ac230c60.
The companion LICENSE preserves that revision's MIT license and copyright notice.
Digest checks enforce exact provenance; normal pytest runs these probes offline.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_github_workflows import _agentic_workflow, _safe_output_config

HANDLER_SHA256 = "ee395db6f6234240b3f2266567b71ade84c85320e3c89fe40f67ef2f189fe249"
LICENSE_SHA256 = "2510b446bc1f0cf9702453075d20cd88631e20e5642658edb7325d9c1eb534f7"
ACTION_REVISION = "924af5fdc64061cfbf66fb584c8b07e2ac230c60"
HANDLER_PROBE = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const input = JSON.parse(fs.readFileSync(0, "utf8"));
let labels = [...input.labels];
const writes = [];
const reads = [];
const github = {rest: {issues: {
  get: async params => {
    reads.push(params);
    return {data: {labels: labels.map(name => ({name}))}};
  },
  setLabels: async params => {
    writes.push(params);
    if (input.rejectWrite) throw Object.assign(new Error("Write rejected"), {status: 403});
    labels = [...params.labels];
    return {data: labels.map(name => ({name}))};
  },
}}};
// Isolate the real replacement logic; retry, authentication, repository resolution,
// execution metadata and count-gating infrastructure are outside this probe.
const modules = {
  "./glob_pattern_helpers.cjs": {matchesSimpleGlob: (name, pattern) => name === pattern},
  "./error_helpers.cjs": {getErrorMessage: error => error.message},
  "./repo_helpers.cjs": {
    resolveTargetRepoConfig: () => ({defaultTargetRepo: "KSchlobohm/spec-kit", allowedRepos: new Set()}),
    resolveAndValidateRepo: () => ({
      success: true, repo: "KSchlobohm/spec-kit",
      repoParts: {owner: "KSchlobohm", repo: "spec-kit"},
    }),
  },
  "./staged_preview.cjs": {logStagedPreviewInfo: () => {}},
  "./handler_auth.cjs": {createAuthenticatedGitHubClient: async () => github},
  "./temporary_id.cjs": {resolveSafeOutputIssueTarget: () => {throw new Error("Unexpected wildcard target");}},
  "./safe_output_execution_metadata.cjs": {
    attachExecutionState: result => result,
    fetchIssueState: async (client, repo, number) =>
      (await client.rest.issues.get({...repo, issue_number: number})).data,
    normalizeLabelNames: labels => labels.map(label => typeof label === "string" ? label : label.name),
  },
  "./handler_scaffold.cjs": {createCountGatedHandler: options => options.setup},
  "./error_recovery.cjs": {withRetry: async operation => operation(), RATE_LIMIT_RETRY_CONFIG: {}},
  "./invocation_context_helpers.cjs": {
    resolveInvocationContext: context => ({eventPayload: context.payload}),
  },
};
const sandbox = {
  module: {exports: {}},
  require: name => {
    if (!(name in modules)) throw new Error(`Unexpected dependency: ${name}`);
    return modules[name];
  },
  core: {info: () => {}, warning: () => {}, error: () => {}},
  context: {payload: {pull_request: {number: 37}}},
};
vm.runInNewContext(fs.readFileSync(process.argv[1], "utf8"), sandbox);
(async () => {
  const handle = await sandbox.module.exports.main(input.config, 1, false);
  const result = await handle(input.message, {});
  process.stdout.write(JSON.stringify({result, labels, reads, writes}));
})().catch(error => {console.error(error); process.exitCode = 1;});
"""


@pytest.fixture
def pinned_handler() -> Path:
    path = Path(__file__).parent / "fixtures" / "gh_aw" / "replace_label.cjs"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == HANDLER_SHA256
    assert hashlib.sha256(path.with_name("LICENSE").read_bytes()).hexdigest() == LICENSE_SHA256
    assert shutil.which("node"), "Node.js is required for the pinned-handler probe"
    return path


@pytest.mark.parametrize(
    ("labels", "remove", "add", "reject_write", "success", "expected", "write_count"),
    [
        (["pr-assess", "unrelated"], "pr-description-aligned",
         "pr-description-needs-update", False, True,
         ["pr-assess", "unrelated", "pr-description-needs-update"], 1),
        (["pr-assess", "unrelated", "pr-description-aligned"], "pr-description-aligned",
         "pr-description-needs-update", False, True,
         ["pr-assess", "unrelated", "pr-description-needs-update"], 1),
        (["pr-assess", "pr-description-aligned"], "pr-description-aligned",
         "pr-description-needs-update", True, False,
         ["pr-assess", "pr-description-aligned"], 1),
        (["pr-assess", "pr-description-aligned"], "pr-assess",
         "pr-description-needs-update", False, False,
         ["pr-assess", "pr-description-aligned"], 0),
        (["pr-assess", "pr-description-aligned"], "pr-description-aligned",
         "unrelated", False, False, ["pr-assess", "pr-description-aligned"], 0),
        (["pr-assess", "pr-description-aligned"], "",
         "pr-description-needs-update", False, False,
         ["pr-assess", "pr-description-aligned"], 0),
    ],
    ids=["absent-remove-label", "changed-verdict", "rejected-replacement",
         "trigger-removal-blocked", "unrelated-add-blocked", "empty-remove-blocked"],
)
def test_pinned_pr_assess_replacement(
    pinned_handler, labels, remove, add, reject_write, success, expected, write_count
):
    _, compiled_text, _, compiled = _agentic_workflow("pr-assess")
    assert f"github/gh-aw-actions/setup@{ACTION_REVISION}" in compiled_text
    config = _safe_output_config(compiled)["replace_label"]
    probe = subprocess.run(
        ["node", "-e", HANDLER_PROBE, str(pinned_handler)],
        input=json.dumps({
            "config": config,
            "labels": labels,
            "message": {"label_to_remove": remove, "label_to_add": add, "item_number": 999},
            "rejectWrite": reject_write,
        }),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    output = json.loads(probe.stdout)
    assert output["result"]["success"] is success
    assert output["labels"] == expected
    assert len(output["writes"]) == write_count
    for request in output["reads"] + output["writes"]:
        assert request["issue_number"] == 37
        assert request["owner"] == "KSchlobohm"
        assert request["repo"] == "spec-kit"
    if not success:
        assert output["result"]["error"]
    if reject_write:
        assert output["result"]["error"] == "Write rejected"
