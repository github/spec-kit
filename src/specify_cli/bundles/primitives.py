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

from . import BundlerError
from .manifest import ComponentRef
from .versioning import same_version

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
    from .versioning import same_version

    if not same_version(actual, pinned):
        raise BundlerError(
            f"{kind} '{component_id}' is pinned to version {pinned} in the bundle "
            f"manifest, but the resolved version is {actual}. Update the bundle's "
            "pinned version or the source before installing."
        )


def _select_pinned_release(
    kind: str, component: ComponentRef, info: dict, select_release
) -> tuple[dict, str | None]:
    """Select the catalog release a bundle pin names.

    Returns the selected release record and the version the archive must
    declare (``None`` when the pin cannot be enforced). Selection stays within
    the winning catalog entry, so a pinned release missing from it is an error
    rather than a silent fall-through to the advertised release or to a
    lower-priority catalog. An entry advertising no version cannot enforce the
    pin, so it is installed as resolved (mirrors ``_assert_pinned_version``).
    """
    _assert_catalog_source(kind, component, info)
    pinned = component.version
    advertised = info.get("version")
    if not pinned or advertised is None or not str(advertised).strip():
        return info, None
    selected = select_release(info, pinned)
    if selected is None:
        raise BundlerError(
            f"{kind} '{component.id}' is pinned to version {pinned} in the bundle "
            f"manifest, but its catalog has no release for that version (it "
            f"advertises {str(advertised).strip()}). Update the bundle's pinned "
            "version or the catalog before installing."
        )
    return selected, selected["version"]


def _assert_catalog_source(kind: str, component: ComponentRef, info: dict) -> None:
    """A source identifies the winning catalog; it cannot select another one."""
    if component.source and component.source != info.get("_catalog_name"):
        raise BundlerError(
            f"{kind} '{component.id}' requests catalog '{component.source}', "
            f"but its highest-priority source is "
            f"'{info.get('_catalog_name', '<unknown>')}'. "
            "A bundle source cannot bypass catalog precedence."
        )
    if not info.get("_install_allowed", True):
        raise BundlerError(
            f"{kind} '{component.id}' is from a discovery-only catalog; "
            "installation is not allowed."
        )


def _selected_catalog_info(kind: str, component: ComponentRef, catalog) -> dict:
    """Resolve an exact workflow/step release within the winning catalog."""
    from .component_catalog import select_catalog_release, winning_catalog_entry

    current = winning_catalog_entry(catalog, component)
    if current is None:
        raise BundlerError(f"{kind} '{component.id}' not found in any catalog.")
    _assert_catalog_source(kind, component, current)
    if component.version is None:
        return current
    selected = select_catalog_release(component, current)
    if selected is None:
        raise BundlerError(
            f"{kind} '{component.id}' has no catalog release for pinned version "
            f"{component.version} in the highest-priority source."
        )
    if selected.get("_catalog_name") != current.get("_catalog_name"):
        raise BundlerError(
            f"{kind} '{component.id}' changed catalog sources during version lookup."
        )
    _assert_catalog_source(kind, component, selected)
    if not selected.get("version") or not same_version(
        selected["version"], component.version
    ):
        raise BundlerError(
            f"{kind} '{component.id}' has no verifiable catalog release for "
            f"pinned version {component.version}."
        )
    return selected


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
    except Exception:  # noqa: BLE001 - unreadable manifest: version unknown
        return None
    return None


def _registry_version(registry, component_id: str) -> str | None:
    """Version a primitive registry recorded for an installed component.

    Returns ``None`` when there is no entry, the registry is unreadable, or the
    entry has no usable version, meaning the installed version is unknown.
    """
    try:
        entry = registry.get(component_id)
    except Exception:  # noqa: BLE001 - unreadable registry: version unknown
        return None
    version = entry.get("version") if isinstance(entry, dict) else None
    return version if isinstance(version, str) and version.strip() else None


