"""Per-step ``reasoning_effort`` and ``context_size`` on the dispatching steps.

The integrations here are fakes registered for one test, or built-ins that
translate neither setting (Gemini, Docker Agent). Executable lookup and the
CLI process are faked, so no agent CLI runs.
"""

from __future__ import annotations

import dataclasses
import json
from types import SimpleNamespace

import pytest
import yaml

from specify_cli.integrations import INTEGRATION_REGISTRY
from specify_cli.integrations._capture import CapturedProcess
from specify_cli.integrations.base import (
    DISPATCH_SETTINGS,
    DispatchSettingsError,
    IntegrationBase,
    dispatch_setting_value_error,
)
from specify_cli.integrations.gemini import GeminiIntegration
from specify_cli.workflows import STEP_REGISTRY
from specify_cli.workflows.base import (
    RunStatus,
    StepBase,
    StepContext,
    StepResult,
    StepStatus,
)
from specify_cli.workflows.engine import (
    WorkflowDefinition,
    WorkflowEngine,
    validate_workflow,
)
from specify_cli.workflows.step._dispatch_settings import (
    dispatch_settings_attribution,
    resolve_dispatch_settings,
)
from specify_cli.workflows.step.command import CommandStep
from specify_cli.workflows.step.prompt import PromptStep

STEPS = {
    "command": (CommandStep, {"command": "speckit.plan"}),
    "prompt": (PromptStep, {"type": "prompt", "prompt": "Summarise the plan"}),
}
LABELS = {"command": "Command", "prompt": "Prompt"}
PROMPTS = {"command": "/speckit.plan", "prompt": "Summarise the plan"}
KINDS = pytest.mark.parametrize("kind", list(STEPS))

UNSUPPORTED = (
    "Integration {key!r} does not support per-step '{name}'. {supporters} "
    "Remove the setting from this step (and from the workflow defaults it "
    "inherits), or dispatch the step to a supporting integration."
)
NO_SUPPORTERS = "No available integration supports it."
UNSAFE_VALUES = pytest.mark.parametrize(
    "value",
    [
        pytest.param("-high", id="leading-dash"),
        pytest.param("high effort", id="space"),
        pytest.param("high\n", id="trailing-newline"),
        pytest.param("a" * 65, id="65-chars"),
        pytest.param("a&b", id="ampersand"),
        pytest.param("a|b", id="pipe"),
        pytest.param("a;b", id="semicolon"),
        pytest.param("a<b", id="less-than"),
        pytest.param("a>b", id="greater-than"),
        pytest.param("a^b", id="caret"),
    ],
)
# Untrusted text, such as captured agent output, that reaches a setting.
HUGE = "\x1b[31m" + "x" * (1024 * 1024) + "\nSECRET"


# -- Fake integrations ----------------------------------------------------


class _Translating(IntegrationBase):
    """Declares both settings and translates them in its own builder."""

    key = "fake-translating"
    supported_dispatch_settings = frozenset(DISPATCH_SETTINGS)

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def build_exec_args(self, prompt, **kwargs):
        self.calls.append(kwargs)
        args = [self.key, "-p", prompt]
        self._apply_extra_args_env_var(args)
        for flag, name in (
            ("--effort", "reasoning_effort"),
            ("--context", "context_size"),
        ):
            if name in kwargs:
                args.extend([flag, kwargs[name]])
        return args


class _Inheriting(_Translating):
    """Inherits the declaration together with the builder it covers."""

    key = "fake-inheriting"


class _EffortOnly(IntegrationBase):
    """Translates reasoning effort but not context size."""

    key = "fake-effort-only"
    supported_dispatch_settings = frozenset({"reasoning_effort"})

    def build_exec_args(self, prompt, *, reasoning_effort=None, **kwargs):
        args = [self.key, "-p", prompt]
        if reasoning_effort is not None:
            args.extend(["--effort", reasoning_effort])
        return args


class _CommandOwner(IntegrationBase):
    """Translates reasoning effort in its own ``dispatch_command`` only."""

    key = "fake-command-owner"
    supported_dispatch_settings = frozenset({"reasoning_effort"})

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def dispatch_command(self, command_name, args="", **kwargs):
        self.calls.append(kwargs)
        return {"exit_code": 0, "stdout": "", "stderr": ""}


class _Validating(_Translating):
    """Rejects the value ``rejected`` with a plain ``ValueError``."""

    key = "fake-validating"

    def validate_dispatch_setting(self, name, value):
        if value == "rejected":
            raise ValueError(f"the CLI does not accept this {name}")


class _Unlabeled(_Translating):
    """Raises its own ``DispatchSettingsError`` that names no setting."""

    key = "fake-unlabeled"
    supported_dispatch_settings = frozenset(DISPATCH_SETTINGS)

    def build_exec_args(self, prompt, **kwargs):
        if any(name in kwargs for name in DISPATCH_SETTINGS):
            raise DispatchSettingsError("the CLI rejected these settings")
        return super().build_exec_args(prompt, **kwargs)


class _LegacyKwargsOverride(_Translating):
    """Replaces the capable builder without declaring support itself."""

    key = "fake-legacy-kwargs"

    def build_exec_args(self, prompt, **kwargs):
        return [self.key, "-p", prompt]


class _StringDeclaration(IntegrationBase):
    """Declares support with a string, which is not a set of settings."""

    key = "fake-string-declaration"
    supported_dispatch_settings = "reasoning_effort"

    def build_exec_args(self, prompt, **kwargs):
        return [self.key, "-p", prompt]


