"""Deterministic tests for the built-in GitHub workflow step."""

from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.workflows import BUILTIN_STEP_TYPES, get_step_type
from specify_cli.workflows.base import RunStatus, StepContext, StepStatus
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.step import github


@pytest.fixture
def context(tmp_path: Path) -> StepContext:
    return StepContext(
        inputs={"issue": "12", "pr": 7},
        project_root=str(tmp_path),
        run_id="run-1",
    )


@pytest.fixture
def api(monkeypatch):
    comments: list[dict] = []
    calls: list[tuple[str, str]] = []

    def fake_api(root, endpoint, *, method="GET", data=None, paginated=False):
        calls.append((method, endpoint))
        if endpoint.endswith("/user"):
            return {"login": "maintainer"}
        if endpoint.endswith("/pulls/7"):
            return {"number": 7, "head": {"sha": "a" * 40}}
        if endpoint.endswith("/issues/12"):
            return {"number": 12}
        if endpoint.endswith("/comments?per_page=100"):
            assert paginated
            return [comments[:]]
        if endpoint.endswith("/comments") and method == "POST":
            comment = {"id": len(comments) + 1, "body": data["body"],
                       "user": {"login": "maintainer"}}
            comments.append(comment)
            return comment
        raise AssertionError(f"Unexpected API call: {method} {endpoint}")

    monkeypatch.setattr(github, "_api", fake_api)
    monkeypatch.setattr(github, "_identity", lambda root: (
        "owner/repo", "https://api.github.com/repos/owner/repo",
    ))
    return comments, calls


def config(**kwargs):
    definition = {"id": "post-plan", "type": "github", "operation": "comment",
                  "target": "issue", "number": "{{ inputs.issue }}"}
    definition.update(kwargs)
    return definition


def test_registered_builtin_and_validation():
    step = get_step_type("github")
    assert step is not None
    assert "github" in BUILTIN_STEP_TYPES
    assert step.validate(config(body="text")) == []
    assert step.validate(config(body_file="plan.md")) == []
    assert step.validate(config(body_files=["plan.md"])) == []
    assert step.validate(config(body="text", body_file="plan.md"))
    assert step.validate(config(body_files=[]))
    assert step.validate(config(body="text", number=True))
    assert step.validate(config(body="text", target="repository"))
    assert step.validate(config(body="text", unexpected="field"))
    assert step.validate(config(body="text", maintainer_action={"summary": "x"}))
    assert step.validate({"id": "fetch", "type": "github", "operation": "fetch-artifact",
                          "target": "issue", "number": 12, "write_to": "result.md"})
    assert step.validate({"id": "checkout", "type": "github", "operation": "checkout-pr",
                          "number": 0})


def test_comment_retry_is_idempotent_and_changed_content_fails(context, api):
    comments, calls = api
    step = get_step_type("github")
    definition = config(body="Plan for {{ inputs.issue }}", artifact="plan",
                        maintainer_action={"summary": "Review only",
                                           "possible_labels": ["approved"]})
    first = step.execute(definition, context)
    again = step.execute(definition, context)
    assert first.status == again.status == StepStatus.COMPLETED
    assert first.output["comment_id"] == again.output["comment_id"] == 1
    assert len(comments) == 1
    assert "Plan for 12" in comments[0]["body"]
    assert "Possible labels: approved" in comments[0]["body"]
    assert not any("/labels" in endpoint for _, endpoint in calls)
    assert len([method for method, _ in calls if method == "POST"]) == 1
    changed = step.execute(config(body="Different", artifact="plan"), context)
    assert changed.status == StepStatus.FAILED
    assert "differs" in changed.error
    assert len(comments) == 1


