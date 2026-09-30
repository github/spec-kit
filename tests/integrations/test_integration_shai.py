"""Tests for ShaiIntegration."""

from unittest.mock import MagicMock, patch

from specify_cli.integrations import get_integration
from specify_cli.workflows.base import StepContext, StepStatus
from specify_cli.workflows.step.command import CommandStep
from specify_cli.workflows.step.prompt import PromptStep

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestShaiIntegration(MarkdownIntegrationTests):
    KEY = "shai"
    FOLDER = ".shai/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".shai/commands"


class TestShaiCliDispatch:
    """SHAI's CLI can't run an installed Spec Kit command (#2416).

    Its argument, stdin and `shai agent <name> <prompt>` routes all hand the
    text to its auto-fix agent, which exits 0, and `.shai/commands` is never
    loaded, so dispatching `shai -p <prompt>` marked workflow steps completed
    without running the command.
    """

    def test_build_exec_args_opts_out(self):
        integration = get_integration("shai")
        assert integration.build_exec_args("/speckit.plan", model="m") is None

    def _run(self, step, config, tmp_path):
        ctx = StepContext(default_integration="shai", project_root=str(tmp_path))
        exited_ok = MagicMock(returncode=0, stdout="", stderr="")
        with patch("shutil.which", return_value="/usr/local/bin/shai"), \
             patch("subprocess.run", return_value=exited_ok) as run:
            result = step.execute(config, ctx)
        return result, run

    def test_command_step_fails_instead_of_running_shai(self, tmp_path):
        result, run = self._run(
            CommandStep(), {"id": "plan", "command": "speckit.plan"}, tmp_path
        )
        assert result.status == StepStatus.FAILED
        assert result.output["dispatched"] is False
        assert "does not support CLI dispatch" in result.error
        assert "set the step's 'integration'" in result.error
        run.assert_not_called()

    def test_prompt_step_fails_instead_of_running_shai(self, tmp_path):
        result, run = self._run(
            PromptStep(), {"id": "ask", "prompt": "Summarize the spec"}, tmp_path
        )
        assert result.status == StepStatus.FAILED
        assert result.output["dispatched"] is False
        assert "does not support CLI dispatch" in result.error
        assert "set the step's 'integration'" in result.error
        run.assert_not_called()