def _forward_to_toml_builder(self, prompt, **kwargs):
    """A Gemini builder that hands every keyword to ``TomlIntegration``."""
    return super(GeminiIntegration, self).build_exec_args(prompt, **kwargs)


class _StrictBuilder(IntegrationBase):
    """A builder whose signature predates the dispatch settings."""

    key = "fake-strict-builder"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def build_exec_args(
        self,
        prompt,
        *,
        model=None,
        output_json=True,
        integration_args=None,
        integration_options=None,
        project_root=None,
    ):
        self.calls.append(prompt)
        return [self.key, "-p", prompt]


class _StrictCommand(IntegrationBase):
    """A ``dispatch_command`` whose signature predates the dispatch settings."""

    key = "fake-strict-command"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def dispatch_command(
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
        output_json=None,
        capture_max_bytes=None,
    ):
        self.calls.append(command_name)
        return {"exit_code": 0, "stdout": "", "stderr": ""}


class _After(StepBase):
    """Records that the run went on past the step under test."""

    type_key = "dispatch-settings-after"

    def execute(self, config, context):
        return StepResult(output={"ran": True})


# -- Fixtures and helpers -------------------------------------------------


@pytest.fixture
def register(monkeypatch):
    """Register a fake integration for one test."""

    def add(integration):
        monkeypatch.setitem(INTEGRATION_REGISTRY, integration.key, integration)
        return integration

    return add


@pytest.fixture
def cli(monkeypatch):
    """Find every CLI and fake running it, recording each argv."""
    state = SimpleNamespace(runs=[], returncode=0, stdout="", stderr="")

    def run(args, **kwargs):
        state.runs.append(list(args))
        return SimpleNamespace(returncode=state.returncode, stdout="", stderr="")

    def run_captured(args, **kwargs):
        state.runs.append(list(args))
        return CapturedProcess(
            exit_code=state.returncode, stdout=state.stdout, stderr=state.stderr
        )

    monkeypatch.setattr("shutil.which", lambda name: name)
    monkeypatch.setattr("subprocess.run", run)
    for module in (
        "specify_cli.integrations.base",
        "specify_cli.workflows.step.prompt",
    ):
        monkeypatch.setattr(f"{module}.run_captured", run_captured)
    return state


@pytest.fixture
def no_cli(monkeypatch):
    """Find no CLI, so reaching executable detection means 'not installed'."""
    monkeypatch.setattr("shutil.which", lambda name: None)


@pytest.fixture
def without_builtin_supporters(monkeypatch):
    """Withdraw built-in declarations so supporter lists name only fakes."""
    for integration in list(INTEGRATION_REGISTRY.values()):
        for klass in type(integration).__mro__:
            if vars(klass).get("supported_dispatch_settings"):
                monkeypatch.setattr(klass, "supported_dispatch_settings", frozenset())


@pytest.fixture
def after_step(monkeypatch):
    monkeypatch.setitem(STEP_REGISTRY, _After.type_key, _After())
    return {"id": "after", "type": _After.type_key}


def _config(kind: str, **fields) -> dict:
    return {"id": "ask", **STEPS[kind][1], **fields}


def _execute(kind, project_dir, integration, *, inputs=None, defaults=None, **fields):
    defaults = defaults or {}
    context = StepContext(
        inputs=inputs or {},
        default_integration=integration,
        project_root=str(project_dir),
        default_reasoning_effort=defaults.get("reasoning_effort"),
        default_context_size=defaults.get("context_size"),
    )
    return STEPS[kind][0]().execute(_config(kind, **fields), context)


def _received(integration) -> dict:
    """Return the dispatch settings *integration* last dispatched with."""
    call = integration.calls[-1]
    return {name: call[name] for name in DISPATCH_SETTINGS if name in call}


def _outputs(result) -> dict:
    return {name: result.output[name] for name in DISPATCH_SETTINGS}


def _assert_summarized(message: str, value: str) -> None:
    """A malformed value is reported by its length, never echoed into the message."""
    assert f"got a string of length {len(value)}." in message
    assert value not in message
    assert len(message) < 400
    assert "\x1b" not in message
    assert "\n" not in message
    assert "SECRET" not in message


def _workflow(steps, *, defaults=None, inputs=None, workflow_id="wf"):
    data = {
        "schema_version": "1.0",
        "workflow": {
            "id": workflow_id,
            "name": workflow_id,
            "version": "1.0.0",
            **(defaults or {}),
        },
        "steps": steps,
    }
    if inputs:
        data["inputs"] = inputs
    return WorkflowDefinition(data)


def _install(project_dir, definition: WorkflowDefinition) -> None:
    from specify_cli.workflows.catalog import WorkflowRegistry

    directory = project_dir / ".specify" / "workflows" / definition.id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "workflow.yml").write_text(
        yaml.safe_dump(definition.data), encoding="utf-8"
    )
    WorkflowRegistry(project_dir).add(
        definition.id, {"version": "1.0.0", "enabled": True}
    )


# -- Resolution -----------------------------------------------------------


