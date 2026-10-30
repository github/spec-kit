"""Real-process regression tests for shell step output decoding."""

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
