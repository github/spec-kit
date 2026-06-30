"""Tests for RovodevIntegration."""

from __future__ import annotations

import os

import pytest
import yaml
from click.testing import Result
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


def _run_init(project, *flags: str) -> Result:
    """Run ``specify init --here`` in *project* with the given extra flags.

    Centralises the cwd-management boilerplate so individual tests just
    declare the flags they care about.
    """
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        return CliRunner().invoke(
            app,
            ["init", "--here", *flags, "--script", "sh", "--ignore-agent-tools"],
            catch_exceptions=False,
        )
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def rovodev_init_project(tmp_path):
    """Run ``specify init --integration rovodev`` once and return the project root.

    Shared across the slow init-inventory tests so we pay the full-CLI cost
    only once instead of three times.
    """
    project = tmp_path / "rovodev-init"
    project.mkdir()
    result = _run_init(project, "--integration", "rovodev")
    assert result.exit_code == 0, result.output
    return project


class TestRovodevIntegration:
    """Rovodev-specific tests (not inherited from SkillsIntegrationTests because
    rovodev's setup() emits prompt wrappers + prompts.yml in addition to skills,
    which violates the base mixin's pure-skills assumptions)."""

    KEY = "rovodev"

    # -- ACLI dispatch -----------------------------------------------------

    def test_build_exec_args(self):
        impl = get_integration(self.KEY)
        args = impl.build_exec_args("/speckit.plan add OAuth")
        assert args[0:3] == ["acli", "rovodev", "run"]
        assert args[3] == "/speckit.plan add OAuth"
        assert "--output-schema" in args

    def test_build_exec_args_without_json(self):
        impl = get_integration(self.KEY)
        args = impl.build_exec_args("/speckit.plan add OAuth", output_json=False)
        assert args == ["acli", "rovodev", "run", "/speckit.plan add OAuth"]

    def test_build_exec_args_executable_env_override(self, monkeypatch):
        """SPECKIT_INTEGRATION_ROVODEV_EXECUTABLE overrides the binary path.

        Lets operators pin a specific ``acli`` build or relocate the binary
        without modifying the integration. Mirrors codex/devin/claude/etc.
        """
        monkeypatch.setenv("SPECKIT_INTEGRATION_ROVODEV_EXECUTABLE", "/opt/atl/bin/acli")
        impl = get_integration(self.KEY)
        args = impl.build_exec_args("hello", output_json=False)
        assert args == ["/opt/atl/bin/acli", "rovodev", "run", "hello"]

    def test_build_exec_args_executable_env_blank_falls_back(self, monkeypatch):
        """Whitespace/empty env override is treated as unset → default ``acli``."""
        monkeypatch.setenv("SPECKIT_INTEGRATION_ROVODEV_EXECUTABLE", "   ")
        impl = get_integration(self.KEY)
        args = impl.build_exec_args("hello", output_json=False)
        assert args[0] == "acli"

    def test_build_exec_args_extra_args_env_injection(self, monkeypatch):
        """SPECKIT_INTEGRATION_ROVODEV_EXTRA_ARGS injects extra CLI flags.

        Useful for CI or non-interactive contexts that need to pass flags
        the integration doesn't expose. Mirrors the contract on every other
        CLI integration (claude, codex, devin, …).
        """
        monkeypatch.setenv("SPECKIT_INTEGRATION_ROVODEV_EXTRA_ARGS", "--quiet --no-color")
        impl = get_integration(self.KEY)
        args = impl.build_exec_args("hello", output_json=False)
        assert args == [
            "acli", "rovodev", "run", "hello", "--quiet", "--no-color",
        ]

    # -- Setup-level: prompt wrappers + prompts.yml ------------------------

    def test_setup_creates_prompts_and_manifest(self, tmp_path):
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
        prompt_files = sorted(prompts_dir.glob("speckit-*.prompt.md"))
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir() and d.name.startswith("speckit-"))
        assert len(prompt_files) == len(templates)
        assert len(skill_dirs) == len(templates)
        for skill_dir in skill_dirs:
            assert (skill_dir / "SKILL.md").exists()

    def test_prompts_manifest_entries_well_formed(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)

        prompts_manifest = tmp_path / ".rovodev" / "prompts.yml"
        data = yaml.safe_load(prompts_manifest.read_text(encoding="utf-8"))
        assert list(data) == ["prompts"]
        entries = data["prompts"]
        assert entries
        for entry in entries:
            assert entry["name"].startswith("speckit-")
            assert entry["description"]
            content_file = tmp_path / ".rovodev" / entry["content_file"]
            assert content_file.exists(), f"Missing prompt file {content_file}"

    def test_prompt_wrapper_format(self, tmp_path):
        """Every prompt wrapper delegates to its paired skill via 'use skill ...'."""
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.setup(tmp_path, manifest)

        prompts_dir = tmp_path / ".rovodev" / "prompts"
        prompt_files = sorted(prompts_dir.glob("speckit-*.prompt.md"))
        assert prompt_files
        for prompt_file in prompt_files:
            skill_name = prompt_file.name.removesuffix(".prompt.md")
            content = prompt_file.read_text(encoding="utf-8")
            assert content == f"use skill {skill_name} $ARGUMENTS\n", (
                f"{prompt_file} has unexpected wrapper format"
            )

    def test_prompts_manifest_merge_preserves_user_entries(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)

        prompts_manifest = tmp_path / ".rovodev" / "prompts.yml"
        prompts_manifest.parent.mkdir(parents=True, exist_ok=True)
        user_entry = {
            "name": "my-custom-prompt",
            "description": "User-added prompt",
            "content_file": "prompts/my-custom-prompt.md",
        }
        prompts_manifest.write_text(
            yaml.safe_dump({"prompts": [user_entry]}, sort_keys=False),
            encoding="utf-8",
        )

        impl.setup(tmp_path, manifest)

        data = yaml.safe_load(prompts_manifest.read_text(encoding="utf-8"))
        names = {entry.get("name") for entry in data.get("prompts", [])}
        assert "my-custom-prompt" in names
        assert "speckit-plan" in names

    def test_modified_prompts_yml_survives_uninstall(self, tmp_path):
        impl = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        impl.install(tmp_path, manifest)
        manifest.save()
        modified = tmp_path / ".rovodev" / "prompts.yml"
        modified.write_text("user modified this", encoding="utf-8")
        _, skipped = impl.uninstall(tmp_path, manifest)
        assert modified.exists()
        assert modified in skipped

    # -- Full-CLI init: skills + prompts integration with extensions -------

    def test_init_inventory(self, rovodev_init_project):
        """Rovodev + extensions produce the expected skill / prompt set.

        Contract:
          - Rovodev.setup() emits one SKILL.md + one .prompt.md per core template.
          - Extensions install additional SKILL.md directories with NO prompt wrapper.
        """
        project = rovodev_init_project
        impl = get_integration(self.KEY)
        core_skill_names = {
            f"speckit-{t.stem.replace('.', '-')}"
            for t in impl.list_command_templates()
        }

        prompt_files = sorted((project / ".rovodev" / "prompts").glob("speckit-*.prompt.md"))
        prompt_stems = {p.name.removesuffix(".prompt.md") for p in prompt_files}

        skills_dir = project / ".rovodev" / "skills"
        skill_names = {
            d.name for d in skills_dir.iterdir()
            if d.is_dir() and d.name.startswith("speckit-")
        }

        # Prompts: exactly the core template set.
        assert prompt_stems == core_skill_names

        # Skills: exactly the core template set (no extension auto-install).
        assert skill_names == core_skill_names

        # prompts.yml mirrors the prompt files exactly.
        prompts_manifest = project / ".rovodev" / "prompts.yml"
        data = yaml.safe_load(prompts_manifest.read_text(encoding="utf-8"))
        assert {e["name"] for e in data["prompts"]} == core_skill_names

    def test_init_skill_files_well_formed(self, rovodev_init_project):
        """Every speckit-* SKILL.md from full init has valid frontmatter +
        processed body, including extension-installed skills."""
        project = rovodev_init_project
        skills_dir = project / ".rovodev" / "skills"
        skill_dirs = sorted(
            d for d in skills_dir.iterdir()
            if d.is_dir() and d.name.startswith("speckit-")
        )
        assert skill_dirs

        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"Missing {skill_file}"
            content = skill_file.read_text(encoding="utf-8")

            # Frontmatter delimited by leading '---\n' ... '\n---\n'
            assert content.startswith("---\n"), f"{skill_file} missing frontmatter"
            fm_end = content.find("\n---\n", 4)
            assert fm_end != -1, f"{skill_file} has unterminated frontmatter"
            fm = yaml.safe_load(content[4:fm_end])
            body = content[fm_end + len("\n---\n"):]

            assert fm.get("name") == skill_dir.name
            assert fm.get("description")
            assert body.strip(), f"{skill_file} has empty body"

            for placeholder in ("{SCRIPT}", "__AGENT__", "__CONTEXT_FILE__", "__SPECKIT_COMMAND_"):
                assert placeholder not in body, (
                    f"{skill_file} body contains unprocessed placeholder {placeholder!r}"
                )
            # Skills agents must use hyphen-style refs in body.
            assert "/speckit." not in body, (
                f"{skill_file} body contains dot-notation /speckit. reference"
            )

    # -- Full-CLI init: integration metadata -------------------------------

    def test_init_writes_integration_manifest_and_options(self, rovodev_init_project):
        """Full init must produce an integration manifest and well-formed
        init-options.json — used by extensions, presets, and uninstall."""
        import json

        project = rovodev_init_project

        manifest_path = project / ".specify" / "integrations" / "rovodev.manifest.json"
        speckit_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        assert manifest_path.exists(), "rovodev integration manifest missing"
        assert speckit_manifest.exists(), "speckit shared manifest missing"

        init_options = json.loads(
            (project / ".specify" / "init-options.json").read_text(encoding="utf-8")
        )
        assert init_options["integration"] == self.KEY
        assert init_options["ai"] == self.KEY
        # Rovodev is a SkillsIntegration, so ai_skills is auto-set.
        assert init_options.get("ai_skills") is True
        assert init_options.get("script") == "sh"

    def test_integration_flag_creates_expected_files(self, tmp_path):
        """``--integration rovodev`` should create all expected rovodev files."""
        project = tmp_path / "rovodev-int"
        project.mkdir()
        result = _run_init(project, "--integration", "rovodev")
        assert result.exit_code == 0, result.output
        assert (project / ".rovodev" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".rovodev" / "prompts.yml").exists()
        assert (project / ".specify" / "integrations" / "rovodev.manifest.json").exists()
