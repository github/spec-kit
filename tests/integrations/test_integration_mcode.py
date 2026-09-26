"""Tests for McodeIntegration — skills-based integration (MiniMax Code)."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestMcodeIntegration(SkillsIntegrationTests):
    KEY = "mcode"
    FOLDER = ".minimax/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".minimax/skills"


class TestMcodeMetadata:
    """MiniMax Code-specific metadata and headless dispatch."""

    def test_display_name(self):
        from specify_cli.integrations import get_integration

        assert get_integration("mcode").config["name"] == "MiniMax Code"

    def test_requires_cli(self):
        from specify_cli.integrations import get_integration

        assert get_integration("mcode").config["requires_cli"] is True

    def test_install_url_points_to_github(self):
        from specify_cli.integrations import get_integration

        assert (
            get_integration("mcode").config["install_url"]
            == "https://github.com/MiniMax-AI/minimax-code"
        )

    def test_multi_install_safe(self):
        from specify_cli.integrations import get_integration

        assert get_integration("mcode").multi_install_safe is True

    def test_build_exec_args_uses_mcode_exec(self):
        from specify_cli.integrations import get_integration

        args = get_integration("mcode").build_exec_args("do the thing")
        assert args[:3] == ["mcode", "exec", "do the thing"]
        assert args[3:5] == ["--permission", "full"]
        assert "--output-format" in args
        assert args[args.index("--output-format") + 1] == "json"

    def test_build_exec_args_model_flag(self):
        from specify_cli.integrations import get_integration

        args = get_integration("mcode").build_exec_args(
            "do the thing", model="custom_provider:ark/deepseek-v4-flash", output_json=False
        )
        assert "--model" in args
        assert args[args.index("--model") + 1] == "custom_provider:ark/deepseek-v4-flash"
        assert "--output-format" not in args

    def test_build_exec_args_extra_args_env_var(self, monkeypatch):
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_MCODE_EXTRA_ARGS", "--timeout 60s --max-steps 20"
        )
        from specify_cli.integrations import get_integration

        args = get_integration("mcode").build_exec_args("do the thing")
        assert "--timeout" in args
        assert args[args.index("--timeout") + 1] == "60s"
        assert args[args.index("--max-steps") + 1] == "20"

    def test_build_exec_args_allows_permission_override(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_INTEGRATION_MCODE_EXTRA_ARGS", "--permission off")
        from specify_cli.integrations import get_integration

        args = get_integration("mcode").build_exec_args("do the thing")
        assert args[3:7] == ["--permission", "full", "--permission", "off"]

    def test_dispatch_command_uses_full_permission(self, monkeypatch, tmp_path):
        """The real dispatch path must pass the non-interactive permission mode."""
        import subprocess
        import shutil
        from types import SimpleNamespace

        from specify_cli.integrations import get_integration

        calls = []

        def run(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        monkeypatch.setattr(subprocess, "run", run)
        monkeypatch.setattr(shutil, "which", lambda _: None)
        result = get_integration("mcode").dispatch_command(
            "specify", "Add a health check", project_root=tmp_path, stream=False
        )

        assert result == {"exit_code": 0, "stdout": "ok", "stderr": ""}
        assert len(calls) == 1
        args, kwargs = calls[0]
        assert args[:3] == ["mcode", "exec", "/speckit-specify Add a health check"]
        assert args[3:5] == ["--permission", "full"]
        assert args[-2:] == ["--output-format", "json"]
        assert kwargs["cwd"] == str(tmp_path)

    def test_options_declares_skills_flag(self):
        from specify_cli.integrations import get_integration

        opts = get_integration("mcode").options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 1
        assert skills_opts[0].is_flag is True
        assert skills_opts[0].default is True

    def test_next_steps_show_slash_skill_invocation(self, tmp_path):
        """MiniMax Code next-steps guidance should display /speckit-* usage."""
        import os
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "mcode-next-steps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    "mcode",
                    "--ignore-agent-tools",
                    "--script",
                    "sh",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "/speckit-constitution" in result.output
        assert "/speckit.constitution" not in result.output
        assert "MiniMax Code" in result.output
        assert ".minimax/skills" in result.output
