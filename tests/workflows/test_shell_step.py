"""Regression tests for shell step execution and output decoding."""

from __future__ import annotations

import locale
import sys
from pathlib import Path

import pytest
import yaml

from specify_cli.workflows.base import RunStatus, StepContext, StepStatus
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.step.shell import ShellStep


@pytest.fixture
def utf8_locale(monkeypatch):
    """Use the same subprocess text encoding on Unix and Windows."""
    monkeypatch.setattr(locale, "getencoding", lambda: "utf-8")


def _python_run(project_dir: Path, body: str) -> str:
    script = project_dir / "emit.py"
    script.write_text(body, encoding="utf-8")
    return f'"{sys.executable}" "{script}"'


@pytest.mark.parametrize("run", [
    "echo {{ inputs.value }}",
    'echo "{{ steps.source.output.stdout }}"',
    "echo '{{ item }}'",
    "{{ inputs.command }}",
    "echo {{",
])
def test_strict_rejects_run_expressions_before_execution(monkeypatch, run):
    def unexpected_run(*args, **kwargs):
        pytest.fail("A strict run expression must never reach the shell")

    monkeypatch.setattr("subprocess.run", unexpected_run)
    config = {"id": "strict", "run": run, "strict": True}
    step = ShellStep()

    assert any("strict" in error and "'run'" in error for error in step.validate(config))
    result = step.execute(config, StepContext(inputs={"value": "$(echo injected)"}))
    assert result.status == StepStatus.FAILED
    assert "strict" in result.error
    assert result.output["exit_code"] == -1


@pytest.mark.parametrize("options, message", [
    ({"strict": "true"}, "'strict' must be a boolean"),
    ({"strict": 1}, "'strict' must be a boolean"),
    ({"strict": None}, "'strict' must be a boolean"),
    ({"env": None}, "'env' must be a mapping"),
    ({"env": []}, "'env' must be a mapping"),
    ({"env": "NAME=value"}, "'env' must be a mapping"),
    ({"env": {"": "value"}}, "environment variable name"),
    ({"env": {"BAD=NAME": "value"}}, "environment variable name"),
    ({"env": {"BAD-NAME": "value"}}, "environment variable name"),
    ({"env": {1: "value"}}, "environment variable name"),
    ({"env": {"SPECKIT_WORKFLOW_DIR": "value"}}, "reserved"),
    ({"env": {"speckit_workflow_dir": "value"}}, "reserved"),
    ({"env": {"VALUE": None}}, "must be a string"),
    ({"env": {"VALUE": 1}}, "must be a string"),
    ({"env": {"VALUE": False}}, "must be a string"),
    ({"env": {"VALUE": []}}, "must be a string"),
    ({"env": {"VALUE": "nul\x00value"}}, "NUL"),
])
def test_invalid_shell_bindings_fail_validation_and_execution(monkeypatch, options, message):
    def unexpected_run(*args, **kwargs):
        pytest.fail("Invalid configuration must never reach the shell")

    monkeypatch.setattr("subprocess.run", unexpected_run)
    config = {"id": "invalid", "run": "echo hello", **options}
    step = ShellStep()

    assert any(message in error for error in step.validate(config))
    result = step.execute(config, StepContext())
    assert result.status == StepStatus.FAILED
    assert message in result.error


@pytest.mark.parametrize("value", [None, 42, False, [], {}, "nul\x00value"])
def test_invalid_resolved_environment_fails_before_execution(monkeypatch, value):
    def unexpected_run(*args, **kwargs):
        pytest.fail("Invalid environment values must never reach the shell")

    monkeypatch.setattr("subprocess.run", unexpected_run)
    config = {
        "id": "invalid-env", "strict": True, "run": "echo hello",
        "env": {"VALUE": "{{ inputs.value }}"},
    }
    result = ShellStep().execute(config, StepContext(inputs={"value": value}))
    assert result.status == StepStatus.FAILED
    assert "VALUE" in result.error
    assert "string" in result.error or "NUL" in result.error


