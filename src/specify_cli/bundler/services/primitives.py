"""Bridge from bundler component kinds to existing primitive managers.

The bundler does not own install logic; it routes each component to the
existing Spec Kit primitive machinery so a bundle install behaves exactly as a
sequence of ``specify <primitive> add`` calls would (Principle I: never
reimplement or fake primitive behaviour).

Routing strategy per kind:

* **presets** / **extensions** — wired through their reusable managers
  (``install_from_directory`` / ``install_from_zip``). Bundled assets shipped
  with Spec Kit install fully offline; catalog assets are fetched only when
  network access is permitted.
* **workflows** / **steps** — their install/remove orchestration lives in the
  CLI command layer rather than a reusable service method, so the bundler
  delegates to those existing command callables in-process (with the project
  root as the working directory) instead of duplicating their download and
  validation logic.
"""
from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Protocol

from .. import BundlerError
from ..models.manifest import ComponentRef

DEFAULT_PRIORITY = 10


def _assert_pinned_version(
    kind: str, component_id: str, pinned: str | None, advertised: object
) -> None:
    """Refuse to install when the resolved version differs from the manifest pin.

    Bundle manifests pin component versions for reproducibility; installing
    whatever the resolved source (catalog *or* bundled asset) provides would
    silently violate the pin. When the source advertises no version we cannot
    enforce the pin, so installation proceeds (the source, not the bundler,
    owns that gap).
    """
    if not pinned or advertised is None:
        return
    actual = str(advertised).strip()
    if not actual:
        return
    from ..lib.versioning import parse_version

    try:
        matches = parse_version(actual) == parse_version(pinned)
    except BundlerError:
        matches = actual == str(pinned).strip()
    if not matches:
        raise BundlerError(
            f"{kind} '{component_id}' is pinned to version {pinned} in the bundle "
            f"manifest, but the resolved version is {actual}. Update the bundle's "
            "pinned version or the source before installing."
        )


def _bundled_manifest_version(manifest_path: Path, root_key: str) -> str | None:
    """Best-effort read of a bundled asset's declared version from its manifest.

    Returns ``None`` when the manifest is missing/unreadable/invalid, which
    ``_assert_pinned_version`` treats as "cannot enforce" (proceed) — matching
    the catalog "advertises no version" escape hatch.
    """
    try:
        import yaml

        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            section = data.get(root_key)
            if isinstance(section, dict):
                version = section.get("version")
                # Only a non-empty string is a usable version; anything else
                # (missing / non-string / whitespace) means "cannot enforce".
                if isinstance(version, str) and version.strip():
                    return version
    except Exception:  # noqa: BLE001 - unreadable/invalid manifest: skip pin
        return None
    return None


class _KindManager(Protocol):
    def is_installed(self, component: ComponentRef) -> bool: ...

    def install(self, component: ComponentRef) -> None: ...

    def remove(self, component: ComponentRef) -> None: ...


def primitive_manager(
    kind: str, project_root: Path, *, allow_network: bool = True
) -> _KindManager:
    if kind == "presets":
        return _PresetKindManager(project_root, allow_network)
    if kind == "extensions":
        return _ExtensionKindManager(project_root, allow_network)
    if kind == "workflows":
        return _WorkflowKindManager(project_root, allow_network)
    if kind == "steps":
        return _StepKindManager(project_root, allow_network)
    raise BundlerError(f"Unknown component kind '{kind}'.")


@contextlib.contextmanager
def _chdir(path: Path):
    """Temporarily switch the working directory.

    The delegated workflow/step command callables resolve the project via
    ``Path.cwd()``; this makes that resolution land on *path*.
    """
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _delegate_command(action: str, label: str, call) -> None:
    """Run a delegated CLI command callable, translating its exit into errors."""
    import typer

    try:
        call()
    except typer.Exit as exc:  # raised by the delegated command on failure
        code = getattr(exc, "exit_code", 0) or 0
        if code != 0:
            raise BundlerError(f"Failed to {action} {label}.") from exc
    except SystemExit as exc:  # pragma: no cover - defensive
        if exc.code not in (0, None):
            raise BundlerError(f"Failed to {action} {label}.") from exc


