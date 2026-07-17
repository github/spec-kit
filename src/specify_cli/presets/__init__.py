"""
Preset Manager for Spec Kit

Handles installation, removal, and management of Spec Kit presets.
Presets are self-contained, versioned collections of templates
(artifact, command, and script templates) that can be installed to
customize the Spec-Driven Development workflow.
"""

import copy
import json
import hashlib
import os
import tempfile
import zipfile
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, List, Any

if TYPE_CHECKING:
    from ..agents import CommandRegistrar
from datetime import datetime, timezone
import re

import yaml
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet, InvalidSpecifier

from ..extensions import REINSTALL_COMMAND, ExtensionRegistry, normalize_priority
from .._init_options import is_ai_skills_enabled
from ..integrations.base import IntegrationBase
from .._utils import dump_frontmatter, version_satisfies
from ..shared_infra import (
    _ensure_safe_shared_destination,
    _ensure_safe_shared_directory,
    _write_shared_bytes,
    _write_shared_text,
    verify_archive_sha256,
)


_CONSTITUTION_PROVENANCE_FILE = ".constitution-template.json"


def _content_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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
    except (json.JSONDecodeError, UnicodeDecodeError):
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


def _substitute_core_template(
    body: str,
    cmd_name: str,
    project_root: "Path",
    registrar: "CommandRegistrar",
) -> "tuple[str, dict]":
    """Substitute {CORE_TEMPLATE} with the body of the installed core command template.

    Args:
        body: Preset command body (may contain {CORE_TEMPLATE} placeholder).
        cmd_name: Full command name (e.g. "speckit.git.feature" or "speckit.specify").
        project_root: Project root path.
        registrar: CommandRegistrar instance for parse_frontmatter.

    Returns:
        A tuple of (body, core_frontmatter) where body has {CORE_TEMPLATE} replaced
        by the core template body and core_frontmatter holds the core template's parsed
        frontmatter (so callers can inherit scripts/agent_scripts from it).  Both are
        unchanged / empty when the placeholder is absent or the core template file does
        not exist.
    """
    if "{CORE_TEMPLATE}" not in body:
        return body, {}

    # Derive the short name (strip "speckit." prefix) used by core command templates.
    short_name = cmd_name
    if short_name.startswith("speckit."):
        short_name = short_name[len("speckit."):]

    resolver = PresetResolver(project_root)
    # Resolution order for the core template:
    # 1. resolve_core(cmd_name) — covers tier-1 project overrides and tier-3/4
    #    name-based lookup (file named <cmd_name>.md).  Checked first so that a
    #    local override always wins, even for extension commands.
    # 2. resolve_extension_command_via_manifest(cmd_name) — manifest-based tier-3
    #    fallback for extension commands whose file is named differently from the
    #    command name (e.g. speckit.selftest.extension → commands/selftest.md).
    # 3. resolve_core(short_name) — core template fallback using the unprefixed
    #    name (e.g. specify → templates/commands/specify.md).
    # resolve_core() skips installed presets (tier 2) to prevent accidental nesting
    # where another preset's wrap output is mistaken for the real core.
    core_file = (
        resolver.resolve_core(cmd_name, "command")
        or resolver.resolve_extension_command_via_manifest(cmd_name)
        or resolver.resolve_core(short_name, "command")
    )
    if core_file is None:
        return body, {}

    core_frontmatter, core_body = registrar.parse_frontmatter(core_file.read_text(encoding="utf-8"))
    return body.replace("{CORE_TEMPLATE}", core_body), core_frontmatter


@dataclass
class PresetCatalogEntry:
    """Represents a single entry in the preset catalog stack."""
    url: str
    name: str
    priority: int
    install_allowed: bool
    description: str = ""


class PresetError(Exception):
    """Base exception for preset-related errors."""
    pass


class PresetValidationError(PresetError):
    """Raised when preset manifest validation fails."""
    pass


class PresetCompatibilityError(PresetError):
    """Raised when preset is incompatible with current environment."""
    pass


VALID_PRESET_TEMPLATE_TYPES = {"template", "command", "script"}
VALID_PRESET_STRATEGIES = {"replace", "prepend", "append", "wrap"}
# Scripts only support replace and wrap (prepend/append don't make semantic sense for executable code)
VALID_SCRIPT_STRATEGIES = {"replace", "wrap"}


