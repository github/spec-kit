"""Layout-migration guards for ``specify integration upgrade``."""

from __future__ import annotations

import json
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
