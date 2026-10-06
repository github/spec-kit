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


def _pinned_catalog_version(
    kind: str, component: ComponentRef, lookup, select_release
) -> str | None:
    """Exact catalog release a delegated ``add --version`` must install.

    Workflow and step installs delegate to their ``add`` commands, which select
    and verify the release themselves; this only decides which version to ask
    for. ``None`` installs the advertised release: no pin, an entry that
    advertises no version, or a pin naming the advertised release itself (so
    legacy single-version entries keep their existing install path, which
    ``--version`` would hold to stricter digest requirements). A pin missing
    from the winning entry fails here with the bundle-specific error. If the
    catalog cannot be read, the pin is still forwarded so the command enforces
    it or reports the failure.
    """
    if not component.version:
        return None
    try:
        info = lookup()
        if not info:
            return component.version
        selected, version = _select_pinned_release(
            kind, component, info, select_release
        )
    except BundlerError:
        raise
    except Exception:  # noqa: BLE001 - the delegated command reports catalog errors
        return component.version
    # ``select_release`` returns the entry itself for the advertised release.
    return None if selected is info else version


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

        catalog = PresetCatalog(self._root)
        info = catalog.get_pack_info(component.id)
        if not info:
            raise BundlerError(f"Preset '{component.id}' not found in any catalog.")
        if not info.get("_install_allowed", True):
            raise BundlerError(
                f"Preset '{component.id}' is from a discovery-only catalog; "
                "installation is not allowed."
            )
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
        except Exception as exc:  # noqa: BLE001
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
        except Exception as exc:  # noqa: BLE001
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
        if bundled is not None:
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
            _assert_pinned_version(
                "Workflow", component.id, component.version, definition.version
            )
            from .. import workflow_add

            with _chdir(self._root):
                _delegate_command(
                    "install",
                    f"workflow '{component.id}'",
                    lambda: workflow_add(str(workflow_file), dev=True, from_url=None),
                )
            return

        if not self._allow_network:
            raise BundlerError(
                f"Workflow '{component.id}' installs from a catalog and network "
                "access is disabled. Installing or refreshing this component "
                "requires network access; re-run without --offline."
            )
        from ..workflows.catalog import WorkflowCatalog
        from ..workflows.catalog._versions import select_release

        version = _pinned_catalog_version(
            "Workflow",
            component,
            lambda: WorkflowCatalog(self._root).get_workflow_info(component.id),
            select_release,
        )
        from .. import workflow_add

        with _chdir(self._root):
            _delegate_command(
                "install", f"workflow '{component.id}'",
                lambda: workflow_add(
                    component.id, dev=False, from_url=None, version=version
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
        self._install(component, self._pinned_version(component))

    def _pinned_version(self, component: ComponentRef) -> str | None:
        from ..workflows.catalog import StepCatalog
        from ..workflows.step.catalog._versions import select_release

        return _pinned_catalog_version(
            "Step",
            component,
            lambda: StepCatalog(self._root).get_step_info(component.id),
            lambda info, version: select_release(info, component.id, version),
        )

    def _install(self, component: ComponentRef, version: str | None) -> None:
        from .. import workflow_step_add

        with _chdir(self._root):
            _delegate_command(
                "install", f"step '{component.id}'",
                lambda: workflow_step_add(component.id, version=version),
            )

    def refresh(self, component: ComponentRef) -> None:
        # Preserve an existing step until we've validated we can perform refresh.
        # For already-installed steps, keep a backup and restore it if the
        # remove+reinstall path fails.
        if not (self._allow_network and self.is_installed(component)):
            self.install(component)
            return

        import shutil
        import tempfile

        # Resolve the pin before removing anything: a pinned release missing
        # from the catalog must leave the installed step untouched.
        version = self._pinned_version(component)
        step_dir = self._registry.steps_dir / component.id
        metadata = self._registry.get(component.id)
        backup_dir = Path(tempfile.mkdtemp(prefix="speckit-step-refresh-")) / component.id
        try:
            if step_dir.exists():
                shutil.copytree(step_dir, backup_dir)
            self.remove(component)
            try:
                self._install(component, version)
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
