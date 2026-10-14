"""``capture: true`` on the ``command`` and ``prompt`` workflow steps."""

from __future__ import annotations

import json
import sys

import pytest
import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations._capture import CapturedProcess
from specify_cli.integrations.base import IntegrationBase
from specify_cli.workflows.base import StepContext, StepStatus
from specify_cli.workflows.engine import WorkflowEngine
from specify_cli.workflows.step.command import CommandStep
from specify_cli.workflows.step.prompt import PromptStep

STEPS = {
    "command": (CommandStep, {"command": "speckit.plan"}),
    "prompt": (PromptStep, {"type": "prompt", "prompt": "Summarise the plan"}),
}
LABELS = {"command": "Command", "prompt": "Prompt"}
CAPTURE_FIELDS = ("stdout_truncated", "stderr_truncated", "timed_out", "interrupted")


def _config(kind: str, **fields) -> dict:
    return {"id": "ask", **STEPS[kind][1], **fields}


def _execute(kind: str, project_dir, **fields):
    context = StepContext(default_integration="claude", project_root=str(project_dir))
    return STEPS[kind][0]().execute(_config(kind, **fields), context)


@pytest.fixture
def fake_cli(monkeypatch, project_dir):
    """Make the ``claude`` integration run a Python script as its CLI.

    The script receives the requested output format (``json``/``text``) as
    ``sys.argv[1]`` and counts its invocations in ``calls.txt``.
    """

    def install(body: str) -> None:
        script = project_dir / "fake_cli.py"
        script.write_text(
            "import sys, time\n"
            f"open({str(project_dir / 'calls.txt')!r}, 'a').write('x')\n" + body,
            encoding="utf-8",
        )
        monkeypatch.setattr(
            type(get_integration("claude")),
            "build_exec_args",
            lambda self, prompt, *, output_json=True, **kwargs: [
                sys.executable,
                "-u",
                str(script),
                "json" if output_json else "text",
            ],
        )

    install.calls = lambda: len((project_dir / "calls.txt").read_text())
    return install


@pytest.mark.parametrize("kind", ["command", "prompt"])
class TestCaptureValidation:
    @pytest.mark.parametrize(
        "fields",
        [
            {},
            {"capture": False},
            {"capture": True},
            {"capture": True, "capture_max_bytes": 1},
            {"capture": True, "capture_max_bytes": -1},
            {"capture": True, "timeout": 30},
        ],
    )
    def test_valid_configs_pass(self, kind, fields):
        assert STEPS[kind][0]().validate(_config(kind, **fields)) == []

    @pytest.mark.parametrize("capture", ["true", 1, 0, None, []])
    def test_non_boolean_capture_is_rejected(self, kind, capture):
        errors = STEPS[kind][0]().validate(_config(kind, capture=capture))
        assert errors == [
            f"{LABELS[kind]} step 'ask': 'capture' must be true or false, "
            f"got {capture!r}."
        ]

    @pytest.mark.parametrize("max_bytes", [0, -2, True, False, 1.5, "1024", None])
    def test_invalid_limit_is_rejected(self, kind, max_bytes):
        errors = STEPS[kind][0]().validate(
            _config(kind, capture=True, capture_max_bytes=max_bytes)
        )
        assert errors == [
            f"{LABELS[kind]} step 'ask': 'capture_max_bytes' must be a positive "
            f"integer or -1 (no limit), got {max_bytes!r}."
        ]

    @pytest.mark.parametrize("fields", [{}, {"capture": False}])
    def test_limit_without_capture_is_rejected(self, kind, fields):
        errors = STEPS[kind][0]().validate(
            _config(kind, capture_max_bytes=1024, **fields)
        )
        assert errors == [
            f"{LABELS[kind]} step 'ask': 'capture_max_bytes' requires "
            f"'capture: true'."
        ]

    @pytest.mark.parametrize(
        "fields",
        [
            {"capture": "yes"},
            {"capture": True, "capture_max_bytes": 0},
            {"capture_max_bytes": 1024},
            {"capture": True, "timeout": -1},
        ],
    )
    def test_unvalidated_execute_fails_the_step_without_dispatching(
        self, kind, fields, project_dir, fake_cli
    ):
        fake_cli("print('ran')\n")
        result = _execute(kind, project_dir, **fields)
        assert result.status == StepStatus.FAILED
        assert "'ask'" in result.error
        assert not (project_dir / "calls.txt").exists()


