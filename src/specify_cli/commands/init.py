"""specify init command."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import typer
from rich.live import Live
from rich.markup import escape as _escape_markup
from rich.panel import Panel

from .._agent_config import (
    AGENT_CONFIG,
    SCRIPT_TYPE_CHOICES,
    resolve_default_init_integration,
)
from .._assets import (
    _locate_bundled_preset,
    _locate_bundled_workflow,
    get_speckit_version,
)
from .._console import StepTracker, console, select_with_arrows, show_banner
from .._utils import (
    check_tool,
    path_is_junction as _path_is_junction,
)


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty()


def _prompts_allowed(non_interactive: bool) -> bool:
    """Return True when interactive pickers and confirmations may be shown.

    ``--non-interactive`` suppresses prompts even when stdin is a TTY. Agent
    harnesses often allocate a PTY (so ``isatty()`` is True) but cannot send
    arrow-key input, which previously hung in ``select_with_arrows``.
    """
    return not non_interactive and _stdin_is_interactive()


def _ext_spec_is_url(ext_spec: str) -> bool:
    """Return True when *ext_spec* is an http(s) URL rather than a name/path."""
    from urllib.parse import urlparse

    try:
        return urlparse(ext_spec).scheme in ("http", "https")
    except ValueError:
        return False


def _file_fingerprint(path: Path) -> str:
    """Return a digest of *path* contents and permission bits."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    digest.update(b"\0mode=")
    digest.update(format(stat.S_IMODE(path.stat().st_mode), "o").encode())
    return digest.hexdigest()


def _snapshot_files(root: Path) -> dict[str, str]:
    """Return fingerprints for regular files below *root*."""
    if not root.exists():
        return {}

    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        files[path.relative_to(root).as_posix()] = _file_fingerprint(path)
    return files


def _snapshot_tree_entries(root: Path) -> dict[str, str]:
    """Return a structural snapshot including directories and symlinks."""
    if not root.exists():
        return {}

    entries: dict[str, str] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        try:
            if path.is_symlink():
                entries[relative] = f"symlink:{os.readlink(path)}"
            elif path.is_file():
                entries[relative] = f"file:{_file_fingerprint(path)}"
            elif path.is_dir():
                entries[relative] = "directory"
        except OSError:
            entries[relative] = "unreadable"
    return entries


def _resolve_preview_child_path(spec: str) -> str:
    """Resolve caller-relative local specs before changing the child cwd."""
    if spec.startswith(("~", "./", "../", "/", ".\\", "..\\")):
        return str(Path(spec).expanduser().resolve())
    return spec


def _resolve_preview_preset_path(spec: str) -> str:
    """Resolve a local preset directory before the staged child changes cwd."""
    try:
        candidate = Path(spec).expanduser().resolve()
    except OSError:
        return _resolve_preview_child_path(spec)
    if candidate.is_dir() and (candidate / "preset.yml").is_file():
        return str(candidate)
    return _resolve_preview_child_path(spec)


