"""
Reusable preset stacks: named, ordered lists of preset installs.

Loads and validates `.specify/preset-stacks.yml`, and applies a named stack by
calling existing `PresetManager`/`PresetCatalog` install/remove primitives —
no new install/uninstall logic lives here.
"""

import json
import os
import shutil
import tempfile
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

STACK_STATE_FILENAME = ".stack-state.json"
STACKS_CONFIG_FILENAME = "preset-stacks.yml"
RESERVED_STACK_NAMES = ("none",)


@dataclass
class PresetStackEntry:
    """A single member of a stack."""

    preset: str
    priority: int = 10
    source: Optional[str] = None


@dataclass
class PresetStack:
    """A named, ordered collection of entries."""

    name: str
    entries: list[PresetStackEntry] = field(default_factory=list)


@dataclass
class PresetStacksConfig:
    """The parsed contents of `.specify/preset-stacks.yml`."""

    stacks: list[PresetStack] = field(default_factory=list)


def load_stacks_config(project_root: Path) -> PresetStacksConfig:
    """Load and validate `.specify/preset-stacks.yml` (missing file -> empty config).

    Mirrors `PresetCatalog._load_catalog_config`'s (`presets/__init__.py:4262`)
    error-identifies-the-file validation style (FR-3000/1020/1025/1030).
    """
    from . import PresetValidationError

    config_path = project_root / ".specify" / STACKS_CONFIG_FILENAME
    if not config_path.exists():
        return PresetStacksConfig(stacks=[])

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError, UnicodeError) as e:
        raise PresetValidationError(f"Failed to read {config_path}: {e}")

    if not isinstance(data, dict):
        raise PresetValidationError(
            f"Invalid {config_path}: expected a mapping at root, got {type(data).__name__}"
        )

    stacks_data = data.get("stacks", [])
    if not isinstance(stacks_data, list):
        raise PresetValidationError(
            f"Invalid {config_path}: 'stacks' must be a list, got {type(stacks_data).__name__}"
        )

    stacks: list[PresetStack] = []
    seen_names: set[str] = set()
    for idx, stack_item in enumerate(stacks_data):
        if not isinstance(stack_item, dict):
            raise PresetValidationError(
                f"Invalid {config_path}: stack at index {idx} must be a mapping, "
                f"got {type(stack_item).__name__}"
            )
        name = str(stack_item.get("name", "")).strip()
        if not name:
            raise PresetValidationError(
                f"Invalid {config_path}: stack at index {idx} is missing a 'name'"
            )
        if name in RESERVED_STACK_NAMES:
            raise PresetValidationError(
                f"Invalid {config_path}: stack name '{name}' is reserved and cannot be used "
                f"as a stack definition (FR-1025)"
            )
        if name in seen_names:
            raise PresetValidationError(
                f"Invalid {config_path}: stack name '{name}' is defined more than once"
            )
        seen_names.add(name)

        entries_data = stack_item.get("entries", [])
        if not isinstance(entries_data, list):
            raise PresetValidationError(
                f"Invalid {config_path}: stack '{name}' has an 'entries' value that must be a "
                f"list, got {type(entries_data).__name__}"
            )

        entries: list[PresetStackEntry] = []
        seen_presets: set[str] = set()
        for entry_idx, entry_item in enumerate(entries_data):
            if not isinstance(entry_item, dict):
                raise PresetValidationError(
                    f"Invalid {config_path}: entry {entry_idx} of stack '{name}' must be a "
                    f"mapping, got {type(entry_item).__name__}"
                )
            preset = str(entry_item.get("preset", "")).strip()
            if not preset:
                raise PresetValidationError(
                    f"Invalid {config_path}: entry {entry_idx} of stack '{name}' is missing a "
                    f"'preset' ID"
                )
            if preset in seen_presets:
                raise PresetValidationError(
                    f"Invalid {config_path}: preset '{preset}' appears more than once in stack "
                    f"'{name}'"
                )
            seen_presets.add(preset)

            raw_priority = entry_item.get("priority", 10)
            if isinstance(raw_priority, bool):
                raise PresetValidationError(
                    f"Invalid {config_path}: preset '{preset}' in stack '{name}' has an invalid "
                    f"priority, expected integer, got {raw_priority!r}"
                )
            try:
                priority = int(raw_priority)
            except (TypeError, ValueError, OverflowError):
                raise PresetValidationError(
                    f"Invalid {config_path}: preset '{preset}' in stack '{name}' has an invalid "
                    f"priority, expected integer, got {raw_priority!r}"
                )

            source = entry_item.get("source")
            source = str(source).strip() if source else None

            entries.append(PresetStackEntry(preset=preset, priority=priority, source=source))

        stacks.append(PresetStack(name=name, entries=entries))

    return PresetStacksConfig(stacks=stacks)


