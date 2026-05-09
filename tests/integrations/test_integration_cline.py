"""Tests for ClineIntegration."""

import os
import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.cline import format_cline_command_name
from .test_integration_base_markdown import MarkdownIntegrationTests


class TestClineCommandNameFormatter:
    """Test the Cline command name formatter."""

    def test_simple_name_without_prefix(self):
        """Test formatting a simple name without 'speckit.' prefix."""
        assert format_cline_command_name("plan") == "speckit-plan"
        assert format_cline_command_name("tasks") == "speckit-tasks"
        assert format_cline_command_name("specify") == "speckit-specify"

    def test_name_with_speckit_prefix(self):
        """Test formatting a name that already has 'speckit.' prefix."""
        assert format_cline_command_name("speckit.plan") == "speckit-plan"
        assert format_cline_command_name("speckit.tasks") == "speckit-tasks"

    def test_extension_command_name(self):
        """Test formatting extension command names with dots."""
        assert (
            format_cline_command_name("speckit.my-extension.example")
            == "speckit-my-extension-example"
        )
        assert (
            format_cline_command_name("my-extension.example")
            == "speckit-my-extension-example"
        )

    def test_idempotent_already_hyphenated(self):
        """Test that already-hyphenated names are returned unchanged (idempotent)."""
        assert format_cline_command_name("speckit-plan") == "speckit-plan"
        assert (
            format_cline_command_name("speckit-my-extension-example")
            == "speckit-my-extension-example"
        )


class TestClineIntegration(MarkdownIntegrationTests):
    KEY = "cline"
    FOLDER = ".clinerules/"
    COMMANDS_SUBDIR = "workflows"
    REGISTRAR_DIR = ".clinerules/workflows"
    CONTEXT_FILE = ".clinerules/specify-rules.md"

    @pytest.mark.parametrize(
        "cmd_name, expected_filename",
        [
            ("plan", "speckit-plan.md"),
            ("speckit.plan", "speckit-plan.md"),
            ("speckit.git.commit", "speckit-git-commit.md"),
            ("speckit", "speckit-speckit.md"),
            ("speckitfoo", "speckit-speckitfoo.md"),
        ],
    )
    def test_cline_command_filename(self, cmd_name, expected_filename):
        """Verify Cline uses hyphenated filenames."""
        cline = get_integration("cline")
        assert cline.command_filename(cmd_name) == expected_filename

    def test_cline_invoke_separator(self):
        """Verify Cline uses hyphen as invoke separator."""
        cline = get_integration("cline")
        assert cline.invoke_separator == "-"
        assert cline.registrar_config["invoke_separator"] == "-"

    def test_cline_name_injection_and_formatting(self):
        """Verify Cline has inject_name and format_name configured."""
        cline = get_integration("cline")
        assert cline.registrar_config["inject_name"] is True
        assert cline.registrar_config["format_name"] == format_cline_command_name

    def test_cline_handoff_rewrite(self):
        """Verify Cline rewrites agent: speckit.foo to agent: speckit-foo."""
        cline = get_integration("cline")
        content = "---\nagent: speckit.plan\n---\n"
        rewritten = cline._rewrite_handoff_references(content)
        assert rewritten == "---\nagent: speckit-plan\n---\n"

    def test_cline_hook_instruction_injection(self):
        """Verify Cline injects the dot-to-hyphen note for hooks."""
        cline = get_integration("cline")
        content = "- For each executable hook, output the following:\n"
        injected = cline._inject_hook_command_note(content)
        assert "replace dots (`.`) with hyphens (`-`)" in injected
        assert "- For each executable hook, output the following:" in injected

    # -- Overrides for MarkdownIntegrationTests ---------------------------

    def test_setup_creates_files(self, tmp_path):
        from specify_cli.integrations.manifest import IntegrationManifest

        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        cmd_files = [
            f
            for f in created
            if "scripts" not in f.parts
            and f.suffix == ".md"
            and f.name != i.context_file
        ]
        for f in cmd_files:
            assert f.exists()
            assert f.name.startswith("speckit-")
            assert f.name.endswith(".md")

        specify_file = next(
            (f for f in cmd_files if f.name == "speckit-specify.md"), None
        )
        assert specify_file is not None
        specify_contents = specify_file.read_text(encoding="utf-8")
        assert "/speckit-plan" in specify_contents
        assert "/speckit.plan" not in specify_contents

    def test_integration_flag_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"int-{self.KEY}"
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
                    self.KEY,
                    "--script",
                    "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        i = get_integration(self.KEY)
        cmd_dir = i.commands_dest(project)
        assert cmd_dir.is_dir()
        commands = sorted(cmd_dir.glob("speckit-*"))
        assert len(commands) > 0

    def _expected_files(self, script_variant: str) -> list[str]:
        """Override to expect hyphenated speckit- prefix."""
        i = get_integration(self.KEY)
        cmd_dir = i.registrar_config["dir"]
        files = []

        # Command files
        for stem in (
            self.COMMANDS_SUBDIR_STEMS
            if hasattr(self, "COMMANDS_SUBDIR_STEMS")
            else self.COMMAND_STEMS
        ):
            files.append(f"{cmd_dir}/speckit-{stem.replace('.', '-')}.md")

        # Framework files
        files.append(".specify/integration.json")
        files.append(".specify/init-options.json")
        files.append(f".specify/integrations/{self.KEY}.manifest.json")
        files.append(".specify/integrations/speckit.manifest.json")

        if script_variant == "sh":
            for name in [
                "check-prerequisites.sh",
                "common.sh",
                "create-new-feature.sh",
                "setup-plan.sh",
                "setup-tasks.sh",
            ]:
                files.append(f".specify/scripts/bash/{name}")
        else:
            for name in [
                "check-prerequisites.ps1",
                "common.ps1",
                "create-new-feature.ps1",
                "setup-plan.ps1",
                "setup-tasks.ps1",
            ]:
                files.append(f".specify/scripts/powershell/{name}")

        for name in [
            "checklist-template.md",
            "constitution-template.md",
            "plan-template.md",
            "spec-template.md",
            "tasks-template.md",
        ]:
            files.append(f".specify/templates/{name}")

        files.append(".specify/memory/constitution.md")
        # Bundled workflow
        files.append(".specify/workflows/speckit/workflow.yml")
        files.append(".specify/workflows/workflow-registry.json")

        # Agent context file (if set)
        if i.context_file:
            files.append(i.context_file)

        return sorted(files)
