"""Tests for RovodevIntegration."""

from __future__ import annotations

import json
import os

import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


class TestRovodevIntegration:
    KEY = "rovodev"

    def test_key_and_config(self):
        impl = get_integration(self.KEY)
        assert impl is not None
        assert impl.key == self.KEY
        assert impl.config["folder"] == ".rovodev/"
        assert impl.config["commands_subdir"] == "skills"
        assert impl.registrar_config["dir"] == ".rovodev/prompts"
        assert impl.registrar_config["extension"] == ".prompt.md"
        assert impl.context_file == "AGENTS.md"

    def test_inherited_command_filename_for_base_compatibility(self):
        impl = get_integration(self.KEY)
        # RovoDev scaffolding does not use command_filename directly (skills +
        # prompt wrappers), but this guards inherited IntegrationBase behavior.
        assert impl.command_filename("plan") == "speckit.plan.md"

    def test_build_exec_args(self):
        impl = get_integration(self.KEY)
        args = impl.build_exec_args("/speckit.plan add OAuth")
        assert args[0:3] == ["acli", "rovodev", "run"]
        assert args[3] == "/speckit.plan add OAuth"
        assert "--output-schema" in args

    def test_setup_creates_skills_prompts_and_manifest(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        created = impl.setup(tmp_path, manifest)

        prompts_manifest = tmp_path / ".rovodev" / "prompts.yml"
        assert prompts_manifest in created
        assert prompts_manifest.exists()

        prompts_dir = tmp_path / ".rovodev" / "prompts"
        skills_dir = tmp_path / ".rovodev" / "skills"
        assert prompts_dir.is_dir()
        assert skills_dir.is_dir()

        templates = impl.list_command_templates()
        prompt_files = sorted(prompts_dir.glob("speckit.*.prompt.md"))
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir() and d.name.startswith("speckit-"))
        assert len(prompt_files) == len(templates)
        assert len(skill_dirs) == len(templates)
        # Each skill dir has a SKILL.md
        for skill_dir in skill_dirs:
            assert (skill_dir / "SKILL.md").exists()

    def test_prompts_manifest_references_existing_files(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)

        prompts_manifest = tmp_path / ".rovodev" / "prompts.yml"
        data = yaml.safe_load(prompts_manifest.read_text(encoding="utf-8"))
        assert list(data) == ["prompts"]
        entries = data["prompts"]
        assert entries
        for entry in entries:
            assert entry["name"].startswith("speckit.")
            assert entry["description"]
            content_file = tmp_path / ".rovodev" / entry["content_file"]
            assert content_file.exists(), f"Missing prompt file {content_file}"

    def test_prompt_files_delegate_to_paired_skills(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)

        prompt_file = tmp_path / ".rovodev" / "prompts" / "speckit.plan.prompt.md"
        content = prompt_file.read_text(encoding="utf-8")
        assert content == "use skill speckit-plan $ARGUMENTS\n"

    def test_skill_name_conversion_handles_multi_segment_names(self):
        impl = get_integration(self.KEY)
        assert impl._skill_name_to_dot_name("speckit-plan") == "speckit.plan"
        assert (
            impl._skill_name_to_dot_name("speckit-git-commit")
            == "speckit.git.commit"
        )

    def test_prompts_manifest_merge_preserves_user_entries(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)

        prompts_manifest = tmp_path / ".rovodev" / "prompts.yml"
        prompts_manifest.parent.mkdir(parents=True, exist_ok=True)
        prompts_manifest.write_text(
            yaml.safe_dump(
                {
                    "prompts": [
                        {
                            "name": "custom.user.prompt",
                            "description": "User-added prompt",
                            "content_file": "prompts/custom.user.prompt.md",
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        impl.setup(tmp_path, manifest)

        data = yaml.safe_load(prompts_manifest.read_text(encoding="utf-8"))
        names = {entry.get("name") for entry in data.get("prompts", [])}
        assert "custom.user.prompt" in names
        assert "speckit.plan" in names

    def test_skill_files_have_rovodev_frontmatter(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)

        skill_file = tmp_path / ".rovodev" / "skills" / "speckit-plan" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        first_end = content.find("\n---\n")
        assert first_end != -1
        frontmatter = yaml.safe_load(content[4:first_end])
        assert frontmatter["name"] == "speckit-plan"
        assert "description" in frontmatter
        body = content[first_end + len("\n---\n"):]
        assert not body.lstrip().startswith("---\n")

    def test_skill_templates_are_processed(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)

        skills_dir = tmp_path / ".rovodev" / "skills"
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            content = skill_file.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content
            assert "__AGENT__" not in content
            assert "__SPECKIT_COMMAND_" not in content
            assert "\nscripts:\n" not in content


    def test_setup_upserts_context_section(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)
        ctx_path = tmp_path / impl.context_file
        assert ctx_path.exists()
        content = ctx_path.read_text(encoding="utf-8")
        assert "<!-- SPECKIT START -->" in content
        assert "<!-- SPECKIT END -->" in content

    def test_all_created_files_tracked_in_manifest(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        created = impl.setup(tmp_path, manifest)
        for path in created:
            rel = path.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in manifest.files

    def test_install_uninstall_roundtrip(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        created = impl.install(tmp_path, manifest)
        manifest.save()
        removed, skipped = impl.uninstall(tmp_path, manifest)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        created = impl.install(tmp_path, manifest)
        manifest.save()
        modified = tmp_path / ".rovodev" / "prompts.yml"
        modified.write_text("user modified this", encoding="utf-8")
        removed, skipped = impl.uninstall(tmp_path, manifest)
        assert modified.exists()
        assert modified in skipped

    def test_init_inventory_sh(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "rovodev-inventory"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    "rovodev",
                    "--script",
                    "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        prompts_manifest = project / ".rovodev" / "prompts.yml"
        assert prompts_manifest.exists()
        prompt_files = sorted((project / ".rovodev" / "prompts").glob("speckit.*.prompt.md"))
        skills_dir = project / ".rovodev" / "skills"
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir() and d.name.startswith("speckit-"))
        assert len(prompt_files) == 9
        assert len(skill_dirs) == 9
        assert (project / "AGENTS.md").exists()
        assert (project / ".specify" / "integration.json").exists()
        assert (project / ".specify" / "integrations" / "rovodev.manifest.json").exists()
        assert (project / ".specify" / "integrations" / "speckit.manifest.json").exists()
        data = yaml.safe_load(prompts_manifest.read_text(encoding="utf-8"))
        assert len(data["prompts"]) == 9

    def test_init_options_include_context_file(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "opts"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    "rovodev",
                    "--script",
                    "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        init_options = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert init_options["context_file"] == "AGENTS.md"
