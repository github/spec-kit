"""Tests for the shared ``artifact.lookup`` operation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from specify_cli import _project_policy, artifacts
from specify_cli._project_policy import (
    ProjectResolutionError,
    preflight_project_policy,
)
from specify_cli.artifacts import (
    ArtifactCatalog,
    ArtifactResolutionError,
    _operation_lookup,
)
from specify_cli.artifacts._identifiers import derive_hook_lookup_id
from specify_cli.artifacts._operation_lookup import (
    ARTIFACT_LOOKUP_OPERATION,
    ArtifactLookupFilesystemError,
    ArtifactLookupIdentifierError,
    ArtifactLookupIntegrationError,
    ArtifactLookupInvalidResultError,
    ArtifactLookupJsonObject,
    ArtifactLookupNotFoundError,
    ArtifactLookupPresetError,
    ArtifactLookupProjectDirectoryError,
    ArtifactLookupProjectError,
    ArtifactLookupProjectPolicyError,
    ArtifactLookupRegistryError,
    ArtifactLookupRequest,
    ArtifactLookupResolutionError,
    ArtifactLookupResult,
    lookup_artifact,
)
from specify_cli.extensions import ExtensionRegistry
from specify_cli.integrations.installer import IntegrationInstallError
from specify_cli.presets import PresetError
from tests.conftest import install_preset
from tests.specify_cli.artifacts.helpers import install_extension_with_hooks


def _install_extension_contributions(project_root: Path) -> Path:
    extension_dir = project_root / ".specify" / "extensions" / "quality"
    extension_dir.mkdir()
    for directory in ("commands", "templates", "scripts"):
        (extension_dir / directory).mkdir()
    (extension_dir / "commands" / "review.md").write_text(
        "command body",
        encoding="utf-8",
    )
    (extension_dir / "templates" / "review.md").write_text(
        "template body",
        encoding="utf-8",
    )
    (extension_dir / "scripts" / "review.sh").write_text(
        "#!/bin/sh\n",
        encoding="utf-8",
    )
    (extension_dir / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "quality",
                    "name": "Quality",
                    "version": "1.0.0",
                    "description": "Quality extension",
                    "author": "test",
                    "repository": "https://example.com",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.2.0"},
                "provides": {
                    "commands": [
                        {
                            "name": "speckit.quality.review",
                            "file": "commands/review.md",
                            "description": "Review command",
                        }
                    ],
                    "templates": [
                        {
                            "name": "quality-review",
                            "file": "templates/review.md",
                            "description": "Review template",
                        }
                    ],
                    "scripts": [
                        {
                            "name": "quality-review",
                            "file": "scripts/review.sh",
                            "description": "Review script",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    ExtensionRegistry(project_root / ".specify" / "extensions").add(
        "quality",
        {"version": "1.0.0", "enabled": True},
    )
    return extension_dir


def _valid_payload(
    lookup_id: str = "preset:sample:template:sample",
) -> dict[str, object]:
    layer, source_id, kind, name = lookup_id.split(":", 3)
    return {
        "id": lookup_id,
        "layer": layer,
        "sourceId": source_id,
        "kind": kind,
        "name": name,
        "manifestPath": f".specify/{layer}s/{source_id}/{layer}.yml",
        "sourcePath": None,
        "contribution": {"name": name, "type": kind},
    }


def test_artifact_lookup_operation_descriptor_is_stable():
    assert ARTIFACT_LOOKUP_OPERATION.operation_id == "artifact.lookup"
    assert ARTIFACT_LOOKUP_OPERATION.contract_version == "1"
    assert ARTIFACT_LOOKUP_OPERATION.request_type is ArtifactLookupRequest
    assert ARTIFACT_LOOKUP_OPERATION.result_type is ArtifactLookupResult
    assert ARTIFACT_LOOKUP_OPERATION.warning_types == ()
    assert ARTIFACT_LOOKUP_OPERATION.error_types == (
        ArtifactLookupProjectDirectoryError,
        ArtifactLookupProjectPolicyError,
        ArtifactLookupProjectError,
        ArtifactLookupIdentifierError,
        ArtifactLookupNotFoundError,
        ArtifactLookupRegistryError,
        ArtifactLookupIntegrationError,
        ArtifactLookupPresetError,
        ArtifactLookupFilesystemError,
        ArtifactLookupResolutionError,
        ArtifactLookupInvalidResultError,
    )
    assert ARTIFACT_LOOKUP_OPERATION.capabilities == frozenset({"local-read"})
    assert ARTIFACT_LOOKUP_OPERATION.network_access == "none"


def test_lookup_returns_complete_typed_preset_result(
    spec_kit_project: Path,
):
    pack = install_preset(
        spec_kit_project,
        "typed",
        {
            "templates": [
                {
                    "type": "template",
                    "name": "typed",
                    "file": "templates/typed.md",
                    "description": "Typed ✓",
                    "metadata": {
                        "none": None,
                        "boolean": True,
                        "integer": 7,
                        "float": 2.5,
                        "unicode": {"clé": "välue ✓"},
                        "array": [None, False, 9, 1.25, "text"],
                    },
                }
            ]
        },
    )
    (pack / "templates").mkdir()
    (pack / "templates" / "typed.md").write_text("body", encoding="utf-8")
    request = ArtifactLookupRequest(
        spec_kit_project,
        "preset:typed:template:typed",
    )

    result = lookup_artifact(request)
    payload = result.to_json_dict()

    assert isinstance(result, ArtifactLookupResult)
    assert isinstance(result.contribution, ArtifactLookupJsonObject)
    assert payload == ArtifactCatalog(spec_kit_project).get_contribution_info(
        request.lookup_id
    )
    assert payload == {
        "id": request.lookup_id,
        "layer": "preset",
        "sourceId": "typed",
        "kind": "template",
        "name": "typed",
        "manifestPath": ".specify/presets/typed/preset.yml",
        "sourcePath": ".specify/presets/typed/templates/typed.md",
        "contribution": {
            "type": "template",
            "name": "typed",
            "file": "templates/typed.md",
            "description": "Typed ✓",
            "metadata": {
                "none": None,
                "boolean": True,
                "integer": 7,
                "float": 2.5,
                "unicode": {"clé": "välue ✓"},
                "array": [None, False, 9, 1.25, "text"],
            },
        },
    }


@pytest.mark.parametrize(
    ("kind", "name", "lookup_id"),
    [
        (
            "command",
            "speckit.quality.review",
            "extension:quality:command:speckit.quality.review",
        ),
        (
            "template",
            "quality-review",
            "extension:quality:template:quality-review",
        ),
        (
            "script",
            "quality-review",
            "extension:quality:script:quality-review",
        ),
    ],
)
def test_lookup_accepts_extension_contribution_families(
    spec_kit_project: Path,
    kind: str,
    name: str,
    lookup_id: str,
):
    _install_extension_contributions(spec_kit_project)

    result = lookup_artifact(ArtifactLookupRequest(spec_kit_project, lookup_id))
    payload = result.to_json_dict()

    assert payload["layer"] == "extension"
    assert payload["kind"] == kind
    assert payload["name"] == name
    assert payload["contribution"]["name"] == name
    assert payload["sourcePath"] == (
        f".specify/extensions/quality/{kind}s/review."
        f"{'sh' if kind == 'script' else 'md'}"
    )


@pytest.mark.parametrize(
    ("kind", "name"),
    [
        ("command", "speckit.preset.command"),
        ("template", "preset-template"),
        ("script", "preset-script"),
    ],
)
def test_lookup_accepts_preset_contribution_families(
    spec_kit_project: Path,
    kind: str,
    name: str,
):
    pack = install_preset(
        spec_kit_project,
        "families",
        {
            "templates": [
                {
                    "type": kind,
                    "name": name,
                    "description": f"{kind} contribution",
                }
            ]
        },
    )
    relative_file = {
        "command": Path("commands") / f"{name}.md",
        "template": Path("templates") / f"{name}.md",
        "script": Path("scripts") / f"{name}.sh",
    }[kind]
    source = pack / relative_file
    source.parent.mkdir()
    source.write_text("body", encoding="utf-8")
    lookup_id = f"preset:families:{kind}:{name}"

    result = lookup_artifact(ArtifactLookupRequest(spec_kit_project, lookup_id))

    assert result.kind == kind
    assert result.name == name
    assert result.sourcePath == (
        f".specify/presets/families/{relative_file.as_posix()}"
    )


def test_lookup_preserves_percent_encoded_unicode_hook_identity(
    spec_kit_project: Path,
):
    event_name = "custom:after/✓"
    command = "/skill:speckit-réview:run"
    install_extension_with_hooks(
        spec_kit_project,
        "quality",
        hooks={
            event_name: [
                {
                    "command": command,
                    "description": "Réview ✓",
                    "priority": 4,
                    "optional": False,
                }
            ]
        },
    )
    lookup_id = derive_hook_lookup_id(
        "extension",
        "quality",
        event_name,
        command,
    )

    result = lookup_artifact(ArtifactLookupRequest(spec_kit_project, lookup_id))
    payload = result.to_json_dict()

    assert result.id == lookup_id
    assert result.kind == "hook"
    assert result.name == lookup_id.split(":", 3)[3]
    assert payload["contribution"] == {
        "eventName": event_name,
        "command": command,
        "description": "Réview ✓",
        "priority": 4,
        "optional": False,
    }
    assert result.sourcePath is None


def test_list_info_lookup_round_trip_matches_manifest_and_stack_layer(
    spec_kit_project: Path,
):
    pack = install_preset(
        spec_kit_project,
        "round-trip",
        {
            "templates": [
                {
                    "type": "template",
                    "name": "round-trip",
                    "file": "templates/round-trip.md",
                    "description": "Round trip",
                }
            ]
        },
    )
    (pack / "templates").mkdir()
    (pack / "templates" / "round-trip.md").write_text(
        "body",
        encoding="utf-8",
    )
    catalog = ArtifactCatalog(spec_kit_project)
    row = next(
        item
        for item in catalog.list_artifacts_with_stack()
        if item["id"] == "template:round-trip"
    )
    info = catalog.get_artifact_info(row["id"])
    layer = next(item for item in info["stack"] if item["sourceId"] == "round-trip")

    result = lookup_artifact(
        ArtifactLookupRequest(spec_kit_project, layer["lookupId"])
    ).to_json_dict()

    assert info == row
    assert result == catalog.get_contribution_info(layer["lookupId"])
    assert result["manifestPath"] == layer["manifestPath"]
    assert result["sourcePath"] == layer["sourcePath"]
    manifest = yaml.safe_load(
        (spec_kit_project / result["manifestPath"]).read_text(encoding="utf-8")
    )
    assert result["contribution"] == manifest["provides"]["templates"][0]


def test_lookup_is_stable_across_repeated_calls(spec_kit_project: Path):
    install_preset(
        spec_kit_project,
        "stable",
        {"templates": [{"type": "template", "name": "stable"}]},
    )
    request = ArtifactLookupRequest(
        spec_kit_project,
        "preset:stable:template:stable",
    )

    assert lookup_artifact(request) == lookup_artifact(request)


def test_lookup_isolates_sequential_explicit_projects(
    spec_kit_project: Path,
    tmp_path: Path,
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    second = tmp_path / "second"
    second.mkdir()
    for relative in (
        ".specify",
        ".specify/presets",
        ".specify/extensions",
        ".specify/templates",
    ):
        (second / relative).mkdir(exist_ok=True)
    for project, description in (
        (spec_kit_project, "First"),
        (second, "Second"),
    ):
        install_preset(
            project,
            "isolated",
            {
                "templates": [
                    {
                        "type": "template",
                        "name": "isolated",
                        "description": description,
                    }
                ]
            },
        )
    request_id = "preset:isolated:template:isolated"
    monkeypatch.chdir(non_project)

    first = lookup_artifact(ArtifactLookupRequest(spec_kit_project, request_id))
    second_result = lookup_artifact(ArtifactLookupRequest(second, request_id))

    assert first.to_json_dict()["contribution"]["description"] == "First"
    assert second_result.to_json_dict()["contribution"]["description"] == "Second"
    assert Path.cwd() == non_project


def test_lookup_preserves_trusted_symlinked_project_root(
    spec_kit_project: Path,
    tmp_path: Path,
):
    pack = install_preset(
        spec_kit_project,
        "linked",
        {
            "templates": [
                {
                    "type": "template",
                    "name": "linked",
                    "file": "templates/linked.md",
                }
            ]
        },
    )
    (pack / "templates").mkdir()
    (pack / "templates" / "linked.md").write_text("body", encoding="utf-8")
    linked_project = tmp_path / "linked-project"
    try:
        linked_project.symlink_to(spec_kit_project, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")

    result = lookup_artifact(
        ArtifactLookupRequest(
            linked_project,
            "preset:linked:template:linked",
        )
    )

    assert result.sourcePath == ".specify/presets/linked/templates/linked.md"


def test_lookup_rejects_relative_project_directory():
    with pytest.raises(ArtifactLookupProjectDirectoryError) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                Path("relative"),
                "preset:sample:template:sample",
            )
        )

    assert exc_info.value.code == "invalid_project_directory"
    assert exc_info.value.details == {"project_directory": "relative"}


def test_lookup_rejects_missing_absolute_project_directory(
    tmp_path: Path,
):
    missing = tmp_path / "missing"

    with pytest.raises(ArtifactLookupProjectError):
        lookup_artifact(
            ArtifactLookupRequest(
                missing,
                "preset:sample:template:sample",
            )
        )


@pytest.mark.parametrize(
    "lookup_id",
    [
        "invalid:source:command:name",
        "extension:source:command:missing",
    ],
)
def test_lookup_rejects_non_project_before_lookup_identifier(
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    lookup_id: str,
):
    catalog = Mock(side_effect=AssertionError("catalog reached"))
    monkeypatch.setattr(_operation_lookup, "ArtifactCatalog", catalog)

    with pytest.raises(ArtifactLookupProjectError) as exc_info:
        lookup_artifact(ArtifactLookupRequest(non_project, lookup_id))

    assert exc_info.value.code == "not_a_spec_kit_project"
    catalog.assert_not_called()


@pytest.mark.parametrize(
    "lookup_id",
    [
        "invalid:source:command:name",
        "extension:source:invalid:name",
        "extension:_:command:name",
        "extension:source:hook:event",
        "extension:source:hook:event:command:extra",
        "extension:source:hook:event:bad%escape",
        "extension:source:hook:event:%FF",
        "extension:source:hook:event:%",
    ],
)
def test_lookup_maps_malformed_lookup_ids(
    spec_kit_project: Path,
    lookup_id: str,
):
    with pytest.raises(ArtifactLookupIdentifierError) as exc_info:
        lookup_artifact(ArtifactLookupRequest(spec_kit_project, lookup_id))

    assert exc_info.value.code == "invalid_lookup_id"
    assert exc_info.value.message == f"unknown contribution {lookup_id}"


def test_lookup_maps_invalid_unicode_lookup_id_after_project_validation(
    spec_kit_project: Path,
):
    lookup_id = "extension:source:template:\ud800"

    with pytest.raises(ArtifactLookupIdentifierError) as exc_info:
        lookup_artifact(ArtifactLookupRequest(spec_kit_project, lookup_id))

    escaped_lookup_id = "extension:source:template:\\ud800"
    assert exc_info.value.message == f"unknown contribution {escaped_lookup_id}"
    assert exc_info.value.details == {"lookup_id": escaped_lookup_id}
    json.dumps(
        {"error": exc_info.value.message},
        ensure_ascii=False,
    ).encode("utf-8")


@pytest.mark.parametrize(
    "lookup_id",
    [
        "preset:missing:template:missing",
        "extension:missing:command:speckit.missing",
        "project:_:command:local",
    ],
)
def test_lookup_maps_unknown_contributions(
    spec_kit_project: Path,
    lookup_id: str,
):
    with pytest.raises(ArtifactLookupNotFoundError) as exc_info:
        lookup_artifact(ArtifactLookupRequest(spec_kit_project, lookup_id))

    assert exc_info.value.code == "unknown_contribution"
    assert exc_info.value.message == f"unknown contribution {lookup_id}"


def test_lookup_maps_project_policy_failure_before_loader_and_catalog(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    config = spec_kit_project / ".specify" / "init-options.json"
    config.write_text("{", encoding="utf-8")
    loader = Mock(side_effect=AssertionError("loader reached"))
    catalog = Mock(side_effect=AssertionError("catalog reached"))
    monkeypatch.setattr(
        _operation_lookup.installer,
        "load_installed_integrations",
        loader,
    )
    monkeypatch.setattr(_operation_lookup, "ArtifactCatalog", catalog)

    with pytest.raises(ArtifactLookupProjectPolicyError) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )

    assert exc_info.value.code == "project_policy_error"
    assert "Invalid JSON" in exc_info.value.message
    loader.assert_not_called()
    catalog.assert_not_called()


@pytest.mark.parametrize("marker_kind", ["symlink", "file"])
def test_lookup_preserves_structural_project_policy_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    marker_kind: str,
):
    project_directory = tmp_path / "project"
    project_directory.mkdir()
    marker = project_directory / ".specify"
    if marker_kind == "symlink":
        target = tmp_path / "real-specify"
        target.mkdir()
        try:
            marker.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"Symlinks unavailable: {exc}")
    else:
        marker.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ProjectResolutionError) as preflight_exc:
        preflight_project_policy(project_directory)

    loader = Mock(side_effect=AssertionError("loader reached"))
    catalog = Mock(side_effect=AssertionError("catalog reached"))
    monkeypatch.setattr(
        _operation_lookup.installer,
        "load_installed_integrations",
        loader,
    )
    monkeypatch.setattr(_operation_lookup, "ArtifactCatalog", catalog)

    with pytest.raises(ArtifactLookupProjectPolicyError) as operation_exc:
        lookup_artifact(
            ArtifactLookupRequest(
                project_directory,
                "malformed",
            )
        )

    assert operation_exc.value.message == str(preflight_exc.value)
    if marker_kind == "symlink":
        assert operation_exc.value.message.startswith(
            f"Refusing to use symlinked .specify path: {marker}."
        )
    else:
        assert operation_exc.value.message == (
            "Not a Spec Kit project: .specify path exists but is not a directory: "
            f"{marker}"
        )
    loader.assert_not_called()
    catalog.assert_not_called()


def test_lookup_maps_corrupt_registry_before_malformed_identifier(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    registry = spec_kit_project / ".specify" / "extensions" / ".registry"
    registry.write_text("{invalid", encoding="utf-8")
    catalog = Mock(side_effect=AssertionError("catalog reached"))
    monkeypatch.setattr(_operation_lookup, "ArtifactCatalog", catalog)

    with pytest.raises(ArtifactLookupRegistryError) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "invalid:source:command:name",
            )
        )

    assert exc_info.value.code == "corrupt_extension_registry"
    catalog.assert_not_called()


def test_lookup_maps_registry_filesystem_failure(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        _operation_lookup,
        "ExtensionRegistry",
        Mock(side_effect=OSError("unreadable registry")),
    )

    with pytest.raises(ArtifactLookupFilesystemError) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )

    assert exc_info.value.code == "filesystem_error"


def test_lookup_maps_integration_loader_failure(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    failure = IntegrationInstallError("installed package has been modified")
    monkeypatch.setattr(
        _operation_lookup.installer,
        "load_installed_integrations",
        Mock(side_effect=failure),
    )

    with pytest.raises(ArtifactLookupIntegrationError) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )

    assert exc_info.value.code == "integration_resolution_failed"
    assert exc_info.value.message == (
        "artifact resolution failed: installed package has been modified"
    )
    assert exc_info.value.__cause__ is failure


@pytest.mark.parametrize(
    ("failure", "error_type", "code"),
    [
        (
            ArtifactResolutionError("catalog detail"),
            ArtifactLookupResolutionError,
            "artifact_resolution_failed",
        ),
        (
            PresetError("broken preset"),
            ArtifactLookupPresetError,
            "preset_resolution_failed",
        ),
        (
            OSError("unreadable"),
            ArtifactLookupFilesystemError,
            "filesystem_error",
        ),
    ],
)
def test_lookup_converts_catalog_resolution_failures(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
    error_type: type[Exception],
    code: str,
):
    monkeypatch.setattr(
        artifacts.ArtifactCatalog,
        "get_contribution_info",
        Mock(side_effect=failure),
    )

    with pytest.raises(error_type) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )

    assert exc_info.value.code == code
    assert exc_info.value.__cause__ is failure
    if isinstance(failure, ArtifactResolutionError):
        assert exc_info.value.message == failure.message


def test_lookup_converts_catalog_project_error(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    catalog = Mock()
    catalog.get_contribution_info.side_effect = artifacts.NotASpecKitProjectError()
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        Mock(return_value=catalog),
    )

    with pytest.raises(ArtifactLookupProjectError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


@pytest.mark.parametrize(
    "value",
    [
        date(2026, 1, 1),
        Path("unsupported"),
        object(),
    ],
    ids=["date", "path", "custom-object"],
)
def test_lookup_rejects_unsupported_nested_values(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: object,
):
    payload = _valid_payload()
    payload["contribution"] = {"nested": {"value": value}}
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


def test_lookup_rejects_non_string_nested_mapping_key(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _valid_payload()
    payload["contribution"] = {"nested": {1: "value"}}
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


@pytest.mark.parametrize(
    ("value", "nested"),
    [
        (float("nan"), False),
        (float("inf"), False),
        (float("-inf"), False),
        (float("nan"), True),
        (float("inf"), True),
        (float("-inf"), True),
    ],
    ids=[
        "top-nan",
        "top-positive-infinity",
        "top-negative-infinity",
        "nested-nan",
        "nested-positive-infinity",
        "nested-negative-infinity",
    ],
)
def test_lookup_rejects_non_finite_floats(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    value: float,
    nested: bool,
):
    payload: object
    if nested:
        payload = _valid_payload()
        payload["contribution"] = {"items": [0, {"value": value}]}
    else:
        payload = value
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


@pytest.mark.parametrize("location", ["value", "key"])
def test_lookup_rejects_invalid_unicode_in_contribution(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    location: str,
):
    payload = _valid_payload()
    payload["contribution"] = (
        {"value": "\ud800"} if location == "value" else {"\ud800": "value"}
    )
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {**_valid_payload(), "unexpected": True},
        {key: value for key, value in _valid_payload().items() if key != "name"},
        {**_valid_payload(), "id": "preset:sample:template:wrong"},
        {**_valid_payload(), "layer": "extension"},
        {**_valid_payload(), "sourceId": "other"},
        {**_valid_payload(), "kind": "invalid"},
        {**_valid_payload(), "name": "wrong"},
        {**_valid_payload(), "manifestPath": None},
        {**_valid_payload(), "sourcePath": 1},
        {**_valid_payload(), "contribution": []},
        {**_valid_payload(), "manifestPath": "\ud800"},
        {**_valid_payload(), "sourcePath": "\ud800"},
    ],
)
def test_lookup_rejects_invalid_catalog_result_shapes(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
):
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError) as exc_info:
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )

    assert exc_info.value.code == "invalid_operation_result"
    assert exc_info.value.message == "artifact resolution failed"


def test_lookup_rejects_recursive_catalog_result(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    recursive: list[object] = []
    recursive.append(recursive)
    payload = _valid_payload()
    payload["contribution"] = {"recursive": recursive}
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


def test_lookup_rejects_recursive_object_catalog_result(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    recursive: dict[str, object] = {}
    recursive["self"] = recursive
    payload = _valid_payload()
    payload["contribution"] = recursive
    monkeypatch.setattr(
        _operation_lookup,
        "ArtifactCatalog",
        lambda _project_directory: Mock(
            get_contribution_info=Mock(return_value=payload)
        ),
    )

    with pytest.raises(ArtifactLookupInvalidResultError):
        lookup_artifact(
            ArtifactLookupRequest(
                spec_kit_project,
                "preset:sample:template:sample",
            )
        )


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

    assert forbidden_names.isdisjoint(_operation_lookup.__dict__)
    assert forbidden_names.isdisjoint(_project_policy.__dict__)
    assert ArtifactLookupResult.__module__ == (
        "specify_cli.artifacts._operation_lookup"
    )
