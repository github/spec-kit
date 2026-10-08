"""Persistence tests for the custom step registry."""

from __future__ import annotations

import json

import pytest

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
