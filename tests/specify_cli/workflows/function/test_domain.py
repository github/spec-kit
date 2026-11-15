"""Manifest parser, id validation and persistent registry."""

from __future__ import annotations

import json
import os

import pytest
import yaml

from specify_cli.workflows.function import (
    FunctionRegistry,
    WorkflowFunctionError,
    parse_function_manifest,
)
from specify_cli.workflows.function._domain import _validate_function_id
from specify_cli.workflows.step.installer import StepInstallError, validate_step_id

from .helpers import functions_dir


def manifest(**overrides):
    data = {"id": "text", "functions": [{"name": "trim", "handler": "trim"}]}
    data.update(overrides)
    return yaml.safe_dump(data)


class TestManifestParsing:
    def test_minimal_manifest_uses_defaults(self):
        parsed = parse_function_manifest(manifest(), "text")
        assert (parsed.id, parsed.name, parsed.version, parsed.description) == (
            "text", "", "0.0.0", ""
        )
        (export,) = parsed.exports
        assert (export.name, export.handler, export.min_args, export.max_args) == (
            "trim", "trim", 0, 0
        )
        assert export.description == "" and export.usage == "trim"

    def test_full_manifest(self):
        parsed = parse_function_manifest(
            manifest(
                name="Text helpers", version="1.2.3", description="d",
                functions=[
                    {"name": "pad", "handler": "pad_text", "min_args": 2,
                     "max_args": 3, "description": "Pad it"},
                    {"name": "trim", "handler": "trim"},
                ],
            ),
            "text",
        )
        assert (parsed.name, parsed.version, parsed.description) == ("Text helpers", "1.2.3", "d")
        assert [e.name for e in parsed.exports] == ["pad", "trim"]
        assert parsed.exports[0].usage == "pad(arg1, arg2, arg3)"
        assert parsed.exports[0].description == "Pad it"

    def test_expected_id_is_optional(self):
        assert parse_function_manifest(manifest()).id == "text"

    @pytest.mark.parametrize(
        ("text", "message"),
        [
            ("a: [", "Invalid function.yml"),
            ("- a\n- b\n", "must be a YAML mapping"),
            ("", "must be a YAML mapping"),
            (manifest(extra=1), "unknown key"),
            (yaml.safe_dump({"functions": [{"name": "a", "handler": "a"}]}), "missing required 'id'"),
            (manifest(id=""), "missing required 'id'"),
            (manifest(id=5), "missing required 'id'"),
            (manifest(functions=None), "non-empty list"),
            (manifest(functions=[]), "non-empty list"),
            (manifest(functions={"name": "a"}), "non-empty list"),
            (manifest(functions=["a"]), "must be a mapping"),
            (manifest(functions=[{"name": "a", "handler": "a", "x": 1}]), "unknown key"),
            (manifest(functions=[{"handler": "a"}]), "invalid name"),
            (manifest(functions=[{"name": "a"}]), "invalid handler"),
            (manifest(name=3), "'name' must be a string"),
            (manifest(version=1.0), "'version' must be a string"),
            (manifest(description=[]), "'description' must be a string"),
            (manifest(functions=[{"name": "a", "handler": "a", "description": 1}]), "description must be a string"),
        ],
    )
    def test_invalid_manifests_are_rejected(self, text, message):
        with pytest.raises(WorkflowFunctionError, match=message):
            parse_function_manifest(text, "text")

    def test_id_must_match_expected_id(self):
        with pytest.raises(WorkflowFunctionError, match="does not match"):
            parse_function_manifest(manifest(), "other")

    @pytest.mark.parametrize("name", ["Trim", "a-b", "1a", "a.b", "a b", "", None, 3])
    def test_invalid_function_names(self, name):
        data = manifest(functions=[{"name": name, "handler": "h"}])
        with pytest.raises(WorkflowFunctionError, match="invalid name"):
            parse_function_manifest(data, "text")

    @pytest.mark.parametrize("handler", ["a.b", "1a", "a b", "a-b", "", None, 3, "a()"])
    def test_invalid_handlers(self, handler):
        data = manifest(functions=[{"name": "a", "handler": handler}])
        with pytest.raises(WorkflowFunctionError, match="invalid handler"):
            parse_function_manifest(data, "text")

    def test_duplicate_name_in_one_manifest(self):
        data = manifest(functions=[
            {"name": "a", "handler": "x"}, {"name": "a", "handler": "y"},
        ])
        with pytest.raises(WorkflowFunctionError, match="more than once"):
            parse_function_manifest(data, "text")

    @pytest.mark.parametrize(
        ("text", "listed"),
        [
            ("id: text\n1: x\nfunctions: [{name: a, handler: a}]\n", "1"),
            ("id: text\n1: x\nb: y\nfunctions: [{name: a, handler: a}]\n", "1, b"),
            ("id: text\n1.5: x\n~: y\nfunctions: [{name: a, handler: a}]\n", "1.5, None"),
            ("id: text\nfunctions: [{name: a, handler: a, 2: x}]\n", "2"),
            ("id: text\nfunctions: [{name: a, handler: a, 2: x, c: y}]\n", "2, c"),
        ],
    )
    def test_non_string_unknown_keys_are_reported_not_raised(self, text, listed):
        with pytest.raises(WorkflowFunctionError, match=f"unknown key\\(s\\): {listed}$"):
            parse_function_manifest(text, "text")

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [(2, 1), (-1, 0), (0, -1), (True, 1), (0, True), ("1", 2), (0, 1.5), (None, 1)],
    )
    def test_invalid_bounds(self, minimum, maximum):
        data = manifest(functions=[
            {"name": "a", "handler": "a", "min_args": minimum, "max_args": maximum}
        ])
        with pytest.raises(WorkflowFunctionError, match="argument bounds"):
            parse_function_manifest(data, "text")

    @pytest.mark.parametrize("maximum", [17, 1000, 100_000_000])
    def test_max_args_above_the_cap_is_rejected(self, maximum):
        data = manifest(functions=[{"name": "a", "handler": "a", "max_args": maximum}])
        with pytest.raises(WorkflowFunctionError, match="argument bounds.*<= 16"):
            parse_function_manifest(data, "text")

    def test_min_args_above_the_cap_is_rejected(self):
        data = manifest(functions=[
            {"name": "a", "handler": "a", "min_args": 17, "max_args": 17}
        ])
        with pytest.raises(WorkflowFunctionError, match="argument bounds"):
            parse_function_manifest(data, "text")

    def test_max_args_at_the_cap_is_accepted(self):
        data = manifest(functions=[
            {"name": "a", "handler": "a", "min_args": 16, "max_args": 16}
        ])
        (export,) = parse_function_manifest(data, "text").exports
        assert (export.min_args, export.max_args) == (16, 16)

    def test_max_defaults_to_zero_so_min_alone_is_invalid(self):
        data = manifest(functions=[{"name": "a", "handler": "a", "min_args": 1}])
        with pytest.raises(WorkflowFunctionError, match="argument bounds"):
            parse_function_manifest(data, "text")

    def test_unsafe_yaml_tags_are_not_executed(self):
        with pytest.raises(WorkflowFunctionError, match="Invalid function.yml"):
            parse_function_manifest("id: !!python/object/apply:os.system ['true']", "x")


