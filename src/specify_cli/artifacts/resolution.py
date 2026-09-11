"""Artifact stack projection over the existing preset resolver."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from ._identifiers import (
    PROJECT_OVERRIDE_LAYER,
    IdentifierComponentError,
    derive_lookup_id,
    derive_public_id,
)
from .models import ArtifactKind, ArtifactResolutionError, LayerName, StackLayer


@dataclass(frozen=True)
class _LayerProvenance:
    """Artifact-only metadata derived from an unchanged resolver layer."""

    layer: LayerName | None
    source_id: str | None
    disk_id: str | None
    pack_dir: Path | None
    manifest: Any | None
    manifest_entry: dict[str, Any] | None

    def lookup_id(self, kind: ArtifactKind, name: str) -> str | None:
        if self.layer is None or self.source_id is None:
            return None
        try:
            return derive_lookup_id(self.layer, self.source_id, kind, name)
        except IdentifierComponentError:
            return None


def _same_file(left: Path | None, right: Any) -> bool:
    """Compare paths without requiring either path to exist at comparison time."""
    return isinstance(right, Path) and left is not None and left.resolve() == right.resolve()


def _manifest_entry_for_path(
    manifest: Any,
    layer: Literal["preset", "extension"],
    pack_dir: Path,
    kind: ArtifactKind,
    name: str,
    path: Path,
) -> dict[str, Any] | None:
    """Return the existing manifest declaration that resolved to *path*."""
    if manifest is None:
        return None
    if layer == "preset":
        entries = (
            entry
            for entry in manifest.templates
            if isinstance(entry, dict) and entry.get("type") == kind
        )
    else:
        entries = {
            "command": manifest.commands,
            "template": manifest.templates,
            "script": manifest.scripts,
        }[kind]
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("name") != name:
            continue
        relative_file = entry.get("file")
        if isinstance(relative_file, str) and _same_file(
            pack_dir / relative_file, path
        ):
            return entry
    return None


def _layer_provenance(
    resolver: Any,
    resolver_layer: dict[str, Any],
    kind: ArtifactKind,
    name: str,
    manifest_cache: dict[Path, Any | None],
) -> _LayerProvenance:
    """Derive artifact provenance from the resolver's established layer shape."""
    source = resolver_layer.get("source")
    path = resolver_layer.get("path")

    if source == "project override":
        return _LayerProvenance("project", "_", None, None, None, None)
    if source in {"core", "core (bundled)"}:
        return _LayerProvenance(None, None, None, None, None, None)
    if not isinstance(path, Path) or not isinstance(source, str):
        raise ArtifactResolutionError()

    if source.startswith("extension:"):
        extension_id = resolver_layer.get("extension_id")
        extension_dir = resolver_layer.get("extension_dir")
        if not isinstance(extension_id, str) or not isinstance(extension_dir, Path):
            raise ArtifactResolutionError()
        manifest_path = extension_dir / "extension.yml"
        if manifest_path not in manifest_cache:
            try:
                from ..extensions import ExtensionManifest, ValidationError

                manifest_cache[manifest_path] = (
                    ExtensionManifest(manifest_path) if manifest_path.is_file() else None
                )
            except (
                ValidationError,
                yaml.YAMLError,
                OSError,
                TypeError,
                AttributeError,
            ):
                manifest_cache[manifest_path] = None
        manifest = manifest_cache[manifest_path]
        declared = _manifest_entry_for_path(
            manifest, "extension", extension_dir, kind, name, path
        )
        source_id = (
            manifest.id
            if declared is not None
            and manifest is not None
            and isinstance(manifest.id, str)
            and manifest.id
            else extension_id
        )
        return _LayerProvenance(
            "extension",
            source_id,
            extension_id,
            extension_dir,
            manifest,
            declared,
        )

    try:
        relative = path.relative_to(resolver.presets_dir)
    except ValueError as exc:
        raise ArtifactResolutionError() from exc
    if not relative.parts:
        raise ArtifactResolutionError()
    pack_id = relative.parts[0]
    pack_dir = resolver.presets_dir / pack_id
    manifest = resolver._get_manifest(pack_dir)
    declared = _manifest_entry_for_path(
        manifest, "preset", pack_dir, kind, name, path
    )
    source_id = (
        manifest.id
        if declared is not None
        and manifest is not None
        and isinstance(manifest.id, str)
        and manifest.id
        else pack_id
    )
    return _LayerProvenance(
        "preset",
        source_id,
        pack_id,
        pack_dir,
        manifest,
        declared,
    )


def _derive_manifest_path(
    provenance: _LayerProvenance, project_root: Path
) -> str | None:
    """Return the declaring manifest path for an artifact layer."""
    if provenance.manifest_entry is None or provenance.pack_dir is None:
        return None
    manifest_name = (
        "preset.yml" if provenance.layer == "preset" else "extension.yml"
    )
    manifest_path = provenance.pack_dir / manifest_name
    if not manifest_path.is_file():
        return None
    try:
        return manifest_path.relative_to(project_root).as_posix()
    except ValueError:
        return None


