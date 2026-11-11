"""Regression tests for shell step execution and output decoding."""

from __future__ import annotations

import json
import locale
import os
import sys
from pathlib import Path

import pytest
import yaml

from specify_cli.workflows.base import RunStatus, StepContext, StepStatus
from specify_cli.workflows.engine import RunState, WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.expressions import evaluate_expression
from specify_cli.workflows.step.shell import ShellStep


@pytest.fixture
def utf8_locale(monkeypatch):
    """Use the same subprocess text encoding on Unix and Windows."""
    monkeypatch.setattr(locale, "getencoding", lambda: "utf-8")


def _python_run(project_dir: Path, body: str) -> str:
    script = project_dir / "emit.py"
    script.write_text(body, encoding="utf-8")
    return f'"{sys.executable}" "{script}"'


class TestJsonOutput:
    """The opted-in stdout decoder rejects constants without losing raw output."""

    @staticmethod
    def _execute(project_dir, stdout, *, output_format="json", exit_code=0):
        run = _python_run(
            project_dir,
            f"import sys\nsys.stdout.write({stdout!r})\n"
            f"sys.stderr.write('producer diagnostic')\nsys.exit({exit_code})\n",
        )
        config = {"id": "emit", "run": run}
        if output_format is not None:
            config["output_format"] = output_format
        return ShellStep().execute(config, StepContext(project_root=str(project_dir)))

    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
    @pytest.mark.parametrize("template", [
        " %s \n", "[%s]", '{"value":%s}', '{"outer":[{"inner":%s}]}',
        "[%s,0,%s]", '{"value":%s,"value":0}',
    ], ids=["root", "array", "object", "nested", "repeated", "overwritten"])
    def test_rejects_constants(self, project_dir, token, template):
        stdout = template % ((token, token) if template.count("%s") == 2 else token)
        result = self._execute(project_dir, stdout)

        assert result.status == StepStatus.FAILED
        assert result.output == {
            "exit_code": 0, "stdout": stdout, "stderr": "producer diagnostic",
        }
        assert result.error.startswith(
            "Shell step 'emit' declared output_format: json but stdout is not valid JSON: "
        )
        assert token in result.error

    def test_rejects_mixed_constants(self, project_dir):
        result = self._execute(project_dir, "[NaN,Infinity,-Infinity]")
        assert result.status == StepStatus.FAILED
        assert "data" not in result.output
        assert "NaN" in result.error

    @pytest.mark.parametrize("stdout, expected", [
        ('{"items":[1,false,null]}', {"items": [1, False, None]}),
        ("[0,true,{}]", [0, True, {}]),
        ('"hello"', "hello"), ("42", 42), ("-2.5e2", -250.0),
        ("true", True), ("false", False), ("null", None), ("0", 0),
        ("[]", []), ("{}", {}), ('""', ""),
        ('"\\u5b8c\\u6210"', "\u5b8c\u6210"),
        ('["NaN","Infinity","-Infinity","\\u004eaN"]',
         ["NaN", "Infinity", "-Infinity", "NaN"]),
        ('{"NaN":1,"Infinity":2,"-Infinity":3}', {"NaN": 1, "Infinity": 2, "-Infinity": 3}),
        ('{"value":1,"value":2}', {"value": 2}),
    ])
    def test_preserves_valid_values(self, project_dir, stdout, expected):
        result = self._execute(project_dir, stdout)
        assert result.status == StepStatus.COMPLETED
        assert result.error is None
        assert result.output == {
            "exit_code": 0, "stdout": stdout, "stderr": "producer diagnostic", "data": expected,
        }
        assert type(result.output["data"]) is type(expected)
        context = StepContext(steps={"emit": {"output": result.output}})
        assert evaluate_expression("{{ steps.emit.output.data }}", context) == expected
        encoded = evaluate_expression("{{ steps.emit.output.data | to_json }}", context)
        assert json.loads(encoded) == expected

    @pytest.mark.parametrize("stdout", [
        "not-json", "", " \n\t", "{} trailing", "nan", "inf", "+Infinity", "-NaN",
        "01", "[1,]", '{"v":1,}', '"unescaped\x01"',
    ])
    def test_malformed_json_still_fails(self, project_dir, stdout):
        result = self._execute(project_dir, stdout)
        assert result.status == StepStatus.FAILED
        assert "output_format: json but stdout is not valid JSON:" in result.error
        assert result.output == {
            "exit_code": 0, "stdout": stdout, "stderr": "producer diagnostic",
        }

    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
    def test_raw_default_preserves_constants(self, project_dir, token):
        result = self._execute(project_dir, token, output_format=None)
        assert result.status == StepStatus.COMPLETED
        assert result.error is None
        assert result.output == {
            "exit_code": 0, "stdout": token, "stderr": "producer diagnostic",
        }

    @pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
    def test_nonzero_exit_precedes_json_parsing(self, project_dir, token):
        result = self._execute(project_dir, token, exit_code=7)
        assert result.status == StepStatus.FAILED
        assert result.error == "Shell command exited with code 7."
        assert result.output == {
            "exit_code": 7, "stdout": token, "stderr": "producer diagnostic",
        }

    def test_integer_conversion_error_is_contained(self, project_dir):
        limit = sys.get_int_max_str_digits()
        if not limit:
            pytest.skip("Python integer string conversion limit is disabled")
        stdout = "1" * (limit + 1)
        result = self._execute(project_dir, stdout)
        assert result.status == StepStatus.FAILED
        assert "output_format: json but stdout is not valid JSON:" in result.error
        assert "integer string conversion" in result.error
        assert result.output == {
            "exit_code": 0, "stdout": stdout, "stderr": "producer diagnostic",
        }

    @pytest.mark.parametrize("continue_on_error", [False, True], ids=["halt", "continue"])
    def test_failure_persistence_and_retry(self, project_dir, continue_on_error):
        run = _python_run(
            project_dir, "import sys\nprint('NaN')\nsys.stderr.write('producer diagnostic')\n",
        )
        definition = WorkflowDefinition.from_string(yaml.safe_dump({
            "schema_version": "1.0",
            "workflow": {"id": "json-failure", "name": "JSON failure", "version": "1.0.0"},
            "steps": [
                {"id": "emit", "type": "shell", "run": run, "output_format": "json",
                 "continue_on_error": continue_on_error},
                {"id": "after", "type": "shell", "run": "echo recovered"},
            ],
        }))
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)
        failed = state.step_results["emit"]
        assert failed["status"] == "failed"
        assert "NaN" in failed["error"]
        assert failed["output"] == {
            "exit_code": 0, "stdout": "NaN\n", "stderr": "producer diagnostic",
        }
        loaded = RunState.load(state.run_id, project_dir)
        assert loaded.step_results["emit"] == failed
        if continue_on_error:
            assert loaded.status == RunStatus.COMPLETED
            assert loaded.step_results["after"]["output"]["stdout"].strip() == "recovered"
        else:
            assert loaded.status == RunStatus.FAILED
            assert "after" not in loaded.step_results
            _python_run(project_dir, "print('[1,2]')\n")
            resumed = engine.resume(state.run_id)
            assert resumed.status == RunStatus.COMPLETED
            assert resumed.step_results["emit"]["output"]["data"] == [1, 2]
            assert resumed.step_results["after"]["status"] == "completed"

    def test_completed_valid_producer_replays(self, project_dir):
        run = _python_run(project_dir, "print('[1,2]')\n")
        definition = WorkflowDefinition.from_string(yaml.safe_dump({
            "schema_version": "1.0",
            "workflow": {"id": "json-replay", "name": "JSON replay", "version": "1.0.0"},
            "inputs": {"command": {"type": "string", "default": "exit 7"}},
            "steps": [
                {"id": "emit", "type": "shell", "run": run, "output_format": "json"},
                {"id": "after", "type": "shell", "run": "{{ inputs.command }}"},
            ],
        }))
        engine = WorkflowEngine(project_dir)
        state = engine.execute(definition)
        assert state.status == RunStatus.FAILED
        assert state.step_results["emit"]["output"]["data"] == [1, 2]
        _python_run(project_dir, "raise RuntimeError('completed producer must not rerun')\n")
        resumed = engine.resume(state.run_id, {"command": "exit 0"})
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.step_results["emit"] == state.step_results["emit"]


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
    ({"strict": True, "run": None}, "'run' must be a string in strict mode"),
    ({"strict": True, "run": ["echo", "hello"]}, "'run' must be a string in strict mode"),
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


