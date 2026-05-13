"""Tests for the bundled ``agent-context`` extension and related plumbing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli import (
    INIT_OPTIONS_FILE,
    load_init_options,
    save_init_options,
)
from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.claude import ClaudeIntegration


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "agent-context"


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    """The bundled agent-context extension ships a complete package."""

    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        import yaml

        manifest = yaml.safe_load((EXT_DIR / "extension.yml").read_text())
        assert manifest["extension"]["id"] == "agent-context"
        assert manifest["extension"]["name"] == "Coding Agent Context"
        assert manifest["extension"]["author"] == "spec-kit-core"
        # Provides at least the manual update command
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert "speckit.agent-context.update" in commands

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "Coding Agent Context Extension" in text

    def test_command_file_exists(self):
        cmd = EXT_DIR / "commands" / "speckit.agent-context.update.md"
        assert cmd.is_file()
        assert "init-options.json" in cmd.read_text(encoding="utf-8")

    def test_bundled_scripts_exist(self):
        assert (EXT_DIR / "scripts" / "bash" / "update-agent-context.sh").is_file()
        assert (EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1").is_file()

    def test_bash_script_reads_init_options(self):
        text = (EXT_DIR / "scripts" / "bash" / "update-agent-context.sh").read_text(
            encoding="utf-8"
        )
        # The script must consult init-options.json — no agent-specific logic
        assert "init-options.json" in text
        assert "context_file" in text
        assert "context_markers" in text


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_agent_context_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["agent-context"]
        assert entry["bundled"] is True
        assert entry["id"] == "agent-context"
        assert entry["author"] == "spec-kit-core"


# ── Marker resolution from init-options.json ─────────────────────────────────


class _CtxIntegration(ClaudeIntegration):
    """Use Claude as a concrete integration with a context_file."""


class TestContextMarkerResolution:
    def _seed_options(self, project_root: Path, **overrides):
        save_init_options(project_root, overrides)

    def test_defaults_when_init_options_missing(self, tmp_path):
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_defaults_when_field_missing(self, tmp_path):
        self._seed_options(tmp_path, context_file="CLAUDE.md")
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_custom_markers_respected(self, tmp_path):
        self._seed_options(
            tmp_path,
            context_markers={"start": "<!-- BEGIN -->", "end": "<!-- END -->"},
        )
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == "<!-- BEGIN -->"
        assert end == "<!-- END -->"

    def test_partial_override_falls_back_for_missing_side(self, tmp_path):
        self._seed_options(tmp_path, context_markers={"start": "<!-- ONLY START -->"})
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == "<!-- ONLY START -->"
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_invalid_markers_fall_back(self, tmp_path):
        self._seed_options(tmp_path, context_markers={"start": 42, "end": ""})
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END


# ── upsert_context_section / remove_context_section honor markers ───────────


class TestUpsertWithCustomMarkers:
    def _setup(self, tmp_path: Path, markers: dict | None = None) -> _CtxIntegration:
        opts: dict = {"context_file": "CLAUDE.md"}
        if markers is not None:
            opts["context_markers"] = markers
        save_init_options(tmp_path, opts)
        return _CtxIntegration()

    def test_upsert_uses_default_markers(self, tmp_path):
        i = self._setup(tmp_path)
        result = i.upsert_context_section(tmp_path)
        assert result is not None
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert IntegrationBase.CONTEXT_MARKER_START in text
        assert IntegrationBase.CONTEXT_MARKER_END in text

    def test_upsert_uses_custom_markers(self, tmp_path):
        i = self._setup(
            tmp_path, {"start": "<!-- BEGIN -->", "end": "<!-- END -->"}
        )
        i.upsert_context_section(tmp_path)
        text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "<!-- BEGIN -->" in text
        assert "<!-- END -->" in text
        # Defaults must not appear
        assert IntegrationBase.CONTEXT_MARKER_START not in text
        assert IntegrationBase.CONTEXT_MARKER_END not in text

    def test_upsert_replaces_existing_custom_section(self, tmp_path):
        i = self._setup(
            tmp_path, {"start": "<!-- BEGIN -->", "end": "<!-- END -->"}
        )
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(
            "# header\n\n<!-- BEGIN -->\nold body\n<!-- END -->\n\nfooter\n",
            encoding="utf-8",
        )
        i.upsert_context_section(tmp_path, plan_path="specs/001-foo/plan.md")
        text = ctx.read_text(encoding="utf-8")
        assert "old body" not in text
        assert "specs/001-foo/plan.md" in text
        assert text.startswith("# header\n")
        assert "footer" in text

    def test_remove_uses_custom_markers(self, tmp_path):
        i = self._setup(
            tmp_path, {"start": "<!-- BEGIN -->", "end": "<!-- END -->"}
        )
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(
            "preamble\n\n<!-- BEGIN -->\nbody\n<!-- END -->\nepilogue\n",
            encoding="utf-8",
        )
        removed = i.remove_context_section(tmp_path)
        assert removed is True
        remaining = ctx.read_text(encoding="utf-8")
        assert "<!-- BEGIN -->" not in remaining
        assert "<!-- END -->" not in remaining
        assert "body" not in remaining
        assert "preamble" in remaining
        assert "epilogue" in remaining

    def test_remove_with_default_markers_unchanged_when_custom_in_file(self, tmp_path):
        # init-options.json absent → default markers used. File contains only
        # custom markers — nothing should be removed.
        i = _CtxIntegration()
        ctx = tmp_path / "CLAUDE.md"
        original = "x\n<!-- BEGIN -->\nbody\n<!-- END -->\n"
        ctx.write_text(original, encoding="utf-8")
        assert i.remove_context_section(tmp_path) is False
        assert ctx.read_text(encoding="utf-8") == original


# ── Extension disabled gates setup/teardown ──────────────────────────────────


def _write_registry(project_root: Path, *, enabled: bool) -> None:
    registry = project_root / ".specify" / "extensions" / ".registry"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "extensions": {
                    "agent-context": {
                        "version": "1.0.0",
                        "enabled": enabled,
                    }
                },
            }
        ),
        encoding="utf-8",
    )


class TestExtensionEnabledGate:
    def test_enabled_helper_default_when_no_registry(self, tmp_path):
        assert IntegrationBase._agent_context_extension_enabled(tmp_path) is True

    def test_enabled_helper_when_entry_present(self, tmp_path):
        _write_registry(tmp_path, enabled=True)
        assert IntegrationBase._agent_context_extension_enabled(tmp_path) is True

    def test_disabled_helper_when_entry_disabled(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        assert IntegrationBase._agent_context_extension_enabled(tmp_path) is False

    def test_upsert_skipped_when_disabled(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        i = _CtxIntegration()
        result = i.upsert_context_section(tmp_path)
        assert result is None
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_remove_skipped_when_disabled(self, tmp_path):
        _write_registry(tmp_path, enabled=False)
        i = _CtxIntegration()
        ctx = tmp_path / "CLAUDE.md"
        original = (
            f"head\n{IntegrationBase.CONTEXT_MARKER_START}\nbody\n"
            f"{IntegrationBase.CONTEXT_MARKER_END}\ntail\n"
        )
        ctx.write_text(original, encoding="utf-8")
        assert i.remove_context_section(tmp_path) is False
        # File must be unchanged when extension is disabled
        assert ctx.read_text(encoding="utf-8") == original


# ── init-options writers seed default markers ────────────────────────────────


class TestInitOptionsWriters:
    def test_clear_init_options_pops_context_markers(self, tmp_path):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {
                "integration": "claude",
                "ai": "claude",
                "context_file": "CLAUDE.md",
                "context_markers": {
                    "start": IntegrationBase.CONTEXT_MARKER_START,
                    "end": IntegrationBase.CONTEXT_MARKER_END,
                },
            },
        )
        _clear_init_options_for_integration(tmp_path, "claude")
        opts = load_init_options(tmp_path)
        assert "context_file" not in opts
        assert "context_markers" not in opts

    def test_update_init_options_seeds_default_markers(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i, script_type="sh")
        opts = load_init_options(tmp_path)
        assert opts["integration"] == i.key
        assert opts["context_file"] == i.context_file
        assert opts["context_markers"] == {
            "start": IntegrationBase.CONTEXT_MARKER_START,
            "end": IntegrationBase.CONTEXT_MARKER_END,
        }

    def test_update_init_options_preserves_custom_markers(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        save_init_options(
            tmp_path,
            {"context_markers": {"start": "<!-- B -->", "end": "<!-- E -->"}},
        )
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i)
        opts = load_init_options(tmp_path)
        assert opts["context_markers"] == {"start": "<!-- B -->", "end": "<!-- E -->"}