def _repo_relative_existing_file(project_root: Path, path: Path) -> str | None:
    """Return *path* relative to the project root when it is an existing file."""
    if not path.is_file():
        return None
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return None


def _is_safe_path_component(value: str) -> bool:
    """Return true when *value* is a single non-traversing path component."""
    if not value or value in (".", ".."):
        return False
    path = Path(value)
    return not path.is_absolute() and len(path.parts) == 1 and path.name == value


def _materialized_command_source_path(
    project_root: Path,
    metadata: dict[str, Any] | None,
    name: str,
    *,
    source: Literal["preset", "extension"],
) -> str | None:
    """Return the tracked agent output path for an installed command layer."""
    if not isinstance(metadata, dict):
        return None

    try:
        from ..agents import CommandRegistrar
    except ImportError:
        return None

    registrar = CommandRegistrar()
    registrar._ensure_configs()

    registered_commands = metadata.get("registered_commands")
    if isinstance(registered_commands, dict):
        for agent_name in sorted(registered_commands):
            cmd_names = registered_commands.get(agent_name)
            if not isinstance(cmd_names, list):
                continue
            if name not in cmd_names:
                continue
            agent_config = registrar.AGENT_CONFIGS.get(agent_name)
            if agent_config is None:
                continue
            output_name = registrar._compute_output_name(
                agent_name, name, agent_config
            )
            command_path = (
                registrar._resolve_agent_dir(agent_name, agent_config, project_root)
                / f"{output_name}{agent_config['extension']}"
            )
            rel = _repo_relative_existing_file(project_root, command_path)
            if rel is not None:
                return rel

    registered_skills = metadata.get("registered_skills")
    if source == "preset":
        skill_names_by_agent = registered_skills if isinstance(registered_skills, dict) else {}
    elif isinstance(registered_skills, list):
        # Extension registries store skills as a flat list, unlike presets'
        # per-agent map. Probe every known agent's project-local skills
        # directory and return the first extant tracked file.
        skill_names_by_agent = {
            agent_name: registered_skills for agent_name in sorted(registrar.AGENT_CONFIGS)
        }
    else:
        skill_names_by_agent = {}

    expected_skill_names: set[str] | None = None
    if source == "extension":
        try:
            from ..extensions import ExtensionManager

            expected_skill_names = {ExtensionManager._skill_name_for_command(name)}
        except ImportError:
            expected_skill_names = None
    else:
        try:
            from ..presets import PresetManager

            expected_skill_names = set(PresetManager._skill_names_for_command(name))
        except ImportError:
            expected_skill_names = None

    if isinstance(skill_names_by_agent, dict):
        from .. import _get_skills_dir as _project_skills_dir

        for agent_name in sorted(skill_names_by_agent):
            skill_names = skill_names_by_agent.get(agent_name)
            if not isinstance(agent_name, str) or not isinstance(skill_names, list):
                continue
            agent_config = registrar.AGENT_CONFIGS.get(agent_name)
            if agent_config is None:
                continue
            if agent_config.get("extension") == "/SKILL.md":
                skills_dir = registrar._resolve_agent_dir(
                    agent_name, agent_config, project_root
                )
            else:
                skills_dir = _project_skills_dir(project_root, agent_name)
            for skill_name in sorted(
                n for n in skill_names if isinstance(n, str) and _is_safe_path_component(n)
            ):
                if expected_skill_names is not None and skill_name not in expected_skill_names:
                    continue
                skill_path = skills_dir / skill_name / "SKILL.md"
                rel = _repo_relative_existing_file(project_root, skill_path)
                if rel is not None:
                    return rel

    return None


def _derive_source_path(
    provenance: _LayerProvenance,
    layer: dict[str, Any],
    project_root: Path,
    kind: ArtifactKind,
    name: str,
    *,
    active: bool,
) -> str | None:
    """Return the repo-relative concrete file backing a preset/extension layer.

    The tracked materialized agent output is shared by every stack row that
    contributed the same command name, so it only reflects the winning
    (``active``) row's content. Lower ``replace``/``merge`` rows must report
    their own installed pack file instead of that shared output.
    """
    if provenance.layer == "preset":
        if provenance.disk_id is None:
            return None
        from ..presets import PresetRegistry

        metadata = PresetRegistry(project_root / ".specify" / "presets").get(
            provenance.disk_id
        )
        if kind == "command" and active:
            materialized = _materialized_command_source_path(
                project_root, metadata, name, source="preset"
            )
            if materialized is not None:
                return materialized
    elif provenance.layer == "extension":
        if provenance.disk_id is None:
            return None
        from ..extensions import ExtensionRegistry

        metadata = ExtensionRegistry(project_root / ".specify" / "extensions").get(
            provenance.disk_id
        )
        if kind == "command" and active:
            materialized = _materialized_command_source_path(
                project_root, metadata, name, source="extension"
            )
            if materialized is not None:
                return materialized
    else:
        return None

    # Non-active command layers, non-command preset/extension layers, and
    # active command layers without a tracked materialized agent output all
    # report the installed pack file from the raw
    # PresetResolver.collect_all_layers() row's concrete ``path`` key.
    path = layer.get("path")
    if isinstance(path, Path):
        return _repo_relative_existing_file(project_root, path)
    return None


