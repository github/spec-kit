#!/usr/bin/env python3
"""Resolve extension hooks for a core command's before event."""

from __future__ import annotations

import argparse
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

    entries = config.get("hooks", {}).get(event, [])
    if not isinstance(entries, list):
        raise ValueError(f"Invalid .specify/extensions.yml: hooks.{event} must be a list")

    hooks = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid .specify/extensions.yml: hooks.{event}[{index}] must be a mapping")
        if "enabled" in entry and not isinstance(entry["enabled"], bool):
            raise ValueError(f"Invalid .specify/extensions.yml: hooks.{event}[{index}].enabled must be a boolean")
        if "optional" in entry and not isinstance(entry["optional"], bool):
            raise ValueError(f"Invalid .specify/extensions.yml: hooks.{event}[{index}].optional must be a boolean")
        if entry.get("enabled") is False or entry.get("condition"):
            continue
        extension, command = entry.get("extension"), entry.get("command")
        if not isinstance(extension, str) or not extension or not isinstance(command, str) or not command:
            raise ValueError(f"Invalid .specify/extensions.yml: hooks.{event}[{index}] needs extension and command")
        for field in ("description", "prompt"):
            if entry.get(field) is not None and not isinstance(entry[field], str):
                raise ValueError(f"Invalid .specify/extensions.yml: hooks.{event}[{index}].{field} must be a string")
        priority = entry.get("priority", 10)
        try:
            priority = int(priority) if not isinstance(priority, bool) else 10
        except (TypeError, ValueError, OverflowError):
            priority = 10
        if priority < 1:
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
