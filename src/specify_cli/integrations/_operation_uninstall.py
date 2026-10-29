"""Shared integration uninstall operation used by CLI and project destruction."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, replace
from pathlib import Path

from ..file_helper import FileHelper
from .._utils import same_path_entry
from ..integration_state import (
    default_integration_key,
    installed_integration_keys,
    integration_settings,
    try_read_integration_json,
)
from . import BUILTIN_INTEGRATION_KEYS, get_integration, installer
from ._helpers import _write_integration_json
from .manifest import IntegrationManifest


@dataclass(frozen=True)
class IntegrationUninstallRequest:
    project_directory: Path
    key: str | None = None
    force: bool = False
    require_complete: bool = False
    preserved_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntegrationUninstallResult:
    key: str | None
    name: str
    removed: tuple[Path, ...] = ()
    skipped: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    missing_manifest: bool = False


class IntegrationUninstallError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, object] = {}
        self.retryable = False


def validate_uninstall_ownership(root: Path, key: str) -> dict | None:
    """External cleanup authority comes from the user's existing local binding."""
    if key in BUILTIN_INTEGRATION_KEYS:
        return None
    record = installer.read_records(root).get(key)
    if record is None:
        raise IntegrationUninstallError(
            "unproven_ownership", f"No installed package ownership record for integration '{key}'",
        )
    binding = installer.recovery_metadata(root, key, record)
    if binding is None:
        raise IntegrationUninstallError(
            "unproven_ownership", f"No trusted local cleanup ownership for integration '{key}'",
        )
    return binding


def unregister_integration_artifacts(
    root: Path, key: str, *, require_complete: bool, force: bool = False,
) -> tuple[str, ...]:
    from ..extensions import ExtensionManager
    from ..presets import PresetManager

    warnings: list[str] = []
    for label, manager in (("extension", ExtensionManager), ("preset", PresetManager)):
        try:
            instance = manager(root)
            generic_paths = set()
            if require_complete and key == "generic" and label == "extension":
                for record in instance.registry.list().values():
                    generic_paths.update(record.get("generic_artifact_hashes", {}))
            cleanup_options = {"require_complete": True} if require_complete else {}
            if label == "extension" and force:
                cleanup_options["force"] = True
            instance.unregister_agent_artifacts(key, **cleanup_options)
            if generic_paths:
                from .._file_policy import project_files

                files = project_files(root)
                for relative in generic_paths:
                    try:
                        files.read_bytes(relative)
                    except FileNotFoundError:
                        path = root / relative
                        if not path.exists() and not path.is_symlink():
                            continue
                    raise IntegrationUninstallError(
                        "cleanup_incomplete", f"Generic artifact was preserved: {relative}",
                    )
        except Exception as exc:
            message = f"Could not clean up {label} artifacts for integration '{key}': {exc}"
            if require_complete:
                raise IntegrationUninstallError("cleanup_incomplete", message) from exc
            warnings.append(message)
    return tuple(warnings)


@contextmanager
def _retain_recovery_state(request: IntegrationUninstallRequest, key: str | None):
    """Keep ownership and installation metadata together until strict cleanup completes."""
    if not request.require_complete or key is None:
        yield
        return
    files = FileHelper(request.project_directory)
    originals: dict[str, bytes | None] = {}
    for relative in (
        f".specify/integrations/{key}.manifest.json",
        ".specify/integration.json", ".specify/init-options.json",
    ):
        try:
            originals[relative] = files.read_bytes(relative)
        except FileNotFoundError:
            originals[relative] = None
    try:
        yield
    except Exception:
        from ._file_changes import changing_file

        for relative, original in originals.items():
            with changing_file(request.project_directory / relative, removal=original is None):
                if original is None:
                    try:
                        files.delete(relative)
                    except FileNotFoundError:
                        pass
                else:
                    files.mkdir(Path(relative).parent, parents=True, exist_ok=True)
                    files.write_bytes(relative, original)
        raise


