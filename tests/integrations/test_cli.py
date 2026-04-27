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


class TestIntegrationCatalogDiscoveryCLI:
    """End-to-end CLI tests for `integration search`, `info`, and `catalog …`.

    All tests patch `IntegrationCatalog._get_merged_integrations` so no network
    or on-disk cache is touched. Adds #2344 coverage without affecting any
    existing integration install/switch/uninstall/upgrade behavior.
    """

    FAKE_INTEGRATIONS = [
        {
            "id": "acme-coder",
            "name": "Acme Coder",
            "version": "2.0.0",
            "description": "Community integration for Acme Coder",
            "author": "acme-org",
            "tags": ["cli", "acme"],
            "_catalog_name": "community",
            "_install_allowed": False,
        },
        {
            "id": "stellar-agent",
            "name": "Stellar Agent",
            "version": "1.3.0",
            "description": "First-party Stellar agent integration",
            "author": "stellar-labs",
            "tags": ["ide"],
            "_catalog_name": "default",
            "_install_allowed": True,
        },
    ]

    def _make_project(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        return project

    def _patch_catalog(self, monkeypatch, integrations=None):
        """Return a stubbed `_get_merged_integrations` that yields *integrations*."""
        from specify_cli.integrations.catalog import IntegrationCatalog

        data = list(integrations if integrations is not None else self.FAKE_INTEGRATIONS)

        def fake_merged(self, force_refresh=False):
            return data

        monkeypatch.setattr(IntegrationCatalog, "_get_merged_integrations", fake_merged)

    def _invoke(self, argv, cwd):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        old = os.getcwd()
        try:
            os.chdir(cwd)
            return runner.invoke(app, argv, catch_exceptions=False)
        finally:
            os.chdir(old)

    # -- Project guard -----------------------------------------------------

    def test_search_requires_specify_project(self, tmp_path):
        project = tmp_path / "bare"
        project.mkdir()
        result = self._invoke(["integration", "search"], project)
        assert result.exit_code == 1
        assert "Not a spec-kit project" in result.output

    def test_catalog_list_requires_specify_project(self, tmp_path):
        project = tmp_path / "bare"
        project.mkdir()
        result = self._invoke(["integration", "catalog", "list"], project)
        assert result.exit_code == 1
        assert "Not a spec-kit project" in result.output

    # -- search ------------------------------------------------------------

    def test_search_lists_all(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "Found 2 integration(s)" in result.output
        assert "acme-coder" in result.output
        assert "stellar-agent" in result.output
        assert "specify integration install stellar-agent" not in normalized_output
        assert "Only built-in integration IDs can be installed" in normalized_output

    def test_search_validates_integration_json_before_catalog_lookup(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        (project / ".specify" / "integration.json").write_text(
            "{bad json\n", encoding="utf-8"
        )

        from specify_cli.integrations.catalog import IntegrationCatalog

        def fail_search(self, **kwargs):
            raise AssertionError("catalog search should not be called")

        monkeypatch.setattr(IntegrationCatalog, "search", fail_search)

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1
        assert "contains invalid JSON" in normalized_output
        assert "integration.json" in normalized_output

    def test_search_filters_by_tag(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(["integration", "search", "--tag", "acme"], project)
        assert result.exit_code == 0, result.output
        assert "Found 1 integration(s)" in result.output
        assert "acme-coder" in result.output
        assert "stellar-agent" not in result.output

    def test_search_filters_by_author(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "search", "--author", "stellar-labs"], project
        )
        assert result.exit_code == 0, result.output
        assert "Found 1 integration(s)" in result.output
        assert "stellar-agent" in result.output

    def test_search_no_match_hint(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "search", "--tag", "nope"], project
        )
        assert result.exit_code == 0, result.output
        assert "No integrations found" in result.output
        assert "specify integration search" in result.output

    def test_search_marks_discovery_only_entry(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(["integration", "search", "acme"], project)
        assert result.exit_code == 0, result.output
        # acme-coder is flagged _install_allowed=False, so we should warn
        assert "Not directly installable" in result.output

    # -- info --------------------------------------------------------------

    def test_info_found(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "info", "stellar-agent"], project
        )
        assert result.exit_code == 0, result.output
        assert "Stellar Agent" in result.output
        assert "stellar-agent" in result.output
        assert "v1.3.0" in result.output

    def test_info_not_found(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        self._patch_catalog(monkeypatch)
        result = self._invoke(
            ["integration", "info", "does-not-exist"], project
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_info_builtin_not_in_catalog(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        # Empty catalog, but copilot is a registered built-in.
        self._patch_catalog(monkeypatch, integrations=[])
        result = self._invoke(["integration", "info", "copilot"], project)
        assert result.exit_code == 0, result.output
        assert "Built-in integration" in result.output

    # -- validation vs network guidance ------------------------------------

    def test_search_local_config_error_shows_local_config_tip(
        self, tmp_path, monkeypatch
    ):
        """`integration search` must point at .specify/integration-catalogs.yml
        for local-config errors (not the generic 'temporarily unavailable')."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        # Corrupt YAML to drive _load_catalog_config -> IntegrationValidationError.
        cfg = project / ".specify" / "integration-catalogs.yml"
        invalid_yaml = "catalogs:\n  - [bad\n"
        cfg.write_text(invalid_yaml, encoding="utf-8")

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "configuration file path shown above" in normalized_output
        assert ".specify/integration-catalogs.yml" in normalized_output
        assert "~/.specify/integration-catalogs.yml" in normalized_output
        assert "temporarily unavailable" not in normalized_output

    def test_search_invalid_env_catalog_url_shows_env_tip(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "http://insecure.example.com/catalog.json",
        )

        result = self._invoke(["integration", "search"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "SPECKIT_INTEGRATION_CATALOG_URL environment variable" in normalized_output
        assert "unset it to use the configured catalog files" in normalized_output
        assert ".specify/integration-catalogs.yml" in normalized_output
        assert "~/.specify/integration-catalogs.yml" in normalized_output
        assert "temporarily unavailable" not in normalized_output

    def test_info_unknown_with_local_config_error_shows_local_config_tip(
        self, tmp_path, monkeypatch
    ):
        """`integration info <unknown>` falls back to the catalog-error branch
        and must show local-config guidance, not 'Try again when online'."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        cfg = project / ".specify" / "integration-catalogs.yml"
        invalid_yaml = "catalogs:\n  - [bad\n"
        cfg.write_text(invalid_yaml, encoding="utf-8")

        result = self._invoke(
            ["integration", "info", "definitely-not-real"], project
        )
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "configuration file path shown above" in normalized_output
        assert ".specify/integration-catalogs.yml" in normalized_output
        assert "~/.specify/integration-catalogs.yml" in normalized_output
        assert "Try again when online" not in normalized_output

    def test_info_unknown_with_invalid_env_catalog_url_shows_env_tip(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "http://insecure.example.com/catalog.json",
        )

        result = self._invoke(
            ["integration", "info", "definitely-not-real"], project
        )
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 1, result.output
        assert "SPECKIT_INTEGRATION_CATALOG_URL" in normalized_output
        assert "unset it to use the configured catalog files" in normalized_output
        assert "Try again when online" not in normalized_output

    # -- catalog list / add / remove ---------------------------------------

    def test_catalog_list_shows_builtin_defaults(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)
        result = self._invoke(["integration", "catalog", "list"], project)
        assert result.exit_code == 0, result.output
        assert "Integration Catalog Sources" in result.output
        assert "No project-level catalog sources configured" in result.output
        assert "Active catalog sources" in result.output
        assert "non-removable" in result.output
        assert "default" in result.output
        assert "community" in result.output
        # Built-in defaults are active, but not removable project entries.
        assert "[0]" not in result.output
        assert "[1]" not in result.output

    def test_catalog_add_then_remove_roundtrip(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)

        add_result = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "https://new.example.com/catalog.json",
                "--name",
                "mine",
            ],
            project,
        )
        assert add_result.exit_code == 0, add_result.output
        assert "Catalog source added" in add_result.output

        cfg_path = project / ".specify" / "integration-catalogs.yml"
        assert cfg_path.exists()

        list_result = self._invoke(["integration", "catalog", "list"], project)
        assert list_result.exit_code == 0, list_result.output
        assert "Project catalog sources" in list_result.output
        assert "[0]" in list_result.output
        assert "mine" in list_result.output
        assert "default" not in list_result.output
        assert "community" not in list_result.output

        remove_result = self._invoke(
            ["integration", "catalog", "remove", "0"], project
        )
        assert remove_result.exit_code == 0, remove_result.output
        assert "'mine' removed" in remove_result.output

    def test_catalog_list_env_override_supersedes_project_config(
        self, tmp_path, monkeypatch
    ):
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_CATALOG_URL",
            "https://env.example.com/catalog.json",
        )
        cfg_path = project / ".specify" / "integration-catalogs.yml"
        cfg_path.write_text(
            yaml.dump(
                {
                    "catalogs": [
                        {
                            "url": "https://project.example.com/catalog.json",
                            "name": "project",
                            "priority": 1,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = self._invoke(["integration", "catalog", "list"], project)
        normalized_output = _normalize_cli_output(result.output)
        assert result.exit_code == 0, result.output
        assert "SPECKIT_INTEGRATION_CATALOG_URL is set" in normalized_output
        assert "supersedes configured catalog files" in normalized_output
        assert "non-removable" in normalized_output
        assert "https://env.example.com/catalog.json" in normalized_output
        assert "https://project.example.com/catalog.json" not in normalized_output
        assert "[0]" not in normalized_output

    def test_catalog_add_strips_whitespace_in_success_output_and_storage(
        self, tmp_path, monkeypatch
    ):
        """Surrounding whitespace in the URL must not appear in the success
        message or be persisted to the YAML config."""
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)

        padded_url = "  https://padded.example.com/catalog.json  "
        clean_url = "https://padded.example.com/catalog.json"

        add_result = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                padded_url,
                "--name",
                "padded",
            ],
            project,
        )
        assert add_result.exit_code == 0, add_result.output
        assert clean_url in add_result.output
        assert padded_url not in add_result.output

        cfg_path = project / ".specify" / "integration-catalogs.yml"
        import yaml as _yaml
        data = _yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        urls = [c["url"] for c in data["catalogs"]]
        assert clean_url in urls
        assert padded_url not in urls

    def test_catalog_add_rejects_invalid_url(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        result = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "http://insecure.example.com/catalog.json",
            ],
            project,
        )
        assert result.exit_code == 1
        assert "HTTPS" in result.output

    def test_catalog_add_rejects_duplicate(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        url = "https://dup.example.com/catalog.json"
        first = self._invoke(
            ["integration", "catalog", "add", url], project
        )
        assert first.exit_code == 0, first.output
        second = self._invoke(
            ["integration", "catalog", "add", url], project
        )
        assert second.exit_code == 1
        assert "already configured" in second.output

    def test_catalog_remove_out_of_range(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        # Need a config file for remove to attempt an index lookup
        self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "https://only.example.com/catalog.json",
            ],
            project,
        )
        result = self._invoke(
            ["integration", "catalog", "remove", "9"], project
        )
        assert result.exit_code == 1
        assert "out of range" in result.output

    def test_catalog_remove_without_config(self, tmp_path, monkeypatch):
        project = self._make_project(tmp_path)
        result = self._invoke(
            ["integration", "catalog", "remove", "0"], project
        )
        assert result.exit_code == 1
        assert "No catalog config" in result.output

    def test_catalog_remove_final_entry_restores_defaults(
        self, tmp_path, monkeypatch
    ):
        """End-to-end: add → remove-last-entry → list should not error.

        Regression for the flow where a user adds a catalog, removes it, then
        runs any follow-up integration command. Without the fix the config
        file would be left as `catalogs: []` and every subsequent
        `integration` call would fail with "contains no 'catalogs' entries".
        """
        project = self._make_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.delenv("SPECKIT_INTEGRATION_CATALOG_URL", raising=False)

        add = self._invoke(
            [
                "integration",
                "catalog",
                "add",
                "https://only.example.com/catalog.json",
                "--name",
                "only",
            ],
            project,
        )
        assert add.exit_code == 0, add.output

        remove = self._invoke(
            ["integration", "catalog", "remove", "0"], project
        )
        assert remove.exit_code == 0, remove.output
        assert "'only' removed" in remove.output

        cfg_path = project / ".specify" / "integration-catalogs.yml"
        assert not cfg_path.exists(), (
            "config file should be deleted when the final catalog is removed"
        )

        # Follow-up command must succeed and show the built-in defaults,
        # not error out on "contains no 'catalogs' entries".
        listing = self._invoke(["integration", "catalog", "list"], project)
        assert listing.exit_code == 0, listing.output
        assert "default" in listing.output
        assert "community" in listing.output
