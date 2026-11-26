"""Transport-neutral step-type contract and effect boundaries."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from specify_cli.workflows import BUILTIN_STEP_TYPES
from specify_cli.workflows.step import _operation_list as operation


def _registry(root, entries):
    directory = root / ".specify" / "workflows" / "steps"
    directory.mkdir(parents=True)
    path = directory / "step-registry.json"
    path.write_text(json.dumps({"steps": entries}), encoding="utf-8")
    return path


def test_builtins_sorted_then_installed_sorted(tmp_path):
    _registry(
        tmp_path,
        {
            "z-custom": {"name": "Zed", "version": "2.0.0"},
            "a-custom": {"name": "Ay", "version": "1.0.0"},
        },
    )
    result = operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    expected = [
        operation.WorkflowStepListEntry(key, key, None, "builtin")
        for key in sorted(BUILTIN_STEP_TYPES)
    ] + [
        operation.WorkflowStepListEntry("a-custom", "Ay", "1.0.0", "custom"),
        operation.WorkflowStepListEntry("z-custom", "Zed", "2.0.0", "custom"),
    ]
    assert result == operation.WorkflowStepListResult(tuple(expected))
    assert result.truncated is False
    with pytest.raises(FrozenInstanceError):
        result.truncated = True


def test_missing_registry_lists_builtins_without_creating_storage(tmp_path):
    (tmp_path / ".specify").mkdir()
    result = operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert [item.id for item in result.items] == sorted(BUILTIN_STEP_TYPES)
    assert all(item.kind == "builtin" for item in result.items)
    assert list((tmp_path / ".specify").iterdir()) == []


def test_non_dict_installed_entry_is_warning(tmp_path):
    _registry(tmp_path, {"broken[entry]": None, "ok": {"name": "Ok"}})
    result = operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    warning = operation.WorkflowStepListWarning(
        "broken[entry]", "Skipping corrupted registry entry 'broken[entry]'."
    )
    assert warning in result.items
    assert operation.WorkflowStepListEntry("ok", "Ok", "?", "custom") in result.items


def test_limit_truncates_across_builtins_and_installed(tmp_path):
    (tmp_path / ".specify").mkdir()
    result = operation.list_step_types(
        operation.WorkflowStepListRequest(tmp_path, limit=2)
    )
    assert len(result.items) == 2
    assert result.truncated is True


def test_builtin_snapshot_ignores_live_registry_mutation(tmp_path, monkeypatch):
    from specify_cli.workflows import STEP_REGISTRY

    (tmp_path / ".specify").mkdir()
    monkeypatch.setitem(STEP_REGISTRY, "not-a-builtin", object())
    result = operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert "not-a-builtin" not in {item.id for item in result.items}
    assert {item.id for item in result.items} == set(BUILTIN_STEP_TYPES)


@pytest.mark.parametrize(
    "step_request,code",
    [
        (
            operation.WorkflowStepListRequest(Path("relative")),
            "invalid_project_directory",
        ),
        (operation.WorkflowStepListRequest(Path("/tmp"), limit=0), "invalid_limit"),
        (
            operation.WorkflowStepListRequest(Path("/tmp"), limit=1001),
            "invalid_limit",
        ),
        (
            operation.WorkflowStepListRequest(Path("/tmp"), limit="10"),  # type: ignore[arg-type]
            "invalid_limit",
        ),
    ],
)
def test_invalid_requests_are_rejected(tmp_path, step_request, code):
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(step_request)
    assert excinfo.value.code == code


def test_not_a_spec_kit_project(tmp_path):
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "not_a_spec_kit_project"


def test_unsafe_storage_is_rejected(tmp_path):
    (tmp_path / ".specify").mkdir()
    target = tmp_path / "elsewhere"
    target.mkdir()
    (tmp_path / ".specify" / "workflows").symlink_to(target, target_is_directory=True)
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "unsafe_workflow_storage"


def test_operation_descriptor_contract():
    descriptor = operation.WORKFLOW_STEP_LIST_OPERATION
    assert descriptor.operation_id == "workflow.step.list"
    assert descriptor.contract_version == "1"
    assert descriptor.capabilities == frozenset({"local-read"})
    assert descriptor.network_access == "none"
