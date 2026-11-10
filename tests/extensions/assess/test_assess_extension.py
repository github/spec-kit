"""Tests for the bundled ``assess`` extension.

Validates:
- Bundled layout (manifest, README, five command files)
- Catalog registration
- Wheel/source-checkout resolution via ``_locate_bundled_extension``
- Install via ``ExtensionManager.install_from_directory`` copies the five
  command files and records them in the installed manifest (command
  registration with AI agents is exercised separately and not asserted here)
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "assess"

EXPECTED_COMMANDS = {
    "speckit.assess.intake",
    "speckit.assess.research",
    "speckit.assess.define",
    "speckit.assess.shape",
    "speckit.assess.decide",
}


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert manifest["extension"]["id"] == "assess"
        assert manifest["extension"]["name"] == "Idea Assessment Pipeline"
        assert manifest["extension"]["author"] == "spec-kit-core"
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert commands == EXPECTED_COMMANDS

    def test_declares_no_hooks(self):
        """assess is a standalone pipeline: it must not register lifecycle
        hooks (e.g. before_specify). Discovery and specification stay
        separate processes; the only coupling is the forward decide ->
        /speckit.specify handoff described in the commands."""
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert "hooks" not in manifest or not manifest["hooks"]

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "Idea Assessment Pipeline Extension" in text

    def test_command_files_exist(self):
        for name in EXPECTED_COMMANDS:
            cmd = EXT_DIR / "commands" / f"{name}.md"
            assert cmd.is_file(), f"Missing command file: {cmd}"

    def test_decide_needs_clarification_step_reports_and_stops(self):
        """The decide report-back must keep refinement and reassessment apart
        (#5325, maintainer direction on PR #5329).

        A needs-clarification verdict means decide reports the blocking
        questions and stops. The *user* supplies the missing information by
        refining the named artifact in place (editing the Markdown directly,
        or explicitly directing an agent), and reassessment then goes through
        re-running the decide command against the updated artifacts -- never
        through the agent revising decision.md on its own. The command used to
        say the unconditional next step was "re-run the named stage" (skipping
        refinement); an interim wording swung the other way and told the agent
        to "revise decision.md" in place (skipping the command). Pin the
        middle: refinement is in place and user-driven, reassessment is an
        explicit decide re-run, and re-running an *earlier* stage stays the
        guarded exception.
        """
        text = (EXT_DIR / "commands" / "speckit.assess.decide.md").read_text(
            encoding="utf-8"
        )
        # The report-back next step is the arrow line; the verdict definition
        # and the decision.md output template also mention the verdict and are
        # deliberately untouched (#4402 kept the output template).
        step = next(
            line
            for line in text.splitlines()
            if line.lstrip().startswith("- **needs-clarification** →")
        )
        # decide reports and stops; it does not resolve the unknowns itself.
        assert "report the blocking questions and stop" in step
        # Refinement happens in the artifact, driven by the user.
        assert "refining the named artifact in place" in step
        # Reassessment goes through the command, not in-place decision edits.
        assert "__SPECKIT_COMMAND_ASSESS_DECIDE__" in step
        assert "revise `decision.md`" not in step
        assert "re-run the named stage" not in step
        # An earlier-stage re-run may be offered only as the guarded
        # exception, after the decide re-run, never as the default next step.
        decide_rerun = step.find("__SPECKIT_COMMAND_ASSESS_DECIDE__")
        earlier = step.find("Re-run an earlier stage")
        assert earlier != -1 and earlier > decide_rerun
        assert "only when" in step[earlier:]


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_assess_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["assess"]
        assert entry["bundled"] is True
        assert entry["id"] == "assess"
        assert entry["author"] == "spec-kit-core"


# ── Bundle resolution ────────────────────────────────────────────────────────


class TestBundleResolution:
    def test_locate_bundled_extension_finds_assess(self):
        located = _locate_bundled_extension("assess")
        assert located is not None
        assert (located / "extension.yml").is_file()


# ── Install ──────────────────────────────────────────────────────────────────


class TestExtensionInstall:
    def test_install_from_directory(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        assert manifest.id == "assess"
        assert manager.registry.is_installed("assess")

        installed = tmp_path / ".specify" / "extensions" / "assess"
        for name in EXPECTED_COMMANDS:
            assert (installed / "commands" / f"{name}.md").is_file()

    def test_install_command_names(self, tmp_path: Path):
        """The installed manifest exposes the expected command names."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        names = {c["name"] for c in manifest.commands}
        assert names == EXPECTED_COMMANDS