class TestFunctionIds:
    @pytest.mark.parametrize("value", ["text", "my-fn", "a1", "MyFn", "a_b"])
    def test_valid_ids(self, value):
        _validate_function_id(value)

    @pytest.mark.parametrize(
        "value",
        ["", " ", " a", "a ", "a/b", "a\\b", ".", "..", ".hidden", "a.", "../x",
         "con", "NUL", "a:b", "a\x01"],
    )
    def test_ids_rejected_by_the_shared_step_validator_are_rejected(self, value):
        with pytest.raises(StepInstallError):
            validate_step_id(value)
        with pytest.raises(WorkflowFunctionError, match="function id"):
            _validate_function_id(value)

    @pytest.mark.parametrize(
        "value",
        [
            ".cache",
            ".CACHE",
            "function-registry.json",
            "Function-Registry.Json",
            "FUNCTION-REGISTRY.JSON",
        ],
    )
    def test_function_specific_reserved_names(self, value):
        # Case variants alias the registry file on case-insensitive filesystems.
        with pytest.raises(WorkflowFunctionError):
            _validate_function_id(value)


class TestRegistry:
    def test_empty_registry(self, project_dir):
        registry = FunctionRegistry(project_dir)
        assert registry.list() == {} and not registry.is_installed("x")
        assert registry.get("x") is None

    def test_add_persists_and_reloads(self, project_dir):
        registry = FunctionRegistry(project_dir)
        registry.add("text", {"name": "Text", "functions": []})
        assert FunctionRegistry(project_dir).get("text")["name"] == "Text"
        stored = json.loads((functions_dir(project_dir) / "function-registry.json").read_text())
        assert stored["schema_version"] == "1.0"
        assert {"installed_at", "updated_at"} <= set(stored["functions"]["text"])

    def test_replace_keeps_installed_at(self, project_dir):
        registry = FunctionRegistry(project_dir)
        registry.add("text", {"name": "one"})
        first = registry.get("text")["installed_at"]
        registry.add("text", {"name": "two"})
        entry = registry.get("text")
        assert entry["name"] == "two" and entry["installed_at"] == first

    def test_remove(self, project_dir):
        registry = FunctionRegistry(project_dir)
        registry.add("text", {})
        assert registry.remove("text") is True
        assert registry.remove("text") is False
        assert FunctionRegistry(project_dir).list() == {}

    def test_list_returns_a_copy(self, project_dir):
        registry = FunctionRegistry(project_dir)
        registry.add("text", {})
        registry.list().clear()
        assert registry.is_installed("text")

    @pytest.mark.parametrize("content", ["{bad", "[]", '{"functions": []}', "", "\x00"])
    def test_corrupt_registry_loads_as_empty(self, project_dir, content):
        path = functions_dir(project_dir) / "function-registry.json"
        path.parent.mkdir(parents=True)
        path.write_text(content, encoding="utf-8")
        assert FunctionRegistry(project_dir).list() == {}

    def test_failed_save_rolls_back_in_memory_state(self, project_dir, monkeypatch):
        registry = FunctionRegistry(project_dir)
        registry.add("keep", {"name": "keep"})
        monkeypatch.setattr(
            registry, "save",
            lambda: (_ for _ in ()).throw(WorkflowFunctionError("disk full")),
        )
        with pytest.raises(WorkflowFunctionError, match="disk full"):
            registry.add("new", {})
        with pytest.raises(WorkflowFunctionError, match="disk full"):
            registry.add("keep", {"name": "changed"})
        with pytest.raises(WorkflowFunctionError, match="disk full"):
            registry.remove("keep")
        assert registry.list().keys() == {"keep"}
        assert registry.get("keep")["name"] == "keep"

    def test_save_leaves_no_temp_files(self, project_dir):
        FunctionRegistry(project_dir).add("text", {})
        assert [p.name for p in functions_dir(project_dir).iterdir()] == ["function-registry.json"]

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_functions_dir_is_not_read_or_written(self, project_dir):
        outside = project_dir.parent / f"{project_dir.name}-outside"
        outside.mkdir()
        (outside / "function-registry.json").write_text(
            json.dumps({"functions": {"evil": {}}}), encoding="utf-8"
        )
        functions_dir(project_dir).symlink_to(outside, target_is_directory=True)
        registry = FunctionRegistry(project_dir)
        assert registry.list() == {}
        with pytest.raises(WorkflowFunctionError, match="symlink"):
            registry.add("text", {})
        assert json.loads((outside / "function-registry.json").read_text()) == {
            "functions": {"evil": {}}
        }
