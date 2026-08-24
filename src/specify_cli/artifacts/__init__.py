"""Pure logic for the `specify artifact` command group. No Typer decorators.

Two public entry points:

* :meth:`ArtifactCatalog.list_artifacts` — flat inventory (id, name, kind, description).
* :meth:`ArtifactCatalog.get_artifact_info` — one row plus its full ordered stack.

Everything else in this module is internal machinery. Callers outside
:mod:`specify_cli.artifacts._commands` should not import the private helpers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Literal

import yaml

from .._assets import _locate_core_asset_dir
from .._identifier import (
    PROJECT_OVERRIDE_LAYER,
    IdentifierComponentError,
    derive_named_id,
    layer_kind_from_lookup_id,
    validate_component,
)
from .._script_variants import canonical_script_name

# ---------------------------------------------------------------------------
# Public data classes
# ---------------------------------------------------------------------------

ArtifactKind = Literal["command", "template", "script"]
LayerName = Literal["project", "preset", "extension", "core"]
Strategy = Literal["replace", "wrap", "prepend", "append"]


@dataclass(frozen=True)
class Artifact:
    """One row in the flat inventory returned by ``list_artifacts()``."""

    id: str
    name: str
    kind: ArtifactKind
    description: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
        }


@dataclass(frozen=True)
class StackLayer:
    """One row inside the ``stack`` array returned by ``get_artifact_info()``."""

    layer: LayerName
    presetId: str | None
    presetName: str | None
    strategy: Strategy
    active: bool
    hidden: bool
    manifestPath: str | None
    lookupId: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "presetId": self.presetId,
            "presetName": self.presetName,
            "strategy": self.strategy,
            "active": self.active,
            "hidden": self.hidden,
            "manifestPath": self.manifestPath,
            "lookupId": self.lookupId,
        }


# ---------------------------------------------------------------------------
# Exceptions — pinned error strings (see artifact-error contract regex)
# ---------------------------------------------------------------------------


class ArtifactError(Exception):
    """Base class for the three logical error conditions this module raises.

    Each subclass carries a ``.message`` attribute whose value is the exact
    string emitted to stderr under the ``error`` key of the JSON envelope.
    The contract regex is ``^(unknown artifact |ambiguous artifact |artifact resolution failed|not a Spec Kit project)``.
    """

    message: str


class ArtifactNotFoundError(ArtifactError):
    def __init__(self, name: str) -> None:
        self.message = f"unknown artifact {name}"
        super().__init__(self.message)


class AmbiguousArtifactError(ArtifactError):
    def __init__(self, name: str, kinds: Iterable[str]) -> None:
        kinds_list = sorted(kinds)
        self.message = f"ambiguous artifact {name}: matches kinds {kinds_list}"
        super().__init__(self.message)


class NotASpecKitProjectError(ArtifactError):
    def __init__(self) -> None:
        self.message = "not a Spec Kit project: no .specify/ directory found"
        super().__init__(self.message)


class ArtifactResolutionError(ArtifactError):
    def __init__(self) -> None:
        self.message = "artifact resolution failed"
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Core-baseline enumeration
# ---------------------------------------------------------------------------

_TEMPLATE_SUFFIX = ".md"
_SCRIPT_SUFFIX = ".sh"
_COMMAND_NAME_RE = re.compile(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*")
_TEMPLATE_OR_SCRIPT_NAME_RE = re.compile(r"[a-z0-9-]+")


@dataclass(frozen=True)
class _CoreBaselineRow:
    name: str
    kind: ArtifactKind
    path: Path
    description: str


def _core_asset_root(subdir: str) -> Path | None:
    """Return the on-disk directory holding a family of core assets, or None.

    Delegates to :func:`_locate_core_asset_dir`, the single shared resolver
    also used by :func:`_load_core_command_names` and
    :meth:`PresetResolver._find_bundled_core`, so all three code paths agree
    on what "core" means on this machine instead of each re-deriving it.
    """
    return _locate_core_asset_dir(subdir)


def _project_core_asset_root(project_root: Path | None, subdir: str) -> Path | None:
    """Return the project-local core directory for an asset family, if present."""
    if project_root is None:
        return None
    candidate = project_root / ".specify" / "templates"
    if subdir == "commands":
        candidate /= "commands"
    elif subdir == "scripts":
        candidate /= "scripts"
    elif subdir != "templates":  # pragma: no cover — internal misuse
        return None
    return candidate if candidate.is_dir() else None


def _extract_frontmatter_description(text: str) -> str:
    """Return the ``description`` value from YAML frontmatter, else ``""``.

    Matches the frontmatter shape used by every core command/template on disk:
    a ``---`` fence pair at the top of the file with a YAML mapping between
    them. Anything malformed silently yields the empty string — the contract
    forbids omission but permits ``""``.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return ""
    fence_end = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            fence_end = i
            break
    if fence_end == -1:
        return ""
    try:
        data = yaml.safe_load("".join(lines[1:fence_end]))
    except yaml.YAMLError:
        return ""
    if not isinstance(data, dict):
        return ""
    value = data.get("description", "")
    return value if isinstance(value, str) else ""


