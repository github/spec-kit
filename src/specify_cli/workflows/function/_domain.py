"""Domain models and persistence for installed workflow functions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .._package_registry import PackageRegistry
from ..expressions.filters import ARG_BOUNDS_RULE, format_filter_usage, valid_arg_bounds
from ..step.installer import StepInstallError, validate_step_id


class WorkflowFunctionError(ValueError):
    """A user-facing workflow function manifest, loader, or install error."""


@dataclass(frozen=True)
class FunctionExport:
    name: str
    handler: str
    min_args: int = 0
    max_args: int = 0
    description: str = ""

    @property
    def usage(self) -> str:
        return format_filter_usage(self.name, self.min_args, self.max_args)


@dataclass(frozen=True)
class FunctionManifest:
    id: str
    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    exports: tuple[FunctionExport, ...] = ()


_RESERVED_FUNCTION_IDS = frozenset({".cache", "function-registry.json"})
_FUNCTION_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_HANDLER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_function_id(value: str) -> None:
    try:
        validate_step_id(value)
    except StepInstallError as exc:
        raise WorkflowFunctionError(str(exc).replace("step id", "function id")) from exc
    if value.lower() in _RESERVED_FUNCTION_IDS:
        raise WorkflowFunctionError(f"Invalid function id '{value}': reserved name")


def _string(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise WorkflowFunctionError(f"function.yml '{key}' must be a string")
    return value


def _unknown_keys(mapping: dict[Any, Any], allowed: set[str]) -> list[str]:
    """Sorted text of the keys outside *allowed*.

    YAML mapping keys can be any scalar, so they are stringified before they
    are sorted or joined into a message.
    """
    return sorted(str(key) for key in mapping.keys() - allowed)


def parse_function_manifest(text: str, expected_id: str | None = None) -> FunctionManifest:
    """Parse the strict ``function.yml`` schema without importing code."""
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise WorkflowFunctionError(f"Invalid function.yml: {exc}") from exc
    if not isinstance(raw, dict):
        raise WorkflowFunctionError("function.yml must be a YAML mapping")
    allowed = {"id", "name", "version", "description", "functions"}
    unknown = _unknown_keys(raw, allowed)
    if unknown:
        raise WorkflowFunctionError(f"function.yml contains unknown key(s): {', '.join(unknown)}")
    function_id = raw.get("id")
    if not isinstance(function_id, str) or not function_id:
        raise WorkflowFunctionError("function.yml is missing required 'id'")
    _validate_function_id(function_id)
    if expected_id is not None and function_id != expected_id:
        raise WorkflowFunctionError(
            f"function.yml id ({function_id!r}) does not match function ID ({expected_id!r})"
        )
    functions = raw.get("functions")
    if not isinstance(functions, list) or not functions:
        raise WorkflowFunctionError("function.yml 'functions' must be a non-empty list")
    exports: list[FunctionExport] = []
    seen: set[str] = set()
    for index, item in enumerate(functions):
        if not isinstance(item, dict):
            raise WorkflowFunctionError(f"function.yml function at index {index} must be a mapping")
        allowed_export = {"name", "handler", "min_args", "max_args", "description"}
        unknown_export = _unknown_keys(item, allowed_export)
        if unknown_export:
            raise WorkflowFunctionError(
                f"function.yml function at index {index} contains unknown key(s): {', '.join(unknown_export)}"
            )
        name = item.get("name")
        handler = item.get("handler")
        if not isinstance(name, str) or _FUNCTION_NAME_RE.fullmatch(name) is None:
            raise WorkflowFunctionError(
                f"function.yml function at index {index} has invalid name {name!r}"
            )
        if name in seen:
            raise WorkflowFunctionError(f"function.yml declares function '{name}' more than once")
        seen.add(name)
        if not isinstance(handler, str) or _HANDLER_RE.fullmatch(handler) is None:
            raise WorkflowFunctionError(
                f"function.yml function '{name}' has invalid handler {handler!r}"
            )
        minimum = item.get("min_args", 0)
        maximum = item.get("max_args", 0)
        if not valid_arg_bounds(minimum, maximum):
            raise WorkflowFunctionError(
                f"function.yml function '{name}' has invalid argument bounds: "
                f"expected {ARG_BOUNDS_RULE}"
            )
        description = item.get("description", "")
        if not isinstance(description, str):
            raise WorkflowFunctionError(f"function.yml function '{name}' description must be a string")
        exports.append(FunctionExport(name, handler, minimum, maximum, description))
    return FunctionManifest(
        function_id,
        _string(raw, "name"),
        _string(raw, "version", "0.0.0"),
        _string(raw, "description"),
        tuple(exports),
    )


class FunctionRegistry(PackageRegistry):
    """Persistent metadata for packages under ``workflows/functions``."""

    REGISTRY_FILE = "function-registry.json"
    RECORDS_KEY = "functions"
    DIRECTORY = "functions"
    LABEL = "function"
    ERROR = WorkflowFunctionError

    @property
    def functions_dir(self) -> Path:
        return self.base_dir
