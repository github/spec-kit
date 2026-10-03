"""Check community-submission reporting independently of agent reasoning."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
SHARED = WORKFLOWS / "shared" / "catalog-submission.md"
TYPES = ("extension", "preset", "bundle")


def _frontmatter(path):
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def _reporting_job():
    return _frontmatter(SHARED)["jobs"]["submission_outcome"]


@pytest.mark.parametrize("kind", TYPES)
def test_submission_reporting_is_wired_into_compiled_workflow(kind):
    source = _frontmatter(WORKFLOWS / f"add-community-{kind}.md")
    compiled = yaml.safe_load(
        (WORKFLOWS / f"add-community-{kind}.lock.yml").read_text(encoding="utf-8")
    )
    assert "shared/catalog-submission.md" in source["imports"]
    job = compiled["jobs"]["submission_outcome"]
    assert set(job["needs"]) == {"activation", "agent", "safe_outputs"}
    assert job["if"] == _reporting_job()["if"]
    assert job["permissions"] == {"issues": "write"}
    report_step = next(
        step for step in job["steps"] if step["name"] == "Report missing submission outcome"
    )
    assert report_step == _reporting_job()["steps"][0]
    assert "{{#runtime-import .github/workflows/shared/catalog-submission.md}}" in (
        WORKFLOWS / f"add-community-{kind}.lock.yml"
    ).read_text(encoding="utf-8")
    assert compiled["jobs"]["agent"]["permissions"]["issues"] == "read"
    assert compiled["jobs"]["safe_outputs"]["outputs"]["created_pr_number"] == (
        "${{ steps.process_safe_outputs.outputs.created_pr_number }}"
    )
    assert compiled["jobs"]["safe_outputs"]["outputs"]["comment_id"] == (
        "${{ steps.process_safe_outputs.outputs.comment_id }}"
    )
    for counter in ("failed", "deferred", "cancelled"):
        assert compiled["jobs"]["safe_outputs"]["outputs"][f"process_safe_outputs_items_{counter}"] == (
            "${{ steps.process_safe_outputs.outputs.items_" + counter + " }}"
        )
    text = (WORKFLOWS / f"add-community-{kind}.md").read_text(encoding="utf-8")
    assert "If it does not, stop without commenting" not in text
    assert f"names: [{kind}-submission]" in text


def _run_report(comments=(), pr_number="", safe_result="success",
                agent_result="success", activation_result="success", fail_api="",
                comment_id="", failed="0", deferred="0", cancelled="0"):
    step = _reporting_job()["steps"][0]
    harness = r"""
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const calls = [];
const context = {
  repo: {owner: 'owner', repo: 'repo'}, serverUrl: 'https://github.com',
  payload: {issue: {number: 42}}
};
const record = (api, args) => {
  calls.push({api, args});
  if (api === input.fail_api) throw new Error(`API failure: ${api}`);
};
const github = {
  rest: {issues: {
    listComments: 'listComments',
    createComment: async args => { record('createComment', args); }
  }},
  paginate: async (api, args) => { record(api, args); return input.comments; }
};
process.env.SUBMISSION_RUN_URL = 'https://github.com/owner/repo/actions/runs/123/attempts/2';
process.env.SUBMISSION_PR_NUMBER = input.pr_number;
process.env.SUBMISSION_SAFE_OUTPUTS_RESULT = input.safe_result;
process.env.SUBMISSION_AGENT_RESULT = input.agent_result;
process.env.SUBMISSION_COMMENT_ID = input.comment_id;
process.env.SUBMISSION_ITEMS_FAILED = input.failed;
process.env.SUBMISSION_ITEMS_DEFERRED = input.deferred;
process.env.SUBMISSION_ITEMS_CANCELLED = input.cancelled;
const always = () => true;
const needs = {activation: {result: input.activation_result}};
(async () => {
  let error = null;
  try {
    const shouldRun = new Function('always', 'needs', `return ${input.condition}`)(always, needs);
    if (shouldRun) {
      const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
      await new AsyncFunction('github', 'context', input.script)(github, context);
    }
  } catch (e) { error = e.message; }
  console.log(JSON.stringify({calls, error}));
})();
"""
    result = subprocess.run(
        ["node", "-e", harness],
        input=json.dumps({
            "script": step["with"]["script"], "condition": _reporting_job()["if"],
            "comments": comments, "pr_number": pr_number,
            "safe_result": safe_result, "agent_result": agent_result,
            "activation_result": activation_result, "fail_api": fail_api,
            "comment_id": comment_id,
            "failed": failed, "deferred": deferred, "cancelled": cancelled,
        }),
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


requires_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not available")


@requires_node
@pytest.mark.parametrize(("agent", "safe", "pr"), [
    ("success", "success", ""), ("failure", "skipped", ""),
    ("cancelled", "cancelled", ""), ("success", "failure", "37"),
    ("skipped", "skipped", ""),
])
def test_silent_runs_report_blocked_without_claiming_submission_failed(agent, safe, pr):
    result = _run_report(agent_result=agent, safe_result=safe, pr_number=pr)
    assert result["error"] is None
    comment = result["calls"][-1]["args"]
    assert comment["issue_number"] == 42
    assert "**Outcome: Blocked.**" in comment["body"]
    assert "not a confirmed submission defect" in comment["body"]
    assert "maintainer" in comment["body"]
    assert "[Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)" in comment["body"]
    assert "/pull/" not in comment["body"]


@requires_node
def test_published_pr_reports_actual_link():
    result = _run_report(pr_number="37")
    assert result["error"] is None
    body = result["calls"][-1]["args"]["body"]
    assert "**Outcome: PR created.**" in body
    assert "https://github.com/owner/repo/pull/37" in body


@requires_node
@pytest.mark.parametrize("agent_result", ["failure", "cancelled"])
def test_published_pr_does_not_hide_incomplete_agent_processing(agent_result):
    result = _run_report(agent_result=agent_result, pr_number="37")
    assert result["error"] is None
    body = result["calls"][-1]["args"]["body"]
    assert body.startswith("**Outcome: Blocked.**")
    assert "Workflow processing did not complete" in body
    assert "https://github.com/owner/repo/pull/37" in body
    assert "**Outcome: PR created.**" not in body
    assert "maintainer" in body


@requires_node
def test_existing_run_outcome_prevents_duplicate_comment():
    result = _run_report(comments=[{
        "user": {"type": "Bot"},
        "body": "**Outcome: Wrong submission type.** [Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)",
    }])
    assert result["error"] is None
    assert [call["api"] for call in result["calls"]] == ["listComments"]


@requires_node
def test_pat_authored_safe_output_prevents_duplicate_comment():
    result = _run_report(comment_id="17", comments=[{
        "id": 17, "user": {"type": "User"},
        "body": "**Outcome: Failed.** [Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)",
    }])
    assert result["error"] is None
    assert [call["api"] for call in result["calls"]] == ["listComments"]


@requires_node
@pytest.mark.parametrize(("agent", "safe"), [
    ("success", "failure"), ("failure", "success"), ("success", "cancelled"),
])
def test_incomplete_processing_is_reported_even_after_agent_comment(agent, safe):
    result = _run_report(agent_result=agent, safe_result=safe, comments=[{
        "user": {"type": "Bot"},
        "body": "**Outcome: PR requested.** [Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)",
    }])
    assert result["error"] is None
    assert result["calls"][-1]["api"] == "createComment"
    assert "**Outcome: Blocked.**" in result["calls"][-1]["args"]["body"]
    assert "No submission outcome was reported" not in result["calls"][-1]["args"]["body"]


@requires_node
@pytest.mark.parametrize("counter", ["failed", "deferred", "cancelled"])
@pytest.mark.parametrize("value", ["1", ""])
@pytest.mark.parametrize("pr_number", ["", "37"])
def test_successful_job_does_not_hide_incomplete_output_items(counter, value, pr_number):
    result = _run_report(pr_number=pr_number, **{counter: value}, comments=[{
        "user": {"type": "Bot"},
        "body": "**Outcome: PR requested.** [Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)",
    }])
    assert result["error"] is None
    assert result["calls"][-1]["api"] == "createComment"
    body = result["calls"][-1]["args"]["body"]
    assert body.startswith("**Outcome: Blocked.**")
    assert "Workflow processing did not complete" in body
    assert "**Outcome: PR created.**" not in body
    if pr_number:
        assert "https://github.com/owner/repo/pull/37" in body


@requires_node
@pytest.mark.parametrize("comment", [
    {"user": {"type": "User"}, "body": "https://github.com/owner/repo/actions/runs/123"},
    {"user": {"type": "Bot"}, "body": "https://github.com/owner/repo/actions/runs/122"},
    {"user": {"type": "Bot"}, "body": "[Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/1)"},
    {"user": {"type": "Bot"}, "body": "[Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/20)"},
    {"user": {"type": "Bot"}, "body": None},
    {"user": {"type": "Bot"}, "body": "Logs: [Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)"},
    {"id": 18, "user": {"type": "User"}, "body": "**Outcome: Failed.** [Workflow run](https://github.com/owner/repo/actions/runs/123/attempts/2)"},
])
def test_unrelated_comments_do_not_hide_missing_outcome(comment):
    result = _run_report(comments=[comment])
    assert result["error"] is None
    assert result["calls"][-1]["api"] == "createComment"


@requires_node
@pytest.mark.parametrize("activation_result", ["failure", "skipped", "cancelled"])
def test_unactivated_workflows_do_not_comment(activation_result):
    assert _run_report(activation_result=activation_result) == {"calls": [], "error": None}


@requires_node
@pytest.mark.parametrize("fail_api", ["listComments", "createComment"])
def test_reporting_api_failures_are_not_silenced(fail_api):
    result = _run_report(fail_api=fail_api)
    assert result["error"] == f"API failure: {fail_api}"