def _preset_display_name(pack_dir: Path, pack_id: str) -> str:
    """Return the preset's human-friendly name from ``preset.yml``, or ``pack_id``.

    Delegates parsing and validation to :class:`PresetManifest` — the same
    class ``PresetManager.list_installed()`` and ``specify preset list`` use —
    instead of re-parsing the YAML by hand. Falls back to ``pack_id`` when the
    manifest file is missing or fails manifest validation (for example, an
    older flat-layout manifest with no ``preset:`` section at all).
    """
    from ..presets import PresetManifest, PresetValidationError  # lazy: avoids circular import

    manifest_path = pack_dir / "preset.yml"
    if not manifest_path.is_file():
        return pack_id
    try:
        return PresetManifest(manifest_path).name
    except PresetValidationError:
        return pack_id


def _build_stack(
    project_root: Path,
    kind: ArtifactKind,
    name: str,
    raw_layers: list[dict[str, Any]] | None = None,
    resolver: Any | None = None,
    manifest_cache: dict[Path, Any | None] | None = None,
) -> list[StackLayer]:
    """Build the ordered stack for a single artifact.

    Delegates the actual composition math to
    :meth:`PresetResolver.collect_all_layers`; this function only reshapes
    each raw layer dict into a :class:`StackLayer` and computes the
    ``active`` / ``hidden`` labels documented on the data model.

    Returns an empty list when the artifact is not visible from any tier
    (no preset, no extension, no built-in asset).
    """
    from ..presets import PresetError, PresetResolver  # lazy: avoids circular import

    template_type = kind
    resolver = resolver or PresetResolver(project_root)
    if raw_layers is None:
        try:
            raw = resolver.collect_all_layers(name, template_type)
        except (OSError, PresetError) as exc:
            raise ArtifactResolutionError() from exc
    else:
        raw = raw_layers
    if not raw:
        return []
    manifest_cache = manifest_cache if manifest_cache is not None else {}

    first_replace_idx = next(
        (i for i, layer in enumerate(raw) if layer["strategy"] == "replace"),
        None,
    )

    public_id = derive_public_id(kind, name)
    rows: list[StackLayer] = []
    for idx, layer in enumerate(raw):
        strategy = layer["strategy"]
        active = idx == 0

        if first_replace_idx is None:
            hidden = False
        else:
            hidden = idx > first_replace_idx

        provenance = _layer_provenance(
            resolver, layer, kind, name, manifest_cache
        )
        lookup_id = provenance.lookup_id(kind, name)
        source_path = _derive_source_path(
            provenance, layer, project_root, kind, name, active=active
        )

        if provenance.layer == PROJECT_OVERRIDE_LAYER:
            rows.append(
                StackLayer(
                    id=public_id,
                    layer="project",
                    sourceId=provenance.source_id,
                    presetId=None,
                    presetName=None,
                    strategy=strategy,
                    active=active,
                    hidden=hidden,
                    manifestPath=None,
                    lookupId=lookup_id,
                    sourcePath=source_path,
                )
            )
            continue

        if provenance.layer == "extension":
            manifest_path = _derive_manifest_path(provenance, project_root)
            rows.append(
                StackLayer(
                    id=public_id,
                    layer="extension",
                    sourceId=provenance.source_id,
                    presetId=None,
                    presetName=None,
                    strategy=strategy,
                    active=active,
                    hidden=hidden,
                    manifestPath=manifest_path,
                    lookupId=lookup_id,
                    sourcePath=source_path,
                )
            )
            continue

        if provenance.layer is None:
            rows.append(
                StackLayer(
                    id=public_id,
                    layer=None,
                    sourceId=None,
                    presetId=None,
                    presetName=None,
                    strategy=strategy,
                    active=active,
                    hidden=hidden,
                    manifestPath=None,
                    lookupId=None,
                    sourcePath=source_path,
                )
            )
            continue

        pack_id = provenance.disk_id or ""
        pack_dir = provenance.pack_dir or (
            project_root / ".specify" / "presets" / pack_id
        )
        display = _preset_display_name(pack_dir, pack_id) if pack_id else pack_id
        manifest_path = _derive_manifest_path(provenance, project_root)
        rows.append(
            StackLayer(
                id=public_id,
                layer="preset",
                sourceId=provenance.source_id,
                presetId=pack_id or None,
                presetName=display or None,
                strategy=strategy,
                active=active,
                hidden=hidden,
                manifestPath=manifest_path,
                lookupId=lookup_id,
                sourcePath=source_path,
            )
        )
    return rows
