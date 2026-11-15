"""Tests for CodexIntegration."""

import shutil
import subprocess
import tomllib

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.base import (
    DispatchSettingsError,
    effective_dispatch_settings,
)
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.workflows.base import StepContext, StepStatus
from specify_cli.workflows.step.command import CommandStep
from specify_cli.workflows.step.prompt import PromptStep

from .test_integration_base_skills import SkillsIntegrationTests


class TestCodexIntegration(SkillsIntegrationTests):
    KEY = "codex"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"

class TestCodexInitFlow:
    """--integration codex creates expected files."""

    def test_integration_codex_creates_skills(self, tmp_path):
        """--integration codex should create skills in .agents/skills."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--integration", "codex", "--ignore-agent-tools", "--script", "sh"])

        assert result.exit_code == 0, f"init --integration codex failed: {result.output}"
        assert (target / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_plan_skill_has_no_context_placeholder(self, tmp_path):
        """The core plan skill must not carry a context-file placeholder —
        agent context files are owned by the opt-in agent-context extension."""
        target = tmp_path / "test-proj"
        target.mkdir()

        integration = get_integration("codex")
        manifest = IntegrationManifest("codex", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".agents" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "__CONTEXT_FILE__" not in content

    def test_plan_skill_ignores_extension_config(self, tmp_path):
        """The extension config must not influence rendered commands: the CLI
        no longer reads any context-file metadata when rendering."""
        import yaml

        target = tmp_path / "test-proj"
        target.mkdir()
        ext_cfg = (
            target
            / ".specify"
            / "extensions"
            / "agent-context"
            / "agent-context-config.yml"
        )
        ext_cfg.parent.mkdir(parents=True, exist_ok=True)
        ext_cfg.write_text(
            yaml.safe_dump(
                {
                    "context_file": "FROM_CONFIG.md",
                    "context_files": ["FROM_CONFIG.md", "ALSO_CONFIG.md"],
                }
            ),
            encoding="utf-8",
        )

        integration = get_integration("codex")
        manifest = IntegrationManifest("codex", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".agents" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "FROM_CONFIG.md" not in content
        assert "ALSO_CONFIG.md" not in content
        assert "__CONTEXT_FILE__" not in content


class TestCodexHookCommandNote:
    """Verify dot-to-hyphen normalization note is injected in hook sections.

    Hook commands in ``extensions.yml`` use dotted ids like
    ``speckit.git.commit`` but Codex skills are named with hyphens
    (``speckit-git-commit``). Without this note, Codex emits
    ``/speckit.git.commit``, which does not resolve.
    """

    def test_hook_note_injected_in_skills_with_hooks(self, tmp_path):
        """Skills that have hook sections should get the normalization note."""
        i = get_integration("codex")
        m = IntegrationManifest("codex", tmp_path)
        i.setup(tmp_path, m, script_type="sh")
        specify_skill = tmp_path / ".agents/skills/speckit-specify/SKILL.md"
        assert specify_skill.exists()
        content = specify_skill.read_text(encoding="utf-8")
        assert "replace dots" in content, (
            "speckit-specify should have dot-to-hyphen hook note"
        )
        assert "constructing command invocations" in content
        assert "constructing slash commands" not in content

    def test_hook_note_not_in_skills_without_hooks(self):
        """Skills without hook sections should not get the note."""
        from specify_cli.integrations.codex import CodexIntegration

        content = "---\nname: test\ndescription: test\n---\n\nNo hooks here.\n"
        result = CodexIntegration._inject_hook_command_note(content)
        assert "replace dots" not in result

    def test_hook_note_idempotent(self):
        """Injecting the note twice should not duplicate it."""
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        once = CodexIntegration._inject_hook_command_note(content)
        twice = CodexIntegration._inject_hook_command_note(once)
        assert once == twice, "Hook note injection should be idempotent"

    def test_hook_note_fills_missing_repeated_instructions(self):
        """Already-noted hook sections should not suppress later sections."""
        from specify_cli.integrations.base import _HOOK_COMMAND_NOTE
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            f"{_HOOK_COMMAND_NOTE}"
            "- For each executable hook, output the following based on its flag:\n"
            "\n"
            "  - For each executable hook, output the following based on its flag:\n"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        assert result.count("replace dots (`.`) with hyphens") == 2

    def test_hook_note_not_suppressed_by_unrelated_phrase(self):
        """Unrelated text should not trip the hook-note idempotence guard."""
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            "This paragraph says replace dots in a different context.\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        assert "This paragraph says replace dots in a different context." in result
        assert result.count("replace dots (`.`) with hyphens") == 1

    def test_hook_note_preserves_indentation(self):
        """The injected note should match the indentation of the target line."""
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            "   - For each executable hook, output the following\n"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        lines = result.splitlines()
        note_line = [line for line in lines if "replace dots" in line][0]
        assert note_line.startswith("   "), "Note should preserve indentation"

    def test_hook_note_when_instruction_is_final_line_without_newline(self):
        """Note must not collapse onto the instruction line when the file
        ends without a trailing newline and the preceding line is not blank.
        """
        from specify_cli.integrations.codex import CodexIntegration

        # No blank line before the instruction and no trailing newline:
        # this is the case where the captured ``eol`` is empty and the
        # captured indent is also empty, so a missing line separator would
        # cause the note and instruction to collapse onto one line.
        content = (
            "---\nname: test\n---\n"
            "Body line\n"
            "- For each executable hook, output the following"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        lines = result.splitlines()
        note_line_idx = next(
            i for i, line in enumerate(lines) if "replace dots" in line
        )
        instruction_line_idx = next(
            i for i, line in enumerate(lines)
            if line.lstrip().startswith("- For each executable hook")
        )
        assert note_line_idx < instruction_line_idx, (
            "Note must appear before the instruction"
        )
        assert "For each executable hook" not in lines[note_line_idx], (
            "Note and instruction must not be on the same line"
        )


_COMMAND_STEP = (CommandStep, {"command": "speckit.plan", "input": {"args": "body"}})
_PROMPT_STEP = (PromptStep, {"type": "prompt", "prompt": "Summarise"})
# Captured agent output that passes the host's value pattern, so only Codex's
# own rule rejects it.
_SECRET_OUTPUT = "FAKEsecret0123456789"


class TestCodexDispatchSettings:
    """Per-step ``reasoning_effort`` and ``context_size`` (#4916)."""

    _CODEX_RULE = "positive integer token count (model_context_window)"

    @pytest.fixture
    def runs(self, monkeypatch):
        calls = []

        def fake_run(args, **kwargs):
            calls.append(list(args))
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        return calls

    @pytest.mark.parametrize("via", ["dispatch_command", "build_exec_args"])
    def test_build_exec_args_declares_both_settings(self, via):
        assert effective_dispatch_settings(
            get_integration("codex"), via=via
        ) == frozenset({"reasoning_effort", "context_size"})

    def test_settings_become_config_overrides_after_model(self):
        args = get_integration("codex").build_exec_args(
            "do it", model="gpt-5", reasoning_effort="high", context_size="200000"
        )
        assert args == [
            "codex", "exec", "do it",
            "--model", "gpt-5",
            "-c", 'model_reasoning_effort="high"',
            "-c", "model_context_window=200000",
            "--json",
        ]

    @pytest.mark.parametrize("value", ["high", "xhigh", "v2.max-ultra_1"])
    def test_reasoning_effort_is_embedded_as_a_toml_string(self, value):
        args = get_integration("codex").build_exec_args(
            "do it", reasoning_effort=value, output_json=False
        )
        assert args[-2] == "-c"
        assert tomllib.loads(args[-1]) == {"model_reasoning_effort": value}

    def test_reasoning_effort_values_are_left_to_codex(self):
        args = get_integration("codex").build_exec_args(
            "do it", reasoning_effort="bogus"
        )
        assert args[-3:] == ["-c", 'model_reasoning_effort="bogus"', "--json"]

    @pytest.mark.parametrize("value", ["1", "200000", "9223372036854775807"])
    def test_context_size_accepts_canonical_i64_token_counts(self, value):
        args = get_integration("codex").build_exec_args(
            "do it", context_size=value, output_json=False
        )
        assert args[-2:] == ["-c", f"model_context_window={value}"]
        assert tomllib.loads(args[-1]) == {"model_context_window": int(value)}

    @pytest.mark.parametrize(
        ("value", "reason"),
        [
            ("0", _CODEX_RULE),
            ("01", _CODEX_RULE),
            ("9223372036854775808", _CODEX_RULE),
            ("1e5", _CODEX_RULE),
            ("long_context", _CODEX_RULE),
            ("-5", "starting with a letter or digit"),
        ],
        ids=["zero", "leading-zero", "above-i64", "exponent", "tier-name", "negative"],
    )
    def test_context_size_rejects_other_values(self, value, reason):
        with pytest.raises(DispatchSettingsError) as excinfo:
            get_integration("codex").build_exec_args("do it", context_size=value)
        assert excinfo.value.setting == "context_size"
        assert reason in str(excinfo.value)

    def test_rejected_context_size_is_not_echoed(self):
        with pytest.raises(DispatchSettingsError) as excinfo:
            get_integration("codex").build_exec_args(
                "do it", context_size=_SECRET_OUTPUT
            )
        message = str(excinfo.value)
        assert _SECRET_OUTPUT not in message
        assert self._CODEX_RULE in message

    def test_unset_settings_leave_argv_unchanged(self):
        codex = get_integration("codex")
        baseline = ["codex", "exec", "do it", "--model", "gpt-5", "--json"]
        assert codex.build_exec_args("do it", model="gpt-5") == baseline
        assert codex.build_exec_args(
            "do it", model="gpt-5", reasoning_effort=None, context_size=None
        ) == baseline

    def test_dispatch_command_forwards_settings(self, runs):
        get_integration("codex").dispatch_command(
            "speckit.plan",
            "body",
            stream=False,
            reasoning_effort="low",
            context_size="128000",
        )
        (args,) = runs
        assert args[1:] == [
            "exec", "$speckit-plan body",
            "-c", 'model_reasoning_effort="low"',
            "-c", "model_context_window=128000",
            "--json",
        ]

    def test_overrides_follow_extra_args(self, monkeypatch, runs):
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS", "--sandbox workspace-write"
        )
        codex = get_integration("codex")
        settings = {"reasoning_effort": "high", "context_size": "200000"}
        tail = [
            "--model", "gpt-5",
            "-c", 'model_reasoning_effort="high"',
            "-c", "model_context_window=200000",
            "--json",
        ]
        assert codex.build_exec_args("do it", model="gpt-5", **settings) == [
            "codex", "exec", "do it", "--sandbox", "workspace-write", *tail
        ]
        codex.dispatch_command(
            "speckit.plan", "body", model="gpt-5", stream=False, **settings
        )
        (args,) = runs
        assert args[1:] == [
            "exec", "$speckit-plan body", "--sandbox", "workspace-write", *tail
        ]

    def test_dispatch_command_rejects_before_the_cli_starts(self, runs):
        with pytest.raises(DispatchSettingsError) as excinfo:
            get_integration("codex").dispatch_command(
                "speckit.plan", stream=False, context_size="long_context"
            )
        assert excinfo.value.setting == "context_size"
        assert self._CODEX_RULE in str(excinfo.value)
        assert runs == []

    @staticmethod
    def _execute(monkeypatch, tmp_path, step, config, *, steps=None, **settings):
        monkeypatch.setattr(shutil, "which", lambda name, *a, **k: f"/bin/{name}")
        return step().execute(
            {"id": "ask", **config, **settings},
            StepContext(
                default_integration="codex",
                project_root=str(tmp_path),
                steps=steps or {},
            ),
        )

    @pytest.mark.parametrize(
        ("step", "config", "prompt"),
        [(*_COMMAND_STEP, "$speckit-plan body"), (*_PROMPT_STEP, "Summarise")],
        ids=["command", "prompt"],
    )
    def test_workflow_steps_dispatch_settings(
        self, monkeypatch, tmp_path, runs, step, config, prompt
    ):
        result = self._execute(
            monkeypatch,
            tmp_path,
            step,
            config,
            reasoning_effort="high",
            context_size="200000",
        )
        assert result.status == StepStatus.COMPLETED, result.error
        assert result.output["reasoning_effort"] == "high"
        assert result.output["context_size"] == "200000"
        (args,) = runs
        assert args[1:] == [
            "exec", prompt,
            "-c", 'model_reasoning_effort="high"',
            "-c", "model_context_window=200000",
        ]

    @pytest.mark.parametrize(
        ("step", "config"), [_COMMAND_STEP, _PROMPT_STEP], ids=["command", "prompt"]
    )
    def test_workflow_steps_reject_invalid_context_size(
        self, monkeypatch, tmp_path, runs, step, config
    ):
        result = self._execute(
            monkeypatch, tmp_path, step, config, context_size="long_context"
        )
        assert result.status == StepStatus.FAILED
        assert result.output["dispatched"] is False
        assert self._CODEX_RULE in result.error
        assert runs == []

    @pytest.mark.parametrize(
        ("step", "config"), [_COMMAND_STEP, _PROMPT_STEP], ids=["command", "prompt"]
    )
    def test_workflow_steps_do_not_echo_captured_output(
        self, monkeypatch, tmp_path, runs, step, config
    ):
        result = self._execute(
            monkeypatch,
            tmp_path,
            step,
            config,
            steps={"probe": {"output": {"stdout": _SECRET_OUTPUT}}},
            context_size="{{ steps.probe.output.stdout }}",
        )
        assert result.status == StepStatus.FAILED
        assert _SECRET_OUTPUT not in result.error
        assert self._CODEX_RULE in result.error
        assert result.error.endswith(" (set by step)")
        assert runs == []
