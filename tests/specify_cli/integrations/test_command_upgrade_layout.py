"""Tests for integration upgrade layout-migration guards."""

import json

import pytest


class TestIntegrationUpgradeLayout:
    def test_installed_presets_affecting_agent_absent_vs_unreadable(self, tmp_path):
        """Unit (review #3415, 4744636079): fail closed only when unreadable.

        The preset guard helper must return an empty list for a genuinely
        absent registry, but raise ``_PresetRegistryUnreadableError`` when the
        registry exists yet cannot be read/parsed — so a layout-changing
        upgrade never proceeds on a false "no presets" result.
        """
        from specify_cli.integrations._command_upgrade_layout import (
            _PresetRegistryUnreadableError,
            _installed_command_presets_affecting_agent,
            _installed_presets_affecting_agent,
        )

        project = tmp_path / "proj"
        project.mkdir()

        # Genuinely absent registry → empty list (safe to proceed).
        assert _installed_presets_affecting_agent(project, "bob") == []

        presets_dir = project / ".specify" / "presets"
        presets_dir.mkdir(parents=True)
        registry = presets_dir / ".registry"

        # Corrupted JSON → unreadable → raise.
        registry.write_text("{ not json", encoding="utf-8")
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")

        # Malformed structure (presets not a dict) → unreadable → raise.
        registry.write_text(json.dumps({"presets": []}), encoding="utf-8")
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")

        # Malformed per-preset entry (not a dict) → ownership unknown → raise.
        registry.write_text(
            json.dumps({"presets": {"p1": []}}), encoding="utf-8"
        )
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")

        # Malformed registered_commands (not a dict) → raise.
        registry.write_text(
            json.dumps({"presets": {"p1": {"registered_commands": []}}}),
            encoding="utf-8",
        )
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")

        # Malformed registered_skills (neither list nor dict) → raise.
        registry.write_text(
            json.dumps({"presets": {"p1": {"registered_skills": "oops"}}}),
            encoding="utf-8",
        )
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")

        # Dict-shaped fields with non-list values (ownership undecidable)
        # must also fail closed, not read as "no artifacts".
        registry.write_text(
            json.dumps(
                {"presets": {"p1": {"registered_skills": {"bob": None}}}}
            ),
            encoding="utf-8",
        )
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")
        registry.write_text(
            json.dumps(
                {"presets": {"p1": {"registered_commands": {"bob": ""}}}}
            ),
            encoding="utf-8",
        )
        with pytest.raises(_PresetRegistryUnreadableError):
            _installed_presets_affecting_agent(project, "bob")

        # Valid, empty registry → empty list.
        registry.write_text(json.dumps({"presets": {}}), encoding="utf-8")
        assert _installed_presets_affecting_agent(project, "bob") == []

        # Valid registry with a preset registered for bob → report its ID.
        # registered_skills comes in two shapes: a legacy flat list (not
        # agent-scoped → fail closed, any entry affects) and the per-agent
        # dict written by preset registration ({agent: [skill names]} → only
        # this agent's entries affect it).
        registry.write_text(
            json.dumps({
                "presets": {
                    "p1": {"registered_commands": {"bob": ["speckit.plan"]}},
                    "p2": {"registered_commands": {"codex": ["speckit.plan"]}},
                    "p3": {"registered_skills": ["speckit-x"]},
                    "p4": {"registered_skills": {"bob": ["speckit-y"]}},
                    "p5": {"registered_skills": {"codex": ["speckit-z"]}},
                    "p6": {"registered_skills": {"bob": []}},
                    "p7": {
                        "enabled": False,
                        "registered_commands": {"bob": ["speckit.tasks"]},
                    },
                }
            }),
            encoding="utf-8",
        )
        assert sorted(_installed_presets_affecting_agent(project, "bob")) == [
            "p1",
            "p3",
            "p4",
            "p7",
        ]
        assert _installed_command_presets_affecting_agent(project, "bob") == [
            "p1",
            "p7",
        ]