class PresetManifest:
    """Represents and validates a preset manifest (preset.yml)."""

    SCHEMA_VERSION = "1.0"
    REQUIRED_FIELDS = ["schema_version", "preset", "requires", "provides"]

    def __init__(self, manifest_path: Path):
        """Load and validate preset manifest.

        Args:
            manifest_path: Path to preset.yml file

        Raises:
            PresetValidationError: If manifest is invalid
        """
        self.path = manifest_path
        self.data = self._load_yaml(manifest_path)
        self._validate()

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML file safely."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PresetValidationError(f"Invalid YAML in {path}: {e}")
        except FileNotFoundError:
            raise PresetValidationError(f"Manifest not found: {path}")
        except UnicodeDecodeError as e:
            raise PresetValidationError(
                f"Manifest is not valid UTF-8: {path} ({e.reason} at byte {e.start})"
            )
        except OSError as e:
            raise PresetValidationError(f"Could not read manifest {path}: {e}")
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise PresetValidationError(
                f"Manifest must be a YAML mapping, got {type(data).__name__}: {path}"
            )
        return data

    def _validate(self):
        """Validate manifest structure and required fields."""
        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise PresetValidationError(f"Missing required field: {field}")

        # Validate schema version
        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise PresetValidationError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        # Validate preset metadata
        pack = self.data["preset"]
        for field in ["id", "name", "version", "description"]:
            if field not in pack:
                raise PresetValidationError(f"Missing preset.{field}")

        # Validate pack ID format
        if not re.match(r'^[a-z0-9-]+$', pack["id"]):
            raise PresetValidationError(
                f"Invalid preset ID '{pack['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(pack["version"])
        except pkg_version.InvalidVersion:
            raise PresetValidationError(f"Invalid version: {pack['version']}")

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise PresetValidationError("Missing requires.speckit_version")

        # Validate provides section
        provides = self.data["provides"]
        if "templates" not in provides or not provides["templates"]:
            raise PresetValidationError(
                "Preset must provide at least one template"
            )

        # Validate templates
        for tmpl in provides["templates"]:
            if "type" not in tmpl or "name" not in tmpl or "file" not in tmpl:
                raise PresetValidationError(
                    "Template missing 'type', 'name', or 'file'"
                )

            if tmpl["type"] not in VALID_PRESET_TEMPLATE_TYPES:
                raise PresetValidationError(
                    f"Invalid template type '{tmpl['type']}': "
                    f"must be one of {sorted(VALID_PRESET_TEMPLATE_TYPES)}"
                )

            # Validate file path safety: must be relative, no parent traversal
            file_path = tmpl["file"]
            normalized = os.path.normpath(file_path)
            if os.path.isabs(normalized) or normalized.startswith(".."):
                raise PresetValidationError(
                    f"Invalid template file path '{file_path}': "
                    "must be a relative path within the preset directory"
                )

            # Validate strategy field (optional, defaults to "replace")
            strategy = tmpl.get("strategy", "replace")
            if not isinstance(strategy, str):
                raise PresetValidationError(
                    f"Invalid strategy value: must be a string, "
                    f"got {type(strategy).__name__}"
                )
            strategy = strategy.lower()
            # Persist normalized value so downstream code sees lowercase
            if "strategy" in tmpl:
                tmpl["strategy"] = strategy
            if strategy not in VALID_PRESET_STRATEGIES:
                raise PresetValidationError(
                    f"Invalid strategy '{strategy}': "
                    f"must be one of {sorted(VALID_PRESET_STRATEGIES)}"
                )
            if tmpl["type"] == "script" and strategy not in VALID_SCRIPT_STRATEGIES:
                raise PresetValidationError(
                    f"Invalid strategy '{strategy}' for script: "
                    f"scripts only support {sorted(VALID_SCRIPT_STRATEGIES)}"
                )

            # Validate template name format
            if tmpl["type"] == "command":
                # Commands use dot notation (e.g. speckit.specify)
                if not re.match(r'^[a-z0-9.-]+$', tmpl["name"]):
                    raise PresetValidationError(
                        f"Invalid command name '{tmpl['name']}': "
                        "must be lowercase alphanumeric with hyphens and dots only"
                    )
            else:
                if not re.match(r'^[a-z0-9-]+$', tmpl["name"]):
                    raise PresetValidationError(
                        f"Invalid template name '{tmpl['name']}': "
                        "must be lowercase alphanumeric with hyphens only"
                    )

    @property
    def id(self) -> str:
        """Get preset ID."""
        return self.data["preset"]["id"]

    @property
    def name(self) -> str:
        """Get preset name."""
        return self.data["preset"]["name"]

    @property
    def version(self) -> str:
        """Get preset version."""
        return self.data["preset"]["version"]

    @property
    def description(self) -> str:
        """Get preset description."""
        return self.data["preset"]["description"]

    @property
    def author(self) -> str:
        """Get preset author."""
        return self.data["preset"].get("author", "")

    @property
    def requires_speckit_version(self) -> str:
        """Get required spec-kit version range."""
        return self.data["requires"]["speckit_version"]

    @property
    def templates(self) -> List[Dict[str, Any]]:
        """Get list of provided templates."""
        return self.data["provides"]["templates"]

    @property
    def tags(self) -> List[str]:
        """Get preset tags."""
        return self.data.get("tags", [])

    def get_hash(self) -> str:
        """Calculate SHA256 hash of manifest file."""
        with open(self.path, 'rb') as f:
            return f"sha256:{hashlib.sha256(f.read()).hexdigest()}"


class PresetRegistry:
    """Manages the registry of installed presets."""

    REGISTRY_FILE = ".registry"
    SCHEMA_VERSION = "1.0"

    def __init__(self, packs_dir: Path):
        """Initialize registry.

        Args:
            packs_dir: Path to .specify/presets/ directory
        """
        self.packs_dir = packs_dir
        self.registry_path = packs_dir / self.REGISTRY_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return {
                "schema_version": self.SCHEMA_VERSION,
                "presets": {}
            }

        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            # Validate loaded data is a dict (handles corrupted registry files)
            if not isinstance(data, dict):
                return {
                    "schema_version": self.SCHEMA_VERSION,
                    "presets": {}
                }
            # Normalize presets field (handles corrupted presets value)
            if not isinstance(data.get("presets"), dict):
                data["presets"] = {}
            return data
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "schema_version": self.SCHEMA_VERSION,
                "presets": {}
            }

    def _save(self):
        """Save registry to disk."""
        self.packs_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add(self, pack_id: str, metadata: dict):
        """Add preset to registry.

        Args:
            pack_id: Preset ID
            metadata: Pack metadata (version, source, etc.)
        """
        self.data["presets"][pack_id] = {
            **copy.deepcopy(metadata),
            "installed_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()

    def remove(self, pack_id: str):
        """Remove preset from registry.

        Args:
            pack_id: Preset ID
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict):
            return
        if pack_id in packs:
            del packs[pack_id]
            self._save()

    def update(self, pack_id: str, updates: dict):
        """Update preset metadata in registry.

        Merges the provided updates with the existing entry, preserving any
        fields not specified. The installed_at timestamp is always preserved
        from the original entry.

        Args:
            pack_id: Preset ID
            updates: Partial metadata to merge into existing metadata

        Raises:
            KeyError: If preset is not installed
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict) or pack_id not in packs:
            raise KeyError(f"Preset '{pack_id}' not found in registry")
        existing = packs[pack_id]
        # Handle corrupted registry entries (e.g., string/list instead of dict)
        if not isinstance(existing, dict):
            existing = {}
        # Merge: existing fields preserved, new fields override (deep copy to prevent caller mutation)
        merged = {**existing, **copy.deepcopy(updates)}
        # Always preserve original installed_at based on key existence, not truthiness,
        # to handle cases where the field exists but may be falsy (legacy/corruption)
        if "installed_at" in existing:
            merged["installed_at"] = existing["installed_at"]
        else:
            # If not present in existing, explicitly remove from merged if caller provided it
            merged.pop("installed_at", None)
        packs[pack_id] = merged
        self._save()

    def restore(self, pack_id: str, metadata: dict):
        """Restore preset metadata to registry without modifying timestamps.

        Use this method for rollback scenarios where you have a complete backup
        of the registry entry (including installed_at) and want to restore it
        exactly as it was.

        Args:
            pack_id: Preset ID
            metadata: Complete preset metadata including installed_at

        Raises:
            ValueError: If metadata is None or not a dict
        """
        if metadata is None or not isinstance(metadata, dict):
            raise ValueError(f"Cannot restore '{pack_id}': metadata must be a dict")
        # Ensure presets dict exists (handle corrupted registry)
        if not isinstance(self.data.get("presets"), dict):
            self.data["presets"] = {}
        self.data["presets"][pack_id] = copy.deepcopy(metadata)
        self._save()

    def get(self, pack_id: str) -> Optional[dict]:
        """Get preset metadata from registry.

        Returns a deep copy to prevent callers from accidentally mutating
        nested internal registry state without going through the write path.

        Args:
            pack_id: Preset ID

        Returns:
            Deep copy of preset metadata, or None if not found or corrupted
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict):
            return None
        entry = packs.get(pack_id)
        # Return None for missing or corrupted (non-dict) entries
        if entry is None or not isinstance(entry, dict):
            return None
        return copy.deepcopy(entry)

    def list(self) -> Dict[str, dict]:
        """Get all installed presets with valid metadata.

        Returns a deep copy of presets with dict metadata only.
        Corrupted entries (non-dict values) are filtered out.

        Returns:
            Dictionary of pack_id -> metadata (deep copies), empty dict if corrupted
        """
        packs = self.data.get("presets", {}) or {}
        if not isinstance(packs, dict):
            return {}
        # Filter to only valid dict entries to match type contract
        return {
            pack_id: copy.deepcopy(meta)
            for pack_id, meta in packs.items()
            if isinstance(meta, dict)
        }

    def keys(self) -> set:
        """Get all preset IDs including corrupted entries.

        Lightweight method that returns IDs without deep-copying metadata.
        Use this when you only need to check which presets are tracked.

        Returns:
            Set of preset IDs (includes corrupted entries)
        """
        packs = self.data.get("presets", {}) or {}
        if not isinstance(packs, dict):
            return set()
        return set(packs.keys())

    def list_by_priority(self, include_disabled: bool = False) -> List[tuple]:
        """Get all installed presets sorted by priority.

        Lower priority number = higher precedence (checked first).
        Presets with equal priority are sorted alphabetically by ID
        for deterministic ordering.

        Args:
            include_disabled: If True, include disabled presets. Default False.

        Returns:
            List of (pack_id, metadata_copy) tuples sorted by priority.
            Metadata is deep-copied to prevent accidental mutation.
        """
        packs = self.data.get("presets", {}) or {}
        if not isinstance(packs, dict):
            packs = {}
        sortable_packs = []
        for pack_id, meta in packs.items():
            if not isinstance(meta, dict):
                continue
            # Skip disabled presets unless explicitly requested
            if not include_disabled and not meta.get("enabled", True):
                continue
            metadata_copy = copy.deepcopy(meta)
            metadata_copy["priority"] = normalize_priority(metadata_copy.get("priority", 10))
            sortable_packs.append((pack_id, metadata_copy))
        return sorted(
            sortable_packs,
            key=lambda item: (item[1]["priority"], item[0]),
        )

    def is_installed(self, pack_id: str) -> bool:
        """Check if preset is installed.

        Args:
            pack_id: Preset ID

        Returns:
            True if pack is installed, False if not or registry corrupted
        """
        packs = self.data.get("presets")
        if not isinstance(packs, dict):
            return False
        return pack_id in packs


class PresetManager:
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

    def _register_commands(
        self,
        manifest: PresetManifest,
        preset_dir: Path
    ) -> Dict[str, List[str]]:
        """Register preset command overrides with all detected AI agents.

        Scans the preset's templates for type "command", reads each command
        file, and writes it to every detected agent directory using the
        CommandRegistrar from the agents module.

        When a command uses a composition strategy (prepend, append, wrap),
        the content is composed with the lower-priority command before
        registration.

        Args:
            manifest: Preset manifest
            preset_dir: Installed preset directory

        Returns:
            Dictionary mapping agent names to lists of registered command names
        """
        command_templates = [
            t for t in manifest.templates if t.get("type") == "command"
        ]
        if not command_templates:
            return {}

        # Filter out extension command overrides if the extension isn't installed.
        # Command names follow the pattern: speckit.<ext-id>.<cmd-name>
        # Core commands (e.g. speckit.specify) have only one dot — always register.
        extensions_dir = self.project_root / ".specify" / "extensions"
        filtered = []
        for cmd in command_templates:
            parts = cmd["name"].split(".")
            if len(parts) >= 3 and parts[0] == "speckit":
                ext_id = parts[1]
                if not (extensions_dir / ext_id).is_dir():
                    continue
            filtered.append(cmd)

        if not filtered:
            return {}

        # Handle composition strategies: resolve composed content for non-replace commands
        resolver = PresetResolver(self.project_root)
        composed_dir = None
        commands_to_register = []
        for cmd in filtered:
            strategy = cmd.get("strategy", "replace")
            if strategy != "replace":
                # Only pre-compose if this preset is the top composing layer.
                # If a higher-priority replace already wins, skip composition
                # here — reconciliation will write the correct content.
                layers = resolver.collect_all_layers(cmd["name"], "command")
                top_layer_is_ours = (
                    layers and layers[0]["path"].is_relative_to(preset_dir)
                )
                if top_layer_is_ours:
                    composed = resolver.resolve_content(cmd["name"], "command")
                    if composed is not None:
                        if composed_dir is None:
                            composed_dir = preset_dir / ".composed"
                            composed_dir.mkdir(parents=True, exist_ok=True)
                        composed_file = composed_dir / f"{cmd['name']}.md"
                        composed_file.write_text(composed, encoding="utf-8")
                        commands_to_register.append({
                            **cmd,
                            "file": f".composed/{cmd['name']}.md",
                        })
                    else:
                        raise PresetValidationError(
                            f"Command '{cmd['name']}' uses '{strategy}' strategy "
                            f"but no base command layer exists to compose onto. "
                            f"Ensure a lower-priority preset, extension, or core "
                            f"command provides this command before using "
                            f"composition strategies."
                        )
                else:
                    # Not the top layer — register raw file; reconciliation
                    # will overwrite with the correct composed/winning content.
                    # Note: CommandRegistrar may process frontmatter strategy: wrap
                    # from the raw file (legacy compat), but reconciliation runs
                    # immediately after install and corrects the final output.
                    commands_to_register.append(cmd)
            else:
                commands_to_register.append(cmd)

        try:
            from ..agents import CommandRegistrar
        except ImportError:
            return {}

        registrar = CommandRegistrar()
        return registrar.register_commands_for_all_agents(
            commands_to_register, manifest.id, preset_dir, self.project_root
        )

    def _unregister_commands(self, registered_commands: Dict[str, List[str]]) -> None:
        """Remove previously registered command files from agent directories.

        Args:
            registered_commands: Dict mapping agent names to command name lists
        """
        try:
            from ..agents import CommandRegistrar
        except ImportError:
            return

        registrar = CommandRegistrar()
        registrar.unregister_commands(registered_commands, self.project_root)

    def _reconcile_composed_commands(self, command_names: List[str]) -> None:
        """Re-resolve and re-register composed commands from the full stack.

        After install or remove, recompute the effective content for each
        command name that participates in composition, and write the winning
        content to the agent directories. This ensures command files always
        reflect the current priority stack rather than depending on
        install/remove order.

        Args:
            command_names: List of command names to reconcile
        """
        if not command_names:
            return

        try:
            from ..agents import CommandRegistrar
        except ImportError:
            return

        resolver = PresetResolver(self.project_root)
        registrar = CommandRegistrar()

        # Cache registry and manifests outside the loop to avoid
        # repeated filesystem reads for each command name.
        presets_by_priority = list(self.registry.list_by_priority())

        for cmd_name in command_names:
            layers = resolver.collect_all_layers(cmd_name, "command")
            if not layers:
                continue

            # If the top layer is replace, it wins entirely — lower layers
            # are irrelevant regardless of their strategies.
            top_is_replace = layers[0]["strategy"] == "replace"
            has_composition = not top_is_replace and any(
                layer["strategy"] != "replace" for layer in layers
            )
            if not has_composition:
                # Pure replace — the top layer wins.
                top_layer = layers[0]
                top_path = top_layer["path"]
                # Try to find which preset owns this layer
                registered = False
                for pack_id, _meta in presets_by_priority:
                    pack_dir = self.presets_dir / pack_id
                    if top_path.is_relative_to(pack_dir):
                        manifest = resolver._get_manifest(pack_dir)
                        if manifest:
                            for tmpl in manifest.templates:
                                if tmpl.get("name") == cmd_name and tmpl.get("type") == "command":
                                    self._register_for_non_skill_agents(
                                        registrar, [tmpl], manifest.id, pack_dir
                                    )
                                    registered = True
                                    break
                        break
                if not registered:
                    # Top layer is a non-preset source (extension, core, or
                    # project override). Register directly from the layer path.
                    source = layers[0]["source"]
                    if source.startswith("extension:"):
                        # Use extension's own registration to preserve context formatting
                        ext_id = source.split(":", 1)[1].split(" ", 1)[0]
                        ext_dir = self.project_root / ".specify" / "extensions" / ext_id
                        ext_manifest_path = ext_dir / "extension.yml"
                        if ext_manifest_path.exists():
                            try:
                                from ..extensions import ExtensionManifest
                                ext_manifest = ExtensionManifest(ext_manifest_path)
                                # Filter to only the command being reconciled
                                matching_cmds = [
                                    c for c in ext_manifest.commands
                                    if c.get("name") == cmd_name
                                ]
                                if matching_cmds:
                                    registrar.register_commands_for_non_skill_agents(
                                        matching_cmds, ext_id, ext_dir,
                                        self.project_root,
                                        context_note=f"\n<!-- Extension: {ext_id} -->\n<!-- Config: .specify/extensions/{ext_id}/ -->\n",
                                        extension_id=ext_id,
                                    )
                                    registered = True
                            except Exception:
                                # Extension registration failed; fall back to
                                # generic path-based registration below.
                                pass
                    if not registered:
                        source_id = source.split(":", 1)[1].split(" ", 1)[0] if source.startswith("extension:") else source
                        self._register_command_from_path(
                            registrar, cmd_name, top_path,
                            source_id=source_id,
                        )
            else:
                # Composed command — resolve from full stack
                composed = resolver.resolve_content(cmd_name, "command")
                if composed is None:
                    # Composition no longer possible (e.g. base layer removed).
                    # Unregister any stale command file from non-skill agents.
                    import warnings
                    warnings.warn(
                        f"Cannot compose command '{cmd_name}': no base layer. "
                        f"Stale command files may remain.",
                        stacklevel=2,
                    )
                    registrar._ensure_configs()
                    # Include aliases from the top layer's manifest
                    cmd_names_to_unregister = [cmd_name]
                    for _pid, _meta in presets_by_priority:
                        _pd = self.presets_dir / _pid
                        _m = resolver._get_manifest(_pd)
                        if _m:
                            for _t in _m.templates:
                                if _t.get("name") == cmd_name and _t.get("type") == "command":
                                    for alias in _t.get("aliases", []):
                                        if isinstance(alias, str):
                                            cmd_names_to_unregister.append(alias)
                                    break
                    registrar.unregister_commands(
                        {agent: cmd_names_to_unregister for agent in registrar.AGENT_CONFIGS
                         if registrar.AGENT_CONFIGS[agent].get("extension") != "/SKILL.md"},
                        self.project_root,
                    )
                    continue

                # Write to the highest-priority preset's .composed dir
                registered = False
                for pack_id, _meta in presets_by_priority:
                    pack_dir = self.presets_dir / pack_id
                    manifest = resolver._get_manifest(pack_dir)
                    if not manifest:
                        continue
                    for tmpl in manifest.templates:
                        if tmpl.get("name") == cmd_name and tmpl.get("type") == "command":
                            composed_dir = pack_dir / ".composed"
                            composed_dir.mkdir(parents=True, exist_ok=True)
                            composed_file = composed_dir / f"{cmd_name}.md"
                            composed_file.write_text(composed, encoding="utf-8")
                            self._register_for_non_skill_agents(
                                registrar,
                                [{**tmpl, "file": f".composed/{cmd_name}.md"}],
                                manifest.id, pack_dir,
                            )
                            registered = True
                            break
                    else:
                        continue
                    break
                if not registered:
                    # No preset owns this composed command — write to a
                    # shared .composed dir and register from the top layer.
                    shared_composed = self.presets_dir / ".composed"
                    shared_composed.mkdir(parents=True, exist_ok=True)
                    composed_file = shared_composed / f"{cmd_name}.md"
                    composed_file.write_text(composed, encoding="utf-8")
                    source = layers[0]["source"]
                    if source.startswith("extension:"):
                        source_id = source.split(":", 1)[1].split(" ", 1)[0]
                    else:
                        source_id = source
                    self._register_command_from_path(
                        registrar, cmd_name, composed_file,
                        source_id=source_id,
                    )

    def _register_command_from_path(
        self,
        registrar: Any,
        cmd_name: str,
        cmd_path: Path,
        source_id: str = "reconciled",
    ) -> None:
        """Register a single command from a file path (non-preset source).

        Used by reconciliation when the winning layer is an extension,
        core template, or project override rather than a preset.

        Args:
            registrar: CommandRegistrar instance
            cmd_name: Command name
            cmd_path: Path to the command file
            source_id: Source attribution for rendered output
        """
        if not cmd_path.exists():
            return
        cmd_tmpl: Dict[str, Any] = {
            "name": cmd_name,
            "type": "command",
            "file": cmd_path.name,
        }
        # Load aliases from extension manifest when the winning layer is an extension
        if source_id and not source_id.startswith("preset:"):
            try:
                from ..extensions import ExtensionManifest
                for ext_dir in (self.project_root / ".specify" / "extensions").iterdir():
                    if not ext_dir.is_dir():
                        continue
                    if cmd_path.is_relative_to(ext_dir):
                        manifest_path = ext_dir / "extension.yml"
                        if manifest_path.exists():
                            ext_manifest = ExtensionManifest(manifest_path)
                            for cmd in ext_manifest.commands:
                                if cmd.get("name") == cmd_name:
                                    aliases = cmd.get("aliases", [])
                                    if isinstance(aliases, list) and aliases:
                                        cmd_tmpl["aliases"] = aliases
                                    break
                        break
            except Exception:
                pass  # best-effort alias loading
        self._register_for_non_skill_agents(
            registrar, [cmd_tmpl], source_id, cmd_path.parent
        )

    def _register_for_non_skill_agents(
        self,
        registrar: Any,
        commands: List[Dict[str, Any]],
        source_id: str,
        source_dir: Path,
    ) -> None:
        """Register commands for non-skill agents during reconciliation.

        Skill-based agents (``/SKILL.md`` layout) are handled separately:
        - On removal: ``_unregister_skills()`` restores from core/extension,
          then ``_reconcile_skills()`` re-runs ``_register_skills()`` for the
          next winning preset so SKILL.md files get proper frontmatter and
          descriptions.
        - On install: ``_register_skills()`` writes formatted SKILL.md, then
          ``_reconcile_skills()`` ensures the actual priority winner is used.

        Writing raw command content to skill agents would produce invalid
        SKILL.md files (missing skill frontmatter, descriptions, etc.).
        """
        registrar.register_commands_for_non_skill_agents(
            commands, source_id, source_dir, self.project_root
        )

    class _FilteredManifest:
        """Wrapper that exposes only selected command templates from a manifest.

        Used by _reconcile_skills to avoid overwriting skills for commands
        that aren't being reconciled.
        """

        def __init__(self, manifest: "PresetManifest", cmd_names: set):
            self._manifest = manifest
            self._cmd_names = cmd_names

        def __getattr__(self, name: str):
            return getattr(self._manifest, name)

        @property
        def templates(self) -> List[Dict[str, Any]]:
            return [
                t for t in self._manifest.templates
                if t.get("name") in self._cmd_names
            ]

    def _reconcile_skills(self, command_names: List[str]) -> None:
        """Re-register skills for commands whose winning layer changed.

        After a preset is removed, finds the next preset in the priority
        stack that provides each command and re-runs skill registration
        for that preset so SKILL.md files reflect the current winner.

        Args:
            command_names: List of command names to reconcile skills for
        """
        if not command_names:
            return

        resolver = PresetResolver(self.project_root)
        skills_dir = self._get_skills_dir()

        # Cache registry once to avoid repeated filesystem reads
        presets_by_priority = list(self.registry.list_by_priority())

        # Group command names by winning preset to batch _register_skills calls
        # while only registering skills for the specific commands being reconciled.
        preset_cmds: Dict[str, List[str]] = {}
        non_preset_skills: List[tuple] = []

        for cmd_name in command_names:
            layers = resolver.collect_all_layers(cmd_name, "command")
            if not layers:
                continue

            # Re-create the skill directory only if it was previously managed
            # (i.e., listed in some preset's registered_skills). This avoids
            # creating new skill dirs that _register_skills would normally skip.
            if skills_dir:
                skill_name, _ = self._skill_names_for_command(cmd_name)
                skill_subdir = skills_dir / skill_name
                if not skill_subdir.exists():
                    # Check if any preset previously registered this skill
                    was_managed = False
                    for _pid, meta in presets_by_priority:
                        if not isinstance(meta, dict):
                            continue
                        if skill_name in meta.get("registered_skills", []):
                            was_managed = True
                            break
                    if was_managed:
                        skill_subdir.mkdir(parents=True, exist_ok=True)

            top_path = layers[0]["path"]
            # Find the preset that owns the winning layer
            found_preset = False
            for pack_id, _meta in presets_by_priority:
                pack_dir = self.presets_dir / pack_id
                if top_path.is_relative_to(pack_dir):
                    preset_cmds.setdefault(pack_id, []).append(cmd_name)
                    found_preset = True
                    break
            if not found_preset:
                # Winner is a non-preset source (core/extension/override).
                # Track the winning layer path for skill restoration.
                skill_name, _ = self._skill_names_for_command(cmd_name)
                non_preset_skills.append((skill_name, cmd_name, layers[0]))

        # Restore skills for commands whose winner is non-preset.
        if non_preset_skills and skills_dir:
            # Separate override-backed skills from core/extension-backed ones.
            # _unregister_skills can rmtree the skill dir, so overrides must
            # be handled directly (create dir + write) without that call.
            core_ext_skills = []
            override_skills = []
            for item in non_preset_skills:
                if item[2]["source"] == "project override":
                    override_skills.append(item)
                else:
                    core_ext_skills.append(item)

            if core_ext_skills:
                self._unregister_skills(
                    [s[0] for s in core_ext_skills], self.presets_dir
                )

            for skill_name, cmd_name, top_layer in override_skills:
                skill_subdir = skills_dir / skill_name
                skill_subdir.mkdir(parents=True, exist_ok=True)
                skill_file = skill_subdir / "SKILL.md"
                try:
                    from ..agents import CommandRegistrar
                    from .. import SKILL_DESCRIPTIONS, load_init_options
                    registrar = CommandRegistrar()
                    content = top_layer["path"].read_text(encoding="utf-8")
                    fm, body = registrar.parse_frontmatter(content)
                    short_name = cmd_name
                    if short_name.startswith("speckit."):
                        short_name = short_name[len("speckit."):]
                    desc = fm.get("description", "") or SKILL_DESCRIPTIONS.get(
                        short_name.replace(".", "-"),
                        f"Command: {short_name}",
                    )
                    init_opts = load_init_options(self.project_root)
                    selected_ai = init_opts.get("ai") if isinstance(init_opts, dict) else ""
                    if isinstance(selected_ai, str):
                        body = registrar.resolve_skill_placeholders(
                            selected_ai, fm, body, self.project_root
                        )
                        body = self._resolve_skill_command_refs(
                            body, registrar, selected_ai
                        )
                    from ..integrations import get_integration
                    integration = get_integration(selected_ai) if isinstance(selected_ai, str) else None
                    fm_data = registrar.build_skill_frontmatter(
                        selected_ai if isinstance(selected_ai, str) else "",
                        skill_name, desc,
                        f"override:{cmd_name}",
                    )
                    registrar.apply_argument_hint(fm, fm_data, integration)
                    fm_text = dump_frontmatter(fm_data)
                    skill_title = self._skill_title_from_command(cmd_name)
                    skill_content = (
                        f"---\n{fm_text}\n---\n\n"
                        f"# Speckit {skill_title} Skill\n\n{body}\n"
                    )
                    # Apply integration post-processing (e.g. Claude flags)
                    if integration is not None and hasattr(integration, "post_process_skill_content"):
                        skill_content = integration.post_process_skill_content(skill_content)
                    skill_file.write_text(skill_content, encoding="utf-8")
                except Exception:
                    pass  # best-effort override skill restoration

        # Register skills only for the specific commands being reconciled,
        # not all commands in each winning preset's manifest.
        for pack_id, cmds in preset_cmds.items():
            pack_dir = self.presets_dir / pack_id
            manifest_path = pack_dir / "preset.yml"
            if not manifest_path.exists():
                continue
            try:
                manifest = PresetManifest(manifest_path)
            except PresetValidationError:
                continue
            # Filter manifest to only the commands being reconciled
            cmds_set = set(cmds)
            filtered_manifest = self._FilteredManifest(manifest, cmds_set)
            self._register_skills(filtered_manifest, pack_dir)

    def _get_skills_dir(self) -> Optional[Path]:
        """Return the active skills directory for preset skill overrides.

        Delegates to :func:`resolve_active_skills_dir` which reads
        init-options, applies the Kimi native-skills fallback, and
        safely creates the directory when ``ai_skills`` is enabled.

        Returns ``None`` (instead of raising) when the directory cannot
        be created due to symlink, containment, or permission issues so
        that callers can fall back gracefully.
        """
        from .. import resolve_active_skills_dir, _print_cli_warning
        try:
            return resolve_active_skills_dir(self.project_root)
        except (ValueError, OSError) as exc:
            _print_cli_warning(
                "resolve", "skills directory", None, exc,
                continuing="Continuing without skill registration.",
            )
            return None

    @staticmethod
    def _skill_names_for_command(cmd_name: str) -> tuple[str, str]:
        """Return the modern and legacy skill directory names for a command."""
        raw_short_name = cmd_name
        if raw_short_name.startswith("speckit."):
            raw_short_name = raw_short_name[len("speckit."):]

        modern_skill_name = f"speckit-{raw_short_name.replace('.', '-')}"
        legacy_skill_name = f"speckit.{raw_short_name}"
        return modern_skill_name, legacy_skill_name

    @staticmethod
    def _skill_title_from_command(cmd_name: str) -> str:
        """Return a human-friendly title for a skill command name."""
        title_name = cmd_name
        if title_name.startswith("speckit."):
            title_name = title_name[len("speckit."):]
        return title_name.replace(".", " ").replace("-", " ").title()

    @staticmethod
    def _resolve_skill_command_refs(
        body: str, registrar: "CommandRegistrar", selected_ai: str
    ) -> str:
        """Render ``__SPECKIT_COMMAND_*__`` tokens in a skill body as invocations.

        Looks up the agent's invoke separator and rewrites each
        ``__SPECKIT_COMMAND_<NAME>__`` placeholder into the matching
        slash-command invocation — ``/speckit-<cmd>`` for a ``-`` separator,
        ``/speckit.<cmd>`` for ``.`` — the same rendering the command layer
        applies via ``CommandRegistrar.register_commands()``.
        """
        separator = registrar.AGENT_CONFIGS.get(selected_ai, {}).get(
            "invoke_separator", "."
        )
        return IntegrationBase.resolve_command_refs(body, separator)

    def _build_extension_skill_restore_index(self) -> Dict[str, Dict[str, Any]]:
        """Index extension-backed skill restore data by skill directory name."""
        from ..extensions import ExtensionManifest, ValidationError

        resolver = PresetResolver(self.project_root)
        extensions_dir = self.project_root / ".specify" / "extensions"
        restore_index: Dict[str, Dict[str, Any]] = {}

        for _priority, ext_id, _metadata in resolver._get_all_extensions_by_priority():
            ext_dir = extensions_dir / ext_id
            manifest_path = ext_dir / "extension.yml"
            if not manifest_path.is_file():
                continue

            try:
                manifest = ExtensionManifest(manifest_path)
            except (ValidationError, TypeError, AttributeError):
                continue

            ext_root = ext_dir.resolve()
            for cmd_info in manifest.commands:
                cmd_name = cmd_info.get("name")
                cmd_file_rel = cmd_info.get("file")
                if not isinstance(cmd_name, str) or not isinstance(cmd_file_rel, str):
                    continue

                cmd_path = Path(cmd_file_rel)
                if cmd_path.is_absolute():
                    continue

                try:
                    source_file = (ext_root / cmd_path).resolve()
                    source_file.relative_to(ext_root)
                except (OSError, ValueError):
                    continue

                if not source_file.is_file():
                    continue

                restore_info = {
                    "command_name": cmd_name,
                    "source_file": source_file,
                    "source": f"extension:{manifest.id}",
                    "extension_id": manifest.id,
                    "extension_dir": ext_root,
                }
                modern_skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
                restore_index.setdefault(modern_skill_name, restore_info)
                if legacy_skill_name != modern_skill_name:
                    restore_index.setdefault(legacy_skill_name, restore_info)

        return restore_index

    def _register_skills(
        self,
        manifest: "PresetManifest",
        preset_dir: Path,
    ) -> List[str]:
        """Generate SKILL.md files for preset command overrides.

        For every command template in the preset, checks whether a
        corresponding skill already exists in any detected skills
        directory.  If so, the skill is overwritten with content derived
        from the preset's command file.  This ensures that presets that
        override commands also propagate to the agentskills.io skill
        layer when skills mode was used during project initialisation.

        Args:
            manifest: Preset manifest.
            preset_dir: Installed preset directory.

        Returns:
            List of skill names that were written (for registry storage).
        """
        command_templates = [
            t for t in manifest.templates if t.get("type") == "command"
        ]
        if not command_templates:
            return []

        # Filter out extension command overrides if the extension isn't installed,
        # matching the same logic used by _register_commands().
        extensions_dir = self.project_root / ".specify" / "extensions"
        filtered = []
        for cmd in command_templates:
            parts = cmd["name"].split(".")
            if len(parts) >= 3 and parts[0] == "speckit":
                ext_id = parts[1]
                if not (extensions_dir / ext_id).is_dir():
                    continue
            filtered.append(cmd)

        if not filtered:
            return []

        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return []

        from .. import SKILL_DESCRIPTIONS, load_init_options
        from ..agents import CommandRegistrar
        from ..integrations import get_integration

        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = init_opts.get("ai")
        if not isinstance(selected_ai, str):
            return []
        ai_skills_enabled = is_ai_skills_enabled(init_opts)
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai)
        agent_config = registrar.AGENT_CONFIGS.get(selected_ai, {})
        # Native skill agents (e.g. codex/kimi/agy/trae) materialize brand-new
        # preset skills in _register_commands() because their detected agent
        # directory is already the skills directory. This flag is only for
        # command-backed agents that also mirror commands into skills.
        create_missing_skills = ai_skills_enabled and agent_config.get("extension") != "/SKILL.md"

        written: List[str] = []

        for cmd_tmpl in filtered:
            cmd_name = cmd_tmpl["name"]
            cmd_file_rel = cmd_tmpl["file"]
            source_file = preset_dir / cmd_file_rel
            if not source_file.exists():
                continue

            # Use composed content if available (written by _register_commands
            # for commands with non-replace strategies), otherwise the original.
            composed_file = preset_dir / ".composed" / f"{cmd_name}.md"
            if composed_file.exists():
                source_file = composed_file

            # Derive the short command name (e.g. "specify" from "speckit.specify")
            raw_short_name = cmd_name
            if raw_short_name.startswith("speckit."):
                raw_short_name = raw_short_name[len("speckit."):]
            short_name = raw_short_name.replace(".", "-")
            skill_name, legacy_skill_name = self._skill_names_for_command(cmd_name)
            skill_title = self._skill_title_from_command(cmd_name)

            # Only overwrite skills that already exist under skills_dir,
            # including Kimi native skills when ai_skills is false.
            # If both modern and legacy directories exist, update both.
            target_skill_names: List[str] = []
            if (skills_dir / skill_name).is_dir():
                target_skill_names.append(skill_name)
            if legacy_skill_name != skill_name and (skills_dir / legacy_skill_name).is_dir():
                target_skill_names.append(legacy_skill_name)
            if not target_skill_names and create_missing_skills:
                missing_skill_dir = skills_dir / skill_name
                if not missing_skill_dir.exists():
                    target_skill_names.append(skill_name)
            if not target_skill_names:
                continue

            # Parse the command file
            content = source_file.read_text(encoding="utf-8")
            frontmatter, body = registrar.parse_frontmatter(content)

            if frontmatter.get("strategy") == "wrap":
                body, core_frontmatter = _substitute_core_template(body, cmd_name, self.project_root, registrar)
                frontmatter = dict(frontmatter)
                for key in ("scripts", "agent_scripts"):
                    if key not in frontmatter and key in core_frontmatter:
                        frontmatter[key] = core_frontmatter[key]

            original_desc = frontmatter.get("description", "")
            enhanced_desc = original_desc or SKILL_DESCRIPTIONS.get(
                short_name,
                f"Spec-kit workflow command: {short_name}",
            )
            frontmatter = dict(frontmatter)
            frontmatter["description"] = enhanced_desc
            body = registrar.resolve_skill_placeholders(
                selected_ai, frontmatter, body, self.project_root
            )
            body = self._resolve_skill_command_refs(body, registrar, selected_ai)

            for target_skill_name in target_skill_names:
                skill_subdir = skills_dir / target_skill_name
                if skill_subdir.exists() and not skill_subdir.is_dir():
                    continue
                skill_subdir.mkdir(parents=True, exist_ok=True)
                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai,
                    target_skill_name,
                    enhanced_desc,
                    f"preset:{manifest.id}",
                )
                registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
                frontmatter_text = dump_frontmatter(frontmatter_data)
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# Speckit {skill_title} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )

                skill_file = skill_subdir / "SKILL.md"
                skill_file.write_text(skill_content, encoding="utf-8")
                written.append(target_skill_name)

        return written

    def _unregister_skills(self, skill_names: List[str], preset_dir: Path) -> None:
        """Restore original SKILL.md files after a preset is removed.

        For each skill that was overridden by the preset, attempts to
        regenerate the skill from the core command template.  If no core
        template exists, the skill directory is removed.

        Args:
            skill_names: List of skill names written by the preset.
            preset_dir: The preset's installed directory (may already be deleted).
        """
        if not skill_names:
            return

        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return

        from .. import SKILL_DESCRIPTIONS, load_init_options
        from ..agents import CommandRegistrar
        from ..integrations import get_integration

        # Locate core command templates from the project's installed templates
        core_templates_dir = self.project_root / ".specify" / "templates" / "commands"
        init_opts = load_init_options(self.project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}
        selected_ai = init_opts.get("ai")
        registrar = CommandRegistrar()
        integration = get_integration(selected_ai) if isinstance(selected_ai, str) else None
        extension_restore_index = self._build_extension_skill_restore_index()

        for skill_name in skill_names:
            # Derive command name from skill name (speckit-specify -> specify)
            short_name = skill_name
            if short_name.startswith("speckit-"):
                short_name = short_name[len("speckit-"):]
            elif short_name.startswith("speckit."):
                short_name = short_name[len("speckit."):]

            skill_subdir = skills_dir / skill_name
            skill_file = skill_subdir / "SKILL.md"
            if not skill_subdir.is_dir():
                continue
            if not skill_file.is_file():
                # Only manage directories that contain the expected skill entrypoint.
                continue

            # Try to find the core command template
            core_file = core_templates_dir / f"{short_name}.md" if core_templates_dir.exists() else None
            if core_file and not core_file.exists():
                core_file = None

            if core_file:
                # Restore from core template
                content = core_file.read_text(encoding="utf-8")
                frontmatter, body = registrar.parse_frontmatter(content)
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root
                    )
                    body = self._resolve_skill_command_refs(
                        body, registrar, selected_ai
                    )

                original_desc = frontmatter.get("description", "")
                enhanced_desc = original_desc or SKILL_DESCRIPTIONS.get(
                    short_name,
                    f"Spec-kit workflow command: {short_name}",
                )

                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai if isinstance(selected_ai, str) else "",
                    skill_name,
                    enhanced_desc,
                    f"templates/commands/{short_name}.md",
                )
                registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
                frontmatter_text = dump_frontmatter(frontmatter_data)
                skill_title = self._skill_title_from_command(short_name)
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# Speckit {skill_title} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )
                skill_file.write_text(skill_content, encoding="utf-8")
                continue

            extension_restore = extension_restore_index.get(skill_name)
            if extension_restore:
                content = extension_restore["source_file"].read_text(encoding="utf-8")
                frontmatter, body = registrar.parse_frontmatter(content)
                # Mirror the register-time rewrite (#2101): resolve
                # extension-relative subdir references (agents/,
                # knowledge-base/, etc.) to their installed location before
                # the generic placeholder resolution below, otherwise
                # restoring after a preset override removal would leave
                # bare, unresolvable paths in the skill body.
                body = registrar.rewrite_extension_paths(
                    body,
                    extension_restore["extension_id"],
                    extension_restore["extension_dir"],
                )
                if isinstance(selected_ai, str):
                    body = registrar.resolve_skill_placeholders(
                        selected_ai, frontmatter, body, self.project_root
                    )
                    body = self._resolve_skill_command_refs(
                        body, registrar, selected_ai
                    )

                command_name = extension_restore["command_name"]
                title_name = self._skill_title_from_command(command_name)

                frontmatter_data = registrar.build_skill_frontmatter(
                    selected_ai if isinstance(selected_ai, str) else "",
                    skill_name,
                    frontmatter.get("description", f"Extension command: {command_name}"),
                    extension_restore["source"],
                )
                registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
                frontmatter_text = dump_frontmatter(frontmatter_data)
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# {title_name} Skill\n\n"
                    f"{body}\n"
                )
                if integration is not None and hasattr(integration, "post_process_skill_content"):
                    skill_content = integration.post_process_skill_content(
                        skill_content
                    )
                skill_file.write_text(skill_content, encoding="utf-8")
            else:
                # No core or extension template — remove the skill entirely
                shutil.rmtree(skill_subdir)

    def install_from_directory(
        self,
        source_dir: Path,
        speckit_version: str,
        priority: int = 10,
    ) -> PresetManifest:
        """Install preset from a local directory.

        Args:
            source_dir: Path to preset directory
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)

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
            raise PresetError(
                f"Preset '{manifest.id}' is already installed. "
                f"Use 'specify preset remove {manifest.id}' first."
            )

        dest_dir = self.presets_dir / manifest.id
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir)

        # Pre-register the preset so that composition resolution can see it
        # in the priority stack when resolving composed command content.
        self.registry.add(manifest.id, {
            "version": manifest.version,
            "source": "local",
            "manifest_hash": manifest.get_hash(),
            "enabled": True,
            "priority": priority,
            "registered_commands": {},
            "registered_skills": [],
        })

        registered_commands: Dict[str, List[str]] = {}
        registered_skills: List[str] = []
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
            # Roll back all side effects. Note: if _register_commands or
            # _register_skills raised mid-way (e.g. I/O error after writing
            # some files), registered_commands/registered_skills may be empty
            # and some agent command files could be orphaned. Removing dest_dir
            # (which contains .composed/) and the registry entry ensures the
            # preset system is consistent even if orphaned files remain.
            if registered_commands:
                self._unregister_commands(registered_commands)
            if registered_skills:
                self._unregister_skills(registered_skills, dest_dir)
            try:
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
            except OSError:
                pass  # best-effort cleanup; don't mask the original error
            self.registry.remove(manifest.id)
            raise

        # Reconcile all affected commands from the full priority stack so that
        # install order doesn't determine the winning command file.
        # Apply the same extension-installed filter as _register_commands to
        # avoid reconciling extension commands when the extension isn't installed.
        extensions_dir = self.project_root / ".specify" / "extensions"
        cmd_names = []
        for t in manifest.templates:
            if t.get("type") != "command":
                continue
            name = t["name"]
            parts = name.split(".")
            if len(parts) >= 3 and parts[0] == "speckit":
                ext_id = parts[1]
                if not (extensions_dir / ext_id).is_dir():
                    continue
            cmd_names.append(name)
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

        # Seed/re-seed memory/constitution.md from a preset-provided
        # constitution-template. The constitution is the only template that is
        # materialized to a live file rather than resolved on demand, so a
        # preset that ships one (e.g. strategy: replace with a ratified
        # constitution) must be propagated here. Guard against clobbering an
        # already-authored constitution by only replacing a file whose recorded
        # hash (or exact legacy core-template content) proves it was generated.
        self._seed_constitution_from_preset(manifest, dest_dir)

        return manifest

    def _seed_constitution_from_preset(
        self, manifest: PresetManifest, preset_dir: Path
    ) -> None:
        """Seed memory/constitution.md from a preset constitution-template.

        Only runs when the preset declares a ``type: template`` entry named
        ``constitution-template`` or provides one at a convention path, and the
        live memory file is either missing or is an unchanged generated file.
        Authored constitutions are never overwritten.
        """
        provides_constitution = any(
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
        """Reconcile generated constitution content without failing a persisted change."""
        try:
            self._reconcile_constitution(create_if_missing=create_if_missing)
        except (OSError, UnicodeDecodeError, PresetValidationError, ValueError) as exc:
            import warnings

            warnings.warn(
                f"{failure_context}: {exc}.",
                stacklevel=2,
            )

    def _reconcile_constitution(self, *, create_if_missing: bool = False) -> None:
        """Materialize the winning constitution layer when the live file is generated."""
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

    def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str,
        priority: int = 10,
    ) -> PresetManifest:
        """Install preset from ZIP file.

        Args:
            zip_path: Path to preset ZIP file
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)

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

            with zipfile.ZipFile(zip_path, 'r') as zf:
                temp_path_resolved = temp_path.resolve()
                for member in zf.namelist():
                    member_path = (temp_path / member).resolve()
                    try:
                        member_path.relative_to(temp_path_resolved)
                    except ValueError:
                        raise PresetValidationError(
                            f"Unsafe path in ZIP archive: {member} "
                            "(potential path traversal)"
                        )
                zf.extractall(temp_path)

            pack_dir = temp_path
            manifest_path = pack_dir / "preset.yml"

            if not manifest_path.exists():
                subdirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    pack_dir = subdirs[0]
                    manifest_path = pack_dir / "preset.yml"

            if not manifest_path.exists():
                raise PresetValidationError(
                    "No preset.yml found in ZIP file"
                )

            return self.install_from_directory(pack_dir, speckit_version, priority)

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
        registered_commands = metadata.get("registered_commands", {}) if metadata else {}
        pack_dir = self.presets_dir / pack_id

        # Collect ALL command names before filtering for reconciliation,
        # so commands registered only for skill-based agents are also reconciled.
        # Also include aliases from the manifest as a safety net for registries
        # populated by older versions that may not track aliases.
        removed_cmd_names = set()
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
                        for alias in tmpl.get("aliases", []):
                            if isinstance(alias, str):
                                removed_cmd_names.add(alias)
            except PresetValidationError:
                # Invalid manifest — skip alias extraction; primary command
                # names from registered_commands are still unregistered.
                pass

        if registered_skills:
            self._unregister_skills(registered_skills, pack_dir)
            try:
                from ..agents import CommandRegistrar
            except ImportError:
                CommandRegistrar = None
            if CommandRegistrar is not None:
                registered_commands = {
                    agent_name: cmd_names
                    for agent_name, cmd_names in registered_commands.items()
                    if CommandRegistrar.AGENT_CONFIGS.get(agent_name, {}).get("extension") != "/SKILL.md"
                }

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
                self._reconcile_composed_commands(list(removed_cmd_names))
                self._reconcile_skills(list(removed_cmd_names))
            except Exception as exc:
                import warnings
                warnings.warn(
                    f"Post-removal reconciliation failed for {pack_id}: {exc}. "
                    f"Agent command files may be stale; reinstall affected presets "
                    f"or run 'specify preset add' to refresh.",
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


class PresetCatalog:
    """Manages preset catalog fetching, caching, and searching.

    Supports multi-catalog stacks with priority-based resolution,
    mirroring the extension catalog system.
    """

    DEFAULT_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/presets/catalog.json"
    COMMUNITY_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/presets/catalog.community.json"
    CACHE_DURATION = 3600  # 1 hour in seconds

    def __init__(self, project_root: Path):
        """Initialize preset catalog manager.

        Args:
            project_root: Root directory of the spec-kit project
        """
        self.project_root = project_root
        self.presets_dir = project_root / ".specify" / "presets"
        self.cache_dir = self.presets_dir / ".cache"
        self.cache_file = self.cache_dir / "catalog.json"
        self.cache_metadata_file = self.cache_dir / "catalog-metadata.json"

    def _validate_catalog_url(self, url: str) -> None:
        """Validate that a catalog URL uses HTTPS (localhost HTTP allowed).

        Args:
            url: URL to validate

        Raises:
            PresetValidationError: If URL is invalid or uses non-HTTPS scheme
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
        except ValueError:
            raise PresetValidationError(f"Catalog URL is malformed: {url}") from None
        is_localhost = hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise PresetValidationError(
                f"Catalog URL must use HTTPS (got {parsed.scheme}://). "
                "HTTP is only allowed for localhost."
            )
        # Check hostname, not netloc: netloc is truthy for host-less URLs like
        # "https://:8080" or "https://user@", so the host guarantee this error
        # promises would not actually hold. hostname is None in those cases (#3209).
        if not hostname:
            raise PresetValidationError(
                "Catalog URL must be a valid URL with a host."
            )

    def _make_request(self, url: str):
        """Build a urllib Request, adding auth headers when a provider matches.

        Delegates to :func:`specify_cli.authentication.http.build_request`.
        """
        from specify_cli.authentication.http import build_request
        return build_request(url)

    def _open_url(
        self,
        url: str,
        timeout: int = 10,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        """Open a URL with provider-based auth, trying each configured provider.

        Delegates to :func:`specify_cli.authentication.http.open_url`.
        """
        from specify_cli.authentication.http import open_url
        return open_url(url, timeout, extra_headers=extra_headers)

    def _resolve_github_release_asset_api_url(
        self,
        download_url: str,
        timeout: int = 60,
    ) -> Optional[str]:
        """Resolve a GitHub release asset URL to its REST API asset URL.

        Passes the ``github`` provider hosts from ``auth.json`` so GitHub
        Enterprise Server release assets resolve via ``/api/v3``.
        """
        from specify_cli._github_http import resolve_github_release_asset_api_url
        from specify_cli.authentication.http import github_provider_hosts

        return resolve_github_release_asset_api_url(
            download_url,
            self._open_url,
            timeout=timeout,
            github_hosts=github_provider_hosts(),
        )

    def _validate_catalog_payload(self, catalog_data: Any, url: str) -> None:
        """Validate a parsed preset-catalog payload's shape.

        Applied to both network-fetched and cache-loaded payloads so a
        once-poisoned cache (older spec-kit version, manual edit, upstream
        served a bad payload before the network-side guards were added)
        cannot re-crash ``_get_merged_packs`` on subsequent calls.

        Checking only key presence would let a payload like
        ``{"presets": []}`` or ``{"presets": null}`` slip through here and
        then crash with ``AttributeError: 'list' object has no attribute
        'items'`` deep inside ``_get_merged_packs``. The sibling
        integration catalog reader already guards both the root object and
        the nested mapping (see ``integrations/catalog.py``); the preset
        catalog must stay consistent so a malformed payload surfaces as
        the user-facing ``Invalid preset catalog format`` error instead of
        a raw Python traceback.

        Args:
            catalog_data: Parsed JSON payload from the catalog source.
            url: Source URL — used in the error message so the user can
                tell which catalog in a multi-catalog stack is malformed.

        Raises:
            PresetError: If the payload's shape is invalid.
        """
        if not isinstance(catalog_data, dict):
            raise PresetError(
                f"Invalid preset catalog format from {url}: "
                "expected a JSON object"
            )
        if (
            "schema_version" not in catalog_data
            or "presets" not in catalog_data
        ):
            raise PresetError(f"Invalid preset catalog format from {url}")
        if not isinstance(catalog_data.get("presets"), dict):
            raise PresetError(
                f"Invalid preset catalog format from {url}: "
                "'presets' must be a JSON object"
            )

    def _load_catalog_config(self, config_path: Path) -> Optional[List[PresetCatalogEntry]]:
        """Load catalog stack configuration from a YAML file.

        Args:
            config_path: Path to preset-catalogs.yml

        Returns:
            Ordered list of PresetCatalogEntry objects, or None if file
            doesn't exist or contains no valid catalog entries.

        Raises:
            PresetValidationError: If any catalog entry has an invalid URL,
                the file cannot be parsed, or a priority value is invalid.
        """
        if not config_path.exists():
            return None
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError, UnicodeError) as e:
            raise PresetValidationError(
                f"Failed to read catalog config {config_path}: {e}"
            )
        if not isinstance(data, dict):
            raise PresetValidationError(
                f"Invalid catalog config {config_path}: expected a mapping at root, got {type(data).__name__}"
            )
        catalogs_data = data.get("catalogs", [])
        if not catalogs_data:
            return None
        if not isinstance(catalogs_data, list):
            raise PresetValidationError(
                f"Invalid catalog config: 'catalogs' must be a list, got {type(catalogs_data).__name__}"
            )
        entries: List[PresetCatalogEntry] = []
        for idx, item in enumerate(catalogs_data):
            if not isinstance(item, dict):
                raise PresetValidationError(
                    f"Invalid catalog entry at index {idx}: expected a mapping, got {type(item).__name__}"
                )
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            self._validate_catalog_url(url)
            raw_priority = item.get("priority", idx + 1)
            # Reject bools explicitly: ``bool`` is a subclass of ``int`` so
            # ``int(True)`` silently returns 1, which would let a YAML
            # ``priority: true`` slip through as a valid priority of 1. The
            # sibling integration-catalog reader in ``catalogs.py`` already
            # guards this; mirror the check here so the three catalog
            # validators stay consistent.
            if isinstance(raw_priority, bool):
                raise PresetValidationError(
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {raw_priority!r}"
                )
            try:
                priority = int(raw_priority)
            except (TypeError, ValueError):
                raise PresetValidationError(
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {raw_priority!r}"
                )
            raw_install = item.get("install_allowed", False)
            if isinstance(raw_install, str):
                install_allowed = raw_install.strip().lower() in ("true", "yes", "1")
            else:
                install_allowed = bool(raw_install)
            entries.append(PresetCatalogEntry(
                url=url,
                name=str(item.get("name", f"catalog-{idx + 1}")),
                priority=priority,
                install_allowed=install_allowed,
                description=str(item.get("description", "")),
            ))
        entries.sort(key=lambda e: e.priority)
        return entries if entries else None

    def get_active_catalogs(self) -> List[PresetCatalogEntry]:
        """Get the ordered list of active preset catalogs.

        Resolution order:
        1. SPECKIT_PRESET_CATALOG_URL env var — single catalog replacing all defaults
        2. Project-level .specify/preset-catalogs.yml
        3. User-level ~/.specify/preset-catalogs.yml
        4. Built-in default stack (default + community)

        Returns:
            List of PresetCatalogEntry objects sorted by priority (ascending)

        Raises:
            PresetValidationError: If a catalog URL is invalid
        """
        import sys

        # 1. SPECKIT_PRESET_CATALOG_URL env var replaces all defaults
        if env_value := os.environ.get("SPECKIT_PRESET_CATALOG_URL"):
            catalog_url = env_value.strip()
            self._validate_catalog_url(catalog_url)
            if catalog_url != self.DEFAULT_CATALOG_URL:
                if not getattr(self, "_non_default_catalog_warning_shown", False):
                    print(
                        "Warning: Using non-default preset catalog. "
                        "Only use catalogs from sources you trust.",
                        file=sys.stderr,
                    )
                    self._non_default_catalog_warning_shown = True
            return [PresetCatalogEntry(url=catalog_url, name="custom", priority=1, install_allowed=True, description="Custom catalog via SPECKIT_PRESET_CATALOG_URL")]

        # 2. Project-level config overrides all defaults
        project_config_path = self.project_root / ".specify" / "preset-catalogs.yml"
        catalogs = self._load_catalog_config(project_config_path)
        if catalogs is not None:
            return catalogs

        # 3. User-level config
        user_config_path = Path.home() / ".specify" / "preset-catalogs.yml"
        catalogs = self._load_catalog_config(user_config_path)
        if catalogs is not None:
            return catalogs

        # 4. Built-in default stack
        return [
            PresetCatalogEntry(url=self.DEFAULT_CATALOG_URL, name="default", priority=1, install_allowed=True, description="Built-in catalog of installable presets"),
            PresetCatalogEntry(url=self.COMMUNITY_CATALOG_URL, name="community", priority=2, install_allowed=False, description="Community-contributed presets (discovery only)"),
        ]

    def get_catalog_url(self) -> str:
        """Get the primary catalog URL.

        Returns the URL of the highest-priority catalog. Kept for backward
        compatibility. Use get_active_catalogs() for full multi-catalog support.

        Returns:
            URL of the primary catalog
        """
        active = self.get_active_catalogs()
        return active[0].url if active else self.DEFAULT_CATALOG_URL

    def _get_cache_paths(self, url: str):
        """Get cache file paths for a given catalog URL.

        For the DEFAULT_CATALOG_URL, uses legacy cache files for backward
        compatibility. For all other URLs, uses URL-hash-based cache files.

        Returns:
            Tuple of (cache_file_path, cache_metadata_path)
        """
        if url == self.DEFAULT_CATALOG_URL:
            return self.cache_file, self.cache_metadata_file
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return (
            self.cache_dir / f"catalog-{url_hash}.json",
            self.cache_dir / f"catalog-{url_hash}-metadata.json",
        )

    def _is_url_cache_valid(self, url: str) -> bool:
        """Check if cached catalog for a specific URL is still valid."""
        cache_file, metadata_file = self._get_cache_paths(url)
        if not cache_file.exists() or not metadata_file.exists():
            return False
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age_seconds = (
                datetime.now(timezone.utc) - cached_at
            ).total_seconds()
            return age_seconds < self.CACHE_DURATION
        except (
            json.JSONDecodeError,
            OSError,
            UnicodeError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ):
            # Cache validity is best-effort: invalid/missing fields, an
            # unreadable metadata file (permissions / disk), a wrongly
            # encoded one (written by a tool using the system locale
            # codec), or a metadata payload that parses to a non-mapping
            # like ``[]`` or ``"oops"`` (so ``metadata.get(...)`` raises
            # ``AttributeError``) all degrade to "cache invalid" so the
            # caller falls through to a network refetch instead of
            # crashing.
            return False

    def _fetch_single_catalog(self, entry: PresetCatalogEntry, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch a single catalog with per-URL caching.

        Args:
            entry: PresetCatalogEntry describing the catalog to fetch
            force_refresh: If True, bypass cache

        Returns:
            Catalog data dictionary

        Raises:
            PresetError: If catalog cannot be fetched
        """
        cache_file, metadata_file = self._get_cache_paths(entry.url)

        # Use cache if valid. A previously-cached payload must clear the
        # same shape checks as a freshly-fetched one — otherwise a once-
        # poisoned cache would re-crash on every invocation despite the
        # cache being "valid" by age. If validation fails on the cached
        # read, fall through to the network fetch path so the cache gets
        # refreshed.
        if not force_refresh and self._is_url_cache_valid(entry.url):
            try:
                cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
                self._validate_catalog_payload(cached_data, entry.url)
                return cached_data
            except (json.JSONDecodeError, OSError, UnicodeError, PresetError):
                # Cache is best-effort: a JSON-decode failure, an OS-level
                # read failure (permissions / disk / handle limit), or a
                # text-encoding failure on a cache file written by an
                # older client all fall through to the network fetch path.
                # Only the network failure is surfaced to the caller.
                pass

        try:
            with self._open_url(entry.url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            self._validate_catalog_payload(catalog_data, entry.url)

            # Both files are written explicitly as UTF-8 to match the
            # ``read_text(encoding="utf-8")`` on the read side and the
            # ``integrations/catalog.py`` precedent. Without this,
            # platforms whose default encoding isn't UTF-8 would write
            # locale-encoded bytes the read path can't decode, forcing an
            # unnecessary refetch on every invocation. The write itself
            # is best-effort like the read side: an unwritable cache dir
            # (read-only checkout, permissions) must not be re-raised as
            # a ``PresetError`` for a payload that was already fetched
            # and validated.
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(
                    json.dumps(catalog_data, indent=2), encoding="utf-8"
                )
                metadata = {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": entry.url,
                }
                metadata_file.write_text(
                    json.dumps(metadata, indent=2), encoding="utf-8"
                )
            except OSError:
                pass  # Cache is best-effort; proceed with fetched data

            return catalog_data

        except (ImportError, Exception) as e:
            if isinstance(e, PresetError):
                raise
            raise PresetError(
                f"Failed to fetch preset catalog from {entry.url}: {e}"
            )

    def _get_merged_packs(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Fetch and merge presets from all active catalogs.

        Higher-priority catalogs (lower priority number) win on ID conflicts.

        Returns:
            Merged dictionary of pack_id -> pack_data
        """
        active_catalogs = self.get_active_catalogs()
        merged: Dict[str, Dict[str, Any]] = {}

        for entry in reversed(active_catalogs):
            try:
                data = self._fetch_single_catalog(entry, force_refresh)
                for pack_id, pack_data in data.get("presets", {}).items():
                    # Per-entry guard: ``_fetch_single_catalog`` already
                    # validates that ``data["presets"]`` is a mapping, but it
                    # does not (and should not) validate every entry shape
                    # there — one malformed entry shouldn't poison an
                    # otherwise valid catalog. Skip non-mapping entries here
                    # so a payload like ``{"presets": {"foo": [], "bar":
                    # {...}}}`` still merges the valid entries without
                    # crashing on ``**pack_data``. Mirrors
                    # ``integrations/catalog.py:245``.
                    if not isinstance(pack_data, dict):
                        continue
                    pack_data_with_catalog = {**pack_data, "_catalog_name": entry.name, "_install_allowed": entry.install_allowed}
                    merged[pack_id] = pack_data_with_catalog
            except PresetError:
                continue

        return merged

    def is_cache_valid(self) -> bool:
        """Check if cached catalog is still valid.

        Returns ``False`` for any read/decoding failure on the metadata
        file (missing fields, malformed JSON, permissions / disk errors,
        wrong text encoding) so callers fall through to a network refetch
        instead of crashing. Treating cache validity as best-effort
        matches the contract used by ``_is_url_cache_valid`` above.

        Returns:
            True if cache exists and is within cache duration
        """
        if not self.cache_file.exists() or not self.cache_metadata_file.exists():
            return False

        try:
            metadata = json.loads(
                self.cache_metadata_file.read_text(encoding="utf-8")
            )
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age_seconds = (
                datetime.now(timezone.utc) - cached_at
            ).total_seconds()
            return age_seconds < self.CACHE_DURATION
        except (
            json.JSONDecodeError,
            OSError,
            UnicodeError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ):
            # ``AttributeError`` covers the case where the metadata file
            # parses to a non-mapping (``[]``, ``"oops"``, ``42``) so
            # ``metadata.get(...)`` would otherwise crash. All decode /
            # shape failures degrade to "cache invalid" so the caller
            # falls through to a network refetch.
            return False

    def fetch_catalog(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch preset catalog from URL or cache.

        Args:
            force_refresh: If True, bypass cache and fetch from network

        Returns:
            Catalog data dictionary

        Raises:
            PresetError: If catalog cannot be fetched
        """
        catalog_url = self.get_catalog_url()

        # Match the ``_fetch_single_catalog`` cache contract: a poisoned
        # or unreadable cache silently falls through to a network refetch
        # rather than crashing the caller. ``_validate_catalog_payload``
        # is reused here so a cache written by an older client
        # (pre-validation) is rejected and refreshed instead of returning
        # the stale malformed payload.
        if not force_refresh and self.is_cache_valid():
            try:
                metadata = json.loads(
                    self.cache_metadata_file.read_text(encoding="utf-8")
                )
                if metadata.get("catalog_url") == catalog_url:
                    cached_data = json.loads(
                        self.cache_file.read_text(encoding="utf-8")
                    )
                    self._validate_catalog_payload(cached_data, catalog_url)
                    return cached_data
            except (json.JSONDecodeError, OSError, UnicodeError, PresetError):
                # Cache is corrupt, unreadable, or fails the shape check;
                # fall through to network fetch.
                pass

        try:
            with self._open_url(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            # Validate catalog structure. Reuses the same helper as
            # ``_fetch_single_catalog`` so all three branches (root type,
            # missing keys, nested-mapping type) stay consistent.
            self._validate_catalog_payload(catalog_data, catalog_url)

            # Save to cache. Explicit UTF-8 on both writes mirrors the
            # ``read_text(encoding="utf-8")`` on the read side and the
            # ``integrations/catalog.py`` precedent — otherwise platforms
            # whose default encoding isn't UTF-8 would write
            # locale-encoded bytes the read path can't decode, forcing an
            # unnecessary refetch on every invocation. Like the read
            # side, the write is best-effort: an unwritable cache dir
            # must not be re-raised as a ``PresetError`` for a payload
            # that was already fetched and validated.
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.cache_file.write_text(
                    json.dumps(catalog_data, indent=2), encoding="utf-8"
                )

                metadata = {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": catalog_url,
                }
                self.cache_metadata_file.write_text(
                    json.dumps(metadata, indent=2), encoding="utf-8"
                )
            except OSError:
                pass  # Cache is best-effort; proceed with fetched data

            return catalog_data

        except (ImportError, Exception) as e:
            if isinstance(e, PresetError):
                raise
            raise PresetError(
                f"Failed to fetch preset catalog from {catalog_url}: {e}"
            )

    def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search catalog for presets.

        Searches across all active catalogs (merged by priority) so that
        community and custom catalogs are included in results.

        Args:
            query: Search query (searches name, description, tags)
            tag: Filter by specific tag
            author: Filter by author name

        Returns:
            List of matching preset metadata
        """
        try:
            packs = self._get_merged_packs()
        except PresetError:
            return []

        results = []

        for pack_id, pack_data in packs.items():
            if author and pack_data.get("author", "").lower() != author.lower():
                continue

            if tag and tag.lower() not in [
                t.lower() for t in pack_data.get("tags", [])
            ]:
                continue

            if query:
                query_lower = query.lower()
                searchable_text = " ".join(
                    [
                        pack_data.get("name", ""),
                        pack_data.get("description", ""),
                        pack_id,
                    ]
                    + pack_data.get("tags", [])
                ).lower()

                if query_lower not in searchable_text:
                    continue

            results.append({**pack_data, "id": pack_id})

        return results

    def get_pack_info(
        self, pack_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific preset.

        Searches across all active catalogs (merged by priority).

        Args:
            pack_id: ID of the preset

        Returns:
            Pack metadata or None if not found
        """
        try:
            packs = self._get_merged_packs()
        except PresetError:
            return None

        if pack_id in packs:
            return {**packs[pack_id], "id": pack_id}
        return None

    def download_pack(
        self, pack_id: str, target_dir: Optional[Path] = None
    ) -> Path:
        """Download preset ZIP from catalog.

        Args:
            pack_id: ID of the preset to download
            target_dir: Directory to save ZIP file (defaults to cache directory)

        Returns:
            Path to downloaded ZIP file

        Raises:
            PresetError: If pack not found or download fails
        """
        import urllib.error

        pack_info = self.get_pack_info(pack_id)
        if not pack_info:
            raise PresetError(
                f"Preset '{pack_id}' not found in catalog"
            )

        # Bundled presets without a download URL must be installed locally
        if pack_info.get("bundled") and not pack_info.get("download_url"):
            from ..extensions import REINSTALL_COMMAND
            raise PresetError(
                f"Preset '{pack_id}' is bundled with spec-kit and has no download URL. "
                f"It should be installed from the local package. "
                f"Use 'specify preset add {pack_id}' to install from the bundled package, "
                f"or reinstall spec-kit if the bundled files are missing: {REINSTALL_COMMAND}"
            )

        if not pack_info.get("_install_allowed", True):
            catalog_name = pack_info.get("_catalog_name", "unknown")
            raise PresetError(
                f"Preset '{pack_id}' is from the '{catalog_name}' catalog which does not allow installation. "
                f"Use --from with the preset's repository URL instead."
            )

        download_url = pack_info.get("download_url")
        if not download_url:
            raise PresetError(
                f"Preset '{pack_id}' has no download URL"
            )

        from urllib.parse import urlparse

        parsed = urlparse(download_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise PresetError(
                f"Preset download URL must use HTTPS: {download_url}"
            )

        if target_dir is None:
            target_dir = self.cache_dir / "downloads"
        target_dir.mkdir(parents=True, exist_ok=True)

        version = pack_info.get("version", "unknown")
        zip_filename = f"{pack_id}-{version}.zip"
        zip_path = target_dir / zip_filename

        extra_headers = None
        resolved_download_url = self._resolve_github_release_asset_api_url(download_url)
        if resolved_download_url:
            download_url = resolved_download_url
            extra_headers = {"Accept": "application/octet-stream"}

        try:
            with self._open_url(download_url, timeout=60, extra_headers=extra_headers) as response:
                zip_data = response.read()

            verify_archive_sha256(
                zip_data, pack_info.get("sha256"), pack_id, PresetError
            )

            zip_path.write_bytes(zip_data)
            return zip_path

        except urllib.error.URLError as e:
            raise PresetError(
                f"Failed to download preset from {download_url}: {e}"
            )
        except IOError as e:
            raise PresetError(f"Failed to save preset ZIP: {e}")

    def clear_cache(self):
        """Clear all catalog cache files, including per-URL hashed caches."""
        if self.cache_dir.exists():
            for f in self.cache_dir.iterdir():
                if f.is_file() and f.name.startswith("catalog"):
                    f.unlink(missing_ok=True)


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
        # Use keys() to track ALL extensions (including corrupted entries) without deep copy
        # This prevents corrupted entries from being picked up as "unregistered" dirs
        registered_extension_ids = registry.keys()

        # Get all registered extensions including disabled; we filter disabled manually below
        all_registered = registry.list_by_priority(include_disabled=True)

        all_extensions: list[tuple[int, str, dict | None]] = []

        # Only include enabled extensions in the result
        for ext_id, metadata in all_registered:
            # Skip disabled extensions
            if not metadata.get("enabled", True):
                continue
            priority = normalize_priority(metadata.get("priority") if metadata else None)
            all_extensions.append((priority, ext_id, metadata))

        # Add unregistered directories with implicit priority=10
        for ext_dir in self.extensions_dir.iterdir():
            if not ext_dir.is_dir() or ext_dir.name.startswith("."):
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
            registry = PresetRegistry(self.presets_dir)
            for pack_id, _metadata in registry.list_by_priority():
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
        from specify_cli import _locate_core_pack, _repo_root  # local import to avoid cycles
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
            registry = PresetRegistry(self.presets_dir)
            for pack_id, _metadata in registry.list_by_priority():
                pack_dir = self.presets_dir / pack_id
                try:
                    resolved.relative_to(pack_dir)
                    meta = registry.get(pack_id)
                    version = meta.get("version", "?") if meta else "?"
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
            registry = PresetRegistry(self.presets_dir)
            for pack_id, metadata in registry.list_by_priority():
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
                        except (yaml.YAMLError, OSError):
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
            # Try convention-based lookup first
            candidate = _find_in_subdirs(ext_dir)
            # If not found and this is a command, check extension manifest
            if candidate is None and template_type == "command":
                ext_manifest_path = ext_dir / "extension.yml"
                if ext_manifest_path.exists():
                    try:
                        from ..extensions import ExtensionManifest, ValidationError as ExtValidationError
                        ext_manifest = ExtensionManifest(ext_manifest_path)
                        for cmd in ext_manifest.commands:
                            if cmd.get("name") == template_name:
                                cmd_file = cmd.get("file")
                                if cmd_file:
                                    c = ext_dir / cmd_file
                                    if c.exists():
                                        candidate = c
                                break
                    except (ExtValidationError, yaml.YAMLError):
                        # Invalid extension manifest — fall back to
                        # convention-based lookup (already attempted above).
                        pass
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

        def _read_layer_content(layer: Dict[str, Any]) -> str:
            """Read a layer's raw text, rewriting extension-relative subdir
            references (agents/, knowledge-base/, etc.) to their installed
            location when the layer is extension-provided (#2101).

            Extension layers are always inserted with strategy "replace"
            (see collect_all_layers), so a layer only ever needs this
            rewrite when it wins outright above or serves as the
            composition base below — never as a mid-stack composing
            (append/prepend/wrap) layer.
            """
            text = layer["path"].read_text(encoding="utf-8")
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
            layer_content = layer["path"].read_text(encoding="utf-8")
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
                for key in ("scripts", "agent_scripts"):
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
