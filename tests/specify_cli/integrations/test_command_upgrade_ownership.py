"""Migration guards inspect registrations, not disabled manifest declarations."""

import json

import pytest

from specify_cli.integrations._command_upgrade_layout import (
    _PresetRegistryUnreadableError,
    _installed_presets_affecting_agent,
)
from specify_cli.presets import PresetRegistry, PresetResolver
from tests.conftest import install_preset
from tests.specify_cli.integrations._helpers import _init_project, _run_in_project


@pytest.mark.parametrize("include_skills", [True, False])
def test_disabled_inspection_requires_target_agent_ownership(tmp_path, include_skills):
    presets = tmp_path / ".specify" / "presets"
    presets.mkdir(parents=True)
    entries = {
        "enabled-owner": {"registered_commands": {"bob": ["speckit.plan"]}},
        "disabled-owner": {
            "enabled": False,
            "registered_commands": {"bob": ["speckit.tasks"]},
        },
        "disabled-other": {
            "enabled": False,
            "registered_commands": {"claude": ["speckit.plan"]},
            "registered_skills": {"claude": ["speckit-plan"]},
        },
        "disabled-template-only": {"enabled": False},
        "disabled-empty": {
            "enabled": False,
            "registered_commands": {"bob": []},
            "registered_skills": {"bob": []},
        },
        "disabled-skills": {
            "enabled": False,
            "registered_skills": {"bob": ["speckit-plan"]},
        },
        "disabled-legacy-skills": {
            "enabled": False,
            "registered_skills": ["speckit-plan"],
        },
    }
    (presets / ".registry").write_text(
        json.dumps({"presets": entries}), encoding="utf-8"
    )
    assert _installed_presets_affecting_agent(
        tmp_path, "bob", include_disabled=False, include_skills=include_skills
    ) == ["enabled-owner"]
    expected = ["enabled-owner", "disabled-owner"]
    if include_skills:
        expected += ["disabled-skills", "disabled-legacy-skills"]
    assert (
        _installed_presets_affecting_agent(
            tmp_path, "bob", include_disabled=True, include_skills=include_skills
        )
        == expected
    )


@pytest.mark.parametrize("field", ["registered_commands", "registered_skills"])
def test_disabled_ownership_inspection_fails_closed_on_malformed_provenance(
    tmp_path, field
):
    presets = tmp_path / ".specify" / "presets"
    presets.mkdir(parents=True)
    (presets / ".registry").write_text(
        json.dumps(
            {
                "presets": {
                    "disabled": {"enabled": False, field: {"bob": None}},
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(_PresetRegistryUnreadableError, match=field):
        _installed_presets_affecting_agent(tmp_path, "bob", include_disabled=True)


@pytest.mark.parametrize(
    "ownership", ["none", "other-agent", "target-commands", "target-skills"]
)
def test_real_layout_migration_uses_disabled_registration_ownership(
    tmp_path, ownership
):
    project = _init_project(tmp_path, "bob", integration_options="--legacy-commands")
    pack = install_preset(
        project,
        "disabled-preset",
        {
            "templates": [
                {
                    "type": "template",
                    "name": "ownership-template",
                    "file": "templates/ownership.md",
                }
            ]
        },
    )
    (pack / "templates").mkdir()
    (pack / "templates" / "ownership.md").write_text(
        "# template only\n", encoding="utf-8"
    )
    metadata = {"enabled": False, "registered_commands": {}, "registered_skills": {}}
    if ownership == "other-agent":
        metadata.update(
            registered_commands={"claude": ["speckit.plan"]},
            registered_skills={"claude": ["speckit-plan"]},
        )
    elif ownership == "target-commands":
        metadata["registered_commands"] = {"bob": ["speckit.plan"]}
    elif ownership == "target-skills":
        metadata["registered_skills"] = {"bob": ["speckit-plan"]}
    PresetRegistry(project / ".specify" / "presets").update("disabled-preset", metadata)
    targets = [
        project / ".bob" / "commands" / "speckit.plan.md",
        project / ".specify" / "integrations" / "bob.manifest.json",
        project / ".specify" / "presets" / ".registry",
    ]
    before = {path: path.read_bytes() for path in targets}
    result = _run_in_project(
        project,
        [
            "integration",
            "upgrade",
            "bob",
            "--integration-options",
            "--skills",
            "--script",
            "sh",
            "--force",
        ],
    )
    if ownership.startswith("target-"):
        assert result.exit_code != 0, result.output
        assert "disabled-preset" in result.output
        assert not (project / ".bob" / "skills").exists()
        assert {path: path.read_bytes() for path in targets} == before
    else:
        assert result.exit_code == 0, result.output
        assert (project / ".bob" / "skills" / "speckit-plan" / "SKILL.md").is_file()
        assert not targets[0].exists()
        assert targets[2].read_bytes() == before[targets[2]]


def test_enabled_lower_owner_is_not_replaced_by_disabled_higher_inspection(tmp_path):
    project = _init_project(tmp_path, "bob", integration_options="--legacy-commands")
    for preset_id, priority, enabled in [
        ("owner-a", 10, True),
        ("disabled-b", 1, False),
    ]:
        pack = install_preset(
            project,
            preset_id,
            {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
            priority=priority,
        )
        (pack / "commands").mkdir()
        (pack / "commands" / "plan.md").write_text(f"# {preset_id}\n", encoding="utf-8")
        PresetRegistry(project / ".specify" / "presets").update(
            preset_id,
            {
                "enabled": enabled,
                "registered_commands": {"bob": ["speckit.plan"]},
            },
        )
    resolver = PresetResolver(project)
    resolved = resolver.resolve("speckit.plan", "command")
    assert resolved is not None
    assert resolved.read_text(encoding="utf-8") == "# owner-a\n"
    assert _installed_presets_affecting_agent(
        project, "bob", include_disabled=False
    ) == ["owner-a"]
    assert _installed_presets_affecting_agent(
        project, "bob", include_disabled=True
    ) == ["owner-a", "disabled-b"]
    result = _run_in_project(
        project,
        [
            "integration",
            "upgrade",
            "bob",
            "--integration-options",
            "--skills",
            "--script",
            "sh",
            "--force",
        ],
    )
    assert result.exit_code != 0, result.output
    assert "owner-a" in result.output and "disabled-b" in result.output
    resolved = resolver.resolve("speckit.plan", "command")
    assert resolved is not None
    assert resolved.read_text(encoding="utf-8") == "# owner-a\n"