@KINDS
class TestResolution:
    @pytest.mark.parametrize(
        ("fields", "defaults", "expected"),
        [
            (
                {"reasoning_effort": "high"},
                {"reasoning_effort": "low"},
                {"reasoning_effort": "high"},
            ),
            ({}, {"reasoning_effort": "low"}, {"reasoning_effort": "low"}),
            (
                {"reasoning_effort": None},
                {"reasoning_effort": "low"},
                {"reasoning_effort": "low"},
            ),
            (
                {"reasoning_effort": ""},
                {"reasoning_effort": "low"},
                {"reasoning_effort": "low"},
            ),
            ({"reasoning_effort": None, "context_size": ""}, {}, {}),
            (
                {"context_size": "200000"},
                {"reasoning_effort": "low", "context_size": "long_context"},
                {"reasoning_effort": "low", "context_size": "200000"},
            ),
        ],
        ids=[
            "step-wins",
            "workflow-default",
            "null-inherits",
            "empty-inherits",
            "unset",
            "mixed-sources",
        ],
    )
    def test_step_value_then_workflow_default_then_unset(
        self, kind, fields, defaults, expected, project_dir, register, cli
    ):
        fake = register(_Translating())
        result = _execute(kind, project_dir, fake.key, defaults=defaults, **fields)

        assert result.status is StepStatus.COMPLETED, result.error
        assert _received(fake) == expected
        assert _outputs(result) == {
            name: expected.get(name) for name in DISPATCH_SETTINGS
        }

    @pytest.mark.parametrize(
        ("fields", "defaults", "expected"),
        [
            ({"reasoning_effort": "{{ inputs.effort }}"}, {}, "medium"),
            ({}, {"reasoning_effort": "{{ inputs.effort }}"}, "medium"),
            ({"reasoning_effort": "x-{{ inputs.effort }}"}, {}, "x-medium"),
        ],
        ids=["step", "workflow-default", "interpolated"],
    )
    def test_expressions_are_evaluated(
        self, kind, fields, defaults, expected, project_dir, register, cli
    ):
        fake = register(_Translating())
        result = _execute(
            kind,
            project_dir,
            fake.key,
            inputs={"effort": "medium"},
            defaults=defaults,
            **fields,
        )

        assert result.status is StepStatus.COMPLETED, result.error
        assert _received(fake) == {"reasoning_effort": expected}
        assert result.output["reasoning_effort"] == expected

    @pytest.mark.parametrize("effort", ["", None])
    @pytest.mark.parametrize(
        ("fields", "defaults"),
        [
            ({"reasoning_effort": "{{ inputs.effort }}"}, {"reasoning_effort": "low"}),
            ({}, {"reasoning_effort": "{{ inputs.effort }}"}),
        ],
        ids=["step-opts-out-of-default", "default-resolves-empty"],
    )
    def test_resolved_empty_value_is_unset_without_a_second_fallback(
        self, kind, effort, fields, defaults, project_dir, register, cli
    ):
        fake = register(_Translating())
        result = _execute(
            kind,
            project_dir,
            fake.key,
            inputs={"effort": effort},
            defaults=defaults,
            **fields,
        )

        assert result.status is StepStatus.COMPLETED, result.error
        assert _received(fake) == {}
        assert result.output["reasoning_effort"] is None


def test_resolution_records_where_each_set_value_came_from():
    context = StepContext(
        default_reasoning_effort="low", default_context_size="long_context"
    )
    resolved = resolve_dispatch_settings(
        {"id": "ask", "context_size": "200000"}, context, "Command"
    )

    assert resolved.settings == {"reasoning_effort": "low", "context_size": "200000"}
    assert list(resolved.settings) == list(DISPATCH_SETTINGS)
    assert resolved.sources == {
        "reasoning_effort": "workflow.reasoning_effort",
        "context_size": "step",
    }
    assert resolved.outputs == resolved.settings

    unset = resolve_dispatch_settings({"id": "ask"}, StepContext(), "Command")
    assert unset.settings == {}
    assert unset.sources == {}
    assert unset.outputs == dict.fromkeys(DISPATCH_SETTINGS)


@pytest.mark.parametrize(
    ("setting", "sources", "expected"),
    [
        (
            "context_size",
            {"reasoning_effort": "step", "context_size": "workflow.context_size"},
            "(set by workflow.context_size)",
        ),
        (
            None,
            {"context_size": "step", "reasoning_effort": "workflow.reasoning_effort"},
            "(settings: reasoning_effort from workflow.reasoning_effort; "
            "context_size from step)",
        ),
        (
            "context_size",
            {"reasoning_effort": "step"},
            "(settings: reasoning_effort from step)",
        ),
        (None, {}, ""),
        ("reasoning_effort", {}, ""),
    ],
    ids=[
        "named",
        "unnamed-lists-all",
        "unset-setting-lists-all",
        "none-set",
        "named-none-set",
    ],
)
def test_attribution_never_indexes_an_unknown_setting(setting, sources, expected):
    assert dispatch_settings_attribution(setting, sources) == expected


# -- Validation -----------------------------------------------------------


@KINDS
class TestValidation:
    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    @pytest.mark.parametrize(
        "value", [None, "", "high", "200000", "long_context", "{{ inputs.effort }}"]
    )
    def test_valid_values_pass(self, kind, name, value):
        assert STEPS[kind][0]().validate(_config(kind, **{name: value})) == []

    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    @pytest.mark.parametrize("value", [200000, True, False, 1.5, ["high"]])
    def test_non_strings_are_rejected_with_a_quoting_hint(self, kind, name, value):
        errors = STEPS[kind][0]().validate(_config(kind, **{name: value}))

        assert errors == [
            f"{LABELS[kind]} step 'ask': {dispatch_setting_value_error(name, value)}"
        ]
        assert f"'{name}' must be a string, got {type(value).__name__}" in errors[0]
        assert "quote YAML values" in errors[0]

    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    @UNSAFE_VALUES
    def test_unsafe_literals_are_rejected(self, kind, name, value):
        errors = STEPS[kind][0]().validate(_config(kind, **{name: value}))

        assert len(errors) == 1
        assert errors[0].startswith(
            f"{LABELS[kind]} step 'ask': '{name}' must be 1-64 letters"
        )
        _assert_summarized(errors[0], value)

    def test_oversized_literal_is_summarized(self, kind):
        (error,) = STEPS[kind][0]().validate(_config(kind, reasoning_effort=HUGE))

        _assert_summarized(error, HUGE)


