"""Artifact inventory and catalog logic. No Typer decorators.

Two public entry points:

* :meth:`ArtifactCatalog.list_artifacts` — flat inventory (id, name, kind, description).
* :meth:`ArtifactCatalog.get_artifact_info` — one row plus its full ordered stack.

Everything else in this module is internal machinery. Callers outside
:mod:`specify_cli.artifacts._commands` should not import the private helpers.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Literal

import yaml

from ._identifiers import (
    IdentifierComponentError,
    derive_public_id,
    validate_component,
)
from .models import (
    AmbiguousArtifactError,
    Artifact,
    ArtifactKind,
    ArtifactNotFoundError,
    ArtifactResolutionError,
    NotASpecKitProjectError,
)
from .resolution import _build_stack, _layer_provenance


_TEMPLATE_SUFFIX = ".md"
_SCRIPT_SUFFIX = ".sh"


def _resolve_script_reference(script_root: Path, token: str) -> Path | None:
    """Resolve a command script reference that remains inside *script_root*."""
    posix_path = PurePosixPath(token)
    windows_path = PureWindowsPath(token)
    if posix_path.anchor or windows_path.anchor:
        return None
    if ".." in posix_path.parts or ".." in windows_path.parts:
        return None

    relative = Path(token)
    if relative.parts and relative.parts[0] == "scripts":
        relative = Path(*relative.parts[1:])
    if not relative.parts:
        return None

    try:
        resolved_root = script_root.resolve()
        candidate = (resolved_root / relative).resolve()
        candidate.relative_to(resolved_root)
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_file() else None


def _locate_shared_asset_dir(subdir: str) -> Path | None:
    """Locate a core asset directory without changing shared asset behavior."""
    if subdir not in {"commands", "scripts", "templates"}:
        return None

    from .._assets import _locate_core_pack, _repo_root

    core_pack = _locate_core_pack()
    bundled = core_pack / subdir if core_pack is not None else None
    source = (
        _repo_root() / "templates" / "commands"
        if subdir == "commands"
        else _repo_root() / subdir
    )
    for candidate in (bundled, source):
        if candidate is not None and candidate.is_dir():
            return candidate
    return None


def _project_core_asset_root(project_root: Path | None, subdir: str) -> Path | None:
    """Return the project-local built-in-tier directory for an asset family, if present."""
    if project_root is None:
        return None
    if subdir not in {"commands", "scripts", "templates"}:
        return None  # pragma: no cover — internal misuse
    from ..presets import PresetResolver  # lazy: avoids circular import

    candidate = PresetResolver(project_root).templates_dir
    if subdir != "templates":
        candidate = candidate / subdir
    return candidate if candidate.is_dir() else None


def _core_command_logical_name(stem: str) -> str:
    return stem if stem.startswith("speckit.") else f"speckit.{stem}"


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

    Supports the three script runtimes Spec Kit ships:

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


def _describe_artifact_file(path: Path, kind: ArtifactKind) -> str:
    """Return the on-disk description for an artifact file, else ``""``.

    Routes to the same extractors the inventory uses so a project
    override reports its own metadata instead of inheriting the description
    of the core/preset layer it hides.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    if kind == "script":
        return _extract_script_description(text)
    return _extract_frontmatter_description(text)


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
    """Validate the structural identifier component constraints for ``name``."""
    try:
        return validate_component(name, f"{kind} name")
    except IdentifierComponentError as exc:
        raise ArtifactNotFoundError(name) from exc


def _is_valid_artifact_name_component(name: Any, kind: ArtifactKind) -> bool:
    """Return ``True`` when ``name`` can appear in an artifact identifier."""
    try:
        validate_component(name, f"{kind} name")
    except IdentifierComponentError:
        return False
    return True