def test_environment_expression_error_fails_before_execution(monkeypatch):
    def unexpected_run(*args, **kwargs):
        pytest.fail("An invalid environment expression must never reach the shell")

    monkeypatch.setattr("subprocess.run", unexpected_run)
    result = ShellStep().execute({
        "id": "invalid-expression", "run": "echo hello",
        "env": {"VALUE": "{{ inputs.value | upper }}"},
    }, StepContext(inputs={"value": []}))
    assert result.status == StepStatus.FAILED
    assert "VALUE" in result.error
    assert "upper" in result.error


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize("expression", [
    "{{ inputs.value }}",
    "{{ steps.source.output.stdout }}",
    "{{ item }}",
])
def test_environment_preserves_dynamic_values_as_data(
    project_dir, monkeypatch, strict, expression,
):
    import json
    import os

    payload = """'"; echo injected; $(echo substituted) `echo substituted` | & %PATH%
{{ inputs.other }}"""
    monkeypatch.setenv("SHELL_INHERITED", "inherited")
    monkeypatch.setenv("VALUE", "old")
    monkeypatch.delenv("STATIC", raising=False)
    run = _python_run(project_dir, (
        "import json, os\n"
        "print(json.dumps({key: os.environ[key] for key in "
        "['VALUE', 'STATIC', 'SHELL_INHERITED', 'SPECKIT_WORKFLOW_DIR']}))\n"
    ))
    config = {
        "id": "data", "run": run, "strict": strict,
        "env": {"VALUE": expression, "STATIC": ""},
        "output_format": "json",
    }
    context = StepContext(
        project_root=str(project_dir),
        workflow_dir=str(project_dir / "workflow source"),
        inputs={"value": payload},
        steps={"source": {"output": {"stdout": payload}}},
        item=payload,
    )
    assert ShellStep().validate(config) == []
    result = ShellStep().execute(config, context)

    assert result.status == StepStatus.COMPLETED
    assert json.loads(result.output["stdout"]) == {
        "VALUE": payload, "STATIC": "", "SHELL_INHERITED": "inherited",
        "SPECKIT_WORKFLOW_DIR": context.workflow_dir,
    }
    assert os.environ["VALUE"] == "old"
    assert "STATIC" not in os.environ


@pytest.mark.parametrize("strict_options", [{}, {"strict": False}])
def test_legacy_run_interpolation_is_preserved(project_dir, strict_options):
    config = {
        "id": "legacy", "run": "echo {{ inputs.value }}", **strict_options,
    }
    assert ShellStep().validate(config) == []
    result = ShellStep().execute(
        config, StepContext(project_root=str(project_dir), inputs={"value": "hello"}),
    )
    assert result.status == StepStatus.COMPLETED
    assert result.output["stdout"].strip() == "hello"


def test_strict_fixed_shell_retains_pipes_and_redirection(project_dir):
    copy_stdin = _python_run(
        project_dir, "import sys\nsys.stdout.write(sys.stdin.read())\n",
    )
    config = {
        "id": "pipeline", "strict": True,
        "run": f"echo hello | {copy_stdin} > result.txt && echo done",
    }
    result = ShellStep().execute(config, StepContext(project_root=str(project_dir)))
    assert result.status == StepStatus.COMPLETED
    assert result.output["stdout"].strip() == "done"
    assert (project_dir / "result.txt").read_text().strip() == "hello"


