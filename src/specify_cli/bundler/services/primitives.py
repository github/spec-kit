"""Bridge from bundler component kinds to existing primitive managers.

The bundler does not own install logic; it routes each component to the
existing Spec Kit primitive machinery. This module centralises that routing so
:class:`DefaultPrimitiveInstaller` stays declarative.

Presets are fully wired to :class:`~specify_cli.presets.PresetManager`. Other
kinds are routed through their managers where a programmatic API exists; where
only a CLI surface exists today, the wrapper raises an actionable error rather
than silently doing nothing (Principle I: never fake primitive behaviour).
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .. import BundlerError
from ..models.manifest import ComponentRef


class _KindManager(Protocol):
    def is_installed(self, component: ComponentRef) -> bool: ...

    def install(self, component: ComponentRef) -> None: ...

    def remove(self, component: ComponentRef) -> None: ...


def primitive_manager(kind: str, project_root: Path) -> _KindManager:
    if kind == "presets":
        return _PresetKindManager(project_root)
    if kind in ("extensions", "steps", "workflows"):
        return _UnsupportedKindManager(kind)
    raise BundlerError(f"Unknown component kind '{kind}'.")


class _PresetKindManager:
    def __init__(self, project_root: Path) -> None:
        from ...presets import PresetManager

        self._manager = PresetManager(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._manager.get_pack(component.id) is not None
        except Exception:  # noqa: BLE001
            return False

    def install(self, component: ComponentRef) -> None:
        raise BundlerError(
            f"Preset '{component.id}' cannot be auto-installed in-process yet; "
            f"install it with 'specify preset add {component.id}'."
        )

    def remove(self, component: ComponentRef) -> None:
        try:
            self._manager.remove(component.id)
        except Exception as exc:  # noqa: BLE001
            raise BundlerError(
                f"Failed to remove preset '{component.id}': {exc}"
            ) from exc


class _UnsupportedKindManager:
    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._singular = kind[:-1]

    def is_installed(self, component: ComponentRef) -> bool:
        return False

    def install(self, component: ComponentRef) -> None:
        raise BundlerError(
            f"{self._singular} '{component.id}' cannot be auto-installed in-process "
            f"yet; install it with 'specify {self._singular} add {component.id}'."
        )

    def remove(self, component: ComponentRef) -> None:
        raise BundlerError(
            f"{self._singular} '{component.id}' cannot be auto-removed in-process "
            f"yet; remove it with 'specify {self._singular} remove {component.id}'."
        )
