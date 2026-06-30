"""Tests for OmpIntegration."""

from specify_cli.integrations import get_integration

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestOmpIntegration(MarkdownIntegrationTests):
    KEY = "omp"
    FOLDER = ".omp/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".omp/commands"

    def test_build_exec_args_uses_omp_json_mode(self):
        i = get_integration(self.KEY)

        args = i.build_exec_args(
            "/speckit.specify Build auth",
            model="gpt-5",
        )

        assert args == [
            "omp",
            "--print",
            "--model",
            "gpt-5",
            "--mode",
            "json",
            "/speckit.specify Build auth",
        ]