def test_windows_environment_override_is_case_insensitive(monkeypatch):
    import subprocess
    from types import SimpleNamespace

    import specify_cli.workflows.step.shell as shell_module

    parent_env = {"PATH": "inherited", "SPECKIT_WORKFLOW_DIR": "stale"}
    monkeypatch.setattr(shell_module, "os", SimpleNamespace(name="nt", environ=parent_env))

    def capture_run(command, **kwargs):
        assert kwargs["env"] == {"PATH": "configured"}
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr("subprocess.run", capture_run)
    result = ShellStep().execute({
        "id": "windows-env", "strict": True, "run": "echo hello",
        "env": {"Path": "configured"},
    }, StepContext())
    assert result.status == StepStatus.COMPLETED
    assert parent_env == {"PATH": "inherited", "SPECKIT_WORKFLOW_DIR": "stale"}


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell variable syntax")
def test_strict_quoted_environment_expansion_does_not_execute_data(project_dir):
    payload = """'"; echo injected; $(echo substituted) `echo substituted`
second line"""
    result = ShellStep().execute({
        "id": "literal", "strict": True,
        "run": """printf '%s' "$VALUE" """,
        "env": {"VALUE": "{{ inputs.value }}"},
    }, StepContext(project_root=str(project_dir), inputs={"value": payload}))
    assert result.status == StepStatus.COMPLETED
    assert result.output["stdout"] == payload


@pytest.mark.parametrize("continue_on_error", [False, True])
def test_strict_failure_stops_or_continues_workflow(project_dir, continue_on_error):
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "strict-failure", "name": "Strict Failure", "version": "1.0.0"},
        "steps": [
            {
                "id": "blocked", "type": "shell", "strict": True,
                "run": "echo {{ inputs.value }}",
                "continue_on_error": continue_on_error,
            },
            {"id": "after", "type": "shell", "strict": True, "run": "echo after"},
        ],
    }))
    engine = WorkflowEngine(project_dir)
    assert any("strict mode" in error for error in engine.validate(definition))
    state = engine.execute(definition)
    assert state.step_results["blocked"]["status"] == "failed"
    assert "strict mode" in state.step_results["blocked"]["error"]
    if continue_on_error:
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["after"]["status"] == "completed"
    else:
        assert state.status == RunStatus.FAILED
        assert "after" not in state.step_results


def test_engine_binds_prior_output_to_strict_shell_environment(project_dir):
    run = _python_run(project_dir, "import os\nprint(os.environ['VALUE'])\n")
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "strict-env", "name": "Strict Env", "version": "1.0.0"},
        "steps": [
            {"id": "source", "type": "shell", "strict": True, "run": "echo source-data"},
            {
                "id": "consumer", "type": "shell", "strict": True, "run": run,
                "env": {"VALUE": "{{ steps.source.output.stdout }}"},
            },
        ],
    }))
    engine = WorkflowEngine(project_dir)
    assert engine.validate(definition) == []
    state = engine.execute(definition)
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["consumer"]["output"]["stdout"] == "source-data\n\n"


@pytest.mark.parametrize("stream", [1, 2, "both"], ids=["stdout", "stderr", "both"])
@pytest.mark.parametrize("exit_code", [0, 3], ids=["zero-exit", "nonzero-exit"])
@pytest.mark.parametrize("output_format", [None, "json"], ids=["text", "json"])
def test_undecodable_output_fails_step(project_dir, utf8_locale, stream, exit_code, output_format):
    stdout = b'{"message": "\xff"}' if stream in (1, "both") else b'{"message": "ok"}'
    stderr = b"\xff" if stream in (2, "both") else b"diagnostic\r\n"
    run = _python_run(
        project_dir,
        f"import os\nos.write(1, {stdout!r})\nos.write(2, {stderr!r})\n"
        f"raise SystemExit({exit_code})\n",
    )
    config = {"id": "invalid-output", "type": "shell", "run": run}
    if output_format is not None:
        config["output_format"] = output_format

    result = ShellStep().execute(config, StepContext(project_root=str(project_dir)))

    assert result.status == StepStatus.FAILED
    assert "could not be decoded" in result.error
    assert "utf-8" in result.error
    assert result.output["exit_code"] == exit_code
    assert result.output["stdout"] == ("" if stream in (1, "both") else '{"message": "ok"}')
    assert result.output["stderr"] == ("" if stream in (2, "both") else "diagnostic\n")
    for name, number in (("stdout", 1), ("stderr", 2)):
        if stream in (number, "both"):
            assert f"{name} could not be decoded" in result.error
    assert "data" not in result.output


