"""Persistence tests for the custom step registry."""

from __future__ import annotations

import json
import os

import pytest

from specify_cli._file_policy import project_files
from specify_cli.workflows.step.catalog import StepRegistry, StepValidationError


def _entry(step_id: str) -> dict[str, str]:
    return {
        "name": "Example",
        "version": "1.0.0",
        "description": "",
        "author": "",
        "type_key": step_id,
        "source": "local",
    }


def test_save_keeps_existing_registry_when_json_serialization_fails(project_dir):
    registry = StepRegistry(project_dir)
    registry.add("first", _entry("first"))
    before = registry.registry_path.read_bytes()
    registry.data["steps"]["second"] = {"not_json": {1, 2}}

    with pytest.raises(StepValidationError):
        registry.save()

    assert registry.registry_path.read_bytes() == before
    assert json.loads(before)["steps"]["first"]["type_key"] == "first"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are POSIX-only")
def test_load_ignores_a_fifo_registry_file(project_dir):
    steps_dir = project_dir / ".specify" / "workflows" / "steps"
    steps_dir.mkdir(parents=True)
    os.mkfifo(steps_dir / "step-registry.json")

    registry = StepRegistry(project_dir)

    assert registry.list() == {}


def _write_registry(project_dir, entries):
    steps_dir = project_dir / ".specify" / "workflows" / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    path = steps_dir / "step-registry.json"
    path.write_text(json.dumps({"steps": entries}), encoding="utf-8")
    return path


def test_load_rejects_oversized_registry_without_helper(project_dir):
    path = _write_registry(project_dir, {"first": _entry("first")})
    size = path.stat().st_size
    assert StepRegistry(project_dir, max_bytes=size).list() == {
        "first": _entry("first")
    }
    assert StepRegistry(project_dir, max_bytes=size - 1).list() == {}


def test_load_via_helper_rejects_oversized_registry(project_dir):
    path = _write_registry(project_dir, {"first": _entry("first")})
    size = path.stat().st_size
    with project_files(project_dir) as files:
        assert StepRegistry(
            project_dir, read_files=files, max_bytes=size
        ).list() == {"first": _entry("first")}
        assert (
            StepRegistry(project_dir, read_files=files, max_bytes=size - 1).list()
            == {}
        )


def test_load_via_helper_fails_closed_on_symlinked_steps(project_dir):
    outside = project_dir / "outside"
    outside.mkdir()
    (outside / "step-registry.json").write_text(
        json.dumps({"steps": {"first": _entry("first")}}), encoding="utf-8"
    )
    steps_dir = project_dir / ".specify" / "workflows" / "steps"
    try:
        steps_dir.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    with project_files(project_dir) as files:
        with pytest.raises(OSError):
            StepRegistry(project_dir, read_files=files)


def test_load_via_helper_keeps_best_effort_for_missing_and_corrupt(project_dir):
    with project_files(project_dir) as files:
        assert StepRegistry(project_dir, read_files=files).list() == {}
    steps_dir = project_dir / ".specify" / "workflows" / "steps"
    steps_dir.mkdir(parents=True)
    (steps_dir / "step-registry.json").write_text("{not json", encoding="utf-8")
    with project_files(project_dir) as files:
        assert StepRegistry(project_dir, read_files=files).list() == {}


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are POSIX-only")
def test_load_via_helper_ignores_a_fifo_registry_file(project_dir):
    steps_dir = project_dir / ".specify" / "workflows" / "steps"
    steps_dir.mkdir(parents=True)
    os.mkfifo(steps_dir / "step-registry.json")
    with project_files(project_dir) as files:
        assert StepRegistry(project_dir, read_files=files).list() == {}
