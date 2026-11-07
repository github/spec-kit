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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import StepBase

# Maps step type_key → StepBase instance.
STEP_REGISTRY: dict[str, StepBase] = {}


def _register_step(step: StepBase) -> None:
    """Register a step type instance in the global registry.

    Raises ``ValueError`` for falsy keys and ``KeyError`` for duplicates.
    """
    key = step.type_key
    if not key:
        raise ValueError("Cannot register step type with an empty type_key.")
    if key in STEP_REGISTRY:
        raise KeyError(f"Step type with key {key!r} is already registered.")
    STEP_REGISTRY[key] = step


def get_step_type(type_key: str) -> StepBase | None:
    """Return the step type for *type_key*, or ``None`` if not registered."""
    return STEP_REGISTRY.get(type_key)


# -- Register built-in step types ----------------------------------------

def _register_builtin_steps() -> None:
    """Register all built-in step types."""
    from .step.command import CommandStep
    from .step.do_while import DoWhileStep
    from .step.fan_in import FanInStep
    from .step.fan_out import FanOutStep
    from .step.gate import GateStep
    from .step.github import GitHubStep
    from .step.workflow import WorkflowStep
    from .step.if_then import IfThenStep
    from .step.init import InitStep
    from .step.prompt import PromptStep
    from .step.shell import ShellStep
    from .step.slot import SlotStep
    from .step.switch import SwitchStep
    from .step.while_loop import WhileStep

    _register_step(CommandStep())
    _register_step(DoWhileStep())
    _register_step(FanInStep())
    _register_step(FanOutStep())
    _register_step(GateStep())
    _register_step(GitHubStep())
    _register_step(WorkflowStep())
    _register_step(IfThenStep())
    _register_step(InitStep())
    _register_step(PromptStep())
    _register_step(ShellStep())
    _register_step(SlotStep())
    _register_step(SwitchStep())
    _register_step(WhileStep())


_register_builtin_steps()

# The step types Spec Kit ships, snapshotted before any community step can be
# loaded. ``load_custom_steps`` adds project-installed ids to the process-global
# ``STEP_REGISTRY`` and refreshes them for each project, so it cannot answer
# "is this bundled with Spec Kit?" in a long-lived process: a step loaded for one
# project would look built-in for the next. Callers that need the immutable set
# (e.g. the bundler's reference checker) must use this instead.
BUILTIN_STEP_TYPES: frozenset[str] = frozenset(STEP_REGISTRY)
_CUSTOM_STEP_MODULES: set[str] = set()


def _import_package(module_name: str, package_dir: Path):
    """Import an installed package under an isolated synthetic module name."""
    import importlib.util
    import sys

    init_py = Path(package_dir) / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        module_name,
        init_py,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create an import specification for '{package_dir}'")
    module = importlib.util.module_from_spec(spec)
    module.__package__ = module_name
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except BaseException:
        _drop_modules({module_name})
        raise
    return module


def _drop_modules(module_names: set[str] | list[str] | tuple[str, ...]) -> None:
    """Remove synthetic modules and their relative-import children."""
    import sys

    for module_name in module_names:
        sys.modules.pop(module_name, None)
        prefix = module_name + "."
        for loaded_name in [name for name in sys.modules if name.startswith(prefix)]:
            sys.modules.pop(loaded_name, None)


def _unload_custom_steps() -> None:
    """Clear custom registrations and synthetic imports from a prior project."""
    for type_key in tuple(STEP_REGISTRY):
        if type_key not in BUILTIN_STEP_TYPES:
            del STEP_REGISTRY[type_key]
    _drop_modules(_CUSTOM_STEP_MODULES)
    _CUSTOM_STEP_MODULES.clear()


def load_custom_steps(project_root: Path) -> list[str]:
    """Load community-installed custom step types into STEP_REGISTRY.

    Scans ``.specify/workflows/steps/`` for installed step packages.
    Each valid package must contain ``step.yml`` (with a ``step.type_key``
    field) and ``__init__.py`` (a ``StepBase`` subclass).

    Returns a list of type_keys that were successfully loaded.
    Silently skips packages that fail to import or validate.
    """
    import hashlib as _hashlib
    import re as _re

    _unload_custom_steps()
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
            return []

    if not steps_dir.is_dir():
        return []

    loaded: list[str] = []
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
            if type_key in STEP_REGISTRY:
                continue

            # Sanitize type_key so the synthetic module name is a valid identifier
            # (e.g. "test-custom" → "_speckit_custom_step_test_custom_<hash>").
            # The 8-char SHA-256 hash of the original type_key makes the name
            # collision-resistant when different type_keys produce the same
            # sanitized form (e.g. "a-b" and "a_b" both sanitize to "a_b" but
            # have different hashes).
            safe_key = _re.sub(r"[^A-Za-z0-9_]", "_", type_key)
            key_hash = _hashlib.sha256(type_key.encode()).hexdigest()[:8]
            module_name = f"_speckit_custom_step_{safe_key}_{key_hash}"

            # Treat the step directory as a proper package so that relative
            # imports inside the step (e.g. ``from .helpers import …``) work.
            module = _import_package(module_name, step_dir)
            registered = False
            try:
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

                _register_step(step_class())
                loaded.append(type_key)
                registered = True
                _CUSTOM_STEP_MODULES.add(module_name)
            finally:
                # If the step wasn't successfully registered (failed import,
                # no matching StepBase subclass, or registration error), remove
                # the synthetic module — and any submodules loaded via relative
                # imports (e.g. ``from .helpers import …``) — from sys.modules so
                # a broken/skipped step package leaves no lingering import state
                # behind.
                if not registered:
                    _drop_modules({module_name})
        except Exception:  # noqa: BLE001, S112
            # Silently skip broken step packages at load time
            continue

    return loaded


def load_workflow_functions(project_root: Path) -> list[str]:
    """Load project-installed workflow expression functions."""
    from .function.loader import load_workflow_functions as loader

    return loader(project_root)
