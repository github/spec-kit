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
    from .steps.command import CommandStep
    from .steps.do_while import DoWhileStep
    from .steps.fan_in import FanInStep
    from .steps.fan_out import FanOutStep
    from .steps.gate import GateStep
    from .steps.if_then import IfThenStep
    from .steps.prompt import PromptStep
    from .steps.shell import ShellStep
    from .steps.switch import SwitchStep
    from .steps.while_loop import WhileStep

    _register_step(CommandStep())
    _register_step(DoWhileStep())
    _register_step(FanInStep())
    _register_step(FanOutStep())
    _register_step(GateStep())
    _register_step(IfThenStep())
    _register_step(PromptStep())
    _register_step(ShellStep())
    _register_step(SwitchStep())
    _register_step(WhileStep())


_register_builtin_steps()


def load_custom_steps(project_root: Path) -> list[str]:
    """Load community-installed custom step types into STEP_REGISTRY.

    Scans ``.specify/workflows/steps/`` for installed step packages.
    Each valid package must contain ``step.yml`` (with a ``step.type_key``
    field) and ``__init__.py`` (a ``StepBase`` subclass).

    Returns a list of type_keys that were successfully loaded.
    Silently skips packages that fail to import or validate.
    """
    import hashlib as _hashlib
    import importlib.util as _importlib_util
    import re as _re
    import sys as _sys

    steps_dir = Path(project_root) / ".specify" / "workflows" / "steps"
    if not steps_dir.is_dir():
        return []

    loaded: list[str] = []
    for step_dir in steps_dir.iterdir():
        if not step_dir.is_dir():
            continue
        step_yml = step_dir / "step.yml"
        init_py = step_dir / "__init__.py"
        if not step_yml.exists() or not init_py.exists():
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
                try:
                    spec.loader.exec_module(module)  # type: ignore[union-attr]
                except Exception:
                    raise

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
            finally:
                # If the step wasn't successfully registered (failed import,
                # no matching StepBase subclass, or registration error), remove
                # the synthetic module from sys.modules so a broken/skipped
                # step package leaves no lingering import state behind.
                if not registered:
                    _sys.modules.pop(module_name, None)
        except Exception:  # noqa: BLE001
            # Silently skip broken step packages at load time
            continue

    return loaded
