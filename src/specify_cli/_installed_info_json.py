"""Private JSON output helpers for installed preset and extension info.

``preset info --json`` and ``extension info --json`` describe one installed
pack. The top-level fields are the ``list --json`` item for that pack (see
``_installed_list_json``); its ``provides`` counts are replaced by one array
per contribution kind, so the detail view and the summary view never drift.
"""
from __future__ import annotations

from typing import Any

from ._installed_list_json import installed_list_item


def _find_installed(
    records: list[dict[str, Any]], key: str, kind: str, *, match_names: bool
) -> dict[str, Any]:
    """Return the installed record for an ID, or (optionally) a unique display name.

    The lookup mirrors the human-readable ``info`` commands: presets resolve by
    ID only, extensions also accept a case-insensitive display name.
    """
    for record in records:
        if record["id"] == key:
            return record
    by_name = []
    if match_names:
        by_name = [record for record in records if str(record["name"]).lower() == key.lower()]
    if len(by_name) == 1:
        return by_name[0]
    if by_name:
        raise ValueError(
            f"{kind.capitalize()} name '{key}' is ambiguous; use one of the IDs: "
            + ", ".join(sorted(str(record["id"]) for record in by_name))
        )
    raise ValueError(f"{kind.capitalize()} '{key}' is not installed")


def _contribution(entry: dict[str, Any], source: dict[str, str]) -> dict[str, Any]:
    """Return one command, template or script entry of an installed pack.

    ``source`` is the entry's provenance, the layer and the pack that provide
    it (#4213); where the pack was installed from is the top-level ``source``.
    """
    description = entry.get("description")
    return {
        "name": entry["name"],
        # ``description:`` with no value reads as None, and the preset manifest
        # does not check contribution descriptions
        "description": description if isinstance(description, str) else "",
        "source": dict(source),
        "sourcePath": entry["file"],
    }


def preset_info_item(records: list[dict[str, Any]], manager: Any, key: str) -> dict[str, Any]:
    """Return the JSON object for one installed preset."""
    record = _find_installed(records, key, "preset", match_names=False)
    manifest = manager.get_pack(record["id"])
    if manifest is None:
        raise ValueError(f"Preset '{record['id']}' has an unreadable manifest")

    item = installed_list_item(record, include_hooks=False)
    del item["provides"]
    groups: dict[str, list[dict[str, Any]]] = {"commands": [], "templates": [], "scripts": []}
    provenance = {"layer": "preset", "presetId": record["id"]}
    for template in manifest.templates:
        entry = _contribution(template, provenance)
        entry["strategy"] = template.get("strategy", "replace")
        groups[f"{template['type']}s"].append(entry)
    return {**item, **groups}


def extension_info_item(records: list[dict[str, Any]], manager: Any, key: str) -> dict[str, Any]:
    """Return the JSON object for one installed extension."""
    from .extensions import DEFAULT_HOOK_PRIORITY, coerce_hook_entries, normalize_priority

    record = _find_installed(records, key, "extension", match_names=True)
    manifest = manager.get_extension(record["id"])
    if manifest is None:
        raise ValueError(f"Extension '{record['id']}' has an unreadable manifest")

    item = installed_list_item(record, include_hooks=True)
    del item["provides"]
    provenance = {"layer": "extension", "extensionId": record["id"]}
    scripts = []
    for script in manifest.scripts:
        entry = _contribution(script, provenance)
        if "runtimes" in script:
            entry["runtimes"] = list(script["runtimes"])
        scripts.append(entry)

    # Read hooks the way hook registration does: per event, a later
    # declaration for the same command replaces the earlier one, and the
    # priority/optional defaults are the ones the hook executor applies.
    hooks = []
    for event_name, hook_config in manifest.hooks.items():
        by_command: dict[str, dict[str, Any]] = {}
        for entry in coerce_hook_entries(hook_config):
            if isinstance(entry, dict) and entry.get("command"):
                by_command.pop(entry["command"], None)
                by_command[entry["command"]] = entry
        for command, entry in by_command.items():
            hooks.append(
                {
                    "trigger": event_name,
                    "targetCommand": command,
                    "optional": bool(entry.get("optional", True)),
                    "priority": normalize_priority(entry.get("priority"), DEFAULT_HOOK_PRIORITY),
                }
            )

    return {
        **item,
        "commands": [_contribution(command, provenance) for command in manifest.commands],
        "templates": [_contribution(template, provenance) for template in manifest.templates],
        "scripts": scripts,
        "hooks": hooks,
    }