def _preview_subprocess_env(staged_home: Path) -> dict[str, str]:
    """Return a child environment with user-scoped paths isolated in staging."""
    env = os.environ.copy()
    home = str(staged_home)
    env.update(
        {
            "HOME": home,
            "USERPROFILE": home,
            "XDG_CACHE_HOME": str(staged_home / ".cache"),
            "XDG_CONFIG_HOME": str(staged_home / ".config"),
            "XDG_DATA_HOME": str(staged_home / ".local" / "share"),
            "XDG_STATE_HOME": str(staged_home / ".local" / "state"),
            "APPDATA": str(staged_home / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(staged_home / "AppData" / "Local"),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    home_drive, home_path = os.path.splitdrive(home)
    if home_drive:
        env["HOMEDRIVE"] = home_drive
        env["HOMEPATH"] = home_path
    else:
        env.pop("HOMEDRIVE", None)
        env.pop("HOMEPATH", None)
    return env


def _seed_preview_home(staged_home: Path, real_home: Path) -> None:
    """Copy the read-only catalog and auth settings resolved from HOME."""
    for filename in (
        "auth.json",
        "extension-catalogs.yml",
        "preset-catalogs.yml",
    ):
        source = real_home / ".specify" / filename
        if source.is_file():
            destination = staged_home / ".specify" / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def _preview_home_seed_paths(
    real_home: Path, selected_integration: str
) -> tuple[set[Path], set[Path]]:
    """Return home paths to stage and selected-integration paths to own."""
    from ..agents import CommandRegistrar
    from ..integrations import get_integration

    integration = get_integration(selected_integration)
    if integration is None or not integration.registrar_config:
        return set(), set()

    registrar_config = integration.registrar_config
    directory = registrar_config.get("dir")
    extension = registrar_config.get("extension")
    if (
        not isinstance(directory, str)
        or not directory.startswith("~")
        or not isinstance(extension, str)
    ):
        return set(), set()

    destination = Path(directory[1:].lstrip("/\\"))
    owned_paths: set[Path] = set()
    for template in integration.list_command_templates():
        command_name = f"speckit.{template.stem}"
        output_name = CommandRegistrar._compute_output_name(
            selected_integration, command_name, registrar_config
        )
        owned_paths.add(destination / f"{output_name}{extension}")

    paths = set(owned_paths)
    real_destination = real_home / destination
    if real_destination.is_dir() and not real_destination.is_symlink():
        entries = list(real_destination.iterdir())
        for entry in entries:
            if not entry.name.startswith(("speckit-", "speckit.")):
                continue
            if extension == "/SKILL.md":
                paths.add(destination / entry.name / "SKILL.md")
            elif entry.name.endswith(extension):
                paths.add(destination / entry.name)
    return paths, owned_paths


_INIT_PLAN_ENV = "SPECIFY_INIT_PLAN_PATH"
_PREVIEW_CHILD_ACTIVE = False


def _run_staged_preview_child() -> None:
    """Run the CLI with the existing-directory prompt bypass scoped in-process."""
    global _PREVIEW_CHILD_ACTIVE

    from specify_cli import main

    _PREVIEW_CHILD_ACTIVE = True
    try:
        main()
    finally:
        _PREVIEW_CHILD_ACTIVE = False


def _staging_confirmation_is_accepted() -> bool:
    """Return whether a staged preview child may skip its directory prompt."""
    return _PREVIEW_CHILD_ACTIVE and bool(os.environ.get(_INIT_PLAN_ENV))


def _record_init_plan_action(
    action: str,
    path: str,
    provenance: str,
    source_id: str | None = None,
) -> None:
    """Append one initializer outcome when a preview plan path is configured."""
    plan_path = os.environ.get(_INIT_PLAN_ENV)
    if not _PREVIEW_CHILD_ACTIVE or not plan_path:
        return
    record: dict[str, str] = {
        "action": action,
        "path": path,
        "provenance": provenance,
    }
    if source_id:
        record["source_id"] = source_id
    try:
        with open(plan_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError as exc:
        sys.stderr.write(f"specify: failed to record init plan action: {exc}\n")


def _record_init_plan_failure(component: str, source_id: str, error: str) -> None:
    """Append an optional component failure when a preview plan is configured."""
    plan_path = os.environ.get(_INIT_PLAN_ENV)
    if not _PREVIEW_CHILD_ACTIVE or not plan_path:
        return
    record = {
        "outcome": "failure",
        "component": component,
        "source_id": source_id,
        "error": error,
    }
    try:
        with open(plan_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError as exc:
        sys.stderr.write(f"specify: failed to record init plan failure: {exc}\n")


def _recorded_plan_failures(plan_path: Path) -> list[dict[str, str]]:
    """Read structured optional component failures from a staged preview."""
    if not plan_path.is_file():
        return []
    try:
        lines = plan_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    failures: list[dict[str, str]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(record, dict) or record.get("outcome") != "failure":
            continue
        component = record.get("component")
        source_id = record.get("source_id")
        error = record.get("error")
        if all(isinstance(value, str) for value in (component, source_id, error)):
            failures.append(
                {
                    "component": component,
                    "source_id": source_id,
                    "error": error,
                }
            )
    return failures


def _merge_recorded_plan_actions(
    actions: list[dict[str, str]], plan_path: Path
) -> list[dict[str, str]]:
    """Fold initializer-recorded skip outcomes into the digest-based preview."""
    if not plan_path.is_file():
        return actions
    try:
        lines = plan_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return actions

    by_path = {record["path"]: record for record in actions}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            recorded = json.loads(line)
        except (TypeError, ValueError):
            continue
        if not isinstance(recorded, dict):
            continue
        if recorded.get("action") != "skip" or not isinstance(recorded.get("path"), str):
            continue
        path = recorded["path"]
        existing = by_path.get(path)
        if existing is not None and existing.get("action") != "preserve":
            continue
        merged: dict[str, str] = {
            "action": "skip",
            "path": path,
            "provenance": str(recorded.get("provenance") or "core"),
        }
        source_id = recorded.get("source_id")
        if source_id:
            merged["source_id"] = str(source_id)
        by_path[path] = merged
    return list(by_path.values())


PreviewOwnership = tuple[str, str | None]


def _preview_manifest_ownership(staged_root: Path) -> dict[str, PreviewOwnership]:
    """Map manifest-tracked staged paths to provenance category and source ID."""
    ownership: dict[str, PreviewOwnership] = {}
    manifests = staged_root / ".specify" / "integrations"
    if not manifests.is_dir():
        return ownership

    for manifest_path in manifests.glob("*.manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            key = str(
                manifest.get(
                    "integration",
                    manifest.get("key", manifest_path.stem.removesuffix(".manifest")),
                )
            )
            source = ("core", key) if key == "speckit" else ("integration", key)
            for relative_path in manifest.get("files", {}):
                ownership[str(relative_path)] = source
        except (OSError, TypeError, ValueError):
            continue
    return ownership


def _preview_registry_entries(staged_root: Path) -> list[tuple[str, dict[str, Any]]]:
    """Load valid source entries from staged extension and preset registries."""
    registries: list[tuple[str, dict[str, Any]]] = []
    registry_specs = (
        (
            "extension",
            staged_root / ".specify" / "extensions" / ".registry",
            "extensions",
        ),
        ("preset", staged_root / ".specify" / "presets" / ".registry", "presets"),
    )
    for category, registry_path, collection_key in registry_specs:
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            entries = data.get(collection_key, {})
        except (AttributeError, OSError, TypeError, ValueError):
            continue
        if not isinstance(entries, dict):
            continue
        registries.append(
            (
                category,
                {
                    source_id: metadata
                    for source_id, metadata in entries.items()
                    if isinstance(source_id, str) and isinstance(metadata, dict)
                },
            )
        )
    return registries


def _preview_registry_sources(staged_root: Path) -> dict[str, set[str]]:
    """Return source ID to provenance categories from staged registries."""
    sources: dict[str, set[str]] = {}
    for category, entries in _preview_registry_entries(staged_root):
        for source_id in entries:
            sources.setdefault(source_id, set()).add(category)
    return sources


def _preview_registry_ownership(
    staged_root: Path,
) -> tuple[dict[str, PreviewOwnership], dict[str, PreviewOwnership]]:
    """Map registered command outputs in project and home staging scopes."""
    from ..agents import CommandRegistrar

    registrar = CommandRegistrar()
    project_ownership: dict[str, PreviewOwnership] = {}
    home_ownership: dict[str, PreviewOwnership] = {}
    for category, entries in _preview_registry_entries(staged_root):
        for source_id, metadata in entries.items():
            registered = metadata.get("registered_commands", {})
            if not isinstance(registered, dict):
                continue
            for agent_name, command_names in registered.items():
                agent_config = registrar.AGENT_CONFIGS.get(agent_name)
                if not isinstance(agent_config, dict) or not isinstance(
                    command_names, list
                ):
                    continue
                dir_value = agent_config.get("dir")
                extension = agent_config.get("extension")
                if not isinstance(dir_value, str) or not isinstance(extension, str):
                    continue
                if dir_value.startswith("~"):
                    destination = Path(dir_value[1:].lstrip("/"))
                    scope = home_ownership
                else:
                    destination = Path(dir_value)
                    if destination.is_absolute():
                        continue
                    canonical = staged_root / destination
                    legacy = agent_config.get("legacy_dir")
                    if (
                        not canonical.exists()
                        and isinstance(legacy, str)
                        and (staged_root / legacy).exists()
                    ):
                        destination = Path(legacy)
                    scope = project_ownership
                for command_name in command_names:
                    if not isinstance(command_name, str):
                        continue
                    output_name = registrar._compute_output_name(
                        agent_name, command_name, agent_config
                    )
                    relative_path = (
                        destination / f"{output_name}{extension}"
                    ).as_posix()
                    scope[relative_path] = category, source_id
                    if agent_name == "copilot":
                        prompt_path = (
                            Path(".github") / "prompts" / f"{command_name}.prompt.md"
                        ).as_posix()
                        project_ownership[prompt_path] = category, source_id
    return project_ownership, home_ownership


def _preview_content_ownership(
    content: str, registry_sources: dict[str, set[str]]
) -> PreviewOwnership | None:
    """Read generated ownership markers, using registries to type bare IDs."""
    bare_source_id: str | None = None
    for line in content.splitlines():
        marker = line.strip()
        if marker.startswith("source:"):
            value = marker.removeprefix("source:").strip().strip("\"'")
            if value.startswith(("preset:", "extension:")):
                category, source_id = value.split(":", 1)
                source_id = source_id.split(":", 1)[0]
                if category in registry_sources.get(source_id, set()):
                    return category, source_id
        if marker.startswith("<!--") and marker.endswith("-->"):
            value = marker.removeprefix("<!--").removesuffix("-->").strip()
            if value.startswith(("preset:", "extension:")):
                category, source_id = value.split(":", 1)
                if category in registry_sources.get(source_id, set()):
                    return category, source_id
            if value.startswith("Source:"):
                bare_source_id = value.removeprefix("Source:").strip()
        elif marker.startswith("# Source:"):
            bare_source_id = marker.removeprefix("# Source:").strip()

    categories = registry_sources.get(bare_source_id or "", set())
    if len(categories) == 1 and bare_source_id:
        return next(iter(categories)), bare_source_id
    if bare_source_id:
        for category in ("preset", "extension"):
            if category in categories and f"{category}:{bare_source_id}" in content:
                return category, bare_source_id
    return None


def _preview_marker_ownership(
    staged_root: Path,
    registry_sources: dict[str, set[str]],
    relative_paths: set[str] | None = None,
) -> dict[str, PreviewOwnership]:
    """Map staged generated artifacts using their embedded ownership markers."""
    ownership: dict[str, PreviewOwnership] = {}
    paths = (
        relative_paths
        if relative_paths is not None
        else set(_snapshot_files(staged_root))
    )
    for relative_path in paths:
        path = staged_root / relative_path
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        source = _preview_content_ownership(content, registry_sources)
        if source is not None:
            ownership[relative_path] = source
    return ownership


def _preview_default_ownership(
    relative_path: str, default: PreviewOwnership
) -> PreviewOwnership:
    if (
        relative_path.startswith(".specify/integrations/")
        and relative_path.endswith(".manifest.json")
    ):
        integration_id = Path(relative_path).name.removesuffix(".manifest.json")
        if integration_id == "speckit":
            return "core", "speckit"
        return "integration", integration_id
    if relative_path.startswith(".specify/workflows/"):
        remainder = relative_path.removeprefix(".specify/workflows/")
        workflow_id = remainder.split("/", 1)[0]
        return "workflow", workflow_id if "/" in remainder else None
    if relative_path.startswith(".specify/extensions/"):
        remainder = relative_path.removeprefix(".specify/extensions/")
        extension_id = remainder.split("/", 1)[0]
        return "extension", extension_id if "/" in remainder else None
    if relative_path.startswith(".specify/presets/"):
        remainder = relative_path.removeprefix(".specify/presets/")
        preset_id = remainder.split("/", 1)[0]
        return "preset", preset_id if "/" in remainder else None
    if relative_path.startswith(".specify/"):
        return "core", None
    return default


def _constitution_plan_ownership(project_path: Path) -> PreviewOwnership:
    """Read the materialized constitution's source from its sidecar."""
    provenance = (
        project_path / ".specify" / "memory" / ".constitution-template.json"
    )
    try:
        metadata = json.loads(provenance.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return "core", None
    if not isinstance(metadata, dict):
        return "core", None

    source = metadata.get("source")
    if not isinstance(source, str):
        return "core", None
    if source.startswith("extension:"):
        source_id = source.removeprefix("extension:").split(" ", 1)[0]
        return "extension", source_id or None
    if source in {"core", "core (bundled)", "project override"}:
        return "core", None
    source_id = source.split(" v", 1)[0].strip()
    return ("preset", source_id) if source_id else ("core", None)


def _build_preview_actions(
    initial_files: dict[str, str],
    staged_root: Path,
    *,
    path_prefix: str = "",
    ownership: dict[str, PreviewOwnership] | None = None,
    default_ownership: PreviewOwnership = ("integration", None),
    directory_conflict: bool = False,
    staged_files: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Classify files produced by a staged initialization."""
    if staged_files is None:
        staged_files = _snapshot_files(staged_root)
    ownership = ownership or {}
    candidates = {
        path
        for path, digest in staged_files.items()
        if initial_files.get(path) != digest
    }
    candidates.update(path for path in initial_files if path not in staged_files)
    candidates.update(path for path in ownership if path in staged_files)

    actions: list[dict[str, str]] = []
    for path in sorted(candidates):
        staged_digest = staged_files.get(path)
        initial_digest = initial_files.get(path)
        if staged_digest is None:
            action = "remove"
        elif initial_digest is None:
            action = "create"
        elif initial_digest != staged_digest:
            action = "conflict" if directory_conflict else "overwrite"
        else:
            action = "preserve"
        provenance, source_id = ownership.get(
            path, _preview_default_ownership(path, default_ownership)
        )
        record = {
            "action": action,
            "path": f"{path_prefix}{path}",
            "provenance": provenance,
        }
        if source_id:
            record["source_id"] = source_id
        actions.append(record)
    return actions


def _emit_dry_run_preview(payload: dict[str, Any], *, json_output: bool) -> None:
    """Render a stable human or machine-readable initialization preview."""
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
        return

    console.print("\n[bold cyan]Initialization preview[/bold cyan]")
    if payload.get("gate") == "force_required":
        console.print(
            "[yellow]conflict[/yellow]  target directory exists; applying this plan requires --force"
        )
    elif payload.get("gate") == "confirmation_required":
        console.print("[yellow]confirmation required[/yellow]  target directory is not empty")
    if payload.get("error"):
        console.print(
            f"[red]failed[/red]    {_escape_markup(str(payload['error']))}"
        )
    for failure in payload["failures"]:
        component = _escape_markup(str(failure["component"]))
        source_id = _escape_markup(str(failure["source_id"]))
        error = _escape_markup(str(failure["error"]))
        console.print(
            f"failed     {component}:{source_id} {error}"
        )
    for record in payload["actions"]:
        action = _escape_markup(str(record["action"]))
        path = _escape_markup(str(record["path"]))
        source = str(record["provenance"])
        if record.get("source_id"):
            source = f"{source}:{record['source_id']}"
        console.print(
            f"{action:<10} {path} [dim]({_escape_markup(source)})[/dim]"
        )


def _raise_dry_run_json_error(
    message: str,
    *,
    project_name: str | None,
    here: bool,
) -> None:
    """Emit one stable JSON error document for parent-side validation."""
    if here or project_name == ".":
        target: str | None = str(Path.cwd())
    elif project_name:
        target = str(Path(project_name).resolve())
    else:
        target = None
    _emit_dry_run_preview(
        {
            "dry_run": True,
            "target": target,
            "conflict": False,
            "gate": "none",
            "actions": [],
            "failures": [],
            "error": message,
        },
        json_output=True,
    )
    raise typer.Exit(1)


def _strip_windows_extended_prefix(text: str) -> str:
    """Strip the ``\\\\?\\`` / ``//?/`` prefix Windows adds to long paths."""
    if text.startswith("\\\\?\\"):
        text = text[4:]
        if text[:4].upper() == "UNC\\":
            return "\\\\" + text[4:]
        return text
    if text.startswith("//?/"):
        text = text[4:]
        if text[:4].upper() == "UNC/":
            return "//" + text[4:]
        return text
    return text


def _normalize_fs_path(path: Path) -> Path:
    """Resolve *path* and drop Windows extended prefixes so containment works."""
    text = _strip_windows_extended_prefix(os.fsdecode(os.fspath(path)))
    path = Path(text)
    try:
        path = path.resolve()
    except (OSError, RuntimeError):
        pass
    text = _strip_windows_extended_prefix(os.fsdecode(os.fspath(path)))
    if os.name == "nt":
        text = os.path.normcase(text)
    return Path(text)


def _is_within_root(path: Path, root: Path) -> bool:
    path_text = os.fspath(_normalize_fs_path(path))
    root_text = os.fspath(_normalize_fs_path(root))
    try:
        common = os.path.commonpath((path_text, root_text))
    except ValueError:
        return False
    if os.name == "nt":
        return os.path.normcase(common) == os.path.normcase(root_text)
    return common == root_text


def _symlink_target(path: Path) -> Path | None:
    raw = _strip_windows_extended_prefix(os.fsdecode(os.readlink(path)))
    raw_target = Path(raw)
    if not raw_target.is_absolute():
        raw_target = path.parent / raw_target
    return _normalize_fs_path(raw_target)


def _iter_symlinks(root: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in (*dirnames, *filenames):
            candidate = Path(dirpath) / name
            if candidate.is_symlink():
                found.append(candidate)
    return found


def _remap_symlink_to_staged(
    path: Path, project_root: Path, staged_root: Path
) -> None:
    target = _symlink_target(path)
    if target is None:
        _quarantine_symlink(path, staged_root)
        return
    try:
        relative = os.path.relpath(os.fspath(target), os.fspath(project_root))
    except ValueError:
        _quarantine_symlink(path, staged_root)
        return
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        _quarantine_symlink(path, staged_root)
        return
    remapped = staged_root / relative_path
    was_dir = path.is_dir()
    path.unlink()
    path.symlink_to(remapped, target_is_directory=was_dir)


def _quarantine_root(staged_root: Path) -> Path:
    return _normalize_fs_path(
        staged_root.parent / f"{staged_root.name}-quarantine"
    )


def _quarantine_symlink(path: Path, staged_root: Path) -> None:
    """Retarget an external symlink at an isolated dummy outside *staged_root*.

    The dummy stays outside the staged project so ``Path.resolve()`` still
    escapes, matching real init containment checks, while writes cannot reach
    the original live target.
    """
    dummy = _quarantine_root(staged_root) / path.relative_to(staged_root)
    dummy.parent.mkdir(parents=True, exist_ok=True)
    was_dir = path.is_dir()
    path.unlink()
    if was_dir:
        dummy.mkdir(parents=True, exist_ok=True)
    else:
        dummy.touch()
    path.symlink_to(dummy, target_is_directory=was_dir)


def _remap_in_project_symlinks(project_root: Path, staged_root: Path) -> None:
    """Keep staged symlinks from pointing at the live project or external paths.

    In-project absolute links are retargeted at the staged copy. Links that
    resolve outside the project are retargeted at an isolated dummy outside
    staging so containment checks still fail, without writing through to the
    live target.
    """
    project_root = _normalize_fs_path(project_root)
    staged_root = _normalize_fs_path(staged_root)
    quarantine_root = _quarantine_root(staged_root)
    for _ in range(32):
        changed = False
        for path in _iter_symlinks(staged_root):
            resolved = _symlink_target(path)
            if resolved is not None and (
                _is_within_root(resolved, staged_root)
                or _is_within_root(resolved, quarantine_root)
            ):
                continue
            if resolved is not None and _is_within_root(resolved, project_root):
                _remap_symlink_to_staged(path, project_root, staged_root)
                changed = True
                continue
            _quarantine_symlink(path, staged_root)
            changed = True
        if not changed:
            return
    raise RuntimeError("staged symlink isolation did not converge")


def _preview_path_is_managed(path: Path, copy_root: Path) -> bool:
    """Return whether an unreadable path may affect initialization behavior."""
    try:
        relative = path.relative_to(copy_root)
    except ValueError:
        return True
    parts = (copy_root.name, *relative.parts)
    if copy_root.name == ".specify" and relative.parts:
        return relative.parts[0] in {
            ".gitignore",
            "extensions",
            "extensions.yml",
            "init-options.json",
            "integration.json",
            "integrations",
            "memory",
            "presets",
            "scripts",
            "templates",
            "workflows",
        }
    return any(part.startswith(("speckit-", "speckit.")) for part in parts)


def _path_is_readable_for_staging(path: Path) -> bool:
    """Probe whether copytree can read a regular file or enumerate a directory."""
    try:
        if path.is_file():
            with path.open("rb"):
                pass
        elif path.is_dir():
            with os.scandir(path):
                pass
        return True
    except OSError:
        return False


def _ignore_special_files(
    directory: str,
    names: list[str],
    *,
    copy_root: Path | None = None,
) -> set[str]:
    """Skip inaccessible unrelated entries and unsupported filesystem nodes."""
    ignored: set[str] = set()
    root = copy_root or Path(directory)
    for name in names:
        candidate = Path(directory) / name
        try:
            if _path_is_junction(candidate):
                raise ValueError(
                    f"Preview staging refuses Windows directory junction: {candidate}"
                )
            if (
                not candidate.is_symlink()
                and not candidate.is_file()
                and not candidate.is_dir()
            ):
                ignored.add(name)
                continue
            if (
                not candidate.is_symlink()
                and not _path_is_readable_for_staging(candidate)
                and not _preview_path_is_managed(candidate, root)
            ):
                ignored.add(name)
        except OSError:
            ignored.add(name)
    return ignored


def _copy_staged_path(source: Path, destination: Path) -> None:
    """Copy one selected path without following symlinks."""
    if _path_is_junction(source):
        raise ValueError(
            f"Preview staging refuses Windows directory junction: {source}"
        )
    if source.is_symlink():
        if os.path.lexists(destination):
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(
            os.readlink(source), target_is_directory=source.is_dir()
        )
    elif source.is_dir():
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            dirs_exist_ok=True,
            ignore=lambda directory, names: _ignore_special_files(
                directory, names, copy_root=source
            ),
        )
    elif source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _copy_selected_staged_path(
    project_path: Path,
    staged_root: Path,
    relative_path: Path,
) -> None:
    """Copy a selected path while preserving any symlinked parent component."""
    current = Path()
    for index, part in enumerate(relative_path.parts):
        current /= part
        source = project_path / current
        destination = staged_root / current
        if _path_is_junction(source):
            raise ValueError(
                f"Preview staging refuses Windows directory junction: {source}"
            )
        if source.is_symlink():
            _copy_staged_path(source, destination)
            return
        if not source.exists():
            return
        if index < len(relative_path.parts) - 1 and not source.is_dir():
            _copy_staged_path(source, destination)
            return
    _copy_staged_path(project_path / relative_path, staged_root / relative_path)


def _copy_staged_symlink_targets(project_path: Path, staged_root: Path) -> None:
    """Copy project-local targets reached by selected staged symlinks."""
    for _ in range(32):
        copied = False
        for staged_link in _iter_symlinks(staged_root):
            relative_link = staged_link.relative_to(staged_root)
            source_link = project_path / relative_link
            try:
                source_target = _symlink_target(source_link)
            except OSError:
                continue
            if source_target is None or not _is_within_root(
                source_target, project_path
            ):
                continue
            relative_target = source_target.relative_to(
                _normalize_fs_path(project_path)
            )
            staged_target = staged_root / relative_target
            if os.path.lexists(staged_target):
                continue
            _copy_staged_path(project_path / relative_target, staged_target)
            copied = True
        if not copied:
            return
    raise RuntimeError("staged symlink target copy did not converge")


def _stage_project_copy(
    project_path: Path,
    staged_root: Path,
    relative_paths: set[Path] | None = None,
) -> None:
    """Copy selected project paths into staging and isolate live symlinks."""
    if relative_paths is None:
        shutil.copytree(
            project_path,
            staged_root,
            symlinks=True,
            ignore=lambda directory, names: _ignore_special_files(
                directory, names, copy_root=project_path
            ),
        )
    else:
        staged_root.mkdir(parents=True, exist_ok=True)
        selected: list[Path] = []
        for relative_path in sorted(relative_paths, key=lambda path: len(path.parts)):
            if relative_path.is_absolute() or ".." in relative_path.parts:
                continue
            if any(
                relative_path == parent or parent in relative_path.parents
                for parent in selected
            ):
                continue
            selected.append(relative_path)
            _copy_selected_staged_path(project_path, staged_root, relative_path)
        _copy_staged_symlink_targets(project_path, staged_root)
    _remap_in_project_symlinks(project_path.resolve(), staged_root.resolve())


def _preview_seed_paths(
    selected_integration: str,
    integration_options: str | None,
    script_type: str,
) -> set[Path]:
    """Return project paths whose existing state can affect initialization."""
    from ..integrations import INTEGRATION_REGISTRY, get_integration

    integration = get_integration(selected_integration)
    paths = {Path(".specify")}
    if integration is None:
        return paths

    config = integration.config or {}
    registrar = integration.registrar_config or {}
    folder = config.get("folder")
    commands_subdir = config.get("commands_subdir")
    values = [
        registrar.get("dir"),
        registrar.get("legacy_dir"),
        registrar.get("detect_dir"),
        getattr(integration, "legacy_flat_command_dir", None),
        ".opencode/plugin/speckit-events.ts",
    ]
    values.extend(
        getattr(candidate, "events_config_file", None)
        for candidate in INTEGRATION_REGISTRY.values()
    )
    if isinstance(folder, str) and isinstance(commands_subdir, str):
        values.append(str(Path(folder) / commands_subdir))

    if selected_integration == "generic" and integration_options:
        resolver = getattr(integration, "_resolve_commands_dir", None)
        if callable(resolver):
            try:
                values.append(resolver(None, {"raw_options": integration_options}))
            except (TypeError, ValueError):
                pass

    extras = {
        "bob": (".bob/skills",),
        "copilot": (
            ".github/skills",
            ".github/prompts",
            ".vscode/settings.json",
        ),
        "kimi": (".kimi/skills",),
        "rovodev": (".rovodev/prompts", ".rovodev/prompts.yml"),
    }
    values.extend(extras.get(selected_integration, ()))
    if script_type == "py":
        values.extend((".venv/bin/python", ".venv/Scripts/python.exe"))

    for value in values:
        if not isinstance(value, str) or value.startswith("~"):
            continue
        relative_path = Path(value)
        if (
            relative_path == Path(".")
            or relative_path.is_absolute()
            or ".." in relative_path.parts
        ):
            continue
        paths.add(relative_path)
    return paths


def _preview_child_failure_message(result: subprocess.CompletedProcess[str]) -> str:
    """Extract the initializer failure from captured child output."""
    combined = " ".join(
        part.strip().replace("\n", " ")
        for part in (result.stderr, result.stdout)
        if part
    )
    combined = " ".join(
        "".join(
            " " if "\u2500" <= char <= "\u257f" else char for char in combined
        ).split()
    )
    marker = "Initialization failed: "
    if marker in combined:
        combined = combined[combined.index(marker) + len(marker) :]
    elif "escapes project root" in combined:
        start = combined.find("Integration destination")
        if start >= 0:
            combined = combined[start:]
    return combined[:500]


def _preview_init(
    *,
    project_path: Path,
    gate: str,
    force: bool,
    here: bool,
    script_type: str,
    selected_integration: str,
    ignore_agent_tools: bool,
    preset: str | None,
    integration_options: str | None,
    extensions: list[str] | None,
    trust_extension_urls: bool,
    json_output: bool,
) -> None:
    """Run the canonical initializer in staging and report its file plan."""
    payload: dict[str, Any] = {
        "dry_run": True,
        "target": str(project_path),
        "conflict": gate != "none",
        "gate": gate,
        "actions": [],
        "failures": [],
    }

    real_home = Path.home()
    url_extensions = [spec for spec in extensions or [] if _ext_spec_is_url(spec)]
    staged_extensions = [spec for spec in extensions or [] if not _ext_spec_is_url(spec)]

    with tempfile.TemporaryDirectory(prefix="specify-init-preview-") as tmp_dir:
        staged_root = Path(tmp_dir) / "project"
        staged_home = Path(tmp_dir) / "home"
        staged_home.mkdir()
        try:
            home_seed_paths, home_owned_paths = _preview_home_seed_paths(
                real_home, selected_integration
            )
            _seed_preview_home(staged_home, real_home)
            if home_seed_paths:
                _stage_project_copy(real_home, staged_home, home_seed_paths)
            if project_path.exists():
                _stage_project_copy(
                    project_path,
                    staged_root,
                    _preview_seed_paths(
                        selected_integration,
                        integration_options,
                        script_type,
                    ),
                )
            else:
                staged_root.mkdir()
        except (OSError, RuntimeError, ValueError, shutil.Error) as exc:
            payload["error"] = f"failed to stage preview inputs: {exc}"
            _emit_dry_run_preview(payload, json_output=json_output)
            raise typer.Exit(1) from None

        initial_project_files = _snapshot_files(staged_root)
        initial_home_files = _snapshot_files(staged_home)
        initial_registry_sources = _preview_registry_sources(staged_root)
        initial_project_ownership = _preview_manifest_ownership(staged_root)
        initial_registry_project, initial_registry_home = (
            _preview_registry_ownership(staged_root)
        )
        initial_project_ownership.update(initial_registry_project)
        initial_project_ownership.update(
            _preview_marker_ownership(
                staged_root,
                initial_registry_sources,
                set(initial_project_files),
            )
        )
        initial_home_ownership = dict(initial_registry_home)
        initial_home_ownership.update(
            _preview_marker_ownership(
                staged_home,
                initial_registry_sources,
                set(initial_home_files),
            )
        )
        for relative_path in home_owned_paths:
            initial_home_ownership.setdefault(
                relative_path.as_posix(),
                ("integration", selected_integration),
            )
        quarantine_states = {
            "project": _snapshot_tree_entries(_quarantine_root(staged_root)),
            "home": _snapshot_tree_entries(_quarantine_root(staged_home)),
        }

        # Run the same public CLI path in a child process. Besides preventing
        # mutations of the target root, this isolates Rich's Live output from
        # the preview's human/JSON output contract. The staging-only
        # confirmation signal avoids a prompt without changing force mode.
        command = [
            sys.executable,
            "-I",
            "-c",
            (
                "from specify_cli.commands.init import "
                "_run_staged_preview_child; _run_staged_preview_child()"
            ),
            "init",
            "--non-interactive",
            "--integration",
            selected_integration,
            "--script",
            script_type,
        ]
        if here:
            command.append("--here")
        else:
            command.append(str(staged_root))
        if force or gate == "force_required":
            command.append("--force")
        command.append("--ignore-agent-tools")
        if integration_options:
            command.extend(["--integration-options", integration_options])
        if preset:
            command.extend(["--preset", _resolve_preview_preset_path(preset)])
        for extension in staged_extensions:
            command.extend(["--extension", _resolve_preview_child_path(extension)])
        if trust_extension_urls:
            command.append("--trust-extension-urls")

        plan_path = Path(tmp_dir) / "init-plan.jsonl"
        env = _preview_subprocess_env(staged_home)
        env[_INIT_PLAN_ENV] = str(plan_path)
        result = subprocess.run(
            command,
            cwd=staged_root if here else Path.cwd(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )
        if result.returncode:
            payload["error"] = _preview_child_failure_message(result)
        elif any(
            _snapshot_tree_entries(
                _quarantine_root(staged_root if scope == "project" else staged_home)
            )
            != before
            for scope, before in quarantine_states.items()
        ):
            payload["error"] = (
                "staged initialization attempted to write through an external "
                "symlink"
            )
        else:
            staged_project_files = _snapshot_files(staged_root)
            registry_sources = _preview_registry_sources(staged_root)
            project_ownership = dict(initial_project_ownership)
            project_ownership.update(_preview_manifest_ownership(staged_root))
            registry_project_ownership, registry_home_ownership = (
                _preview_registry_ownership(staged_root)
            )
            project_ownership.update(registry_project_ownership)
            project_ownership.update(
                _preview_marker_ownership(
                    staged_root, registry_sources, set(staged_project_files)
                )
            )
            payload["actions"] = _build_preview_actions(
                initial_project_files,
                staged_root,
                ownership=project_ownership,
                default_ownership=("integration", selected_integration),
                directory_conflict=gate == "force_required",
                staged_files=staged_project_files,
            )
            staged_home_files = _snapshot_files(staged_home)
            home_ownership = dict(initial_home_ownership)
            home_ownership.update(registry_home_ownership)
            home_ownership.update(
                _preview_marker_ownership(
                    staged_home, registry_sources, set(staged_home_files)
                )
            )
            payload["actions"].extend(
                _build_preview_actions(
                    initial_home_files,
                    staged_home,
                    path_prefix="~/",
                    ownership=home_ownership,
                    default_ownership=("integration", selected_integration),
                    directory_conflict=False,
                    staged_files=staged_home_files,
                )
            )
            payload["actions"] = _merge_recorded_plan_actions(
                payload["actions"], plan_path
            )
        payload["failures"] = _recorded_plan_failures(plan_path)

    if not payload.get("error"):
        for spec in url_extensions:
            payload["actions"].append(
                {
                    "action": "unresolved",
                    "path": spec,
                    "provenance": "extension",
                    "source_id": spec,
                    "reason": "URL extensions are not fetched during dry-run",
                }
            )
    payload["actions"].sort(key=lambda action: action["path"])
    _emit_dry_run_preview(payload, json_output=json_output)
    if payload.get("error"):
        raise typer.Exit(1)


def _confirm_extension_url_trust(
    url_specs: list[str],
    *,
    trust_override: bool,
    allow_prompt: bool | None = None,
) -> dict[str, bool]:
    """Resolve trust for each URL-based extension before the Live display.

    URL installs pull an arbitrary external extension, so they get the same
    default-deny confirmation as ``extension add --from``. Returns a mapping of
    ``url_spec -> approved``. With *trust_override* every URL is pre-approved.
    In a non-interactive session without the override, every URL is denied
    (the prompt cannot be answered), mirroring the default-deny posture.
    """
    from rich.markup import escape as _escape_markup
    from rich.panel import Panel

    approvals: dict[str, bool] = {}
    interactive = _stdin_is_interactive() if allow_prompt is None else allow_prompt
    for spec in url_specs:
        if trust_override:
            approvals[spec] = True
            continue
        if not interactive:
            approvals[spec] = False
            continue
        console.print()
        console.print(
            Panel(
                "[bold]You are installing an extension from an external URL that is not\n"
                "listed in any of your configured extension catalogs.[/bold]\n\n"
                f"URL: {_escape_markup(spec)}\n\n"
                "Only install extensions from sources you trust.",
                title="[bold yellow]⚠ Untrusted Source[/bold yellow]",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        console.print()
        approvals[spec] = typer.confirm(
            f"Install extension from {spec}?", default=False
        )
    return approvals


def _install_extension_during_init(project_path: Path, ext_spec: str, speckit_version: str) -> str:
    """Install a single extension during ``specify init``.

    Handles bundled extension names, local directory paths, and HTTPS URLs.
    Returns a short status message on success.
    Raises ``ValueError`` on failure so the caller can convert it to a
    tracker error without aborting the entire init.
    """
    from urllib.parse import urlparse

    from .._assets import _locate_bundled_extension
    from ..extensions import ExtensionCatalog, ExtensionError, ExtensionManager
    from ..extensions._commands import (
        _resolve_catalog_extension,
        install_extension_from_url,
    )

    manager = ExtensionManager(project_path)

    # --- URL ---
    parsed = urlparse(ext_spec)
    if parsed.scheme in ("http", "https"):
        try:
            manifest = install_extension_from_url(
                manager, project_path, ext_spec, speckit_version
            )
        except ExtensionError as exc:
            raise ValueError(str(exc)) from exc
        return f"{manifest.name} v{manifest.version} installed"

    # --- Local path ---
    if ext_spec.startswith(("./", "../", "/", "~/", ".\\", "..\\")) or Path(ext_spec).is_absolute():
        source_path = Path(ext_spec).expanduser().resolve()
        if not source_path.exists():
            raise ValueError(f"Directory not found: {source_path}")
        if not (source_path / "extension.yml").exists():
            raise ValueError(f"No extension.yml found in {source_path}")
        manifest = manager.install_from_directory(source_path, speckit_version)
        return f"{manifest.name} v{manifest.version} installed"

    # --- Bundled extension name or catalog ID ---
    bundled_path = _locate_bundled_extension(ext_spec)
    if bundled_path is not None:
        if manager.registry.is_installed(ext_spec):
            _record_init_plan_action(
                "skip",
                f".specify/extensions/{ext_spec}/extension.yml",
                "extension",
                ext_spec,
            )
            return "already installed"
        manifest = manager.install_from_directory(bundled_path, speckit_version)
        return f"{manifest.name} v{manifest.version} installed"

    # Fall back to catalog
    catalog = ExtensionCatalog(project_path)
    ext_info, catalog_error = _resolve_catalog_extension(ext_spec, catalog, "add")
    if catalog_error:
        raise ValueError(f"Could not query extension catalog: {catalog_error}")
    if not ext_info:
        raise ValueError(f"Extension '{ext_spec}' not found in bundled extensions or catalog")

    resolved_id = ext_info["id"]
    if resolved_id != ext_spec:
        bundled_path = _locate_bundled_extension(resolved_id)
        if bundled_path is not None:
            if manager.registry.is_installed(resolved_id):
                _record_init_plan_action(
                    "skip",
                    f".specify/extensions/{resolved_id}/extension.yml",
                    "extension",
                    resolved_id,
                )
                return "already installed"
            manifest = manager.install_from_directory(bundled_path, speckit_version)
            return f"{manifest.name} v{manifest.version} installed"

    if ext_info.get("bundled") and not ext_info.get("download_url"):
        from ..extensions import REINSTALL_COMMAND

        raise ValueError(
            f"Extension '{resolved_id}' is bundled with spec-kit but not found in the installed package. "
            f"Try reinstalling spec-kit: {REINSTALL_COMMAND}"
        )

    if not ext_info.get("_install_allowed", True):
        catalog_name = ext_info.get("_catalog_name", "community")
        raise ValueError(
            f"Extension '{ext_spec}' is in the '{catalog_name}' catalog but installation is not allowed from that catalog"
        )

    zip_path = catalog.download_extension(resolved_id)
    try:
        manifest = manager.install_from_zip(zip_path, speckit_version)
    finally:
        zip_path.unlink(missing_ok=True)
    return f"{manifest.name} v{manifest.version} installed"


def _shell_quote_arg(value: str) -> str:
    """Quote *value* as one argument for the shells of the host OS.

    The Next Steps ``cd`` line is copy-pasted into whichever shell ran
    ``specify init``, so it is quoted for the host the same way
    ``_version._render_argv`` renders its copy-pasteable installer command:
    ``list2cmdline`` on Windows, ``shlex.quote`` elsewhere. The Windows branch
    must emit double quotes -- ``cd 'my project'`` is a path-not-found in
    cmd.exe, while ``cd "my project"`` is accepted by cmd.exe, PowerShell and
    Git Bash alike. A value needing no quoting is returned unchanged.

    Whitespace only. PowerShell also glob-expands ``[``/``]`` and expands
    ``$``/backtick inside double quotes, so such a name still needs
    ``Set-Location -LiteralPath`` there -- syntax invalid in cmd.exe and sh, so
    this shell-neutral line cannot cover it.
    """
    return subprocess.list2cmdline([value]) if os.name == "nt" else shlex.quote(value)


def ensure_constitution_from_template(
    project_path: Path, tracker: StepTracker | None = None
) -> None:
    """Materialize the resolved constitution template to memory if missing.

    Resolution walks the full priority stack (project overrides → installed
    presets → extensions → core) via :class:`PresetResolver`, so a preset that
    ships a ``constitution-template`` (e.g. ``strategy: replace`` with a ratified
    constitution) can seed the memory file. When nothing overrides it, the
    resolver falls through to the core template.
    """
    from ..presets import _materialize_constitution_template

    memory_constitution = project_path / ".specify" / "memory" / "constitution.md"

    if memory_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.skip("constitution", "existing file preserved")
        provenance, source_id = _constitution_plan_ownership(project_path)
        _record_init_plan_action(
            "skip",
            ".specify/memory/constitution.md",
            provenance,
            source_id,
        )
        return

    try:
        materialization = _materialize_constitution_template(
            project_path, memory_constitution
        )
        if materialization is None:
            if tracker:
                tracker.add("constitution", "Constitution setup")
                tracker.error("constitution", "template not found")
            _record_init_plan_failure(
                "constitution", "constitution", "template not found"
            )
            return
        if tracker:
            tracker.add("constitution", "Constitution setup")
            if materialization == "copied":
                tracker.complete("constitution", "copied from template")
            else:
                tracker.complete("constitution", "composed from template")
        else:
            console.print("[cyan]Initialized constitution from template[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", str(e))
        else:
            console.print(
                f"[yellow]Warning: Could not initialize constitution: {e}[/yellow]"
            )
        _record_init_plan_failure("constitution", "constitution", str(e))


def register(app: typer.Typer) -> None:
    @app.command()
    def init(
        project_name: str = typer.Argument(
            None,
            help="Name for your new project directory (optional if using --here, or use '.' for current directory)",
        ),
        script_type: str = typer.Option(
            None, "--script", help="Script type to use: sh, ps, or py"
        ),
        ignore_agent_tools: bool = typer.Option(
            False,
            "--ignore-agent-tools",
            help="Skip checks for coding agent tools like Claude Code",
        ),
        here: bool = typer.Option(
            False,
            "--here",
            help="Initialize project in the current directory instead of creating a new one",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            help="Force merge/overwrite when using --here (skip confirmation)",
        ),
        non_interactive: bool = typer.Option(
            False,
            "--non-interactive",
            help=(
                "Never prompt. Use documented defaults for unspecified "
                "selections and fail instead of hanging when a choice has no "
                "safe default. Required for agent harnesses that allocate a "
                "PTY but cannot send arrow-key input."
            ),
        ),
        skip_tls: bool = typer.Option(
            False,
            "--skip-tls",
            help="Deprecated (no-op). Previously: skip SSL/TLS verification.",
            hidden=True,
        ),
        debug: bool = typer.Option(
            False,
            "--debug",
            help="Deprecated. Previously: show verbose diagnostic output; currently only prints additional diagnostic details on failure.",
            hidden=True,
        ),
        github_token: str = typer.Option(
            None,
            "--github-token",
            help="Deprecated (no-op). Previously: GitHub token for API requests.",
            hidden=True,
        ),
        offline: bool = typer.Option(
            False,
            "--offline",
            help="Deprecated (no-op). All scaffolding now uses bundled assets.",
            hidden=True,
        ),
        preset: str = typer.Option(
            None,
            "--preset",
            help="Install a preset during initialization (by preset ID)",
        ),
        integration: str = typer.Option(
            None,
            "--integration",
            help="AI coding agent integration to use (e.g. --integration copilot). See 'specify check' for available integrations.",
        ),
        integration_options: str = typer.Option(
            None,
            "--integration-options",
            help='Options for the integration (e.g. --integration-options="--commands-dir .myagent/cmds")',
        ),
        extensions: list[str] | None = typer.Option(
            None,
            "--extension",
            help="Install an extension during initialization (bundled name, local path, or HTTPS URL). Repeatable.",
        ),
        trust_extension_urls: bool = typer.Option(
            False,
            "--trust-extension-urls",
            help="Pre-authorize installing extensions from external URLs without the interactive trust prompt (required for non-interactive URL installs).",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview initialization changes without writing to the target project.",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Emit the dry-run preview as a single JSON document.",
        ),
    ):
        """
        Initialize a new Specify project.

        Project files are scaffolded from assets bundled inside the specify-cli
        package, so initialization does not need network access and templates
        match the installed CLI version.

        This command will:
        1. Check that required tools are installed
        2. Let you choose your coding agent integration, or default to Copilot
           in non-interactive sessions (no TTY, or --non-interactive)
        3. Install bundled Spec Kit templates, scripts, workflow, and shared
           project infrastructure
        4. Set up coding agent integration commands and optional presets

        Examples:
            specify init my-project
            specify init my-project --integration claude
            specify init --ignore-agent-tools my-project
            specify init . --integration claude         # Initialize in current directory
            specify init .                     # Initialize in current directory (interactive integration selection)
            specify init --here --integration claude    # Alternative syntax for current directory
            specify init --here --integration codex --integration-options="--skills"
            specify init --here --integration codebuddy
            specify init --here --integration vibe      # Initialize with Mistral Vibe support
            specify init --here
            specify init --here --force  # Skip confirmation when current directory not empty
            specify init my-project --non-interactive  # CI/agent: defaults, no prompts
            specify init --here --force --non-interactive --integration claude  # Scripted init, no hang
            specify init my-project --integration claude   # Claude installs skills by default
            specify init --here --integration gemini
            specify init my-project --integration generic --integration-options="--commands-dir .myagent/commands/"  # Bring your own agent; requires --commands-dir
            specify init my-project --integration claude --preset healthcare-compliance  # With preset
            specify init my-project --integration copilot --extension git  # With bundled extension
            specify init my-project --extension git --extension selftest  # Multiple extensions
            specify init my-project --extension ./my-extensions/custom-ext  # Local path extension
            specify init my-project --extension https://example.com/extensions/my-ext.zip --trust-extension-urls  # URL extension (non-interactive)
        """
        # Lazy imports to avoid circular dependency — __init__.py imports this module
        from .. import (
            _install_shared_infra_or_exit,
            _print_cli_warning,
            ensure_executable_scripts,
            save_init_options,
        )
        from ..integration_runtime import (
            invoke_prefix_for_integration as _invoke_prefix_for_integration,
            with_integration_setting as _with_integration_setting,
        )
        from ..integrations._commands import (
            _parse_integration_options,
            _write_integration_json,
        )

        if not (dry_run and json_output):
            show_banner()

        if json_output and not dry_run:
            console.print("[red]Error:[/red] --json requires --dry-run")
            raise typer.Exit(1)

        from ..integrations import INTEGRATION_REGISTRY, get_integration

        if integration:
            resolved_integration = get_integration(integration)
            if not resolved_integration:
                message = f"Unknown integration: '{integration}'"
                if dry_run and json_output:
                    _raise_dry_run_json_error(
                        message, project_name=project_name, here=here
                    )
                console.print(
                    f"[red]Error:[/red] Unknown integration: "
                    f"'{_escape_markup(str(integration))}'"
                )
                available = ", ".join(sorted(INTEGRATION_REGISTRY))
                console.print(f"[yellow]Available integrations:[/yellow] {available}")
                raise typer.Exit(1)

        if project_name == ".":
            here = True
            project_name = None

        if here and project_name:
            if dry_run and json_output:
                _raise_dry_run_json_error(
                    "Cannot specify both project name and --here flag",
                    project_name=project_name,
                    here=here,
                )
            console.print(
                "[red]Error:[/red] Cannot specify both project name and --here flag"
            )
            raise typer.Exit(1)

        if not here and not project_name:
            if dry_run and json_output:
                _raise_dry_run_json_error(
                    "Must specify either a project name, use '.' for current "
                    "directory, or use --here flag",
                    project_name=project_name,
                    here=here,
                )
            console.print(
                "[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag"
            )
            raise typer.Exit(1)

        dir_existed_before = False
        directory_conflict = False
        staging_confirmation_accepted = _staging_confirmation_is_accepted()
        if here:
            project_name = Path.cwd().name
            project_path = Path.cwd()
            dir_existed_before = True

            existing_items = list(project_path.iterdir())
            if existing_items:
                if not (dry_run and json_output):
                    console.print(
                        f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)"
                    )
                if dry_run and not force:
                    directory_conflict = True
                elif force:
                    # Proceeding: the merge/overwrite warning is accurate here.
                    if not (dry_run and json_output):
                        console.print(
                            "[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]"
                        )
                        console.print(
                            "[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]"
                        )
                elif non_interactive and not staging_confirmation_accepted:
                    console.print(
                        "[red]Error:[/red] Current directory is not empty and "
                        "--non-interactive was set. Re-run with "
                        "[bold]--force[/bold] to merge into it."
                    )
                    raise typer.Exit(1)
                elif not staging_confirmation_accepted:
                    # Fold the merge risk into the confirmation prompt rather than
                    # printing it unconditionally first: on the EOF/no-input path
                    # below the command exits without changing anything, so a
                    # standalone "will be merged" line would mislead. Interactive
                    # users still see the risk as part of the question.
                    #
                    # Call typer.confirm normally so piped y/n is honored — e.g.
                    # `echo y | specify init --here` keeps reaching the
                    # non-destructive preserve-merge path.
                    try:
                        proceed = typer.confirm(
                            "Template files will be merged with existing content "
                            "and may overwrite existing files. Do you want to continue?"
                        )
                    except (typer.Abort, EOFError):
                        # typer.confirm raises Abort for BOTH an interactive Ctrl+C
                        # and an EOF on closed/empty stdin. Distinguish them: a real
                        # TTY cancellation is a normal exit (0, "cancelled"), while a
                        # missing-input EOF (non-interactive) becomes an actionable
                        # error pointing at --force.
                        if _stdin_is_interactive():
                            console.print("[yellow]Operation cancelled[/yellow]")
                            raise typer.Exit(0) from None
                        console.print(
                            "[red]Error:[/red] Current directory is not empty and no "
                            "confirmation input is available. Re-run with "
                            "[bold]--force[/bold] to merge into it."
                        )
                        raise typer.Exit(1) from None
                    if not proceed:
                        console.print("[yellow]Operation cancelled[/yellow]")
                        raise typer.Exit(0)
        else:
            project_path = Path(project_name).resolve()
            dir_existed_before = project_path.exists()
            if project_path.exists():
                safe_name = _escape_markup(str(project_name))
                if not project_path.is_dir():
                    if dry_run and json_output:
                        _raise_dry_run_json_error(
                            f"'{project_name}' exists but is not a directory",
                            project_name=project_name,
                            here=here,
                        )
                    console.print(
                        f"[red]Error:[/red] '{safe_name}' exists but is not a directory."
                    )
                    raise typer.Exit(1)
                existing_items = list(project_path.iterdir())
                if dry_run and not force:
                    directory_conflict = True
                elif force:
                    if existing_items and not (dry_run and json_output):
                        console.print(
                            f"[yellow]Warning:[/yellow] Directory '{safe_name}' is not empty ({len(existing_items)} items)"
                        )
                        console.print(
                            "[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]"
                        )
                    if not (dry_run and json_output):
                        console.print(
                            f"[cyan]--force supplied: merging into existing directory '[cyan]{safe_name}[/cyan]'[/cyan]"
                        )
                elif not staging_confirmation_accepted:
                    error_panel = Panel(
                        f"Directory already exists: '[cyan]{safe_name}[/cyan]'\n"
                        "Please choose a different project name or remove the existing directory.\n"
                        "Use [bold]--force[/bold] to merge into the existing directory.",
                        title="[red]Directory Conflict[/red]",
                        border_style="red",
                        padding=(1, 2),
                    )
                    console.print()
                    console.print(error_panel)
                    raise typer.Exit(1)

        if integration:
            if integration not in AGENT_CONFIG:
                if dry_run and json_output:
                    _raise_dry_run_json_error(
                        f"Invalid integration '{integration}'",
                        project_name=project_name,
                        here=here,
                    )
                console.print(
                    f"[red]Error:[/red] Invalid integration '{_escape_markup(str(integration))}'. Choose from: {', '.join(AGENT_CONFIG.keys())}"
                )
                raise typer.Exit(1)
            selected_ai = integration
        elif not _prompts_allowed(non_interactive):
            default_integration = resolve_default_init_integration()
            if not (dry_run and json_output):
                console.print(
                    f"[dim]Non-interactive session detected: defaulting to '{default_integration}'. "
                    "Use --integration to choose a different agent.[/dim]"
                )
            selected_ai = default_integration
        else:
            ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
            selected_ai = select_with_arrows(
                ai_choices,
                "Choose your coding agent integration:",
                resolve_default_init_integration(),
                flag_hint="--integration <agent>",
            )

        if not integration:
            resolved_integration = get_integration(selected_ai)
            if not resolved_integration:
                console.print(f"[red]Error:[/red] Unknown agent '{selected_ai}'")
                raise typer.Exit(1)

        if selected_ai == "generic" and not integration_options:
            if dry_run and json_output:
                _raise_dry_run_json_error(
                    "--integration generic requires --integration-options "
                    "with --commands-dir",
                    project_name=project_name,
                    here=here,
                )
            console.print(
                "[red]Error:[/red] --integration generic requires --integration-options with --commands-dir"
            )
            console.print(
                '[dim]Example: specify init my-project --integration generic --integration-options="--commands-dir .myagent/commands/"[/dim]'
            )
            raise typer.Exit(1)

        current_dir = Path.cwd()

        setup_lines = [
            "[cyan]Specify Project Setup[/cyan]",
            "",
            f"{'Project':<15} [green]{_escape_markup(project_path.name)}[/green]",
            f"{'Working Path':<15} [dim]{_escape_markup(str(current_dir))}[/dim]",
        ]

        if not here:
            setup_lines.append(
                f"{'Target Path':<15} [dim]{_escape_markup(str(project_path))}[/dim]"
            )

        if not (dry_run and json_output):
            console.print(
                Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2))
            )

        if not ignore_agent_tools:
            agent_config = AGENT_CONFIG.get(selected_ai)
            if agent_config and agent_config["requires_cli"]:
                install_url = agent_config["install_url"]
                if not check_tool(selected_ai):
                    if dry_run and json_output:
                        _raise_dry_run_json_error(
                            f"{selected_ai} not found; {agent_config['name']} is "
                            "required to continue with this project type",
                            project_name=project_name,
                            here=here,
                        )
                    error_panel = Panel(
                        f"[cyan]{selected_ai}[/cyan] not found\n"
                        f"Install from: [cyan]{install_url}[/cyan]\n"
                        f"{agent_config['name']} is required to continue with this project type.\n\n"
                        "Tip: Use [cyan]--ignore-agent-tools[/cyan] to skip this check",
                        title="[red]Agent Detection Error[/red]",
                        border_style="red",
                        padding=(1, 2),
                    )
                    console.print()
                    console.print(error_panel)
                    raise typer.Exit(1)

        if script_type:
            if script_type not in SCRIPT_TYPE_CHOICES:
                if dry_run and json_output:
                    _raise_dry_run_json_error(
                        f"Invalid script type '{script_type}'",
                        project_name=project_name,
                        here=here,
                    )
                console.print(
                    f"[red]Error:[/red] Invalid script type '{_escape_markup(str(script_type))}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}"
                )
                raise typer.Exit(1)
            selected_script = script_type
        else:
            default_script = "ps" if os.name == "nt" else "sh"

            if _prompts_allowed(non_interactive):
                selected_script = select_with_arrows(
                    SCRIPT_TYPE_CHOICES,
                    "Choose script type (or press Enter)",
                    default_script,
                    flag_hint="--script sh|ps|py",
                )
            else:
                selected_script = default_script

        if not (dry_run and json_output):
            console.print(f"[cyan]Selected coding agent integration:[/cyan] {selected_ai}")
            console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")

        if dry_run:
            gate = (
                "confirmation_required"
                if here and directory_conflict
                else "force_required"
                if directory_conflict
                else "none"
            )
            _preview_init(
                project_path=project_path,
                gate=gate,
                force=force,
                here=here,
                script_type=selected_script,
                selected_integration=selected_ai,
                ignore_agent_tools=ignore_agent_tools,
                preset=preset,
                integration_options=integration_options,
                extensions=extensions,
                trust_extension_urls=trust_extension_urls,
                json_output=json_output,
            )
            return

        tracker = StepTracker("Initialize Specify Project")

        tracker.add("precheck", "Check required tools")
        tracker.complete("precheck", "ok")
        tracker.add("ai-select", "Select coding agent integration")
        tracker.complete("ai-select", f"{selected_ai}")
        tracker.add("script-select", "Select script type")
        tracker.complete("script-select", selected_script)

        tracker.add("integration", "Install integration")
        tracker.add("shared-infra", "Install shared infrastructure")

        for key, label in [
            ("chmod", "Ensure scripts executable"),
            ("constitution", "Constitution setup"),
            ("workflow", "Install bundled workflow"),
        ]:
            tracker.add(key, label)

        if extensions:
            for i, ext_spec in enumerate(extensions):
                tracker.add(
                    f"extension-{i}", f"Install extension: {_escape_markup(ext_spec)}"
                )

        tracker.add("final", "Finalize")

        # Resolve trust for URL-based extensions BEFORE entering the Live
        # display: the confirmation prompt cannot be shown/answered underneath
        # the Rich Live spinner. URL installs are default-deny unless the user
        # confirms interactively or passes --trust-extension-urls.
        extension_url_approvals: dict[str, bool] = {}
        if extensions:
            url_specs = [e for e in extensions if _ext_spec_is_url(e)]
            if url_specs:
                extension_url_approvals = _confirm_extension_url_trust(
                    url_specs,
                    trust_override=trust_extension_urls,
                    allow_prompt=_prompts_allowed(non_interactive),
                )

        # Disable transient mode on Windows: PowerShell 5.1's legacy console
        # hangs when Rich tries to restore cursor state via VT escape sequences.
        _transient = sys.platform != "win32"

        with Live(
            tracker.render(), console=console, refresh_per_second=8, transient=_transient
        ) as live:
            tracker.attach_refresh(lambda: live.update(tracker.render()))
            try:
                from ..integrations.manifest import IntegrationManifest

                tracker.start("integration")
                manifest = IntegrationManifest(
                    resolved_integration.key,
                    project_path,
                    version=get_speckit_version(),
                )

                integration_parsed_options: dict[str, Any] = {}
                if integration_options:
                    extra = _parse_integration_options(
                        resolved_integration, integration_options
                    )
                    if extra:
                        integration_parsed_options.update(extra)

                from ..events import resolve_events
                events_map = resolve_events(
                    resolved_integration.key,
                    resolved_integration.config,
                    project_path,
                    integration_parsed_options or None,
                )
                resolved_integration.setup(
                    project_path,
                    manifest,
                    parsed_options=integration_parsed_options or None,
                    script_type=selected_script,
                    raw_options=integration_options,
                    events=events_map,
                )
                manifest.save()

                if force:
                    from ..integrations._helpers import (
                        _register_extensions_for_agent,
                        _register_presets_for_agent,
                    )

                    _register_extensions_for_agent(
                        project_path,
                        resolved_integration.key,
                        force=True,
                        continuing=(
                            "The project was re-initialized, but installed extensions"
                            " may need re-registration."
                        ),
                    )
                    _register_presets_for_agent(
                        project_path,
                        resolved_integration.key,
                        continuing=(
                            "The project was re-initialized, but installed presets"
                            " may need re-registration."
                        ),
                    )

                integration_settings = _with_integration_setting(
                    {},
                    resolved_integration.key,
                    resolved_integration,
                    script_type=selected_script,
                    raw_options=integration_options,
                    parsed_options=integration_parsed_options or None,
                    project_root=project_path,
                )
                _write_integration_json(
                    project_path,
                    resolved_integration.key,
                    [resolved_integration.key],
                    integration_settings,
                )

                tracker.complete(
                    "integration",
                    resolved_integration.config.get("name", resolved_integration.key),
                )

                tracker.start("shared-infra")
                _install_shared_infra_or_exit(
                    project_path,
                    selected_script,
                    tracker=tracker,
                    force=force,
                    invoke_separator=resolved_integration.effective_invoke_separator(
                        integration_parsed_options, project_root=project_path
                    ),
                    invoke_prefix=_invoke_prefix_for_integration(
                        resolved_integration,
                        resolved_integration.key,
                        integration_parsed_options,
                        project_path,
                    ),
                )
                tracker.complete(
                    "shared-infra", f"scripts ({selected_script}) + templates"
                )

                try:
                    bundled_wf = _locate_bundled_workflow("speckit")
                    if bundled_wf:
                        from ..workflows.catalog import WorkflowRegistry
                        from ..workflows.engine import WorkflowDefinition

                        wf_registry = WorkflowRegistry(project_path)
                        if wf_registry.is_installed("speckit"):
                            tracker.complete("workflow", "already installed")
                            _record_init_plan_action(
                                "skip",
                                ".specify/workflows/speckit/workflow.yml",
                                "workflow",
                                "speckit",
                            )
                        else:
                            import shutil as _shutil

                            dest_wf = (
                                project_path / ".specify" / "workflows" / "speckit"
                            )
                            dest_wf.mkdir(parents=True, exist_ok=True)
                            _shutil.copy2(
                                bundled_wf / "workflow.yml",
                                dest_wf / "workflow.yml",
                            )
                            definition = WorkflowDefinition.from_yaml(
                                dest_wf / "workflow.yml"
                            )
                            wf_registry.add(
                                "speckit",
                                {
                                    "name": definition.name,
                                    "version": definition.version,
                                    "description": definition.description,
                                    "source": "bundled",
                                },
                            )
                            tracker.complete("workflow", "speckit installed")
                    else:
                        tracker.skip("workflow", "bundled workflow not found")
                except Exception as wf_err:
                    sanitized_wf = str(wf_err).replace("\n", " ").strip()
                    _record_init_plan_failure("workflow", "speckit", sanitized_wf)
                    tracker.error("workflow", f"install failed: {sanitized_wf[:120]}")

                init_opts = {
                    "ai": selected_ai,
                    "integration": resolved_integration.key,
                    "here": here,
                    "script": selected_script,
                    "feature_numbering": "sequential",
                    "speckit_version": get_speckit_version(),
                }
                if resolved_integration.is_skills_mode(
                    integration_parsed_options or None, project_root=project_path
                ):
                    init_opts["ai_skills"] = True
                save_init_options(project_path, init_opts)

                for chmod_failure in ensure_executable_scripts(
                    project_path, tracker=tracker
                ):
                    _record_init_plan_failure("chmod", chmod_failure, chmod_failure)

                if preset:
                    try:
                        from ..presets import PresetCatalog, PresetError, PresetManager

                        preset_manager = PresetManager(project_path)
                        speckit_ver = get_speckit_version()

                        local_path = Path(preset).resolve()
                        if local_path.is_dir() and (local_path / "preset.yml").exists():
                            preset_manager.install_from_directory(
                                local_path, speckit_ver
                            )
                        else:
                            bundled_path = _locate_bundled_preset(preset)
                            if bundled_path:
                                preset_manager.install_from_directory(
                                    bundled_path, speckit_ver
                                )
                            else:
                                preset_catalog = PresetCatalog(project_path)
                                pack_info = preset_catalog.get_pack_info(preset)
                                if not pack_info:
                                    _record_init_plan_failure(
                                        "preset",
                                        preset,
                                        f"Preset '{preset}' not found in catalog",
                                    )
                                    console.print(
                                        f"[yellow]Warning:[/yellow] Preset '{preset}' not found in catalog. Skipping."
                                    )
                                elif pack_info.get("bundled") and not pack_info.get(
                                    "download_url"
                                ):
                                    from ..extensions import REINSTALL_COMMAND

                                    _record_init_plan_failure(
                                        "preset",
                                        preset,
                                        "bundled preset not found in installed package",
                                    )
                                    console.print(
                                        f"[yellow]Warning:[/yellow] Preset '{preset}' is bundled with spec-kit "
                                        f"but could not be found in the installed package."
                                    )
                                    console.print(
                                        "This usually means the spec-kit installation is incomplete or corrupted."
                                    )
                                    console.print(
                                        f"Try reinstalling: {REINSTALL_COMMAND}"
                                    )
                                else:
                                    zip_path = None
                                    try:
                                        zip_path = preset_catalog.download_pack(preset)
                                        preset_manager.install_from_zip(
                                            zip_path, speckit_ver
                                        )
                                    except PresetError as preset_err:
                                        _record_init_plan_failure(
                                            "preset", preset, str(preset_err)
                                        )
                                        _print_cli_warning(
                                            "install",
                                            "preset",
                                            preset,
                                            preset_err,
                                            continuing="Continuing without the optional preset.",
                                        )
                                    finally:
                                        if zip_path is not None:
                                            try:
                                                zip_path.unlink(missing_ok=True)
                                            except OSError:
                                                pass
                    except Exception as preset_err:
                        _record_init_plan_failure("preset", preset, str(preset_err))
                        _print_cli_warning(
                            "install",
                            "preset",
                            preset,
                            preset_err,
                            continuing="Continuing without the optional preset.",
                        )

                # Install extensions specified via --extension
                if extensions:
                    from ..extensions._commands import _refresh_events_and_warn

                    speckit_ver = get_speckit_version()
                    any_extension_installed = False
                    for i, ext_spec in enumerate(extensions):
                        tracker.start(f"extension-{i}")
                        # Skip URL extensions the user did not confirm as trusted
                        # (default-deny; resolved before the Live display).
                        if _ext_spec_is_url(ext_spec) and not extension_url_approvals.get(
                            ext_spec, False
                        ):
                            tracker.error(
                                f"extension-{i}",
                                "skipped: untrusted URL not confirmed "
                                "(use --trust-extension-urls)",
                            )
                            continue
                        try:
                            status_msg = _install_extension_during_init(
                                project_path, ext_spec, speckit_ver
                            )
                            tracker.complete(f"extension-{i}", status_msg)
                            any_extension_installed = True
                        except Exception as ext_err:
                            sanitized_ext = str(ext_err).replace("\n", " ").strip()
                            _record_init_plan_failure(
                                "extension", ext_spec, sanitized_ext
                            )
                            tracker.error(
                                f"extension-{i}",
                                f"failed: {_escape_markup(sanitized_ext[:120])}",
                            )

                    # Refresh native event configuration once after the batch so
                    # that an extension declaring ``events:`` has its hooks
                    # activated, mirroring the ``extension add`` path.
                    if any_extension_installed:
                        _refresh_events_and_warn(project_path)

                # Seed the constitution AFTER preset installation so that a
                # preset-provided constitution-template (resolved via the
                # priority stack) wins over the core template.
                ensure_constitution_from_template(project_path, tracker=tracker)

                tracker.complete("final", "project ready")
            except (typer.Exit, SystemExit):
                raise
            except Exception as e:
                tracker.error("final", str(e))
                console.print(
                    Panel(
                        f"Initialization failed: {e}",
                        title="Failure",
                        border_style="red",
                    )
                )
                if debug:
                    _env_pairs = [
                        ("Python", sys.version.split()[0]),
                        ("Platform", sys.platform),
                        ("CWD", str(Path.cwd())),
                    ]
                    _label_width = max(len(k) for k, _ in _env_pairs)
                    env_lines = [
                        f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]"
                        for k, v in _env_pairs
                    ]
                    console.print(
                        Panel(
                            "\n".join(env_lines),
                            title="Debug Environment",
                            border_style="magenta",
                        )
                    )
                if not here and project_path.exists() and not dir_existed_before:
                    shutil.rmtree(project_path)
                raise typer.Exit(1)
            finally:
                pass

        if _transient:
            console.print(tracker.render())
        console.print("\n[bold green]Project ready.[/bold green]")

        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config:
            agent_folder = agent_config["folder"] or integration_parsed_options.get(
                "commands_dir"
            )
            if agent_folder:
                security_notice = Panel(
                    f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
                    f"Consider adding [cyan]{_escape_markup(str(agent_folder))}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
                    title="[yellow]Agent Folder Security[/yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                )
                console.print()
                console.print(security_notice)

        steps_lines = []
        if not here:
            steps_lines.append(
                f"1. Go to the project folder: [cyan]cd {_escape_markup(_shell_quote_arg(str(project_name)))}[/cyan]"
            )
            step_num = 2
        else:
            steps_lines.append("1. You're already in the project directory!")
            step_num = 2

        _is_skills_integration = resolved_integration.is_skills_mode(
            integration_parsed_options or None, project_root=project_path
        )

        codex_skill_mode = selected_ai == "codex" and _is_skills_integration
        zcode_skill_mode = selected_ai == "zcode" and _is_skills_integration
        claude_skill_mode = selected_ai == "claude" and _is_skills_integration
        kimi_skill_mode = selected_ai == "kimi"
        agy_skill_mode = selected_ai == "agy" and _is_skills_integration
        trae_skill_mode = selected_ai == "trae"
        cursor_agent_skill_mode = (
            selected_ai == "cursor-agent" and _is_skills_integration
        )
        copilot_skill_mode = selected_ai == "copilot" and _is_skills_integration
        devin_skill_mode = selected_ai == "devin"
        zed_skill_mode = selected_ai == "zed" and _is_skills_integration
        muse_skill_mode = selected_ai == "muse" and _is_skills_integration
        grok_skill_mode = selected_ai == "grok" and _is_skills_integration
        dsh_skill_mode = selected_ai == "dsh" and _is_skills_integration
        cline_skill_mode = selected_ai == "cline"
        forge_skill_mode = selected_ai == "forge"
        bob_skill_mode = selected_ai == "bob" and _is_skills_integration
        native_skill_mode = (
            codex_skill_mode
            or zcode_skill_mode
            or claude_skill_mode
            or kimi_skill_mode
            or agy_skill_mode
            or trae_skill_mode
            or cursor_agent_skill_mode
            or copilot_skill_mode
            or devin_skill_mode
            or zed_skill_mode
            or muse_skill_mode
            or grok_skill_mode
            or dsh_skill_mode
            or bob_skill_mode
        )

        if codex_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Codex in this project directory; spec-kit skills were installed to [cyan].agents/skills[/cyan]"
            )
            step_num += 1
        if zcode_skill_mode:
            steps_lines.append(
                f"{step_num}. Start ZCode in this project directory; spec-kit skills were installed to [cyan].zcode/skills[/cyan]"
            )
            step_num += 1
        if claude_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Claude in this project directory; spec-kit skills were installed to [cyan].claude/skills[/cyan]"
            )
            step_num += 1
        if cursor_agent_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Cursor Agent in this project directory; spec-kit skills were installed to [cyan].cursor/skills[/cyan]"
            )
            step_num += 1
        if devin_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Devin in this project directory; spec-kit skills were installed to [cyan].devin/skills[/cyan]"
            )
            step_num += 1
        if zed_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Zed in this project directory; spec-kit skills were installed to [cyan].agents/skills[/cyan]"
            )
            step_num += 1
        if muse_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Muse Code in this project directory; spec-kit skills were installed to [cyan].agents/skills[/cyan]"
            )
            step_num += 1
        if grok_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Grok Build in this project directory; spec-kit skills were installed to [cyan].grok/skills[/cyan]"
            )
            step_num += 1
        if dsh_skill_mode:
            steps_lines.append(
                f"{step_num}. Start DSH ([cyan]dsh web[/cyan]) in this project directory; spec-kit skills were installed to [cyan].dsh/skills[/cyan]"
            )
            step_num += 1
        if bob_skill_mode:
            steps_lines.append(
                f"{step_num}. Start Bob in this project directory; spec-kit skills were installed to [cyan].bob/skills[/cyan]"
            )
            step_num += 1
        usage_label = "skills" if native_skill_mode else "slash commands"

        from .._invocation_style import (
            is_dollar_skills_agent as _is_dollar_skills_agent,
            is_slash_skills_agent as _is_slash_skills_agent,
        )

        # `_is_skills_integration` means the integration is installed in
        # skills mode, which is the semantic equivalent of `ai_skills_enabled`
        # used by `is_slash_skills_agent()`.
        _ai_skills_enabled = _is_skills_integration

        def _display_cmd(name: str) -> str:
            if _is_dollar_skills_agent(selected_ai, _ai_skills_enabled):
                return f"$speckit-{name}"
            if kimi_skill_mode:
                return f"/skill:speckit-{name}"
            if (
                _is_slash_skills_agent(selected_ai, _ai_skills_enabled)
                or cline_skill_mode
                or forge_skill_mode
            ):
                return f"/speckit-{name}"
            return f"/speckit.{name}"

        steps_lines.append(
            f"{step_num}. Start using {usage_label} with your coding agent:"
        )

        steps_lines.append(
            f"   {step_num}.1 [cyan]{_display_cmd('constitution')}[/] - Establish project principles"
        )
        steps_lines.append(
            f"   {step_num}.2 [cyan]{_display_cmd('specify')}[/] - Create baseline specification"
        )
        steps_lines.append(
            f"   {step_num}.3 [cyan]{_display_cmd('plan')}[/] - Create implementation plan"
        )
        steps_lines.append(
            f"   {step_num}.4 [cyan]{_display_cmd('tasks')}[/] - Generate actionable tasks"
        )
        steps_lines.append(
            f"   {step_num}.5 [cyan]{_display_cmd('implement')}[/] - Execute implementation"
        )
        steps_lines.append(
            f"   {step_num}.6 [cyan]{_display_cmd('converge')}[/] - Assess the codebase and append remaining work as tasks"
        )

        steps_panel = Panel(
            "\n".join(steps_lines),
            title="Next Steps",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print()
        console.print(steps_panel)

        enhancement_intro = (
            "Optional skills that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]"
            if native_skill_mode
            else "Optional commands that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]"
        )
        enhancement_lines = [
            enhancement_intro,
            "",
            f"○ [cyan]{_display_cmd('clarify')}[/] [bright_black](optional)[/bright_black] - Ask structured questions to de-risk ambiguous areas before planning (run before [cyan]{_display_cmd('plan')}[/] if used)",
            f"○ [cyan]{_display_cmd('analyze')}[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency & alignment report (after [cyan]{_display_cmd('tasks')}[/], before [cyan]{_display_cmd('implement')}[/])",
            f"○ [cyan]{_display_cmd('checklist')}[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]{_display_cmd('plan')}[/])",
        ]
        enhancements_title = (
            "Enhancement Skills" if native_skill_mode else "Enhancement Commands"
        )
        enhancements_panel = Panel(
            "\n".join(enhancement_lines),
            title=enhancements_title,
            border_style="cyan",
            padding=(1, 2),
        )
        console.print()
        console.print(enhancements_panel)