def _extract_script_description(text: str) -> str:
    """Return the first docstring/comment line of a script, else ``""``.

    Supports the three script runtimes SpecKit ships:

    * Python (``.py``): the first line of the module docstring.
    * Bash (``.sh``): the first ``#``-prefixed comment line following the
      shebang.
    * PowerShell (``.ps1``): either the first line of a ``<# ... #>`` block
      comment or the first ``#``-prefixed line.

    Anything unrecognized yields the empty string.
    """
    py_match = re.match(r'^(?:#![^\n]*\n)?\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', text, re.DOTALL)
    if py_match:
        first = py_match.group(1).strip().splitlines()
        if first:
            return first[0].strip()

    ps_block = re.match(r'^(?:<#\s*(.*?)#>)', text, re.DOTALL)
    if ps_block:
        first = ps_block.group(1).strip().splitlines()
        if first:
            return first[0].strip().lstrip(".").strip()

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#!"):
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        break
    return ""


def _enumerate_core_commands(project_root: Path | None = None) -> list[_CoreBaselineRow]:
    """Enumerate every command shipped in the core baseline.

    Names are surfaced with the ``speckit.`` prefix so they collide with
    preset/extension contributions in a stable way — this is what the id
    grammar ``command:speckit.constitution`` requires.
    """
    from ..extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

    commands_dir = _core_asset_root("commands")
    project_commands_dir = _project_core_asset_root(project_root, "commands")
    rows: list[_CoreBaselineRow] = []
    if commands_dir is None and project_commands_dir is None:
        return rows
    candidate_stems = set(CORE_COMMAND_NAMES)
    if commands_dir is not None:
        candidate_stems.update(
            entry.stem
            for entry in commands_dir.iterdir()
            if entry.is_file() and entry.suffix == _TEMPLATE_SUFFIX
        )
    if project_commands_dir is not None:
        candidate_stems.update(
            entry.stem
            for entry in project_commands_dir.iterdir()
            if entry.is_file() and entry.suffix == _TEMPLATE_SUFFIX
        )
    rows_by_name: dict[str, _CoreBaselineRow] = {}
    for stem in sorted(candidate_stems):
        logical_name = stem if stem.startswith("speckit.") else f"speckit.{stem}"
        project_candidates = (
            (
                project_commands_dir / f"{stem}.md",
                project_commands_dir / f"{logical_name}.md",
            )
            if project_commands_dir is not None
            else ()
        )
        bundled_candidates = (
            (
                commands_dir / f"{stem}.md",
                commands_dir / f"{logical_name}.md",
            )
            if commands_dir is not None
            else ()
        )
        path = next(
            (
                candidate
                for candidate in (*project_candidates, *bundled_candidates)
                if candidate.is_file()
            ),
            None,
        )
        if path is None:
            continue
        if logical_name in rows_by_name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        rows_by_name[logical_name] = _CoreBaselineRow(
            name=logical_name,
            kind="command",
            path=path,
            description=_extract_frontmatter_description(text),
        )
    rows.extend(rows_by_name[name] for name in sorted(rows_by_name))
    return rows


