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
            "agent", "arch", "governance", "analyze", "checklist", "clarify", "constitution",
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
        """SKILL.md must have governance contract frontmatter."""
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
            assert "purpose" in fm, f"{f} frontmatter missing 'purpose'"
            assert "trigger" in fm, f"{f} frontmatter missing 'trigger'"
            assert "allowed-read-paths" in fm, f"{f} frontmatter missing 'allowed-read-paths'"
            assert "allowed-write-paths" in fm, f"{f} frontmatter missing 'allowed-write-paths'"
            assert "forbidden-paths" in fm, f"{f} frontmatter missing 'forbidden-paths'"
            assert "outputs" in fm, f"{f} frontmatter missing 'outputs'"
            assert "validation-command" in fm, f"{f} frontmatter missing 'validation-command'"
            assert "compatibility" in fm, f"{f} frontmatter missing 'compatibility'"
            assert "metadata" in fm, f"{f} frontmatter missing 'metadata'"
            assert ".specify/**" in fm["allowed-read-paths"]
            assert ".git/**" in fm["forbidden-paths"]
            if fm["name"] == "speckit-implement":
                assert "**" in fm["allowed-write-paths"]
                assert "Implementation files, completed tasks.md checkboxes, validation results, and handoff summary" in fm["outputs"]
            else:
                assert fm["allowed-write-paths"] == [".specify/**", "specs/**"]
                assert "Workflow-specific spec artifacts and handoff summary" in fm["outputs"]
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
            assert "__SPECKIT_COMMAND_" not in content, f"{f.name} has unprocessed __SPECKIT_COMMAND_*__"

    def test_command_refs_use_hyphen_separator(self, tmp_path):
        """Skills agents must resolve command refs with hyphen separator."""
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        skill_files = [f for f in created if "scripts" not in f.parts]
        assert len(skill_files) > 0
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            # Skills agents must use /speckit-<name>, not /speckit.<name>
            assert "/speckit." not in content, (
                f"{f.name} contains dot-notation /speckit. reference; "
                f"skills agents must use /speckit-<name>"
            )

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

    def test_plan_references_correct_context_file(self, tmp_path):
        """The generated plan skill must reference this integration's context file."""
        i = get_integration(self.KEY)
        if not i.context_file:
            return
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        plan_file = i.skills_dest(tmp_path) / "speckit-plan" / "SKILL.md"
        assert plan_file.exists(), f"Plan skill {plan_file} not created"
        content = plan_file.read_text(encoding="utf-8")
        assert i.context_file in content, (
            f"Plan skill should reference {i.context_file!r} but it was not found"
        )
        assert "__CONTEXT_FILE__" not in content, (
            "Plan skill has unprocessed __CONTEXT_FILE__ placeholder"
        )

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

    # -- Context section ---------------------------------------------------

    def test_setup_upserts_context_section(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        if i.context_file:
            ctx_path = tmp_path / i.context_file
            assert ctx_path.exists(), f"Context file {i.context_file} not created for {self.KEY}"
            content = ctx_path.read_text(encoding="utf-8")
            assert "<!-- SPECKIT START -->" in content
            assert "<!-- SPECKIT END -->" in content
            assert "read the current plan" in content

    def test_teardown_removes_context_section(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m)
        m.save()
        if i.context_file:
            ctx_path = tmp_path / i.context_file
            content = ctx_path.read_text(encoding="utf-8")
            ctx_path.write_text("# My Rules\n\n" + content + "\n# Footer\n", encoding="utf-8")
            i.teardown(tmp_path, m)
            remaining = ctx_path.read_text(encoding="utf-8")
            assert "<!-- SPECKIT START -->" not in remaining
            assert "<!-- SPECKIT END -->" not in remaining
            assert "# My Rules" in remaining

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
        i = get_integration(self.KEY)
        skills_dir = i.skills_dest(project)
        assert skills_dir.is_dir(), f"--ai {self.KEY} did not create skills directory"

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

    def test_init_options_includes_context_file(self, tmp_path):
        """init-options.json must include context_file for the active integration."""
        import json
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / f"opts-{self.KEY}"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", self.KEY, "--script", "sh",
                "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        opts = json.loads((project / ".specify" / "init-options.json").read_text())
        i = get_integration(self.KEY)
        assert opts.get("context_file") == i.context_file, (
            f"Expected context_file={i.context_file!r}, got {opts.get('context_file')!r}"
        )

    # -- IntegrationOption ------------------------------------------------

    def test_options_include_skills_flag(self):
        i = get_integration(self.KEY)
        opts = i.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 1
        assert skills_opts[0].is_flag is True

    # -- Complete file inventory ------------------------------------------

    _SKILL_COMMANDS = [
        "agent", "arch", "governance", "analyze", "checklist", "clarify", "constitution",
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
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/agent-governance.md",
            ".specify/memory/constitution.md",
        ]
        # Script variant
        if script_variant == "sh":
            files += [
                ".specify/scripts/bash/check-prerequisites.sh",
                ".specify/scripts/bash/common.sh",
                ".specify/scripts/bash/create-new-feature.sh",
                ".specify/scripts/bash/setup-arch.sh",
                ".specify/scripts/bash/setup-plan.sh",
                ".specify/scripts/bash/setup-tasks.sh",
            ]
        else:
            files += [
                ".specify/scripts/powershell/check-prerequisites.ps1",
                ".specify/scripts/powershell/common.ps1",
                ".specify/scripts/powershell/create-new-feature.ps1",
                ".specify/scripts/powershell/setup-arch.ps1",
                ".specify/scripts/powershell/setup-plan.ps1",
                ".specify/scripts/powershell/setup-tasks.ps1",
            ]
        # Templates
        files += [
            ".specify/templates/agent-governance-template.md",
            ".specify/templates/architecture-development-template.md",
            ".specify/templates/architecture-logical-template.md",
            ".specify/templates/architecture-physical-template.md",
            ".specify/templates/architecture-process-template.md",
            ".specify/templates/architecture-scenario-template.md",
            ".specify/templates/architecture-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
        ]
        # Bundled workflow
        files += [
            ".specify/workflows/speckit/workflow.yml",
            ".specify/workflows/workflow-registry.json",
        ]
        # Agent context file (if set)
        if i.context_file:
            files.append(i.context_file)
        files.append("AGENTS.md")
        return sorted(set(files))

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
