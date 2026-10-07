"""Tests for the shared ``artifact.info`` operation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from specify_cli import artifacts
from specify_cli.artifacts import (
    ArtifactCatalog,
    ArtifactResolutionError,
    _operation_info,
)
from specify_cli.artifacts._operation_info import (
    ARTIFACT_INFO_OPERATION,
    ArtifactInfoAmbiguousError,
    ArtifactInfoHookArtifact,
    ArtifactInfoHookNotFoundError,
    ArtifactInfoIdentifierError,
    ArtifactInfoInvalidResultError,
    ArtifactInfoKindError,
    ArtifactInfoNamedArtifact,
    ArtifactInfoNotFoundError,
    ArtifactInfoProjectDirectoryError,
    ArtifactInfoProjectError,
    ArtifactInfoRequest,
    ArtifactInfoResolutionError,
    ArtifactInfoResult,
    get_artifact_info,
)
from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import PresetError
from tests.conftest import install_preset
from tests.specify_cli.artifacts.helpers import install_extension_with_hooks


def test_artifact_info_operation_descriptor_is_stable():
    assert ARTIFACT_INFO_OPERATION.operation_id == "artifact.info"
    assert ARTIFACT_INFO_OPERATION.contract_version == "1"
    assert ARTIFACT_INFO_OPERATION.request_type is ArtifactInfoRequest
    assert ARTIFACT_INFO_OPERATION.result_type is ArtifactInfoResult
    assert ARTIFACT_INFO_OPERATION.warning_types == ()
    assert ARTIFACT_INFO_OPERATION.error_types == (
        ArtifactInfoProjectDirectoryError,
        ArtifactInfoProjectError,
        ArtifactInfoKindError,
        ArtifactInfoIdentifierError,
        ArtifactInfoNotFoundError,
        ArtifactInfoHookNotFoundError,
        ArtifactInfoAmbiguousError,
        ArtifactInfoResolutionError,
        ArtifactInfoInvalidResultError,
    )
    assert ARTIFACT_INFO_OPERATION.capabilities == frozenset({"local-read"})
    assert ARTIFACT_INFO_OPERATION.network_access == "none"


def test_get_artifact_info_returns_complete_typed_core_result(
    spec_kit_project: Path,
):
    request = ArtifactInfoRequest(
        project_directory=spec_kit_project,
        identifier="command:speckit.constitution",
    )

    result = get_artifact_info(request)
    payload = result.to_json_dict()

    assert isinstance(result, ArtifactInfoResult)
    assert isinstance(result.artifact, ArtifactInfoNamedArtifact)
    assert payload == ArtifactCatalog(spec_kit_project).get_artifact_info(
        request.identifier
    )
    assert set(payload) == {"id", "name", "kind", "description", "stack"}
    assert payload["id"] == "command:speckit.constitution"
    assert payload["stack"]
    assert all(
        set(entry)
        == {
            "id",
            "layer",
            "sourceId",
            "presetId",
            "presetName",
            "strategy",
            "active",
            "hidden",
            "manifestPath",
            "lookupId",
            "sourcePath",
        }
        for entry in payload["stack"]
    )


def test_bare_name_and_public_id_are_identical(spec_kit_project: Path):
    by_name = get_artifact_info(ArtifactInfoRequest(spec_kit_project, "speckit.plan"))
    by_id = get_artifact_info(
        ArtifactInfoRequest(spec_kit_project, "command:speckit.plan")
    )

    assert by_name == by_id


@pytest.mark.parametrize(
    ("identifier", "kind"),
    [
        ("speckit.constitution", "command"),
        ("spec-template", "template"),
        ("setup-plan", "script"),
    ],
)
def test_explicit_kind_selects_each_named_family(
    spec_kit_project: Path,
    identifier: str,
    kind: str,
):
    result = get_artifact_info(
        ArtifactInfoRequest(
            spec_kit_project,
            identifier,
            kind=kind,  # type: ignore[arg-type]
        )
    )

    assert result.artifact.kind == kind
    assert result.to_json_dict() == ArtifactCatalog(spec_kit_project).get_artifact_info(
        identifier, kind=kind
    )  # type: ignore[arg-type]


def test_hook_result_preserves_encoded_identity_and_stack_metadata(
    spec_kit_project: Path,
):
    install_extension_with_hooks(
        spec_kit_project,
        "quality",
        hooks={
            "custom:after": [
                {
                    "command": "/skill:speckit-quality",
                    "description": "Réview hook",
                    "priority": 4,
                    "optional": False,
                }
            ]
        },
    )
    identifier = "hook:custom%3Aafter:%2Fskill%3Aspeckit-quality"

    result = get_artifact_info(ArtifactInfoRequest(spec_kit_project, identifier))
    payload = result.to_json_dict()

    assert isinstance(result.artifact, ArtifactInfoHookArtifact)
    assert payload == ArtifactCatalog(spec_kit_project).get_artifact_info(identifier)
    assert payload["name"] == "custom%3Aafter:%2Fskill%3Aspeckit-quality"
    assert payload["eventName"] == "custom:after"
    assert payload["targetCommand"] == "/skill:speckit-quality"
    assert payload["description"] == "Réview hook"
    assert payload["stack"] == [
        {
            "id": identifier,
            "layer": "extension",
            "sourceId": "quality",
            "presetId": None,
            "presetName": None,
            "strategy": "additive",
            "active": False,
            "hidden": False,
            "manifestPath": ".specify/extensions/quality/extension.yml",
            "lookupId": (
                "extension:quality:hook:custom%3Aafter:%2Fskill%3Aspeckit-quality"
            ),
            "sourcePath": None,
            "priority": 4,
            "optional": False,
        }
    ]


def test_info_preserves_unicode_paths_and_matches_list_row(
    spec_kit_project: Path,
):
    extension_dir = spec_kit_project / ".specify" / "extensions" / "quality"
    template = extension_dir / "templates" / "réview.md"
    template.parent.mkdir(parents=True)
    template.write_text("---\ndescription: Réview ✓\n---\n", encoding="utf-8")
    (extension_dir / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "quality",
                    "name": "Quality",
                    "version": "1.0.0",
                    "description": "test",
                    "author": "test",
                    "repository": "https://example.com",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.2.0"},
                "provides": {
                    "templates": [
                        {
                            "name": "réview",
                            "file": "templates/réview.md",
                            "description": "Réview ✓",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    ExtensionRegistry(spec_kit_project / ".specify" / "extensions").add(
        "quality",
        {"version": "1.0.0", "enabled": True},
    )

    result = get_artifact_info(
        ArtifactInfoRequest(spec_kit_project, "template:réview")
    ).to_json_dict()
    list_row = next(
        row
        for row in ArtifactCatalog(spec_kit_project).list_artifacts_with_stack()
        if row["id"] == "template:réview"
    )

    assert result == list_row
    assert result["name"] == "réview"
    assert result["description"] == "Réview ✓"
    assert result["stack"][0]["sourcePath"] == (
        ".specify/extensions/quality/templates/réview.md"
    )


def test_info_preserves_preset_layer_order(spec_kit_project: Path):
    for pack_id, priority, strategy in (
        ("top", 5, "prepend"),
        ("lower", 10, "append"),
    ):
        pack = install_preset(
            spec_kit_project,
            pack_id,
            {
                "templates": [
                    {
                        "name": "spec-template",
                        "strategy": strategy,
                        "description": f"{pack_id} description",
                    }
                ]
            },
            priority=priority,
        )
        (pack / "templates").mkdir()
        (pack / "templates" / "spec-template.md").write_text(
            f"{pack_id} content",
            encoding="utf-8",
        )

    result = get_artifact_info(
        ArtifactInfoRequest(spec_kit_project, "template:spec-template")
    ).to_json_dict()

    assert [entry["sourceId"] for entry in result["stack"][:2]] == [
        "top",
        "lower",
    ]
    assert [entry["strategy"] for entry in result["stack"]] == [
        "prepend",
        "append",
        "replace",
    ]


def test_info_is_stable_across_repeated_calls(spec_kit_project: Path):
    request = ArtifactInfoRequest(spec_kit_project, "speckit.plan")

    assert get_artifact_info(request) == get_artifact_info(request)


def test_info_isolates_sequential_explicit_projects(
    spec_kit_project: Path,
    tmp_path: Path,
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    second = tmp_path / "second"
    second.mkdir()
    (second / ".specify").mkdir()
    (second / ".specify" / "presets").mkdir()
    (second / ".specify" / "extensions").mkdir()
    (second / ".specify" / "templates").mkdir()
    first_override = spec_kit_project / ".specify" / "templates" / "overrides"
    second_override = second / ".specify" / "templates" / "overrides"
    first_override.mkdir(parents=True)
    second_override.mkdir(parents=True)
    (first_override / "isolated.md").write_text(
        "---\ndescription: First\n---\n",
        encoding="utf-8",
    )
    (second_override / "isolated.md").write_text(
        "---\ndescription: Second\n---\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(non_project)

    first = get_artifact_info(ArtifactInfoRequest(spec_kit_project, "command:isolated"))
    second_result = get_artifact_info(ArtifactInfoRequest(second, "command:isolated"))

    assert first.artifact.description == "First"
    assert second_result.artifact.description == "Second"
    assert Path.cwd() == non_project


def test_info_rejects_relative_project_directory():
    with pytest.raises(ArtifactInfoProjectDirectoryError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(Path("relative"), "speckit.plan"))

    assert exc_info.value.code == "invalid_project_directory"
    assert exc_info.value.details == {"project_directory": "relative"}


def test_info_rejects_non_project_before_catalog_lookup(
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    catalog = Mock(side_effect=AssertionError("catalog reached"))
    monkeypatch.setattr(_operation_info, "ArtifactCatalog", catalog)

    with pytest.raises(ArtifactInfoProjectError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(non_project, "speckit.plan"))

    assert exc_info.value.code == "not_a_spec_kit_project"
    assert exc_info.value.details == {"project_directory": str(non_project)}
    catalog.assert_not_called()


def test_info_rejects_invalid_semantic_kind(spec_kit_project: Path):
    with pytest.raises(ArtifactInfoKindError) as exc_info:
        get_artifact_info(
            ArtifactInfoRequest(
                spec_kit_project,
                "speckit.plan",
                kind="invalid",  # type: ignore[arg-type]
            )
        )

    assert exc_info.value.code == "invalid_artifact_kind"
    assert exc_info.value.details == {"kind": "invalid"}


@pytest.mark.parametrize(
    "identifier",
    ["missing", "command:missing"],
)
def test_info_maps_unknown_named_artifacts(
    spec_kit_project: Path,
    identifier: str,
):
    with pytest.raises(ArtifactInfoNotFoundError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, identifier))

    assert exc_info.value.code == "unknown_artifact"
    assert exc_info.value.message == f"unknown artifact {identifier}"


def test_info_maps_ambiguous_artifact(spec_kit_project: Path):
    overrides = spec_kit_project / ".specify" / "templates" / "overrides"
    overrides.mkdir(parents=True)
    (overrides / "shared.md").write_text("body", encoding="utf-8")

    with pytest.raises(ArtifactInfoAmbiguousError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, "shared"))

    assert exc_info.value.code == "ambiguous_artifact"
    assert exc_info.value.message.startswith("ambiguous artifact shared:")


def test_info_maps_unknown_hook(spec_kit_project: Path):
    with pytest.raises(ArtifactInfoHookNotFoundError) as exc_info:
        get_artifact_info(
            ArtifactInfoRequest(
                spec_kit_project,
                "hook:nope:missing.cmd",
            )
        )

    assert exc_info.value.code == "unknown_hook"
    assert exc_info.value.message == "unknown artifact hook:nope:missing.cmd"


@pytest.mark.parametrize(
    "identifier",
    [
        "hook:event:bad%escape",
        "hook:event:%FF",
        "hook:event",
        "",
    ],
)
def test_info_maps_malformed_identifiers(
    spec_kit_project: Path,
    identifier: str,
):
    with pytest.raises(ArtifactInfoIdentifierError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, identifier))

    assert exc_info.value.code == "invalid_artifact_identifier"
    assert exc_info.value.message == f"unknown artifact {identifier}"


def test_info_maps_corrupt_registry_to_resolution_error(
    spec_kit_project: Path,
):
    registry = spec_kit_project / ".specify" / "extensions" / ".registry"
    registry.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ArtifactInfoResolutionError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, "speckit.plan"))

    assert exc_info.value.code == "artifact_resolution_failed"
    assert exc_info.value.message == "artifact resolution failed"


@pytest.mark.parametrize(
    "failure",
    [
        ArtifactResolutionError(),
        PresetError("broken preset"),
        OSError("unreadable"),
    ],
)
def test_info_converts_resolution_failures(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
):
    monkeypatch.setattr(
        artifacts.ArtifactCatalog,
        "get_artifact_info",
        Mock(side_effect=failure),
    )

    with pytest.raises(ArtifactInfoResolutionError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, "speckit.plan"))

    assert exc_info.value.__cause__ is failure


def _named_payload() -> dict[str, object]:
    return {
        "id": "template:broken",
        "name": "broken",
        "kind": "template",
        "description": "Broken",
        "stack": [
            {
                "id": "template:broken",
                "layer": None,
                "sourceId": None,
                "presetId": None,
                "presetName": None,
                "strategy": "replace",
                "active": True,
                "hidden": False,
                "manifestPath": None,
                "lookupId": None,
                "sourcePath": None,
            }
        ],
    }


def _hook_payload() -> dict[str, object]:
    return {
        "id": "hook:event:cmd",
        "name": "event:cmd",
        "kind": "hook",
        "description": "Hook",
        "eventName": "event",
        "targetCommand": "cmd",
        "registered": False,
        "stack": [
            {
                "id": "hook:event:cmd",
                "layer": "extension",
                "sourceId": "ext",
                "presetId": None,
                "presetName": None,
                "strategy": "additive",
                "active": False,
                "hidden": False,
                "manifestPath": ".specify/extensions/ext/extension.yml",
                "lookupId": "extension:ext:hook:event:cmd",
                "sourcePath": None,
                "priority": 10,
                "optional": True,
            }
        ],
    }


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {**_named_payload(), "stack": []},
        {**_named_payload(), "unexpected": True},
        {**_named_payload(), "stack": [None]},
        {
            **_named_payload(),
            "stack": [
                {
                    **_named_payload()["stack"][0],  # type: ignore[index]
                    "active": "yes",
                }
            ],
        },
        {**_named_payload(), "id": "template:wrong"},
        {**_named_payload(), "name": None},
        {**_named_payload(), "name": "bad:name"},
        {**_hook_payload(), "stack": []},
        {**_hook_payload(), "unexpected": True},
        {**_hook_payload(), "stack": [None]},
        {
            **_hook_payload(),
            "stack": [
                {
                    **_hook_payload()["stack"][0],  # type: ignore[index]
                    "priority": True,
                }
            ],
        },
        {**_hook_payload(), "registered": "no"},
        {**_hook_payload(), "eventName": "\ud800"},
        {**_hook_payload(), "id": "hook:event:wrong"},
        {**_hook_payload(), "name": "event:wrong"},
    ],
)
def test_info_rejects_invalid_catalog_results(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
):
    monkeypatch.setattr(
        _operation_info,
        "ArtifactCatalog",
        lambda _project_directory: Mock(get_artifact_info=Mock(return_value=payload)),
    )

    with pytest.raises(ArtifactInfoInvalidResultError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, "template:broken"))

    assert exc_info.value.code == "invalid_operation_result"
    assert exc_info.value.message == "artifact resolution failed"


def test_info_converts_catalog_project_error(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    catalog = Mock()
    catalog.get_artifact_info.side_effect = artifacts.NotASpecKitProjectError()
    monkeypatch.setattr(
        _operation_info,
        "ArtifactCatalog",
        Mock(return_value=catalog),
    )

    with pytest.raises(ArtifactInfoProjectError) as exc_info:
        get_artifact_info(ArtifactInfoRequest(spec_kit_project, "speckit.plan"))

    assert isinstance(exc_info.value.__cause__, artifacts.NotASpecKitProjectError)


def test_operation_contract_is_transport_neutral():
    forbidden_names = {
        "typer",
        "rich",
        "mcp",
        "console",
        "subprocess",
        "os",
        "chdir",
        "getcwd",
    }

    assert forbidden_names.isdisjoint(_operation_info.__dict__)
    assert ArtifactInfoResult.__module__ == ("specify_cli.artifacts._operation_info")
