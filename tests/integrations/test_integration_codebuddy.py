"""Tests for CodebuddyIntegration."""

from specify_cli.integrations import get_integration

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestCodebuddyIntegration(MarkdownIntegrationTests):
    KEY = "codebuddy"
    FOLDER = ".codebuddy/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".codebuddy/commands"

    def test_install_url_points_to_official_cli_install_docs(self):
        integration = get_integration(self.KEY)
        assert integration is not None

        assert (
            integration.config["install_url"]
            == "https://www.codebuddy.cn/docs/cli/installation"
        )