def _enumerate_core_templates(project_root: Path | None = None) -> list[_CoreBaselineRow]:
    templates_dir = _core_asset_root("templates")
    project_templates_dir = _project_core_asset_root(project_root, "templates")
    rows: list[_CoreBaselineRow] = []
    seen: set[str] = set()
    for directory in (project_templates_dir, templates_dir):
        if directory is None:
            continue
        for entry in sorted(directory.iterdir(), key=lambda p: p.name):
            if (
                not entry.is_file()
                or entry.suffix != _TEMPLATE_SUFFIX
                or entry.stem in seen
            ):
                continue
            seen.add(entry.stem)
            try:
                text = entry.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                text = ""
            rows.append(
                _CoreBaselineRow(
                    name=entry.stem,
                    kind="template",
                    path=entry,
                    description=_extract_frontmatter_description(text),
                )
            )
    return rows


def _enumerate_core_scripts(project_root: Path | None = None) -> list[_CoreBaselineRow]:
    scripts_dir = _core_asset_root("scripts")
    project_scripts_dir = _project_core_asset_root(project_root, "scripts")
    rows: list[_CoreBaselineRow] = []
    seen: dict[str, _CoreBaselineRow] = {}
    for directory in (project_scripts_dir, scripts_dir):
        if directory is None:
            continue
        for entry in sorted(directory.glob(f"*{_SCRIPT_SUFFIX}"), key=lambda p: p.name):
            if entry.stem not in seen:
                seen[entry.stem] = _core_script_row(entry, entry.stem)
        for runtime_dir in sorted(directory.iterdir(), key=lambda p: p.name):
            if not runtime_dir.is_dir():
                continue
            for entry in sorted(runtime_dir.iterdir(), key=lambda p: p.name):
                if not entry.is_file():
                    continue
                name = canonical_script_name(entry)
                if name is not None and name not in seen:
                    seen[name] = _core_script_row(entry, name)
    rows.extend(sorted(seen.values(), key=lambda r: r.name))
    return rows


def _core_script_row(path: Path, name: str) -> _CoreBaselineRow:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    return _CoreBaselineRow(
        name=name,
        kind="script",
        path=path,
        description=_extract_script_description(text),
    )


@dataclass(frozen=True)
class CoreBaseline:
    """The union of the three core enumerators, indexed for O(1) lookup."""

    commands: tuple[_CoreBaselineRow, ...]
    templates: tuple[_CoreBaselineRow, ...]
    scripts: tuple[_CoreBaselineRow, ...]

    @classmethod
    def load(cls, project_root: Path | None = None) -> "CoreBaseline":
        return cls(
            commands=tuple(_enumerate_core_commands(project_root)),
            templates=tuple(_enumerate_core_templates(project_root)),
            scripts=tuple(_enumerate_core_scripts(project_root)),
        )

    def by_kind(self, kind: ArtifactKind) -> tuple[_CoreBaselineRow, ...]:
        return {
            "command": self.commands,
            "template": self.templates,
            "script": self.scripts,
        }[kind]

    def find(self, kind: ArtifactKind, name: str) -> _CoreBaselineRow | None:
        for row in self.by_kind(kind):
            if row.name == name:
                return row
        return None


# ---------------------------------------------------------------------------
# Resolver-adaptation helpers
# ---------------------------------------------------------------------------


