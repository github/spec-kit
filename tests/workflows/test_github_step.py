"""Tests for the opt-in-by-use built-in GitHub label step (no live API calls)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli.workflows import BUILTIN_STEP_TYPES, get_step_type
from specify_cli.workflows.base import RunStatus, StepContext, StepStatus
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.step import github


@pytest.fixture
def context(tmp_path: Path) -> StepContext:
    return StepContext(
        inputs={"number": 12}, project_root=str(tmp_path), run_id="run-1"
    )


@pytest.fixture
def api(monkeypatch):
    stored: list[str] = []
    calls: list[tuple[str, str, list[str] | None]] = []

    def fake_api(root, endpoint, *, labels: list[str] | None = None):
        calls.append(("POST" if labels is not None else "GET", endpoint, labels))
        if endpoint.endswith("/issues/12"):
            return {"number": 12, "labels": [{"name": name} for name in stored]}
        if endpoint.endswith("/pulls/12"):
            return {"number": 12, "labels": [{"name": name} for name in stored]}
        if endpoint.endswith("/issues/12/labels") and labels is not None:
            for name in labels:
                if name.casefold() not in {existing.casefold() for existing in stored}:
                    stored.append(name)
            return [{"name": name} for name in stored]
        raise AssertionError(f"Unexpected API call: {endpoint}")

    monkeypatch.setattr(github, "_api", fake_api)
    monkeypatch.setattr(
        github,
        "_identity",
        lambda root: ("owner/repo", "https://api.github.com/repos/owner/repo"),
    )
    return stored, calls


def config(**overrides):
    definition = {
        "id": "label",
        "type": "github",
        "operation": "add-label",
        "target": "issue",
        "number": "{{ inputs.number }}",
        "label": "ready-for-review",
    }
    definition.update(overrides)
    return definition


def test_builtin_registered_and_accepts_only_add_label():
    step = get_step_type("github")
    assert step is not None
    assert "github" in BUILTIN_STEP_TYPES
    assert step.validate(config()) == []
    assert step.validate(config(target="pull_request")) == []
    for operation in ("comment", "fetch-artifact", "checkout-pr", "remove-label", None):
        assert step.validate(config(operation=operation))
    assert step.validate(config(body="Not supported"))


def test_issue_label_added_once_and_retry_skips_write(context, api):
    labels, calls = api
    step = get_step_type("github")
    first = step.execute(config(), context)
    retry = step.execute(config(), context)
    assert first.status == retry.status == StepStatus.COMPLETED
    assert first.output == {
        "repository": "owner/repo",
        "target": "issue",
        "number": 12,
        "label": "ready-for-review",
        "added": True,
    }
    assert retry.output == {**first.output, "added": False}
    assert labels == ["ready-for-review"]
    assert len([method for method, _, _ in calls if method == "POST"]) == 1


def test_pull_request_uses_issue_labels_endpoint(context, api):
    labels, calls = api
    result = get_step_type("github").execute(config(target="pull_request"), context)
    assert result.status == StepStatus.COMPLETED
    assert result.output["target"] == "pull_request"
    assert labels == ["ready-for-review"]
    assert calls[0][1].endswith("/pulls/12")
    assert calls[1][1].endswith("/issues/12/labels")


def test_existing_label_is_case_insensitive_and_skips_post(context, api):
    labels, calls = api
    labels.append("Ready-For-Review")
    result = get_step_type("github").execute(config(), context)
    assert result.status == StepStatus.COMPLETED
    assert result.output["added"] is False
    assert len(calls) == 1


@pytest.mark.parametrize("number", [0, -1, True, None, "1; echo bad", ""])
def test_invalid_number_fails_before_any_api_call(context, api, number):
    _, calls = api
    result = get_step_type("github").execute(config(number=number), context)
    assert result.status == StepStatus.FAILED
    assert "number" in result.error
    assert calls == []


@pytest.mark.parametrize(
    "label", [None, "", " ", "bad\nlabel", "bad\x7flabel", "a" * 51, ["ready"]]
)
def test_invalid_label_fails_before_any_api_call(context, api, label):
    _, calls = api
    result = get_step_type("github").execute(config(label=label), context)
    assert result.status == StepStatus.FAILED
    assert "label" in result.error
    assert calls == []


def test_missing_fields_and_unsupported_operations_fail(context, api):
    _, calls = api
    step = get_step_type("github")
    for broken in (
        config(target="repository"),
        config(operation="comment"),
        {key: value for key, value in config().items() if key != "label"},
        {key: value for key, value in config().items() if key != "number"},
        config(body="unexpected"),
    ):
        assert step.validate(broken)
        assert step.execute(broken, context).status == StepStatus.FAILED
    assert calls == []


def test_wrong_issue_target_and_malformed_labels_fail(context, api, monkeypatch):
    original_api = github._api
    step = get_step_type("github")

    def wrong_target(root, endpoint, **kwargs):
        if endpoint.endswith("/issues/12"):
            return {"number": 12, "pull_request": {}, "labels": []}
        return original_api(root, endpoint, **kwargs)

    monkeypatch.setattr(github, "_api", wrong_target)
    result = step.execute(config(), context)
    assert result.status == StepStatus.FAILED
    assert "does not match" in result.error

    monkeypatch.setattr(
        github,
        "_api",
        lambda root, endpoint, **kwargs: {"number": 12, "labels": "invalid"},
    )
    result = step.execute(config(), context)
    assert result.status == StepStatus.FAILED
    assert "invalid label list" in result.error


def test_api_failure_or_missing_posted_label_is_not_success(context, api, monkeypatch):
    step = get_step_type("github")
    original_api = github._api

    def no_label(root, endpoint, **kwargs):
        if kwargs.get("labels") is not None:
            return []
        return original_api(root, endpoint, **kwargs)

    monkeypatch.setattr(github, "_api", no_label)
    result = step.execute(config(), context)
    assert result.status == StepStatus.FAILED
    assert "did not apply label" in result.error
    monkeypatch.setattr(
        github,
        "_api",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("GitHub API failed")),
    )
    result = step.execute(config(), context)
    assert result.status == StepStatus.FAILED
    assert "GitHub API failed" in result.error
    assert result.output == {}


def test_api_post_uses_json_stdin_and_does_not_put_label_in_arguments(
    context, monkeypatch
):
    observed = []

    def fake_run(args, root, *, input_text=None):
        observed.append((args, input_text))
        return '[{"name":"ready"}]'

    monkeypatch.setattr(github, "_run", fake_run)
    github._api(
        Path(context.project_root),
        "https://api.github.com/repos/o/r/issues/12/labels",
        labels=["ready"],
    )
    assert json.loads(observed[0][1]) == {"labels": ["ready"]}
    assert "ready" not in observed[0][0]


def test_origin_must_be_github_dot_com(context, monkeypatch):
    monkeypatch.setattr(
        github, "_run", lambda args, root, **kwargs: "https://evil.example/o/r.git"
    )
    with pytest.raises(ValueError, match="github.com origin"):
        github._identity(Path(context.project_root))


def test_engine_executes_label_yaml_and_fan_out_with_retries(context, api):
    labels, calls = api
    workflow = WorkflowDefinition.from_string("""
schema_version: "1.0"
workflow:
  id: label-items
  name: Label items
  version: "1.0.0"
steps:
  - id: labels
    type: fan-out
    items: "{{ ['ready', 'needs-review'] }}"
    max_concurrency: 2
    step:
      id: add-label
      type: github
      operation: add-label
      target: issue
      number: 12
      label: "{{ item }}"
""")
    engine = WorkflowEngine(Path(context.project_root))
    assert engine.validate(workflow) == []
    assert engine.execute(workflow, run_id="labels-run").status == RunStatus.COMPLETED
    assert set(labels) == {"ready", "needs-review"}
    assert engine.execute(workflow, run_id="labels-run").status == RunStatus.COMPLETED
    assert len([method for method, _, _ in calls if method == "POST"]) == 2
