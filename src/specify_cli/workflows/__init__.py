"""Workflow engine for multi-step, resumable automation workflows.

Provides:
- ``StepBase`` — abstract base every step type must implement.
- ``StepContext`` — execution context passed to each step.
- ``StepResult`` — return value from step execution.
- ``STEP_REGISTRY`` — maps ``type_key`` to ``StepBase`` subclass instances.
- ``WorkflowEngine`` — orchestrator that loads, validates, and executes
  workflow YAML definitions.
- ``load_custom_steps`` — loads community-installed step types into STEP_REGISTRY.
"""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import StepBase

# Maps step type_key → StepBase instance.
STEP_REGISTRY: dict[str, StepBase] = {}
_STEP_LOCK = RLock()


def _register_step(step: StepBase) -> None:
    """Register a step type instance in the global registry.

    Raises ``ValueError`` for falsy keys and ``KeyError`` for duplicates.
    """
    key = step.type_key
    if not key:
        raise ValueError("Cannot register step type with an empty type_key.")
    with _STEP_LOCK:
        if key in STEP_REGISTRY:
            raise KeyError(f"Step type with key {key!r} is already registered.")
        STEP_REGISTRY[key] = step


def get_step_type(type_key: str) -> StepBase | None:
    """Return the step type for *type_key*, or ``None`` if not registered."""
    with _STEP_LOCK:
        return STEP_REGISTRY.get(type_key)


# -- Register built-in step types ----------------------------------------

def _register_builtin_steps() -> None:
    """Register all built-in step types."""
    from .steps.command import CommandStep
    from .steps.do_while import DoWhileStep
    from .steps.fan_in import FanInStep
    from .steps.fan_out import FanOutStep
    from .steps.gate import GateStep
    from .steps.if_then import IfThenStep
    from .steps.init import InitStep
    from .steps.prompt import PromptStep
    from .steps.shell import ShellStep
    from .steps.slot import SlotStep
    from .steps.switch import SwitchStep
    from .steps.while_loop import WhileStep

    _register_step(CommandStep())
    _register_step(DoWhileStep())
    _register_step(FanInStep())
    _register_step(FanOutStep())
    _register_step(GateStep())
    _register_step(IfThenStep())
    _register_step(InitStep())
    _register_step(PromptStep())
    _register_step(ShellStep())
    _register_step(SlotStep())
    _register_step(SwitchStep())
    _register_step(WhileStep())


_register_builtin_steps()

# The step types Spec Kit ships, snapshotted before any community step can be
# loaded. Callers that need the immutable set (e.g. the bundler's reference
# checker) must use this instead of the project-scoped entries in STEP_REGISTRY.
BUILTIN_STEP_TYPES: frozenset[str] = frozenset(STEP_REGISTRY)


def get_step_registry(project_root: Path | None = None) -> dict[str, StepBase]:
    """Return an isolated registry, loading a project when one is supplied."""
    with _STEP_LOCK:
        if project_root is None:
            return dict(STEP_REGISTRY)
        registry = {
            key: step for key, step in STEP_REGISTRY.items()
            if key in BUILTIN_STEP_TYPES
        }
        _load_custom_steps(project_root, registry)
        return registry


def _unload_step_module(module_name: str) -> None:
    import sys

    with _STEP_LOCK:
        for name in tuple(sys.modules):
            if name == module_name or name.startswith(module_name + "."):
                sys.modules.pop(name, None)


def load_custom_steps(project_root: Path) -> list[str]:
    """Load community-installed custom step types into STEP_REGISTRY.

    Scans ``.specify/workflows/steps/`` for installed step packages.
    Each valid package must contain ``step.yml`` (with a ``step.type_key``
    field) and ``__init__.py`` (a ``StepBase`` subclass).

    Returns a list of type_keys that were successfully loaded.
    Silently skips packages that fail to import or validate.
    """
    with _STEP_LOCK:
        registry = get_step_registry(project_root)
        STEP_REGISTRY.clear()
        STEP_REGISTRY.update(registry)
        return [key for key in registry if key not in BUILTIN_STEP_TYPES]


