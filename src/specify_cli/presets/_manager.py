"""Preset installation, removal, and lifecycle coordination (private)."""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from packaging import version as pkg_version
from packaging.specifiers import InvalidSpecifier, SpecifierSet

from .._download_security import safe_extract_archive
from .._init_options import is_ai_skills_enabled, resolve_active_agent_for_registration
from .._utils import version_satisfies
from ..extensions import REINSTALL_COMMAND, normalize_priority
from ..shared_infra import (
    _ensure_safe_shared_destination,
    _ensure_safe_shared_directory,
    _write_shared_bytes,
    _write_shared_text,
)
from ._manager_commands import _PresetCommandMethods
from ._manager_skills import _PresetSkillMethods
from ._manifest import (
    PresetCompatibilityError,
    PresetError,
    PresetManifest,
    PresetValidationError,
)
from ._registry import PresetRegistry
from ._resolver import PresetResolver

_CONSTITUTION_PROVENANCE_FILE = ".constitution-template.json"
_CONSTITUTION_SYNC_PRESET_ID = "constitution-sync"


def _content_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_comparable_version(value: str) -> bool:
    """Return whether a recorded version can be evaluated against a specifier.

    ``version_satisfies()`` answers "does not satisfy" for an unparseable
    version, which is indistinguishable from a genuine mismatch. Callers that
    need to tell those apart check here first.
    """
    try:
        pkg_version.Version(value)
    except pkg_version.InvalidVersion:
        return False
    return True


