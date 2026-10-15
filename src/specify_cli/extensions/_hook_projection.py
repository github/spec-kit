"""Validated projection of extension hooks for future dispatchers."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from .._init_options import load_init_options
from ..integrations._file_changes import changing_file, unlink, write_bytes
from . import DEFAULT_HOOK_PRIORITY, normalize_priority

_EVENT = re.compile(r"(before|after)_[a-z0-9][a-z0-9_]*\Z")


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
            "only letters, digits, or underscores. Normalize hyphens to underscores "
            "(for example, my-extension -> my_extension). Rename legacy events such "
            "as custom:after before installing or refreshing."
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
    _check_paths(config_file)
    if cache.exists():
        with changing_file(cache, removal=True):
            shutil.rmtree(cache)


def _write_digest(directory: Path, name: str, payload: bytes) -> None:
    write_bytes(directory / name, payload)
    write_bytes(
        directory / f"{name}.sha256",
        (hashlib.sha256(payload).hexdigest() + "\n").encode("ascii"),
    )


def publish(config_file: Path, config: dict[str, Any], *, preserve_source: bool = False) -> None:
    """Write the validated hook configuration and projection directly."""
    if not preserve_source:
        projected = project_hooks(config)
        rendered = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True).encode("utf-8")
    root = config_file.parent
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
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not preserve_source:
            write_bytes(config_file, rendered)
        cache.mkdir(exist_ok=True)
        retained = {"source.yml", "events.txt", "events.txt.sha256"}
        for event, payload in projected.items():
            name = f"{event}.json"
            _write_digest(cache, name, payload)
            retained.update((name, f"{name}.sha256"))
        _write_digest(cache, "events.txt", "".join(f"{event}\n" for event in projected).encode("utf-8"))
        write_bytes(cache / "source.yml", source)
        for child in cache.iterdir():
            if child.name not in retained and child.name.endswith((".json", ".sha256")):
                unlink(child)
    except OSError as exc:
        raise OSError(
            f"Hook projection write failed ({exc}); .specify/extensions.yml or "
            ".specify/hook-dispatch/ may be incomplete. Repair the filesystem and "
            "extensions.yml if needed, then retry the extension operation or run "
            "`specify integration switch <current-key> --refresh-shared-infra`."
        ) from exc
