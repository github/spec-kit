"""Reusable test mixin for standard SkillsIntegration subclasses.

Each per-agent test file sets ``KEY``, ``FOLDER``, ``COMMANDS_SUBDIR``,
``REGISTRAR_DIR``, and ``CONTEXT_FILE``, then inherits all verification
logic from ``SkillsIntegrationTests``.

Mirrors ``MarkdownIntegrationTests`` / ``TomlIntegrationTests`` closely,
adapted for the ``speckit-<name>/SKILL.md`` skills layout.
"""

import os

import yaml

from specify_cli.integrations import INTEGRATION_REGISTRY, get_integration
from specify_cli.integrations.base import SkillsIntegration
from specify_cli.integrations.manifest import IntegrationManifest


class SkillsIntegrationTests:
    """Mixin — set class-level constants and inherit these tests.

    Required class attrs on subclass::

        KEY: str              — integration registry key
        FOLDER: str           — e.g. ".agents/"
        COMMANDS_SUBDIR: str  — e.g. "skills"
        REGISTRAR_DIR: str    — e.g. ".agents/skills"
        CONTEXT_FILE: str     — e.g. "AGENTS.md"
    """

    KEY: str
    FOLDER: str
    COMMANDS_SUBDIR: str
    REGISTRAR_DIR: str
    CONTEXT_FILE: str

    # -- Registration -----------------------------------------------------

    def test_registered(self):
        assert self.KEY in INTEGRATION_REGISTRY
        assert get_integration(self.KEY) is not None

    def test_is_skills_integration(self):
        assert isinstance(get_integration(self.KEY), SkillsIntegration)

    # -- Config -----------------------------------------------------------

    def test_config_folder(self):
        i = get_integration(self.KEY)
        assert i.config["folder"] == self.FOLDER

    def test_config_commands_subdir(self):
        i = get_integration(self.KEY)
        assert i.config["commands_subdir"] == self.COMMANDS_SUBDIR

    def test_registrar_config(self):
        i = get_integration(self.KEY)
        assert i.registrar_config["dir"] == self.REGISTRAR_DIR
        assert i.registrar_config["format"] == "markdown"
        assert i.registrar_config["args"] == "$ARGUMENTS"
        assert i.registrar_config["extension"] == "/SKILL.md"

    def test_context_file(self):
        i = get_integration(self.KEY)
        assert i.context_file == self.CONTEXT_FILE

    # -- Setup / teardown -------------------------------------------------

    def test_setup_creates_files(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        assert len(created) > 0
        skill_files = [f for f in created if "scripts" not in f.parts]
        for f in skill_files:
            assert f.exists()
            assert f.name == "SKILL.md"
            assert f.parent.name.startswith("speckit-")

    def test_setup_writes_to_correct_directory(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        expected_dir = i.skills_dest(tmp_path)
        assert expected_dir.exists(), f"Expected directory {expected_dir} was not created"
        skill_files = [f for f in created if "scripts" not in f.parts]
        assert len(skill_files) > 0, "No skill files were created"
        for f in skill_files:
            # Each SKILL.md is in speckit-<name>/ under the skills directory
            assert f.resolve().parent.parent == expected_dir.resolve(), (
                f"{f} is not under {expected_dir}"
            )

    def test_skill_directory_structure(self, tmp_path):
        """Each command produces speckit-<name>/SKILL.md."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]

        expected_commands = {
            "analyze", "checklist", "clarify", "constitution",
            "implement", "plan", "specify", "tasks", "taskstoissues",
        }

        # Derive command names from the skill directory names
        actual_commands = set()
        for f in skill_files:
            skill_dir_name = f.parent.name  # e.g. "speckit-plan"
            assert skill_dir_name.startswith("speckit-")
            actual_commands.add(skill_dir_name.removeprefix("speckit-"))

        assert actual_commands == expected_commands

    def test_skill_frontmatter_structure(self, tmp_path):
        """SKILL.md must have name, description, compatibility, metadata."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]

        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert content.startswith("---\n"), f"{f} missing frontmatter"
            parts = content.split("---", 2)
            fm = yaml.safe_load(parts[1])
            assert "name" in fm, f"{f} frontmatter missing 'name'"
            assert "description" in fm, f"{f} frontmatter missing 'description'"
            assert "compatibility" in fm, f"{f} frontmatter missing 'compatibility'"
            assert "metadata" in fm, f"{f} frontmatter missing 'metadata'"
            assert fm["metadata"]["author"] == "github-spec-kit"
            assert "source" in fm["metadata"]

    def test_skill_uses_template_descriptions(self, tmp_path):
        """SKILL.md should use the original template description for ZIP parity."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]

        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            fm = yaml.safe_load(parts[1])
            # Description must be a non-empty string (from the template)
            assert isinstance(fm["description"], str)
            assert len(fm["description"]) > 0, f"{f} has empty description"

    def test_templates_are_processed(self, tmp_path):
        """Skill body must have placeholders replaced, not raw templates."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]
        assert len(skill_files) > 0
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{f.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{f.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{f.name} has unprocessed {{ARGS}}"

    def test_skill_body_has_content(self, tmp_path):
        """Each SKILL.md body should contain template content after the frontmatter."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            # Body is everything after the second ---
            parts = content.split("---", 2)
            body = parts[2].strip() if len(parts) >= 3 else ""
            assert len(body) > 0, f"{f} has empty body"

    def test_all_files_tracked_in_manifest(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = i.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        m.save()
        modified_file = created[0]
        modified_file.write_text("user modified this", encoding="utf-8")
        removed, skipped = i.uninstall(tmp_path, m)
        assert modified_file.exists()
        assert modified_file in skipped

    def test_pre_existing_skills_not_removed(self, tmp_path):
        """Pre-existing non-speckit skills should be left untouched."""
        i = get_integration(self.KEY)
        skills_dir = i.skills_dest(tmp_path)
        foreign_dir = skills_dir / "other-tool"
        foreign_dir.mkdir(parents=True)
        (foreign_dir / "SKILL.md").write_text("# Foreign skill\n")

        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)

        assert (foreign_dir / "SKILL.md").exists(), "Foreign skill was removed"

    # -- Scripts ----------------------------------------------------------

    def test_setup_installs_update_context_scripts(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        scripts_dir = tmp_path / ".specify" / "integrations" / self.KEY / "scripts"
        assert scripts_dir.is_dir(), f"Scripts directory not created for {self.KEY}"
        assert (scripts_dir / "update-context.sh").exists()
        assert (scripts_dir / "update-context.ps1").exists()

    def test_scripts_tracked_in_manifest(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        script_rels = [k for k in m.files if "update-context" in k]
        assert len(script_rels) >= 2

    def test_sh_script_is_executable(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        sh = tmp_path / ".specify" / "integrations" / self.KEY / "scripts" / "update-context.sh"
        assert os.access(sh, os.X_OK)

    # -- CLI auto-promote -------------------------------------------------

    def test_ai_flag_auto_promotes(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"promote-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", self.KEY, "--script", "sh", "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init --ai {self.KEY} failed: {result.output}"
        assert f"--integration {self.KEY}" in result.output

    def test_integration_flag_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"int-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--integration", self.KEY, "--script", "sh", "--no-git",
                "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init --integration {self.KEY} failed: {result.output}"
        i = get_integration(self.KEY)
        skills_dir = i.skills_dest(project)
        assert skills_dir.is_dir(), f"Skills directory {skills_dir} not created"

    # -- IntegrationOption ------------------------------------------------

    def test_options_include_skills_flag(self):
        i = get_integration(self.KEY)
        opts = i.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 1
        assert skills_opts[0].is_flag is True

    # -- Complete file inventory ------------------------------------------

    _SKILL_COMMANDS = [
        "analyze", "checklist", "clarify", "constitution",
        "implement", "plan", "specify", "tasks", "taskstoissues",
    ]

    def _expected_files(self, script_variant: str) -> list[str]:
        """Build the full expected file list for a given script variant."""
        i = get_integration(self.KEY)
        skills_prefix = i.config["folder"].rstrip("/") + "/" + i.config.get("commands_subdir", "skills")

        files = []
        # Skill files
        for cmd in self._SKILL_COMMANDS:
            files.append(f"{skills_prefix}/speckit-{cmd}/SKILL.md")
        # Integration metadata
        files += [
            ".specify/init-options.json",
            ".specify/integration.json",
            f".specify/integrations/{self.KEY}.manifest.json",
            f".specify/integrations/{self.KEY}/scripts/update-context.ps1",
            f".specify/integrations/{self.KEY}/scripts/update-context.sh",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/constitution.md",
        ]
        # Script variant
        if script_variant == "sh":
            files += [
                ".specify/scripts/bash/check-prerequisites.sh",
                ".specify/scripts/bash/common.sh",
                ".specify/scripts/bash/create-new-feature.sh",
                ".specify/scripts/bash/setup-plan.sh",
                ".specify/scripts/bash/update-agent-context.sh",
            ]
        else:
            files += [
                ".specify/scripts/powershell/check-prerequisites.ps1",
                ".specify/scripts/powershell/common.ps1",
                ".specify/scripts/powershell/create-new-feature.ps1",
                ".specify/scripts/powershell/setup-plan.ps1",
                ".specify/scripts/powershell/update-agent-context.ps1",
            ]
        # Templates
        files += [
            ".specify/templates/agent-file-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
        ]
        return sorted(files)

    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by specify init --integration <key> --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-sh-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY,
                "--script", "sh", "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        expected = self._expected_files("sh")
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )

    def test_complete_file_inventory_ps(self, tmp_path):
        """Every file produced by specify init --integration <key> --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"inventory-ps-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY,
                "--script", "ps", "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        expected = self._expected_files("ps")
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
