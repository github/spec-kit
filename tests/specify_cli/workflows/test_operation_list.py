"""Transport-neutral installed-workflow contract and effect boundaries."""

import builtins
import errno
import io
import json
import os
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from specify_cli.workflows import _operation_list as operation
from specify_cli.file_helper import FileHelper


def _registry(root, entries):
    directory = root / ".specify" / "workflows"
    directory.mkdir(parents=True)
    path = directory / "workflow-registry.json"
    path.write_text(json.dumps({"workflows": entries}), encoding="utf-8")
    return path


def test_registry_order_defaults_and_warnings(tmp_path):
    _registry(
        tmp_path,
        {
            "z": {"description": ["old", "metadata"], "enabled": 0},
            "broken[entry]": None,
            "a": {"name": None, "version": 7},
        },
    )
    result = operation.list_workflows(operation.WorkflowListRequest(tmp_path))
    assert result == operation.WorkflowListResult(
        (
            operation.WorkflowListEntry("z", "z", "?", "['old', 'metadata']", False),
            operation.WorkflowListWarning(
                "broken[entry]", "Skipping corrupted registry entry 'broken[entry]'."
            ),
            operation.WorkflowListEntry("a", "None", "7", None, True),
        )
    )
    with pytest.raises(FrozenInstanceError):
        result.truncated = True


def test_missing_registry_is_empty_without_creating_storage(tmp_path):
    (tmp_path / ".specify").mkdir()
    assert operation.list_workflows(operation.WorkflowListRequest(tmp_path)).items == ()
    assert list((tmp_path / ".specify").iterdir()) == []


@pytest.mark.parametrize("contents", ["{", "[]", '{"workflows": []}', "\udcff"])
def test_corrupt_registry_fails_closed(tmp_path, contents):
    path = _registry(tmp_path, {})
    path.write_bytes(contents.encode("utf-8", errors="surrogateescape"))
    with pytest.raises(operation.WorkflowListError) as exc:
        operation.list_workflows(operation.WorkflowListRequest(tmp_path))
    assert exc.value.code == "workflow_registry_read_failed"


@pytest.mark.parametrize("limit", [0, -1, 1001, True, "2", 1.5])
def test_invalid_limit_is_rejected_before_io(tmp_path, monkeypatch, limit):
    monkeypatch.setattr(
        operation,
        "project_files",
        lambda *a: pytest.fail("IO before validation"),
    )
    with pytest.raises(operation.WorkflowListError) as exc:
        operation.list_workflows(operation.WorkflowListRequest(tmp_path, limit))
    assert exc.value.code == "invalid_limit"


def test_limit_counts_warnings_and_explicitly_reports_omissions(tmp_path):
    _registry(tmp_path, {"broken": 1, "ok": {}, "last": {}})
    request = operation.WorkflowListRequest(tmp_path, 2)
    result = operation.list_workflows(request)
    assert len(result.items) == 2
    assert result.truncated is True
    assert isinstance(result.items[0], operation.WorkflowListWarning)
    assert (
        operation.list_workflows(operation.WorkflowListRequest(tmp_path, 3)).truncated
        is False
    )
    assert (
        len(operation.list_workflows(operation.WorkflowListRequest(tmp_path)).items)
        == 3
    )


def test_relative_and_nonproject_directories_are_rejected(tmp_path):
    with pytest.raises(operation.WorkflowListError) as exc:
        operation.list_workflows(operation.WorkflowListRequest(Path("relative")))
    assert exc.value.code == "invalid_project_directory"
    with pytest.raises(operation.WorkflowListError) as exc:
        operation.list_workflows(operation.WorkflowListRequest(tmp_path))
    assert exc.value.code == "not_a_spec_kit_project"


@pytest.mark.parametrize(
    "suffix",
    [
        ".specify",
        ".specify/workflows",
        ".specify/workflows/runs",
        ".specify/workflows/overlays",
    ],
)
def test_nondirectory_storage_is_rejected(tmp_path, suffix):
    target = tmp_path / suffix
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("not a directory", encoding="utf-8")
    with pytest.raises(operation.WorkflowListError):
        operation.list_workflows(operation.WorkflowListRequest(tmp_path))


@pytest.mark.parametrize(
    "suffix",
    [
        ".specify",
        ".specify/workflows",
        ".specify/workflows/runs",
        ".specify/workflows/overlays",
        ".specify/workflows/workflow-registry.json",
    ],
)
def test_symlinked_storage_is_rejected(tmp_path, suffix):
    root = tmp_path / "project"
    target = root / suffix
    target.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    is_file = suffix.endswith(".json")
    if is_file:
        outside.write_text('{"workflows": {}}', encoding="utf-8")
    else:
        outside.mkdir()
    try:
        target.symlink_to(outside, target_is_directory=not is_file)
    except OSError as exc:
        if exc.errno in {
            errno.EPERM,
            errno.ENOSYS,
            errno.ENOTSUP,
            errno.EOPNOTSUPP,
        } or getattr(exc, "winerror", None) in {50, 1314}:
            pytest.skip(f"Host cannot create symlinks: {exc}")
        raise
    with pytest.raises(operation.WorkflowListError):
        operation.list_workflows(operation.WorkflowListRequest(root))