def _derive_manifest_path(layer: dict[str, Any], project_root: Path) -> str | None:
    """Return a repo-relative POSIX path to the manifest declaring this layer.

    ``layer`` is one dict entry from ``PresetResolver.collect_all_layers()``.
    Only ``preset`` and ``extension`` layers have an on-disk manifest — core
    and project-override layers return ``None``.

    ``PresetResolver.collect_all_layers`` always reads a pack's files from
    ``project_root / ".specify" / "<presets|extensions>" / "<sourceId>"``,
    whether or not that pack is registered — registration only changes which
    priority/version metadata is attached, never where the pack lives on
    disk. That means the manifest's location is fully determined by the
    layer's own ``lookupId`` (``"{layer}:{sourceId}:..."``), so it is derived
    directly rather than walking upward from the contribution file.

    Uses ``as_posix()`` so the string is stable across Windows and POSIX — a
    caller comparing snapshots between operating systems gets the same value
    on both.
    """
    lookup_id = layer.get("lookupId", "")
    layer_kind = layer_kind_from_lookup_id(lookup_id)
    if layer_kind not in ("preset", "extension"):
        return None
    pack_id = _extract_lookup_pack_id(lookup_id)
    if not pack_id:
        return None
    tier_dir, manifest_name = (
        ("presets", "preset.yml")
        if layer_kind == "preset"
        else ("extensions", "extension.yml")
    )
    manifest_path = project_root / ".specify" / tier_dir / pack_id / manifest_name
    if not manifest_path.is_file():
        return None
    return manifest_path.relative_to(project_root).as_posix()


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


def _extract_lookup_pack_id(lookup_id: str) -> str | None:
    """Return the ``sourceId`` segment of a lookupId, or ``None`` if malformed."""
    parts = lookup_id.split(":")
    if len(parts) < 4:
        return None
    return parts[1]


