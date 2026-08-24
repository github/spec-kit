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
from typing import Any, Iterable, Literal

import yaml

from .._assets import _locate_core_pack, _repo_root
from .._identifier import derive_named_id
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
    The contract regex is ``^(unknown artifact |ambiguous artifact |not a Spec Kit project)``.
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


# ---------------------------------------------------------------------------
# Core-baseline enumeration
# ---------------------------------------------------------------------------

_TEMPLATE_SUFFIX = ".md"


@dataclass(frozen=True)
class _CoreBaselineRow:
    name: str
    kind: ArtifactKind
    path: Path
    description: str


def _core_asset_root(subdir: str) -> Path | None:
    """Return the on-disk directory holding a family of core assets, or None.

    Prefers the wheel-installed ``core_pack`` bundle, then falls back to the
    source-checkout layout. Mirrors the two-tier resolution used by
    :func:`_load_core_command_names` and :meth:`PresetResolver._find_bundled_core`
    so all three code paths agree on what "core" means on this machine.
    """
    core = _locate_core_pack()
    if core is not None:
        candidate = core / subdir
        if candidate.is_dir():
            return candidate
    if subdir == "commands":
        candidate = _repo_root() / "templates" / "commands"
    elif subdir == "templates":
        candidate = _repo_root() / "templates"
    elif subdir == "scripts":
        candidate = _repo_root() / "scripts"
    else:  # pragma: no cover — internal misuse
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


def _enumerate_core_commands() -> list[_CoreBaselineRow]:
    """Enumerate every command shipped in the core baseline.

    Names are surfaced with the ``speckit.`` prefix so they collide with
    preset/extension contributions in a stable way — this is what the id
    grammar ``command:speckit.constitution`` requires.
    """
    from ..extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

    commands_dir = _core_asset_root("commands")
    rows: list[_CoreBaselineRow] = []
    if commands_dir is None:
        return rows
    for stem in sorted(CORE_COMMAND_NAMES):
        path = commands_dir / f"{stem}.md"
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        rows.append(
            _CoreBaselineRow(
                name=f"speckit.{stem}",
                kind="command",
                path=path,
                description=_extract_frontmatter_description(text),
            )
        )
    return rows


