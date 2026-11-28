"""Transport-neutral step-type contract and effect boundaries."""

import io
import json
import os
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from specify_cli.file_helper import FileHelper
from specify_cli.workflows import BUILTIN_STEP_TYPES
from specify_cli.workflows.step import _operation_list as operation
from specify_cli.workflows.step.catalog import StepRegistry


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
        (operation.WorkflowStepListRequest(Path.cwd(), limit=0), "invalid_limit"),
        (
            operation.WorkflowStepListRequest(Path.cwd(), limit=1001),
            "invalid_limit",
        ),
        (
            operation.WorkflowStepListRequest(Path.cwd(), limit="10"),  # type: ignore[arg-type]
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


def _symlink(link, target):
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")


def test_limit_stops_at_first_installed_entry(tmp_path):
    _registry(
        tmp_path,
        {
            f"step-{letter}": {"name": letter, "version": "1.0.0"}
            for letter in "abcde"
        },
    )
    result = operation.list_step_types(
        operation.WorkflowStepListRequest(
            tmp_path, limit=len(BUILTIN_STEP_TYPES) + 1
        )
    )
    assert len(result.items) == len(BUILTIN_STEP_TYPES) + 1
    assert result.truncated is True
    assert result.items[-1].id == "step-a"


def test_registry_size_cap_is_enforced_before_parsing(tmp_path, monkeypatch):
    path = _registry(tmp_path, {"a-custom": {"name": "Ay", "version": "1.0.0"}})
    size = path.stat().st_size
    monkeypatch.setattr(StepRegistry, "MAX_REGISTRY_BYTES", size)
    result = operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert "a-custom" in {item.id for item in result.items}
    monkeypatch.setattr(StepRegistry, "MAX_REGISTRY_BYTES", size - 1)
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "step_registry_read_failed"


def test_symlinked_steps_directory_is_rejected(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / ".specify" / "workflows").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "step-registry.json").write_text(
        json.dumps({"steps": {"outside-secret": {"name": "Leaked"}}}),
        encoding="utf-8",
    )
    _symlink(root / ".specify" / "workflows" / "steps", outside)
    opened = []
    original_open = io.open

    def track(file, *args, **kwargs):
        if Path(file).name == "step-registry.json":
            opened.append(file)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", track)
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(root))
    assert excinfo.value.code == "step_registry_read_failed"
    assert opened == []


def test_unreadable_registry_is_read_failed(tmp_path, monkeypatch):
    path = _registry(tmp_path, {"ok": {"name": "Ok"}})
    original = FileHelper.read_bytes

    def denied(files, file):
        if Path(file) == path:
            raise PermissionError("private registry details")
        return original(files, file)

    monkeypatch.setattr(FileHelper, "read_bytes", denied)
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "step_registry_read_failed"


def test_corrupt_registry_is_read_failed(tmp_path):
    directory = tmp_path / ".specify" / "workflows" / "steps"
    directory.mkdir(parents=True)
    (directory / "step-registry.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "step_registry_read_failed"


def test_invalid_registry_shape_is_read_failed(tmp_path):
    _registry(tmp_path, {"ok": {"name": "Ok"}})
    path = tmp_path / ".specify" / "workflows" / "steps" / "step-registry.json"
    path.write_text(json.dumps({"steps": "not-a-mapping"}), encoding="utf-8")
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "step_registry_read_failed"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are POSIX-only")
def test_fifo_registry_is_read_failed(tmp_path):
    directory = tmp_path / ".specify" / "workflows" / "steps"
    directory.mkdir(parents=True)
    os.mkfifo(directory / "step-registry.json")
    with pytest.raises(operation.WorkflowStepListError) as excinfo:
        operation.list_step_types(operation.WorkflowStepListRequest(tmp_path))
    assert excinfo.value.code == "step_registry_read_failed"


@pytest.mark.skipif(os.name != "nt", reason="Windows directory junction regression")
@pytest.mark.parametrize("registry_present", [False, True])
def test_step_list_rejects_junction_at_registry_read_boundary(
    tmp_path, monkeypatch, registry_present
):
    from typer.testing import CliRunner

    from specify_cli import app
    from specify_cli.workflows.step import mcp_list

    root = tmp_path / "project"
    (root / ".specify" / "workflows").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    registry = outside / "step-registry.json"
    if registry_present:
        registry.write_text('{"steps": {"outside-secret": {}}}', encoding="utf-8")
    before = registry.read_bytes() if registry_present else None
    junction = root / ".specify" / "workflows" / "steps"
    created = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert created.returncode == 0, created.stderr
    assert not junction.is_symlink()
    opened = []
    original_open = io.open

    def track(file, *args, **kwargs):
        if Path(file).name == "step-registry.json":
            opened.append(file)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", track)
    with pytest.raises(operation.WorkflowStepListError) as error:
        operation.list_step_types(operation.WorkflowStepListRequest(root))
    assert error.value.code == "step_registry_read_failed"
    response = mcp_list.create_workflow_step_list_tool(launch_directory=root)()
    assert response.is_error is True
    assert (
        response.structured_content["error"]["code"] == "step_registry_read_failed"
    )
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(root))
    cli = CliRunner().invoke(app, ["workflow", "step", "list"])
    assert cli.exit_code == 1
    assert "Failed to read step registry" in cli.output
    assert "outside-secret" not in cli.output
    assert opened == []
    if registry_present:
        assert registry.read_bytes() == before
