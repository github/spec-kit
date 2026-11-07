"""Load project-installed workflow function packages."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .. import _drop_modules, _import_package
from ..expressions.filters import (
    BUILTIN_FILTERS,
    register_custom_filter,
    unregister_custom_filter,
    unregister_custom_filters,
)
from ._domain import FunctionManifest, WorkflowFunctionError, parse_function_manifest

_CUSTOM_FUNCTION_MODULES: set[str] = set()


def _unload_custom_functions() -> None:
    unregister_custom_filters()
    _drop_modules(_CUSTOM_FUNCTION_MODULES)
    _CUSTOM_FUNCTION_MODULES.clear()


def _function_paths(project_root: Path) -> tuple[Path, Path]:
    root = Path(project_root)
    current = root
    for part in (".specify", "workflows", "functions"):
        current /= part
        if current.is_symlink():
            raise WorkflowFunctionError(f"Refusing to load symlinked function directory '{current}'")
    return current, root


def _collision_error(collisions: list[tuple[str, str, str]]) -> WorkflowFunctionError:
    """Describe every collision as ``(name, existing owner, new owner)``."""
    if len(collisions) == 1:
        name, other, source = collisions[0]
        return WorkflowFunctionError(
            f"Workflow function '{name}' collides between {other} and {source}; "
            "rename or remove the package."
        )
    details = "; ".join(
        f"'{name}' between {other} and {source}" for name, other, source in collisions
    )
    return WorkflowFunctionError(
        f"Workflow functions collide: {details}; rename or remove the packages."
    )


def load_workflow_functions(project_root: Path) -> list[str]:
    """Load every valid function package for *project_root*.

    Discovery and validation happen before importing any package, so a manifest
    collision cannot execute package code. A package is registered atomically:
    a bad export does not leave its earlier exports or synthetic modules behind.
    """
    _unload_custom_functions()
    functions_dir, _ = _function_paths(Path(project_root))
    if not functions_dir.exists():
        return []
    if not functions_dir.is_dir():
        raise WorkflowFunctionError(f"Function directory is not a directory: '{functions_dir}'")

    manifests: list[tuple[Path, FunctionManifest]] = []
    owners: dict[str, str] = {name: "built-in filters" for name in BUILTIN_FILTERS}
    collisions: list[tuple[str, str, str]] = []
    for package_dir in sorted(functions_dir.iterdir(), key=lambda p: p.name):
        if package_dir.name in {"function-registry.json", ".cache"}:
            continue
        if package_dir.is_symlink():
            continue
        if not package_dir.is_dir():
            continue
        manifest_path = package_dir / "function.yml"
        init_path = package_dir / "__init__.py"
        if manifest_path.is_symlink() or init_path.is_symlink():
            continue
        if not manifest_path.is_file() or not init_path.is_file():
            continue
        try:
            manifest = parse_function_manifest(
                manifest_path.read_text(encoding="utf-8"), package_dir.name
            )
        except (OSError, UnicodeError):
            continue
        except WorkflowFunctionError:
            # Runtime loading follows custom-step behavior for malformed or
            # broken packages: ignore that package, but never hide collisions
            # among manifests that were successfully parsed.
            continue
        for export in manifest.exports:
            if export.name in owners:
                collisions.append((export.name, owners[export.name], f"package '{manifest.id}'"))
            else:
                owners[export.name] = f"package '{manifest.id}'"
        manifests.append((package_dir, manifest))
    if collisions:
        raise _collision_error(collisions)

    loaded: list[str] = []
    for package_dir, manifest in manifests:
        safe_id = re.sub(r"[^A-Za-z0-9_]", "_", manifest.id)
        module_name = (
            f"_speckit_workflow_function_{safe_id}_"
            f"{hashlib.sha256(str(package_dir).encode()).hexdigest()[:8]}"
        )
        added: list[str] = []
        successful = False
        try:
            module = _import_package(module_name, package_dir)
            handlers: list[tuple[Any, Any]] = []
            for export in manifest.exports:
                handler = getattr(module, export.handler, None)
                if not callable(handler):
                    raise WorkflowFunctionError(
                        f"Workflow function '{export.name}' handler '{export.handler}' "
                        f"in package '{manifest.id}' is not callable"
                    )
                handlers.append((export, handler))
            for export, handler in handlers:
                register_custom_filter(
                    export.name, handler, export.min_args, export.max_args
                )
                added.append(export.name)
            _CUSTOM_FUNCTION_MODULES.add(module_name)
            loaded.extend(export.name for export in manifest.exports)
            successful = True
        except WorkflowFunctionError:
            # A package is an all-or-nothing registration unit.  Broken package
            # code follows the installed-step loader's skip behavior; only the
            # collision pre-pass above is intentionally fatal.
            pass
        except Exception:
            pass
        finally:
            if not successful:
                for name in added:
                    unregister_custom_filter(name)
                _drop_modules({module_name})
    return loaded
