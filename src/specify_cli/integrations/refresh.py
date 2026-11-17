"""Refresh installed integration outputs after a committed extension addition."""

from __future__ import annotations

import hashlib
import os
import warnings
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from .. import load_init_options
from ..file_helper import FileHelper
from ..integration_runtime import (
    file_write_validator,
    invoke_prefix_for_integration,
    invoke_separator_for_integration,
    parse_integration_options,
    registration_options,
    resolve_integration_options,
)
from ..integration_state import (
    default_integration_key,
    installed_integration_keys,
    integration_setting,
    try_read_integration_json,
)
from ._file_changes import file_change_observer
from .manifest import IntegrationManifest

_Manifest = TypeVar("_Manifest", bound=IntegrationManifest)


@dataclass
class RefreshResult:
    completed: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    unattempted: list[str] = field(default_factory=list)
    shared_ready: bool = False

    @property
    def success(self) -> bool:
        return self.shared_ready and bool(self.completed) and not self.failed and not self.unattempted


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _PreserveOutputs:
    """Preserve uncertain existing bytes until final composition proves equality."""

    def __init__(self, root: Path):
        self.root = root
        self.owners: dict[Path, set[str]] = {}
        self.current: dict[Path, str] = {}
        self.pending: dict[Path, bytes] = {}
        self.writing: set[Path] = set()
        self.hashes: dict[str, str] = {}
        self.modes: dict[str, str] = {}
        self.recovered: set[str] = set()
        self.home_output: Path | None = None
        self.key = ""
        self.merged_paths: set[str] = set()
        self.mergeable: set[Path] = set()
        self.approved: set[Path] = set()

    def _label(self, path: Path) -> str:
        if ".." in path.parts:
            raise ValueError(f"Noncanonical output path: {path}")
        if path.is_relative_to(self.root):
            anchor = self.root
            relative = path.relative_to(anchor).as_posix()
        elif self.home_output is not None and path.is_relative_to(self.home_output):
            anchor = Path.home().absolute()
            relative = "~/" + path.relative_to(anchor).as_posix()
        else:
            raise ValueError(f"Output outside the configured project/home destination: {path}")
        parent = path
        while parent != anchor:
            if parent.is_symlink():
                produced_link = (
                    parent == path
                    and (self.key in self.owners.get(path, set()) or path in self.writing)
                    and path.resolve().is_relative_to(self.root / ".specify/extensions")
                )
                if not produced_link:
                    raise ValueError(f"Unsafe symlinked output: {relative}")
            parent = parent.parent
        return relative

    def _metadata(self, path: Path) -> bool:
        return path.is_relative_to(self.root / ".specify/extensions") or path.is_relative_to(
            self.root / ".specify/presets"
        ) or (
            path.is_relative_to(self.root / ".specify/integrations")
            and path.name.endswith(".manifest.json")
        )

    def _managed(self, path: Path, relative: str) -> bool:
        expected = self.current.get(path) or self.hashes.get(relative)
        return (
            path.is_file() and expected is not None
            and (relative not in self.recovered or path in self.current)
            and _digest(path) == expected
        )

    def validate(self, path: Path, content: bytes) -> bool:
        path = path.absolute()
        relative = self._label(path)
        if self._metadata(path):
            return True
        if path.name in {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}:
            raise ValueError(f"User-owned context file must not be regenerated: {relative}")
        merged = relative in self.merged_paths or self.modes.get(relative) == "partial"
        if (
            path in self.owners and self.key not in self.owners[path]
            and not (merged and path in self.mergeable)
            and (not path.is_file() or path.read_bytes() != content)
        ):
            raise ValueError(f"Incompatible shared destination: {relative}")
        if merged:
            return True
        if path.exists() and (path in self.pending or not self._managed(path, relative)):
            self.pending[path] = content
            return False
        self.approved.add(path)
        return True

    def observe(self, path: Path, before: bool, removal: bool) -> None:
        path = path.absolute()
        relative = self._label(path)
        if self._metadata(path):
            return
        if not before:
            if path in self.writing and path.is_file():
                self.current[path] = _digest(path)
                self.owners.setdefault(path, set()).add(self.key)
            self.writing.discard(path)
            return
        if path in self.owners and self.key not in self.owners[path]:
            if removal:
                raise ValueError(f"Cannot remove shared output {relative} needed by a completed integration")
            merged = relative in self.merged_paths or self.modes.get(relative) == "partial"
            if path not in self.approved and not (merged and path in self.mergeable):
                raise ValueError(f"Cannot safely overwrite shared output: {relative}")
        if path.is_dir() and not removal:
            return
        if path.exists() and (
            relative not in self.merged_paths and self.modes.get(relative) != "partial"
            and not self._managed(path, relative)
        ):
            raise ValueError(f"Preserved customized or untracked output: {relative}; back up and reconcile it before retry")
        if relative in self.merged_paths or self.modes.get(relative) == "partial":
            self.mergeable.add(path)
        self.writing.add(path)

    def begin(
        self, key: str, manifest: IntegrationManifest, merged_paths: Iterable[str] = (),
        contributions: IntegrationManifest | None = None, home_output: Path | None = None,
    ) -> None:
        self.key = key
        self.current = {}
        self.pending = {}
        self.writing = set()
        self.approved = set()
        self.merged_paths = set(merged_paths)
        self.hashes = manifest.files
        self.modes = manifest.ownership_modes
        self.recovered = manifest.recovered_files
        self.home_output = home_output
        if contributions is not None:
            self.hashes.update(contributions.files)
            self.modes.update(contributions.ownership_modes)
            self.recovered.update(contributions.recovered_files)

    def finish(self) -> None:
        for path, content in self.pending.items():
            if not path.is_file() or path.read_bytes() != content:
                raise ValueError(
                    f"Preserved customized or untracked output: {self._label(path)}; "
                    "back up and reconcile it, then retry"
                )
            self.current[path] = _digest(path)
            self.owners.setdefault(path, set()).add(self.key)