@pytest.mark.parametrize("run_config", [
    {},
    {"run": None},
    {"run": ["echo", "hello"]},
], ids=["missing", "null", "list"])
def test_strict_invalid_run_has_one_diagnostic_and_never_launches(monkeypatch, run_config):
    def unexpected_run(*args, **kwargs):
        pytest.fail("An invalid strict run must never reach the shell")

    monkeypatch.setattr("subprocess.run", unexpected_run)
    config = {"id": "invalid-run", "strict": True, **run_config}
    expected_error = "Shell step 'invalid-run': 'run' must be a string in strict mode."
    step = ShellStep()

    assert step.validate(config) == [expected_error]
    result = step.execute(config, StepContext())
    assert result.status == StepStatus.FAILED
    assert result.error == expected_error
    assert result.output["exit_code"] == -1


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


@pytest.mark.skipif(os.name != "posix", reason="POSIX process environment encoding")
@pytest.mark.parametrize("value", ["\ud800", "\udc00"])
@pytest.mark.parametrize("template", ["literal", "{{ inputs.value }}", "value={{ inputs.value }}"])
@pytest.mark.parametrize("strict", [False, True])
def test_unencodable_environment_fails_before_execution(monkeypatch, value, template, strict):
    def unexpected_run(*args, **kwargs):
        pytest.fail("Unencodable environment values must never reach subprocess.run")

    monkeypatch.setattr("subprocess.run", unexpected_run)
    config = {
        "id": "unencodable-env", "strict": strict, "run": "echo hello",
        "env": {"VALUE": value if template == "literal" else template},
    }
    step = ShellStep()
    errors = step.validate(config)
    if template == "literal":
        assert any("env 'VALUE'" in error and "encoded" in error for error in errors)
    else:
        assert errors == []

    result = step.execute(config, StepContext(inputs={"value": value}))
    assert result.status == StepStatus.FAILED
    assert "env 'VALUE'" in result.error
    assert "encoded" in result.error
    assert result.output["exit_code"] == -1


