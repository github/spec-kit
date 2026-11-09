"""Step and function registries share one persistence implementation.

Every case runs against both kinds, so a behavior can only exist for both.
"""

from __future__ import annotations

import json
import os
import stat
import sys

import pytest

from specify_cli.workflows._package_registry import PackageRegistry
from specify_cli.workflows.function import FunctionRegistry, WorkflowFunctionError
from specify_cli.workflows.step.catalog import StepRegistry, StepValidationError

KINDS = {
    "step": (StepRegistry, StepValidationError, "steps", "step-registry.json"),
    "function": (FunctionRegistry, WorkflowFunctionError, "functions", "function-registry.json"),
}


@pytest.fixture(params=sorted(KINDS))
def kind(request, project_dir):
    cls, error, directory, filename = KINDS[request.param]
    base = project_dir / ".specify" / "workflows" / directory
    return type("Kind", (), {
        "cls": cls, "error": error, "key": directory, "path": base / filename,
        "base": base, "root": project_dir, "label": request.param,
    })


def test_both_registries_derive_from_the_shared_base():
    assert issubclass(StepRegistry, PackageRegistry)
    assert issubclass(FunctionRegistry, PackageRegistry)
    assert StepRegistry.save is PackageRegistry.save
    assert FunctionRegistry.add is PackageRegistry.add
    assert StepRegistry.remove is FunctionRegistry.remove


def test_each_kind_keeps_its_established_attributes(kind):
    registry = kind.cls(kind.root)
    assert registry.registry_path == kind.path
    assert registry.data == {"schema_version": "1.0", kind.key: {}}
    assert getattr(registry, f"{kind.key}_dir") == kind.base


def test_add_get_list_remove_roundtrip(kind):
    registry = kind.cls(kind.root)
    registry.add("one", {"name": "One"})
    assert kind.cls(kind.root).get("one")["name"] == "One"
    assert list(kind.cls(kind.root).list()) == ["one"] and registry.is_installed("one")
    assert registry.remove("one") is True and registry.remove("one") is False
    assert kind.cls(kind.root).list() == {}


def test_add_stamps_times_and_preserves_installed_at(kind):
    registry = kind.cls(kind.root)
    registry.add("one", {"name": "a"})
    first = registry.get("one")["installed_at"]
    registry.add("one", {"name": "b"})
    entry = registry.get("one")
    assert entry["installed_at"] == first and entry["name"] == "b" and "updated_at" in entry


def test_metadata_is_copied_not_aliased(kind):
    registry = kind.cls(kind.root)
    metadata = {"functions": [{"name": "x"}]}
    registry.add("one", metadata)
    metadata["functions"][0]["name"] = "mutated"
    assert registry.get("one")["functions"][0]["name"] == "x"


def test_non_dict_existing_entry_is_replaced(kind):
    kind.base.mkdir(parents=True)
    kind.path.write_text(json.dumps({kind.key: {"one": "junk"}}))
    registry = kind.cls(kind.root)
    registry.add("one", {"name": "ok"})
    assert registry.get("one")["name"] == "ok"


@pytest.mark.parametrize("content", ["{bad", "[]", "", "null", "\x00"])
def test_unreadable_registry_loads_as_empty(kind, content):
    kind.base.mkdir(parents=True)
    kind.path.write_text(content)
    assert kind.cls(kind.root).list() == {}


def test_missing_records_key_is_repaired_and_other_keys_kept(kind):
    kind.base.mkdir(parents=True)
    kind.path.write_text(json.dumps({"schema_version": "1.0", "extra": 1, kind.key: []}))
    registry = kind.cls(kind.root)
    assert registry.list() == {} and registry.data["extra"] == 1


def test_failed_save_rolls_back_every_mutation(kind, monkeypatch):
    registry = kind.cls(kind.root)
    registry.add("keep", {"name": "keep"})

    def fail():
        raise kind.error("disk full")

    monkeypatch.setattr(registry, "save", fail)
    with pytest.raises(kind.error, match="disk full"):
        registry.add("new", {})
    with pytest.raises(kind.error, match="disk full"):
        registry.add("keep", {"name": "changed"})
    with pytest.raises(kind.error, match="disk full"):
        registry.remove("keep")
    assert list(registry.list()) == ["keep"] and registry.get("keep")["name"] == "keep"


def test_unserializable_metadata_is_rejected_and_rolled_back(kind):
    registry = kind.cls(kind.root)
    with pytest.raises((TypeError, ValueError, kind.error)):
        registry.add("bad", {"value": object()})
    assert not registry.is_installed("bad")
    assert not kind.path.exists() or "bad" not in json.loads(kind.path.read_text())[kind.key]


def test_write_error_uses_the_kind_error_type_and_label(kind, monkeypatch):
    registry = kind.cls(kind.root)

    def boom(*args, **kwargs):
        raise OSError("no space")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(kind.error) as info:
        registry.add("one", {})
    assert f"Failed to write {kind.label} registry" in str(info.value)
    assert [p.name for p in kind.base.iterdir()] == []  # no temp file left behind


def test_save_leaves_only_the_registry_file(kind):
    kind.cls(kind.root).add("one", {})
    assert [p.name for p in kind.base.iterdir()] == [kind.path.name]


@pytest.mark.skipif(sys.platform == "win32", reason="chmod mode bits not reliable on Windows")
def test_save_preserves_existing_file_mode(kind):
    registry = kind.cls(kind.root)
    registry.add("one", {})
    os.chmod(kind.path, 0o640)
    registry.add("two", {})
    assert stat.S_IMODE(kind.path.stat().st_mode) == 0o640


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
class TestSymlinks:
    def test_symlinked_directory_is_neither_read_nor_written(self, kind, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / kind.path.name).write_text(json.dumps({kind.key: {"evil": {}}}))
        kind.base.parent.mkdir(parents=True, exist_ok=True)
        kind.base.symlink_to(outside, target_is_directory=True)
        registry = kind.cls(kind.root)
        assert registry.list() == {}
        with pytest.raises(kind.error, match="symlinked path"):
            registry.add("one", {})
        assert json.loads((outside / kind.path.name).read_text()) == {kind.key: {"evil": {}}}

    def test_symlinked_registry_file_is_neither_read_nor_written(self, kind, tmp_path):
        outside = tmp_path / "outside.json"
        outside.write_text(json.dumps({kind.key: {"evil": {}}}))
        kind.base.mkdir(parents=True)
        kind.path.symlink_to(outside)
        registry = kind.cls(kind.root)
        assert registry.list() == {}
        with pytest.raises(kind.error, match="symlinked path"):
            registry.add("one", {})
        assert json.loads(outside.read_text()) == {kind.key: {"evil": {}}}