class _ContributionManifest(IntegrationManifest):
    @property
    def manifest_path(self) -> Path:
        return self.project_root / ".specify/integrations/.contributions" / f"{self.key}.manifest.json"


def _load_manifest(
    manifest_type: type[_Manifest], key: str, root: Path, *, optional: bool = False,
) -> _Manifest:
    manifest = manifest_type(key, root)
    with FileHelper(root) as files:
        try:
            files.read_bytes(manifest.manifest_path.relative_to(root))
        except FileNotFoundError:
            if optional:
                return manifest
            raise
    return manifest_type.load(key, root)


def _script(options: dict[str, Any], state: dict[str, Any], key: str) -> str:
    value = integration_setting(state, key).get("script", options.get("script", "ps" if os.name == "nt" else "sh"))
    if not isinstance(value, str) or value not in {"sh", "ps", "py"}:
        raise ValueError(f"Invalid saved script setting for '{key}': {value!r}")
    return value


def _validate_contribution_sources(root: Path) -> None:
    from ..extensions import ExtensionManager, ExtensionManifest
    from ..presets import PresetManager, PresetManifest

    for kind, manager, manifest_type, directory, filename in (
        ("extension", ExtensionManager(root), ExtensionManifest, "extensions", "extension.yml"),
        ("preset", PresetManager(root), PresetManifest, "presets", "preset.yml"),
    ):
        for key, metadata in manager.registry.list().items():
            if not metadata.get("enabled", True):
                continue
            source = root / ".specify" / directory / key
            manifest = manifest_type(source / filename)
            entries = manifest.commands if kind == "extension" else [
                entry for entry in manifest.templates if entry.get("type") == "command"
            ]
            for entry in entries:
                path = source / entry["file"]
                if not path.is_file() or not path.resolve().is_relative_to(source.resolve()):
                    raise ValueError(f"Missing or unsafe {kind} command source: {path}")


