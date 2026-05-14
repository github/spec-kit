"""Tests for the bundled ``agent-context`` extension and related plumbing."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli import (
    _load_agent_context_config,
    _save_agent_context_config,
    load_init_options,
    save_init_options,
)
from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.claude import ClaudeIntegration


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "agent-context"


def _write_ext_config(project_root: Path, **overrides: object) -> None:
    """Write a minimal agent-context extension config."""
    cfg: dict = {
        "context_file": overrides.get("context_file", ""),
        "context_markers": overrides.get(
            "context_markers",
            {
                "start": IntegrationBase.CONTEXT_MARKER_START,
                "end": IntegrationBase.CONTEXT_MARKER_END,
            },
        ),
    }
    _save_agent_context_config(project_root, cfg)


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    """The bundled agent-context extension ships a complete package."""

    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
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

    def test_config_template_exists(self):
        cfg = EXT_DIR / "agent-context-config.yml"
        assert cfg.is_file()
        parsed = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        assert "context_file" in parsed
        assert "context_markers" in parsed

    def test_command_file_exists(self):
        cmd = EXT_DIR / "commands" / "speckit.agent-context.update.md"
        assert cmd.is_file()
        assert "agent-context-config.yml" in cmd.read_text(encoding="utf-8")

    def test_bundled_scripts_exist(self):
        assert (EXT_DIR / "scripts" / "bash" / "update-agent-context.sh").is_file()
        assert (EXT_DIR / "scripts" / "powershell" / "update-agent-context.ps1").is_file()

    def test_bash_script_reads_extension_config(self):
        text = (EXT_DIR / "scripts" / "bash" / "update-agent-context.sh").read_text(
            encoding="utf-8"
        )
        # The script must consult the extension config, not init-options.json
        assert "agent-context-config.yml" in text
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


# ── Marker resolution from extension config ──────────────────────────────────


class _CtxIntegration(ClaudeIntegration):
    """Use Claude as a concrete integration with a context_file."""


class TestContextMarkerResolution:
    def test_defaults_when_ext_config_missing(self, tmp_path):
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_defaults_when_markers_field_missing(self, tmp_path):
        _write_ext_config(tmp_path, context_file="CLAUDE.md")
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_custom_markers_respected(self, tmp_path):
        _write_ext_config(
            tmp_path,
            context_markers={"start": "<!-- BEGIN -->", "end": "<!-- END -->"},
        )
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == "<!-- BEGIN -->"
        assert end == "<!-- END -->"

    def test_partial_override_falls_back_for_missing_side(self, tmp_path):
        _write_ext_config(tmp_path, context_markers={"start": "<!-- ONLY START -->"})
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == "<!-- ONLY START -->"
        assert end == IntegrationBase.CONTEXT_MARKER_END

    def test_invalid_markers_fall_back(self, tmp_path):
        _write_ext_config(tmp_path, context_markers={"start": 42, "end": ""})
        i = _CtxIntegration()
        start, end = i._resolve_context_markers(tmp_path)
        assert start == IntegrationBase.CONTEXT_MARKER_START
        assert end == IntegrationBase.CONTEXT_MARKER_END


# ── upsert_context_section / remove_context_section honor markers ───────────


class TestUpsertWithCustomMarkers:
    def _setup(self, tmp_path: Path, markers: dict | None = None) -> _CtxIntegration:
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            **({"context_markers": markers} if markers is not None else {}),
        )
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
        # Extension config absent → default markers used. File contains only
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


# ── Extension config writers ─────────────────────────────────────────────────


class TestExtensionConfigWriters:
    def test_clear_init_options_clears_ext_config_context_file(self, tmp_path):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {"integration": "claude", "ai": "claude"},
        )
        _write_ext_config(tmp_path, context_file="CLAUDE.md")
        _clear_init_options_for_integration(tmp_path, "claude")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg.get("context_file") == ""

    def test_clear_init_options_creates_ext_config_when_missing(self, tmp_path):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {"integration": "claude", "ai": "claude"},
        )
        _clear_init_options_for_integration(tmp_path, "claude")
        cfg = _load_agent_context_config(tmp_path)
        assert cfg.get("context_file") == ""

    def test_clear_init_options_removes_legacy_context_keys_even_when_not_active(
        self, tmp_path
    ):
        from specify_cli import _clear_init_options_for_integration

        save_init_options(
            tmp_path,
            {
                "integration": "copilot",
                "ai": "copilot",
                "context_file": "CLAUDE.md",
                "context_markers": {"start": "<!-- X -->", "end": "<!-- Y -->"},
            },
        )
        _clear_init_options_for_integration(tmp_path, "claude")
        opts = load_init_options(tmp_path)
        assert opts["integration"] == "copilot"
        assert opts["ai"] == "copilot"
        assert "context_file" not in opts
        assert "context_markers" not in opts

    def test_update_init_options_writes_context_file_to_ext_config(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        # Pre-create the extension config so _update_init_options_for_integration
        # updates it (rather than skipping it when ext config doesn't exist yet).
        _write_ext_config(tmp_path, context_file="")
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i, script_type="sh")
        # init-options.json must NOT have context_file or context_markers
        opts = load_init_options(tmp_path)
        assert "context_file" not in opts
        assert "context_markers" not in opts
        # Extension config must have them
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_file"] == i.context_file
        assert "context_markers" in cfg

    def test_update_init_options_preserves_custom_markers(self, tmp_path):
        from specify_cli import _update_init_options_for_integration

        _write_ext_config(
            tmp_path,
            context_file="",
            context_markers={"start": "<!-- B -->", "end": "<!-- E -->"},
        )
        i = _CtxIntegration()
        _update_init_options_for_integration(tmp_path, i)
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_markers"] == {"start": "<!-- B -->", "end": "<!-- E -->"}

    def test_reinit_preserves_custom_markers(self, tmp_path):
        """specify init (reinit) must not overwrite user-customised markers."""
        from specify_cli import _update_agent_context_config_file

        # Simulate existing project with custom markers
        _write_ext_config(
            tmp_path,
            context_file="CLAUDE.md",
            context_markers={"start": "<!-- CUSTOM -->", "end": "<!-- /CUSTOM -->"},
        )
        # Re-running init updates context_file but must preserve markers
        _update_agent_context_config_file(
            tmp_path, "CLAUDE.md", preserve_markers=True
        )
        cfg = _load_agent_context_config(tmp_path)
        assert cfg["context_markers"] == {
            "start": "<!-- CUSTOM -->",
            "end": "<!-- /CUSTOM -->",
        }
