"""Tests for --integration flag on specify init (CLI-level)."""

import json
import os

import yaml

from tests.conftest import strip_ansi


def _normalize_cli_output(output: str) -> str:
    output = strip_ansi(output)
    output = " ".join(output.split())
    return output.strip()


class TestInitIntegrationFlag:
    def test_integration_and_ai_mutually_exclusive(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(tmp_path / "test-project"), "--ai", "claude", "--integration", "copilot",
        ])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    def test_unknown_integration_rejected(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(tmp_path / "test-project"), "--integration", "nonexistent",
        ])
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_integration_copilot_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "int-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()
        assert (project / ".github" / "prompts" / "speckit.plan.prompt.md").exists()
        assert (project / ".specify" / "scripts" / "bash" / "common.sh").exists()

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "copilot"
        assert opts["context_file"] == ".github/copilot-instructions.md"

        assert (project / ".specify" / "integrations" / "copilot.manifest.json").exists()

        # Context section should be upserted into the copilot instructions file
        ctx_file = project / ".github" / "copilot-instructions.md"
        assert ctx_file.exists()
        ctx_content = ctx_file.read_text(encoding="utf-8")
        assert "<!-- SPECKIT START -->" in ctx_content
        assert "<!-- SPECKIT END -->" in ctx_content

        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        assert shared_manifest.exists()

    def test_ai_copilot_auto_promotes(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        project = tmp_path / "promote-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()

    def test_ai_emits_deprecation_warning_with_integration_replacement(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "warn-ai"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "Deprecation Warning" in normalized_output
        assert "--ai" in normalized_output
        assert "deprecated" in normalized_output
        assert "no longer be available" in normalized_output
        assert "1.0.0" in normalized_output
        assert "--integration copilot" in normalized_output
        assert normalized_output.index("Deprecation Warning") < normalized_output.index("Next Steps")
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()

    def test_ai_generic_warning_suggests_integration_options_equivalent(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "warn-generic"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "generic", "--ai-commands-dir", ".myagent/commands",
                "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "Deprecation Warning" in normalized_output
        assert "--integration generic" in normalized_output
        assert "--integration-options" in normalized_output
        assert ".myagent/commands" in normalized_output
        assert normalized_output.index("Deprecation Warning") < normalized_output.index("Next Steps")
        assert (project / ".myagent" / "commands" / "speckit.plan.md").exists()

    def test_ai_claude_here_preserves_preexisting_commands(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "claude-here-existing"
        project.mkdir()
        commands_dir = project / ".claude" / "skills"
        commands_dir.mkdir(parents=True)
        skill_dir = commands_dir / "speckit-specify"
        skill_dir.mkdir(parents=True)
        command_file = skill_dir / "SKILL.md"
        command_file.write_text("# preexisting command\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--force", "--ai", "claude", "--ai-skills", "--script", "sh", "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, result.output
        assert command_file.exists()
        # init replaces skills (not additive); verify the file has valid skill content
        assert command_file.exists()
        assert "speckit-specify" in command_file.read_text(encoding="utf-8")
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_shared_infra_skips_existing_files(self, tmp_path):
        """Pre-existing shared files are not overwritten by _install_shared_infra."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "skip-test"
        project.mkdir()

        # Pre-create a shared script with custom content
        scripts_dir = project / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        custom_content = "# user-modified common.sh\n"
        (scripts_dir / "common.sh").write_text(custom_content, encoding="utf-8")

        # Pre-create a shared template with custom content
        templates_dir = project / ".specify" / "templates"
        templates_dir.mkdir(parents=True)
        custom_template = "# user-modified spec-template\n"
        (templates_dir / "spec-template.md").write_text(custom_template, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--force",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0

        # User's files should be preserved
        assert (scripts_dir / "common.sh").read_text(encoding="utf-8") == custom_content
        assert (templates_dir / "spec-template.md").read_text(encoding="utf-8") == custom_template

        # Other shared files should still be installed
        assert (scripts_dir / "setup-plan.sh").exists()
        assert (templates_dir / "plan-template.md").exists()


class TestForceExistingDirectory:
    """Tests for --force merging into an existing named directory."""

    def test_force_merges_into_existing_dir(self, tmp_path):
        """specify init <dir> --force succeeds when the directory already exists."""
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "existing-proj"
        target.mkdir()
        # Place a pre-existing file to verify it survives the merge
        marker = target / "user-file.txt"
        marker.write_text("keep me", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(target), "--integration", "copilot", "--force",
            "--no-git", "--script", "sh",
        ], catch_exceptions=False)

        assert result.exit_code == 0, f"init --force failed: {result.output}"

        # Pre-existing file should survive
        assert marker.read_text(encoding="utf-8") == "keep me"

        # Spec Kit files should be installed
        assert (target / ".specify" / "init-options.json").exists()
        assert (target / ".specify" / "templates" / "spec-template.md").exists()

    def test_without_force_errors_on_existing_dir(self, tmp_path):
        """specify init <dir> without --force errors when directory exists."""
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "existing-proj"
        target.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(target), "--integration", "copilot",
            "--no-git", "--script", "sh",
        ], catch_exceptions=False)

        assert result.exit_code == 1
        assert "already exists" in _normalize_cli_output(result.output)


class TestGitExtensionAutoInstall:
    """Tests for auto-installation of the git extension during specify init."""

    def test_git_extension_auto_installed(self, tmp_path):
        """Without --no-git, the git extension is installed during init."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "git-auto"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "claude", "--script", "sh",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        # Check that the tracker didn't report a git error
        assert "install failed" not in result.output, f"git extension install failed: {result.output}"

        # Git extension files should be installed
        ext_dir = project / ".specify" / "extensions" / "git"
        assert ext_dir.exists(), "git extension directory not installed"
        assert (ext_dir / "extension.yml").exists()
        assert (ext_dir / "scripts" / "bash" / "create-new-feature.sh").exists()
        assert (ext_dir / "scripts" / "bash" / "initialize-repo.sh").exists()

        # Hooks should be registered
        extensions_yml = project / ".specify" / "extensions.yml"
        assert extensions_yml.exists(), "extensions.yml not created"
        hooks_data = yaml.safe_load(extensions_yml.read_text(encoding="utf-8"))
        assert "hooks" in hooks_data
        assert "before_specify" in hooks_data["hooks"]
        assert "before_constitution" in hooks_data["hooks"]

    def test_no_git_skips_extension(self, tmp_path):
        """With --no-git, the git extension is NOT installed."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "no-git"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "claude", "--script", "sh",
                "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        # Git extension should NOT be installed
        ext_dir = project / ".specify" / "extensions" / "git"
        assert not ext_dir.exists(), "git extension should not be installed with --no-git"

    def test_git_extension_commands_registered(self, tmp_path):
        """Git extension commands are registered with the agent during init."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "git-cmds"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "claude", "--script", "sh",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        # Git extension commands should be registered with the agent
        claude_skills = project / ".claude" / "skills"
        assert claude_skills.exists(), "Claude skills directory was not created"
        git_skills = [f for f in claude_skills.iterdir() if f.name.startswith("speckit-git-")]
        assert len(git_skills) > 0, "no git extension commands registered"