class ArtifactCatalog:
    """Read-only view over one Spec Kit project's artifact inventory."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    # ------------------------------------------------------------------ list
    def list_artifacts(self) -> list[Artifact]:
        """Return every artifact Spec Kit exposes for this project, deduped.

        Sort order is deterministic — first by ``kind`` in the fixed
        ``["command", "template", "script"]`` order, then by ``name``.
        Returns an empty list when no artifacts are found rather than raising;
        a fresh install with no presets, no extensions, and no built-in assets is
        still a valid Spec Kit project.

        Skills (``.github/skills/**/SKILL.md``) are intentionally excluded —
        they are integration-specific output, not a shipped asset family.

        Descriptions are picked from the highest-priority layer that has one,
        not the first layer discovered — a built-in command that an active
        preset overrides must report the preset's description, and two
        competing packs must report the higher-precedence one's. Precedence
        is decided by :meth:`PresetResolver.collect_all_layers`'s own
        ordering (index 0 = winner), not by enumeration order here.
        """
        artifacts, _layers_cache, _resolver, _manifest_cache = self._collect_inventory()
        return artifacts

    def list_artifacts_with_stack(self) -> list[dict[str, Any]]:
        """Return list rows enriched with each artifact's full composition stack."""
        artifacts, layers_cache, resolver, manifest_cache = self._collect_inventory()
        rows: list[dict[str, Any]] = []
        for artifact in artifacts:
            stack = _build_stack(
                self.project_root,
                artifact.kind,
                artifact.name,
                raw_layers=layers_cache.get((artifact.kind, artifact.name)),
                resolver=resolver,
                manifest_cache=manifest_cache,
            )
            row = artifact.to_json_dict()
            row["stack"] = [layer.to_json_dict() for layer in stack]
            rows.append(row)
        return rows

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
        bare, resolved_kind = _resolve_kind_hint(name, kind)

        # Project and registry validation happens once, inside
        # ``_collect_inventory`` below — the same chokepoint ``list_artifacts``
        # uses — so both public methods fail closed identically instead of
        # each re-implementing the checks.
        inventory, layers_cache, resolver, manifest_cache = self._collect_inventory()
        if resolved_kind is None:
            matches = [
                (artifact.kind, artifact.name)
                for artifact in inventory
                if artifact.name == bare
            ]
            if not matches:
                raise ArtifactNotFoundError(name)
            if len(matches) > 1:
                raise AmbiguousArtifactError(bare, [k for k, _ in matches])
            resolved_kind = matches[0][0]

        validated_name = _validate_artifact_name(bare, resolved_kind)
        artifact = next(
            (
                item
                for item in inventory
                if item.kind == resolved_kind and item.name == validated_name
            ),
            None,
        )
        if artifact is None:
            raise ArtifactNotFoundError(name)
        stack = _build_stack(
            self.project_root,
            resolved_kind,
            validated_name,
            raw_layers=layers_cache.get((resolved_kind, validated_name)),
            resolver=resolver,
            manifest_cache=manifest_cache,
        )
        if not stack:
            raise ArtifactNotFoundError(name)

        return {
            "id": derive_public_id(resolved_kind, validated_name),
            "name": validated_name,
            "kind": resolved_kind,
            "description": artifact.description,
            "stack": [layer.to_json_dict() for layer in stack],
        }

    # -------------------------------------------------------------- internals
    def _collect_inventory(
        self,
    ) -> tuple[
        list[Artifact],
        dict[tuple[ArtifactKind, str], list[dict[str, Any]]],
        Any,
        dict[Path, Any | None],
    ]:
        _validate_project(self.project_root)
        _validate_extension_registry(self.project_root)

        from ..presets import PresetError, PresetResolver  # lazy: avoids circular import

        resolver = PresetResolver(self.project_root)
        layers_cache: dict[tuple[ArtifactKind, str], list[dict[str, Any]]] = {}
        core_script_paths = self._selected_core_script_paths()

        def _layers_for(kind: ArtifactKind, name: str) -> list[dict[str, Any]]:
            key = (kind, name)
            if key not in layers_cache:
                try:
                    layers = resolver.collect_all_layers(name, kind)
                except (OSError, PresetError) as exc:
                    raise ArtifactResolutionError() from exc
                core_script = core_script_paths.get(name) if kind == "script" else None
                if core_script is not None and not any(
                    layer.get("source") in {"core", "core (bundled)"}
                    for layer in layers
                ):
                    layers.append(
                        {
                            "path": core_script,
                            "source": "core",
                            "strategy": "replace",
                        }
                    )
                layers_cache[key] = layers
            return layers_cache[key]

        def _has_any_replace_layer(layers: list[dict[str, Any]]) -> bool:
            return any(layer.get("strategy") == "replace" for layer in layers)

        names: set[tuple[ArtifactKind, str]] = set()
        try:
            for kind, name in self._iter_candidate_artifacts(
                resolver, core_script_paths
            ):
                key = (kind, name)
                if not _is_valid_artifact_name_component(name, kind):
                    continue
                # Resolve each candidate through Spec Kit's existing single-artifact
                # path for behavioral parity; optimize shared manifest reads only if
                # typical small extension sets show a measurable inventory cost.
                layers = _layers_for(kind, name)
                if layers and _has_any_replace_layer(layers):
                    names.add(key)
        except (OSError, PresetError) as exc:
            raise ArtifactResolutionError() from exc

        artifacts: list[Artifact] = []
        manifest_cache: dict[Path, Any | None] = {}
        for kind, name in names:
            description = ""
            for layer in _layers_for(kind, name):
                candidate = self._describe_layer(
                    resolver, layer, kind, name, manifest_cache
                )
                if candidate:
                    description = candidate
                    break
            artifacts.append(
                Artifact(
                    id=derive_public_id(kind, name),
                    name=name,
                    kind=kind,
                    description=description,
                )
            )

        kind_order = {"command": 0, "template": 1, "script": 2}
        return (
            sorted(artifacts, key=lambda a: (kind_order[a.kind], a.name)),
            layers_cache,
            resolver,
            manifest_cache,
        )

    def _iter_candidate_artifacts(
        self,
        resolver: Any,
        core_script_paths: dict[str, Path],
    ) -> Iterable[tuple[ArtifactKind, str]]:
        """Yield candidate ``(kind, name)`` pairs from every resolver tier.

        Covers the ways a pack can contribute an artifact:

        * manifest-declared entries (``preset.yml`` / ``extension.yml``), read
          through each manifest class's existing normalized properties, and
        * convention-placed extension files (``commands/``, ``templates/``,
          ``scripts/``) that the resolver picks up even without a manifest.

        Presets and extensions are enumerated through the resolver's existing
        priority helpers, so the candidate set follows the same install,
        enable, and priority rules as resolution. Project overrides and
        resolver-compatible core asset paths are included only as candidate
        names; :meth:`PresetResolver.collect_all_layers` remains the source of
        truth for which candidates are actually present and which layer wins.

        Project-local overrides under ``.specify/templates/overrides`` are
        included too, so an artifact that exists only as an override is still
        listed.

        Silent on any manifest that fails to parse — that would already be
        surfaced by ``specify preset list`` or ``specify extension list``, and
        this command's job is to describe the composed inventory, not to be
        the second validation surface.
        """
        from ..extensions import ExtensionManager, ExtensionManifest, ValidationError
        from ..presets import PresetManager  # lazy: avoids circular import

        # -- Presets: the registry is authoritative, no unregistered fallback.
        preset_manager = PresetManager(self.project_root)
        for pack_id, _metadata in resolver._get_all_presets_by_priority():
            pack_dir = preset_manager.presets_dir / pack_id
            manifest = preset_manager.get_pack(pack_id)
            yield from self._iter_pack_candidates(manifest, pack_dir, "preset")

        # -- Extensions: use the resolver's own extension enumeration order.
        ext_manager = ExtensionManager(self.project_root)
        for _priority, ext_id, metadata in resolver._get_all_extensions_by_priority():
            ext_dir = resolver.extensions_dir / ext_id
            if metadata is not None:
                manifest = ext_manager.get_extension(ext_id)
            else:
                manifest_path = ext_dir / "extension.yml"
                manifest = None
                if manifest_path.is_file():
                    try:
                        manifest = ExtensionManifest(manifest_path)
                    except (ValidationError, OSError, TypeError, AttributeError):
                        manifest = None
            yield from self._iter_pack_candidates(manifest, ext_dir, "extension")

        yield from self._iter_project_override_candidates(resolver)
        yield from self._iter_core_candidates(core_script_paths)

    @staticmethod
    def _iter_pack_candidates(
        manifest: Any,
        pack_dir: Path,
        layer: Literal["preset", "extension"],
    ) -> Iterable[tuple[ArtifactKind, str]]:
        """Yield manifest-declared and convention-based candidate names."""
        if manifest is not None:
            if layer == "preset":
                declarations = (
                    (entry.get("type"), entry)
                    for entry in manifest.templates
                    if isinstance(entry, dict)
                )
            else:
                declarations = (
                    (kind, entry)
                    for kind, entries in (
                        ("command", manifest.commands),
                        ("template", manifest.templates),
                        ("script", manifest.scripts),
                    )
                    for entry in entries
                    if isinstance(entry, dict)
                )
            for kind, contribution in declarations:
                name = contribution.get("name")
                if (
                    kind in ("command", "template", "script")
                    and isinstance(name, str)
                    and name
                    and ":" not in name
                ):
                    yield kind, name

        yield from ((kind, name) for kind, name, _path in _iter_convention_contributions(pack_dir))

    def _iter_project_override_candidates(
        self,
        resolver: Any,
    ) -> Iterable[tuple[ArtifactKind, str]]:
        """Yield candidate ``(kind, name)`` pairs for project overrides.

        A root ``overrides/<name>.md`` file is the override for both the
        ``template`` and the ``command`` lookup of ``<name>``. Both candidates
        are emitted and the normal inventory resolution path decides whether
        each is present.
        """
        overrides_dir = resolver.overrides_dir
        if not overrides_dir.is_dir():
            return
        for entry in sorted(overrides_dir.iterdir(), key=lambda p: p.name):
            if not entry.is_file() or entry.suffix != _TEMPLATE_SUFFIX:
                continue
            name = entry.stem
            if not _is_valid_artifact_name_component(name, "command"):
                continue
            for kind in ("command", "template"):
                yield kind, name
        scripts_dir = overrides_dir / "scripts"
        if not scripts_dir.is_dir():
            return
        for entry in sorted(scripts_dir.iterdir(), key=lambda p: p.name):
            if entry.is_file() and entry.suffix == _SCRIPT_SUFFIX:
                if not _is_valid_artifact_name_component(entry.stem, "script"):
                    continue
                yield "script", entry.stem

    def _iter_core_candidates(
        self, core_script_paths: dict[str, Path]
    ) -> Iterable[tuple[ArtifactKind, str]]:
        """Yield candidate names from resolver-compatible core asset paths."""
        from ..extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import
        from ..presets import PresetResolver

        project_commands_dir = _project_core_asset_root(self.project_root, "commands")
        bundled_commands_dir = _locate_shared_asset_dir("commands")
        command_dirs = tuple(
            directory
            for directory in (project_commands_dir, bundled_commands_dir)
            if directory is not None
        )
        command_names = {_core_command_logical_name(name) for name in CORE_COMMAND_NAMES}
        for directory in command_dirs:
            for entry in sorted(directory.iterdir(), key=lambda p: p.name):
                if entry.is_file() and entry.suffix == _TEMPLATE_SUFFIX:
                    command_names.add(_core_command_logical_name(entry.stem))
        for name in sorted(command_names):
            if any(
                (directory / f"{candidate}.md").is_file()
                for directory in command_dirs
                for candidate in (
                    name,
                    *(
                        (PresetResolver._core_stem(name),)
                        if PresetResolver._core_stem(name)
                        else ()
                    ),
                )
                if candidate is not None
            ):
                yield "command", name

        seen_templates: set[str] = set()
        for directory in (
            _project_core_asset_root(self.project_root, "templates"),
            _locate_shared_asset_dir("templates"),
        ):
            if directory is None:
                continue
            for entry in sorted(directory.iterdir(), key=lambda p: p.name):
                if (
                    entry.is_file()
                    and entry.suffix == _TEMPLATE_SUFFIX
                    and entry.stem not in seen_templates
                ):
                    seen_templates.add(entry.stem)
                    yield "template", entry.stem

        for directory in (
            _project_core_asset_root(self.project_root, "scripts"),
            _locate_shared_asset_dir("scripts"),
        ):
            if directory is None:
                continue
            for entry in sorted(directory.glob(f"*{_SCRIPT_SUFFIX}"), key=lambda p: p.name):
                yield "script", entry.stem
        yield from (("script", name) for name in sorted(core_script_paths))

    def _selected_core_script_paths(self) -> dict[str, Path]:
        """Return built-in scripts selected by the project's existing runtime policy."""
        from .._init_options import load_init_options
        from ..agents import CommandRegistrar
        from ..integrations.base import IntegrationBase

        command_dirs = tuple(
            directory
            for directory in (
                _project_core_asset_root(self.project_root, "commands"),
                _locate_shared_asset_dir("commands"),
            )
            if directory is not None
        )
        script_dirs = tuple(
            directory
            for directory in (
                _project_core_asset_root(self.project_root, "scripts"),
                _locate_shared_asset_dir("scripts"),
            )
            if directory is not None
        )
        requested = load_init_options(self.project_root).get("script")
        selected: dict[str, Path] = {}

        for command_dir in command_dirs:
            for template_path in sorted(command_dir.glob("*.md"), key=lambda p: p.name):
                try:
                    content = template_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                frontmatter, _body = CommandRegistrar.parse_frontmatter(content)
                scripts = frontmatter.get("scripts", {})
                if not isinstance(scripts, dict):
                    continue
                script_commands = {
                    key: value
                    for key, value in scripts.items()
                    if isinstance(key, str) and isinstance(value, str) and value.strip()
                }
                if not script_commands:
                    continue
                try:
                    variant = IntegrationBase.select_script_variant(
                        requested, script_commands
                    )
                    tokens = shlex.split(script_commands[variant], posix=True)
                except (KeyError, ValueError):
                    continue
                if not tokens:
                    continue

                path = None
                for script_dir in script_dirs:
                    path = _resolve_script_reference(script_dir, tokens[0])
                    if path is not None:
                        break
                if path is None:
                    continue
                name = path.stem.replace("_", "-") if variant == "py" else path.stem
                selected.setdefault(name, path)

        return selected

    def _describe_layer(
        self,
        resolver: Any,
        layer: dict[str, Any],
        kind: ArtifactKind,
        name: str,
        manifest_cache: dict[Path, Any | None],
    ) -> str:
        """Return manifest metadata or on-disk metadata for one resolver layer."""
        manifest_description = self._manifest_description_for_layer(
            resolver, layer, kind, name, manifest_cache
        )
        if manifest_description:
            return manifest_description
        path = layer.get("path")
        if isinstance(path, Path):
            return _describe_artifact_file(path, kind)
        return ""

    def _manifest_description_for_layer(
        self,
        resolver: Any,
        layer: dict[str, Any],
        kind: ArtifactKind,
        name: str,
        manifest_cache: dict[Path, Any | None],
    ) -> str:
        provenance = _layer_provenance(
            resolver, layer, kind, name, manifest_cache
        )
        entry = provenance.manifest_entry
        if entry is None:
            return ""
        description = entry.get("description", "")
        return description if isinstance(description, str) else ""