class _PresetKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ...presets import PresetManager

        self._root = project_root
        self._allow_network = allow_network
        self._manager = PresetManager(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._manager.get_pack(component.id) is not None
        except Exception:  # noqa: BLE001
            return False

    def install(self, component: ComponentRef) -> None:
        from ... import get_speckit_version
        from ..._assets import _locate_bundled_preset

        speckit_version = get_speckit_version()
        priority = DEFAULT_PRIORITY if component.priority is None else component.priority

        bundled = _locate_bundled_preset(component.id)
        if bundled is not None:
            # Enforce the manifest pin against the bundled asset's own version,
            # mirroring the catalog path below (the bundled path previously
            # skipped the pin entirely).
            _assert_pinned_version(
                "Preset",
                component.id,
                component.version,
                _bundled_manifest_version(bundled / "preset.yml", "preset"),
            )
            self._manager.install_from_directory(bundled, speckit_version, priority)
            return

        if not self._allow_network:
            raise BundlerError(
                f"Preset '{component.id}' is not bundled and network access is "
                f"disabled; re-run without --offline or install it first with "
                f"'specify preset add {component.id}'."
            )

        from ...presets import PresetCatalog

        catalog = PresetCatalog(self._root)
        info = catalog.get_pack_info(component.id)
        if not info:
            raise BundlerError(f"Preset '{component.id}' not found in any catalog.")
        if not info.get("_install_allowed", True):
            raise BundlerError(
                f"Preset '{component.id}' is from a discovery-only catalog; "
                "installation is not allowed."
            )
        _assert_pinned_version(
            "Preset", component.id, component.version, info.get("version")
        )
        zip_path = catalog.download_pack(component.id)
        try:
            self._manager.install_from_zip(zip_path, speckit_version, priority)
        finally:
            with contextlib.suppress(Exception):
                if zip_path.exists():
                    zip_path.unlink()

    def remove(self, component: ComponentRef) -> None:
        try:
            self._manager.remove(component.id)
        except Exception as exc:  # noqa: BLE001
            raise BundlerError(
                f"Failed to remove preset '{component.id}': {exc}"
            ) from exc


class _ExtensionKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ...extensions import ExtensionManager

        self._root = project_root
        self._allow_network = allow_network
        self._manager = ExtensionManager(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._manager.registry.is_installed(component.id)
        except Exception:  # noqa: BLE001
            return False

    def install(self, component: ComponentRef) -> None:
        from ... import get_speckit_version
        from ..._assets import _locate_bundled_extension

        speckit_version = get_speckit_version()
        priority = DEFAULT_PRIORITY if component.priority is None else component.priority

        bundled = _locate_bundled_extension(component.id)
        if bundled is not None:
            # Enforce the manifest pin against the bundled asset's own version,
            # mirroring the catalog path below (the bundled path previously
            # skipped the pin entirely).
            _assert_pinned_version(
                "Extension",
                component.id,
                component.version,
                _bundled_manifest_version(bundled / "extension.yml", "extension"),
            )
            self._manager.install_from_directory(
                bundled, speckit_version, priority=priority
            )
            return

        if not self._allow_network:
            raise BundlerError(
                f"Extension '{component.id}' is not bundled and network access is "
                f"disabled; re-run without --offline or install it first with "
                f"'specify extension add {component.id}'."
            )

        from ...extensions import ExtensionCatalog

        catalog = ExtensionCatalog(self._root)
        info = catalog.get_extension_info(component.id)
        if not info:
            raise BundlerError(
                f"Extension '{component.id}' not found in any catalog."
            )
        if not info.get("_install_allowed", True):
            raise BundlerError(
                f"Extension '{component.id}' is from a discovery-only catalog; "
                "installation is not allowed."
            )
        _assert_pinned_version(
            "Extension", component.id, component.version, info.get("version")
        )
        zip_path = catalog.download_extension(component.id)
        try:
            self._manager.install_from_zip(
                zip_path, speckit_version, priority=priority
            )
        finally:
            with contextlib.suppress(Exception):
                if zip_path.exists():
                    zip_path.unlink()

    def remove(self, component: ComponentRef) -> None:
        try:
            self._manager.remove(component.id)
        except Exception as exc:  # noqa: BLE001
            raise BundlerError(
                f"Failed to remove extension '{component.id}': {exc}"
            ) from exc


class _WorkflowKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ...workflows.catalog import WorkflowRegistry

        self._root = project_root
        self._allow_network = allow_network
        self._registry = WorkflowRegistry(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._registry.is_installed(component.id)
        except Exception:  # noqa: BLE001
            return False

    def install(self, component: ComponentRef) -> None:
        if not self._allow_network and not self._is_bundled(component.id):
            raise BundlerError(
                f"Workflow '{component.id}' installs from a catalog and network "
                f"access is disabled; re-run without --offline or install it first "
                f"with 'specify workflow add {component.id}'."
            )
        self._assert_pinned_version(component)
        from ... import workflow_add

        with _chdir(self._root):
            _delegate_command(
                "install", f"workflow '{component.id}'",
                lambda: workflow_add(component.id),
            )

    def _assert_pinned_version(self, component: ComponentRef) -> None:
        if not component.version:
            return
        try:
            from ...workflows.catalog import WorkflowCatalog

            info = WorkflowCatalog(self._root).get_workflow_info(component.id)
        except Exception:  # noqa: BLE001 - catalog unreachable: cannot enforce
            return
        if info:
            _assert_pinned_version(
                "Workflow", component.id, component.version, info.get("version")
            )

    @staticmethod
    def _is_bundled(workflow_id: str) -> bool:
        # A workflow that ships with Spec Kit installs fully offline.
        from ..._assets import _locate_bundled_workflow

        return _locate_bundled_workflow(workflow_id) is not None

    def remove(self, component: ComponentRef) -> None:
        from ... import workflow_remove

        with _chdir(self._root):
            _delegate_command(
                "remove", f"workflow '{component.id}'",
                lambda: workflow_remove(component.id),
            )


class _StepKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ...workflows.catalog import StepRegistry

        self._root = project_root
        self._allow_network = allow_network
        self._registry = StepRegistry(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._registry.is_installed(component.id)
        except Exception:  # noqa: BLE001
            return False

    def install(self, component: ComponentRef) -> None:
        if not self._allow_network:
            raise BundlerError(
                f"Step '{component.id}' installs from a catalog and network access "
                f"is disabled; re-run without --offline or install it first with "
                f"'specify workflow step add {component.id}'."
            )
        from ... import workflow_step_add

        with _chdir(self._root):
            _delegate_command(
                "install", f"step '{component.id}'",
                lambda: workflow_step_add(component.id),
            )

    def remove(self, component: ComponentRef) -> None:
        from ... import workflow_step_remove

        with _chdir(self._root):
            _delegate_command(
                "remove", f"step '{component.id}'",
                lambda: workflow_step_remove(component.id),
            )