def _uninstall(
    request: IntegrationUninstallRequest, warnings: list[str],
) -> IntegrationUninstallResult:
    from ._helpers import (
        _clear_init_options_for_integration,
        _register_extensions_for_agent,
        _register_presets_for_agent,
        _remove_integration_json,
        _resolve_integration_options,
        _set_default_integration,
    )

    root = request.project_directory
    state, error = try_read_integration_json(root)
    if error:
        raise IntegrationUninstallError("invalid_state", f"Cannot read integration state: {error.detail}")
    state = state or {}
    default = default_integration_key(state)
    installed = installed_integration_keys(state)
    key = request.key or default
    if key is None:
        return IntegrationUninstallResult(None, "")
    if key not in installed:
        raise IntegrationUninstallError("not_installed", f"Integration '{key}' is not installed.")
    integration = get_integration(key)
    manifest_path = root / ".specify/integrations" / f"{key}.manifest.json"
    missing = not manifest_path.exists()
    removed: list[Path] = []
    skipped: list[Path] = []
    manifest = None
    recovery_manifest = None
    if missing:
        if request.require_complete:
            raise IntegrationUninstallError("missing_manifest", f"Missing manifest for integration '{key}'")
    else:
        try:
            manifest = IntegrationManifest.load(key, root)
            if request.require_complete:
                recovery_manifest = IntegrationManifest.load(key, root)
            for preserved in request.preserved_paths:
                for name in manifest.files:
                    if any(
                        same_path_entry(root / ancestor, root / preserved)
                        for ancestor in (Path(name), *Path(name).parents)
                    ):
                        manifest.remove(name)
        except (ValueError, OSError) as exc:
            raise IntegrationUninstallError(
                "unreadable_manifest", f"Integration manifest for '{key}' is unreadable: {manifest_path}: {exc}",
            ) from exc
        if integration is None:
            warnings.append(f"Integration '{key}' not found in registry. Falling back to manifest-based cleanup.")
            removed, skipped = manifest.uninstall(root, force=request.force)
        else:
            native_config = getattr(integration, "events_config_file", None)
            verify_events = request.require_complete and native_config in manifest.files
            if verify_events:
                from ..events import validate_integration_event_cleanup

                try:
                    validate_integration_event_cleanup(integration, root)
                except (OSError, ValueError) as exc:
                    raise IntegrationUninstallError("cleanup_incomplete", str(exc)) from exc
            try:
                removed, skipped = integration.teardown(root, manifest, force=request.force)
            except SystemExit as exc:
                raise IntegrationUninstallError(
                    "uninstall_failed", f"Integration '{key}' teardown exited before cleanup completed (code {exc.code}).",
                ) from exc

    if (
        integration is not None and request.require_complete and recovery_manifest is not None
        and getattr(integration, "events_config_file", None) in recovery_manifest.files
    ):
        from ..events import validate_integration_event_cleanup

        try:
            validate_integration_event_cleanup(integration, root, require_clean=True)
        except (OSError, ValueError) as exc:
            raise IntegrationUninstallError("cleanup_incomplete", str(exc)) from exc
    warnings.extend(unregister_integration_artifacts(
        root, key, require_complete=request.require_complete, force=request.force,
    ))
    if request.require_complete and skipped:
        raise IntegrationUninstallError(
            "cleanup_incomplete",
            f"Integration '{key}' preserved files that require attention: "
            + ", ".join(str(path) for path in skipped),
        )
    if request.require_complete and (root / ".specify/events.py").exists():
        others = [installed_key for installed_key in installed if installed_key != key]
        if not others:
            raise IntegrationUninstallError(
                "cleanup_incomplete", "The event lifecycle preserved .specify/events.py; resolve it before destroy.",
            )

    remaining = [installed_key for installed_key in installed if installed_key != key]
    new_default = default if default != key else (remaining[0] if remaining else None)
    if remaining:
        fallback = get_integration(new_default) if new_default else None
        if default == key and fallback is not None:
            raw, parsed = _resolve_integration_options(fallback, state, new_default, None)
            _set_default_integration(
                root, state, new_default, fallback, remaining, raw_options=raw, parsed_options=parsed,
            )
            _register_extensions_for_agent(
                root, new_default, continuing="The fallback integration was selected; check extension registration.",
            )
            _register_presets_for_agent(
                root, new_default, continuing="The fallback integration was selected; check preset registration.",
            )
        else:
            _write_integration_json(root, new_default, remaining, integration_settings(state))
    else:
        _remove_integration_json(root)
    if default == key:
        _clear_init_options_for_integration(root, key)
    name = (integration.config or {}).get("name", key) if integration else key
    return IntegrationUninstallResult(key, name, tuple(removed), tuple(skipped), missing_manifest=missing)