def test_comment_files_and_fetch_artifact(context, api):
    comments, _ = api
    root = Path(context.project_root)
    (root / "one.md").write_text("First")
    (root / "two.md").write_text("Second")
    step = get_step_type("github")
    posted = step.execute(config(body_files=["one.md", "two.md"], artifact="report"), context)
    assert posted.status == StepStatus.COMPLETED
    result = step.execute({"id": "retrieve", "type": "github", "operation": "fetch-artifact",
                           "target": "issue", "number": 12, "artifact": "report",
                           "write_to": "result.md"}, context)
    assert result.status == StepStatus.COMPLETED, result.error
    assert (root / "result.md").read_text() == "First\n\nSecond"
    assert result.output["comment_id"] == comments[0]["id"]
    again = step.execute({"id": "retrieve", "operation": "fetch-artifact",
                          "target": "issue", "number": 12, "artifact": "report",
                          "write_to": "result.md"}, context)
    assert again.status == StepStatus.FAILED
    assert (root / "result.md").read_text() == "First\n\nSecond"


def test_engine_executes_github_yaml_without_shell(context, api):
    comments, _ = api
    definition = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: github-pipeline
  name: GitHub pipeline
  version: "1.0.0"
inputs:
  issue:
    type: number
    required: true
steps:
  - id: publish
    type: github
    operation: comment
    target: issue
    number: "{{ inputs.issue }}"
    body: "Plan for {{ inputs.issue }}"
    artifact: plan