@KINDS
class TestResolvedValueValidation:
    @pytest.mark.parametrize(
        ("fields", "defaults", "inputs", "value", "source", "from_expression"),
        [
            (
                {"reasoning_effort": "{{ inputs.value }}"},
                {},
                {"value": 5},
                5,
                "step",
                True,
            ),
            (
                {"reasoning_effort": "{{ inputs.value }}"},
                {},
                {"value": True},
                True,
                "step",
                True,
            ),
            (
                {},
                {"reasoning_effort": "{{ inputs.value }}"},
                {"value": ["high"]},
                ["high"],
                "workflow.reasoning_effort",
                True,
            ),
            ({"reasoning_effort": 200000}, {}, {}, 200000, "step", False),
            (
                {},
                {"reasoning_effort": False},
                {},
                False,
                "workflow.reasoning_effort",
                False,
            ),
        ],
        ids=[
            "step-expression-int",
            "step-expression-bool",
            "default-expression-list",
            "unvalidated-step-literal",
            "unvalidated-default-literal",
        ],
    )
    def test_non_string_results_fail_the_step(
        self,
        kind,
        fields,
        defaults,
        inputs,
        value,
        source,
        from_expression,
        project_dir,
        register,
        cli,
    ):
        fake = register(_Translating())
        result = _execute(
            kind, project_dir, fake.key, inputs=inputs, defaults=defaults, **fields
        )

        type_name = type(value).__name__
        advice = (
            f"but its expression resolved to {type_name}; make it resolve to a "
            "string, for example by reading an input declared with type: string."
            if from_expression
            else f"got {type_name}; quote YAML values such as 200000, on, or off."
        )
        assert result.status is StepStatus.FAILED
        assert result.error == (
            f"{LABELS[kind]} step 'ask': 'reasoning_effort' must be a string, "
            f"{advice} (set by {source})"
        )
        assert fake.calls == []
        assert cli.runs == []

    @UNSAFE_VALUES
    def test_unsafe_results_fail_the_step(
        self, kind, value, project_dir, register, cli
    ):
        fake = register(_Translating())
        result = _execute(
            kind,
            project_dir,
            fake.key,
            inputs={"value": value},
            context_size="{{ inputs.value }}",
        )

        assert result.status is StepStatus.FAILED
        assert result.error.startswith(
            f"{LABELS[kind]} step 'ask': 'context_size' must be 1-64 letters"
        )
        assert result.error.endswith(" (set by step)")
        _assert_summarized(result.error, value)
        assert cli.runs == []

    def test_oversized_untrusted_result_is_summarized(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        result = _execute(
            kind,
            project_dir,
            fake.key,
            inputs={"captured": HUGE},
            defaults={"reasoning_effort": "{{ inputs.captured }}"},
        )

        assert result.status is StepStatus.FAILED
        assert result.error.endswith(" (set by workflow.reasoning_effort)")
        _assert_summarized(result.error, HUGE)
        assert cli.runs == []

    @pytest.mark.parametrize("continue_on_error", [True, False])
    def test_rejected_captured_output_stays_out_of_the_error_and_log(
        self, kind, continue_on_error, project_dir, register, cli, after_step
    ):
        """Spec Kit does not print or log captured text, even as a rejected value."""
        fake = register(_Translating())
        cli.stdout = "SECRET-api-key-0123456789 tail"
        steps = [
            _config(kind, id="read", integration=fake.key, capture=True),
            _config(
                kind,
                integration=fake.key,
                reasoning_effort="{{ steps.read.output.stdout }}",
                continue_on_error=continue_on_error,
            ),
            after_step,
        ]
        state = WorkflowEngine(project_dir).execute(_workflow(steps))

        assert state.step_results["read"]["output"]["stdout"] == cli.stdout
        error = state.step_results["ask"]["error"]
        assert error == (
            f"{LABELS[kind]} step 'ask': 'reasoning_effort' must be 1-64 letters, "
            "digits, '.', '_', or '-' starting with a letter or digit, got a "
            f"string of length {len(cli.stdout)}. (set by step)"
        )
        log = (
            project_dir / ".specify" / "workflows" / "runs" / state.run_id / "log.jsonl"
        ).read_text(encoding="utf-8")
        failure = "step_continue_on_error" if continue_on_error else "step_failed"
        events = [json.loads(line) for line in log.splitlines()]
        assert [event["error"] for event in events if event["event"] == failure] == [
            error
        ]
        assert "SECRET" not in log
        assert len(cli.runs) == 1
        assert state.status is (
            RunStatus.COMPLETED if continue_on_error else RunStatus.FAILED
        )
        assert ("after" in state.step_results) is continue_on_error


# -- Unsupported integrations ---------------------------------------------


@KINDS
class TestUnsupportedIntegrations:
    @pytest.mark.parametrize("integration", ["gemini", "docker-agent"])
    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    def test_fails_before_executable_detection(
        self, kind, integration, name, project_dir, no_cli, without_builtin_supporters
    ):
        result = _execute(kind, project_dir, integration, **{name: "high"})

        assert result.status is StepStatus.FAILED
        assert result.error == (
            f"{LABELS[kind]} step 'ask': "
            + UNSUPPORTED.format(key=integration, name=name, supporters=NO_SUPPORTERS)
            + " (set by step)"
        )
        assert result.output["exit_code"] == 1
        assert result.output["dispatched"] is False
        assert result.output[name] == "high"

    def test_names_the_source_of_the_first_rejected_setting(
        self, kind, project_dir, no_cli
    ):
        result = _execute(
            kind,
            project_dir,
            "gemini",
            defaults={"reasoning_effort": "high"},
            context_size="long_context",
        )

        assert result.status is StepStatus.FAILED
        assert "does not support per-step 'reasoning_effort'" in result.error
        assert result.error.endswith(" (set by workflow.reasoning_effort)")

    def test_names_the_source_when_only_one_setting_is_unsupported(
        self, kind, project_dir, register, no_cli
    ):
        fake = register(_EffortOnly())
        result = _execute(
            kind,
            project_dir,
            fake.key,
            defaults={"context_size": "long_context"},
            reasoning_effort="high",
        )

        assert result.status is StepStatus.FAILED
        assert result.error.startswith(
            f"{LABELS[kind]} step 'ask': Integration 'fake-effort-only' does not "
            "support per-step 'context_size'."
        )
        assert result.error.endswith(" (set by workflow.context_size)")
        assert _outputs(result) == {
            "reasoning_effort": "high",
            "context_size": "long_context",
        }

    def test_lists_the_integrations_that_support_it_on_this_path(
        self, kind, project_dir, register, no_cli, without_builtin_supporters
    ):
        register(_Translating())
        register(_CommandOwner())
        result = _execute(kind, project_dir, "gemini", reasoning_effort="high")

        # Only the command step dispatches through dispatch_command.
        supporters = {
            "command": "fake-command-owner, fake-translating",
            "prompt": "fake-translating",
        }[kind]
        assert result.error == (
            f"{LABELS[kind]} step 'ask': "
            + UNSUPPORTED.format(
                key="gemini",
                name="reasoning_effort",
                supporters=f"Integrations that support it: {supporters}.",
            )
            + " (set by step)"
        )


# -- Supported integrations -----------------------------------------------


@KINDS
class TestSupportedIntegrations:
    @pytest.mark.parametrize(
        "fake_type", [_Translating, _Inheriting], ids=["declaring", "inheriting"]
    )
    @pytest.mark.parametrize(
        "settings",
        [
            {"reasoning_effort": "high"},
            {"context_size": "200000"},
            {"reasoning_effort": "xhigh", "context_size": "long_context"},
        ],
        ids=["effort", "context", "both"],
    )
    def test_receives_exactly_the_set_keywords(
        self, kind, fake_type, settings, project_dir, register, cli
    ):
        fake = register(fake_type())
        result = _execute(kind, project_dir, fake.key, **settings)

        assert result.status is StepStatus.COMPLETED, result.error
        assert _received(fake) == settings
        flags = []
        if "reasoning_effort" in settings:
            flags += ["--effort", settings["reasoning_effort"]]
        if "context_size" in settings:
            flags += ["--context", settings["context_size"]]
        assert cli.runs == [[fake.key, "-p", PROMPTS[kind], *flags]]

    @pytest.mark.parametrize("capture", [False, True], ids=["streamed", "captured"])
    def test_settings_compose_with_capture(
        self, kind, capture, project_dir, register, cli
    ):
        fake = register(_Translating())
        result = _execute(
            kind, project_dir, fake.key, reasoning_effort="low", capture=capture
        )

        assert result.status is StepStatus.COMPLETED, result.error
        assert _received(fake) == {"reasoning_effort": "low"}
        assert cli.runs[-1][-2:] == ["--effort", "low"]


def test_command_step_dispatches_through_an_owning_dispatch_command(
    project_dir, register, cli
):
    fake = register(_CommandOwner())
    result = _execute("command", project_dir, fake.key, reasoning_effort="high")

    assert result.status is StepStatus.COMPLETED, result.error
    assert _received(fake) == {"reasoning_effort": "high"}


def test_prompt_step_rejects_support_declared_only_on_dispatch_command(
    project_dir, register, cli
):
    """A prompt is built by ``build_exec_args``, which this fake does not own."""
    fake = register(_CommandOwner())
    result = _execute("prompt", project_dir, fake.key, reasoning_effort="high")

    assert result.status is StepStatus.FAILED
    assert result.error.startswith(
        "Prompt step 'ask': Integration 'fake-command-owner' does not support "
        "per-step 'reasoning_effort'."
    )
    assert fake.calls == []
    assert cli.runs == []


# -- Declarations that are not backed by a translating builder ------------


@pytest.fixture(
    params=[
        "format-base-declaration",
        "legacy-kwargs-override",
        "string-declaration",
        "forwards-to-super",
    ]
)
def untranslated(request, monkeypatch, register):
    """Return ``(key, problem)`` for an integration that would drop a setting."""
    for suffix in ("EXTRA_ARGS", "EXECUTABLE"):
        monkeypatch.delenv(f"SPECKIT_INTEGRATION_GEMINI_{suffix}", raising=False)
    unsupported = "does not support per-step 'reasoning_effort'"
    if request.param in ("format-base-declaration", "forwards-to-super"):
        # Gemini declaring support while TomlIntegration builds its argv.
        monkeypatch.setattr(
            GeminiIntegration,
            "supported_dispatch_settings",
            frozenset(DISPATCH_SETTINGS),
        )
    if request.param == "format-base-declaration":
        return "gemini", unsupported
    if request.param == "forwards-to-super":
        monkeypatch.setattr(
            GeminiIntegration, "build_exec_args", _forward_to_toml_builder
        )
        return "gemini", "does not translate per-step 'reasoning_effort'"
    fake_type = {
        "legacy-kwargs-override": _LegacyKwargsOverride,
        "string-declaration": _StringDeclaration,
    }[request.param]
    return register(fake_type()).key, unsupported


@KINDS
def test_untranslated_declarations_never_dispatch(kind, untranslated, project_dir, cli):
    key, problem = untranslated
    assert _execute(kind, project_dir, key).status is StepStatus.COMPLETED
    cli.runs.clear()

    result = _execute(kind, project_dir, key, reasoning_effort="high")

    assert result.status is StepStatus.FAILED
    assert result.error.startswith(
        f"{LABELS[kind]} step 'ask': Integration {key!r} {problem}."
    )
    assert result.error.endswith(" (set by step)")
    assert result.output["dispatched"] is False
    assert cli.runs == []


# -- Attribution of integration-raised errors -----------------------------


@KINDS
class TestAttribution:
    @pytest.mark.parametrize(
        ("fields", "defaults", "message"),
        [
            (
                {"reasoning_effort": "high"},
                {"context_size": "rejected"},
                "the CLI does not accept this context_size "
                "(set by workflow.context_size)",
            ),
            (
                {"reasoning_effort": "rejected"},
                {"context_size": "long_context"},
                "the CLI does not accept this reasoning_effort (set by step)",
            ),
        ],
        ids=["default-rejected", "step-rejected"],
    )
    def test_validator_value_error_names_the_exact_source(
        self, kind, fields, defaults, message, project_dir, register, cli
    ):
        fake = register(_Validating())
        result = _execute(kind, project_dir, fake.key, defaults=defaults, **fields)

        assert result.status is StepStatus.FAILED
        assert result.error == f"{LABELS[kind]} step 'ask': {message}"
        assert result.output["exit_code"] == 1
        assert result.output["dispatched"] is False
        assert cli.runs == []

    def test_unlabeled_integration_error_lists_every_source(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Unlabeled())
        result = _execute(
            kind,
            project_dir,
            fake.key,
            defaults={"context_size": "long_context"},
            reasoning_effort="high",
        )

        assert result.status is StepStatus.FAILED
        assert result.error == (
            f"{LABELS[kind]} step 'ask': the CLI rejected these settings "
            "(settings: reasoning_effort from step; "
            "context_size from workflow.context_size)"
        )
        assert result.output["dispatched"] is False
        assert cli.runs == []

    @pytest.mark.parametrize("continue_on_error", [True, False])
    @pytest.mark.parametrize(
        ("fake_type", "defaults", "attribution"),
        [
            (
                _Validating,
                {"context_size": "rejected"},
                "(set by workflow.context_size)",
            ),
            (
                _Unlabeled,
                {"context_size": "long_context"},
                "(settings: reasoning_effort from step; "
                "context_size from workflow.context_size)",
            ),
        ],
        ids=["validator", "unlabeled"],
    )
    def test_rejection_in_a_run_fails_only_the_step(
        self,
        kind,
        continue_on_error,
        fake_type,
        defaults,
        attribution,
        project_dir,
        register,
        cli,
        after_step,
    ):
        fake = register(fake_type())
        steps = [
            _config(
                kind,
                integration=fake.key,
                reasoning_effort="high",
                continue_on_error=continue_on_error,
            ),
            after_step,
        ]
        state = WorkflowEngine(project_dir).execute(_workflow(steps, defaults=defaults))

        assert state.step_results["ask"]["status"] == "failed"
        assert state.step_results["ask"]["error"].endswith(f" {attribution}")
        if continue_on_error:
            assert state.status is RunStatus.COMPLETED
            assert state.step_results["after"]["output"] == {"ran": True}
        else:
            assert state.status is RunStatus.FAILED
            assert "after" not in state.step_results
        assert cli.runs == []


# -- Unset invariant ------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "fake_type"),
    [
        ("command", _StrictCommand),
        ("command", _StrictBuilder),
        ("prompt", _StrictBuilder),
    ],
    ids=["command-dispatch-command", "command-base-dispatch-command", "prompt-builder"],
)
@pytest.mark.parametrize(
    ("fields", "defaults"),
    [
        ({}, {}),
        ({"reasoning_effort": None, "context_size": ""}, {"reasoning_effort": ""}),
    ],
    ids=["absent", "null-and-empty"],
)
def test_unset_settings_pass_no_new_keywords(
    kind, fake_type, fields, defaults, project_dir, register, cli
):
    """A strict signature would raise TypeError on any added keyword."""
    fake = register(fake_type())
    result = _execute(kind, project_dir, fake.key, defaults=defaults, **fields)

    assert result.status is StepStatus.COMPLETED, result.error
    assert fake.calls
    assert _outputs(result) == dict.fromkeys(DISPATCH_SETTINGS)


