"""Layered preset and extension resolution (private implementation)."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .._utils import dump_frontmatter
from ..extensions import ExtensionRegistry, normalize_priority
from ._manifest import VALID_PRESET_STRATEGIES, PresetManifest, PresetValidationError
from ._registry import PresetRegistry


class PresetResolver:
    """Resolves template names to file paths using a priority stack.

    Resolution order:
    1. .specify/templates/overrides/          - Project-local overrides
    2. .specify/presets/<preset-id>/          - Installed presets
    3. .specify/extensions/<ext-id>/templates/ - Extension-provided templates
    4. .specify/templates/                    - Core templates (shipped with Spec Kit)
    """

    def __init__(self, project_root: Path):
        """Initialize preset resolver.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.templates_dir = project_root / ".specify" / "templates"
        self.presets_dir = project_root / ".specify" / "presets"
        self.overrides_dir = self.templates_dir / "overrides"
        self.extensions_dir = project_root / ".specify" / "extensions"
        self._manifest_cache: Dict[str, Optional["PresetManifest"]] = {}

    def _get_manifest(self, pack_dir: Path) -> Optional["PresetManifest"]:
        """Get a cached preset manifest, parsing it on first access."""
        key = str(pack_dir)
        if key not in self._manifest_cache:
            manifest_path = pack_dir / "preset.yml"
            if manifest_path.exists():
                try:
                    self._manifest_cache[key] = PresetManifest(manifest_path)
                except PresetValidationError:
                    self._manifest_cache[key] = None
            else:
                self._manifest_cache[key] = None
        return self._manifest_cache[key]

    @staticmethod
    def _is_safe_registry_id(value: object) -> bool:
        return isinstance(value, str) and re.fullmatch(r"[a-z0-9-]+", value) is not None

    def _get_all_presets_by_priority(self) -> List[tuple[str, dict]]:
        registry = PresetRegistry(self.presets_dir)
        return [
            (pack_id, metadata)
            for pack_id, metadata in registry.list_by_priority()
            if self._is_safe_registry_id(pack_id)
        ]

    def _manifest_declared_template(
        self, pack_dir: Path, template_name: str, template_type: str
    ) -> tuple[dict | None, Path | None]:
        """Resolve a preset's manifest-declared template entry and usable file.

        Returns ``(entry, candidate)``:
        - ``entry`` is the matching ``provides.templates`` mapping, or ``None`` if
          the manifest is absent or does not list this ``(name, type)``.
        - ``candidate`` is the declared ``file:`` resolved under ``pack_dir`` IFF
          it is a regular file (``is_file()``); ``None`` otherwise — a missing,
          empty, or non-file (e.g. directory) declaration yields ``(entry, None)``.

        The manifest is authoritative: when it declares a template (``entry`` is
        not ``None``) but the file is unusable (``candidate`` is ``None``),
        callers must NOT fall back to the convention lookup — that would mask a
        typo or pick up an undeclared file. Shared by ``resolve()`` and
        ``collect_all_layers()`` so their manifest-first resolution cannot
        silently diverge again (the divergence this fix addressed).
        """
        manifest = self._get_manifest(pack_dir)
        if not manifest:
            return None, None
        for tmpl in manifest.templates:
            if tmpl.get("name") == template_name and tmpl.get("type") == template_type:
                file_path = tmpl.get("file")
                if file_path:
                    manifest_candidate = pack_dir / file_path
                    return tmpl, (
                        manifest_candidate if manifest_candidate.is_file() else None
                    )
                return tmpl, None
        return None, None

    def _extension_manifest_declared_template(
        self, ext_dir: Path, template_name: str, template_type: str
    ) -> tuple[dict | None, Path | None]:
        """Resolve an extension's manifest-declared command/template/script entry and usable file.

        Mirrors ``_manifest_declared_template`` (for presets): returns ``(entry, candidate)``
        where ``entry`` is the matching ``provides.<type>`` mapping, or ``None`` if the
        extension has no (valid) manifest or doesn't declare this ``(name, type)``.
        ``candidate`` is the declared ``file:`` resolved under ``ext_dir`` IFF it is a
        regular file that stays within ``ext_dir`` (guards against path traversal via a
        malformed manifest, mirroring ``resolve_extension_command_via_manifest``);
        ``None`` otherwise.

        The manifest is authoritative: when ``entry`` is not ``None`` but ``candidate`` is
        ``None``, callers must NOT fall back to convention-based lookup — that would mask
        a typo or pick up an undeclared file. Shared by ``resolve()`` and
        ``collect_all_layers()`` so their manifest-first resolution cannot silently
        diverge (the divergence flagged in review on #4012).
        """
        if template_type not in ("command", "template", "script"):
            return None, None
        ext_manifest_path = ext_dir / "extension.yml"
        if not ext_manifest_path.exists():
            return None, None
        from ..extensions import ExtensionManifest
        from ..extensions import ValidationError as ExtValidationError

        try:
            ext_manifest = ExtensionManifest(ext_manifest_path)
        except (ExtValidationError, yaml.YAMLError, OSError, TypeError, AttributeError):
            return None, None
        if template_type == "command":
            entries = ext_manifest.commands
        elif template_type == "template":
            entries = ext_manifest.templates
        else:
            entries = ext_manifest.scripts
        for entry in entries:
            if entry.get("name") != template_name:
                continue
            file_rel = entry.get("file")
            if not file_rel:
                return entry, None
            rel_path = Path(file_rel)
            if rel_path.is_absolute():
                return entry, None
            candidate = ext_dir / rel_path
            try:
                # Resolve only for the containment check, not for the
                # returned path -- resolving the returned path would follow
                # symlinks in ext_dir's ancestors (e.g. a symlinked tmp dir
                # on macOS) and diverge from the unresolved paths convention
                # lookup returns for the same directory.
                candidate.resolve().relative_to(ext_dir.resolve())  # raises ValueError if outside
            except (OSError, ValueError):
                return entry, None
            return entry, (candidate if candidate.is_file() else None)
        return None, None

    def _get_all_extensions_by_priority(self) -> list[tuple[int, str, dict | None]]:
        """Build unified list of registered and unregistered extensions sorted by priority.

        Registered extensions use their stored priority; unregistered directories
        get implicit priority=10. Results are sorted by (priority, ext_id) for
        deterministic ordering.

        Returns:
            List of (priority, ext_id, metadata_or_none) tuples sorted by priority.
        """
        if not self.extensions_dir.exists():
            return []

        registry = ExtensionRegistry(self.extensions_dir)
        # Fail closed on a corrupt registry. ExtensionRegistry._load() recovers
        # by normalizing an unreadable registry to an empty mapping, which would
        # otherwise cause the directory scan below to admit every on-disk
        # directory as an unregistered, enabled extension — a fail-open path
        # that could supply constitution content from an invalid registry state.
        if registry.is_corrupt():
            raise PresetValidationError(
                f"Invalid extension registry {registry.registry_path}: "
                "refusing to enumerate extensions"
            )
        # Use keys() to track ALL extensions (including corrupted entries) without deep copy
        # This prevents corrupted entries from being picked up as "unregistered" dirs
        registered_extension_ids = registry.keys()

        # Get all registered extensions including disabled; we filter disabled manually below
        all_registered = registry.list_by_priority(include_disabled=True)

        all_extensions: list[tuple[int, str, dict | None]] = []

        # Only include enabled extensions in the result
        for ext_id, metadata in all_registered:
            if not self._is_safe_registry_id(ext_id):
                continue
            # Skip disabled extensions
            if not metadata.get("enabled", True):
                continue
            priority = normalize_priority(metadata.get("priority") if metadata else None)
            all_extensions.append((priority, ext_id, metadata))

        # Add unregistered directories with implicit priority=10
        for ext_dir in self.extensions_dir.iterdir():
            if not ext_dir.is_dir() or not self._is_safe_registry_id(ext_dir.name):
                continue
            if ext_dir.name not in registered_extension_ids:
                all_extensions.append((10, ext_dir.name, None))

        # Sort by (priority, ext_id) for deterministic ordering
        all_extensions.sort(key=lambda x: (x[0], x[1]))
        return all_extensions

    @staticmethod
    def _core_stem(template_name: str) -> Optional[str]:
        """Extract the stem for core command lookup.

        Commands use dot notation (e.g. ``speckit.specify``), but core
        command files are named by stem (e.g. ``specify.md``).  Returns
        the stem if *template_name* follows the ``speckit.<stem>`` pattern,
        or ``None`` otherwise.
        """
        if template_name.startswith("speckit."):
            return template_name[len("speckit."):]
        return None

    def resolve(
        self,
        template_name: str,
        template_type: str = "template",
        skip_presets: bool = False,
    ) -> Optional[Path]:
        """Resolve a template name to its file path.

        Walks the priority stack and returns the first match.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")
            skip_presets: When True, skip tier 2 (installed presets). Use
                resolve_core() as the preferred caller-facing API for this.

        Returns:
            Path to the resolved template file, or None if not found
        """
        # Determine subdirectory based on template type
        if template_type == "template":
            subdirs = ["templates", ""]
        elif template_type == "command":
            subdirs = ["commands"]
        elif template_type == "script":
            subdirs = ["scripts"]
        else:
            subdirs = [""]

        # Determine file extension based on template type
        ext = ".md"
        if template_type == "script":
            ext = ".sh"  # scripts use .sh; callers can also check .ps1

        # Priority 1: Project-local overrides
        if template_type == "script":
            override = self.overrides_dir / "scripts" / f"{template_name}{ext}"
        else:
            override = self.overrides_dir / f"{template_name}{ext}"
        if override.exists():
            return override

        # Priority 2: Installed presets (sorted by priority — lower number wins)
        if not skip_presets and self.presets_dir.exists():
            for pack_id, _metadata in self._get_all_presets_by_priority():
                pack_dir = self.presets_dir / pack_id
                # The preset manifest is authoritative: if it declares this
                # template with an explicit ``file:``, resolve to that path —
                # and do NOT fall back to convention when it's missing, to
                # avoid masking typos or picking up an undeclared file. Only
                # when the manifest is absent or doesn't list this template do
                # we use the convention-based subdir lookup. Mirrors
                # collect_all_layers()/resolve_content() so resolve() and
                # resolve_with_source() agree with them instead of returning
                # the core template (or a stray convention file).
                entry, manifest_candidate = self._manifest_declared_template(
                    pack_dir, template_name, template_type
                )
                if manifest_candidate is not None:
                    return manifest_candidate
                if entry is not None:
                    # Manifest declares this template but the file is missing,
                    # non-file (e.g. a directory), or an empty/falsey ``file``
                    # value. The manifest is authoritative, so skip this pack's
                    # convention fallback rather than mask a typo — mirrors
                    # collect_all_layers().
                    continue
                for subdir in subdirs:
                    if subdir:
                        candidate = pack_dir / subdir / f"{template_name}{ext}"
                    else:
                        candidate = pack_dir / f"{template_name}{ext}"
                    if candidate.exists():
                        return candidate

        # Priority 3: Extension-provided templates (sorted by priority — lower number wins)
        for _priority, ext_id, _metadata in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            if not ext_dir.is_dir():
                continue
            # The extension manifest is authoritative, same as preset manifests
            # above: check it before convention-based lookup so a declared entry
            # at a non-conventional path wins over a stale conventional file.
            entry, manifest_candidate = self._extension_manifest_declared_template(
                ext_dir, template_name, template_type
            )
            if manifest_candidate is not None:
                return manifest_candidate
            if entry is not None:
                continue
            for subdir in subdirs:
                if subdir:
                    candidate = ext_dir / subdir / f"{template_name}{ext}"
                else:
                    candidate = ext_dir / f"{template_name}{ext}"
                if candidate.exists():
                    return candidate

        # Priority 4: Core templates
        if template_type == "template":
            core = self.templates_dir / f"{template_name}.md"
            if core.exists():
                return core
        elif template_type == "command":
            core = self.templates_dir / "commands" / f"{template_name}.md"
            if core.exists():
                return core
            # Fallback: speckit.<stem> → <stem>.md
            stem = self._core_stem(template_name)
            if stem:
                core = self.templates_dir / "commands" / f"{stem}.md"
                if core.exists():
                    return core
        elif template_type == "script":
            core = self.templates_dir / "scripts" / f"{template_name}{ext}"
            if core.exists():
                return core

        # Priority 5: Bundled core_pack (wheel install) or repo-root templates
        # (source-checkout / editable install).  This is the canonical home for
        # speckit's built-in command/template files and must always be checked
        # so that strategy:wrap presets can locate {CORE_TEMPLATE}.
        from specify_cli import (  # local import to avoid cycles
            _locate_core_pack,
            _repo_root,
        )
        _core_pack = _locate_core_pack()
        if _core_pack is not None:
            # Wheel install path
            if template_type == "template":
                candidate = _core_pack / "templates" / f"{template_name}.md"
            elif template_type == "command":
                candidate = _core_pack / "commands" / f"{template_name}.md"
                if not candidate.exists():
                    stem = self._core_stem(template_name)
                    if stem:
                        candidate = _core_pack / "commands" / f"{stem}.md"
            elif template_type == "script":
                candidate = _core_pack / "scripts" / f"{template_name}{ext}"
            else:
                candidate = _core_pack / f"{template_name}.md"
            if candidate.exists():
                return candidate
        else:
            # Source-checkout / editable install: templates live at repo root
            repo_root = _repo_root()
            if template_type == "template":
                candidate = repo_root / "templates" / f"{template_name}.md"
            elif template_type == "command":
                candidate = repo_root / "templates" / "commands" / f"{template_name}.md"
                if not candidate.exists():
                    stem = self._core_stem(template_name)
                    if stem:
                        candidate = repo_root / "templates" / "commands" / f"{stem}.md"
            elif template_type == "script":
                candidate = repo_root / "scripts" / f"{template_name}{ext}"
            else:
                candidate = repo_root / f"{template_name}.md"
            if candidate.exists():
                return candidate

        return None

    def resolve_core(
        self,
        template_name: str,
        template_type: str = "template",
    ) -> Optional[Path]:
        """Resolve while skipping installed presets (tier 2).

        Searches tiers 1, 3, 4, and 5 (bundled core_pack / repo-root fallback).
        Use when resolving {CORE_TEMPLATE} to guarantee the result is actual
        base content, never another preset's wrap output.
        """
        return self.resolve(template_name, template_type, skip_presets=True)

    def resolve_extension_command_via_manifest(self, cmd_name: str) -> Optional[Path]:
        """Resolve an extension command by consulting installed extension manifests.

        Walks installed extension directories in priority order, loads each
        extension.yml via ExtensionManifest, and looks up the command by its
        declared name to find the actual file path.  This is necessary because
        the manifest's ``provides.commands[].file`` field is authoritative and
        may differ from the command name
        (e.g. ``speckit.selftest.extension`` → ``commands/selftest.md``).

        Returns None if no manifest maps the given command name, so the caller
        can fall back to the name-based lookup.
        """
        if not self.extensions_dir.exists():
            return None

        from ..extensions import ExtensionManifest, ValidationError

        for _priority, ext_id, _metadata in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            manifest_path = ext_dir / "extension.yml"
            if not manifest_path.is_file():
                continue
            try:
                manifest = ExtensionManifest(manifest_path)
            except (ValidationError, OSError, TypeError, AttributeError):
                continue
            for cmd_info in manifest.commands:
                if cmd_info.get("name") != cmd_name:
                    continue
                file_rel = cmd_info.get("file")
                if not file_rel:
                    continue
                # Mirror the containment check in ExtensionManager to guard against
                # path traversal via a malformed manifest (e.g. file: ../../AGENTS.md).
                cmd_path = Path(file_rel)
                if cmd_path.is_absolute():
                    continue
                try:
                    ext_root = ext_dir.resolve()
                    candidate = (ext_root / cmd_path).resolve()
                    candidate.relative_to(ext_root)  # raises ValueError if outside
                except (OSError, ValueError):
                    continue
                if candidate.is_file():
                    return candidate
        return None

    def resolve_with_source(
        self,
        template_name: str,
        template_type: str = "template",
    ) -> Optional[Dict[str, str]]:
        """Resolve a template name and return source attribution.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")

        Returns:
            Dictionary with 'path' and 'source' keys, or None if not found
        """
        # Delegate to resolve() for the actual lookup, then determine source
        resolved = self.resolve(template_name, template_type)
        if resolved is None:
            return None

        resolved_str = str(resolved)

        # Determine source attribution
        if str(self.overrides_dir) in resolved_str:
            return {"path": resolved_str, "source": "project override"}

        if str(self.presets_dir) in resolved_str and self.presets_dir.exists():
            for pack_id, metadata in self._get_all_presets_by_priority():
                pack_dir = self.presets_dir / pack_id
                try:
                    resolved.relative_to(pack_dir)
                    version = metadata.get("version", "?")
                    return {
                        "path": resolved_str,
                        "source": f"{pack_id} v{version}",
                    }
                except ValueError:
                    continue

        for _priority, ext_id, ext_meta in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            if not ext_dir.is_dir():
                continue
            try:
                resolved.relative_to(ext_dir)
                if ext_meta:
                    version = ext_meta.get("version", "?")
                    return {
                        "path": resolved_str,
                        "source": f"extension:{ext_id} v{version}",
                    }
                else:
                    return {
                        "path": resolved_str,
                        "source": f"extension:{ext_id} (unregistered)",
                    }
            except ValueError:
                continue

        return {"path": resolved_str, "source": "core"}

    def collect_all_layers(
        self,
        template_name: str,
        template_type: str = "template",
    ) -> List[Dict[str, Any]]:
        """Collect all layers in the priority stack for a template.

        Returns layers from highest priority (checked first) to lowest priority.
        Each layer is a dict with 'path', 'source', and 'strategy' keys.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")

        Returns:
            List of layer dicts ordered highest-to-lowest priority.
        """
        if template_type == "template":
            subdirs = ["templates", ""]
        elif template_type == "command":
            subdirs = ["commands"]
        elif template_type == "script":
            subdirs = ["scripts"]
        else:
            subdirs = [""]

        ext = ".md"
        if template_type == "script":
            ext = ".sh"

        layers: List[Dict[str, Any]] = []

        def _find_in_subdirs(base_dir: Path) -> Optional[Path]:
            for subdir in subdirs:
                if subdir:
                    candidate = base_dir / subdir / f"{template_name}{ext}"
                else:
                    candidate = base_dir / f"{template_name}{ext}"
                if candidate.exists():
                    return candidate
            return None

        # Priority 1: Project-local overrides (always "replace" strategy)
        if template_type == "script":
            override = self.overrides_dir / "scripts" / f"{template_name}{ext}"
        else:
            override = self.overrides_dir / f"{template_name}{ext}"
        if override.exists():
            layers.append({
                "path": override,
                "source": "project override",
                "strategy": "replace",
            })

        # Priority 2: Installed presets (sorted by priority — lower number = higher precedence)
        if self.presets_dir.exists():
            for pack_id, metadata in self._get_all_presets_by_priority():
                pack_dir = self.presets_dir / pack_id
                # Read strategy and manifest file path from preset manifest
                strategy = "replace"
                manifest_has_strategy = False
                entry, manifest_candidate = self._manifest_declared_template(
                    pack_dir, template_name, template_type
                )
                if entry is not None:
                    strategy = entry.get("strategy", "replace")
                    manifest_has_strategy = "strategy" in entry
                # Use the manifest's declared file when it's a usable regular file;
                # only fall back to convention-based lookup when the manifest
                # doesn't list this template at all, so preset.yml stays
                # authoritative (a declared-but-unusable file skips convention —
                # parity with resolve()).
                candidate = None
                if manifest_candidate is not None:
                    candidate = manifest_candidate
                elif entry is None:
                    candidate = _find_in_subdirs(pack_dir)
                if candidate:
                    # Legacy fallback: if manifest doesn't explicitly declare a
                    # strategy, check the command file's frontmatter for any valid
                    # strategy. Skip when the manifest entry includes strategy key
                    # (even if it's "replace") to avoid overriding explicit declarations.
                    if not manifest_has_strategy and strategy == "replace" and template_type == "command":
                        try:
                            cmd_content = candidate.read_text(encoding="utf-8")
                            lines = cmd_content.splitlines(keepends=True)
                            if lines and lines[0].rstrip("\r\n") == "---":
                                fence_end = -1
                                for fi, fline in enumerate(lines[1:], start=1):
                                    if fline.rstrip("\r\n") == "---":
                                        fence_end = fi
                                        break
                                if fence_end > 0:
                                    fm_text = "".join(lines[1:fence_end])
                                    fm_data = yaml.safe_load(fm_text)
                                    if isinstance(fm_data, dict):
                                        fm_strategy = fm_data.get("strategy")
                                        if isinstance(fm_strategy, str) and fm_strategy.lower() in VALID_PRESET_STRATEGIES:
                                            strategy = fm_strategy.lower()
                        except (UnicodeDecodeError, yaml.YAMLError, OSError):
                            # Best-effort legacy frontmatter parsing: keep default
                            # strategy ("replace") when content is unreadable/invalid.
                            pass
                    version = metadata.get("version", "?") if metadata else "?"
                    layers.append({
                        "path": candidate,
                        "source": f"{pack_id} v{version}",
                        "strategy": strategy,
                    })

        # Priority 3: Extension-provided templates (always "replace")
        for _priority, ext_id, ext_meta in self._get_all_extensions_by_priority():
            ext_dir = self.extensions_dir / ext_id
            if not ext_dir.is_dir():
                continue
            # The extension manifest is authoritative, same as preset manifests
            # above: check it before convention-based lookup so a declared entry
            # at a non-conventional path wins over a stale conventional file, and
            # a declared-but-missing file isn't silently masked by convention.
            entry, candidate = self._extension_manifest_declared_template(
                ext_dir, template_name, template_type
            )
            if entry is None:
                candidate = _find_in_subdirs(ext_dir)
            if candidate:
                if ext_meta:
                    version = ext_meta.get("version", "?")
                    source = f"extension:{ext_id} v{version}"
                else:
                    source = f"extension:{ext_id} (unregistered)"
                layers.append({
                    "path": candidate,
                    "source": source,
                    "strategy": "replace",
                    "extension_id": ext_id,
                    "extension_dir": ext_dir,
                })

        # Priority 4: Core templates (always "replace")
        core = None
        if template_type == "template":
            c = self.templates_dir / f"{template_name}.md"
            if c.exists():
                core = c
        elif template_type == "command":
            c = self.templates_dir / "commands" / f"{template_name}.md"
            if c.exists():
                core = c
            else:
                # Fallback: speckit.<stem> → <stem>.md
                stem = self._core_stem(template_name)
                if stem:
                    c = self.templates_dir / "commands" / f"{stem}.md"
                    if c.exists():
                        core = c
        elif template_type == "script":
            c = self.templates_dir / "scripts" / f"{template_name}{ext}"
            if c.exists():
                core = c
        if core:
            layers.append({
                "path": core,
                "source": "core",
                "strategy": "replace",
            })
        else:
            # Priority 5: Bundled core_pack (wheel install) or repo-root
            # templates (source-checkout), matching resolve()'s tier-5 fallback.
            bundled = self._find_bundled_core(template_name, template_type, ext)
            if bundled:
                layers.append({
                    "path": bundled,
                    "source": "core (bundled)",
                    "strategy": "replace",
                })

        return layers

    def resolve_script_chain(self, script_name: str) -> List[Path]:
        """Return the ordered chain of files backing a script's continuation.

        Scripts are executed rather than merely read, so â€” unlike
        templates and commands â€” their composition doesn't need to be
        spliced into a single file ahead of time. A ``"wrap"`` script
        contains a literal ``$CORE_SCRIPT`` reference that a runtime
        continuation runner resolves hop by hop, so this returns the
        stack of files that reference forms, in priority order, rather
        than composed content.

        This walks the same priority stack as ``resolve_content()`` for
        ``template_type="script"``: the highest-priority layer down
        through the nearest layer with strategy ``"replace"``
        (inclusive), which terminates the chain â€” only ``"replace"`` and
        ``"wrap"`` are valid script strategies, so a chain longer than
        one entry always has a ``"wrap"`` top. Layers below the
        terminating ``"replace"`` layer are never reachable and are
        omitted, matching ``resolve_content()``.

        Returns an empty list when the script name has no layers, or
        when none of them has strategy ``"replace"`` (composition has no
        base to terminate on â€” the same condition under which
        ``resolve_content()`` returns ``None``).
        """
        layers = list(self.collect_all_layers(script_name, "script"))
        if not any(layer["strategy"] == "replace" for layer in layers):
            # collect_all_layers() only knows scripts/<name>.sh; the real
            # built-in Bash assets live under scripts/bash/.
            bundled = self._find_bundled_bash_script(script_name)
            if bundled is not None:
                layers.append(
                    {"path": bundled, "source": "core (bundled)", "strategy": "replace"}
                )
        if not layers:
            return []
        base_idx = next(
            (i for i, layer in enumerate(layers) if layer["strategy"] == "replace"),
            None,
        )
        if base_idx is None:
            return []
        chain_layers = layers[: base_idx + 1]
        for layer in chain_layers:
            if layer["strategy"] != "wrap":
                continue
            try:
                body = layer["path"].read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise PresetValidationError(
                    f"Cannot read wrap script '{layer['source']}': {exc}"
                ) from exc
            if "$CORE_SCRIPT" not in body:
                raise PresetValidationError(
                    f"Wrap strategy in '{layer['source']}' is missing the "
                    f"$CORE_SCRIPT placeholder; executing it would silently "
                    f"drop every lower layer."
                )
        return [layer["path"] for layer in chain_layers]

    def _find_bundled_bash_script(self, script_name: str) -> Optional[Path]:
        """Locate the built-in Bash script from the core pack or source tree."""
        try:
            from specify_cli import _locate_core_pack, _repo_root
        except ImportError:
            return None
        core_pack = _locate_core_pack()
        base = core_pack if core_pack is not None else _repo_root()
        candidate = base / "scripts" / "bash" / f"{script_name}.sh"
        return candidate if candidate.is_file() else None

    def _find_bundled_core(
        self,
        template_name: str,
        template_type: str,
        ext: str,
    ) -> Optional[Path]:
        """Find a core template from the bundled pack or source checkout.

        Mirrors the tier-5 fallback logic in ``resolve()`` so that
        ``collect_all_layers()`` can locate base layers even when
        ``.specify/templates/`` doesn't contain the core file.
        """
        try:
            from specify_cli import _locate_core_pack, _repo_root
        except ImportError:
            return None

        stem = self._core_stem(template_name)
        names = [template_name]
        if stem and stem != template_name:
            names.append(stem)

        core_pack = _locate_core_pack()
        if core_pack is not None:
            for name in names:
                if template_type == "template":
                    c = core_pack / "templates" / f"{name}.md"
                elif template_type == "command":
                    c = core_pack / "commands" / f"{name}.md"
                elif template_type == "script":
                    c = core_pack / "scripts" / f"{name}{ext}"
                else:
                    c = core_pack / f"{name}.md"
                if c.exists():
                    return c
        else:
            repo_root = _repo_root()
            for name in names:
                if template_type == "template":
                    c = repo_root / "templates" / f"{name}.md"
                elif template_type == "command":
                    c = repo_root / "templates" / "commands" / f"{name}.md"
                elif template_type == "script":
                    c = repo_root / "scripts" / f"{name}{ext}"
                else:
                    c = repo_root / f"{name}.md"
                if c.exists():
                    return c
        return None

    def resolve_content(
        self,
        template_name: str,
        template_type: str = "template",
    ) -> Optional[str]:
        """Resolve a template name and return composed content.

        Walks the priority stack and composes content using strategies:
        - replace (default): highest-priority content wins entirely
        - prepend: content is placed before lower-priority content
        - append: content is placed after lower-priority content
        - wrap: content contains {CORE_TEMPLATE} placeholder replaced
                with lower-priority content (or $CORE_SCRIPT for scripts)

        Composition is recursive — multiple composing presets chain.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")

        Returns:
            Composed content string, or None if not found
        """
        layers = self.collect_all_layers(template_name, template_type)
        if not layers:
            return None

        def _read_layer_content(layer: Dict[str, Any]) -> Optional[str]:
            """Read a layer's raw text, rewriting extension-relative subdir
            references (agents/, knowledge-base/, etc.) to their installed
            location when the layer is extension-provided (#2101).

            Extension layers are always inserted with strategy "replace"
            (see collect_all_layers), so a layer only ever needs this
            rewrite when it wins outright above or serves as the
            composition base below — never as a mid-stack composing
            (append/prepend/wrap) layer.

            Returns None when the layer cannot be read or decoded:
            collect_all_layers deliberately keeps a non-UTF-8 legacy layer
            (with its "replace" default) so unrelated commands still
            resolve, so the same tolerance must apply here — the documented
            contract is "Composed content string, or None if not found",
            not a raw UnicodeDecodeError at composition time.
            """
            try:
                text = layer["path"].read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return None
            extension_id = layer.get("extension_id")
            extension_dir = layer.get("extension_dir")
            if extension_id and extension_dir:
                from ..agents import CommandRegistrar

                text = CommandRegistrar.rewrite_extension_paths(
                    text, extension_id, extension_dir
                )
            return text

        # If the top (highest-priority) layer is replace, it wins entirely —
        # lower layers are irrelevant regardless of their strategies.
        if layers[0]["strategy"] == "replace":
            return _read_layer_content(layers[0])

        # Composition: build content bottom-up from the effective base.
        # The base is the nearest replace layer scanning from highest priority
        # downward. Only layers above the base contribute to composition.
        #
        # layers is ordered highest-priority first. We process in reverse.
        reversed_layers = list(reversed(layers))

        # Find the effective base: scan from highest priority (layers[0]) downward
        # to find the nearest replace layer. Only compose layers above that base.
        # layers is highest-priority first; reversed_layers is lowest first.
        base_layer_idx = None  # index in layers[] (highest-priority first)
        for idx, layer in enumerate(layers):
            if layer["strategy"] == "replace":
                base_layer_idx = idx
                break

        if base_layer_idx is None:
            return None  # no replace base found

        # Convert to reversed_layers index
        base_reversed_idx = len(layers) - 1 - base_layer_idx
        content = _read_layer_content(layers[base_layer_idx])
        if content is None:
            return None
        # Compose only the layers above the base (higher priority = lower index in layers,
        # higher index in reversed_layers). Process bottom-up from base+1.
        start_idx = base_reversed_idx + 1

        # For command composition, strip frontmatter from each layer to avoid
        # leaking YAML metadata into the composed body. The highest-priority
        # layer's frontmatter will be reattached at the end.
        is_command = template_type == "command"
        top_frontmatter_text = None
        base_frontmatter_text = None

        def _split_frontmatter(text: str) -> tuple:
            """Return (frontmatter_block_with_fences, body) or (None, text).

            Uses line-based fence detection (fence must be ``---`` on its
            own line) to avoid false matches on ``---`` inside YAML values.
            """
            lines = text.splitlines(keepends=True)
            if not lines or lines[0].rstrip("\r\n") != "---":
                return None, text

            fence_end = -1
            for i, line in enumerate(lines[1:], start=1):
                if line.rstrip("\r\n") == "---":
                    fence_end = i
                    break

            if fence_end == -1:
                return None, text

            fm_block = "".join(lines[:fence_end + 1]).rstrip("\r\n")
            body = "".join(lines[fence_end + 1:])
            return fm_block, body

        if is_command:
            fm, body = _split_frontmatter(content)
            if fm:
                top_frontmatter_text = fm
                base_frontmatter_text = fm
                content = body

        # Apply composition layers from bottom to top
        for layer in reversed_layers[start_idx:]:
            try:
                layer_content = layer["path"].read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                # Same tolerance as _read_layer_content: an unreadable layer
                # means the composed result cannot be produced.
                return None
            strategy = layer["strategy"]

            if is_command:
                fm, layer_body = _split_frontmatter(layer_content)
                layer_content = layer_body
                # Track the highest-priority frontmatter seen;
                # replace layers reset both top and base frontmatter since
                # they replace the entire command including metadata.
                if strategy == "replace":
                    top_frontmatter_text = fm
                    base_frontmatter_text = fm
                elif fm:
                    top_frontmatter_text = fm

            if strategy == "replace":
                content = layer_content
            elif strategy == "prepend":
                content = layer_content + "\n\n" + content
            elif strategy == "append":
                content = content + "\n\n" + layer_content
            elif strategy == "wrap":
                if template_type == "script":
                    placeholder = "$CORE_SCRIPT"
                else:
                    placeholder = "{CORE_TEMPLATE}"
                if placeholder not in layer_content:
                    raise PresetValidationError(
                        f"Wrap strategy in '{layer['source']}' is missing "
                        f"the {placeholder} placeholder. The wrapper must "
                        f"contain {placeholder} to indicate where the "
                        f"lower-priority content should be inserted."
                    )
                content = layer_content.replace(placeholder, content)

        # Reattach the highest-priority frontmatter for commands,
        # inheriting scripts/agent_scripts from the base if missing
        # and stripping the strategy key (internal-only, not for agent output).
        if is_command and top_frontmatter_text:
            def _parse_fm_yaml(fm_block: str) -> dict:
                """Parse YAML from a frontmatter block (with --- fences)."""
                lines = fm_block.splitlines()
                # Parse only interior lines (between --- fences)
                if len(lines) >= 2:
                    yaml_lines = lines[1:-1]
                else:
                    yaml_lines = []
                try:
                    return yaml.safe_load("\n".join(yaml_lines)) or {}
                except yaml.YAMLError:
                    return {}

            top_fm = _parse_fm_yaml(top_frontmatter_text)

            # Inherit scripts/agent_scripts from base frontmatter if missing
            if base_frontmatter_text and base_frontmatter_text != top_frontmatter_text:
                base_fm = _parse_fm_yaml(base_frontmatter_text)
                for key in ("scripts", "agent_scripts", "argument-hint"):
                    if key not in top_fm and key in base_fm:
                        top_fm[key] = base_fm[key]

            # Strip strategy key — it's an internal composition directive,
            # not meant for rendered agent command files
            top_fm.pop("strategy", None)

            if top_fm:
                top_frontmatter_text = (
                    "---\n"
                    + dump_frontmatter(top_fm)
                    + "\n---"
                )
            else:
                # Empty frontmatter — omit rather than emitting {}
                top_frontmatter_text = None

            if top_frontmatter_text:
                content = top_frontmatter_text + "\n\n" + content

        return content