def _uninstall_with_lifecycle(request: IntegrationUninstallRequest) -> IntegrationUninstallResult:
    """Run the established teardown, recovery, package, and metadata lifecycle."""
    from ._lifecycle import _transaction

    root = request.project_directory
    if not root.is_absolute():
        raise IntegrationUninstallError("invalid_project_directory", "project_directory must be absolute")
    from .._file_policy import project_files

    project_files(root)
    if not (root / ".specify").is_dir():
        raise IntegrationUninstallError("not_a_spec_kit_project", "Not a Spec Kit project: no .specify directory")
    records = installer.read_records(root)
    state, error = try_read_integration_json(root)
    if error:
        raise IntegrationUninstallError("invalid_state", f"Cannot read integration state: {error.detail}")
    key = request.key or default_integration_key(state or {})
    warnings: list[str] = []
    token = None
    binding = validate_uninstall_ownership(root, key) if request.require_complete and key else None
    if key in records and not request.require_complete:
        binding = installer.recovery_metadata(root, key, records[key])
    loaded = False
    try:
        try:
            installer.load_installed_integrations(root)
        except installer.IntegrationInstallError:
            if not request.force or key not in records:
                raise
            token = installer.recovery_exclusion.set((root.resolve(), key))
            installer.load_installed_integrations(root)
            binding = installer.recovery_metadata(root, key, records[key])
            warnings.append(
                f"Recovering integration '{key}' from validated ownership metadata "
                "without loading its failed implementation.",
            )
        loaded = True
        transaction = _transaction(root, key, state, records) if records else nullcontext()
        with transaction:
            if token is not None:
                path = root / ".specify/integrations" / f"{key}.manifest.json"
                if path.exists():
                    manifest = IntegrationManifest.load(key, root)
                    if binding is None:
                        manifest = IntegrationManifest(key, root, version=manifest.version)
                        warnings.append("No local recovery ownership record; preserving old generated files.")
                    else:
                        preserved = []
                        for name in manifest.files:
                            mode = binding.get("ownership_modes", {}).get(name, "shared")
                            manifest.set_ownership(name, mode)
                            if mode != "whole":
                                preserved.append(name)
                        if preserved:
                            warnings.append(
                                "Preserving shared, partial, or unproven file ownership: "
                                + ", ".join(preserved) + "; manual event cleanup may be needed.",
                            )
                    manifest.save()
            elif binding is not None and (root / ".specify/integrations" / f"{key}.manifest.json").exists():
                # Project metadata cannot promote a locally partial/shared claim.
                manifest = IntegrationManifest.load(key, root)
                for name in manifest.files:
                    mode = binding.get("ownership_modes", {}).get(name, "shared")
                    if mode != manifest.ownership_modes[name]:
                        manifest.set_ownership(name, mode)
                manifest.save()
            with _retain_recovery_state(request, key):
                result = _uninstall(request, warnings)
                new_state, error = try_read_integration_json(root)
                if error:
                    raise IntegrationUninstallError("invalid_state", f"Cannot read integration state: {error.detail}")
                remaining = installed_integration_keys(new_state or {})
                for removed_key in records.keys() - set(remaining):
                    if removed_key != key:
                        warnings.extend(unregister_integration_artifacts(
                            root, removed_key, require_complete=request.require_complete, force=request.force,
                        ))
                    installer.remove_package(root, removed_key)
        return replace(result, warnings=tuple(warnings))
    except IntegrationUninstallError:
        raise
    except Exception as exc:
        raise IntegrationUninstallError("uninstall_failed", f"Integration uninstall failed: {exc}") from exc
    finally:
        try:
            if loaded:
                installer.load_installed_integrations(root)
        finally:
            if token is not None:
                installer.recovery_exclusion.reset(token)


@installer.registry_synchronized
def uninstall_integration(request: IntegrationUninstallRequest) -> IntegrationUninstallResult:
    """Normalize preparation, execution, and recovery failures at one boundary."""
    try:
        if not request.project_directory.is_absolute():
            raise IntegrationUninstallError("invalid_project_directory", "project_directory must be absolute")
        return _uninstall_with_lifecycle(replace(
            request, project_directory=request.project_directory.resolve(strict=True),
        ))
    except IntegrationUninstallError:
        raise
    except Exception as exc:
        raise IntegrationUninstallError("uninstall_failed", f"Integration uninstall failed: {exc}") from exc