def _enumerate_core_templates() -> list[_CoreBaselineRow]:
    templates_dir = _core_asset_root("templates")
    rows: list[_CoreBaselineRow] = []
    if templates_dir is None:
        return rows
    for entry in sorted(templates_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_file() or entry.suffix != _TEMPLATE_SUFFIX:
            continue
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


def _enumerate_core_scripts() -> list[_CoreBaselineRow]:
    scripts_dir = _core_asset_root("scripts")
    rows: list[_CoreBaselineRow] = []
    if scripts_dir is None:
        return rows
    seen: dict[str, _CoreBaselineRow] = {}
    for runtime_dir in sorted(scripts_dir.iterdir(), key=lambda p: p.name):
        if not runtime_dir.is_dir():
            continue
        for entry in sorted(runtime_dir.iterdir(), key=lambda p: p.name):
            if not entry.is_file():
                continue
            name = canonical_script_name(entry)
            if name is None:
                continue
            if name in seen:
                continue
            try:
                text = entry.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                text = ""
            seen[name] = _CoreBaselineRow(
                name=name,
                kind="script",
                path=entry,
                description=_extract_script_description(text),
            )
    rows.extend(sorted(seen.values(), key=lambda r: r.name))
    return rows


@dataclass(frozen=True)
class CoreBaseline:
    """The union of the three core enumerators, indexed for O(1) lookup."""

    commands: tuple[_CoreBaselineRow, ...]
    templates: tuple[_CoreBaselineRow, ...]
    scripts: tuple[_CoreBaselineRow, ...]

    @classmethod
    def load(cls) -> "CoreBaseline":
        return cls(
            commands=tuple(_enumerate_core_commands()),
            templates=tuple(_enumerate_core_templates()),
            scripts=tuple(_enumerate_core_scripts()),
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
    Core layers return ``None`` — they have no on-disk manifest that ships
    with the project. Non-core layers walk upward from the contribution file
    until they find the preset's ``preset.yml`` or the extension's
    ``extension.yml``, then relativize against ``project_root``.

    Uses ``as_posix()`` so the string is stable across Windows and POSIX —
    a caller comparing snapshots between operating systems gets the same
    value on both.
    """
    lookup_id = layer.get("lookupId", "")
    if lookup_id.startswith("core:"):
        return None
    source = layer.get("path")
    if not isinstance(source, Path):
        return None
    manifest = _find_enclosing_manifest(source)
    if manifest is None:
        return None
    try:
        rel = manifest.relative_to(project_root)
    except ValueError:
        return manifest.as_posix()
    return rel.as_posix()


def _find_enclosing_manifest(path: Path) -> Path | None:
    """Walk parents of ``path`` looking for preset.yml or extension.yml."""
    for parent in path.parents:
        for name in ("preset.yml", "extension.yml"):
            candidate = parent / name
            if candidate.is_file():
                return candidate
    return None


def _preset_display_name(pack_dir: Path, pack_id: str) -> str:
    """Return the preset's human-friendly name from ``preset.yml``.

    Falls back to the pack id when the manifest is missing or lacks a
    ``metadata.name`` value.
    """
    manifest_path = pack_dir / "preset.yml"
    if not manifest_path.is_file():
        return pack_id
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return pack_id
    if not isinstance(data, dict):
        return pack_id
    preset = data.get("preset")
    if isinstance(preset, dict):
        display = preset.get("name")
        if isinstance(display, str) and display:
            return display
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

        # Layer classification: prefer lookupId prefix (authoritative) with a
        # source-string fallback for defensive parsing.
        if lookup_id.startswith("core:") or source.startswith("core"):
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

        if lookup_id.startswith("project:") or source == "project override":
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

        if lookup_id.startswith("extension:") or source.startswith("extension:"):
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

        stack = _build_stack(self.project_root, resolved_kind, bare)
        if not stack:
            raise ArtifactNotFoundError(name)

        description = self._describe(resolved_kind, bare)
        return {
            "id": f"{resolved_kind}:{bare}",
            "name": bare,
            "kind": resolved_kind,
            "description": description,
            "stack": [layer.to_json_dict() for layer in stack],
        }

    # -------------------------------------------------------------- internals
    def _get_baseline(self) -> CoreBaseline:
        if self._baseline is None:
            self._baseline = CoreBaseline.load()
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

        Silent on any manifest that fails to parse — that would already be
        surfaced by ``specify preset list`` or ``specify extension list``, and
        this command's job is to describe the composed inventory, not to be
        the second validation surface.
        """
        from ..presets import PresetResolver  # lazy: avoids circular import

        specify_dir = self.project_root / ".specify"
        resolver = PresetResolver(self.project_root)
        layers_by_artifact: dict[tuple[ArtifactKind, str], set[str]] = {}
        for tier in ("presets", "extensions"):
            tier_dir = specify_dir / tier
            if not tier_dir.is_dir():
                continue
            for pack_dir in sorted(tier_dir.iterdir(), key=lambda p: p.name):
                if not pack_dir.is_dir():
                    continue
                manifest_name = "preset.yml" if tier == "presets" else "extension.yml"
                manifest = pack_dir / manifest_name
                if not manifest.is_file():
                    continue
                try:
                    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, yaml.YAMLError):
                    continue
                if not isinstance(data, dict):
                    continue
                layer = "preset" if tier == "presets" else "extension"
                for kind, name, description in _iter_manifest_contributions(
                    data, is_preset=tier == "presets"
                ):
                    lookup_id = derive_named_id(layer, pack_dir.name, kind, name)
                    key = (kind, name)
                    if key not in layers_by_artifact:
                        layers_by_artifact[key] = {
                            candidate["lookupId"]
                            for candidate in resolver.collect_all_layers(name, kind)
                        }
                    if lookup_id in layers_by_artifact[key]:
                        yield kind, name, description


def _iter_manifest_contributions(
    data: dict[str, Any],
    *,
    is_preset: bool = False,
) -> Iterable[tuple[ArtifactKind, str, str]]:
    """Yield ``(kind, name, description)`` entries declared by a manifest.

    Extension manifests group entries by artifact kind:

    .. code-block:: yaml

        provides:
          commands: [ {name: "...", description: "..."} , ... ]
          templates: [ ... ]
          scripts: [ ... ]

    Preset manifests instead place every contribution under ``templates`` and
    identify its artifact kind with each entry's ``type`` field.

    Anything malformed at the entry level is skipped rather than raised —
    the artifact command is a projection, not a validator.
    """
    provides = data.get("provides")
    if not isinstance(provides, dict):
        return
    if is_preset:
        entries = provides.get("templates")
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            kind_value = entry.get("type")
            name = entry.get("name")
            if kind_value not in ("command", "template", "script"):
                continue
            if not isinstance(name, str) or not name or ":" in name:
                continue
            description = entry.get("description", "")
            if not isinstance(description, str):
                description = ""
            yield kind_value, name, description
        return
    for kind_key, kind_value in (
        ("commands", "command"),
        ("templates", "template"),
        ("scripts", "script"),
    ):
        entries = provides.get(kind_key)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str):
                yield kind_value, entry, ""  # type: ignore[misc]
                continue
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name or ":" in name:
                continue
            description = entry.get("description", "")
            if not isinstance(description, str):
                description = ""
            yield kind_value, name, description  # type: ignore[misc]


__all__ = [
    "AmbiguousArtifactError",
    "Artifact",
    "ArtifactCatalog",
    "ArtifactError",
    "ArtifactKind",
    "ArtifactNotFoundError",
    "CoreBaseline",
    "LayerName",
    "NotASpecKitProjectError",
    "StackLayer",
    "Strategy",
]

_ = derive_named_id  # keep the import edge visible for tooling
