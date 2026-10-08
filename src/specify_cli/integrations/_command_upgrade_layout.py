"""Layout-migration guards for ``specify integration upgrade``."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePath

def _manifest_tracks_skill_layout(manifest) -> bool:
    """Return True when *manifest* tracks any skills-layout artifact.

    A skill scaffold is written as ``.../speckit-<name>/SKILL.md``, so a
    manifest whose tracked files include a ``/SKILL.md`` key is in the skills
    layout; otherwise it is in the command layout. Used by ``upgrade`` to
    detect a dual-mode agent (e.g. Bob) flipping between the legacy commands
    layout and the skills layout so orphaned extension artifacts from the old
    layout can be reconciled.
    """
    return any(str(rel).endswith("/SKILL.md") for rel in manifest.files)


def _manifest_path_under(rel_path: str, root: str) -> bool:
    """Return True when manifest key *rel_path* is inside project-relative *root*."""
    normalized_root = PurePath(root).as_posix().strip("/")
    normalized_rel = PurePath(rel_path).as_posix().strip("/")
    if not normalized_root:
        return False
    return normalized_rel == normalized_root or normalized_rel.startswith(
        f"{normalized_root}/"
    )


def _legacy_command_root_changed(
    integration,
    project_root: Path,
    old_manifest,
    new_manifest,
) -> bool:
    """Return True when command artifacts moved from legacy_dir to canonical dir."""
    config = integration.registrar_config or {}
    canonical = config.get("dir")
    legacy = config.get("legacy_dir")
    if (
        not isinstance(canonical, str)
        or not canonical.strip()
        or not isinstance(legacy, str)
        or not legacy.strip()
        or PurePath(canonical).as_posix() == PurePath(legacy).as_posix()
    ):
        return False

    canonical_dir = project_root / canonical
    legacy_dir = project_root / legacy
    if not canonical_dir.is_dir() or not legacy_dir.is_dir():
        return False

    old_had_legacy = any(
        _manifest_path_under(rel, legacy) for rel in old_manifest.files
    )
    new_has_canonical = any(
        _manifest_path_under(rel, canonical) for rel in new_manifest.files
    )
    return old_had_legacy and new_has_canonical


def _planned_command_files(integration) -> set[str]:
    """Return the manifest keys ``setup()`` will write for core command templates."""
    commands_dir = (integration.registrar_config or {}).get("dir")
    if not isinstance(commands_dir, str) or not commands_dir.strip():
        return set()
    return {
        (PurePath(commands_dir) / integration.command_filename(template.stem)).as_posix()
        for template in integration.list_command_templates()
    }


def _command_file_names_changed(integration, old_files, new_files) -> bool:
    """Return True when core command files are renamed inside the command dir.

    Kiro CLI moved from ``speckit.<cmd>.md`` to ``speckit-<cmd>.md`` in the
    same ``.kiro/prompts`` directory (#4797). *old_files* and *new_files* are
    manifest keys; ``upgrade`` passes ``_planned_command_files()`` as the new
    ones so it can refuse the rename while presets have commands registered
    for the agent, before changing files. Only a removed file that matches an
    added one up to ``.``/``-`` separators counts, so a release that just adds
    and drops commands is not a rename.
    """
    commands_dir = (integration.registrar_config or {}).get("dir")
    if not isinstance(commands_dir, str) or not commands_dir.strip():
        return False
    old = {rel for rel in old_files if _manifest_path_under(rel, commands_dir)}
    new = {rel for rel in new_files if _manifest_path_under(rel, commands_dir)}
    # Compare whole paths: skill layouts name every file SKILL.md.
    removed = {rel.replace(".", "-") for rel in old - new}
    added = {rel.replace(".", "-") for rel in new - old}
    return bool(removed & added)


def _command_files_on_disk(project_root, integration) -> set[str]:
    """Return manifest keys for the entries directly in the command dir."""
    commands_dir = (integration.registrar_config or {}).get("dir")
    if not isinstance(commands_dir, str) or not commands_dir.strip():
        return set()
    try:
        with os.scandir(Path(project_root) / commands_dir) as entries:
            return {
                (PurePath(commands_dir) / entry.name).as_posix()
                for entry in entries
                if not entry.is_dir(follow_symlinks=False)
            }
    except (FileNotFoundError, NotADirectoryError):
        return set()


class _ExtensionRegistryUnreadableError(Exception):
    """Raised when the extension registry can't show who owns a command file.

    The counterpart of :class:`_PresetRegistryUnreadableError` for
    ``_extension_commands_at``.
    """


def _extension_commands_at(project_root, integration, rel_paths) -> list[str]:
    """Return ``"<extension> (<command>)"`` for registered commands at *rel_paths*.

    *rel_paths* are manifest keys. A command is matched by the file
    registration wrote before Kiro CLI's rename (#4797), named after the
    command itself, so an older alias ``speckit-plan`` matches
    ``.kiro/prompts/speckit-plan.md``. Disabled extensions count: their
    files stay on disk.

    Fails **closed** like ``_installed_presets_affecting_agent``: an absent
    registry returns an empty list, but a registry that exists and can't be
    read or parsed, or an entry whose ``registered_commands`` for the
    integration isn't a list of names, raises
    :class:`_ExtensionRegistryUnreadableError`. Skipping it would let the
    rename write a core file over an extension's.
    """
    from ..extensions import ExtensionRegistry

    config = integration.registrar_config or {}
    commands_dir, suffix = config.get("dir"), config.get("extension")
    if not isinstance(commands_dir, str) or not isinstance(suffix, str):
        return []
    registry_path = (
        Path(project_root) / ".specify" / "extensions" / ExtensionRegistry.REGISTRY_FILE
    )
    if not os.path.lexists(registry_path):
        return []
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _ExtensionRegistryUnreadableError(str(exc)) from exc
    extensions = data.get("extensions", {}) if isinstance(data, dict) else None
    if not isinstance(extensions, dict):
        raise _ExtensionRegistryUnreadableError(
            "extension registry structure is malformed"
        )

    targets = {os.path.normcase(rel) for rel in rel_paths}
    found = []
    for ext_id, metadata in extensions.items():
        recorded = (
            metadata.get("registered_commands")
            if isinstance(metadata, dict)
            else None
        )
        names = (
            recorded.get(integration.key, [])
            if isinstance(recorded, dict)
            else None
        )
        if not isinstance(names, list) or not all(
            isinstance(name, str) for name in names
        ):
            raise _ExtensionRegistryUnreadableError(
                f"extension '{ext_id}' registered_commands is missing or malformed"
            )
        for name in names:
            rel = (PurePath(commands_dir) / f"{name}{suffix}").as_posix()
            if os.path.normcase(rel) in targets:
                found.append(f"{ext_id} ({name})")
    return sorted(found)


def _check_extension_command_claims(project_root, integration, planned_command_files) -> None:
    """Refuse core writes at extension claims during upgrade and Kiro init (#4797)."""
    import typer

    from .._console import console
    from ._helpers import _cli_error_detail

    key = integration.key
    try:
        taken = _extension_commands_at(
            project_root, integration, planned_command_files
        )
    except _ExtensionRegistryUnreadableError as exc:
        console.print(
            f"[red]Error:[/red] Cannot write '{key}' core command files: the "
            "extension registry could not be read."
        )
        console.print(f"[dim]Details:[/dim] {_cli_error_detail(exc)}")
        console.print(
            "Writing them could replace an extension's files, so this is refused "
            "before changing files. Fix or restore "
            "[cyan].specify/extensions/.registry[/cyan] and retry."
        )
        raise typer.Exit(1)
    if taken:
        console.print(
            f"[red]Error:[/red] Cannot write '{key}' core command files while "
            "extension commands use a core command's file name: "
            f"[bold]{', '.join(taken)}[/bold]."
        )
        console.print(
            "Writing them would replace the extension's files, so this is refused "
            "before changing files. Update or remove the extension(s), then retry."
        )
        raise typer.Exit(1)


def _legacy_command_root_upgrade_pending(integration, old_manifest) -> bool:
    """Return True when the old manifest tracks command files under legacy_dir."""
    config = integration.registrar_config or {}
    canonical = config.get("dir")
    legacy = config.get("legacy_dir")
    if (
        not isinstance(canonical, str)
        or not canonical.strip()
        or not isinstance(legacy, str)
        or not legacy.strip()
        or PurePath(canonical).as_posix() == PurePath(legacy).as_posix()
    ):
        return False
    return any(_manifest_path_under(rel, legacy) for rel in old_manifest.files)


class _PresetRegistryUnreadableError(Exception):
    """Raised when an existing preset registry cannot be read or parsed.

    Distinct from a *genuinely absent* registry (no presets installed): an
    unreadable registry means we cannot verify whether preset overrides would
    be orphaned by a layout change, so the migration must be rejected rather
    than proceeding on a false "no presets" assumption.
    """


def _installed_presets_affecting_agent(
    project_root,
    agent_key: str,
    *,
    include_skills: bool = True,
) -> list[str]:
    """Return IDs of installed presets with artifacts registered for *agent_key*.

    Preset registration is active-agent-only (#2948): command overrides are
    written for the active non-skills agent and skills for the active skills
    agent, tracked per preset in ``registered_commands`` /
    ``registered_skills``. Entries for *other* agents may still exist from
    when those agents were active. Callers use this to reject command-root or
    command↔skills layout migrations before mutation: preset rescaffolding is
    best-effort and cannot guarantee every tracked artifact has a replacement.

    Fails **closed**: a genuinely absent registry (no presets ever installed)
    returns an empty list, but if the registry file exists and cannot be read
    or parsed (e.g. a permission error or corruption) this raises
    :class:`_PresetRegistryUnreadableError`.  Reporting "no presets" in that
    case would let a ``--force`` layout-changing upgrade delete
    preset-overridden files while their registry state can't be reconciled —
    the exact inconsistency the guard exists to prevent.
    """
    from ..presets import PresetRegistry

    registry_path = (
        Path(project_root) / ".specify" / "presets" / PresetRegistry.REGISTRY_FILE
    )
    # Genuinely absent registry → no presets installed → safe to proceed.
    if not registry_path.exists():
        return []

    # The registry exists: any failure to read or parse it must surface as an
    # error, not be swallowed into an empty ("no presets") result.
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _PresetRegistryUnreadableError(str(exc)) from exc
    if not isinstance(data, dict) or not isinstance(data.get("presets", {}), dict):
        raise _PresetRegistryUnreadableError(
            "preset registry structure is malformed"
        )

    affected: list[str] = []
    for preset_id, meta in data.get("presets", {}).items():
        # A malformed entry means we cannot verify whether this preset owns
        # artifacts for the agent, so fail closed rather than skip it.
        if not isinstance(meta, dict):
            raise _PresetRegistryUnreadableError(
                f"preset '{preset_id}' entry is malformed"
            )
        registered_commands = meta.get("registered_commands", {})
        if not isinstance(registered_commands, dict) or not all(
            isinstance(names, list) for names in registered_commands.values()
        ):
            raise _PresetRegistryUnreadableError(
                f"preset '{preset_id}' registered_commands is malformed"
            )
        registered_skills = meta.get("registered_skills", [])
        if isinstance(registered_skills, dict):
            # Per-agent provenance ({agent: [skill names]}): only entries for
            # *this* agent make the preset affect it. Values must be lists —
            # anything else (e.g. null) leaves ownership undecidable, so fail
            # closed rather than read it as "no artifacts".
            if not all(
                isinstance(names, list) for names in registered_skills.values()
            ):
                raise _PresetRegistryUnreadableError(
                    f"preset '{preset_id}' registered_skills is malformed"
                )
            has_skills = include_skills and bool(
                registered_skills.get(agent_key)
            )
        elif isinstance(registered_skills, (list, tuple)):
            # Legacy flat list: not agent-scoped, so any recorded skill may
            # belong to this agent — fail closed and count it as affecting.
            has_skills = include_skills and bool(registered_skills)
        else:
            raise _PresetRegistryUnreadableError(
                f"preset '{preset_id}' registered_skills is malformed"
            )
        has_commands = bool(registered_commands.get(agent_key))
        if has_commands or has_skills:
            affected.append(preset_id)
    return affected


def _installed_command_presets_affecting_agent(
    project_root,
    agent_key: str,
) -> list[str]:
    """Return installed presets with command artifacts registered for *agent_key*."""
    return _installed_presets_affecting_agent(
        project_root,
        agent_key,
        include_skills=False,
    )