def _stack_state_path(project_root: Path) -> Path:
    return project_root / ".specify" / "presets" / STACK_STATE_FILENAME


def _load_stack_state(project_root: Path) -> dict[str, list[str]]:
    """Load `{stack_name: [pack_id, ...]}` from `.stack-state.json` (absent file -> `{}`)."""
    state_path = _stack_state_path(project_root)
    if not state_path.exists():
        return {}
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _save_stack_state(project_root: Path, state: dict[str, list[str]]) -> None:
    """Save `{stack_name: [pack_id, ...]}` to `.stack-state.json`."""
    state_path = _stack_state_path(project_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _download_archive(url: str) -> Path:
    """Download an archive from a stack entry's explicit `source:` URL.

    Mirrors `preset add`'s `--from` branch (`presets/_commands.py:79-306`) using
    the same security primitives, without touching that existing, heavily
    tested code path.
    """
    from urllib.parse import urlparse

    from .._download_security import (
        archive_format_from_name,
        archive_suffix,
        detect_archive_format,
        is_https_or_localhost_http,
        read_response_limited,
    )
    from .._github_http import resolve_github_release_asset_api_url
    from ..authentication.http import github_provider_hosts, open_url
    from . import PresetError

    try:
        parsed = urlparse(url)
        parsed.port
    except ValueError:
        raise PresetError(f"Invalid URL: {url}")

    if not is_https_or_localhost_http(url):
        raise PresetError(
            f"URL must use HTTPS with a hostname and be a valid URL with a host. "
            f"HTTP is only allowed for localhost, 127.0.0.1, and ::1: {url}"
        )

    tmpdir = Path(tempfile.mkdtemp(prefix="specify-stack-"))
    archive_path = tmpdir / "preset.archive"
    try:
        extra_headers = None
        resolved_url = resolve_github_release_asset_api_url(
            url, open_url, github_hosts=github_provider_hosts()
        )
        if resolved_url:
            url = resolved_url
            extra_headers = {"Accept": "application/octet-stream"}

        with open_url(url, timeout=60, extra_headers=extra_headers) as response:
            final_url = response.geturl() if hasattr(response, "geturl") else url
            if not is_https_or_localhost_http(final_url):
                raise PresetError(f"URL redirected to a disallowed URL: {final_url}")
            archive_data = read_response_limited(
                response, error_type=PresetError, label=f"preset {url}"
            )
            content_type = (
                response.getheader("Content-Type") if hasattr(response, "getheader") else None
            )

        archive_path.write_bytes(archive_data)
        archive_format = detect_archive_format(
            archive_path, source_name=url, content_type=content_type, error_type=PresetError
        )
        detected_path = archive_path.with_suffix(archive_suffix(archive_format))
        os.replace(archive_path, detected_path)
        return detected_path
    except PresetError:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    except (urllib.error.URLError, OSError) as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise PresetError(f"Failed to download {url}: {e}") from e
    except BaseException:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


def _resolve_entry_source(
    project_root: Path, entry: PresetStackEntry
) -> tuple[Path, bool, Optional[Path]]:
    """Resolve a stack entry to an installable source.

    Resolution order mirrors `preset add`'s `--dev`/`--from`/plain-`preset_id`
    branches (`presets/_commands.py:79-306`): an entry's own `source:` (local
    directory or archive URL) takes precedence over catalog resolution, and
    any catalog-resolved entry bypasses `install_allowed` (FR-2025) since
    listing a preset in one's own stack is itself the trust decision.

    Returns:
        `(path, is_directory, cleanup)` — `is_directory` selects
        `install_from_directory` vs `install_from_zip` in `apply_stack`;
        `cleanup`, if not None, is a file or directory to remove after install.
    """
    from .. import _locate_bundled_preset
    from . import PresetCatalog, PresetError

    if entry.source:
        if entry.source.startswith(("http://", "https://")):
            archive_path = _download_archive(entry.source)
            return archive_path, False, archive_path.parent
        dev_path = Path(entry.source).resolve()
        if not dev_path.exists():
            raise PresetError(f"Source directory not found: {entry.source}")
        return dev_path, True, None

    bundled_path = _locate_bundled_preset(entry.preset)
    if bundled_path:
        return bundled_path, True, None

    catalog = PresetCatalog(project_root)
    pack_info = catalog.get_pack_info(entry.preset)
    if not pack_info:
        raise PresetError(
            f"Preset '{entry.preset}' not found: no bundled preset, no catalog "
            f"entry, and no explicit 'source' in the stack"
        )

    if pack_info.get("bundled") and not pack_info.get("download_url"):
        from ..extensions import REINSTALL_COMMAND

        raise PresetError(
            f"Preset '{entry.preset}' is bundled with spec-kit but could not be "
            f"found in the installed package. Try reinstalling spec-kit: "
            f"{REINSTALL_COMMAND}"
        )

    archive_path = catalog.download_pack(entry.preset, bypass_install_allowed=True)
    return archive_path, False, archive_path


@dataclass
class StackEntryResult:
    """The outcome of resolving and installing one stack entry."""

    preset: str
    success: bool
    error: Optional[str] = None


@dataclass
class StackApplyResult:
    """The outcome of applying a whole stack."""

    stack_name: str
    entries: list[StackEntryResult] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(e.success for e in self.entries)


def apply_stack(project_root: Path, stack: PresetStack, speckit_version: str) -> StackApplyResult:
    """Apply a named stack: install every current entry, then sync out dropped ones.

    Calls only the existing `PresetManager.install_from_directory`/
    `install_from_zip` (with `force=True`, which already removes-then-reinstalls
    a present pack, per `presets/__init__.py:3567-3573`) and `PresetManager.remove`
    — no new install/uninstall logic lives here.
    """
    from . import PresetError, PresetManager

    manager = PresetManager(project_root)
    entries: list[StackEntryResult] = []
    current_ids: list[str] = []

    for entry in stack.entries:
        cleanup: Optional[Path] = None
        try:
            source_path, is_directory, cleanup = _resolve_entry_source(project_root, entry)
            if is_directory:
                manager.install_from_directory(
                    source_path, speckit_version, priority=entry.priority, force=True
                )
            else:
                manager.install_from_zip(
                    source_path, speckit_version, priority=entry.priority, force=True
                )
            entries.append(StackEntryResult(preset=entry.preset, success=True))
            current_ids.append(entry.preset)
        except PresetError as e:
            entries.append(
                StackEntryResult(
                    preset=entry.preset,
                    success=False,
                    error=f"stack '{stack.name}', preset '{entry.preset}': {e}",
                )
            )
        finally:
            if cleanup is not None:
                if cleanup.is_dir():
                    shutil.rmtree(cleanup, ignore_errors=True)
                else:
                    cleanup.unlink(missing_ok=True)

    state = _load_stack_state(project_root)
    previous_ids = set(state.get(stack.name, []))
    other_stacks_ids: set[str] = set()
    for other_name, other_ids in state.items():
        if other_name != stack.name:
            other_stacks_ids.update(other_ids)

    removed: list[str] = []
    for pid in previous_ids - set(current_ids):
        if pid not in other_stacks_ids:
            manager.remove(pid)
            removed.append(pid)

    state[stack.name] = current_ids
    _save_stack_state(project_root, state)

    return StackApplyResult(stack_name=stack.name, entries=entries, removed=removed)