@pytest.mark.skipif(os.name != "posix", reason="POSIX process environment encoding")
@pytest.mark.parametrize("value", ["caf\u00e9", "byte-\udcff"])
def test_encodable_environment_preserves_unicode_and_surrogateescape(project_dir, value):
    run = _python_run(
        project_dir, "import os\nprint(os.fsencode(os.environ['VALUE']).hex())\n",
    )
    config = {
        "id": "encodable-env", "strict": True, "run": run,
        "env": {"VALUE": "{{ inputs.value }}"},
    }
    assert ShellStep().validate(config) == []
    result = ShellStep().execute(config, StepContext(
        project_root=str(project_dir), inputs={"value": value},
    ))
    assert result.status == StepStatus.COMPLETED
    assert result.output["stdout"].strip() == os.fsencode(value).hex()


@pytest.mark.parametrize(("value", "expected"), [
    (42, "n=42"),
    (None, "n="),
    (False, "n=False"),
    ([1, 2], "n=[1, 2]"),
    ({"key": "value"}, "n={'key': 'value'}"),
])
def test_mixed_environment_template_converts_embedded_values(project_dir, value, expected):
    run = _python_run(project_dir, "import os\nprint(os.environ['VALUE'])\n")
    config = {
        "id": "mixed-env", "strict": True, "run": run,
        "env": {"VALUE": "n={{ inputs.value }}"},
    }
    assert ShellStep().validate(config) == []
    result = ShellStep().execute(config, StepContext(
        project_root=str(project_dir), inputs={"value": value},
    ))
    assert result.status == StepStatus.COMPLETED
    assert result.output["stdout"] == expected + "\n"


@pytest.mark.skipif(os.name != "posix", reason="POSIX process environment encoding")
@pytest.mark.parametrize("continue_on_error", [False, True])
def test_unencodable_environment_respects_continue_on_error(project_dir, continue_on_error):
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {"id": "env-encoding", "name": "Env Encoding", "version": "1.0.0"},
        "inputs": {"encoded": {"type": "string", "default": r'"\ud800"'}},
        "steps": [
            {
                "id": "invalid", "type": "shell", "strict": True, "run": "echo hello",
                "env": {"VALUE": "{{ inputs.encoded | from_json }}"},
                "continue_on_error": continue_on_error,
            },
            {"id": "after", "type": "shell", "strict": True, "run": "echo after"},
        ],
    }))
    engine = WorkflowEngine(project_dir)
    assert engine.validate(definition) == []
    state = engine.execute(definition)
    assert state.step_results["invalid"]["status"] == "failed"
    assert "encoded" in state.step_results["invalid"]["error"]
    if continue_on_error:
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["after"]["status"] == "completed"
    else:
        assert state.status == RunStatus.FAILED
        assert "after" not in state.step_results


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


