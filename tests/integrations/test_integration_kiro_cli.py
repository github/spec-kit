"""Tests for KiroCliIntegration."""

import os
import re

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.kiro_cli import _KIRO_ARG_FALLBACK, format_kiro_command_name
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests


# Regex shapes that indicate a value is a placeholder token, not prose.
# Covers Bash ($VAR, ${VAR}, ${VAR:-default}), Mustache/Handlebars/Jinja
# ({{var}}, {{{var}}}), Liquid/Jinja control ({% ... %}), Python str.format /
# .NET ({var}, {0}), angle-bracket (<var>), and Windows-style (%VAR%).
# Anchored to the FULL STRING so legitimate prose mentioning a placeholder
# (e.g. "the {{magic}} of placeholders") is not flagged. The Liquid pattern
# is anchored to the START so multi-tag templates fire while mid-sentence
# {%-quotation does not.
_PLACEHOLDER_TOKEN_PATTERNS = (
    re.compile(r"^\$\w+$"),                                  # $ARGUMENTS, $args
    re.compile(r"^\$\{\w+(?:[:\-+?][^}]*)?\}$"),             # ${ARGS}, ${ARGS:-default}
    re.compile(r"^\{\{\{?\s*\w+(\s*[|.][^}]*)?\s*\}?\}\}$"), # {{var}} {{{var}}} {{x|y}}
    re.compile(r"^\{%"),                                     # {% if x %}{{ x }}{% endif %}
    re.compile(r"^<\w+>$"),                                  # <args>
    re.compile(r"^%\w+%$"),                                  # %USERNAME%
    re.compile(r"^\{(?:\d+|[a-zA-Z_]\w*)(?:[.\[][^}]*)?(?:![rsa])?(?::[^}]*)?\}$"),  # {0}, {var}, {0:>5}
)


def _looks_like_placeholder_token(value: str) -> bool:
    """Return True if *value* matches a known placeholder-token shape."""
    if not value:
        return False
    return any(p.search(value) for p in _PLACEHOLDER_TOKEN_PATTERNS)