@pytest.mark.parametrize("output_format", [None, "json"], ids=["text", "json"])
def test_valid_unicode_output_is_preserved(project_dir, utf8_locale, output_format):
    stdout = '{\r\n"message": "caf\u00e9"\r}'
    stderr = "diagnostic: caf\u00e9\r\nnext line\rlast line\n"
    run = _python_run(
        project_dir,
        f"import os\nos.write(1, {stdout.encode('utf-8')!r})\n"
        f"os.write(2, {stderr.encode('utf-8')!r})\n",
    )
    config = {"id": "valid-output", "type": "shell", "run": run}
    if output_format is not None:
        config["output_format"] = output_format

    result = ShellStep().execute(config, StepContext(project_root=str(project_dir)))

    assert result.status == StepStatus.COMPLETED
    assert result.error is None
    assert result.output["stdout"] == '{\n"message": "caf\u00e9"\n}'
    assert result.output["stderr"] == "diagnostic: caf\u00e9\nnext line\nlast line\n"
    assert result.output["exit_code"] == 0
    if output_format == "json":
        assert result.output["data"] == {"message": "caf\u00e9"}
    else:
        assert "data" not in result.output


@pytest.mark.parametrize("continue_on_error", [False, True], ids=["halt", "continue"])
def test_decoding_failure_respects_continue_on_error(project_dir, utf8_locale, continue_on_error):
    run = _python_run(project_dir, "import os\nos.write(1, bytes([255]))\n")
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {
            "id": "shell-output-decoding",
            "name": "Shell Output Decoding",
            "version": "1.0.0",
        },
        "steps": [
            {
                "id": "invalid-output",
                "type": "shell",
                "run": run,
                "continue_on_error": continue_on_error,
            },
            {"id": "after", "type": "shell", "run": "echo did-run"},
        ],
    }))

    state = WorkflowEngine(project_dir).execute(definition)

    assert state.step_results["invalid-output"]["status"] == "failed"
    assert "could not be decoded" in state.step_results["invalid-output"]["error"]
    if continue_on_error:
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["after"]["status"] == "completed"
        assert state.step_results["after"]["output"]["stdout"].strip() == "did-run"
    else:
        assert state.status == RunStatus.FAILED
        assert "after" not in state.step_results


@pytest.mark.parametrize("branch_type", ["if", "switch"])
def test_decoding_failure_preserves_exit_code_for_branching(project_dir, utf8_locale, branch_type):
    run = _python_run(
        project_dir,
        "import os\nos.write(1, b'usable output')\nos.write(2, bytes([255]))\n"
        "raise SystemExit(3)\n",
    )
    recovery = [{"id": "recovery", "type": "shell", "run": "echo recovery-ran"}]
    fallback = [{"id": "wrong-exit", "type": "shell", "run": "echo wrong-exit"}]
    branch = {"id": "route", "type": branch_type}
    if branch_type == "if":
        branch.update({
            "condition": "{{ steps.invalid-output.output.exit_code == 3 }}",
            "then": recovery,
            "else": fallback,
        })
    else:
        branch.update({
            "expression": "{{ steps.invalid-output.output.exit_code }}",
            "cases": {"3": recovery},
            "default": fallback,
        })
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {
            "id": "shell-decode-branching",
            "name": "Shell Decode Branching",
            "version": "1.0.0",
        },
        "steps": [
            {
                "id": "invalid-output",
                "type": "shell",
                "run": run,
                "continue_on_error": True,
            },
            branch,
        ],
    }))

    state = WorkflowEngine(project_dir).execute(definition)

    assert state.status == RunStatus.COMPLETED
    assert "recovery" in state.step_results
    assert "wrong-exit" not in state.step_results
    result = state.step_results["invalid-output"]
    assert result["status"] == "failed"
    assert result["output"]["exit_code"] == 3
    assert result["output"]["stdout"] == "usable output"
    assert result["output"]["stderr"] == ""
    assert "stderr could not be decoded" in result["error"]
