"""Tests for the bundled ``evaluator`` extension.

Validates:
- Bundled layout (manifest, README, three command files, schema, template, scripts)
- Catalog registration
- Wheel/source-checkout resolution via ``_locate_bundled_extension``
- Install via ``ExtensionManager.install_from_directory`` copies the command
  files, schema, template, and scripts and records them in the installed manifest
- Evaluator result JSON Schema validation
- compose_results.py composition logic
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from specify_cli import _locate_bundled_extension


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "evaluator"

EXPECTED_COMMANDS = {
    "speckit.evaluator.run",
    "speckit.evaluator.compose",
    "speckit.evaluator.report",
    "speckit.evaluator.route",
}

EXPECTED_TEMPLATES = {
    "evaluator-result-template",
}

EXPECTED_SCRIPTS = {
    "evaluator-compose",
    "evaluator-compose-sh",
    "evaluator-compose-ps",
}


# ── Bundled extension layout ─────────────────────────────────────────────────


class TestExtensionLayout:
    def test_extension_yml_exists(self):
        assert (EXT_DIR / "extension.yml").is_file()

    def test_extension_yml_has_required_fields(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert manifest["extension"]["id"] == "evaluator"
        assert manifest["extension"]["name"] == "Evaluator Contract"
        assert manifest["extension"]["author"] == "spec-kit-core"
        commands = {c["name"] for c in manifest["provides"]["commands"]}
        assert commands == EXPECTED_COMMANDS

    def test_declares_templates(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        templates = {t["name"] for t in manifest["provides"].get("templates", [])}
        assert templates == EXPECTED_TEMPLATES

    def test_declares_scripts(self):
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        scripts = {s["name"] for s in manifest["provides"].get("scripts", [])}
        assert scripts == EXPECTED_SCRIPTS

    def test_declares_hooks(self):
        """The evaluator extension registers hooks at key lifecycle points."""
        manifest = yaml.safe_load(
            (EXT_DIR / "extension.yml").read_text(encoding="utf-8")
        )
        assert "hooks" in manifest
        hooks = manifest["hooks"]
        expected_events = {"after_specify", "after_plan", "after_tasks", "after_implement"}
        assert set(hooks.keys()) == expected_events
        # Each hook event should reference speckit.evaluator.run
        for event in expected_events:
            entries = hooks[event]
            if not isinstance(entries, list):
                entries = [entries]
            for entry in entries:
                assert entry["command"] == "speckit.evaluator.run"
                assert entry.get("optional") is True

    def test_readme_exists(self):
        readme = EXT_DIR / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        assert "Evaluator Contract Extension" in text

    def test_command_files_exist(self):
        for name in EXPECTED_COMMANDS:
            cmd = EXT_DIR / "commands" / f"{name}.md"
            assert cmd.is_file(), f"Missing command file: {cmd}"

    def test_schema_file_exists(self):
        schema = EXT_DIR / "schemas" / "evaluator-result.schema.json"
        assert schema.is_file()

    def test_template_file_exists(self):
        template = EXT_DIR / "templates" / "evaluator-result-template.json"
        assert template.is_file()

    def test_script_files_exist(self):
        scripts = [
            "scripts/python/compose_results.py",
            "scripts/bash/compose-results.sh",
            "scripts/powershell/compose-results.ps1",
        ]
        for script in scripts:
            path = EXT_DIR / script
            assert path.is_file(), f"Missing script file: {path}"


# ── Catalog registration ─────────────────────────────────────────────────────


class TestCatalogEntry:
    def test_catalog_lists_evaluator_as_bundled(self):
        catalog = json.loads(
            (PROJECT_ROOT / "extensions" / "catalog.json").read_text(encoding="utf-8")
        )
        entry = catalog["extensions"]["evaluator"]
        assert entry["bundled"] is True
        assert entry["id"] == "evaluator"
        assert entry["author"] == "spec-kit-core"


# ── Bundle resolution ────────────────────────────────────────────────────────


class TestBundleResolution:
    def test_locate_bundled_extension_finds_evaluator(self):
        located = _locate_bundled_extension("evaluator")
        assert located is not None
        assert (located / "extension.yml").is_file()


# ── Install ──────────────────────────────────────────────────────────────────


class TestExtensionInstall:
    def test_install_from_directory(self, tmp_path: Path):
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "1.0.0", register_commands=False)

        assert manifest.id == "evaluator"
        assert manager.registry.is_installed("evaluator")

        installed = tmp_path / ".specify" / "extensions" / "evaluator"
        for name in EXPECTED_COMMANDS:
            assert (installed / "commands" / f"{name}.md").is_file()

    def test_install_command_names(self, tmp_path: Path):
        """The installed manifest exposes the expected command names."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "1.0.0", register_commands=False)

        names = {c["name"] for c in manifest.commands}
        assert names == EXPECTED_COMMANDS

    def test_install_copies_schema(self, tmp_path: Path):
        """Schema file is copied into the installed extension directory."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "1.0.0", register_commands=False)

        installed = tmp_path / ".specify" / "extensions" / "evaluator"
        assert (installed / "schemas" / "evaluator-result.schema.json").is_file()

    def test_install_copies_template(self, tmp_path: Path):
        """Template file is copied into the installed extension directory."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "1.0.0", register_commands=False)

        installed = tmp_path / ".specify" / "extensions" / "evaluator"
        assert (installed / "templates" / "evaluator-result-template.json").is_file()

    def test_install_copies_scripts(self, tmp_path: Path):
        """Script files are copied into the installed extension directory."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "1.0.0", register_commands=False)

        installed = tmp_path / ".specify" / "extensions" / "evaluator"
        assert (installed / "scripts" / "python" / "compose_results.py").is_file()
        assert (installed / "scripts" / "bash" / "compose-results.sh").is_file()
        assert (installed / "scripts" / "powershell" / "compose-results.ps1").is_file()

    def test_route_command_file_exists(self):
        """The route command file is present."""
        cmd = EXT_DIR / "commands" / "speckit.evaluator.route.md"
        assert cmd.is_file(), f"Missing command file: {cmd}"


# ── Model Routing ────────────────────────────────────────────────────────────


class TestModelRouting:
    """Test model routing recommendation logic."""

    def test_merge_routing_most_conservative_wins(self):
        """When evaluators disagree on tier, the highest tier wins."""
        from compose_results import _merge_model_routing

        results = [
            {
                "evaluator": {"id": "eval-a"},
                "outcome": "pass",
                "model_routing": {
                    "recommended_tier": "budget",
                    "reason": "Low risk",
                    "escalation_triggers": [],
                    "estimated_tokens": 5000,
                    "estimated_cost_usd": 0.01,
                    "tier_breakdown": {},
                },
            },
            {
                "evaluator": {"id": "eval-b"},
                "outcome": "warn",
                "model_routing": {
                    "recommended_tier": "premium",
                    "reason": "Critical security finding",
                    "escalation_triggers": [
                        {"condition": "New critical finding", "escalate_to": "premium"}
                    ],
                    "estimated_tokens": 3000,
                    "estimated_cost_usd": 0.27,
                    "tier_breakdown": {},
                },
            },
        ]

        merged = _merge_model_routing(results, "warn")
        assert merged is not None
        assert merged["recommended_tier"] == "premium"
        assert "Critical security finding" in merged["reason"]

    def test_merge_routing_no_routing_returns_none(self):
        """When no evaluator provides routing, returns None."""
        from compose_results import _merge_model_routing

        results = [
            {"evaluator": {"id": "eval-a"}, "outcome": "pass"},
            {"evaluator": {"id": "eval-b"}, "outcome": "pass"},
        ]
        assert _merge_model_routing(results, "pass") is None

    def test_merge_routing_single_evaluator(self):
        """Single evaluator routing is passed through."""
        from compose_results import _merge_model_routing

        results = [{
            "evaluator": {"id": "eval-a"},
            "outcome": "pass",
            "model_routing": {
                "recommended_tier": "standard",
                "reason": "Moderate complexity",
                "escalation_triggers": [],
                "estimated_tokens": 8000,
                "estimated_cost_usd": 0.15,
                "tier_breakdown": {
                    "budget": {"estimated_tokens": 12000, "estimated_cost_usd": 0.01},
                    "standard": {"estimated_tokens": 8000, "estimated_cost_usd": 0.15},
                    "premium": {"estimated_tokens": 6000, "estimated_cost_usd": 0.54},
                },
            },
        }]

        merged = _merge_model_routing(results, "pass")
        assert merged is not None
        assert merged["recommended_tier"] == "standard"
        assert merged["tier_breakdown"]["budget"]["estimated_cost_usd"] == 0.01

    def test_compose_includes_model_routing(self, tmp_path: Path):
        """Composed result includes model_routing when evaluators provide it."""
        import json
        from compose_results import compose_results

        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = {
            "schema_version": "1.0",
            "evaluator": {"id": "eval-a", "version": "1.0.0"},
            "phase": "after_plan",
            "outcome": "warn",
            "summary": "Test",
            "findings": [
                {"id": "F-001", "severity": "high", "kind": "security_concern", "subject": "COMP-002"}
            ],
            "next_action": {"kind": "warn", "target_phase": None, "message": ""},
            "metadata": {"timestamp": "2026-01-01T00:00:00Z"},
            "state": {},
            "model_routing": {
                "recommended_tier": "premium",
                "reason": "Security concern requires premium review",
                "escalation_triggers": [],
                "estimated_tokens": 5000,
                "estimated_cost_usd": 0.45,
                "tier_breakdown": {},
            },
        }
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert "model_routing" in composed
        assert composed["model_routing"]["recommended_tier"] == "premium"
