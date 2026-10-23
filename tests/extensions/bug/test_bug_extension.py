"""Tests for the bundled ``bug`` extension.

Validates:
- Bundled layout (manifest, README, three command files)
- Catalog registration
- Wheel/source-checkout resolution via ``_locate_bundled_extension``
- Install via ``ExtensionManager.install_from_directory`` copies the three
  command files and records them in the installed manifest (command
  registration with AI agents is exercised separately and not asserted here)
- Command-template guardrails for re-assessed bugs: the README documents the
  installed (hyphenated) skill names, re-assessment offers to rename the old
  fix/test reports instead of deleting them, and validation refuses a fix
  report older than the current assessment
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "bug"

EXPECTED_COMMANDS = {
    "speckit.bug.assess",
    "speckit.bug.fix",
    "speckit.bug.test",
}


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert manifest["extension"]["id"] == "bug"
        assert manifest["extension"]["name"] == "Bug Triage Workflow"
        assert manifest["extension"]["author"] == "spec-kit-core"
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert commands == EXPECTED_COMMANDS

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "Bug Triage Workflow Extension" in text

    def test_readme_documents_installed_skill_names(self):
        """The README shows the hyphenated names agents install the commands as."""
        text = (EXT_DIR / "README.md").read_text(encoding="utf-8")
        for installed in ("speckit-bug-assess", "speckit-bug-fix", "speckit-bug-test"):
            assert installed in text

    def test_readme_documents_per_agent_invocation_spellings(self):
        """The README distinguishes slash, dollar, and skill-colon invocations."""
        text = (EXT_DIR / "README.md").read_text(encoding="utf-8")
        assert "/speckit-bug-assess" in text
        assert "$speckit-bug-assess" in text
        assert "/skill:speckit-bug-assess" in text

    def test_command_files_exist(self):
        for name in EXPECTED_COMMANDS:
            cmd = EXT_DIR / "commands" / f"{name}.md"
            assert cmd.is_file(), f"Missing command file: {cmd}"


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_bug_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["bug"]
        assert entry["bundled"] is True
        assert entry["id"] == "bug"
        assert entry["author"] == "spec-kit-core"


# ── Bundle resolution ────────────────────────────────────────────────────────


class TestBundleResolution:
    def test_locate_bundled_extension_finds_bug(self):
        located = _locate_bundled_extension("bug")
        assert located is not None
        assert (located / "extension.yml").is_file()


# ── Install ──────────────────────────────────────────────────────────────────


class TestExtensionInstall:
    def test_install_from_directory(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        assert manifest.id == "bug"
        assert manager.registry.is_installed("bug")

        # All three command files are copied into the installed extension dir
        installed = tmp_path / ".specify" / "extensions" / "bug"
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


# ── Stale-report guardrails ──────────────────────────────────────────────────


class TestStaleReportGuardrails:
    """Static checks for the re-assessment flow (stale fix/test reports).

    Re-assessing a bug that already has ``fix.md`` / ``test.md`` must offer to
    rename the older reports instead of deleting them, and validation must
    refuse a fix report that predates the current assessment.
    """

    def test_assess_template_offers_stale_rename(self):
        text = (EXT_DIR / "commands" / "speckit.bug.assess.md").read_text(
            encoding="utf-8"
        )
        assert "fix.stale.md" in text
        assert "test.stale.md" in text
        assert "never delete" in text.lower()

    def test_assess_template_flags_declined_reports_as_stale(self):
        text = (EXT_DIR / "commands" / "speckit.bug.assess.md").read_text(
            encoding="utf-8"
        )
        assert "stale" in text

    def test_test_template_refuses_fix_older_than_assessment(self):
        text = (EXT_DIR / "commands" / "speckit.bug.test.md").read_text(
            encoding="utf-8"
        )
        assert "Staleness check" in text
        assert "__SPECKIT_COMMAND_BUG_FIX__ slug=" in text

    def test_test_template_falls_back_to_modification_times(self):
        text = (EXT_DIR / "commands" / "speckit.bug.test.md").read_text(
            encoding="utf-8"
        )
        assert "modification times" in text

    def test_readme_describes_stale_report_behavior(self):
        text = (EXT_DIR / "README.md").read_text(encoding="utf-8")
        assert "fix.stale.md" in text
        assert "predates the current" in text
