"""Tests for AmpIntegration."""

from specify_cli.integrations import get_integration

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestAmpIntegration(MarkdownIntegrationTests):
    KEY = "amp"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".agents/commands"

    def test_build_exec_args_uses_execute_mode(self):
        """Amp dispatches through execute mode, not the inherited `-p`.

        The Amp CLI has no `-p`/`--prompt` flag; passing one aborts with
        `error: unknown option '-p'` before the agent runs (#4580).
        """
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.specify build a login page",
            output_json=False,
        )

        assert args == [
            "amp",
            "--execute",
            "/speckit.specify build a login page",
        ]
        assert "-p" not in args

    def test_build_exec_args_requests_stream_json(self):
        """`--stream-json` is Amp's structured-output flag, used with --execute."""
        integration = get_integration(self.KEY)

        args = integration.build_exec_args("/speckit.plan add OAuth", output_json=True)

        assert args == [
            "amp",
            "--execute",
            "/speckit.plan add OAuth",
            "--stream-json",
        ]
        assert "--output-format" not in args

    def test_build_exec_args_omits_model_flag(self):
        """Amp exposes no model-selection flag, so `model` is not forwarded.

        `-m/--mode` takes an agent mode (low/medium/high/ultra), not a model
        identifier, so remapping the caller's model onto it would be wrong.
        """
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "explain this repository",
            model="gpt-5",
            output_json=False,
        )

        assert args == ["amp", "--execute", "explain this repository"]
        assert "--model" not in args
        assert "-m" not in args
        assert "gpt-5" not in args

    def test_build_exec_args_applies_extra_args_before_execute(self, monkeypatch):
        """Operator-injected flags precede `--execute` so they stay global.

        `--execute [message]` takes the prompt as an optional inline value, so
        injecting between the flag and the prompt would consume the prompt.
        """
        monkeypatch.setenv("SPECKIT_INTEGRATION_AMP_EXTRA_ARGS", "--no-notifications")
        integration = get_integration(self.KEY)

        args = integration.build_exec_args("check the build", output_json=True)

        assert args == [
            "amp",
            "--no-notifications",
            "--execute",
            "check the build",
            "--stream-json",
        ]
