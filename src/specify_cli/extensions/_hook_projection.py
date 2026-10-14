"""Validated, transactional projection of extension hooks for future dispatchers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .._init_options import load_init_options
from ..integrations._file_changes import changing_file
from ..shared_infra import _exclusive_project_lock
from . import DEFAULT_HOOK_PRIORITY, normalize_priority

_EVENT = re.compile(r"(before|after)_[a-z0-9][a-z0-9_-]*\Z")


def projection_enabled(project_root: Path) -> bool:
    options = load_init_options(project_root)
    enabled = options.get("native_extension_hooks", False)
    if not isinstance(enabled, bool):
        raise ValueError(
            "Invalid native_extension_hooks in .specify/init-options.json: "
            "expected true or false"
        )
    return enabled


def validate_event_name(event: object) -> None:
    if (
        not isinstance(event, str)
        or not _EVENT.fullmatch(event)
        or len(event) + len(".json.sha256") > 255
    ):
        raise ValueError(
            f"Invalid extension hook event {event!r}: use before_<command_name> "
            "or after_<command_name> with a lowercase command name containing "
            "letters, digits, underscores, or hyphens. "
            "Rename legacy events such as custom:after before installing or refreshing."
        )


def _cache_path(config_file: Path) -> Path:
    return config_file.parent / "hook-dispatch"


def _check_paths(config_file: Path) -> None:
    root = config_file.parent
    cache = _cache_path(config_file)
    if root.is_symlink() or config_file.is_symlink():
        raise ValueError("Refusing symlinked extension configuration")
    if cache.is_symlink() or (cache.exists() and not cache.is_dir()):
        raise ValueError("Refusing non-directory or symlinked hook projection")
    if cache.exists():
        for child in cache.iterdir():
            if child.is_symlink() or not child.is_file():
                raise ValueError(f"Refusing non-file hook projection entry: {child.name}")


def project_hooks(config: dict[str, Any]) -> dict[str, bytes]:
    """Render unconditionally eligible hooks in YAML declaration order."""
    hooks = config.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Invalid extension hooks: expected a mapping")
    projected: dict[str, bytes] = {}
    for event, entries in hooks.items():
        validate_event_name(event)
        if not isinstance(entries, list):
            raise ValueError(f"Invalid extension hooks.{event}: expected a list")
        selected = []
        for index, entry in enumerate(entries):
            label = f"hooks.{event}[{index}]"
            if not isinstance(entry, dict):
                raise ValueError(f"Invalid {label}: expected a mapping")
            for field in ("extension", "command"):
                if not isinstance(entry.get(field), str) or not entry[field]:
                    raise ValueError(f"Invalid {label}: missing {field}")
            for field in ("enabled", "optional"):
                if field in entry and not isinstance(entry[field], bool):
                    raise ValueError(f"Invalid {label}.{field}: expected a boolean")
            for field in ("condition", "description", "prompt"):
                if entry.get(field) is not None and not isinstance(entry[field], str):
                    raise ValueError(f"Invalid {label}.{field}: expected a string or null")
            if any(isinstance(value, str) and "\0" in value for value in entry.values()):
                raise ValueError(f"Invalid {label}: NUL character")
            if entry.get("enabled", True) is False or entry.get("condition"):
                continue
            priority = normalize_priority(entry.get("priority"))
            if priority > 2147483647:
                priority = DEFAULT_HOOK_PRIORITY
            selected.append({
                "extension": entry["extension"],
                "command": entry["command"],
                "optional": entry.get("optional", True),
                "description": entry.get("description") or "",
                "prompt": entry.get("prompt") or "",
                "priority": priority,
            })
        projected[event] = (
            json.dumps({"event": event, "hooks": selected}, ensure_ascii=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    return projected


def load_for_update(config_file: Path) -> dict[str, Any]:
    """Reject malformed existing state before extension lifecycle mutations."""
    _check_paths(config_file)
    if not config_file.exists():
        return {"installed": [], "settings": {"auto_execute_hooks": True}, "hooks": {}}
    try:
        config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Invalid extension configuration: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("Invalid extension configuration: expected a mapping")
    project_hooks(config)
    return config


def retire(config_file: Path) -> None:
    """Retire a prior projection when native hooks are no longer enabled."""
    cache = _cache_path(config_file)
    if not cache.exists() and not cache.is_symlink():
        return
    root = config_file.parent
    with changing_file(root / ".hook-dispatch.lock"), _exclusive_project_lock(
        root.parent, ".hook-dispatch.lock", context="hook projection"
    ):
        _check_paths(config_file)
        if cache.exists():
            with changing_file(cache, removal=True):
                shutil.rmtree(cache)


def _write_digest(directory: Path, name: str, payload: bytes) -> None:
    (directory / name).write_bytes(payload)
    (directory / f"{name}.sha256").write_text(
        hashlib.sha256(payload).hexdigest() + "\n", encoding="ascii"
    )


def publish(config_file: Path, config: dict[str, Any], *, preserve_source: bool = False) -> None:
    """Publish one complete projection and its YAML source, or restore the prior pair."""
    if not preserve_source:
        projected = project_hooks(config)
        rendered = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    root = config_file.parent
    root.mkdir(parents=True, exist_ok=True)
    with changing_file(root / ".hook-dispatch.lock"), _exclusive_project_lock(
        root.parent, ".hook-dispatch.lock", context="hook projection"
    ):
        _check_paths(config_file)
        if preserve_source:
            source = config_file.read_bytes()
            try:
                current = yaml.safe_load(source.decode("utf-8"))
            except (UnicodeError, yaml.YAMLError) as exc:
                raise ValueError(f"Invalid extension configuration: {exc}") from exc
            if not isinstance(current, dict):
                raise ValueError("Invalid extension configuration: expected a mapping")
            projected = project_hooks(current)
        else:
            source = rendered
        cache = _cache_path(config_file)
        old_config = config_file.read_bytes() if config_file.exists() else None
        stage = Path(tempfile.mkdtemp(prefix=".hook-stage-", dir=root))
        backup = root / f"{stage.name}.backup"
        moved = False
        installed = False
        try:
            if cache.exists():
                for child in cache.iterdir():
                    if child.name not in {"source.yml", "events.txt", "events.txt.sha256"} and not child.name.endswith((".json", ".sha256")):
                        shutil.copy2(child, stage / child.name)
            for event, payload in projected.items():
                _write_digest(stage, f"{event}.json", payload)
            _write_digest(stage, "events.txt", "".join(f"{event}\n" for event in projected).encode("utf-8"))
            (stage / "source.yml").write_bytes(source)
            with changing_file(cache):
                if cache.exists():
                    os.replace(cache, backup)
                    moved = True
                os.replace(stage, cache)
                installed = True
            if not preserve_source:
                temporary = root / f"{stage.name}.yml"
                try:
                    temporary.write_bytes(rendered)
                    with changing_file(config_file):
                        os.replace(temporary, config_file)
                finally:
                    temporary.unlink(missing_ok=True)
        except Exception as exc:
            try:
                if installed:
                    with changing_file(cache, removal=True):
                        shutil.rmtree(cache)
                if moved:
                    with changing_file(cache):
                        os.replace(backup, cache)
                if not preserve_source:
                    if old_config is None:
                        with changing_file(config_file, removal=True):
                            config_file.unlink(missing_ok=True)
                    elif config_file.read_bytes() != old_config:
                        with changing_file(config_file):
                            config_file.write_bytes(old_config)
            except Exception as rollback_exc:
                raise OSError(f"Hook projection publication failed ({exc}); rollback failed: {rollback_exc}") from exc
            raise
        finally:
            if stage.exists():
                shutil.rmtree(stage)
        if moved:
            try:
                shutil.rmtree(backup)
            except OSError as exc:
                logging.getLogger(__name__).warning(
                    "Hook projection committed; could not remove backup %s: %s",
                    backup,
                    exc,
                )
