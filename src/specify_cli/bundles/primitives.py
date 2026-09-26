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
from typing import Callable, Protocol

from . import BundlerError
from .manifest import ComponentRef

DEFAULT_PRIORITY = 10


def _pinned_release_matches(pinned: str | None, advertised: object) -> bool:
    """Return whether a manifest pin is satisfied by an advertised version.

    Mirrors the normalization of :func:`_assert_pinned_version`: a missing
    pin, or a source that advertises no version, cannot be checked, so both
    count as matching.
    """
    if not pinned or advertised is None:
        return True
    actual = str(advertised).strip()
    if not actual:
        return True
    from .versioning import parse_version

    try:
        return parse_version(actual) == parse_version(pinned)
    except BundlerError:
        return actual == str(pinned).strip()


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
    if _pinned_release_matches(pinned, advertised):
        return
    actual = str(advertised).strip() if advertised is not None else ""
    raise BundlerError(
        f"{kind} '{component_id}' is pinned to version {pinned} in the bundle "
        f"manifest, but the resolved version is {actual}. Update the bundle's "
        "pinned version or the source before installing."
    )


def _replace_version_token(segment: str, token: str, prefix: str, pinned: str) -> str | None:
    """Substitute *token* with *pinned* when it appears as a bounded token.

    Returns the rewritten path segment, or ``None`` when no bounded
    occurrence exists. A token is bounded when it is not embedded in a
    longer dotted/dashed run: a preceding ``.`` is accepted only when it is
    not itself preceded by a digit, and a following ``.`` only when it is
    not followed by one -- so an advertised ``0.5.1`` never matches inside
    ``1.0.5.1``, ``0.5.10`` or ``10.5.1``.
    """
    start = 0
    while True:
        pos = segment.find(token, start)
        if pos < 0:
            return None
        before = segment[pos - 1] if pos > 0 else ""
        end = pos + len(token)
        after = segment[end] if end < len(segment) else ""
        before_ok = (
            before == ""
            or before in "-_/"
            or (before == "." and (pos < 2 or not segment[pos - 2].isdigit()))
        )
        after_ok = (
            after == ""
            or after in "-_/"
            or (
                after == "."
                and (end + 1 >= len(segment) or not segment[end + 1].isdigit())
            )
        )
        if before_ok and after_ok:
            return segment[:pos] + prefix + pinned + segment[end:]
        start = pos + 1


def _pinned_release_url(
    download_url: object, advertised: object, pinned: str | None
) -> str | None:
    """Derive the pinned release's URL from the advertised release's URL.

    Catalog entries advertise a single (version, download_url) pair, so when
    a catalog moves to a newer release a bundle's pinned release is no longer
    advertised -- although its artifact usually remains reachable at the same
    location with the version token substituted (e.g. a GitHub release
    download URL pinned to a tag). Returns such a derived URL, or ``None``
    when the advertised version token does not appear as a distinct token in
    the URL path and no derivation is possible.

    Only the URL path is rewritten (query strings are left untouched), so
    the derivation stays conservative: the same host, scheme, and any
    authentication the advertised URL carries are preserved.
    """
    if not isinstance(download_url, str) or not download_url:
        return None
    if not pinned or advertised is None:
        return None
    advertised = str(advertised).strip()
    pinned = str(pinned).strip()
    if not advertised or not pinned:
        return None
    if advertised == pinned:
        return None

    from urllib.parse import urlunparse, urlparse

    try:
        parts = urlparse(download_url)
    except ValueError:
        return None
    if not parts.path:
        return None

    if advertised[:1] in ("v", "V"):
        # The catalog spells the version v/V-prefixed; preserve that tag
        # prefix form (the pin is bare semver, so the prefix is never its own
        # version character).
        candidates: list[tuple[str, str]] = [(advertised, advertised[:1])]
    else:
        candidates = [
            (f"V{advertised}", "V"),
            (f"v{advertised}", "v"),
            (advertised, ""),
        ]

    segments = parts.path.split("/")
    changed = False
    for index, segment in enumerate(segments):
        for token, prefix in candidates:
            replaced = _replace_version_token(segment, token, prefix, pinned)
            if replaced is not None:
                segments[index] = replaced
                changed = True
                break
    if not changed:
        return None
    return urlunparse(parts._replace(path="/".join(segments)))


