"""Tests for the shared ``artifact.list`` operation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from specify_cli import artifacts
from specify_cli.artifacts import ArtifactCatalog, _operation_list
from specify_cli.artifacts._operation_list import (
    ARTIFACT_LIST_OPERATION,
    ArtifactListProjectError,
    ArtifactListRequest,
    ArtifactListResolutionError,
    ArtifactListResult,
    list_artifacts,
)
from specify_cli.extensions import ExtensionRegistry
from specify_cli.presets import PresetError


def test_artifact_list_operation_descriptor_is_stable():
    assert ARTIFACT_LIST_OPERATION.operation_id == "artifact.list"
    assert ARTIFACT_LIST_OPERATION.contract_version == "1"
    assert ARTIFACT_LIST_OPERATION.request_type is ArtifactListRequest
    assert ARTIFACT_LIST_OPERATION.result_type is ArtifactListResult
    assert ARTIFACT_LIST_OPERATION.warning_types == ()
    assert ARTIFACT_LIST_OPERATION.error_types == (
        ArtifactListProjectError,
        ArtifactListResolutionError,
    )
    assert ARTIFACT_LIST_OPERATION.capabilities == frozenset({"local-read"})
    assert ARTIFACT_LIST_OPERATION.network_access == "none"


def test_list_artifacts_returns_complete_typed_inventory(spec_kit_project: Path):
    expected = ArtifactCatalog(spec_kit_project).list_artifacts_with_stack()

    result = list_artifacts(ArtifactListRequest(spec_kit_project))

    assert isinstance(result, ArtifactListResult)
    assert list(result.rows) == expected
    assert result.rows
    assert all(
        {"id", "name", "kind", "description", "stack"} <= row.keys()
        for row in result.rows
    )


def test_list_artifacts_preserves_empty_inventory(
    spec_kit_project: Path, monkeypatch: pytest.MonkeyPatch
):
    list_with_stack = Mock(return_value=[])
    monkeypatch.setattr(
        _operation_list,
        "ArtifactCatalog",
        lambda _project_directory: Mock(list_artifacts_with_stack=list_with_stack),
    )

    result = list_artifacts(ArtifactListRequest(spec_kit_project))

    assert result == ArtifactListResult(rows=())
    list_with_stack.assert_called_once_with()


def test_list_artifacts_is_stable_across_repeated_calls(spec_kit_project: Path):
    request = ArtifactListRequest(spec_kit_project)

    first = list_artifacts(request)
    second = list_artifacts(request)

    assert first == second
    assert [row["id"] for row in first.rows] == [row["id"] for row in second.rows]


def test_list_artifacts_preserves_unicode_source_paths_and_stack(
    spec_kit_project: Path,
):
    extension_dir = spec_kit_project / ".specify" / "extensions" / "quality"
    template = extension_dir / "templates" / "réview-checklist.md"
    template.parent.mkdir(parents=True)
    template.write_text(
        "---\ndescription: Réview checklist\n---\n",
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
                    "description": "test",
                    "author": "test",
                    "repository": "https://example.com",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.2.0"},
                "provides": {
                    "templates": [
                        {
                            "name": "review-checklist",
                            "file": "templates/réview-checklist.md",
                            "description": "Réview checklist",
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

    result = list_artifacts(ArtifactListRequest(spec_kit_project))
    row = next(
        item for item in result.rows if item["id"] == "template:review-checklist"
    )

    assert row["description"] == "Réview checklist"
    assert row["stack"][0]["sourcePath"] == (
        ".specify/extensions/quality/templates/réview-checklist.md"
    )
    assert (
        row["stack"]
        == ArtifactCatalog(spec_kit_project).get_artifact_info(row["id"])["stack"]
    )


def test_list_artifacts_uses_explicit_project_without_process_cwd(
    spec_kit_project: Path,
    non_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.chdir(non_project)

    result = list_artifacts(ArtifactListRequest(spec_kit_project))

    assert result.rows


def test_list_artifacts_rejects_relative_project_directory():
    with pytest.raises(ArtifactListProjectError) as exc_info:
        list_artifacts(ArtifactListRequest(Path("relative-project")))

    assert exc_info.value.code == "not_a_spec_kit_project"
    assert exc_info.value.message == (
        "not a Spec Kit project: no .specify/ directory found"
    )
    assert exc_info.value.details == {"project_directory": "relative-project"}
    assert exc_info.value.retryable is False


def test_list_artifacts_rejects_non_project(non_project: Path):
    with pytest.raises(ArtifactListProjectError) as exc_info:
        list_artifacts(ArtifactListRequest(non_project))

    assert exc_info.value.code == "not_a_spec_kit_project"
    assert exc_info.value.details == {"project_directory": str(non_project)}


def test_list_artifacts_maps_corrupt_registry_to_resolution_error(
    spec_kit_project: Path,
):
    registry = spec_kit_project / ".specify" / "extensions" / ".registry"
    registry.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ArtifactListResolutionError) as exc_info:
        list_artifacts(ArtifactListRequest(spec_kit_project))

    assert exc_info.value.code == "artifact_resolution_failed"
    assert exc_info.value.message == "artifact resolution failed"
    assert exc_info.value.details == {"project_directory": str(spec_kit_project)}
    assert exc_info.value.retryable is False


def test_list_artifacts_maps_preset_failures_to_resolution_error(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        artifacts.ArtifactCatalog,
        "list_artifacts_with_stack",
        Mock(side_effect=PresetError("broken preset")),
    )

    with pytest.raises(ArtifactListResolutionError) as exc_info:
        list_artifacts(ArtifactListRequest(spec_kit_project))

    assert isinstance(exc_info.value.__cause__, PresetError)


def test_list_artifacts_maps_filesystem_failures_to_resolution_error(
    spec_kit_project: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        artifacts.ArtifactCatalog,
        "list_artifacts_with_stack",
        Mock(side_effect=OSError("unreadable")),
    )

    with pytest.raises(ArtifactListResolutionError) as exc_info:
        list_artifacts(ArtifactListRequest(spec_kit_project))

    assert isinstance(exc_info.value.__cause__, OSError)


def test_operation_contract_is_transport_neutral():
    forbidden_names = {"typer", "rich", "mcp", "console"}

    assert forbidden_names.isdisjoint(_operation_list.__dict__)
    assert ArtifactListResult.__module__ == ("specify_cli.artifacts._operation_list")