def _constitution_is_generated(
    project_root: Path,
    memory_constitution: Path,
    resolver: "PresetResolver",
) -> bool:
    """Return whether the live constitution is an unchanged generated file."""
    _ensure_safe_shared_destination(project_root, memory_constitution)
    content = memory_constitution.read_bytes()
    provenance = memory_constitution.parent / _CONSTITUTION_PROVENANCE_FILE
    _ensure_safe_shared_destination(project_root, provenance)

    if provenance.exists():
        try:
            metadata = json.loads(provenance.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
        return (
            isinstance(metadata, dict)
            and metadata.get("sha256") == _content_sha256(content)
        )

    # Older projects have no provenance sidecar. Only the immutable bundled or
    # source-checkout core template is safe to treat as generated.
    core = resolver._find_bundled_core(
        "constitution-template", "template", ".md"
    )
    return core is not None and core.read_bytes() == content


def _constitution_provenance_matches_preset(
    project_root: Path,
    memory_constitution: Path,
    pack_id: str,
    pack_version: str,
) -> bool:
    """Return whether provenance identifies a preset as the materialized source."""
    provenance = memory_constitution.parent / _CONSTITUTION_PROVENANCE_FILE
    if not provenance.parent.exists():
        return False
    _ensure_safe_shared_destination(project_root, provenance)
    if not provenance.exists():
        return False
    try:
        metadata = json.loads(provenance.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    return (
        isinstance(metadata, dict)
        and metadata.get("source") == f"{pack_id} v{pack_version}"
    )


def _materialize_constitution_template(
    project_root: Path,
    memory_constitution: Path,
) -> str | None:
    """Materialize constitution-template content into memory/constitution.md.

    Returns:
        "copied" when the winning layer is ``replace`` and the source file is
        copied verbatim; "composed" when a composing strategy is materialized
        via ``resolve_content``; ``None`` when no constitution template resolves.
    """
    resolver = PresetResolver(project_root)
    layers = resolver.collect_all_layers("constitution-template", "template")
    if not layers:
        return None

    top_layer = layers[0]
    if top_layer["strategy"] == "replace":
        content = top_layer["path"].read_bytes()
        result = "copied"
    else:
        composed_content = resolver.resolve_content("constitution-template", "template")
        if composed_content is None:
            return None
        content = composed_content.encode("utf-8")
        result = "composed"

    _ensure_safe_shared_directory(project_root, memory_constitution.parent)
    _write_shared_bytes(project_root, memory_constitution, content)
    provenance = memory_constitution.parent / _CONSTITUTION_PROVENANCE_FILE
    _write_shared_text(
        project_root,
        provenance,
        json.dumps(
            {
                "sha256": _content_sha256(content),
                "source": top_layer["source"],
            },
            indent=2,
        )
        + "\n",
    )
    return result


# Generated files for script composition (#4551). Both carry no
# stack-specific data â€” only the script's own name â€” so they never need
# rewriting when priorities/enablement change; the dispatcher resolves the
# live chain on every invocation via `specify preset script-chain`. They are
# generated (not shipped under scripts/bash) so projects initialized before
# this feature get the runner too, and shared-infra inventories are unchanged.
_SCRIPT_DISPATCHER_MARKER = "# speckit-generated: script continuation dispatcher"
_SCRIPT_RUNNER_MARKER = "# speckit-generated: script continuation runner"
_SCRIPT_RUNNER_NAME = "continuation-runner.sh"
# Names the generated runtime relies on: a dispatcher for ``common`` would
# overwrite the library every dispatcher sources, and one for
# ``continuation-runner`` would overwrite the runner itself.
_RESERVED_SCRIPT_NAMES = frozenset({"common", "continuation-runner"})

_SCRIPT_CONTINUATION_DISPATCHER_TEMPLATE = """#!/usr/bin/env bash
# speckit-generated: script continuation dispatcher
# Generated by specify for the "{script_name}" script. Do not edit directly;
# customize via presets/overrides instead (`specify preset add`).
set -e
set -o pipefail

SCRIPT_DIR="$(CDPATH="" cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)
if command -v specify >/dev/null 2>&1; then
    SPECIFY_CMD=(specify)
elif command -v python3 >/dev/null 2>&1; then
    SPECIFY_CMD=(python3 -m specify_cli)
else
    echo "ERROR: 'specify' is required to resolve the '{script_name}' script chain" >&2
    exit 1
fi
# Strip carriage returns: on Windows the CLI emits CRLF, and $(...) only
# strips trailing newlines, so a stray CR would corrupt the exec path.
CHAIN=$( (cd "$REPO_ROOT" && "${{SPECIFY_CMD[@]}}" preset script-chain "{script_name}") | tr -d '\\r' ) || {{
    echo "ERROR: could not resolve the script chain for '{script_name}'" >&2
    exit 1
}}

TOP_LAYER=$(printf '%s\\n' "$CHAIN" | head -n 1)
REMAINING=$(printf '%s\\n' "$CHAIN" | tail -n +2)

if [[ -n "$REMAINING" ]]; then
    export SPECKIT_SCRIPT_CONTINUATION="$REMAINING"
    export CORE_SCRIPT="$SCRIPT_DIR/{runner_name}"
fi

# Run via bash so layers need no execute bit (preset copies keep source modes).
exec bash "$TOP_LAYER" "$@"
"""

_SCRIPT_CONTINUATION_RUNNER = """#!/usr/bin/env bash
# speckit-generated: script continuation runner
# Advances the script continuation one hop: consumes the head of
# SPECKIT_SCRIPT_CONTINUATION (newline-delimited remaining layers, highest
# priority first) and runs it, re-exporting the remainder so a further
# "wrap" layer's own $CORE_SCRIPT call continues correctly.
# Portable to bash 3.2: no mapfile or associative arrays.
set -e

if [[ -z "${SPECKIT_SCRIPT_CONTINUATION:-}" ]]; then
    echo "ERROR: continuation runner invoked with no remaining script layers" >&2
    exit 1
fi

__speckit_remaining=()
while IFS= read -r __speckit_line; do
    __speckit_line="${__speckit_line%$'\\r'}"
    [[ -n "$__speckit_line" ]] && __speckit_remaining+=("$__speckit_line")
done <<< "$SPECKIT_SCRIPT_CONTINUATION"

if [[ ${#__speckit_remaining[@]} -eq 0 ]]; then
    echo "ERROR: continuation runner found no remaining script layers" >&2
    exit 1
fi

__speckit_next="${__speckit_remaining[0]}"

if [[ ${#__speckit_remaining[@]} -gt 1 ]]; then
    SPECKIT_SCRIPT_CONTINUATION=$(printf '%s\\n' "${__speckit_remaining[@]:1}")
    export SPECKIT_SCRIPT_CONTINUATION
else
    unset SPECKIT_SCRIPT_CONTINUATION
fi

exec bash "$__speckit_next" "$@"
"""


class PresetManager(_PresetCommandMethods, _PresetSkillMethods):
    """Manages preset lifecycle: installation, removal, updates."""

    def __init__(self, project_root: Path):
        """Initialize preset manager.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.presets_dir = project_root / ".specify" / "presets"
        self.registry = PresetRegistry(self.presets_dir)

    def check_compatibility(
        self,
        manifest: PresetManifest,
        speckit_version: str
    ) -> bool:
        """Check if preset is compatible with current spec-kit version.

        Args:
            manifest: Preset manifest
            speckit_version: Current spec-kit version

        Returns:
            True if compatible

        Raises:
            PresetCompatibilityError: If pack is incompatible
        """
        required = manifest.requires_speckit_version
        # Defense in depth: the manifest validator now rejects a non-string
        # requires.speckit_version, but this method is public and also reachable
        # with a hand-built manifest object. ``InvalidSpecifier`` alone does not
        # cover a non-string -- scalars raise TypeError from the constructor, and
        # a list/dict is iterable so it constructs here and only breaks inside
        # .contains(). Reject up front so this always reports a
        # PresetCompatibilityError.
        if not isinstance(required, str):
            raise PresetCompatibilityError(
                "Invalid version specifier: expected a string, got "
                f"{type(required).__name__} ({required!r})"
            )
        try:
            SpecifierSet(required)  # Just to validate
        except InvalidSpecifier:
            raise PresetCompatibilityError(f"Invalid version specifier: {required}")

        if not version_satisfies(speckit_version, required):
            raise PresetCompatibilityError(
                f"Preset requires spec-kit {required}, "
                f"but {speckit_version} is installed.\n"
                f"Upgrade spec-kit with: {REINSTALL_COMMAND}"
            )

        return True

    def find_unmet_extension_dependencies(
        self,
        manifest: PresetManifest
    ) -> List[Dict[str, Any]]:
        """Find declared extension dependencies that are not satisfied.

        Reports rather than raises. A preset whose overrides call into an
        extension is written to degrade safely -- without the extension the
        core workflow still runs -- so a missing dependency is a warning, not
        an install failure. See issue #4231.

        Args:
            manifest: Preset manifest to inspect

        Returns:
            One entry per unsatisfied dependency, each with ``id``, the
            requested ``version`` specifier (``None`` when unconstrained), the
            ``installed`` version (``None`` when absent or unusable), and a
            ``reason`` of ``"missing"``, ``"corrupt"``, ``"stale"``,
            ``"disabled"``, or ``"version"``. Optional dependencies
            (``required: false``) are never reported.

            An unreadable registry yields no results rather than raising, since
            this runs after the install has already succeeded.

            A registry version that cannot be parsed is treated as
            uncomparable, not as a mismatch: the extension is installed and
            usable, and only its recorded version is unreadable. An extension
            present on disk but absent from the registry is likewise treated as
            satisfied, because resolution admits unregistered directories.
        """
        # Defense in depth, mirroring check_compatibility(): this method is
        # public and also reachable with a hand-built manifest object that
        # predates this field. A manifest without it declares nothing.
        candidates = getattr(manifest, "requires_extensions", None)
        if not isinstance(candidates, list):
            return []

        # Collapse exact repeats so a manifest naming the same dependency twice
        # warns once. Two entries for one id with *different* constraints are
        # kept, since both genuinely have to hold.
        declared: List[Dict[str, Any]] = []
        seen: Set[tuple] = set()
        for dep in candidates:
            if not isinstance(dep, dict) or not dep.get("required", True):
                continue
            key = (dep.get("id"), dep.get("version"))
            if key in seen:
                continue
            seen.add(key)
            declared.append(dep)
        if not declared:
            return []

        extensions_dir = self.project_root / ".specify" / "extensions"
        try:
            from . import ExtensionRegistry

            registry = ExtensionRegistry(extensions_dir)
            registered_ids = registry.keys()
            registry_corrupt = registry.is_corrupt()
        except OSError:
            # Both reads can raise: _load() recovers from malformed content but
            # deliberately lets OSError through, and is_corrupt() re-reads the
            # file. This check runs *after* the install has completed, and
            # preset_add only handles preset-domain errors, so letting that
            # escape would turn a finished install into a traceback over a
            # warning. An unreadable registry simply cannot be inspected.
            return []

        unmet: List[Dict[str, Any]] = []

        for dep in declared:
            metadata = registry.get(dep["id"])
            if metadata is None:
                # An absent registry entry does not mean the extension is
                # unusable. _get_all_extensions_by_priority() admits a safe
                # on-disk directory as an unregistered extension at implicit
                # priority 10, so it resolves and the preset works -- but only
                # when the registry is readable, since a corrupt one makes that
                # path fail closed and contribute nothing.
                #
                # get() returns None for a corrupted (non-dict) entry as well as
                # an absent one, but keys() retains corrupted ids -- both so
                # resolution does not re-admit their directories as
                # unregistered, and because is_installed() still counts them, so
                # a plain `extension add` would be refused as already installed.
                # That is a different state from absent, and needs a different
                # remedy.
                if dep["id"] in registered_ids:
                    unmet.append({**dep, "installed": None, "reason": "corrupt"})
                    continue
                if (
                    (extensions_dir / dep["id"]).is_dir()
                    and PresetResolver._is_safe_registry_id(dep["id"])
                    and not registry_corrupt
                ):
                    # Unregistered means no recorded version, so a constraint
                    # cannot be evaluated -- uncomparable, not unsatisfied.
                    continue
                unmet.append({**dep, "installed": None, "reason": "missing"})
                continue

            installed_version = metadata.get("version")
            installed_version = (
                installed_version if isinstance(installed_version, str) else None
            )

            # A registry entry is not proof the extension can contribute. If
            # its directory is gone, PresetResolver skips it outright (both
            # template lookup and layer collection guard on ``is_dir()``), so
            # the preset is as inert as if it were never installed -- but the
            # surviving entry would otherwise read as satisfied.
            if not (extensions_dir / dep["id"]).is_dir():
                unmet.append(
                    {**dep, "installed": installed_version, "reason": "stale"}
                )
                continue

            # A disabled extension is registered but contributes nothing:
            # resolution skips it (see _collect_extension_layers), so the
            # preset is just as inert as if it were absent. Report it before
            # any version check -- enabling it is the prerequisite, and the
            # version may well be fine once it is.
            if not metadata.get("enabled", True):
                unmet.append(
                    {**dep, "installed": installed_version, "reason": "disabled"}
                )
                continue

            constraint = dep["version"]
            if not constraint:
                continue

            # A version that cannot be compared is not a mismatch. Absent or
            # non-string is one way to be unusable; an unparseable string such
            # as "unknown" is another, and version_satisfies() cannot tell them
            # apart -- it catches InvalidVersion and returns False, which would
            # report a mismatch against a version nobody can evaluate. Check
            # parseability up front so only real comparisons reach the warning.
            if installed_version is None or not _is_comparable_version(installed_version):
                continue
            if not version_satisfies(installed_version, constraint):
                unmet.append(
                    {**dep, "installed": installed_version, "reason": "version"}
                )

        return unmet

    def install_from_directory(
        self,
        source_dir: Path,
        speckit_version: str,
        priority: int = 10,
        force: bool = False,
        *,
        catalog_name: str | None = None,
    ) -> PresetManifest:
        """Install preset from a local directory.

        Args:
            source_dir: Path to preset directory
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)
            force: If True and the preset is already installed, remove it first

        Returns:
            Installed preset manifest

        Raises:
            PresetValidationError: If manifest is invalid or priority is invalid
            PresetCompatibilityError: If pack is incompatible
        """
        # Validate priority
        if priority < 1:
            raise PresetValidationError("Priority must be a positive integer (1 or higher)")

        manifest_path = source_dir / "preset.yml"
        manifest = PresetManifest(manifest_path)

        self.check_compatibility(manifest, speckit_version)

        if self.registry.is_installed(manifest.id):
            if not force:
                raise PresetError(
                    f"Preset '{manifest.id}' is already installed. "
                    f"Use 'specify preset remove {manifest.id}' first."
                )
            self.remove(manifest.id)

        dest_dir = self.presets_dir / manifest.id
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir)

        # Pre-register the preset so that composition resolution can see it
        # in the priority stack when resolving composed command content.
        normalized_catalog_name = (
            catalog_name.strip() if isinstance(catalog_name, str) else ""
        )
        source = (
            {"kind": "catalog", "catalog": normalized_catalog_name}
            if normalized_catalog_name
            else "local"
        )
        self.registry.add(manifest.id, {
            "version": manifest.version,
            "source": source,
            "manifest_hash": manifest.get_hash(),
            "enabled": True,
            "priority": priority,
            "registered_commands": {},
            "registered_skills": {},
        })

        registered_commands: Dict[str, List[str]] = {}
        registered_skills: Dict[str, List[str]] = {}
        try:
            # Register command overrides with AI agents and persist the result
            # immediately so cleanup can recover even if installation stops
            # before later phases complete.
            registered_commands = self._register_commands(manifest, dest_dir)
            self.registry.update(manifest.id, {
                "registered_commands": registered_commands,
            })

            # Update corresponding skills when skills mode was previously used
            # and persist that result as well.
            registered_skills = self._register_skills(manifest, dest_dir)
            self.registry.update(manifest.id, {
                "registered_skills": registered_skills,
            })
        except Exception:
            # Roll back all side effects. _register_skills persists each
            # successful write immediately, so reload that partial map when
            # a later template fails before the call can return.
            if registered_commands:
                self._unregister_commands(registered_commands)
            persisted_metadata = self.registry.get(manifest.id) or {}
            persisted_skills = persisted_metadata.get(
                "registered_skills", registered_skills
            )
            if persisted_skills:
                self._unregister_skills(
                    persisted_skills, dest_dir, restore_from_bundled_core=True
                )
            try:
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
            except OSError:
                pass  # best-effort cleanup; don't mask the original error
            self.registry.remove(manifest.id)
            raise

        # Reconcile all affected commands from the full priority stack so that
        # install order doesn't determine the winning command file.
        cmd_names = [
            t["name"]
            for t in manifest.templates
            if t.get("type") == "command"
        ]
        if cmd_names:
            try:
                self._reconcile_composed_commands(cmd_names)
                self._reconcile_skills(cmd_names)
            except Exception as exc:
                import warnings
                warnings.warn(
                    f"Post-install reconciliation failed for {manifest.id}: {exc}. "
                    f"Agent command files may not reflect the current priority stack.",
                    stacklevel=2,
                )

        # Scripts don't need the same repeated reconciliation as commands:
        # once a script name's canonical file is a continuation dispatcher,
        # it re-resolves the live stack on every invocation (#4551), so
        # later priority/enablement changes take effect without touching
        # this file again. Only install (here) and remove() ever need to
        # write it.
        script_names = [
            t["name"]
            for t in manifest.templates
            if t.get("type") == "script"
        ]
        for script_name in script_names:
            try:
                self._reconcile_script_chain(script_name)
            except Exception as exc:
                import warnings
                warnings.warn(
                    f"Post-install script reconciliation failed for "
                    f"{manifest.id} script '{script_name}': {exc}. "
                    f"Run 'specify preset script-chain {script_name}' to diagnose.",
                    stacklevel=2,
                )

        # TODO: constitution-sync is a named preset with core-owned side effects.
        # Give synchronization an explicit owner without changing its opt-in
        # behavior or overwriting authored constitutions.
        # Materialize constitution-template changes only for projects that opt
        # into the constitution-sync preset. The core /constitution command
        # resolves this template on demand; constitution-sync preserves the
        # previous install-time behavior for teams that want reviewed snapshots.
        self._seed_constitution_from_preset(manifest, dest_dir)

        return manifest

    def _reconcile_script_chain(self, script_name: str) -> None:
        """Materialize the project's canonical bash script for ``script_name``.

        Scripts are executed rather than read, so composition is resolved at
        *invocation* time (#4551): while any preset provides this script, the
        canonical ``.specify/scripts/bash/<name>.sh`` is a fixed dispatcher
        that resolves the live chain via ``specify preset script-chain``.
        Because it is used for every chain length (including one layer), later
        enable/disable/set-priority changes never require rewriting it. When
        no preset provides the script any more, the bundled core script is
        restored (or the generated dispatcher removed if there is no core).
        """
        if script_name in _RESERVED_SCRIPT_NAMES:
            raise PresetValidationError(
                f"Script name '{script_name}' is reserved for the generated "
                f"script continuation runtime and cannot be provided by a preset."
            )
        resolver = PresetResolver(self.project_root)
        chain = resolver.resolve_script_chain(script_name)
        scripts_dir = self.project_root / ".specify" / "scripts" / "bash"
        canonical = scripts_dir / f"{script_name}.sh"

        # Validate every ancestor (not just the leaf): a symlinked ``.specify``
        # would otherwise redirect the writes and the cleanup unlink outside
        # the project.
        _ensure_safe_shared_directory(self.project_root, scripts_dir)
        _ensure_safe_shared_destination(self.project_root, canonical)
        runner = scripts_dir / _SCRIPT_RUNNER_NAME
        _ensure_safe_shared_destination(self.project_root, runner)

        # Judge "provided by a preset" from every active declaration, not the
        # truncated chain: an extension's replace layer can end the chain
        # above a lower-priority preset, and a later set-priority or enable
        # change must still find the dispatcher already in place.
        preset_roots = (
            self.project_root / ".specify" / "presets",
            self.project_root / ".specify" / "templates" / "overrides",
        )
        provided_by_preset = bool(chain) and any(
            root in layer["path"].parents
            for layer in resolver.collect_all_layers(script_name, "script")
            for root in preset_roots
        )

        if provided_by_preset:
            _write_shared_text(self.project_root, runner, _SCRIPT_CONTINUATION_RUNNER)
            _write_shared_text(
                self.project_root,
                canonical,
                _SCRIPT_CONTINUATION_DISPATCHER_TEMPLATE.format(
                    script_name=script_name, runner_name=_SCRIPT_RUNNER_NAME
                ),
            )
            if os.name != "nt":
                for generated in (runner, canonical):
                    generated.chmod(generated.stat().st_mode | 0o111)
            return

        # No preset layer left: restore core, or drop a stale generated stub.
        if chain:
            _write_shared_text(
                self.project_root, canonical, chain[-1].read_text(encoding="utf-8")
            )
            # Command frontmatter executes this path directly, and
            # _write_shared_text writes 0644.
            if os.name != "nt":
                canonical.chmod(canonical.stat().st_mode | 0o111)
        elif canonical.is_file():
            first_line = canonical.read_text(encoding="utf-8").splitlines()[:2]
            if any(_SCRIPT_DISPATCHER_MARKER in line for line in first_line):
                canonical.unlink()

    def _seed_constitution_from_preset(
        self, manifest: PresetManifest, preset_dir: Path
    ) -> None:
        """Seed memory/constitution.md when constitution-sync opts into snapshots.

        Installing constitution-sync itself materializes the currently resolved
        stack. Later preset installs only reconcile when they provide a
        ``constitution-template``. Authored constitutions are never overwritten.
        """
        provides_constitution = manifest.id == _CONSTITUTION_SYNC_PRESET_ID or any(
            t.get("type") == "template" and t.get("name") == "constitution-template"
            for t in manifest.templates
        ) or any(
            (preset_dir / relative_path).is_file()
            for relative_path in (
                "templates/constitution-template.md",
                "constitution-template.md",
            )
        )
        if not provides_constitution:
            return

        self.reconcile_constitution(
            f"Failed to seed constitution from preset {manifest.id}",
            create_if_missing=True,
        )

    def reconcile_constitution(
        self, failure_context: str, *, create_if_missing: bool = False
    ) -> None:
        """Reconcile an opted-in generated constitution without failing a change."""
        try:
            self._reconcile_constitution(create_if_missing=create_if_missing)
        except (OSError, UnicodeDecodeError, PresetValidationError, ValueError) as exc:
            import warnings

            warnings.warn(
                f"{failure_context}: {exc}.",
                stacklevel=2,
            )

    def _reconcile_constitution(self, *, create_if_missing: bool = False) -> None:
        """Materialize the winning layer when constitution-sync is enabled."""
        sync_metadata = self.registry.get(_CONSTITUTION_SYNC_PRESET_ID)
        if sync_metadata is None or not sync_metadata.get("enabled", True):
            return

        memory_constitution = (
            self.project_root / ".specify" / "memory" / "constitution.md"
        )
        if not memory_constitution.exists() and not create_if_missing:
            return
        resolver = PresetResolver(self.project_root)
        if memory_constitution.exists() and not _constitution_is_generated(
            self.project_root, memory_constitution, resolver
        ):
            return
        _materialize_constitution_template(self.project_root, memory_constitution)

    def install_from_archive(
        self,
        archive_path: Path,
        speckit_version: str,
        priority: int = 10,
        force: bool = False,
        *,
        catalog_name: str | None = None,
    ) -> PresetManifest:
        """Install a preset from a supported archive.

        Args:
            archive_path: Path to a .zip, .tar.gz, or .tgz archive
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)
            force: If True and the preset is already installed, remove it first

        Returns:
            Installed preset manifest

        Raises:
            PresetValidationError: If manifest is invalid or priority is invalid
            PresetCompatibilityError: If pack is incompatible
        """
        # Validate priority early
        if priority < 1:
            raise PresetValidationError("Priority must be a positive integer (1 or higher)")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            safe_extract_archive(
                archive_path,
                temp_path,
                error_type=PresetValidationError,
            )

            pack_dir = temp_path
            manifest_path = pack_dir / "preset.yml"

            if not manifest_path.exists():
                subdirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    pack_dir = subdirs[0]
                    manifest_path = pack_dir / "preset.yml"

            if not manifest_path.exists():
                raise PresetValidationError(
                    "No preset.yml found in archive"
                )

            return self.install_from_directory(
                pack_dir,
                speckit_version,
                priority,
                force=force,
                catalog_name=catalog_name,
            )

    def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str,
        priority: int = 10,
        force: bool = False,
        *,
        catalog_name: str | None = None,
    ) -> PresetManifest:
        """Backward-compatible wrapper for archive installation."""
        return self.install_from_archive(
            zip_path,
            speckit_version,
            priority,
            force=force,
            catalog_name=catalog_name,
        )

    def remove(self, pack_id: str) -> bool:
        """Remove an installed preset.

        Args:
            pack_id: Preset ID

        Returns:
            True if pack was removed
        """
        if not self.registry.is_installed(pack_id):
            return False

        metadata = self.registry.get(pack_id)
        # Restore original skills when preset is removed
        registered_skills = metadata.get("registered_skills", []) if metadata else []
        if isinstance(registered_skills, list) and registered_skills:
            # Legacy flat-list registries predate per-agent provenance
            # tracking. Migration to the per-agent dict form previously
            # only happened during a rescaffold (register_enabled_presets_
            # for_agent); if the *first* post-upgrade operation is instead
            # `preset remove` (no intervening use/upgrade), the legacy
            # branch of _unregister_skills restores only the currently
            # active agent's directory, leaving this preset's overrides in
            # every previously active agent's directory orphaned. Infer
            # real per-agent ownership from the on-disk preset marker now,
            # while pack_id is still known, and hand the resulting mapping
            # through the same dict-based cleanup path already used for
            # non-legacy registries (#2948).
            from .. import load_init_options

            init_opts = load_init_options(self.project_root)
            fallback_agent = init_opts.get("ai") if isinstance(init_opts, dict) else None
            if not isinstance(fallback_agent, str):
                fallback_agent = ""
            registered_skills = self._infer_legacy_skill_provenance(
                [name for name in registered_skills if isinstance(name, str)],
                pack_id,
                fallback_agent=fallback_agent,
            )
        registered_commands = metadata.get("registered_commands", {}) if metadata else {}
        pack_dir = self.presets_dir / pack_id

        # Record which historical agents this preset's registered_commands
        # actually targeted, *before* any filtering below, so post-removal
        # reconciliation can restore a surviving lower-priority preset's
        # override into every one of those directories too — not only the
        # currently active agent's. Without this, removing a preset that
        # was rendered under a previously-active (now inactive) agent
        # deletes that agent's command file via _unregister_commands below,
        # but active-only reconciliation would only recreate the surviving
        # winner for the current agent, leaving the inactive integration
        # with a missing/stale file (#2948).
        try:
            from ..agents import CommandRegistrar as _CommandRegistrarForScope
        except ImportError:
            _CommandRegistrarForScope = None
        affected_command_agents = {
            agent_name
            for agent_name in registered_commands
            if _CommandRegistrarForScope is None
            or _CommandRegistrarForScope.AGENT_CONFIGS.get(agent_name, {}).get("extension") != "/SKILL.md"
        }

        # Collect ALL command names before filtering for reconciliation,
        # so commands registered only for skill-based agents are also
        # reconciled. Every command-type template's primary name is added
        # unconditionally (not just aliases) since ai_skills-mode presets
        # never populate registered_commands for command-backed
        # integrations (see _register_commands's ai_skills guard) — without
        # this, removing a skills-mode preset that overrides a command no
        # other preset registered "the normal way" would skip reconciliation
        # entirely and _unregister_skills would restore core/extension
        # content instead of a surviving lower-priority preset's override.
        removed_cmd_names = set()
        removed_script_names = set()
        removed_constitution = any(
            path.exists()
            for path in (
                pack_dir / "templates" / "constitution-template.md",
                pack_dir / "constitution-template.md",
            )
        )
        if metadata and isinstance(metadata.get("version"), str):
            memory_constitution = (
                self.project_root / ".specify" / "memory" / "constitution.md"
            )
            removed_constitution = removed_constitution or (
                _constitution_provenance_matches_preset(
                    self.project_root,
                    memory_constitution,
                    pack_id,
                    metadata["version"],
                )
            )
        for cmd_names in registered_commands.values():
            removed_cmd_names.update(cmd_names)
        manifest_path = pack_dir / "preset.yml"
        if manifest_path.exists():
            try:
                manifest = PresetManifest(manifest_path)
                for tmpl in manifest.templates:
                    if (
                        tmpl.get("type") == "template"
                        and tmpl.get("name") == "constitution-template"
                    ):
                        removed_constitution = True
                    if tmpl.get("type") == "command":
                        name = tmpl.get("name")
                        if isinstance(name, str):
                            removed_cmd_names.add(name)
                        for alias in tmpl.get("aliases", []):
                            if isinstance(alias, str):
                                removed_cmd_names.add(alias)
                    if tmpl.get("type") == "script":
                        name = tmpl.get("name")
                        if isinstance(name, str):
                            removed_script_names.add(name)
            except PresetValidationError:
                # Invalid manifest — skip alias extraction; primary command
                # names from registered_commands are still unregistered.
                pass

        affected_skill_dirs: Dict[
            Path, tuple[Optional[str], List[str]]
        ] = {}
        if registered_skills:
            restorable_skills = registered_skills
            # A skill tracked for a command-backed agent whose ai_skills is
            # now off is a leftover from a partially failed skills→command
            # toggle. Restoring it via _unregister_skills (and letting
            # _reconcile_skills reapply a surviving lower preset through
            # extra_skills_dirs) would hand the active command-mode agent a
            # skill artifact it must not have — its current representation
            # is the command file handled via registered_commands above.
            # Delete the preset-owned skill instead and keep its directory
            # out of restoration/reconciliation entirely (#2948). Inactive
            # agents' entries still restore as before.
            # The legacy branch above locally imports load_init_options,
            # shadowing the module-level name for this whole function.
            from .._init_options import load_init_options as _load_init_options

            resolved_active = resolve_active_agent_for_registration(
                self.project_root
            )
            if (
                isinstance(registered_skills, dict)
                and isinstance(resolved_active, str)
                and resolved_active in registered_skills
                and _CommandRegistrarForScope is not None
                and _CommandRegistrarForScope.AGENT_CONFIGS.get(
                    resolved_active, {}
                ).get("extension") != "/SKILL.md"
                and not is_ai_skills_enabled(
                    _load_init_options(self.project_root)
                )
            ):
                raw_names = registered_skills.get(resolved_active)
                stale_names = [
                    name
                    for name in (
                        raw_names if isinstance(raw_names, list) else []
                    )
                    if isinstance(name, str)
                ]
                restorable_skills = {
                    agent_name: names
                    for agent_name, names in registered_skills.items()
                    if agent_name != resolved_active
                }
                if stale_names:
                    self._delete_agent_preset_skills(
                        resolved_active, stale_names, pack_id
                    )
            override_sources = {
                skill_name: f"override:{command_name}"
                for command_name in removed_cmd_names
                for skill_name in self._skill_names_for_command(command_name)
            }
            affected_skill_dirs = self._unregister_skills(
                restorable_skills,
                pack_dir,
                additional_owned_sources=override_sources,
                restore_from_bundled_core=True,
            )
            try:
                from ..agents import CommandRegistrar
            except ImportError:
                CommandRegistrar = None
            if CommandRegistrar is not None:
                skill_coverage = (
                    registered_skills
                    if isinstance(registered_skills, dict)
                    else {}
                )
                commands_to_unregister: Dict[str, List[str]] = {}
                for agent_name, cmd_names in registered_commands.items():
                    is_native_skill_agent = (
                        CommandRegistrar.AGENT_CONFIGS.get(
                            agent_name, {}
                        ).get("extension")
                        == "/SKILL.md"
                    )
                    if not is_native_skill_agent:
                        commands_to_unregister[agent_name] = cmd_names
                        continue

                    raw_skill_names = skill_coverage.get(agent_name, [])
                    covered_skill_names = {
                        name
                        for name in (
                            raw_skill_names
                            if isinstance(raw_skill_names, list)
                            else []
                        )
                        if isinstance(name, str)
                    }
                    uncovered_commands = [
                        cmd_name
                        for cmd_name in cmd_names
                        if not isinstance(cmd_name, str)
                        or covered_skill_names.isdisjoint(
                            self._skill_names_for_command(cmd_name)
                        )
                    ]
                    if uncovered_commands:
                        commands_to_unregister[agent_name] = (
                            uncovered_commands
                        )
                registered_commands = commands_to_unregister

        # Unregister non-skill command files from AI agents.
        if registered_commands:
            self._unregister_commands(registered_commands)

        if pack_dir.exists():
            shutil.rmtree(pack_dir)

        self.registry.remove(pack_id)

        # Reconcile: if other presets still provide these commands,
        # re-resolve from the remaining stack so the next layer takes effect.
        if removed_cmd_names:
            try:
                self._reconcile_composed_commands(
                    list(removed_cmd_names), extra_agents=affected_command_agents
                )
                self._reconcile_skills(
                    list(removed_cmd_names), extra_skills_dirs=affected_skill_dirs
                )
            except Exception as exc:
                import warnings
                warnings.warn(
                    f"Post-removal reconciliation failed for {pack_id}: {exc}. "
                    f"Agent command files may be stale; reinstall affected presets "
                    f"or run 'specify preset add' to refresh.",
                    stacklevel=2,
                )

        if removed_script_names:
            for script_name in removed_script_names:
                try:
                    self._reconcile_script_chain(script_name)
                except Exception as exc:
                    import warnings
                    warnings.warn(
                        f"Post-removal script reconciliation failed for "
                        f"{pack_id} script '{script_name}': {exc}. "
                        f"Run 'specify preset script-chain {script_name}' to diagnose.",
                        stacklevel=2,
                    )

        if removed_constitution:
            try:
                self._reconcile_constitution()
            except (OSError, UnicodeDecodeError, PresetValidationError, ValueError) as exc:
                import warnings

                warnings.warn(
                    f"Post-removal constitution reconciliation failed for {pack_id}: "
                    f"{exc}. The live constitution may be stale.",
                    stacklevel=2,
                )

        return True

    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed presets with metadata.

        Returns:
            List of preset metadata dictionaries
        """
        result = []

        for pack_id, metadata in self.registry.list().items():
            # Ensure metadata is a dictionary to avoid AttributeError when using .get()
            if not isinstance(metadata, dict):
                metadata = {}
            pack_dir = self.presets_dir / pack_id
            manifest_path = pack_dir / "preset.yml"

            try:
                manifest = PresetManifest(manifest_path)
                provided_counts = {"commands": 0, "templates": 0, "scripts": 0, "hooks": 0}
                for template in manifest.templates:
                    provided_counts[f"{template['type']}s"] += 1
                author = manifest.author
                result.append({
                    "id": pack_id,
                    "name": manifest.name,
                    "version": metadata.get("version", manifest.version),
                    "description": manifest.description,
                    "enabled": metadata.get("enabled", True),
                    "installed_at": metadata.get("installed_at"),
                    "template_count": len(manifest.templates),
                    "tags": manifest.tags,
                    "priority": normalize_priority(metadata.get("priority")),
                    "_json_author": author if isinstance(author, str) and author else None,
                    "_json_source": metadata.get("source"),
                    "_json_provides": provided_counts,
                })
            except PresetValidationError:
                result.append({
                    "id": pack_id,
                    "name": pack_id,
                    "version": metadata.get("version", "unknown"),
                    "description": "⚠️ Corrupted preset",
                    "enabled": False,
                    "installed_at": metadata.get("installed_at"),
                    "template_count": 0,
                    "tags": [],
                    "priority": normalize_priority(metadata.get("priority")),
                    "_json_author": None,
                    "_json_source": metadata.get("source"),
                    "_json_provides": {"commands": 0, "templates": 0, "scripts": 0, "hooks": 0},
                })

        return result

    def get_pack(self, pack_id: str) -> Optional[PresetManifest]:
        """Get manifest for an installed preset.

        Args:
            pack_id: Preset ID

        Returns:
            Preset manifest or None if not installed
        """
        if not self.registry.is_installed(pack_id):
            return None

        pack_dir = self.presets_dir / pack_id
        manifest_path = pack_dir / "preset.yml"

        try:
            return PresetManifest(manifest_path)
        except PresetValidationError:
            return None