_CONVENTION_SUBDIRS: tuple[tuple[str, ArtifactKind, str], ...] = (
    ("commands", "command", _TEMPLATE_SUFFIX),
    ("templates", "template", _TEMPLATE_SUFFIX),
    ("scripts", "script", _SCRIPT_SUFFIX),
)


def _iter_convention_contributions(
    pack_dir: Path,
) -> Iterable[tuple[ArtifactKind, str, Path]]:
    """Yield ``(kind, name, path)`` for files exposed by convention.

    Templates are also accepted at the pack root for legacy compatibility,
    matching the resolver's ``templates/``-then-root lookup order.
    """
    for subdir, kind, suffix in _CONVENTION_SUBDIRS:
        candidate_dir = pack_dir / subdir
        if not candidate_dir.is_dir():
            continue
        for entry in sorted(candidate_dir.iterdir(), key=lambda p: p.name):
            if entry.is_file() and entry.suffix == suffix and ":" not in entry.stem:
                yield kind, entry.stem, entry
    if not pack_dir.is_dir():
        return
    for entry in sorted(pack_dir.iterdir(), key=lambda p: p.name):
        if (
            entry.is_file()
            and entry.suffix == _TEMPLATE_SUFFIX
            and ":" not in entry.stem
        ):
            yield "template", entry.stem, entry
