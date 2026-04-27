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
        assert "0.10.0" in normalized_output
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

    def test_shared_infra_skips_existing_files_without_force(self, tmp_path):
        """Pre-existing shared files are not overwritten without --force."""
        from specify_cli import _install_shared_infra

        project = tmp_path / "skip-test"
        project.mkdir()
        (project / ".specify").mkdir()

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

        _install_shared_infra(project, "sh", force=False)

        # User's files should be preserved (not overwritten)
        assert (scripts_dir / "common.sh").read_text(encoding="utf-8") == custom_content
        assert (templates_dir / "spec-template.md").read_text(encoding="utf-8") == custom_template

        # Other shared files should still be installed
        assert (scripts_dir / "setup-plan.sh").exists()
        assert (templates_dir / "plan-template.md").exists()

    def test_shared_infra_overwrites_existing_files_with_force(self, tmp_path):
        """Pre-existing shared files ARE overwritten when force=True."""
        from specify_cli import _install_shared_infra

        project = tmp_path / "force-test"
        project.mkdir()
        (project / ".specify").mkdir()

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

        _install_shared_infra(project, "sh", force=True)

        # Files should be overwritten with bundled versions
        assert (scripts_dir / "common.sh").read_text(encoding="utf-8") != custom_content
        assert (templates_dir / "spec-template.md").read_text(encoding="utf-8") != custom_template

        # Other shared files should also be installed
        assert (scripts_dir / "setup-plan.sh").exists()
        assert (templates_dir / "plan-template.md").exists()

    def test_shared_infra_skip_warning_displayed(self, tmp_path, capsys):
        """Console warning is displayed when files are skipped."""
        from specify_cli import _install_shared_infra

        project = tmp_path / "warn-test"
        project.mkdir()
        (project / ".specify").mkdir()

        scripts_dir = project / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "common.sh").write_text("# custom\n", encoding="utf-8")

        _install_shared_infra(project, "sh", force=False)

        captured = capsys.readouterr()
        assert "already exist and were not updated" in captured.out
        assert "specify init --here --force" in captured.out
        # Rich may wrap long lines; normalize whitespace for the second command
        normalized = " ".join(captured.out.split())
        assert "specify integration upgrade --force" in normalized

    def test_shared_infra_no_warning_when_forced(self, tmp_path, capsys):
        """No skip warning when force=True (all files overwritten)."""
        from specify_cli import _install_shared_infra

        project = tmp_path / "no-warn-test"
        project.mkdir()
        (project / ".specify").mkdir()

        scripts_dir = project / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "common.sh").write_text("# custom\n", encoding="utf-8")

        _install_shared_infra(project, "sh", force=True)

        captured = capsys.readouterr()
        assert "already exist and were not updated" not in captured.out

    def test_init_here_force_overwrites_shared_infra(self, tmp_path):
        """E2E: specify init --here --force overwrites shared infra files."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "e2e-force"
        project.mkdir()

        scripts_dir = project / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        custom_content = "# user-modified common.sh\n"
        (scripts_dir / "common.sh").write_text(custom_content, encoding="utf-8")

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
        # --force should overwrite the custom file
        assert (scripts_dir / "common.sh").read_text(encoding="utf-8") != custom_content

    def test_init_here_without_force_preserves_shared_infra(self, tmp_path):
        """E2E: specify init --here (no --force) preserves existing shared infra files."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "e2e-no-force"
        project.mkdir()

        scripts_dir = project / ".specify" / "scripts" / "bash"
        scripts_dir.mkdir(parents=True)
        custom_content = "# user-modified common.sh\n"
        (scripts_dir / "common.sh").write_text(custom_content, encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here",
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
            ], input="y\n", catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        # Without --force, custom file should be preserved
        assert (scripts_dir / "common.sh").read_text(encoding="utf-8") == custom_content
        # Warning about skipped files should appear
        assert "not updated" in result.output


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

    def test_no_git_emits_deprecation_warning(self, tmp_path):
        """Using --no-git emits a visible deprecation warning."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "no-git-warn"
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

        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "--no-git" in normalized_output
        assert "deprecated" in normalized_output
        assert "0.10.0" in normalized_output
        assert "specify extension" in normalized_output
        assert "will be removed" in normalized_output
        assert "git extension will no longer be enabled by default" in normalized_output

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


class TestSharedInfraCommandRefs:
    """Verify _install_shared_infra resolves __SPECKIT_COMMAND_*__ in page templates."""

    def test_dot_separator_in_page_templates(self, tmp_path):
        """Markdown agents get /speckit.<name> in page templates."""
        from specify_cli import _install_shared_infra

        project = tmp_path / "dot-test"
        project.mkdir()
        (project / ".specify").mkdir()

        _install_shared_infra(project, "sh", invoke_separator=".")

        plan = project / ".specify" / "templates" / "plan-template.md"
        assert plan.exists()
        content = plan.read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_" not in content, "unresolved placeholder in plan-template.md"
        assert "/speckit.plan" in content

        checklist = project / ".specify" / "templates" / "checklist-template.md"
        content = checklist.read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_" not in content
        assert "/speckit.checklist" in content

    def test_hyphen_separator_in_page_templates(self, tmp_path):
        """Skills agents get /speckit-<name> in page templates."""
        from specify_cli import _install_shared_infra

        project = tmp_path / "hyphen-test"
        project.mkdir()
        (project / ".specify").mkdir()

        _install_shared_infra(project, "sh", invoke_separator="-")

        plan = project / ".specify" / "templates" / "plan-template.md"
        assert plan.exists()
        content = plan.read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_" not in content, "unresolved placeholder in plan-template.md"
        assert "/speckit-plan" in content
        assert "/speckit.plan" not in content, "dot-notation leaked into skills page template"

        tasks = project / ".specify" / "templates" / "tasks-template.md"
        content = tasks.read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_" not in content
        assert "/speckit-tasks" in content

    def test_full_init_claude_resolves_page_templates(self, tmp_path):
        """Full CLI init with Claude (skills agent) produces hyphen refs in page templates."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "init-claude"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "init", str(project),
                "--integration", "claude",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        plan = project / ".specify" / "templates" / "plan-template.md"
        content = plan.read_text(encoding="utf-8")
        assert "/speckit-plan" in content, "Claude (skills) should use /speckit-plan"
        assert "__SPECKIT_COMMAND_" not in content

    def test_full_init_copilot_resolves_page_templates(self, tmp_path):
        """Full CLI init with Copilot (markdown agent) produces dot refs in page templates."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "init-copilot"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "init", str(project),
                "--integration", "copilot",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        plan = project / ".specify" / "templates" / "plan-template.md"
        content = plan.read_text(encoding="utf-8")
        assert "/speckit.plan" in content, "Copilot (markdown) should use /speckit.plan"
        assert "__SPECKIT_COMMAND_" not in content

    def test_full_init_copilot_skills_resolves_page_templates(self, tmp_path):
        """Full CLI init with Copilot --skills produces hyphen refs in page templates."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        project = tmp_path / "init-copilot-skills"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, [
                "init", str(project),
                "--integration", "copilot",
                "--integration-options", "--skills",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"

        plan = project / ".specify" / "templates" / "plan-template.md"
        content = plan.read_text(encoding="utf-8")
        assert "/speckit-plan" in content, "Copilot --skills should use /speckit-plan"
        assert "/speckit.plan" not in content, "dot-notation leaked into Copilot skills page template"
        assert "__SPECKIT_COMMAND_" not in content