class TestKiroCliIntegration(MarkdownIntegrationTests):
    KEY = "kiro-cli"
    FOLDER = ".kiro/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".kiro/prompts"

    def test_declares_multi_install_safe(self):
        assert get_integration(self.KEY).multi_install_safe is True

    @pytest.mark.parametrize(
        "cmd_name, expected",
        [
            ("plan", "speckit-plan"),
            ("speckit.plan", "speckit-plan"),
            ("speckit.git.commit", "speckit-git-commit"),
            ("speckit-plan", "speckit-plan"),
        ],
    )
    def test_format_kiro_command_name(self, cmd_name, expected):
        assert format_kiro_command_name(cmd_name) == expected

    def test_prompts_and_invocations_are_hyphenated(self):
        """Kiro CLI rejects ``/speckit.plan`` as an unrecognized slash command
        but runs ``/speckit-plan`` from ``.kiro/prompts/speckit-plan.md``."""
        i = get_integration(self.KEY)
        assert i.command_filename("plan") == "speckit-plan.md"
        assert i.build_command_invocation("plan") == "/speckit-plan"
        assert (
            i.build_command_invocation("speckit.git.commit", "now")
            == "/speckit-git-commit now"
        )
        assert i.invoke_separator == "-"
        assert i.registrar_config["invoke_separator"] == "-"
        # Extension and preset prompts get the same names via the registrar.
        assert i.registrar_config["format_name"] is format_kiro_command_name

    def test_command_step_dispatches_hyphenated_prompt(self, tmp_path):
        """A workflow ``command: speckit.constitution`` step reaches Kiro CLI
        as ``/speckit-constitution`` through ``chat --no-interactive``."""
        from unittest.mock import MagicMock, patch

        from specify_cli.workflows.base import StepContext, StepStatus
        from specify_cli.workflows.step.command import CommandStep

        ctx = StepContext(
            inputs={}, default_integration=self.KEY, project_root=str(tmp_path)
        )
        config = {"id": "constitution", "command": "speckit.constitution"}
        done = MagicMock(returncode=0, stdout="", stderr="")

        with patch("specify_cli.workflows.step.command.shutil.which", return_value="/usr/local/bin/kiro-cli"), \
             patch("specify_cli.integrations.base.shutil.which", return_value="/usr/local/bin/kiro-cli"), \
             patch("subprocess.run", return_value=done) as mock_run:
            result = CommandStep().execute(config, ctx)

        assert result.status == StepStatus.COMPLETED
        assert mock_run.call_args[0][0] == [
            "/usr/local/bin/kiro-cli",
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            "/speckit-constitution",
        ]

    def test_post_process_adds_hook_note_and_rewrites_handoffs(self):
        i = get_integration(self.KEY)
        content = (
            "---\nhandoffs:\n  - label: Plan\n    agent: speckit.plan\n---\n"
            "When normalizing table names, replace dots with underscores.\n"
            "- For each executable hook, output the following:\n"
        )
        processed = i.post_process_command_content(content)
        assert "    agent: speckit-plan\n" in processed
        assert "`/speckit-git-commit`" in processed
        assert i.post_process_command_content(processed) == processed

    def test_build_exec_args_uses_headless_chat(self):
        """``kiro-cli -p`` exits 2 (``unexpected argument '-p'``).

        Kiro CLI runs one prompt through ``chat --no-interactive``, and in
        that mode it denies every tool call unless ``--trust-all-tools`` is
        set, while still exiting 0.
        """
        args = get_integration(self.KEY).build_exec_args(
            "/speckit-plan", output_json=False
        )

        assert args == [
            "kiro-cli",
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            "/speckit-plan",
        ]
        assert "-p" not in args

    def test_build_exec_args_forwards_model_and_stream_json(self):
        """Kiro has no ``json`` output format; structured output is ``stream-json``."""
        args = get_integration(self.KEY).build_exec_args(
            "/speckit-plan", model="claude-sonnet-4.5", output_json=True
        )

        assert args == [
            "kiro-cli",
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            "--model",
            "claude-sonnet-4.5",
            "--output-format",
            "stream-json",
            "/speckit-plan",
        ]

    def test_build_exec_args_applies_extra_args_before_prompt(self, monkeypatch):
        """Operator-injected flags reach ``chat`` ahead of the positional prompt."""
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_KIRO_CLI_EXTRA_ARGS", "--agent reviewer"
        )
        args = get_integration(self.KEY).build_exec_args(
            "/speckit-plan", output_json=False
        )

        assert args == [
            "kiro-cli",
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            "--agent",
            "reviewer",
            "/speckit-plan",
        ]

    def test_registrar_config(self):
        """Override base assertion: kiro-cli uses a prose fallback for args
        because Kiro CLI file-based prompts do not natively substitute
        ``$ARGUMENTS`` (see issue #1926 / kirodotdev/Kiro#4141). The
        regression-guard load is carried by the two layer tests below
        (exact-fallback + placeholder-shape rejection)."""
        i = get_integration(self.KEY)
        assert i.registrar_config["dir"] == self.REGISTRAR_DIR
        assert i.registrar_config["format"] == "markdown"
        assert i.registrar_config["extension"] == ".md"

    def test_registrar_config_args_is_exact_prose_fallback(self):
        """Layer 1 — pin the exact fallback so wording drift requires a
        deliberate paired commit (production constant + test update)."""
        i = get_integration(self.KEY)
        assert i.registrar_config["args"] == _KIRO_ARG_FALLBACK, (
            f"args drifted from the pinned fallback constant. "
            f"Got: {i.registrar_config['args']!r}; expected: {_KIRO_ARG_FALLBACK!r}. "
            f"If the wording change is intentional, update _KIRO_ARG_FALLBACK and "
            f"this test together."
        )

    def test_registrar_config_args_does_not_look_like_a_placeholder_token(self):
        """Layer 2 — independent regression guard: even if someone bypasses
        layer-1 by changing both constant and test, the value still must not
        look like ANY placeholder token shape ($X, ${X}, {{X}}, <X>, %X%, {0},
        {% %}). Catches the class of regression Copilot called out: a swap
        from $ARGUMENTS to $INPUT or {{userMessage}} would fail this test
        even if it accidentally passed layer 1."""
        i = get_integration(self.KEY)
        args = i.registrar_config["args"]
        assert not _looks_like_placeholder_token(args), (
            f"registrar_config['args'] = {args!r} matches a known placeholder-"
            f"token shape — Kiro CLI does not substitute placeholders so this "
            f"would reach the model verbatim and break the prompt (issue #1926). "
            f"Use a prose fallback instead."
        )

    def test_rendered_prompts_do_not_contain_raw_arguments(self, tmp_path):
        """Rendered Kiro prompt files must NOT contain the raw ``$ARGUMENTS``
        token — Kiro CLI does not substitute it, so the literal would reach
        the model and break the prompt (issue #1926)."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        prompts_dir = tmp_path / self.REGISTRAR_DIR
        rendered = list(prompts_dir.glob("*.md"))
        assert rendered, "expected at least one rendered prompt file"

        offenders = [
            p.name for p in rendered if "$ARGUMENTS" in p.read_text(encoding="utf-8")
        ]
        assert offenders == [], (
            f"these rendered prompts still contain the raw $ARGUMENTS token: {offenders}"
        )

    def test_rendered_prompts_contain_kiro_arg_placeholder(self, tmp_path):
        """The chosen kiro-cli args fallback string must end up in at least
        one rendered prompt (proves substitution actually fired, not just
        that $ARGUMENTS was removed). Imports the fallback constant directly
        instead of reading the field back so the test stays independent of
        the integration's own config — even if the registrar_config['args']
        regresses, this test still verifies the FALLBACK STRING is in the
        rendered output."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        expected = _KIRO_ARG_FALLBACK
        prompts_dir = tmp_path / self.REGISTRAR_DIR
        contents = "\n".join(
            p.read_text(encoding="utf-8") for p in prompts_dir.glob("*.md")
        )
        assert expected in contents, (
            f"none of the rendered prompts contain the configured args fallback "
            f"({expected!r})"
        )

    # -- Overrides for MarkdownIntegrationTests (hyphenated prompt names) --

    def test_setup_creates_files(self, tmp_path):
        i = get_integration(self.KEY)
        created = i.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path))
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert cmd_files
        for f in cmd_files:
            assert f.exists()
            assert f.name.startswith("speckit-")
            assert f.name.endswith(".md")

        specify = (tmp_path / self.REGISTRAR_DIR / "speckit-specify.md").read_text(
            encoding="utf-8"
        )
        assert "/speckit-plan" in specify
        assert "/speckit.plan" not in specify

    def test_integration_flag_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"int-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY, "--script", "sh",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init --integration {self.KEY} failed: {result.output}"
        cmd_dir = get_integration(self.KEY).commands_dest(project)
        assert sorted(cmd_dir.glob("speckit-*.md"))
        assert not sorted(cmd_dir.glob("speckit.*"))

    def _expected_files(self, script_variant: str) -> list[str]:
        # Kiro prompts are hyphenated, so remap the base mixin's
        # ``speckit.<stem>.md`` expectations under the prompts dir.
        prefix = f"{self.REGISTRAR_DIR}/speckit."
        return sorted(
            f"{self.REGISTRAR_DIR}/speckit-{f[len(prefix):]}" if f.startswith(prefix) else f
            for f in super()._expected_files(script_variant)
        )


class TestKiroIntegration:
    """--integration kiro-cli creates expected files."""

    def test_integration_kiro_cli_creates_files(self, tmp_path):
        """--integration kiro-cli should create files in .kiro/prompts."""
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "kiro-proj"
        target.mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(target)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--integration", "kiro-cli",
                "--ignore-agent-tools", "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert (target / ".kiro" / "prompts" / "speckit-plan.md").exists()