def _download_catalog_component(
    download_by_id: Callable[..., Path],
    download_by_url: Callable[..., Path],
    kind: str,
    component: ComponentRef,
    info: dict,
    *,
    error_types: tuple[type[Exception], ...],
) -> Path:
    """Download a catalog component, fetching the pinned release on demand.

    *download_by_id* is the catalog's standard ID-based download;
    *download_by_url* is its explicit-URL counterpart. When the bundle's pin
    differs from the version the catalog currently advertises, the pinned
    release's URL is derived from the catalog's own ``download_url`` (same
    host, re-validated as HTTPS by the catalog's download path) and
    retrieved without the catalog's SHA-256, which only covers the
    advertised release. When no derivation is possible, or the pinned
    retrieval fails, the error names the pin and the advertised version so
    the failure reports the pin mismatch rather than a bare network error.
    """
    pinned = component.version
    if pinned and not _pinned_release_matches(pinned, info.get("version")):
        advertised = str(info.get("version")).strip()
        derived = _pinned_release_url(
            info.get("download_url"), info.get("version"), pinned
        )
        if derived is None:
            raise BundlerError(
                f"{kind} '{component.id}' is pinned to version {pinned} in the "
                f"bundle manifest, but the catalog now advertises {advertised} "
                "and its download URL does not identify that version, so the "
                "pinned release cannot be located. Update the bundle's pinned "
                "version to match the catalog, or restore the pinned release, "
                "before installing."
            )
        try:
            return download_by_url(derived, component.id, pinned)
        except error_types as exc:
            raise BundlerError(
                f"{kind} '{component.id}' is pinned to version {pinned} in the "
                f"bundle manifest, but the catalog now advertises {advertised}. "
                f"Retrieving the pinned release from {derived} failed: {exc} "
                "Update the bundle's pinned version or the catalog before "
                "installing."
            ) from exc
    return download_by_id(component.id)


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
    def is_installed(self, component: ComponentRef) -> bool:
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

        from ..presets import PresetCatalog, PresetError

        catalog = PresetCatalog(self._root)
        info = catalog.get_pack_info(component.id)
        if not info:
            raise BundlerError(f"Preset '{component.id}' not found in any catalog.")
        if not info.get("_install_allowed", True):
            raise BundlerError(
                f"Preset '{component.id}' is from a discovery-only catalog; "
                "installation is not allowed."
            )
        zip_path = _download_catalog_component(
            catalog.download_pack,
            catalog.download_pack_url,
            "Preset",
            component,
            info,
            error_types=(PresetError,),
        )
        try:
            self._manager.install_from_zip(
                zip_path,
                speckit_version,
                priority,
                catalog_name=info.get("_catalog_name"),
                **({"force": True} if force else {}),
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

        from ..extensions import ExtensionCatalog, ExtensionError

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
        zip_path = _download_catalog_component(
            catalog.download_extension,
            catalog.download_extension_url,
            "Extension",
            component,
            info,
            error_types=(ExtensionError,),
        )
        try:
            manifest = self._manager.install_from_zip(
                zip_path,
                speckit_version,
                priority=priority,
                force=force,
                catalog_name=info.get("_catalog_name"),
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
        self._assert_pinned_version(component)
        from .. import workflow_add

        with _chdir(self._root):
            _delegate_command(
                "install", f"workflow '{component.id}'",
                lambda: workflow_add(component.id, dev=False, from_url=None),
            )

    def refresh(self, component: ComponentRef) -> None:
        # workflow_add is idempotent for already-installed workflows; delegate
        # to the standard install path which handles version refresh correctly.
        self.install(component)

    def _assert_pinned_version(self, component: ComponentRef) -> None:
        if not component.version:
            return
        try:
            from ..workflows.catalog import WorkflowCatalog

            info = WorkflowCatalog(self._root).get_workflow_info(component.id)
        except Exception:  # noqa: BLE001 - catalog unreachable: cannot enforce
            return
        if info:
            _assert_pinned_version(
                "Workflow", component.id, component.version, info.get("version")
            )

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

    def install(self, component: ComponentRef) -> None:
        if not self._allow_network:
            raise BundlerError(
                f"Step '{component.id}' installs from a catalog and network access "
                "is disabled. Installing or refreshing this component requires "
                "network access; re-run without --offline."
            )
        from .. import workflow_step_add

        with _chdir(self._root):
            _delegate_command(
                "install", f"step '{component.id}'",
                lambda: workflow_step_add(component.id),
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