@pytest.mark.skipif(os.name != "posix", reason="POSIX executable fixtures")
@pytest.mark.parametrize("variable", ["PATH", "PYTHONPATH"])
@pytest.mark.parametrize("selected", ["first", "second"])
def test_strict_environment_can_select_executables_and_modules(project_dir, variable, selected):
    parent_value = os.environ.get(variable)
    for name in ("first", "second"):
        directory = project_dir / name
        directory.mkdir()
        if variable == "PATH":
            script = directory / "strict-env-probe"
            script.write_text(f"#!/bin/sh\nprintf '%s\\n' '{name}'\n", encoding="utf-8")
            script.chmod(0o755)
        else:
            (directory / "workflow_env_probe.py").write_text(
                f"selected = {name!r}\n", encoding="utf-8",
            )
    run = "strict-env-probe" if variable == "PATH" else _python_run(
        project_dir, "import workflow_env_probe\nprint(workflow_env_probe.selected)\n",
    )
    config = {
        "id": "execution-env", "strict": True, "run": run,
        "env": {variable: "{{ inputs.directory }}"},
    }
    assert ShellStep().validate(config) == []
    result = ShellStep().execute(config, StepContext(
        project_root=str(project_dir),
        inputs={"directory": str(project_dir / selected)},
    ))
    assert result.status == StepStatus.COMPLETED
    assert result.output["stdout"] == selected + "\n"
    assert os.environ.get(variable) == parent_value


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


@pytest.fixture
def utf8_mode_code_page_locale(monkeypatch):
    """Python's UTF-8 mode on a system whose code page is cp936."""
    monkeypatch.setattr(locale, "getpreferredencoding", lambda do_setlocale=True: "utf-8")
    monkeypatch.setattr(locale, "getencoding", lambda: "cp936")


@pytest.mark.parametrize("output_format", [None, "json"], ids=["text", "json"])
def test_code_page_output_is_decoded_in_utf8_mode(project_dir, utf8_mode_code_page_locale, output_format):
    # cmd.exe and other native programs write in the code page even when
    # Python runs in UTF-8 mode (the default from Python 3.15).
    stdout = '{"message": "\u5b8c\u6210"}\r\n'
    stderr = "\u8b66\u544a\r\n"
    run = _python_run(
        project_dir,
        f"import os\nos.write(1, {stdout.encode('cp936')!r})\n"
        f"os.write(2, {stderr.encode('cp936')!r})\n",
    )
    config = {"id": "code-page-output", "type": "shell", "run": run}
    if output_format is not None:
        config["output_format"] = output_format

    result = ShellStep().execute(config, StepContext(project_root=str(project_dir)))

    assert result.status == StepStatus.COMPLETED
    assert result.error is None
    assert result.output["stdout"] == '{"message": "\u5b8c\u6210"}\n'
    assert result.output["stderr"] == "\u8b66\u544a\n"
    if output_format == "json":
        assert result.output["data"] == {"message": "\u5b8c\u6210"}


def test_output_invalid_in_code_page_too_fails_step(project_dir, utf8_mode_code_page_locale):
    run = _python_run(project_dir, "import os\nos.write(1, b'\\xff')\n")
    config = {"id": "invalid-output", "type": "shell", "run": run}

    result = ShellStep().execute(config, StepContext(project_root=str(project_dir)))

    assert result.status == StepStatus.FAILED
    assert "stdout could not be decoded" in result.error
    assert "utf-8" in result.error
    assert result.output["stdout"] == ""


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


@pytest.mark.parametrize(
    ("printed", "condition", "expected_branch"),
    [
        ("10", "== 10", "then-ran"),
        ("10", "!= 10", "else-ran"),
        ("10", "== 11", "else-ran"),
        ("10", "!= 11", "then-ran"),
        ("10", ">= 10", "then-ran"),
        ("10", "<= 10", "then-ran"),
        ("2.5", "== 2.5", "then-ran"),
        ("10x", "== 10", "else-ran"),
        ("10x", "!= 10", "then-ran"),
    ],
)
def test_captured_stdout_with_newline_compares_as_number(
    project_dir, printed, condition, expected_branch
):
    """Raw stdout keeps its trailing newline, yet compares as a number.

    A command such as ``echo 10`` captures ``"10\\n"``. ``==``/``!=`` must
    agree with ``>=``/``<=`` on that value, while non-numeric output is still
    compared as a string.
    """
    run = _python_run(project_dir, f"print({printed!r})\n")
    definition = WorkflowDefinition.from_string(yaml.safe_dump({
        "schema_version": "1.0",
        "workflow": {
            "id": "shell-stdout-compare",
            "name": "Shell Stdout Compare",
            "version": "1.0.0",
        },
        "steps": [
            {"id": "count", "type": "shell", "run": run},
            {
                "id": "route",
                "type": "if",
                "condition": "{{ steps.count.output.stdout " + condition + " }}",
                "then": [{"id": "then-ran", "type": "shell", "run": "echo then"}],
                "else": [{"id": "else-ran", "type": "shell", "run": "echo else"}],
            },
        ],
    }))

    state = WorkflowEngine(project_dir).execute(definition)

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["count"]["output"]["stdout"] == f"{printed}\n"
    other_branch = "else-ran" if expected_branch == "then-ran" else "then-ran"
    assert expected_branch in state.step_results
    assert other_branch not in state.step_results