""")
    engine = WorkflowEngine(Path(context.project_root))
    assert engine.validate(definition) == []
    state = engine.execute(definition, {"issue": "12"}, run_id="pipeline1")
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["publish"]["output"]["comment_id"] == 1
    assert len(comments) == 1


def test_pull_request_comment_uses_issue_comment_endpoint(context, api):
    comments, calls = api
    definition = config(body="PR feedback", target="pull_request", number=7)
    result = get_step_type("github").execute(definition, context)
    assert result.status == StepStatus.COMPLETED, result.error
    assert get_step_type("github").execute(definition, context).status == StepStatus.COMPLETED
    assert len(comments) == 1
    assert any(url.endswith("/pulls/7") for _, url in calls)
    assert any(method == "POST" and url.endswith("/issues/7/comments")
               for method, url in calls)


@pytest.mark.parametrize("change,expected", [
    (lambda comments: comments[0].update(body=comments[0]["body"].replace("First", "Altered")), "digest"),
    (lambda comments: comments[0].update(user={"login": "someone-else"}), "not posted"),
    (lambda comments: comments.append(dict(comments[0], id=2)), "found 2"),
])
def test_fetch_rejects_untrusted_or_ambiguous(context, api, change, expected):
    comments, _ = api
    step = get_step_type("github")
    assert step.execute(config(body="First", artifact="report"), context).status == StepStatus.COMPLETED
    change(comments)
    result = step.execute({"id": "retrieve", "operation": "fetch-artifact",
                           "target": "issue", "number": 12, "artifact": "report",
                           "write_to": "result.md"}, context)
    assert result.status == StepStatus.FAILED
    assert expected in result.error
    assert not (Path(context.project_root) / "result.md").exists()


@pytest.mark.parametrize("name", ["../elsewhere", "/tmp/elsewhere", "absent/result.md", "link/result.md"])
def test_fetch_rejects_unsafe_destinations(context, api, name, tmp_path):
    root = Path(context.project_root)
    (root / "link").symlink_to(tmp_path.parent, target_is_directory=True)
    step = get_step_type("github")
    assert step.execute(config(body="text", artifact="report"), context).status == StepStatus.COMPLETED
    result = step.execute({"id": "fetch", "operation": "fetch-artifact", "target": "issue",
                           "number": 12, "artifact": "report", "write_to": name}, context)
    assert result.status == StepStatus.FAILED


def test_bad_identifiers_and_missing_artifact_fail_without_post(context, api):
    comments, calls = api
    step = get_step_type("github")
    for number in (0, "-1", True, "1; echo bad", None):
        result = step.execute(config(body="hello", number=number), context)
        assert result.status == StepStatus.FAILED
        assert "number" in result.error
    result = step.execute({"id": "fetch", "operation": "fetch-artifact", "target": "issue",
                           "number": 12, "artifact": "missing", "write_to": "result.md"}, context)
    assert result.status == StepStatus.FAILED
    assert "found 0" in result.error
    assert not comments
    assert not any(method == "POST" for method, _ in calls)


def test_comment_rejects_symlinked_source_and_fan_out(context, api, tmp_path):
    root = Path(context.project_root)
    (root / "link.md").symlink_to(tmp_path.parent / "outside.md")
    step = get_step_type("github")
    result = step.execute(config(body_file="link.md"), context)
    assert result.status == StepStatus.FAILED
    assert "Symlinked" in result.error
    context.inside_fan_out = True
    result = step.execute(config(body="hi"), context)
    assert result.status == StepStatus.FAILED
    assert "fan-out" in result.error


def test_api_error_fails_without_success_shaped_output(context, api, monkeypatch):
    monkeypatch.setattr(github, "_api", lambda *args, **kwargs: (_ for _ in ()).throw(
        ValueError("GitHub request failed (exit code 403)")))
    result = get_step_type("github").execute(config(body="hi"), context)
    assert result.status == StepStatus.FAILED
    assert "403" in result.error
    assert result.output == {}


def test_api_posts_json_on_stdin_and_slurps_comment_pages(context, monkeypatch):
    observed = []

    def fake_run(args, root, *, input_text=None):
        observed.append((args, input_text))
        return "[[]]" if "--paginate" in args else '{"id": 1}'

    monkeypatch.setattr(github, "_run", fake_run)
    root = Path(context.project_root)
    assert github._api(root, "https://api.github.com/repos/o/r/issues/1/comments",
                       method="POST", data={"body": "private body"}) == {"id": 1}
    assert observed[0][1] == '{"body": "private body"}'
    assert "private body" not in " ".join(observed[0][0])
    assert github._api(root, "https://api.github.com/repos/o/r/issues/1/comments",
                       paginated=True) == [[]]
    assert observed[1][0][-2:] == ["--paginate", "--slurp"]


def test_identity_rejects_non_github_origin(context, monkeypatch):
    assert github._ORIGIN.fullmatch("https://evil.example/owner/repo.git") is None
    assert github._ORIGIN.fullmatch("https://github.com/owner/repo.git")
    monkeypatch.setattr(github, "_run", lambda args, root, **kwargs: "https://evil.example/owner/repo.git")
    with pytest.raises(ValueError, match="github.com origin"):
        github._identity(Path(context.project_root))


def test_comment_rejects_wrong_target(context, api, monkeypatch):
    step = get_step_type("github")
    original_api = github._api

    def wrong_target(root, endpoint, **kwargs):
        if endpoint.endswith("/issues/12"):
            return {"number": 12, "pull_request": {}}
        return original_api(root, endpoint, **kwargs)

    monkeypatch.setattr(github, "_api", wrong_target)
    bad = step.execute(config(body="hi"), context)
    assert bad.status == StepStatus.FAILED
    assert "does not match" in bad.error


def test_checkout_verifies_head_before_checkout(context, api, monkeypatch):
    commands = []
    sha = "a" * 40

    def fake_run(args, root, *, input_text=None):
        commands.append(args)
        if args[:2] == ["git", "rev-parse"]:
            return sha
        return ""

    monkeypatch.setattr(github, "_run", fake_run)
    step = get_step_type("github")
    definition = {"id": "checkout", "type": "github", "operation": "checkout-pr",
                  "number": "{{ inputs.pr }}"}
    result = step.execute(definition, context)
    assert result.status == StepStatus.COMPLETED
    assert result.output["head_sha"] == sha
    assert ["git", "fetch", "origin", "pull/7/head"] in commands
    assert ["git", "-c", "advice.detachedHead=false", "checkout", "--detach", sha] in commands
    assert commands[-1] == ["git", "rev-parse", "HEAD"]
    commands.clear()
    monkeypatch.setattr(github, "_run", lambda args, root, **kwargs: "b" * 40)
    failed = step.execute(definition, context)
    assert failed.status == StepStatus.FAILED
    assert "differs" in failed.error