def test_operation_has_no_writes_network_execution_or_rendering(
    tmp_path, monkeypatch, capsys
):
    from specify_cli.authentication import http
    from specify_cli.integrations import installer
    from specify_cli import workflows

    path = _registry(tmp_path, {"ok": {}})
    before = path.read_bytes()
    original_open = builtins.open
    original_io_open = io.open

    def read_only_open(file, mode="r", *args, **kwargs):
        assert not any(flag in mode for flag in "wax+")
        return original_open(file, mode, *args, **kwargs)

    def unexpected(*args, **kwargs):
        pytest.fail("Listing must not write, fetch, import custom steps or execute")

    monkeypatch.setattr(builtins, "open", read_only_open)

    def read_only_io_open(file, mode="r", *args, **kwargs):
        assert not any(flag in mode for flag in "wax+")
        return original_io_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(io, "open", read_only_io_open)
    monkeypatch.setattr(Path, "mkdir", unexpected)
    monkeypatch.setattr(Path, "write_text", unexpected)
    monkeypatch.setattr(Path, "write_bytes", unexpected)
    monkeypatch.setattr(operation.WorkflowRegistry, "save", unexpected)
    monkeypatch.setattr(http, "open_url", unexpected)
    monkeypatch.setattr(subprocess, "run", unexpected)
    monkeypatch.setattr(workflows, "load_custom_steps", unexpected)
    monkeypatch.setattr(installer, "load_installed_integrations", unexpected)
    result = operation.list_workflows(operation.WorkflowListRequest(tmp_path))
    assert len(result.items) == 1
    assert path.read_bytes() == before
    assert capsys.readouterr() == ("", "")


def test_unreadable_registry_is_not_empty_success(tmp_path, monkeypatch):
    path = _registry(tmp_path, {})
    original = FileHelper.read_bytes

    def denied(files, file):
        if files.root / file == path:
            raise PermissionError("private registry details")
        return original(files, file)

    monkeypatch.setattr(FileHelper, "read_bytes", denied)
    with pytest.raises(operation.WorkflowListError) as exc:
        operation.list_workflows(operation.WorkflowListRequest(tmp_path))
    assert exc.value.code == "workflow_registry_read_failed"


@pytest.mark.skipif(os.name != "nt", reason="Windows directory junction regression")
@pytest.mark.parametrize("registry_present", [False, True])
def test_list_rejects_junction_at_registry_read_boundary(
    tmp_path, monkeypatch, registry_present
):
    from typer.testing import CliRunner
    from specify_cli import app
    from specify_cli.workflows import mcp_list

    root = tmp_path / "project"
    (root / ".specify").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    registry = outside / "workflow-registry.json"
    if registry_present:
        registry.write_text('{"workflows": {"outside-secret": {}}}', encoding="utf-8")
    before = registry.read_bytes() if registry_present else None
    junction = root / ".specify" / "workflows"
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
        if Path(file).name == "workflow-registry.json":
            opened.append(file)
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", track)
    with pytest.raises(operation.WorkflowListError) as error:
        operation.list_workflows(operation.WorkflowListRequest(root))
    assert error.value.code == "workflow_registry_read_failed"
    response = mcp_list.create_workflow_list_tool(launch_directory=root)()
    assert response.is_error is True
    assert (
        response.structured_content["error"]["code"] == "workflow_registry_read_failed"
    )
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(root))
    cli = CliRunner().invoke(app, ["workflow", "list"])
    assert cli.exit_code == 1
    assert "Failed to read workflow registry" in cli.output
    assert "outside-secret" not in cli.output
    assert opened == []
    monkeypatch.setattr(io, "open", original_open)
    if registry_present:
        assert registry.read_bytes() == before
    else:
        assert not registry.exists()


def test_unexpected_symlink_setup_errors_are_not_skipped(tmp_path, monkeypatch):
    def missing_parent(*args, **kwargs):
        raise FileNotFoundError(errno.ENOENT, "unexpected fixture setup failure")

    monkeypatch.setattr(Path, "symlink_to", missing_parent)
    with pytest.raises(FileNotFoundError, match="unexpected fixture setup failure"):
        test_symlinked_storage_is_rejected(tmp_path, ".specify/workflows")


def test_policy_reader_preserves_legacy_json_error_offsets(tmp_path):
    path = _registry(tmp_path, {})
    path.write_bytes(b'{\r\n "workflows":\r\n broken\r\n}')
    with pytest.raises(OSError) as legacy:
        operation.WorkflowRegistry(tmp_path)
    with pytest.raises(operation.WorkflowListError) as current:
        operation.list_workflows(operation.WorkflowListRequest(tmp_path))
    assert str(current.value) == f"Failed to read workflow registry: {legacy.value}"
