#!/usr/bin/env python3
"""Resolve extension hooks for a core command's before event."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_EVENT = re.compile(r"^(before|after)_[a-z][a-z0-9_]*$")


def resolve(event: str, project_root: Path) -> dict:
    """Return enabled, unconditional hooks in priority order."""
    if not _EVENT.fullmatch(event):
        raise ValueError(f"Invalid hook event: {event}")

    config_file = project_root / ".specify" / "extensions.yml"
    cache = project_root / ".specify" / "hook-dispatch"
    if cache.is_dir():
        try:
            source = config_file.read_bytes()
            if source != (cache / "source.yml").read_bytes():
                raise ValueError("Hook projection is stale; reinstall the extension or refresh the project")
            event_bytes = (cache / "events.txt").read_bytes()
            index_digest = (cache / "events.txt.sha256").read_text(encoding="utf-8").strip()
            if not re.fullmatch("[0-9a-f]{64}", index_digest) or hashlib.sha256(event_bytes).hexdigest() != index_digest:
                raise ValueError("Hook projection index is invalid; reinstall the extension or refresh the project")
            events = event_bytes.decode("utf-8").splitlines()
            projection = cache / f"{event}.json"
            if not projection.exists():
                if event in events:
                    raise ValueError("Hook projection is incomplete; reinstall the extension or refresh the project")
                result = {"event": event, "hooks": []}
            else:
                expected = (cache / f"{event}.sha256").read_text(encoding="utf-8").strip()
                payload = projection.read_bytes()
                if not re.fullmatch("[0-9a-f]{64}", expected) or hashlib.sha256(payload).hexdigest() != expected:
                    raise ValueError("Hook projection is invalid; reinstall the extension or refresh the project")
                result = json.loads(payload.decode("utf-8"))
            if source != config_file.read_bytes() or source != (cache / "source.yml").read_bytes():
                raise ValueError("Hook projection changed during resolution; retry the command")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Could not read hook projection: {exc}") from exc
        if not isinstance(result, dict) or result.get("event") != event or not isinstance(result.get("hooks"), list):
            raise ValueError("Invalid hook projection; reinstall the extension or refresh the project")
        for hook in result["hooks"]:
            if (not isinstance(hook, dict)
                or any(not isinstance(hook.get(field), str) or not hook[field]
                       for field in ("extension", "command"))
                or not isinstance(hook.get("optional"), bool)
                or not isinstance(hook.get("description"), str)
                or not isinstance(hook.get("prompt"), str)
                or not isinstance(hook.get("priority"), int)
                or isinstance(hook["priority"], bool)
                or hook["priority"] < 1):
                raise ValueError("Invalid hook projection; reinstall the extension or refresh the project")
        return result
    if config_file.exists():
        try:
            with config_file.open(encoding="utf-8") as handle:
                if handle.readline().strip() == "# Hook projection: .specify/hook-dispatch":
                    raise ValueError("Hook projection is missing; reinstall the extension or refresh the project")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"Could not read .specify/extensions.yml: {exc}") from exc
    if not config_file.exists():
        return {"event": event, "hooks": []}

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read .specify/extensions.yml") from exc

    try:
        config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Could not read .specify/extensions.yml: {exc}") from exc
    if not isinstance(config, dict) or not isinstance(config.get("hooks", {}), dict):
        raise ValueError("Invalid .specify/extensions.yml: expected a hooks mapping")

    hooks = []
    for hook_event, entries in config.get("hooks", {}).items():
        if not isinstance(entries, list):
            raise ValueError(f"Invalid .specify/extensions.yml: hooks.{hook_event} must be a list")
        for index, entry in enumerate(entries):
            label = f"hooks.{hook_event}[{index}]"
            if not isinstance(entry, dict):
                raise ValueError(f"Invalid .specify/extensions.yml: {label} must be a mapping")
            if any(isinstance(value, str) and "\0" in value for value in entry.values()):
                raise ValueError(f"Invalid .specify/extensions.yml: {label} contains a NUL character")
            for field in ("enabled", "optional"):
                if field in entry and not isinstance(entry[field], bool):
                    raise ValueError(f"Invalid .specify/extensions.yml: {label}.{field} must be a boolean")
            for field in ("condition", "description", "prompt"):
                if entry.get(field) is not None and not isinstance(entry[field], str):
                    raise ValueError(f"Invalid .specify/extensions.yml: {label}.{field} must be a string or null")
            for field in ("extension", "command"):
                if field in entry and (not isinstance(entry[field], str) or not entry[field]):
                    raise ValueError(f"Invalid .specify/extensions.yml: {label} needs extension and command")
            extension, command = entry.get("extension"), entry.get("command")
            if not extension or not command:
                raise ValueError(f"Invalid .specify/extensions.yml: {label} needs extension and command")
            if hook_event != event or entry.get("enabled") is False or entry.get("condition"):
                continue
            priority = entry.get("priority", 10)
            try:
                priority = int(priority) if not isinstance(priority, bool) else 10
            except (TypeError, ValueError, OverflowError):
                priority = 10
            if priority < 1 or priority > 2147483647:
                priority = 10
            hooks.append({
                "extension": extension,
                "command": command,
                "optional": entry.get("optional", True),
                "description": entry.get("description") or "",
                "prompt": entry.get("prompt") or "",
                "priority": priority,
            })
    hooks.sort(key=lambda hook: hook["priority"])
    return {"event": event, "hooks": hooks}


def main(phase: str = "before") -> int:
    parser = argparse.ArgumentParser(description=f"Resolve {phase} extension hooks")
    parser.add_argument("command", help="Core command name, e.g. plan")
    args = parser.parse_args()
    event = f"{phase}_{args.command}"
    try:
        result = resolve(event, Path.cwd())
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"event": event, "hooks": [], "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