class TestCommandTimeoutValidation:
    @pytest.mark.parametrize("timeout", [0, -5, True, "60", float("inf")])
    def test_invalid_timeout_is_rejected_when_capturing(self, timeout):
        errors = CommandStep().validate(
            _config("command", capture=True, timeout=timeout)
        )
        assert errors == [
            f"Command step 'ask': 'timeout' must be a positive number of "
            f"seconds, got {timeout!r}."
        ]

    def test_streaming_command_timeout_stays_unchecked(self):
        """A streaming command never applied 'timeout'; validation is unchanged."""
        assert CommandStep().validate(_config("command", timeout="5m")) == []


@pytest.mark.parametrize("kind", ["command", "prompt"])
class TestCaptureExecution:
    def test_captures_text_output_without_printing_it(
        self, kind, project_dir, fake_cli, capfd
    ):
        fake_cli("print('format=' + sys.argv[1]); sys.stderr.write('note')\n")
        result = _execute(kind, project_dir, capture=True)

        assert result.status == StepStatus.COMPLETED
        assert result.error is None
        assert result.output["exit_code"] == 0
        assert result.output["stdout"] == "format=text\n"
        assert result.output["stderr"] == "note"
        assert result.output["dispatched"] is True
        assert {field: result.output[field] for field in CAPTURE_FIELDS} == dict.fromkeys(
            CAPTURE_FIELDS, False
        )
        printed = capfd.readouterr()
        assert "format=text" not in printed.out + printed.err

    @pytest.mark.parametrize("fields", [{}, {"capture": False}])
    def test_streaming_is_unchanged_without_capture(
        self, kind, fields, project_dir, fake_cli, capfd
    ):
        fake_cli("print('format=' + sys.argv[1]); sys.stderr.write('note')\n")
        result = _execute(kind, project_dir, **fields)

        assert result.status == StepStatus.COMPLETED
        assert result.output["stdout"] == ""
        assert result.output["stderr"] == ""
        assert not set(CAPTURE_FIELDS) & set(result.output)
        printed = capfd.readouterr()
        assert printed.out == "format=text\n"
        assert printed.err == "note"

    def test_non_zero_exit_keeps_output_and_summarises_the_error(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("print('half done'); sys.stderr.write('token=SECRET'); sys.exit(7)\n")
        result = _execute(kind, project_dir, capture=True)

        assert result.status == StepStatus.FAILED
        assert result.error == f"{LABELS[kind]} exited with code 7"
        assert result.output["exit_code"] == 7
        assert result.output["stdout"] == "half done\n"
        assert result.output["stderr"] == "token=SECRET"
        assert result.output["timed_out"] is False

    def test_streaming_non_zero_exit_error_is_unchanged(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("sys.exit(7)\n")
        result = _execute(kind, project_dir)
        assert result.status == StepStatus.FAILED
        assert result.error == f"{LABELS[kind]} exited with code 7"
        assert result.output["stderr"] == ""

    def test_finite_limit_truncates_and_flags(self, kind, project_dir, fake_cli):
        fake_cli("sys.stdout.write('a' * 500_000); sys.stderr.write('e' * 4)\n")
        result = _execute(kind, project_dir, capture=True, capture_max_bytes=16)

        assert result.status == StepStatus.COMPLETED
        assert result.output["stdout"] == "a" * 16
        assert result.output["stdout_truncated"] is True
        assert result.output["stderr"] == "eeee"
        assert result.output["stderr_truncated"] is False

    def test_unlimited_capture_never_flags_truncation(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("sys.stdout.write('a' * 2_000_000)\n")
        result = _execute(kind, project_dir, capture=True, capture_max_bytes=-1)

        assert result.status == StepStatus.COMPLETED
        assert len(result.output["stdout"]) == 2_000_000
        assert result.output["stdout_truncated"] is False

    def test_non_utf8_output_is_decoded_with_replacement(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("sys.stdout.buffer.write('caf\\u00e9 '.encode('utf-8') + b'\\xff')\n")
        result = _execute(kind, project_dir, capture=True)
        assert result.output["stdout"] == "café \ufffd"

    def test_timeout_fails_the_step_with_partial_output(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("print('partial'); sys.stderr.write('slow'); time.sleep(60)\n")
        result = _execute(
            kind, project_dir, capture=True, capture_max_bytes=-1, timeout=1
        )

        assert result.status == StepStatus.FAILED
        assert result.error == f"{LABELS[kind]} timed out after 1 seconds."
        assert result.output["exit_code"] == -1
        assert result.output["timed_out"] is True
        assert result.output["stdout"] == "partial\n"
        assert result.output["stderr"] == "slow"
        # Partial because the process was stopped, not because of the limit.
        assert result.output["stdout_truncated"] is False

    def test_interruption_fails_the_step_with_partial_output(
        self, kind, project_dir, fake_cli, monkeypatch
    ):
        fake_cli("print('unused')\n")
        interrupted = CapturedProcess(
            exit_code=130, stdout="partial", stderr="noise", interrupted=True
        )
        for module in (
            "specify_cli.integrations.base",
            "specify_cli.workflows.step.prompt",
        ):
            monkeypatch.setattr(
                f"{module}.run_captured", lambda *args, **kwargs: interrupted
            )
        result = _execute(kind, project_dir, capture=True)

        assert result.status == StepStatus.FAILED
        assert result.error == "Interrupted by user"
        assert result.output["exit_code"] == 130
        assert result.output["interrupted"] is True
        assert result.output["stdout"] == "partial"
        assert result.output["stderr"] == "noise"


class TestCommandCaptureDispatch:
    def test_default_timeout_is_600_seconds(self, project_dir, fake_cli, monkeypatch):
        fake_cli("print('unused')\n")
        seen: dict = {}

        def fake_run_captured(args, **kwargs):
            seen.update(kwargs)
            return CapturedProcess(exit_code=0, stdout="", stderr="")

        monkeypatch.setattr(
            "specify_cli.integrations.base.run_captured", fake_run_captured
        )
        _execute("command", project_dir, capture=True)
        assert seen["timeout"] == 600
        assert seen["max_bytes"] == 1024 * 1024

    def test_integration_without_capture_keywords_fails_cleanly(
        self, project_dir, fake_cli, monkeypatch
    ):
        """An installed integration may still override the older signature."""
        fake_cli("print('ran')\n")

        def legacy_dispatch(
            self,
            command_name,
            args="",
            *,
            project_root=None,
            model=None,
            timeout=600,
            stream=True,
            integration_args=None,
            integration_options=None,
        ):
            return IntegrationBase.dispatch_command(
                self, command_name, args, project_root=project_root, stream=stream
            )

        monkeypatch.setattr(
            type(get_integration("claude")), "dispatch_command", legacy_dispatch
        )
        captured = _execute("command", project_dir, capture=True)
        assert captured.status == StepStatus.FAILED
        assert captured.error == (
            "Command step 'ask': integration 'claude' does not support "
            "'capture: true'."
        )
        assert not (project_dir / "calls.txt").exists()

        streamed = _execute("command", project_dir)
        assert streamed.status == StepStatus.COMPLETED


def _install_workflow(project_dir, steps: list[dict], inputs: dict | None = None):
    definition = {
        "schema_version": "1.0",
        "workflow": {
            "id": "wf",
            "name": "WF",
            "version": "1.0.0",
            "integration": "claude",
        },
        "steps": steps,
    }
    if inputs:
        definition["inputs"] = inputs
    workflow_dir = project_dir / ".specify" / "workflows" / "wf"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "workflow.yml").write_text(
        yaml.safe_dump(definition), encoding="utf-8"
    )
    engine = WorkflowEngine(project_dir)
    return engine, engine.load_workflow("wf")


def _run_dir(project_dir, state):
    return project_dir / ".specify" / "workflows" / "runs" / state.run_id


@pytest.mark.parametrize("kind", ["command", "prompt"])
class TestCaptureInWorkflows:
    """The composition gap from issue #4613, before and after ``capture``."""

    @staticmethod
    def _steps(kind: str, **fields) -> list[dict]:
        return [
            _config(kind, **fields),
            {
                "id": "use",
                "type": "shell",
                "run": "echo verdict={{ steps.ask.output.stdout }}",
            },
        ]

    def test_without_capture_downstream_sees_no_output(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("sys.stdout.write('READY')\n")
        engine, definition = _install_workflow(project_dir, self._steps(kind))
        state = engine.execute(definition, {})

        assert state.status.value == "completed"
        assert state.step_results["use"]["output"]["stdout"].strip() == "verdict="

    def test_with_capture_downstream_consumes_the_output(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("sys.stdout.write('READY')\n")
        engine, definition = _install_workflow(
            project_dir, self._steps(kind, capture=True)
        )
        state = engine.execute(definition, {})

        assert state.status.value == "completed"
        assert state.step_results["use"]["output"]["stdout"].strip() == "verdict=READY"

    def test_captured_output_survives_resume_without_redispatch(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("sys.stdout.write('READY')\n")
        steps = self._steps(kind, capture=True)
        steps.insert(
            1,
            {
                "id": "review",
                "type": "gate",
                "message": "Continue?",
                "options": ["approve", "reject"],
                "verdict_input": "verdict",
            },
        )
        engine, definition = _install_workflow(
            project_dir, steps, inputs={"verdict": {"type": "string", "default": ""}}
        )
        paused = engine.execute(definition, {})
        assert paused.status.value == "paused"
        assert "use" not in paused.step_results

        resumed = WorkflowEngine(project_dir).resume(
            paused.run_id, inputs={"verdict": "approve"}
        )
        assert resumed.status.value == "completed"
        assert resumed.step_results["use"]["output"]["stdout"].strip() == "verdict=READY"
        assert fake_cli.calls() == 1

    def test_captured_stderr_is_persisted_in_state_but_kept_out_of_the_log(
        self, kind, project_dir, fake_cli, capfd
    ):
        fake_cli("sys.stderr.write('token=SECRET'); sys.exit(2)\n")
        engine, definition = _install_workflow(
            project_dir, self._steps(kind, capture=True)
        )
        state = engine.execute(definition, {})

        assert state.status.value == "failed"
        run_dir = _run_dir(project_dir, state)
        saved = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        assert saved["step_results"]["ask"]["output"]["stderr"] == "token=SECRET"
        assert "SECRET" not in (run_dir / "log.jsonl").read_text(encoding="utf-8")
        printed = capfd.readouterr()
        assert "SECRET" not in printed.out + printed.err

    def test_continue_on_error_lets_downstream_inspect_a_failed_capture(
        self, kind, project_dir, fake_cli
    ):
        fake_cli("print('partial'); time.sleep(60)\n")
        steps = [
            _config(kind, capture=True, timeout=1, continue_on_error=True),
            {
                "id": "recover",
                "type": "if",
                "condition": "{{ steps.ask.output.timed_out }}",
                "then": [
                    {
                        "id": "report",
                        "type": "shell",
                        "run": "echo partial={{ steps.ask.output.stdout }}",
                    }
                ],
            },
        ]
        engine, definition = _install_workflow(project_dir, steps)
        state = engine.execute(definition, {})

        assert state.status.value == "completed"
        assert state.step_results["ask"]["output"]["exit_code"] == -1
        report = state.step_results["report"]["output"]["stdout"]
        assert report.strip() == "partial=partial"