class _KindManager(Protocol):
    def is_installed(self, component: ComponentRef) -> bool:
        pass

    def installed_version(self, component: ComponentRef) -> str | None:
        pass

    def install(self, component: ComponentRef) -> None:
        pass

    def refresh(self, component: ComponentRef) -> None:
        pass

    def remove(self, component: ComponentRef) -> None:
        pass


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
        from ..presets import PresetManager

        self._root = project_root
        self._allow_network = allow_network
        self._manager = PresetManager(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._manager.get_pack(component.id) is not None
        except Exception:  # noqa: BLE001
            return False

    def installed_version(self, component: ComponentRef) -> str | None:
        return _registry_version(self._manager.registry, component.id)

    def install(self, component: ComponentRef) -> None:
        self._do_install(component, force=False)

    def refresh(self, component: ComponentRef) -> None:
        self._do_install(component, force=True)

    def _do_install(self, component: ComponentRef, *, force: bool) -> None:
        from .. import get_speckit_version
        from .._assets import _locate_bundled_preset

        speckit_version = get_speckit_version()
        priority = DEFAULT_PRIORITY if component.priority is None else component.priority

        bundled = _locate_bundled_preset(component.id)
        if bundled is not None and component.source is None:
            # Enforce the manifest pin against the bundled asset's own version,
            # mirroring the catalog path below (the bundled path previously
            # skipped the pin entirely).
            _assert_pinned_version(
                "Preset",
                component.id,
                component.version,
                _bundled_manifest_version(bundled / "preset.yml", "preset"),
            )
            self._manager.install_from_directory(
                bundled, speckit_version, priority, **({"force": True} if force else {})
            )
            return

        if not self._allow_network:
            raise BundlerError(
                f"Preset '{component.id}' is not bundled and network access is "
                "disabled. Installing or refreshing this component requires "
                "network access; re-run without --offline."
            )

        from ..presets import PresetCatalog
        from .component_catalog import winning_catalog_entry

        catalog = PresetCatalog(self._root)
        info = winning_catalog_entry(catalog, component)
        if not info:
            raise BundlerError(f"Preset '{component.id}' not found in any catalog.")
        from ..presets._catalog_versions import select_release

        info, expected_version = _select_pinned_release(
            "Preset", component, info, select_release
        )
        zip_path = catalog.download_pack_info(info)
        try:
            self._manager.install_from_zip(
                zip_path,
                speckit_version,
                priority,
                catalog_name=info.get("_catalog_name"),
                **({"force": True} if force else {}),
                **(
                    {"expected_id": component.id, "expected_version": expected_version}
                    if expected_version is not None
                    else {}
                ),
            )
        finally:
            with contextlib.suppress(Exception):
                if zip_path.exists():
                    zip_path.unlink()

    def remove(self, component: ComponentRef) -> None:
        try:
            self._manager.remove(component.id)
        except Exception as exc:
            raise BundlerError(
                f"Failed to remove preset '{component.id}': {exc}"
            ) from exc


class _ExtensionKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ..extensions import ExtensionManager

        self._root = project_root
        self._allow_network = allow_network
        self._manager = ExtensionManager(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._manager.registry.is_installed(component.id)
        except Exception:  # noqa: BLE001
            return False

    def installed_version(self, component: ComponentRef) -> str | None:
        return _registry_version(self._manager.registry, component.id)

    def install(self, component: ComponentRef) -> None:
        self._do_install(component, force=False)

    def refresh(self, component: ComponentRef) -> None:
        self._do_install(component, force=True)

    def _do_install(self, component: ComponentRef, *, force: bool) -> None:
        from .. import get_speckit_version
        from .._assets import _locate_bundled_extension

        speckit_version = get_speckit_version()
        priority = DEFAULT_PRIORITY if component.priority is None else component.priority

        bundled = _locate_bundled_extension(component.id)
        if bundled is not None and component.source is None:
            # Enforce the manifest pin against the bundled asset's own version,
            # mirroring the catalog path below (the bundled path previously
            # skipped the pin entirely).
            _assert_pinned_version(
                "Extension",
                component.id,
                component.version,
                _bundled_manifest_version(bundled / "extension.yml", "extension"),
            )
            manifest = self._manager.install_from_directory(
                bundled, speckit_version, priority=priority, force=force
            )
            self._manager.scaffold_config(manifest.id)
            return

        if not self._allow_network:
            raise BundlerError(
                f"Extension '{component.id}' is not bundled and network access is "
                "disabled. Installing or refreshing this component requires "
                "network access; re-run without --offline."
            )

        from ..extensions import ExtensionCatalog
        from .component_catalog import winning_catalog_entry

        catalog = ExtensionCatalog(self._root)
        info = winning_catalog_entry(catalog, component)
        if not info:
            raise BundlerError(
                f"Extension '{component.id}' not found in any catalog."
            )
        from ..extensions._catalog_versions import select_release

        info, expected_version = _select_pinned_release(
            "Extension", component, info, select_release
        )
        zip_path = catalog.download_extension_info(info)
        try:
            manifest = self._manager.install_from_zip(
                zip_path,
                speckit_version,
                priority=priority,
                force=force,
                catalog_name=info.get("_catalog_name"),
                **(
                    {"expected_id": component.id, "expected_version": expected_version}
                    if expected_version is not None
                    else {}
                ),
            )
            self._manager.scaffold_config(manifest.id)
        finally:
            with contextlib.suppress(Exception):
                if zip_path.exists():
                    zip_path.unlink()

    def remove(self, component: ComponentRef) -> None:
        try:
            self._manager.remove(component.id)
        except Exception as exc:
            raise BundlerError(
                f"Failed to remove extension '{component.id}': {exc}"
            ) from exc


class _WorkflowKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ..workflows.catalog import WorkflowRegistry

        self._root = project_root
        self._allow_network = allow_network
        self._registry = WorkflowRegistry(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._registry.is_installed(component.id)
        except Exception:  # noqa: BLE001
            return False

    def installed_version(self, component: ComponentRef) -> str | None:
        return _registry_version(self._registry, component.id)

    def install(self, component: ComponentRef) -> None:
        from .._assets import _locate_bundled_workflow

        bundled = _locate_bundled_workflow(component.id)
        if bundled is not None and component.source is None:
            workflow_file = bundled / "workflow.yml"
            try:
                from ..workflows.engine import WorkflowDefinition

                definition = WorkflowDefinition.from_yaml(workflow_file)
            except (OSError, ValueError) as exc:
                raise BundlerError(
                    f"Failed to load bundled workflow '{component.id}': {exc}"
                ) from exc
            if definition.id != component.id:
                raise BundlerError(
                    f"Bundled workflow at {workflow_file} declares ID "
                    f"'{definition.id}', expected '{component.id}'."
                )
            if component.version is None or (
                definition.version and same_version(definition.version, component.version)
            ):
                from .. import workflow_add

                with _chdir(self._root):
                    _delegate_command(
                        "install",
                        f"workflow '{component.id}'",
                        lambda: workflow_add(str(workflow_file), dev=True, from_url=None),
                    )
                return
            if not self._allow_network:
                _assert_pinned_version(
                    "Workflow", component.id, component.version, definition.version
                )

        if not self._allow_network:
            raise BundlerError(
                f"Workflow '{component.id}' installs from a catalog and network "
                "access is disabled. Installing or refreshing this component "
                "requires network access; re-run without --offline."
            )
        from ..workflows.catalog import WorkflowCatalog

        catalog = WorkflowCatalog(self._root)
        selected = _selected_catalog_info(
            "Workflow", component, catalog
        )
        from ..workflows.command_add import _install_preselected_workflow

        with _chdir(self._root):
            _delegate_command(
                "install", f"workflow '{component.id}'",
                lambda: _install_preselected_workflow(
                    component.id, version=component.version, selected_info=selected,
                ),
            )

    def refresh(self, component: ComponentRef) -> None:
        # workflow_add is idempotent for already-installed workflows; delegate
        # to the standard install path which handles version refresh correctly.
        self.install(component)

    def remove(self, component: ComponentRef) -> None:
        from .. import workflow_remove

        with _chdir(self._root):
            _delegate_command(
                "remove", f"workflow '{component.id}'",
                lambda: workflow_remove(component.id),
            )


class _StepKindManager:
    def __init__(self, project_root: Path, allow_network: bool) -> None:
        from ..workflows.catalog import StepRegistry

        self._root = project_root
        self._allow_network = allow_network
        self._registry = StepRegistry(project_root)

    def is_installed(self, component: ComponentRef) -> bool:
        try:
            return self._registry.is_installed(component.id)
        except Exception:  # noqa: BLE001
            return False

    def installed_version(self, component: ComponentRef) -> str | None:
        return _registry_version(self._registry, component.id)

    def install(self, component: ComponentRef) -> None:
        if not self._allow_network:
            raise BundlerError(
                f"Step '{component.id}' installs from a catalog and network access "
                "is disabled. Installing or refreshing this component requires "
                "network access; re-run without --offline."
            )
        from ..workflows.catalog import StepCatalog, StepCatalogError
        from ..workflows.step.installer import StepInstallError, validate_step_id

        try:
            validate_step_id(component.id)
        except StepInstallError as exc:
            raise BundlerError(
                f"Invalid step '{component.id}': {exc}"
            ) from exc

        try:
            catalog = StepCatalog(self._root)
            selected = _selected_catalog_info(
                "Step", component, catalog
            )
        except StepCatalogError as exc:
            raise BundlerError(
                f"Failed to resolve step '{component.id}': {exc}"
            ) from exc
        from ..workflows.step.command_add import _install_preselected_step

        with _chdir(self._root):
            try:
                _delegate_command(
                    "install", f"step '{component.id}'",
                    lambda: _install_preselected_step(
                        component.id, version=component.version, selected_info=selected,
                    ),
                )
            except StepInstallError as exc:
                raise BundlerError(
                    f"Failed to install step '{component.id}': {exc}"
                ) from exc

    def refresh(self, component: ComponentRef) -> None:
        # Preserve an existing step until we've validated we can perform refresh.
        # For already-installed steps, keep a backup and restore it if the
        # remove+reinstall path fails.
        if not (self._allow_network and self.is_installed(component)):
            self.install(component)
            return

        import shutil
        import tempfile

        step_dir = self._registry.steps_dir / component.id
        metadata = self._registry.get(component.id)
        backup_dir = Path(tempfile.mkdtemp(prefix="speckit-step-refresh-")) / component.id
        try:
            if step_dir.exists():
                shutil.copytree(step_dir, backup_dir)
            self.remove(component)
            try:
                self.install(component)
            except BundlerError:
                if backup_dir.exists():
                    shutil.copytree(backup_dir, step_dir, dirs_exist_ok=True)
                # Re-read the registry: ``StepRegistry`` snapshots the file once
                # in ``__init__`` (``self.data = self._load()``) and
                # ``is_installed`` only consults that snapshot. ``self.remove()``
                # above has already deleted the entry from disk, but
                # ``self._registry``'s snapshot still contains it -- so the
                # guard was always False here and the restore never ran, in
                # exactly the failure case it was written for. The step package
                # came back but stayed unregistered: ``workflow step list``
                # stopped showing it and ``workflow step add`` then refused with
                # "Step directory already exists".
                from ..workflows.catalog import StepRegistry

                current = StepRegistry(self._root)
                if metadata is not None and not current.is_installed(component.id):
                    # Restore the saved entry verbatim rather than via ``add()``,
                    # which would rewrite the metadata it is meant to roll back:
                    # this registry is freshly constructed *after*
                    # ``self.remove()`` deleted the entry, so ``add()`` sees no
                    # existing record and stamps ``installed_at`` with
                    # ``datetime.now()`` (it also overwrites ``updated_at``
                    # unconditionally). ``workflow_step_remove`` bypasses
                    # ``add()`` for exactly this reason.
                    current.data["steps"][component.id] = metadata
                    current.save()
                raise
        finally:
            shutil.rmtree(backup_dir.parent, ignore_errors=True)

    def remove(self, component: ComponentRef) -> None:
        from .. import workflow_step_remove

        with _chdir(self._root):
            _delegate_command(
                "remove", f"step '{component.id}'",
                lambda: workflow_step_remove(component.id),
            )
