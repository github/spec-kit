"""Tests for the bundled ``bug`` extension.

Validates:
- Bundled layout (manifest, README, config template, command files)
- Catalog registration
- Wheel/source-checkout resolution via ``_locate_bundled_extension``
- Install via ``ExtensionManager.install_from_directory`` copies the
  command files and records them in the installed manifest (command
  registration with AI agents is exercised separately and not asserted here)
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
    "speckit.bug.issue",
    "speckit.bug.fetch",
    "speckit.bug.fix",
    "speckit.bug.pr",
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

    def test_command_files_exist(self):
        for name in EXPECTED_COMMANDS:
            cmd = EXT_DIR / "commands" / f"{name}.md"
            assert cmd.is_file(), f"Missing command file: {cmd}"

    def test_config_template_exists(self):
        assert (EXT_DIR / "config-template.yml").is_file()


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


class TestAutoCreateIssueHook:
    """The bug extension must register a non-optional create-issue hook.

    When ``auto_create_issue`` is enabled, the ``after_bug_assess`` hook runs
    ``speckit.bug.issue`` automatically (optional: false). The hook is gated by
    a ``config.auto_create_issue == 'true'`` condition so it only fires when the
    user has opted in.
    """

    def test_manifest_declares_hook_optional_false(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        hooks = manifest.get("hooks", {})
        assert "after_bug_assess" in hooks

        entry = hooks["after_bug_assess"]
        # Accept either the single-mapping or list form.
        if isinstance(entry, list):
            entry = entry[0]
        assert entry["command"] == "speckit.bug.issue"
        assert entry["optional"] is False
        assert entry["condition"] == "config.auto_create_issue == 'true'"

    def test_register_hooks_writes_optional_false(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager, HookExecutor

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        executor = HookExecutor(tmp_path)
        config = executor.get_project_config()
        hook_entries = config.get("hooks", {}).get("after_bug_assess", [])
        assert hook_entries, "after_bug_assess hook was not registered"

        hook = hook_entries[0]
        assert hook["extension"] == "bug"
        assert hook["command"] == "speckit.bug.issue"
        # The create-issue hook must be mandatory (optional: false), not a
        # soft suggestion the agent may skip.
        assert hook["optional"] is False
        assert hook["condition"] == "config.auto_create_issue == 'true'"

    def test_hook_fires_only_when_auto_create_issue_enabled(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager, HookExecutor

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "0.9.0", register_commands=False)

        executor = HookExecutor(tmp_path)
        # No config present (auto_create_issue absent) -> condition fails -> no
        # executable hook.
        result = executor.check_hooks_for_event("after_bug_assess")
        assert result["has_hooks"] is False

        # Enable auto_create_issue and re-check: the hook becomes executable.
        config_dir = tmp_path / ".specify" / "extensions" / "bug"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "bug-config.yml").write_text(
            "auto_create_issue: true\n", encoding="utf-8"
        )

        result = executor.check_hooks_for_event("after_bug_assess")
        assert result["has_hooks"] is True
        assert result["hooks"][0]["command"] == "speckit.bug.issue"