def _build_stack(
    project_root: Path,
    kind: ArtifactKind,
    name: str,
) -> list[StackLayer]:
    """Build the ordered stack for a single artifact.

    Delegates the actual composition math to
    :meth:`PresetResolver.collect_all_layers`; this function only reshapes
    each raw layer dict into a :class:`StackLayer` and computes the
    ``active`` / ``hidden`` labels documented on the data model.

    Returns an empty list when the artifact is not visible from any tier
    (no preset, no extension, no core baseline row).
    """
    from ..presets import PresetResolver  # lazy: avoids circular import

    resolver = PresetResolver(project_root)
    template_type = kind
    raw = resolver.collect_all_layers(name, template_type)
    if not raw:
        return []

    first_replace_idx = next(
        (i for i, layer in enumerate(raw) if layer["strategy"] == "replace"),
        None,
    )

    rows: list[StackLayer] = []
    for idx, layer in enumerate(raw):
        lookup_id = layer.get("lookupId", "")
        source = str(layer.get("source", ""))
        strategy = layer["strategy"]
        active = idx == 0

        if first_replace_idx is None:
            hidden = False
        else:
            hidden = idx > first_replace_idx

        # Layer classification: the lookupId prefix is the resolver's own
        # grammar (see layer_kind_from_lookup_id) and is authoritative; the
        # source-string check only guards against a malformed lookupId.
        layer_kind = layer_kind_from_lookup_id(lookup_id)

        if layer_kind == "core" or (layer_kind is None and source.startswith("core")):
            rows.append(
                StackLayer(
                    layer="core",
                    presetId=None,
                    presetName=None,
                    strategy=strategy,
                    active=active,
                    hidden=hidden,
                    manifestPath=None,
                    lookupId=lookup_id,
                )
            )
            continue

        if layer_kind == PROJECT_OVERRIDE_LAYER or (
            layer_kind is None and source == "project override"
        ):
            rows.append(
                StackLayer(
                    layer="project",
                    presetId=None,
                    presetName=None,
                    strategy=strategy,
                    active=active,
                    hidden=hidden,
                    manifestPath=None,
                    lookupId=lookup_id,
                )
            )
            continue

        if layer_kind == "extension" or (
            layer_kind is None and source.startswith("extension:")
        ):
            manifest_path = _derive_manifest_path(layer, project_root)
            rows.append(
                StackLayer(
                    layer="extension",
                    presetId=None,
                    presetName=None,
                    strategy=strategy,
                    active=active,
                    hidden=hidden,
                    manifestPath=manifest_path,
                    lookupId=lookup_id,
                )
            )
            continue

        pack_id = _extract_lookup_pack_id(lookup_id) or ""
        pack_dir = project_root / ".specify" / "presets" / pack_id
        display = _preset_display_name(pack_dir, pack_id) if pack_id else pack_id
        manifest_path = _derive_manifest_path(layer, project_root)
        rows.append(
            StackLayer(
                layer="preset",
                presetId=pack_id or None,
                presetName=display or None,
                strategy=strategy,
                active=active,
                hidden=hidden,
                manifestPath=manifest_path,
                lookupId=lookup_id,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# ArtifactCatalog — public façade
# ---------------------------------------------------------------------------


def _validate_project(project_root: Path) -> None:
    """Raise NotASpecKitProjectError when ``project_root`` isn't a Spec Kit project.

    The two invariants the rest of the module relies on are that
    ``project_root`` exists and that a ``.specify/`` subdirectory sits under
    it. Anything else — missing presets/, missing extensions/, missing
    templates/ — is a valid empty-inventory scenario and is not treated as
    an error.
    """
    if not (project_root / ".specify").is_dir():
        raise NotASpecKitProjectError()


def _validate_extension_registry(project_root: Path) -> None:
    extensions_dir = project_root / ".specify" / "extensions"
    if not extensions_dir.exists():
        return

    from ..extensions import ExtensionRegistry

    if ExtensionRegistry(extensions_dir).is_corrupt():
        raise ArtifactResolutionError()


def _resolve_kind_hint(name: str, kind: ArtifactKind | None) -> tuple[str, ArtifactKind | None]:
    """Parse ``kind:name`` shorthand and reconcile it with an explicit ``--kind`` flag.

    Returns ``(bare_name, resolved_kind)``. When ``name`` uses the ``kind:name``
    grammar and ``kind`` is also set explicitly, the two must agree — a
    mismatch is treated as an unknown artifact.
    """
    if ":" in name:
        prefix, _, bare = name.partition(":")
        if prefix in ("command", "template", "script"):
            resolved: ArtifactKind = prefix  # type: ignore[assignment]
            if kind is not None and kind != resolved:
                raise ArtifactNotFoundError(name)
            return bare, resolved
    return name, kind


def _validate_artifact_name(name: str, kind: ArtifactKind) -> str:
    """Validate a candidate artifact name using resolver-compatible grammars."""
    try:
        validated = validate_component(name, f"{kind} name")
    except IdentifierComponentError as exc:
        raise ArtifactNotFoundError(name) from exc

    pattern = _COMMAND_NAME_RE if kind == "command" else _TEMPLATE_OR_SCRIPT_NAME_RE
    if pattern.fullmatch(validated):
        return validated
    raise ArtifactNotFoundError(name)


class ArtifactCatalog:
    """Read-only view over one Spec Kit project's artifact inventory."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._baseline: CoreBaseline | None = None

    # ------------------------------------------------------------------ list
    def list_artifacts(self) -> list[Artifact]:
        """Return every artifact SpecKit exposes for this project, deduped.

        Sort order is deterministic — first by ``kind`` in the fixed
        ``["command", "template", "script"]`` order, then by ``name``.
        Returns an empty list when no artifacts are found rather than raising;
        a fresh install with no presets, no extensions, and an empty core
        baseline is still a valid Spec Kit project.

        Skills (``.github/skills/**/SKILL.md``) are intentionally excluded —
        they are integration-specific output, not a shipped asset family.
        """
        _validate_project(self.project_root)
        _validate_extension_registry(self.project_root)
        baseline = self._get_baseline()

        seen: dict[tuple[ArtifactKind, str], Artifact] = {}

        for row in (*baseline.commands, *baseline.templates, *baseline.scripts):
            key = (row.kind, row.name)
            if key not in seen:
                seen[key] = Artifact(
                    id=f"{row.kind}:{row.name}",
                    name=row.name,
                    kind=row.kind,
                    description=row.description,
                )

        for kind, name, description in self._iter_contribution_artifacts():
            key = (kind, name)
            if key not in seen:
                seen[key] = Artifact(
                    id=f"{kind}:{name}",
                    name=name,
                    kind=kind,
                    description=description,
                )
            elif description and not seen[key].description:
                seen[key] = Artifact(
                    id=seen[key].id,
                    name=seen[key].name,
                    kind=seen[key].kind,
                    description=description,
                )

        kind_order = {"command": 0, "template": 1, "script": 2}
        return sorted(seen.values(), key=lambda a: (kind_order[a.kind], a.name))

    # ------------------------------------------------------------------ info
    def get_artifact_info(
        self,
        name: str,
        kind: ArtifactKind | None = None,
    ) -> dict[str, Any]:
        """Return the full JSON-ready dict for ``specify artifact info``.

        Argument resolution:

        * ``name`` accepts the ``kind:name`` grammar as shorthand; when both
          the shorthand and ``kind`` are supplied they must agree.
        * When neither the shorthand nor ``kind`` narrows the search and
          more than one kind matches ``name``, raises
          :class:`AmbiguousArtifactError`.
        * When no artifact matches, raises :class:`ArtifactNotFoundError`.
        """
        _validate_project(self.project_root)
        bare, resolved_kind = _resolve_kind_hint(name, kind)

        if resolved_kind is None:
            matches = self._find_matches(bare)
            if not matches:
                raise ArtifactNotFoundError(name)
            if len(matches) > 1:
                raise AmbiguousArtifactError(bare, [k for k, _ in matches])
            resolved_kind = matches[0][0]

        validated_name = _validate_artifact_name(bare, resolved_kind)
        stack = _build_stack(self.project_root, resolved_kind, validated_name)
        if not stack:
            raise ArtifactNotFoundError(name)

        description = self._describe(resolved_kind, validated_name)
        return {
            "id": f"{resolved_kind}:{validated_name}",
            "name": validated_name,
            "kind": resolved_kind,
            "description": description,
            "stack": [layer.to_json_dict() for layer in stack],
        }

    # -------------------------------------------------------------- internals
    def _get_baseline(self) -> CoreBaseline:
        if self._baseline is None:
            self._baseline = CoreBaseline.load(self.project_root)
        return self._baseline

    def _find_matches(self, name: str) -> list[tuple[ArtifactKind, str]]:
        """Return every (kind, name) pair whose name matches exactly."""
        artifacts = self.list_artifacts()
        return [(a.kind, a.name) for a in artifacts if a.name == name]

    def _describe(self, kind: ArtifactKind, name: str) -> str:
        """Return the description that would appear on the flat-list row.

        Sources the value from :meth:`list_artifacts` so the two commands
        agree on the same string for the same artifact — the ``info`` output
        promises "matching the same field on 'artifact list --json'".
        """
        for artifact in self.list_artifacts():
            if artifact.kind == kind and artifact.name == name:
                return artifact.description
        return ""

    def _iter_contribution_artifacts(
        self,
    ) -> Iterable[tuple[ArtifactKind, str, str]]:
        """Yield ``(kind, name, description)`` for resolver-visible contributions.

        Covers the two ways a pack can contribute an artifact:

        * manifest-declared entries (``preset.yml`` / ``extension.yml``), read
          via each manifest class's own ``iter_contributions()`` rather than
          re-parsing ``provides`` by hand, and
        * convention-placed extension files (``commands/``, ``templates/``,
          ``scripts/``) that the resolver picks up even without a manifest.

        Presets are enumerated through ``PresetManager.list_installed()`` —
        presets have no unregistered-directory fallback in the resolver (see
        ``PresetResolver._get_all_presets_by_priority``), so the registry is
        the complete set. Extensions additionally admit unregistered
        directories at implicit priority 10 (see
        ``PresetResolver._get_all_extensions_by_priority``), so those are
        folded in alongside the registered set. Either way, every yielded
        contribution is still checked against the resolver's own
        ``collect_all_layers()`` output before being surfaced, so a disabled
        pack, an orphaned directory the resolver would not admit, or a
        declared-but-unusable entry cannot appear in the inventory.

        Project-local overrides under ``.specify/templates/overrides`` are
        included too, so an artifact that exists only as an override is still
        listed.

        Silent on any manifest that fails to parse — that would already be
        surfaced by ``specify preset list`` or ``specify extension list``, and
        this command's job is to describe the composed inventory, not to be
        the second validation surface.
        """
        from ..extensions import ExtensionManager, ExtensionManifest, ValidationError
        from ..presets import PresetManager, PresetResolver  # lazy: avoids circular import

        resolver = PresetResolver(self.project_root)
        layers_by_artifact: dict[tuple[ArtifactKind, str], set[str]] = {}

        def _lookup_ids(kind: ArtifactKind, name: str) -> set[str]:
            key = (kind, name)
            if key not in layers_by_artifact:
                layers_by_artifact[key] = {
                    candidate["lookupId"]
                    for candidate in resolver.collect_all_layers(name, kind)
                }
            return layers_by_artifact[key]

        # -- Presets: the registry is authoritative, no unregistered fallback.
        preset_manager = PresetManager(self.project_root)
        for entry in sorted(preset_manager.list_installed(), key=lambda e: e["id"]):
            pack_id = entry["id"]
            pack_dir = preset_manager.presets_dir / pack_id
            manifest = preset_manager.get_pack(pack_id)
            yield from self._iter_pack_contributions(
                manifest, pack_dir, "preset", _lookup_ids
            )

        # -- Extensions: registered ids plus on-disk unregistered directories,
        # mirroring PresetResolver._get_all_extensions_by_priority.
        ext_manager = ExtensionManager(self.project_root)
        registered_ext_ids = {e["id"] for e in ext_manager.list_installed()}
        ext_ids = set(registered_ext_ids)
        if ext_manager.extensions_dir.is_dir():
            ext_ids.update(
                p.name for p in ext_manager.extensions_dir.iterdir() if p.is_dir()
            )
        for ext_id in sorted(ext_ids):
            ext_dir = ext_manager.extensions_dir / ext_id
            if ext_id in registered_ext_ids:
                manifest = ext_manager.get_extension(ext_id)
            else:
                manifest_path = ext_dir / "extension.yml"
                manifest = None
                if manifest_path.is_file():
                    try:
                        manifest = ExtensionManifest(manifest_path)
                    except ValidationError:
                        manifest = None
            yield from self._iter_pack_contributions(manifest, ext_dir, "extension", _lookup_ids)

        yield from self._iter_project_override_artifacts(resolver)

    @staticmethod
    def _iter_pack_contributions(
        manifest: Any,
        pack_dir: Path,
        layer: str,
        lookup_ids: Callable[[ArtifactKind, str], set[str]],
    ) -> Iterable[tuple[ArtifactKind, str, str]]:
        """Yield ``(kind, name, description)`` for one preset or extension pack.

        ``manifest`` is a validated ``PresetManifest``/``ExtensionManifest``
        (or ``None`` if the pack has no usable manifest). Declared
        contributions come from the manifest's own ``iter_contributions()``;
        convention-placed files are scanned separately since they exist
        whether or not any manifest declares them.
        """
        if manifest is not None:
            for contribution in manifest.iter_contributions():
                kind = contribution.get("kind")
                name = contribution.get("name")
                if kind not in ("command", "template", "script"):
                    continue
                if not isinstance(name, str) or not name or ":" in name:
                    continue
                description = contribution.get("description", "")
                if not isinstance(description, str):
                    description = ""
                if contribution["id"] in lookup_ids(kind, name):
                    yield kind, name, description

        # Convention fallback: a preset/extension file placed at the
        # conventional path resolves whether or not the manifest declares it,
        # so it belongs in the inventory as well.
        for kind, name in _iter_convention_contributions(pack_dir):
            lookup_id = derive_named_id(layer, pack_dir.name, kind, name)
            if lookup_id in lookup_ids(kind, name):
                yield kind, name, ""

    def _iter_project_override_artifacts(
        self,
        resolver: Any,
    ) -> Iterable[tuple[ArtifactKind, str, str]]:
        """Yield ``(kind, name, "")`` for project-local override files.

        A root ``overrides/<name>.md`` file is the override for both the
        ``template`` and the ``command`` lookup of ``<name>``, so it is
        reported as a command when some other layer already provides that
        command and as a template otherwise. That keeps a command override
        from also appearing as a second, spurious ``template:`` row.

        A dotted name (``speckit.local``) is a command name under the
        resolver's own grammar (see ``_COMMAND_NAME_RE``) regardless of
        whether any lower, non-project layer backs it, so it is classified
        as a command even when the override is the only layer — matching
        the exact ID ``preset resolve``/``artifact info`` accepts for it.
        """
        overrides_dir = resolver.overrides_dir
        if not overrides_dir.is_dir():
            return
        for entry in sorted(overrides_dir.iterdir(), key=lambda p: p.name):
            if not entry.is_file() or entry.suffix != _TEMPLATE_SUFFIX:
                continue
            name = entry.stem
            command_layers = resolver.collect_all_layers(name, "command")
            backed_by_command = any(
                not str(layer.get("lookupId", "")).startswith(
                    f"{PROJECT_OVERRIDE_LAYER}:"
                )
                for layer in command_layers
            )
            is_command = backed_by_command or (
                "." in name and bool(_COMMAND_NAME_RE.fullmatch(name))
            )
            yield ("command" if is_command else "template"), name, ""
        scripts_dir = overrides_dir / "scripts"
        if not scripts_dir.is_dir():
            return
        for entry in sorted(scripts_dir.iterdir(), key=lambda p: p.name):
            if entry.is_file() and entry.suffix == _SCRIPT_SUFFIX:
                yield "script", entry.stem, ""


_CONVENTION_SUBDIRS: tuple[tuple[str, ArtifactKind, str], ...] = (
    ("commands", "command", _TEMPLATE_SUFFIX),
    ("templates", "template", _TEMPLATE_SUFFIX),
    ("scripts", "script", _SCRIPT_SUFFIX),
)


def _iter_convention_contributions(pack_dir: Path) -> Iterable[tuple[ArtifactKind, str]]:
    """Yield ``(kind, name)`` for files an extension exposes by convention.

    Only the conventional subdirectories are scanned; loose ``.md`` files at
    the extension root (``README.md`` and friends) are deliberately skipped so
    packaging files don't show up as templates.
    """
    for subdir, kind, suffix in _CONVENTION_SUBDIRS:
        candidate_dir = pack_dir / subdir
        if not candidate_dir.is_dir():
            continue
        for entry in sorted(candidate_dir.iterdir(), key=lambda p: p.name):
            if entry.is_file() and entry.suffix == suffix and ":" not in entry.stem:
                yield kind, entry.stem


__all__ = [
    "AmbiguousArtifactError",
    "Artifact",
    "ArtifactCatalog",
    "ArtifactError",
    "ArtifactKind",
    "ArtifactNotFoundError",
    "ArtifactResolutionError",
    "CoreBaseline",
    "LayerName",
    "NotASpecKitProjectError",
    "StackLayer",
    "Strategy",
]

_ = derive_named_id  # keep the import edge visible for tooling