def refresh_installed_integrations(
    project_root: Path, *, development_extension: str | None = None,
) -> RefreshResult:
    """Regenerate locally, preserving the default and retaining partial work."""
    root = project_root.resolve()
    result = RefreshResult()
    state, error = try_read_integration_json(root)
    if error is not None or not state:
        result.failed["integration state"] = f"Cannot read recorded integrations: {error or 'missing state'}"
        return result
    keys = installed_integration_keys(state)
    result.unattempted = list(keys)
    default = default_integration_key(state)
    if not keys or not default or default not in keys:
        result.failed["integration state"] = "No recorded installed integration/default; run specify init or repair integration.json"
        return result
    try:
        from .installer import project_integrations

        with project_integrations(root):
            _refresh_loaded(root, state, keys, default, result, development_extension)
    except Exception as exc:  # noqa: BLE001 - report adapter failures without rolling back installation
        # This is the operation's failure boundary; adapters receive structured
        # failure rather than a success-shaped fallback or a process exit.
        result.failed["installed adapters"] = str(exc)
    return result


def _refresh_loaded(
    root: Path, state: dict[str, Any], keys: list[str], default: str,
    result: RefreshResult, development_extension: str | None,
) -> None:
    from ..events import resolve_events
    from ..extensions import ExtensionManager
    from ..presets import PresetManager
    from ..shared_infra import refresh_shared_infrastructure
    from . import get_integration

    options = load_init_options(root)
    for name in ("ai", "integration"):
        if name in options and (not isinstance(options[name], str) or not options[name]):
            result.failed["project options"] = f"Invalid saved default in init-options.json: {name}"
            return
    guard = _PreserveOutputs(root)
    default_adapter = get_integration(default)
    if default_adapter is None:
        result.failed[default] = "Installed adapter is missing, damaged, or untrusted; restore its reviewed installation"
        return
    _, default_parsed = resolve_integration_options(
        default_adapter, state, default, None, parse_options=parse_integration_options,
    )
    shared = _load_manifest(IntegrationManifest, "speckit", root, optional=True)
    guard.begin("shared", shared)
    token = file_change_observer.set(guard.observe)
    write_token = file_write_validator.set(guard.validate)
    try:
        try:
            installed = refresh_shared_infrastructure(
                root, _script(options, state, default),
                invoke_separator=invoke_separator_for_integration(
                    default_adapter, state, default, default_parsed, root,
                ),
                invoke_prefix=invoke_prefix_for_integration(default_adapter, default, default_parsed, root),
            )
            if not installed:
                raise ValueError("Shared infrastructure sources are unavailable")
            guard.finish()
            result.shared_ready = True
        except Exception as exc:  # noqa: BLE001 - retain and report partial shared refreshes
            result.failed["shared infrastructure"] = str(exc)
            try:
                retained = _load_manifest(IntegrationManifest, "speckit", root, optional=True)
                for path in guard.pending:
                    if path.is_file():
                        retained.record_existing(path.relative_to(root), recovered=True)
                retained.save()
            except (OSError, ValueError) as save_error:
                result.failed["shared infrastructure"] += f"; ownership update failed: {save_error}"
            return
        for key in keys:
            result.unattempted.remove(key)
            refreshed = None
            try:
                integration = get_integration(key)
                if integration is None:
                    raise ValueError("Installed adapter is missing, damaged, or untrusted; restore its reviewed installation")
                prior = _load_manifest(IntegrationManifest, key, root)
                contributions = _load_manifest(_ContributionManifest, key, root, optional=True)
                home_output = None
                directory = (integration.registrar_config or {}).get("dir")
                if isinstance(directory, str) and directory.startswith("~/"):
                    home_output = Path(directory).expanduser().absolute()
                guard.begin(
                    key, prior, integration.stale_cleanup_exclusions(),
                    contributions=contributions, home_output=home_output,
                )
                raw, parsed = resolve_integration_options(
                    integration, state, key, None, parse_options=parse_integration_options,
                )
                script = _script(options, state, key)
                scoped = dict(options, ai=key, integration=key, script=script)
                with registration_options(root, scoped):
                    scoped["ai_skills"] = integration.is_skills_mode(parsed, root)
                with registration_options(root, scoped), warnings.catch_warnings():
                    _validate_contribution_sources(root)
                    integration.preflight_setup(root, parsed, script_type=script)
                    refreshed = IntegrationManifest(key, root, prior.version)
                    events = resolve_events(key, integration.config, root, parsed)
                    core_outputs = integration.setup(
                        root, refreshed, parsed_options=parsed,
                        script_type=script, raw_options=raw, events=events, force=False,
                    )
                    if integration.list_command_templates() and not core_outputs:
                        raise ValueError("No core invocation artifacts were generated")
                    for output in core_outputs or []:
                        if not output.is_file():
                            raise ValueError(f"Missing generated core output: {output}")
                    core_paths = set(refreshed.files)
                    warnings.simplefilter("error")
                    ExtensionManager(root).register_enabled_extensions_for_agent(
                        key, force=True, strict=True, development_extension=development_extension,
                    )
                    PresetManager(root).register_enabled_presets_for_agent(key, strict=True)
                    guard.finish()
                    fresh_contributions = _ContributionManifest(key, root, prior.version)
                    for path in list(guard.current):
                        if path.is_relative_to(root) and path.is_file() and not path.is_symlink():
                            rel = path.relative_to(root).as_posix()
                            mode = refreshed.ownership_modes.get(rel) or prior.ownership_modes.get(rel)
                            if rel in guard.merged_paths and mode not in {"partial", "shared"}:
                                mode = "partial"
                            if rel in core_paths or rel in guard.merged_paths:
                                refreshed.record_existing(rel, ownership=mode if mode != "whole" else None)
                            else:
                                fresh_contributions.record_existing(rel, ownership=mode if mode != "whole" else None)
                    from ._file_changes import unlink

                    desired = refreshed.files.keys() | fresh_contributions.files.keys() | guard.merged_paths
                    for rel in (prior.files.keys() | contributions.files.keys()) - desired:
                        if guard.modes.get(rel) == "whole":
                            unlink(root / rel, missing_ok=True)
                    refreshed.save()
                    fresh_contributions.save()
                    from .installer import update_generated_recovery_ownership

                    update_generated_recovery_ownership(root, key, refreshed, set(refreshed.files))
                result.completed.append(key)
            except Exception as exc:  # noqa: BLE001 - continue independent integrations and report partial readiness
                result.failed[key] = str(exc)
                # Preserve usable ownership for completed writes in this failed
                # refresh too; do not make a retry mistake them for user changes.
                if refreshed is not None:
                    try:
                        for path in list(guard.current):
                            if path.is_relative_to(root) and path.is_file() and not path.is_symlink():
                                rel = path.relative_to(root).as_posix()
                                if rel in refreshed.files:
                                    prior.record_existing(rel, ownership=refreshed.ownership_modes.get(rel))
                                else:
                                    contributions.record_existing(rel, ownership=refreshed.ownership_modes.get(rel))
                        prior.save()
                        contributions.save()
                        from .installer import update_generated_recovery_ownership

                        touched = {
                            path.relative_to(root).as_posix()
                            for path in guard.current if path.is_relative_to(root)
                        }
                        update_generated_recovery_ownership(root, key, prior, touched & prior.files.keys())
                    except (OSError, ValueError) as save_error:
                        result.failed[key] += f"; ownership update failed: {save_error}"
    finally:
        file_write_validator.reset(write_token)
        file_change_observer.reset(token)