def _load_custom_steps(project_root: Path, registry: dict[str, StepBase]) -> None:
    """Populate a private registry while the caller holds the import lock."""
    import importlib as _importlib
    import importlib.util as _importlib_util
    import re as _re
    import shutil as _shutil
    import sys as _sys
    import uuid as _uuid
    import weakref as _weakref

    steps_dir = Path(project_root) / ".specify" / "workflows" / "steps"

    # Defense-in-depth: refuse to execute step code from a symlinked
    # parent directory under .specify/workflows/steps, which could redirect
    # the import outside the project root and bypass the install-time
    # symlink guard.  Check symlinks *before* is_dir() since the latter
    # follows symlinks and would stat an external target.
    _current = Path(project_root)
    for _part in (".specify", "workflows", "steps"):
        _current = _current / _part
        if _current.is_symlink():
            return

    if not steps_dir.is_dir():
        return

    for step_dir in steps_dir.iterdir():
        # Check symlinks before is_dir() since the latter follows symlinks
        # and would stat an external target through a symlinked directory.
        if step_dir.is_symlink():
            continue
        if not step_dir.is_dir():
            continue
        step_yml = step_dir / "step.yml"
        init_py = step_dir / "__init__.py"
        if step_yml.is_symlink() or init_py.is_symlink():
            continue
        if not step_yml.is_file() or not init_py.is_file():
            continue

        try:
            import yaml as _yaml

            meta = _yaml.safe_load(step_yml.read_text(encoding="utf-8")) or {}
            step_meta = meta.get("step", {})
            type_key = step_meta.get("type_key", "")
            if not type_key:
                continue

            # Skip if already registered (e.g. built-in or previously loaded)
            if type_key in registry:
                continue

            # Each loaded instance owns a package namespace. A later scan must
            # not replace relative imports used by an already-running workflow.
            safe_key = _re.sub(r"[^A-Za-z0-9_]", "_", type_key)
            module_name = f"_speckit_custom_step_{safe_key}_{_uuid.uuid4().hex}"

            # Removing sys.modules entries alone is insufficient for same-path
            # reloads: Python may reuse a same-size, same-mtime .pyc file.
            # Custom packages are small and source-controlled by the project,
            # so discard only their generated bytecode before importing.
            for cache_dir in step_dir.rglob("__pycache__"):
                if cache_dir.is_symlink():
                    raise OSError(f"Refusing symlinked bytecode cache: {cache_dir}")
                if cache_dir.is_dir():
                    _shutil.rmtree(cache_dir)
            # PYTHONPYCACHEPREFIX can place caches outside the step package.
            for source_file in step_dir.rglob("*.py"):
                cache_file = Path(_importlib_util.cache_from_source(str(source_file)))
                cache_file.unlink(missing_ok=True)
            _importlib.invalidate_caches()

            # Treat the step directory as a proper package so that relative
            # imports inside the step (e.g. ``from .helpers import …``) work.
            spec = _importlib_util.spec_from_file_location(
                module_name,
                init_py,
                submodule_search_locations=[str(step_dir)],
            )
            if spec is None or spec.loader is None:
                continue
            module = _importlib_util.module_from_spec(spec)
            module.__package__ = module_name
            # Register before exec so relative imports resolve correctly.
            _sys.modules[module_name] = module
            registered = False
            try:
                spec.loader.exec_module(module)  # type: ignore[union-attr]

                # Find the StepBase subclass in the module
                from .base import StepBase as _StepBase

                step_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    try:
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, _StepBase)
                            and attr is not _StepBase
                            and getattr(attr, "type_key", "") == type_key
                        ):
                            step_class = attr
                            break
                    except TypeError:
                        continue

                if step_class is None:
                    continue

                step = step_class()
                _weakref.finalize(step, _unload_step_module, module_name)
                registry[type_key] = step
                registered = True
            finally:
                # If the step wasn't successfully registered (failed import,
                # no matching StepBase subclass, or registration error), remove
                # the synthetic module — and any submodules loaded via relative
                # imports (e.g. ``from .helpers import …``) — from sys.modules so
                # a broken/skipped step package leaves no lingering import state
                # behind.
                if not registered:
                    _unload_step_module(module_name)
        except Exception:  # noqa: BLE001
            # Silently skip broken step packages at load time
            continue
