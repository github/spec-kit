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

    def test_build_exec_args_uses_prompt_flag(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.specify build a login page",
            output_json=False,
        )

        assert args == ["pi", "-p", "/speckit.specify build a login page"]

    def test_build_exec_args_requests_json_mode(self):
        """Pi has no `--output-format`; JSONL events are selected with `--mode json`."""
        integration = get_integration(self.KEY)

        args = integration.build_exec_args("/speckit.plan add OAuth", output_json=True)

        assert args == ["pi", "-p", "/speckit.plan add OAuth", "--mode", "json"]
        assert "--output-format" not in args

    def test_build_exec_args_forwards_model(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.specify build a login page",
            model="openai/gpt-4o",
            output_json=False,
        )

        assert args == [
            "pi",
            "-p",
            "/speckit.specify build a login page",
            "--model",
            "openai/gpt-4o",
        ]

    def test_build_exec_args_applies_extra_args(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_INTEGRATION_PI_EXTRA_ARGS", "--thinking high")
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "check the build", model="openai/gpt-4o", output_json=True
        )

        assert args == [
            "pi",
            "-p",
            "check the build",
            "--thinking",
            "high",
            "--model",
            "openai/gpt-4o",
            "--mode",
            "json",
        ]