@KINDS
def test_output_keys_are_null_when_dispatch_is_impossible(
    kind, project_dir, register, no_cli
):
    fake = register(_Translating())
    result = _execute(kind, project_dir, fake.key)

    assert result.status is StepStatus.FAILED
    assert "CLI not found" in result.error
    assert _outputs(result) == dict.fromkeys(DISPATCH_SETTINGS)


@pytest.mark.parametrize(
    "fields", [{}, {"reasoning_effort": "high"}], ids=["unset", "set"]
)
def test_prompt_step_still_raises_a_malformed_extra_args_error(
    fields, project_dir, monkeypatch, register, cli
):
    """Only a rejected dispatch setting is turned into a failed prompt step."""
    fake = register(_Translating())
    monkeypatch.setenv("SPECKIT_INTEGRATION_FAKE_TRANSLATING_EXTRA_ARGS", '"open')

    with pytest.raises(ValueError, match="EXTRA_ARGS is not parseable") as raised:
        _execute("prompt", project_dir, fake.key, **fields)

    assert not isinstance(raised.value, DispatchSettingsError)
    assert cli.runs == []


# -- Native CLI rejection -------------------------------------------------


@KINDS
class TestNativeRejection:
    def test_captured_stderr_stays_in_the_output(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        cli.returncode = 2
        cli.stderr = "error: unknown reasoning effort 'turbo'"
        result = _execute(
            kind, project_dir, fake.key, reasoning_effort="turbo", capture=True
        )

        assert result.status is StepStatus.FAILED
        assert result.error == f"{LABELS[kind]} exited with code 2"
        assert result.output["stderr"] == cli.stderr
        assert result.output["reasoning_effort"] == "turbo"

    def test_streamed_rejection_reports_a_generic_error(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        cli.returncode = 2
        result = _execute(kind, project_dir, fake.key, reasoning_effort="turbo")

        assert result.status is StepStatus.FAILED
        assert result.error == f"{LABELS[kind]} exited with code 2"
        assert result.output["stderr"] == ""

    @pytest.mark.parametrize("continue_on_error", [True, False])
    @pytest.mark.parametrize("capture", [True, False], ids=["captured", "streamed"])
    def test_rejection_in_a_run_keeps_stderr_out_of_the_error_and_log(
        self, kind, capture, continue_on_error, project_dir, register, cli, after_step
    ):
        fake = register(_Translating())
        cli.returncode = 2
        cli.stderr = "error: unknown reasoning effort 'turbo'"
        steps = [
            _config(
                kind,
                integration=fake.key,
                reasoning_effort="turbo",
                capture=capture,
                continue_on_error=continue_on_error,
            ),
            after_step,
        ]
        state = WorkflowEngine(project_dir).execute(_workflow(steps))

        ask = state.step_results["ask"]
        assert ask["error"] == f"{LABELS[kind]} exited with code 2"
        assert ask["output"]["stderr"] == (cli.stderr if capture else "")
        log = (
            project_dir / ".specify" / "workflows" / "runs" / state.run_id / "log.jsonl"
        ).read_text(encoding="utf-8")
        assert "unknown reasoning effort" not in log
        assert state.status is (
            RunStatus.COMPLETED if continue_on_error else RunStatus.FAILED
        )
        assert ("after" in state.step_results) is continue_on_error


# -- Workflow defaults and engine wiring ----------------------------------

_PROMPT = {"id": "ask", "type": "prompt", "prompt": "hi"}


class TestWorkflowDefaults:
    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    @pytest.mark.parametrize(
        "value", [None, "", "high", "200000", "{{ inputs.effort }}"]
    )
    def test_valid_defaults_pass(self, name, value):
        definition = _workflow([_PROMPT], defaults={name: value})

        assert validate_workflow(definition) == []
        assert getattr(definition, f"default_{name}") == value

    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    @pytest.mark.parametrize("value", [200000, True, ["token=SECRET"]])
    def test_non_string_defaults_are_rejected_without_echoing_them(
        self, name, value
    ):
        errors = validate_workflow(_workflow([_PROMPT], defaults={name: value}))

        assert errors == [dispatch_setting_value_error(f"workflow.{name}", value)]
        assert errors[0].startswith(
            f"'workflow.{name}' must be a string, got {type(value).__name__}"
        )
        assert "quote YAML values" in errors[0]
        assert "SECRET" not in errors[0]

    @pytest.mark.parametrize("name", DISPATCH_SETTINGS)
    @UNSAFE_VALUES
    def test_unsafe_default_literals_are_rejected(self, name, value):
        errors = validate_workflow(_workflow([_PROMPT], defaults={name: value}))

        assert len(errors) == 1
        assert errors[0].startswith(f"'workflow.{name}' must be 1-64 letters")
        _assert_summarized(errors[0], value)

    def test_oversized_default_is_summarized(self):
        (error,) = validate_workflow(
            _workflow([_PROMPT], defaults={"context_size": HUGE})
        )

        _assert_summarized(error, HUGE)

    def test_run_rejects_an_invalid_default_before_any_step(
        self, project_dir, register, cli
    ):
        fake = register(_Translating())
        definition = _workflow(
            [{**_PROMPT, "integration": fake.key}],
            defaults={"reasoning_effort": "high effort"},
        )

        with pytest.raises(ValueError, match=r"'workflow\.reasoning_effort' must be"):
            WorkflowEngine(project_dir).execute(definition)
        assert fake.calls == []


@KINDS
class TestEngineWiring:
    DEFAULTS = {"reasoning_effort": "high", "context_size": "long_context"}

    def test_run_passes_workflow_defaults_and_records_them(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        definition = _workflow(
            [_config(kind, integration=fake.key)], defaults=self.DEFAULTS
        )
        state = WorkflowEngine(project_dir).execute(definition)

        assert state.status is RunStatus.COMPLETED, state.error
        assert _received(fake) == self.DEFAULTS
        assert state.step_results["ask"]["output"]["reasoning_effort"] == "high"
        assert state.step_results["ask"]["output"]["context_size"] == "long_context"

    def test_unset_output_keys_are_null_and_not_recorded_at_top_level(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        state = WorkflowEngine(project_dir).execute(
            _workflow([_config(kind, integration=fake.key)])
        )

        assert state.status is RunStatus.COMPLETED, state.error
        result = state.step_results["ask"]
        assert {name: result["output"][name] for name in DISPATCH_SETTINGS} == (
            dict.fromkeys(DISPATCH_SETTINGS)
        )
        assert not set(DISPATCH_SETTINGS) & set(result)
        assert _received(fake) == {}

    def test_resume_passes_workflow_defaults(self, kind, project_dir, register, cli):
        fake = register(_Translating())
        engine = WorkflowEngine(project_dir)
        cli.returncode = 1
        state = engine.execute(
            _workflow([_config(kind, integration=fake.key)], defaults=self.DEFAULTS)
        )
        assert state.status is RunStatus.FAILED
        fake.calls.clear()

        cli.returncode = 0
        resumed = engine.resume(state.run_id)

        assert resumed.status is RunStatus.COMPLETED, resumed.error
        assert _received(fake) == self.DEFAULTS
        assert len(cli.runs) == 2

    def test_resume_re_resolves_settings_from_new_inputs(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        engine = WorkflowEngine(project_dir)
        step = _config(
            kind, integration=fake.key, reasoning_effort="{{ inputs.effort }}"
        )
        definition = _workflow(
            [step], inputs={"effort": {"type": "string", "default": "low"}}
        )
        cli.returncode = 1
        state = engine.execute(definition)
        assert state.status is RunStatus.FAILED
        assert _received(fake) == {"reasoning_effort": "low"}

        cli.returncode = 0
        resumed = engine.resume(state.run_id, {"effort": "high"})

        assert resumed.status is RunStatus.COMPLETED, resumed.error
        assert _received(fake) == {"reasoning_effort": "high"}
        assert resumed.step_results["ask"]["output"]["reasoning_effort"] == "high"

    def test_number_input_expression_fails_with_expression_advice(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        step = _config(kind, integration=fake.key, context_size="{{ inputs.window }}")
        definition = _workflow(
            [step], inputs={"window": {"type": "number", "default": 200000}}
        )

        state = WorkflowEngine(project_dir).execute(definition)

        assert state.status is RunStatus.FAILED
        assert state.step_results["ask"]["error"] == (
            f"{LABELS[kind]} step 'ask': 'context_size' must be a string, but its "
            "expression resolved to int; make it resolve to a string, for example "
            "by reading an input declared with type: string. (set by step)"
        )
        assert fake.calls == []
        assert cli.runs == []

    def test_string_input_expression_passes_a_number_through(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        step = _config(kind, integration=fake.key, context_size="{{ inputs.window }}")
        definition = _workflow(
            [step], inputs={"window": {"type": "string", "default": "200000"}}
        )

        state = WorkflowEngine(project_dir).execute(definition)

        assert state.status is RunStatus.COMPLETED, state.error
        assert _received(fake) == {"context_size": "200000"}

    @pytest.mark.parametrize(
        ("child_defaults", "expected"),
        [({"reasoning_effort": "low"}, {"reasoning_effort": "low"}), ({}, {})],
        ids=["own-defaults", "no-defaults"],
    )
    def test_called_workflow_uses_only_its_own_defaults(
        self, kind, child_defaults, expected, project_dir, register, cli
    ):
        fake = register(_Translating())
        _install(
            project_dir,
            _workflow(
                [_config(kind, integration=fake.key)],
                defaults=child_defaults,
                workflow_id="child",
            ),
        )
        parent = _workflow(
            [{"id": "call", "type": "workflow", "workflow": "child"}],
            defaults=self.DEFAULTS,
        )
        state = WorkflowEngine(project_dir).execute(parent)

        assert state.status is RunStatus.COMPLETED, state.error
        assert len(cli.runs) == 1
        assert _received(fake) == expected

    def test_fan_out_items_inherit_workflow_defaults(
        self, kind, project_dir, register, cli
    ):
        fake = register(_Translating())
        definition = _workflow(
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "step": _config(kind, integration=fake.key),
                }
            ],
            defaults=self.DEFAULTS,
        )
        state = WorkflowEngine(project_dir).execute(definition)

        assert state.status is RunStatus.COMPLETED, state.error
        assert [run[-4:] for run in cli.runs] == [
            ["--effort", "high", "--context", "long_context"]
        ] * 2


def test_step_context_positional_construction_is_unchanged():
    context = StepContext(
        {"spec": "x"},
        {},
        None,
        False,
        {},
        "claude",
        "sonnet",
        {"max_tokens": 1},
        "/project",
        "run-1",
        True,
        "/workflows/wf",
    )

    assert context.project_root == "/project"
    assert context.run_id == "run-1"
    assert context.is_resume is True
    assert context.workflow_dir == "/workflows/wf"
    assert context.default_reasoning_effort is None
    assert context.default_context_size is None
    names = [field.name for field in dataclasses.fields(StepContext)]
    assert names[8] == "project_root"
    assert names[-2:] == ["default_reasoning_effort", "default_context_size"]
