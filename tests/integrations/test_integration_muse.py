"""Tests for MuseIntegration — skills-based integration (Meta Muse Code)."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestMuseIntegration(SkillsIntegrationTests):
    KEY = "muse"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"


class TestMuseMetadata:
    """Muse Code-specific metadata and headless dispatch."""

    def test_display_name(self):
        from specify_cli.integrations import get_integration

        assert get_integration("muse").config["name"] == "Muse Code"

    def test_requires_cli(self):
        from specify_cli.integrations import get_integration

        assert get_integration("muse").config["requires_cli"] is True

    def test_install_url_points_to_muse_docs(self):
        from specify_cli.integrations import get_integration

        assert (
            get_integration("muse").config["install_url"]
            == "https://dev.meta.ai/docs/muse-code"
        )

    def test_not_multi_install_safe(self):
        """Muse Code shares ``.agents/skills`` with Codex/Zed, so co-install
        stays opt-in (same policy as the docker-agent integration)."""
        from specify_cli.integrations import get_integration

        assert get_integration("muse").multi_install_safe is False

    def test_build_exec_args_uses_muse_exec(self):
        from specify_cli.integrations import get_integration

        args = get_integration("muse").build_exec_args("do the thing")
        assert args[:3] == ["muse", "exec", "do the thing"]
        assert args[-1] == "--json"

    def test_build_exec_args_model_flag(self):
        from specify_cli.integrations import get_integration

        args = get_integration("muse").build_exec_args(
            "do the thing", model="muse-spark-1.2", output_json=False
        )
        assert "--model" in args
        assert args[args.index("--model") + 1] == "muse-spark-1.2"
        assert "--json" not in args

    def test_next_steps_show_slash_skill_invocation(self, tmp_path):
        """Muse Code next-steps guidance should display /speckit-* usage."""
        import os
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "muse-next-steps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--integration", "muse",
                "--ignore-agent-tools", "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "/speckit-constitution" in result.output
        assert "/speckit.constitution" not in result.output
        assert "Muse Code" in result.output
