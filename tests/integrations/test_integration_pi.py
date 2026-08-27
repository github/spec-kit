"""Tests for PiIntegration."""

from specify_cli.integrations import get_integration

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestPiIntegration(MarkdownIntegrationTests):
    KEY = "pi"
    FOLDER = ".pi/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".pi/prompts"

    def test_multi_install_safe(self):
        # Pi writes only to its isolated, static root .pi/prompts, disjoint from
        # every other integration, so it must be co-install safe (mirrors
        # qwen/shai/qodercli and the kiro-cli #3471 precedent).
        assert get_integration(self.KEY).multi_install_safe is True
