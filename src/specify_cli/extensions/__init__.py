"""
Extension Manager for Spec Kit

Handles installation, removal, and management of Spec Kit extensions.
Extensions are modular packages that add commands and functionality to spec-kit
without bloating the core framework.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import pathspec
import yaml
from packaging import version as pkg_version
from packaging.specifiers import InvalidSpecifier, SpecifierSet

from .._assets import _locate_core_pack, _repo_root
from .._init_options import is_ai_skills_enabled
from .._invocation_style import is_dollar_skills_agent, is_slash_skills_agent
from .._utils import dump_frontmatter, relative_extension_path_violation, version_satisfies
from ..catalogs import CatalogEntry as BaseCatalogEntry
from ..catalogs import CatalogStackBase
from ..shared_infra import verify_archive_sha256

_FALLBACK_CORE_COMMAND_NAMES = frozenset(
    {
        "analyze",
        "checklist",
        "clarify",
        "constitution",
        "converge",
        "implement",
        "plan",
        "specify",
        "tasks",
        "taskstoissues",
    }
)
EXTENSION_COMMAND_NAME_PATTERN = re.compile(r"^speckit\.([a-z0-9-]+)\.([a-z0-9-]+)$")

VALID_EFFECTS = frozenset({"read-only", "read-write"})

DEFAULT_HOOK_PRIORITY = 10

REINSTALL_COMMAND = "uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git"


def _load_core_command_names() -> frozenset[str]:
    """Discover bundled core command names from the packaged templates.

    Prefer the wheel-time ``core_pack`` bundle when present, and fall back to
    the source checkout when running from the repository. If neither is
    available, use the baked-in fallback set so validation still works.

    Path resolution is delegated to the canonical ``_assets`` resolvers
    (``_locate_core_pack`` / ``_repo_root``) — the same ones the presets and
    bundle loaders use — rather than bespoke ``Path(__file__)`` arithmetic.
    Hand-counted ``.parent`` chains silently broke discovery once already: the
    #3014 move of this module from ``specify_cli/extensions.py`` to
    ``specify_cli/extensions/__init__.py`` pushed the file one directory deeper
    without updating the counts, so both candidates resolved to non-existent
    paths and every call fell through to the fallback (#3274). The shared
    resolvers are anchored to the package root, so discovery survives future
    module moves.
    """
    core_pack = _locate_core_pack()
    candidate_dirs = [
        # Wheel install: force-include maps templates/commands → core_pack/commands.
        core_pack / "commands" if core_pack is not None else None,
        # Source checkout / editable install: repo-root templates/commands.
        _repo_root() / "templates" / "commands",
    ]

    for commands_dir in candidate_dirs:
        if commands_dir is None or not commands_dir.is_dir():
            continue

        command_names = {
            command_file.stem
            for command_file in commands_dir.iterdir()
            if command_file.is_file() and command_file.suffix == ".md"
        }
        if command_names:
            return frozenset(command_names)

    return _FALLBACK_CORE_COMMAND_NAMES


CORE_COMMAND_NAMES = _load_core_command_names()


class ExtensionError(Exception):
    """Base exception for extension-related errors."""

    pass


class ValidationError(ExtensionError):
    """Raised when extension manifest validation fails."""

    pass


class CompatibilityError(ExtensionError):
    """Raised when extension is incompatible with current environment."""

    pass


def normalize_priority(value: Any, default: int = DEFAULT_HOOK_PRIORITY) -> int:
    """Normalize a stored priority value for sorting and display.

    Corrupted registry data may contain missing, non-numeric, non-positive, or
    boolean values. In those cases, fall back to the default priority.

    Args:
        value: Priority value to normalize (may be int, str, None, etc.)
        default: Default priority to use for invalid values

    Returns:
        Normalized priority as positive integer (>= 1)
    """
    if isinstance(value, bool):
        return default
    try:
        priority = int(value)
    except (TypeError, ValueError):
        return default
    return priority if priority >= 1 else default


def coerce_hook_entries(hook_config: Any) -> List[Any]:
    """Return a hook event's config as a list of entries.

    A hook event may be declared as a single mapping or a list of mappings.
    Both shapes are normalized to a list so callers can iterate uniformly.
    """
    return hook_config if isinstance(hook_config, list) else [hook_config]


@dataclass
class CatalogEntry(BaseCatalogEntry):
    """Represents a single catalog entry in the catalog stack."""


class ExtensionManifest:
    """Represents and validates an extension manifest (extension.yml)."""

    SCHEMA_VERSION = "1.0"
    REQUIRED_FIELDS = ["schema_version", "extension", "requires", "provides"]

    def __init__(self, manifest_path: Path):
        """Load and validate extension manifest.

        Args:
            manifest_path: Path to extension.yml file

        Raises:
            ValidationError: If manifest is invalid
        """
        self.path = manifest_path
        self.warnings: List[str] = []
        self.data = self._load_yaml(manifest_path)
        self._validate()

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML file safely."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {path}: {e}")
        except FileNotFoundError:
            raise ValidationError(f"Manifest not found: {path}")
        except UnicodeDecodeError as e:
            raise ValidationError(
                f"Manifest is not valid UTF-8: {path} ({e.reason} at byte {e.start})"
            )
        except OSError as e:
            raise ValidationError(f"Could not read manifest {path}: {e}")
        if not isinstance(data, dict):
            raise ValidationError(
                f"Manifest must be a YAML mapping, got {type(data).__name__}: {path}"
            )
        return data

    def _validate(self):
        """Validate manifest structure and required fields."""
        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate schema version
        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise ValidationError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        # Validate extension metadata
        ext = self.data["extension"]
        for field in ["id", "name", "version", "description"]:
            if field not in ext:
                raise ValidationError(f"Missing extension.{field}")

        # Validate extension ID format
        if not re.match(r"^[a-z0-9-]+$", ext["id"]):
            raise ValidationError(
                f"Invalid extension ID '{ext['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(ext["version"])
        except pkg_version.InvalidVersion:
            raise ValidationError(f"Invalid version: {ext['version']}")

        # Validate optional category field (free-form string)
        if "category" in ext:
            if not isinstance(ext["category"], str) or not ext["category"].strip():
                raise ValidationError(
                    "Invalid extension.category: must be a non-empty string"
                )

        # Validate optional effect field
        if "effect" in ext:
            if not isinstance(ext["effect"], str) or ext["effect"] not in VALID_EFFECTS:
                raise ValidationError(
                    f"Invalid extension.effect '{ext.get('effect')}': "
                    f"must be one of {sorted(VALID_EFFECTS)}"
                )

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise ValidationError("Missing requires.speckit_version")

        # Validate provides section
        provides = self.data["provides"]
        commands = provides.get("commands", [])
        hooks = self.data.get("hooks")

        if "commands" in provides and not isinstance(commands, list):
            raise ValidationError("Invalid provides.commands: expected a list")
        if "hooks" in self.data and not isinstance(hooks, dict):
            raise ValidationError("Invalid hooks: expected a mapping")

        has_commands = bool(commands)
        has_hooks = bool(hooks)

        if not has_commands and not has_hooks:
            raise ValidationError("Extension must provide at least one command or hook")

        # Validate hook values (if present).
        # Each event is a single mapping or a list of mappings.
        if hooks:
            for hook_name, hook_config in hooks.items():
                if isinstance(hook_config, list) and not hook_config:
                    raise ValidationError(
                        f"Invalid hook '{hook_name}': list must contain at least one entry"
                    )
                for entry in coerce_hook_entries(hook_config):
                    if not isinstance(entry, dict):
                        raise ValidationError(
                            f"Invalid hook '{hook_name}': "
                            "expected a mapping or list of mappings"
                        )
                    if not entry.get("command"):
                        raise ValidationError(
                            f"Hook '{hook_name}' missing required 'command' field"
                        )
                    if "priority" in entry:
                        priority = entry["priority"]
                        if not isinstance(priority, int) or isinstance(priority, bool):
                            raise ValidationError(
                                f"Hook '{hook_name}' has invalid 'priority': "
                                "must be an integer"
                            )
                        if priority < 1:
                            raise ValidationError(
                                f"Hook '{hook_name}' has invalid 'priority': "
                                "must be >= 1"
                            )

        # Validate commands; track renames so hook references can be rewritten.
        rename_map: Dict[str, str] = {}
        for cmd in commands:
            if not isinstance(cmd, dict):
                raise ValidationError(
                    "Each command entry in 'provides.commands' must be a mapping"
                )
            if "name" not in cmd or "file" not in cmd:
                raise ValidationError("Command missing 'name' or 'file'")

            # Validate the 'file' field at manifest-load time using the single
            # shared policy in relative_extension_path_violation(), so manifest
            # validation cannot drift from the runtime registrar guard. This is
            # defense-in-depth: the command/skill/preset readers also contain
            # the resolved path, but rejecting an unsafe value here surfaces a
            # clear error instead of silently skipping the command.
            cmd_file = cmd["file"]
            reason = relative_extension_path_violation(cmd_file)
            if reason:
                label = repr(cmd_file) if isinstance(cmd_file, str) else f"for command '{cmd.get('name')}'"
                raise ValidationError(f"Invalid command 'file' {label}: {reason}")

            # Validate command name format
            if not EXTENSION_COMMAND_NAME_PATTERN.match(cmd["name"]):
                corrected = self._try_correct_command_name(cmd["name"], ext["id"])
                if corrected:
                    self.warnings.append(
                        f"Command name '{cmd['name']}' does not follow the required pattern "
                        f"'speckit.{{extension}}.{{command}}'. Registering as '{corrected}'. "
                        f"The extension author should update the manifest to use this name."
                    )
                    rename_map[cmd["name"]] = corrected
                    cmd["name"] = corrected
                else:
                    raise ValidationError(
                        f"Invalid command name '{cmd['name']}': "
                        "must follow pattern 'speckit.{extension}.{command}'"
                    )

            # Validate alias types; no pattern enforcement on aliases — they are
            # intentionally free-form to preserve community extension compatibility
            # (e.g. 'speckit.verify' short aliases used by existing extensions).
            aliases = cmd.get("aliases")
            if aliases is None:
                cmd["aliases"] = []
                aliases = []
            if not isinstance(aliases, list):
                raise ValidationError(
                    f"Aliases for command '{cmd['name']}' must be a list"
                )
            for alias in aliases:
                if not isinstance(alias, str):
                    raise ValidationError(
                        f"Aliases for command '{cmd['name']}' must be strings"
                    )

        # Rewrite any hook command references that pointed at a renamed command or
        # an alias-form ref (ext.cmd → speckit.ext.cmd).  Always emit a warning when
        # the reference is changed so extension authors know to update the manifest.
        for hook_name, hook_data in self.data.get("hooks", {}).items():
            for entry in coerce_hook_entries(hook_data):
                if not isinstance(entry, dict):
                    raise ValidationError(
                        f"Hook '{hook_name}' must be a mapping or list of mappings, "
                        f"got {type(entry).__name__}"
                    )
                command_ref = entry.get("command")
                if not isinstance(command_ref, str):
                    continue
                # Step 1: apply any rename from the auto-correction pass.
                after_rename = rename_map.get(command_ref, command_ref)
                # Step 2: lift alias-form '{ext_id}.cmd' to canonical 'speckit.{ext_id}.cmd'.
                parts = after_rename.split(".")
                if len(parts) == 2 and parts[0] == ext["id"]:
                    final_ref = f"speckit.{ext['id']}.{parts[1]}"
                else:
                    final_ref = after_rename
                if final_ref != command_ref:
                    entry["command"] = final_ref
                    self.warnings.append(
                        f"Hook '{hook_name}' referenced command '{command_ref}'; "
                        f"updated to canonical form '{final_ref}'. "
                        f"The extension author should update the manifest."
                    )

    @staticmethod
    def _try_correct_command_name(name: str, ext_id: str) -> Optional[str]:
        """Try to auto-correct a non-conforming command name to the required pattern.

        Handles the two legacy formats used by community extensions:
          - 'speckit.command'  → 'speckit.{ext_id}.command'
          - '{ext_id}.command' → 'speckit.{ext_id}.command'

        The 'X.Y' form is only corrected when X matches ext_id to ensure the
        result passes the install-time namespace check. Any other prefix is
        uncorrectable and will produce a ValidationError at the call site.

        Returns the corrected name, or None if no safe correction is possible.
        """
        parts = name.split(".")
        if len(parts) == 2:
            if parts[0] == "speckit" or parts[0] == ext_id:
                candidate = f"speckit.{ext_id}.{parts[1]}"
                if EXTENSION_COMMAND_NAME_PATTERN.match(candidate):
                    return candidate
        return None

    @property
    def id(self) -> str:
        """Get extension ID."""
        return self.data["extension"]["id"]

    @property
    def name(self) -> str:
        """Get extension name."""
        return self.data["extension"]["name"]

    @property
    def version(self) -> str:
        """Get extension version."""
        return self.data["extension"]["version"]

    @property
    def description(self) -> str:
        """Get extension description."""
        return self.data["extension"]["description"]

    @property
    def category(self) -> Optional[str]:
        """Get extension category (free-form; common values: docs, code, process, integration, visibility)."""
        return self.data["extension"].get("category")

    @property
    def effect(self) -> Optional[str]:
        """Get extension effect (read-only, read-write)."""
        return self.data["extension"].get("effect")

    @property
    def requires_speckit_version(self) -> str:
        """Get required spec-kit version range."""
        return self.data["requires"]["speckit_version"]

    @property
    def commands(self) -> List[Dict[str, Any]]:
        """Get list of provided commands."""
        return self.data.get("provides", {}).get("commands", [])

    @property
    def hooks(self) -> Dict[str, Any]:
        """Get hook definitions."""
        return self.data.get("hooks", {})

    def get_hash(self) -> str:
        """Calculate SHA256 hash of manifest file."""
        with open(self.path, "rb") as f:
            return f"sha256:{hashlib.sha256(f.read()).hexdigest()}"


class ExtensionRegistry:
    """Manages the registry of installed extensions."""

    REGISTRY_FILE = ".registry"
    SCHEMA_VERSION = "1.0"

    def __init__(self, extensions_dir: Path):
        """Initialize registry.

        Args:
            extensions_dir: Path to .specify/extensions/ directory
        """
        self.extensions_dir = extensions_dir
        self.registry_path = extensions_dir / self.REGISTRY_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return {"schema_version": self.SCHEMA_VERSION, "extensions": {}}

        try:
            with open(self.registry_path, "r") as f:
                data = json.load(f)
            # Validate loaded data is a dict (handles corrupted registry files)
            if not isinstance(data, dict):
                return {"schema_version": self.SCHEMA_VERSION, "extensions": {}}
            # Normalize extensions field (handles corrupted extensions value)
            if not isinstance(data.get("extensions"), dict):
                data["extensions"] = {}
            return data
        except (json.JSONDecodeError, FileNotFoundError):
            # Corrupted or missing registry, start fresh
            return {"schema_version": self.SCHEMA_VERSION, "extensions": {}}

    def _save(self):
        """Save registry to disk."""
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def add(self, extension_id: str, metadata: dict):
        """Add extension to registry.

        Args:
            extension_id: Extension ID
            metadata: Extension metadata (version, source, etc.)
        """
        self.data["extensions"][extension_id] = {
            **copy.deepcopy(metadata),
            "installed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def update(self, extension_id: str, metadata: dict):
        """Update extension metadata in registry, merging with existing entry.

        Merges the provided metadata with the existing entry, preserving any
        fields not specified in the new metadata. The installed_at timestamp
        is always preserved from the original entry.

        Use this method instead of add() when updating existing extension
        metadata (e.g., enabling/disabling) to preserve the original
        installation timestamp and other existing fields.

        Args:
            extension_id: Extension ID
            metadata: Extension metadata fields to update (merged with existing)

        Raises:
            KeyError: If extension is not installed
        """
        extensions = self.data.get("extensions")
        if not isinstance(extensions, dict) or extension_id not in extensions:
            raise KeyError(f"Extension '{extension_id}' is not installed")
        # Merge new metadata with existing, preserving original installed_at
        existing = extensions[extension_id]
        # Handle corrupted registry entries (e.g., string/list instead of dict)
        if not isinstance(existing, dict):
            existing = {}
        # Merge: existing fields preserved, new fields override (deep copy to prevent caller mutation)
        merged = {**existing, **copy.deepcopy(metadata)}
        # Always preserve original installed_at based on key existence, not truthiness,
        # to handle cases where the field exists but may be falsy (legacy/corruption)
        if "installed_at" in existing:
            merged["installed_at"] = existing["installed_at"]
        else:
            # If not present in existing, explicitly remove from merged if caller provided it
            merged.pop("installed_at", None)
        extensions[extension_id] = merged
        self._save()

    def restore(self, extension_id: str, metadata: dict):
        """Restore extension metadata to registry without modifying timestamps.

        Use this method for rollback scenarios where you have a complete backup
        of the registry entry (including installed_at) and want to restore it
        exactly as it was.

        Args:
            extension_id: Extension ID
            metadata: Complete extension metadata including installed_at

        Raises:
            ValueError: If metadata is None or not a dict
        """
        if metadata is None or not isinstance(metadata, dict):
            raise ValueError(
                f"Cannot restore '{extension_id}': metadata must be a dict"
            )
        # Ensure extensions dict exists (handle corrupted registry)
        if not isinstance(self.data.get("extensions"), dict):
            self.data["extensions"] = {}
        self.data["extensions"][extension_id] = copy.deepcopy(metadata)
        self._save()

    def remove(self, extension_id: str):
        """Remove extension from registry.

        Args:
            extension_id: Extension ID
        """
        extensions = self.data.get("extensions")
        if not isinstance(extensions, dict):
            return
        if extension_id in extensions:
            del extensions[extension_id]
            self._save()

    def get(self, extension_id: str) -> Optional[dict]:
        """Get extension metadata from registry.

        Returns a deep copy to prevent callers from accidentally mutating
        nested internal registry state without going through the write path.

        Args:
            extension_id: Extension ID

        Returns:
            Deep copy of extension metadata, or None if not found or corrupted
        """
        extensions = self.data.get("extensions")
        if not isinstance(extensions, dict):
            return None
        entry = extensions.get(extension_id)
        # Return None for missing or corrupted (non-dict) entries
        if entry is None or not isinstance(entry, dict):
            return None
        return copy.deepcopy(entry)

    def list(self) -> Dict[str, dict]:
        """Get all installed extensions with valid metadata.

        Returns a deep copy of extensions with dict metadata only.
        Corrupted entries (non-dict values) are filtered out.

        Returns:
            Dictionary of extension_id -> metadata (deep copies), empty dict if corrupted
        """
        extensions = self.data.get("extensions", {}) or {}
        if not isinstance(extensions, dict):
            return {}
        # Filter to only valid dict entries to match type contract
        return {
            ext_id: copy.deepcopy(meta)
            for ext_id, meta in extensions.items()
            if isinstance(meta, dict)
        }

    def keys(self) -> set:
        """Get all extension IDs including corrupted entries.

        Lightweight method that returns IDs without deep-copying metadata.
        Use this when you only need to check which extensions are tracked.

        Returns:
            Set of extension IDs (includes corrupted entries)
        """
        extensions = self.data.get("extensions", {}) or {}
        if not isinstance(extensions, dict):
            return set()
        return set(extensions.keys())

    def is_installed(self, extension_id: str) -> bool:
        """Check if extension is installed.

        Args:
            extension_id: Extension ID

        Returns:
            True if extension is installed, False if not or registry corrupted
        """
        extensions = self.data.get("extensions")
        if not isinstance(extensions, dict):
            return False
        return extension_id in extensions

    def list_by_priority(self, include_disabled: bool = False) -> List[tuple]:
        """Get all installed extensions sorted by priority.

        Lower priority number = higher precedence (checked first).
        Extensions with equal priority are sorted alphabetically by ID
        for deterministic ordering.

        Args:
            include_disabled: If True, include disabled extensions. Default False.

        Returns:
            List of (extension_id, metadata_copy) tuples sorted by priority.
            Metadata is deep-copied to prevent accidental mutation.
        """
        extensions = self.data.get("extensions", {}) or {}
        if not isinstance(extensions, dict):
            extensions = {}
        sortable_extensions = []
        for ext_id, meta in extensions.items():
            if not isinstance(meta, dict):
                continue
            # Skip disabled extensions unless explicitly requested
            if not include_disabled and not meta.get("enabled", True):
                continue
            metadata_copy = copy.deepcopy(meta)
            metadata_copy["priority"] = normalize_priority(
                metadata_copy.get("priority", 10)
            )
            sortable_extensions.append((ext_id, metadata_copy))
        return sorted(
            sortable_extensions,
            key=lambda item: (item[1]["priority"], item[0]),
        )


class ExtensionManager:
    """Manages extension lifecycle: installation, removal, updates."""

    def __init__(self, project_root: Path):
        """Initialize extension manager.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.extensions_dir = project_root / ".specify" / "extensions"
        self.registry = ExtensionRegistry(self.extensions_dir)

    @staticmethod
    def _collect_manifest_command_names(manifest: ExtensionManifest) -> Dict[str, str]:
        """Collect command and alias names declared by a manifest.

        Performs install-time validation for extension-specific constraints:
        - primary commands must use the canonical `speckit.{extension}.{command}` shape
        - primary commands must use this extension's namespace
        - command namespaces must not shadow core commands
        - duplicate command/alias names inside one manifest are rejected
        - aliases are validated for type and uniqueness only (no pattern enforcement)

        Args:
            manifest: Parsed extension manifest

        Returns:
            Mapping of declared command/alias name -> kind ("command"/"alias")

        Raises:
            ValidationError: If any declared name is invalid
        """
        if manifest.id in CORE_COMMAND_NAMES:
            raise ValidationError(
                f"Extension ID '{manifest.id}' conflicts with core command namespace '{manifest.id}'"
            )

        declared_names: Dict[str, str] = {}

        for cmd in manifest.commands:
            primary_name = cmd["name"]
            aliases = cmd.get("aliases", [])

            if aliases is None:
                aliases = []
            if not isinstance(aliases, list):
                raise ValidationError(
                    f"Aliases for command '{primary_name}' must be a list"
                )

            for kind, name in [("command", primary_name)] + [
                ("alias", alias) for alias in aliases
            ]:
                if not isinstance(name, str):
                    raise ValidationError(
                        f"{kind.capitalize()} for command '{primary_name}' must be a string"
                    )

                # Enforce canonical pattern only for primary command names;
                # aliases are free-form to preserve community extension compat.
                if kind == "command":
                    match = EXTENSION_COMMAND_NAME_PATTERN.match(name)
                    if match is None:
                        raise ValidationError(
                            f"Invalid {kind} '{name}': "
                            "must follow pattern 'speckit.{extension}.{command}'"
                        )

                    namespace = match.group(1)
                    if namespace != manifest.id:
                        raise ValidationError(
                            f"{kind.capitalize()} '{name}' must use extension namespace '{manifest.id}'"
                        )

                    if namespace in CORE_COMMAND_NAMES:
                        raise ValidationError(
                            f"{kind.capitalize()} '{name}' conflicts with core command namespace '{namespace}'"
                        )

                if name in declared_names:
                    raise ValidationError(
                        f"Duplicate command or alias '{name}' in extension manifest"
                    )

                declared_names[name] = kind

        return declared_names

    def _get_installed_command_name_map(
        self,
        exclude_extension_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Return registered command and alias names for installed extensions."""
        installed_names: Dict[str, str] = {}

        for ext_id in self.registry.keys():
            if ext_id == exclude_extension_id:
                continue

            manifest = self.get_extension(ext_id)
            if manifest is None:
                continue

            for cmd in manifest.commands:
                cmd_name = cmd.get("name")
                if isinstance(cmd_name, str):
                    installed_names.setdefault(cmd_name, ext_id)

                aliases = cmd.get("aliases", [])
                if not isinstance(aliases, list):
                    continue

                for alias in aliases:
                    if isinstance(alias, str):
                        installed_names.setdefault(alias, ext_id)

        return installed_names

    def _validate_install_conflicts(self, manifest: ExtensionManifest) -> None:
        """Reject installs that would shadow core or installed extension commands."""
        declared_names = self._collect_manifest_command_names(manifest)
        installed_names = self._get_installed_command_name_map(
            exclude_extension_id=manifest.id
        )

        collisions = [
            f"{name} (already provided by extension '{installed_names[name]}')"
            for name in sorted(declared_names)
            if name in installed_names
        ]
        if collisions:
            raise ValidationError(
                "Extension commands conflict with installed extensions:\n- "
                + "\n- ".join(collisions)
            )

    @staticmethod
    def _load_extensionignore(
        source_dir: Path,
    ) -> Optional[Callable[[str, List[str]], Set[str]]]:
        """Load .extensionignore and return an ignore function for shutil.copytree.

        The .extensionignore file uses .gitignore-compatible patterns (one per line).
        Lines starting with '#' are comments. Blank lines are ignored.
        The .extensionignore file itself is always excluded.

        Pattern semantics mirror .gitignore:
        - '*' matches anything except '/'
        - '**' matches zero or more directories
        - '?' matches any single character except '/'
        - Trailing '/' restricts a pattern to directories only
        - Patterns with '/' (other than trailing) are anchored to the root
        - '!' negates a previously excluded pattern

        Args:
            source_dir: Path to the extension source directory

        Returns:
            An ignore function compatible with shutil.copytree, or None
            if no .extensionignore file exists.
        """
        ignore_file = source_dir / ".extensionignore"
        if not ignore_file.exists():
            return None

        # Pin UTF-8 explicitly: ``Path.read_text`` defaults to the system
        # locale codec on Windows (cp1252 / gb2312 / cp932), which silently
        # corrupts multibyte patterns when the file is shared across
        # machines with different locales. The next line already
        # normalises backslashes "so Windows-authored files work" — the
        # codebase already expects Windows authors to write this file.
        #
        # A file that is not valid UTF-8 is a user-authoring mistake, so
        # surface it as ``ValidationError`` with a pointer to the offending
        # byte — the same pattern ``ExtensionManifest._load_yaml`` uses
        # for ``extension.yml`` (see ``UnicodeDecodeError`` handler in
        # this module). Without the wrap, the raw ``UnicodeDecodeError``
        # would abort installation with a Python traceback instead of a
        # clear message naming the file.
        try:
            raw = ignore_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValidationError(
                f".extensionignore is not valid UTF-8: {ignore_file} "
                f"({e.reason} at byte {e.start})"
            )
        lines: List[str] = raw.splitlines()

        # Normalise backslashes in patterns so Windows-authored files work
        normalised: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                normalised.append(stripped.replace("\\", "/"))
            else:
                # Preserve blanks/comments so pathspec line numbers stay stable
                normalised.append(line)

        # Always ignore the .extensionignore file itself
        normalised.append(".extensionignore")

        spec = pathspec.GitIgnoreSpec.from_lines(normalised)

        def _ignore(directory: str, entries: List[str]) -> Set[str]:
            ignored: Set[str] = set()
            rel_dir = Path(directory).relative_to(source_dir)
            for entry in entries:
                rel_path = str(rel_dir / entry) if str(rel_dir) != "." else entry
                # Normalise to forward slashes for consistent matching
                rel_path_fwd = rel_path.replace("\\", "/")

                entry_full = Path(directory) / entry
                if entry_full.is_dir():
                    # Append '/' so directory-only patterns (e.g. tests/) match
                    if spec.match_file(rel_path_fwd + "/"):
                        ignored.add(entry)
                else:
                    if spec.match_file(rel_path_fwd):
                        ignored.add(entry)
            return ignored

        return _ignore

    def _get_skills_dir(self) -> Optional[Path]:
        """Return the active skills directory for extension skill registration.

        Delegates to :func:`resolve_active_skills_dir` which reads
        init-options, applies the Kimi native-skills fallback, and
        safely creates the directory when ``ai_skills`` is enabled.

        Returns ``None`` (instead of raising) when the directory cannot
        be created due to symlink, containment, or permission issues so
        that callers can fall back gracefully.
        """
        from .. import (
            _print_cli_warning,
            load_init_options,
            resolve_active_skills_dir,
        )

        def _ensure_usable(skills_dir: Path) -> Optional[Path]:
            try:
                skills_dir.mkdir(parents=True, exist_ok=True)
                if not skills_dir.is_dir():
                    raise NotADirectoryError(f"{skills_dir} is not a directory")
            except (OSError, ValueError) as exc:
                _print_cli_warning(
                    "resolve",
                    "skills directory",
                    str(skills_dir),
                    exc,
                    continuing="Continuing without skill registration.",
                )
                return None
            return skills_dir

        try:
            skills_dir = resolve_active_skills_dir(self.project_root)
        except (ValueError, OSError) as exc:
            _print_cli_warning(
                "resolve",
                "skills directory",
                None,
                exc,
                continuing="Continuing without skill registration.",
            )
            return None
        if skills_dir is None:
            return None

        opts = load_init_options(self.project_root)
        if not isinstance(opts, dict):
            return _ensure_usable(skills_dir)
        selected_ai = opts.get("ai")
        if not isinstance(selected_ai, str) or not selected_ai:
            return _ensure_usable(skills_dir)

        from ..agents import CommandRegistrar

        registrar = CommandRegistrar()
        agent_config = registrar.AGENT_CONFIGS.get(selected_ai)
        if agent_config and agent_config.get("extension") == "/SKILL.md":
            agent_skills_dir = registrar._resolve_agent_dir(
                selected_ai, agent_config, self.project_root
            )
            return _ensure_usable(agent_skills_dir)
        return _ensure_usable(skills_dir)

    def _register_extension_skills(
        self,
        manifest: ExtensionManifest,
        extension_dir: Path,
        link_outputs: bool = False,
    ) -> List[str]:
        """Generate SKILL.md files for extension commands as agent skills.

        For every command in the extension manifest, creates a SKILL.md
        file in the agent's skills directory following the agentskills.io
        specification.  This is only done when skills mode was used
        during project initialisation.

        Args:
            manifest: Extension manifest.
            extension_dir: Installed extension directory.
            link_outputs: If True, create dev-mode symlinks for rendered
                skill files when supported by the OS.

        Returns:
            List of skill names that were created (for registry storage).
        """
        skills_dir = self._get_skills_dir()
        if not skills_dir:
            return []

        from .. import load_init_options
        from ..agents import CommandRegistrar
        from ..integrations import get_integration

        written: List[str] = []
        opts = load_init_options(self.project_root)
        if not isinstance(opts, dict):
            opts = {}
        selected_ai = opts.get("ai")
        if not isinstance(selected_ai, str) or not selected_ai:
            return []
        registrar = CommandRegistrar()
        agent_config = registrar.AGENT_CONFIGS.get(selected_ai, {})
        integration = get_integration(selected_ai)

        for cmd_info in manifest.commands:
            cmd_name = cmd_info["name"]
            cmd_file_rel = cmd_info["file"]

            # Guard against path traversal: reject absolute paths and ensure
            # the resolved file stays within the extension directory.
            cmd_path = Path(cmd_file_rel)
            if cmd_path.is_absolute():
                continue
            try:
                ext_root = extension_dir.resolve()
                source_file = (ext_root / cmd_path).resolve()
                source_file.relative_to(ext_root)  # raises ValueError if outside
            except (OSError, ValueError):
                continue

            if not source_file.is_file():
                continue

            # Derive skill name from command name using the same hyphenated
            # convention as hook rendering and preset skill registration.
            short_name_raw = cmd_name
            if short_name_raw.startswith("speckit."):
                short_name_raw = short_name_raw[len("speckit.") :]
            skill_name = f"speckit-{short_name_raw.replace('.', '-')}"

            # Check if skill already exists before creating the directory
            skill_subdir = skills_dir / skill_name
            skill_file = skill_subdir / "SKILL.md"
            cache_root = extension_dir / ".specify-dev" / "extension-skills"
            cache_file = cache_root / skill_name / "SKILL.md"
            use_dev_symlink = link_outputs and not agent_config.get("dev_no_symlink")
            CommandRegistrar._ensure_inside(cache_file, cache_root)
            if skill_file.exists() or skill_file.is_symlink():
                is_expected_dev_symlink = self._is_expected_dev_symlink(
                    skill_file, cache_file
                )
                # Do not overwrite user-customized skills, but allow dev-mode
                # symlinks that point back to this extension's generated cache
                # to be refreshed on a subsequent dev install.
                if not is_expected_dev_symlink:
                    continue

            # Create skill directory; track whether we created it so we can clean
            # up safely if reading the source file subsequently fails.
            created_now = not skill_subdir.exists()
            skill_subdir.mkdir(parents=True, exist_ok=True)

            # Parse the command file — guard against IsADirectoryError / decode errors
            try:
                content = source_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                if created_now:
                    try:
                        skill_subdir.rmdir()  # undo the mkdir; dir is empty at this point
                    except OSError:
                        pass  # best-effort cleanup
                continue
            frontmatter, body = registrar.parse_frontmatter(content)
            frontmatter = registrar._adjust_script_paths(
                frontmatter, extension_id=manifest.id
            )
            body = registrar.resolve_skill_placeholders(
                selected_ai, frontmatter, body, self.project_root, extension_id=manifest.id
            )

            original_desc = frontmatter.get("description", "")
            description = original_desc or f"Extension command: {cmd_name}"

            frontmatter_data = registrar.build_skill_frontmatter(
                selected_ai,
                skill_name,
                description,
                f"extension:{manifest.id}",
            )
            # Preserve the command's argument-hint in the generated skill,
            # mirroring the core template path (ClaudeIntegration.setup injects
            # it for built-in commands). See CommandRegistrar.apply_argument_hint
            # for why the value is added to the dict before serialization rather
            # than via the string-based inject_argument_hint helper.
            registrar.apply_argument_hint(frontmatter, frontmatter_data, integration)
            frontmatter_text = dump_frontmatter(frontmatter_data)

            # Derive a human-friendly title from the command name
            short_name = cmd_name
            if short_name.startswith("speckit."):
                short_name = short_name[len("speckit.") :]
            title_name = short_name.replace(".", " ").replace("-", " ").title()

            skill_content = (
                f"---\n{frontmatter_text}\n---\n\n# {title_name} Skill\n\n{body}\n"
            )
            if integration is not None and hasattr(
                integration, "post_process_skill_content"
            ):
                skill_content = integration.post_process_skill_content(skill_content)

            if use_dev_symlink:
                try:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(skill_content, encoding="utf-8")
                    if skill_file.exists() or skill_file.is_symlink():
                        skill_file.unlink()
                    target = os.path.relpath(cache_file, skill_file.parent)
                    os.symlink(target, skill_file)
                except (OSError, ValueError):
                    if skill_file.is_symlink():
                        skill_file.unlink()
                    skill_file.write_text(skill_content, encoding="utf-8")
            else:
                if skill_file.is_symlink():
                    skill_file.unlink()
                skill_file.write_text(skill_content, encoding="utf-8")
            written.append(skill_name)

        return written

    @staticmethod
    def _is_expected_dev_symlink(skill_file: Path, cache_file: Path) -> bool:
        """Return True when an existing skill file links to its dev cache."""
        if not skill_file.is_symlink():
            return False

        try:
            return skill_file.resolve(strict=False) == cache_file.resolve(strict=False)
        except OSError:
            return False

    def _unregister_extension_skills(
        self,
        skill_names: List[str],
        extension_id: str,
        skills_dir: Optional[Path] = None,
    ) -> None:
        """Remove SKILL.md directories for extension skills.

        Called during extension removal to clean up skill files that
        were created by ``_register_extension_skills()``.

        If *skills_dir* is not provided and ``_get_skills_dir()`` returns
        ``None`` (e.g. the user removed init-options.json or toggled
        ai_skills after installation), we fall back to scanning all known
        agent skills directories so that orphaned skill directories are
        still cleaned up.  In that case each candidate directory is
        verified against the SKILL.md ``metadata.source`` field before
        removal to avoid accidentally deleting user-created skills with
        the same name.

        Args:
            skill_names: List of skill names to remove.
            extension_id: Extension ID used to verify ownership during
                fallback candidate scanning.
            skills_dir: Optional explicit skills directory to use instead
                of resolving via ``_get_skills_dir()``.  Useful when the
                caller needs to target a specific agent's skills directory
                regardless of the currently-active agent in init-options.
        """
        if not skill_names:
            return

        if skills_dir is None:
            skills_dir = self._get_skills_dir()

        if skills_dir:
            # Fast path: we know the exact skills directory
            for skill_name in skill_names:
                # Guard against path traversal from a corrupted registry entry:
                # reject names that are absolute, contain path separators, or
                # resolve to a path outside the skills directory.
                sn_path = Path(skill_name)
                if sn_path.is_absolute() or len(sn_path.parts) != 1:
                    continue
                try:
                    skill_subdir = (skills_dir / skill_name).resolve()
                    skill_subdir.relative_to(skills_dir.resolve())  # raises if outside
                except (OSError, ValueError):
                    continue
                if not skill_subdir.is_dir():
                    continue
                # Safety check: only delete if SKILL.md exists and its
                # metadata.source matches exactly this extension — mirroring
                # the fallback branch — so a corrupted registry entry cannot
                # delete an unrelated user skill.
                skill_md = skill_subdir / "SKILL.md"
                if not skill_md.is_file():
                    continue
                try:
                    import yaml as _yaml

                    raw = skill_md.read_text(encoding="utf-8")
                    source = ""
                    if raw.startswith("---"):
                        parts = raw.split("---", 2)
                        if len(parts) >= 3:
                            fm = _yaml.safe_load(parts[1]) or {}
                            source = (
                                fm.get("metadata", {}).get("source", "")
                                if isinstance(fm, dict)
                                else ""
                            )
                    if source != f"extension:{extension_id}":
                        continue
                except (OSError, UnicodeDecodeError, Exception):
                    continue
                shutil.rmtree(skill_subdir)
        else:
            # Fallback: scan all possible agent skills directories
            from .. import AGENT_CONFIG, DEFAULT_SKILLS_DIR

            candidate_dirs: set[Path] = set()
            for cfg in AGENT_CONFIG.values():
                folder = cfg.get("folder", "")
                if folder:
                    candidate_dirs.add(
                        self.project_root / folder.rstrip("/") / "skills"
                    )
            candidate_dirs.add(self.project_root / DEFAULT_SKILLS_DIR)

            for skills_candidate in candidate_dirs:
                if not skills_candidate.is_dir():
                    continue
                for skill_name in skill_names:
                    # Same path-traversal guard as the fast path above
                    sn_path = Path(skill_name)
                    if sn_path.is_absolute() or len(sn_path.parts) != 1:
                        continue
                    try:
                        skill_subdir = (skills_candidate / skill_name).resolve()
                        skill_subdir.relative_to(
                            skills_candidate.resolve()
                        )  # raises if outside
                    except (OSError, ValueError):
                        continue
                    if not skill_subdir.is_dir():
                        continue
                    # Safety check: only delete if SKILL.md exists and its
                    # metadata.source matches exactly this extension.  If the
                    # file is missing or unreadable we skip to avoid deleting
                    # unrelated user-created directories.
                    skill_md = skill_subdir / "SKILL.md"
                    if not skill_md.is_file():
                        continue
                    try:
                        import yaml as _yaml

                        raw = skill_md.read_text(encoding="utf-8")
                        source = ""
                        if raw.startswith("---"):
                            parts = raw.split("---", 2)
                            if len(parts) >= 3:
                                fm = _yaml.safe_load(parts[1]) or {}
                                source = (
                                    fm.get("metadata", {}).get("source", "")
                                    if isinstance(fm, dict)
                                    else ""
                                )
                        # Only remove skills explicitly created by this extension
                        if source != f"extension:{extension_id}":
                            continue
                    except (OSError, UnicodeDecodeError, Exception):
                        # If we can't verify, skip to avoid accidental deletion
                        continue
                    shutil.rmtree(skill_subdir)

    def check_compatibility(
        self, manifest: ExtensionManifest, speckit_version: str
    ) -> bool:
        """Check if extension is compatible with current spec-kit version.

        Args:
            manifest: Extension manifest
            speckit_version: Current spec-kit version

        Returns:
            True if compatible

        Raises:
            CompatibilityError: If extension is incompatible
        """
        required = manifest.requires_speckit_version

        # Parse version specifier (e.g., ">=0.1.0,<2.0.0")
        try:
            SpecifierSet(required)  # Just to validate
        except InvalidSpecifier:
            raise CompatibilityError(f"Invalid version specifier: {required}")

        if not version_satisfies(speckit_version, required):
            raise CompatibilityError(
                f"Extension requires spec-kit {required}, "
                f"but {speckit_version} is installed.\n"
                f"Upgrade spec-kit with: {REINSTALL_COMMAND}"
            )

        return True

    def install_from_directory(
        self,
        source_dir: Path,
        speckit_version: str,
        register_commands: bool = True,
        priority: int = 10,
        link_commands: bool = False,
        force: bool = False,
    ) -> ExtensionManifest:
        """Install extension from a local directory.

        Args:
            source_dir: Path to extension directory
            speckit_version: Current spec-kit version
            register_commands: If True, register commands with AI agents
            priority: Resolution priority (lower = higher precedence, default 10)
            link_commands: If True, register rendered agent artifacts as
                symlinks to a dev cache when supported by the OS.
            force: If True and extension is already installed, remove it first
                   before proceeding with installation

        Returns:
            Installed extension manifest

        Raises:
            ValidationError: If manifest is invalid or priority is invalid
            CompatibilityError: If extension is incompatible
        """
        # Validate priority
        if priority < 1:
            raise ValidationError("Priority must be a positive integer (1 or higher)")

        # Load and validate manifest
        manifest_path = source_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        # Check compatibility
        self.check_compatibility(manifest, speckit_version)

        # Check if already installed
        if self.registry.is_installed(manifest.id):
            if not force:
                raise ExtensionError(
                    f"Extension '{manifest.id}' is already installed. "
                    f"Use 'specify extension remove {manifest.id}' first, "
                    f"or retry with --force to overwrite."
                )

        # Reject manifests that would shadow core commands or installed extensions.
        self._validate_install_conflicts(manifest)

        # Refuse to install an extension from its own install destination — with
        # --force this would delete the source before copying it (issue #2990).
        dest_dir = self.extensions_dir / manifest.id
        try:
            same_location = source_dir.resolve(strict=False) == dest_dir.resolve(
                strict=False
            )
        except (OSError, RuntimeError):
            same_location = source_dir.absolute() == dest_dir.absolute()
        if same_location:
            raise ValidationError(
                f"Source path is the install destination for '{manifest.id}' "
                f"({dest_dir}). Refusing to proceed to avoid deleting the "
                f"extension. Install from a copy in a different location instead."
            )

        # Remove existing installation AFTER all validations pass so that a
        # validation failure doesn't leave the user with a half-uninstalled
        # extension (configs stranded in .backup/).
        did_remove = False
        if force and self.registry.is_installed(manifest.id):
            # Clear any stale backup from a previous remove so that only the
            # backup produced by the current remove() call is restored later.
            backup_config_dir = self.extensions_dir / ".backup" / manifest.id
            # Check is_symlink first: is_dir() follows symlinks so a
            # symlink-to-directory would pass, but rmtree() raises on them.
            if backup_config_dir.is_symlink():
                backup_config_dir.unlink()
            elif backup_config_dir.is_dir():
                shutil.rmtree(backup_config_dir)
            elif backup_config_dir.exists():
                backup_config_dir.unlink()
            did_remove = self.remove(manifest.id)

        # Install extension (dest_dir computed above during self-install guard)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        ignore_fn = self._load_extensionignore(source_dir)
        shutil.copytree(source_dir, dest_dir, ignore=ignore_fn)

        # Register commands with AI agents
        registered_commands = {}
        if register_commands:
            registrar = CommandRegistrar()
            # Register for all detected agents
            registered_commands = registrar.register_commands_for_all_agents(
                manifest,
                dest_dir,
                self.project_root,
                link_outputs=link_commands,
                create_missing_active_skills_dir=True,
            )

        # Auto-register extension commands as agent skills when skills mode
        # was used during project initialisation (feature parity).
        registered_skills = self._register_extension_skills(
            manifest, dest_dir, link_outputs=link_commands
        )

        # Register hooks and update installed list in extensions.yml
        hook_executor = HookExecutor(self.project_root)
        hook_executor.register_hooks(manifest)

        # Restore config files from backup when --force triggered a removal.
        # Only restore *.yml config files to match what remove() backs up,
        # so unexpected artifacts in .backup/ are not resurrected.
        if did_remove:
            backup_config_dir = self.extensions_dir / ".backup" / manifest.id
            # is_symlink first: is_dir() follows symlinks, but rmtree()
            # raises on them — and we shouldn't follow symlinks to restore.
            if backup_config_dir.is_symlink():
                backup_config_dir.unlink()
            elif backup_config_dir.is_dir():
                for cfg_file in backup_config_dir.iterdir():
                    if (
                        cfg_file.is_file()
                        and not cfg_file.is_symlink()
                        and (
                            cfg_file.name.endswith("-config.yml")
                            or cfg_file.name.endswith("-config.local.yml")
                        )
                    ):
                        shutil.copy2(cfg_file, dest_dir / cfg_file.name)
                shutil.rmtree(backup_config_dir)
            elif backup_config_dir.exists():
                backup_config_dir.unlink()

        # Update registry
        self.registry.add(
            manifest.id,
            {
                "version": manifest.version,
                "source": "local",
                "manifest_hash": manifest.get_hash(),
                "enabled": True,
                "priority": priority,
                "registered_commands": registered_commands,
                "registered_skills": registered_skills,
            },
        )

        return manifest

    def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str,
        priority: int = 10,
        force: bool = False,
    ) -> ExtensionManifest:
        """Install extension from ZIP file.

        Args:
            zip_path: Path to extension ZIP file
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)
            force: If True and extension is already installed, remove it first
                   before proceeding with installation

        Returns:
            Installed extension manifest

        Raises:
            ValidationError: If manifest is invalid or priority is invalid
            CompatibilityError: If extension is incompatible
        """
        # Validate priority early
        if priority < 1:
            raise ValidationError("Priority must be a positive integer (1 or higher)")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Extract ZIP safely (prevent Zip Slip attack)
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Validate all paths first before extracting anything
                temp_path_resolved = temp_path.resolve()
                for member in zf.namelist():
                    member_path = (temp_path / member).resolve()
                    # Use is_relative_to for safe path containment check
                    try:
                        member_path.relative_to(temp_path_resolved)
                    except ValueError:
                        raise ValidationError(
                            f"Unsafe path in ZIP archive: {member} (potential path traversal)"
                        )
                # Only extract after all paths are validated
                zf.extractall(temp_path)

            # Find extension directory (may be nested)
            extension_dir = temp_path
            manifest_path = extension_dir / "extension.yml"

            # Check if manifest is in a subdirectory
            if not manifest_path.exists():
                subdirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    extension_dir = subdirs[0]
                    manifest_path = extension_dir / "extension.yml"

            if not manifest_path.exists():
                raise ValidationError("No extension.yml found in ZIP file")

            # Install from extracted directory
            return self.install_from_directory(
                extension_dir, speckit_version, priority=priority, force=force
            )

    def remove(self, extension_id: str, keep_config: bool = False) -> bool:
        """Remove an installed extension.

        Args:
            extension_id: Extension ID
            keep_config: If True, preserve config files (don't delete extension dir)

        Returns:
            True if extension was removed
        """
        if not self.registry.is_installed(extension_id):
            return False

        # Get registered commands and skills before removal
        metadata = self.registry.get(extension_id)
        registered_commands = (
            metadata.get("registered_commands", {}) if metadata else {}
        )
        raw_skills = metadata.get("registered_skills", []) if metadata else []
        # Normalize: must be a list of plain strings to avoid corrupted-registry errors
        if isinstance(raw_skills, list):
            registered_skills = [s for s in raw_skills if isinstance(s, str)]
        else:
            registered_skills = []

        extension_dir = self.extensions_dir / extension_id

        # Unregister commands from all AI agents
        if registered_commands:
            registrar = CommandRegistrar()
            registrar.unregister_commands(registered_commands, self.project_root)

        # Unregister agent skills
        self._unregister_extension_skills(registered_skills, extension_id)

        if keep_config:
            # Preserve config files, only remove non-config files
            if extension_dir.exists():
                for child in extension_dir.iterdir():
                    # Keep top-level *-config.yml and *-config.local.yml files
                    if child.is_file() and (
                        child.name.endswith("-config.yml")
                        or child.name.endswith("-config.local.yml")
                    ):
                        continue
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
        else:
            # Backup config files before deleting
            if extension_dir.exists():
                # Use subdirectory per extension to avoid name accumulation
                # (e.g., jira-jira-config.yml on repeated remove/install cycles)
                backup_dir = self.extensions_dir / ".backup" / extension_id
                backup_dir.mkdir(parents=True, exist_ok=True)

                # Backup both primary and local override config files
                config_files = list(extension_dir.glob("*-config.yml")) + list(
                    extension_dir.glob("*-config.local.yml")
                )
                for config_file in config_files:
                    backup_path = backup_dir / config_file.name
                    shutil.copy2(config_file, backup_path)

            # Remove extension directory
            if extension_dir.exists():
                shutil.rmtree(extension_dir)

        # Unregister hooks
        hook_executor = HookExecutor(self.project_root)
        hook_executor.unregister_hooks(extension_id)

        # Update registry
        self.registry.remove(extension_id)

        return True

    @staticmethod
    def _valid_name_list(value: Any) -> List[str]:
        """Return string entries from a registry list, ignoring corrupt values."""
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    def unregister_agent_artifacts(self, agent_name: str) -> None:
        """Remove extension files registered for a specific agent.

        Extension command files are tracked per agent in ``registered_commands``.
        Extension skills are scoped to the provided *agent_name*; they are removed
        from that agent's skills directory (resolved via its integration config)
        and the registry field is cleared.

        Skips cleanup when *agent_name* is not a supported agent to avoid
        losing registry entries while leaving orphaned files on disk.
        """
        if not agent_name:
            return

        registrar = CommandRegistrar()
        if agent_name not in registrar.AGENT_CONFIGS:
            return

        # Resolve the skills directory for the specific agent so cleanup is
        # agent-scoped and does not depend on the currently-active agent in
        # init-options.  Use the same helper that extension install uses.
        from .. import _get_skills_dir as resolve_skills_dir

        agent_skills_dir = resolve_skills_dir(self.project_root, agent_name)

        for ext_id, metadata in self.registry.list().items():
            updates: Dict[str, Any] = {}

            registered_commands = metadata.get("registered_commands", {})
            if (
                isinstance(registered_commands, dict)
                and agent_name in registered_commands
            ):
                command_names = self._valid_name_list(
                    registered_commands.get(agent_name)
                )
                if command_names:
                    registrar.unregister_commands(
                        {agent_name: command_names}, self.project_root
                    )

                new_registered = copy.deepcopy(registered_commands)
                new_registered.pop(agent_name, None)
                updates["registered_commands"] = new_registered

            registered_skills = self._valid_name_list(
                metadata.get("registered_skills", [])
            )
            if registered_skills:
                # Only pass the resolved skills_dir when it actually exists.
                # Otherwise let _unregister_extension_skills fall back to
                # scanning all known agent skills directories, which is useful
                # for cleaning up stale entries created by earlier installs.
                skills_dir = agent_skills_dir if agent_skills_dir.is_dir() else None
                self._unregister_extension_skills(
                    registered_skills, ext_id, skills_dir=skills_dir
                )

                # Only reconcile registry state when cleanup was scoped to a
                # specific existing directory. When skills_dir is None,
                # _unregister_extension_skills falls back to scanning multiple
                # candidate directories, so agent_skills_dir cannot be used to
                # infer what was removed.  When skills_dir is set,
                # _unregister_extension_skills may intentionally skip deletion
                # when ownership cannot be verified (e.g., corrupted/missing
                # SKILL.md or mismatching metadata.source).  Only drop registry
                # entries for skill directories that were actually removed so
                # future cleanup attempts can still find skipped ones.
                if skills_dir is not None:
                    remaining_skills = [
                        skill_name
                        for skill_name in registered_skills
                        if (skills_dir / skill_name).is_dir()
                    ]
                    if remaining_skills != registered_skills:
                        updates["registered_skills"] = remaining_skills

            if updates:
                self.registry.update(ext_id, updates)

    def register_enabled_extensions_for_agent(self, agent_name: str) -> None:
        """Register installed, enabled extensions for ``agent_name``.

        Command-file registration is scoped to the explicit ``agent_name``
        argument, so this method can be used after install, upgrade, or switch.
        Extension skill rendering is still scoped to the active ``ai`` /
        ``ai_skills`` settings in init-options, so non-active skills-mode
        targets receive command files here. Per-agent skills parity is tracked
        separately in #2948.
        """
        if not agent_name:
            return

        from .. import load_init_options

        registrar = CommandRegistrar()
        agent_config = registrar.AGENT_CONFIGS.get(agent_name)
        init_options = load_init_options(self.project_root)
        if not isinstance(init_options, dict):
            init_options = {}

        active_agent = init_options.get("ai")
        ai_skills_enabled = is_ai_skills_enabled(init_options)
        skills_mode_active = (
            active_agent == agent_name
            and ai_skills_enabled
            and bool(agent_config)
            and agent_config.get("extension") != "/SKILL.md"
        )

        for ext_id, metadata in self.registry.list().items():
            if not metadata.get("enabled", True):
                continue

            manifest = self.get_extension(ext_id)
            if manifest is None:
                continue

            ext_dir = self.extensions_dir / ext_id

            # Isolate per-extension failures: one extension that fails to
            # register (e.g. an OSError writing a command file) must not abort
            # registration of the remaining enabled extensions for this agent.
            try:
                updates: Dict[str, Any] = {}

                if agent_config and not skills_mode_active:
                    registered = registrar.register_commands_for_agent(
                        agent_name, manifest, ext_dir, self.project_root
                    )
                    registered_commands = metadata.get("registered_commands", {})
                    if not isinstance(registered_commands, dict):
                        registered_commands = {}
                    new_registered = copy.deepcopy(registered_commands)
                    if registered:
                        new_registered[agent_name] = registered
                    else:
                        # Registration returned empty list (e.g., corrupted
                        # manifest pointing at missing command files).  Clear
                        # stale entry so later cleanup doesn't try to remove
                        # files that were never written.
                        new_registered.pop(agent_name, None)
                    if new_registered != registered_commands:
                        updates["registered_commands"] = new_registered

                # Extension *skills* are only ever rendered for the active agent:
                # `_register_extension_skills` resolves the skills dir and
                # frontmatter from init-options["ai"], ignoring ``agent_name``.
                # When this method runs for a non-active agent — as install/upgrade
                # now do for a secondary integration (#2886) — the skills pass would
                # re-render the *active* agent's extension skills as a side effect,
                # resurrecting skill files the user deliberately deleted. Skip it
                # unless the target is the active agent; `switch` is unaffected
                # because it activates the target before registering. (Rendering
                # skills for a non-active target is tracked separately in #2948.)
                if agent_name == active_agent:
                    try:
                        registered_skills = self._register_extension_skills(
                            manifest, ext_dir
                        )
                    except Exception as skills_err:
                        # Skills are a companion artifact.  If command registration
                        # already succeeded, still persist it so later cleanup can
                        # find those command files.
                        from .. import _print_cli_warning

                        _print_cli_warning(
                            "register extension skills for",
                            "extension",
                            ext_id,
                            skills_err,
                            continuing=(
                                "Continuing with available registration results for this "
                                "extension and the remaining extensions."
                            ),
                        )
                    else:
                        if registered_skills:
                            existing_skills = self._valid_name_list(
                                metadata.get("registered_skills", [])
                            )
                            merged_skills = list(
                                dict.fromkeys(existing_skills + registered_skills)
                            )
                            updates["registered_skills"] = merged_skills

                if updates:
                    self.registry.update(ext_id, updates)
            except Exception as ext_err:
                # Best-effort per extension: warn and move on so a single bad
                # extension cannot silently drop the others. See #2950.
                from .. import _print_cli_warning

                _print_cli_warning(
                    "register extension artifacts for",
                    "extension",
                    ext_id,
                    ext_err,
                    continuing="Continuing with the remaining extensions.",
                )
                continue

    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed extensions with metadata.

        Returns:
            List of extension metadata dictionaries
        """
        result = []

        for ext_id, metadata in self.registry.list().items():
            # Ensure metadata is a dictionary to avoid AttributeError when using .get()
            if not isinstance(metadata, dict):
                metadata = {}
            ext_dir = self.extensions_dir / ext_id
            manifest_path = ext_dir / "extension.yml"

            try:
                manifest = ExtensionManifest(manifest_path)
                result.append(
                    {
                        "id": ext_id,
                        "name": manifest.name,
                        "version": metadata.get("version", "unknown"),
                        "description": manifest.description,
                        "enabled": metadata.get("enabled", True),
                        "priority": normalize_priority(metadata.get("priority")),
                        "installed_at": metadata.get("installed_at"),
                        "command_count": len(manifest.commands),
                        "hook_count": len(manifest.hooks),
                    }
                )
            except ValidationError:
                # Corrupted extension
                result.append(
                    {
                        "id": ext_id,
                        "name": ext_id,
                        "version": metadata.get("version", "unknown"),
                        "description": "⚠️ Corrupted extension",
                        "enabled": False,
                        "priority": normalize_priority(metadata.get("priority")),
                        "installed_at": metadata.get("installed_at"),
                        "command_count": 0,
                        "hook_count": 0,
                    }
                )

        return result

    def get_extension(self, extension_id: str) -> Optional[ExtensionManifest]:
        """Get manifest for an installed extension.

        Args:
            extension_id: Extension ID

        Returns:
            Extension manifest or None if not installed
        """
        if not self.registry.is_installed(extension_id):
            return None

        ext_dir = self.extensions_dir / extension_id
        manifest_path = ext_dir / "extension.yml"

        try:
            return ExtensionManifest(manifest_path)
        except ValidationError:
            return None


class CommandRegistrar:
    """Handles registration of extension commands with AI agents.

    This is a backward-compatible wrapper around the shared CommandRegistrar
    in agents.py. Extension-specific methods accept ExtensionManifest objects
    and delegate to the generic API.
    """

    # Re-export AGENT_CONFIGS at class level for direct attribute access
    from ..agents import CommandRegistrar as _AgentRegistrar

    AGENT_CONFIGS = _AgentRegistrar.AGENT_CONFIGS

    def __init__(self):
        from ..agents import CommandRegistrar as _Registrar

        self._registrar = _Registrar()

    # Delegate static/utility methods
    @staticmethod
    def parse_frontmatter(content: str) -> tuple[dict, str]:
        from ..agents import CommandRegistrar as _Registrar

        return _Registrar.parse_frontmatter(content)

    @staticmethod
    def render_frontmatter(fm: dict) -> str:
        from ..agents import CommandRegistrar as _Registrar

        return _Registrar.render_frontmatter(fm)

    @staticmethod
    def _write_copilot_prompt(project_root, cmd_name: str) -> None:
        from ..agents import CommandRegistrar as _Registrar

        _Registrar.write_copilot_prompt(project_root, cmd_name)

    def _render_markdown_command(self, frontmatter, body, ext_id):
        # Preserve extension-specific comment format for backward compatibility
        context_note = f"\n<!-- Extension: {ext_id} -->\n<!-- Config: .specify/extensions/{ext_id}/ -->\n"
        return (
            self._registrar.render_frontmatter(frontmatter) + "\n" + context_note + body
        )

    def _render_toml_command(self, frontmatter, body, ext_id):
        # Preserve extension-specific context comments for backward compatibility
        base = self._registrar.render_toml_command(frontmatter, body, ext_id)
        context_lines = (
            f"# Extension: {ext_id}\n# Config: .specify/extensions/{ext_id}/\n"
        )
        return base.rstrip("\n") + "\n" + context_lines

    def register_commands_for_agent(
        self,
        agent_name: str,
        manifest: ExtensionManifest,
        extension_dir: Path,
        project_root: Path,
        link_outputs: bool = False,
    ) -> List[str]:
        """Register extension commands for a specific agent."""
        if agent_name not in self.AGENT_CONFIGS:
            raise ExtensionError(f"Unsupported agent: {agent_name}")
        context_note = f"\n<!-- Extension: {manifest.id} -->\n<!-- Config: .specify/extensions/{manifest.id}/ -->\n"
        return self._registrar.register_commands(
            agent_name,
            manifest.commands,
            manifest.id,
            extension_dir,
            project_root,
            context_note=context_note,
            link_outputs=link_outputs,
            extension_id=manifest.id,
        )

    def register_commands_for_all_agents(
        self,
        manifest: ExtensionManifest,
        extension_dir: Path,
        project_root: Path,
        link_outputs: bool = False,
        create_missing_active_skills_dir: bool = False,
    ) -> Dict[str, List[str]]:
        """Register extension commands for all detected agents."""
        context_note = f"\n<!-- Extension: {manifest.id} -->\n<!-- Config: .specify/extensions/{manifest.id}/ -->\n"
        return self._registrar.register_commands_for_all_agents(
            manifest.commands,
            manifest.id,
            extension_dir,
            project_root,
            context_note=context_note,
            link_outputs=link_outputs,
            create_missing_active_skills_dir=create_missing_active_skills_dir,
            extension_id=manifest.id,
        )

    def unregister_commands(
        self, registered_commands: Dict[str, List[str]], project_root: Path
    ) -> None:
        """Remove previously registered command files from agent directories."""
        self._registrar.unregister_commands(registered_commands, project_root)

    def register_commands_for_claude(
        self,
        manifest: ExtensionManifest,
        extension_dir: Path,
        project_root: Path,
        link_outputs: bool = False,
    ) -> List[str]:
        """Register extension commands for Claude Code agent."""
        return self.register_commands_for_agent(
            "claude", manifest, extension_dir, project_root, link_outputs=link_outputs
        )


class ExtensionCatalog(CatalogStackBase):
    """Manages extension catalog fetching, caching, and searching."""

    DEFAULT_CATALOG_URL = (
        "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.json"
    )
    COMMUNITY_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.community.json"
    CACHE_DURATION = 3600  # 1 hour in seconds
    CONFIG_FILENAME = "extension-catalogs.yml"
    ENTRY_CLASS = CatalogEntry
    ERROR_TYPE = ValidationError
    VALIDATION_ERROR_TYPE = ValidationError

    def __init__(self, project_root: Path):
        """Initialize extension catalog manager.

        Args:
            project_root: Root directory of the spec-kit project
        """
        self.project_root = project_root
        self.extensions_dir = project_root / ".specify" / "extensions"
        self.cache_dir = self.extensions_dir / ".cache"
        self.cache_file = self.cache_dir / "catalog.json"
        self.cache_metadata_file = self.cache_dir / "catalog-metadata.json"

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
        """Resolve a GitHub release asset URL to its API asset URL.

        Delegates to the shared helper in :mod:`specify_cli._github_http`,
        passing the ``github`` provider hosts from ``auth.json`` so GitHub
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
        """Validate a parsed catalog payload's shape.

        Applied to both network-fetched and cache-loaded payloads so a
        once-poisoned cache (older spec-kit version, manual edit, upstream
        served a bad payload before the network-side guards were added)
        cannot re-crash ``_get_merged_extensions`` on subsequent calls.

        Checking only key presence would let a payload like
        ``{"extensions": []}`` or ``{"extensions": null}`` slip through
        here and then crash with ``AttributeError: 'list' object has no
        attribute 'items'`` deep inside ``_get_merged_extensions``. The
        sibling integration catalog reader already guards both the root
        object and the nested mapping (see ``integrations/catalog.py``);
        the extension catalog must stay consistent so a malformed payload
        surfaces as the user-facing ``Invalid catalog format`` error
        instead of a raw Python traceback.

        Args:
            catalog_data: Parsed JSON payload from the catalog source.
            url: Source URL — used in the error message so the user can
                tell which catalog in a multi-catalog stack is malformed.

        Raises:
            ExtensionError: If the payload's shape is invalid.
        """
        if not isinstance(catalog_data, dict):
            raise ExtensionError(
                f"Invalid catalog format from {url}: expected a JSON object"
            )
        if "schema_version" not in catalog_data or "extensions" not in catalog_data:
            raise ExtensionError(f"Invalid catalog format from {url}")
        if not isinstance(catalog_data.get("extensions"), dict):
            raise ExtensionError(
                f"Invalid catalog format from {url}: 'extensions' must be a JSON object"
            )

    def get_active_catalogs(self) -> List[CatalogEntry]:
        """Get the ordered list of active catalogs.

        Resolution order:
        1. SPECKIT_CATALOG_URL env var — single catalog replacing all defaults
        2. Project-level .specify/extension-catalogs.yml
        3. User-level ~/.specify/extension-catalogs.yml
        4. Built-in default stack (default + community)

        Returns:
            List of CatalogEntry objects sorted by priority (ascending)

        Raises:
            ValidationError: If a catalog URL is invalid
        """
        import sys

        # 1. SPECKIT_CATALOG_URL env var replaces all defaults for backward compat
        if env_value := os.environ.get("SPECKIT_CATALOG_URL"):
            catalog_url = env_value.strip()
            self._validate_catalog_url(catalog_url)
            if catalog_url != self.DEFAULT_CATALOG_URL:
                if not getattr(self, "_non_default_catalog_warning_shown", False):
                    print(
                        "Warning: Using non-default extension catalog. "
                        "Only use catalogs from sources you trust.",
                        file=sys.stderr,
                    )
                    self._non_default_catalog_warning_shown = True
            return [
                self._entry(
                    url=catalog_url,
                    name="custom",
                    priority=1,
                    install_allowed=True,
                    description="Custom catalog via SPECKIT_CATALOG_URL",
                )
            ]

        # 2. Project-level config overrides all defaults
        project_config_path = self.project_root / ".specify" / self.CONFIG_FILENAME
        catalogs = self._load_catalog_config(project_config_path)
        if catalogs is not None:
            return catalogs

        # 3. User-level config
        user_config_path = Path.home() / ".specify" / self.CONFIG_FILENAME
        catalogs = self._load_catalog_config(user_config_path)
        if catalogs is not None:
            return catalogs

        # 4. Built-in default stack
        return [
            self._entry(
                url=self.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
                description="Built-in catalog of installable extensions",
            ),
            self._entry(
                url=self.COMMUNITY_CATALOG_URL,
                name="community",
                priority=2,
                install_allowed=False,
                description="Community-contributed extensions (discovery only)",
            ),
        ]

    def get_catalog_url(self) -> str:
        """Get the primary catalog URL.

        Returns the URL of the highest-priority catalog. Kept for backward
        compatibility. Use get_active_catalogs() for full multi-catalog support.

        Returns:
            URL of the primary catalog

        Raises:
            ValidationError: If a catalog URL is invalid
        """
        active = self.get_active_catalogs()
        return active[0].url if active else self.DEFAULT_CATALOG_URL

    def _fetch_single_catalog(
        self, entry: CatalogEntry, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Fetch a single catalog with per-URL caching.

        For the DEFAULT_CATALOG_URL, uses legacy cache files (self.cache_file /
        self.cache_metadata_file) for backward compatibility. For all other URLs,
        uses URL-hash-based cache files in self.cache_dir.

        Args:
            entry: CatalogEntry describing the catalog to fetch
            force_refresh: If True, bypass cache

        Returns:
            Catalog data dictionary

        Raises:
            ExtensionError: If catalog cannot be fetched or has invalid format
        """
        import urllib.error

        # Determine cache file paths (backward compat for default catalog)
        if entry.url == self.DEFAULT_CATALOG_URL:
            cache_file = self.cache_file
            cache_meta_file = self.cache_metadata_file
            is_valid = not force_refresh and self.is_cache_valid()
        else:
            url_hash = hashlib.sha256(entry.url.encode()).hexdigest()[:16]
            cache_file = self.cache_dir / f"catalog-{url_hash}.json"
            cache_meta_file = self.cache_dir / f"catalog-{url_hash}-metadata.json"
            is_valid = False
            if not force_refresh and cache_file.exists() and cache_meta_file.exists():
                try:
                    metadata = json.loads(cache_meta_file.read_text(encoding="utf-8"))
                    cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
                    if cached_at.tzinfo is None:
                        cached_at = cached_at.replace(tzinfo=timezone.utc)
                    age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                    is_valid = age < self.CACHE_DURATION
                except (
                    json.JSONDecodeError,
                    OSError,
                    UnicodeError,
                    ValueError,
                    KeyError,
                    TypeError,
                    AttributeError,
                ):
                    # Cache validity is best-effort: invalid/missing metadata
                    # fields, an unreadable metadata file (permissions / disk),
                    # a wrongly-encoded metadata file (written by a tool using
                    # the system locale codec), or a metadata payload that
                    # parses to a non-mapping like ``[]`` or ``"oops"`` (so
                    # ``metadata.get(...)`` raises ``AttributeError``) all
                    # degrade to "cache invalid" so the caller falls through
                    # to a network refetch instead of crashing.
                    pass

        # Use cache if valid. A previously-cached payload must clear the
        # same shape checks as a freshly-fetched one — otherwise a once-
        # poisoned cache (older spec-kit version, manual edit, upstream
        # served a bad payload before the network-side guards were added)
        # would re-crash on every invocation despite the cache being
        # "valid" by age. If validation fails on the cached read, fall
        # through to the network fetch path so the cache gets refreshed.
        if is_valid:
            try:
                cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
                self._validate_catalog_payload(cached_data, entry.url)
                return cached_data
            except (json.JSONDecodeError, OSError, UnicodeError, ExtensionError):
                # Cache is best-effort: a JSON-decode failure, an OS-level
                # read failure (permissions / disk / handle limit), or a
                # text-encoding failure on a cache file written by an older
                # client all fall through to the network fetch path. Only
                # the network failure is surfaced to the caller.
                pass

        # Fetch from network
        try:
            with self._open_url(entry.url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            self._validate_catalog_payload(catalog_data, entry.url)

            # Save to cache. Both files are explicitly UTF-8 to match the
            # ``read_text(encoding="utf-8")`` on the read side and the
            # ``integrations/catalog.py`` precedent (see the cache write
            # helpers in ``CatalogCache`` there). Without this, platforms
            # whose default encoding isn't UTF-8 would write locale-encoded
            # bytes that the read path can't decode, forcing an unnecessary
            # network refetch on every invocation. The write itself is
            # best-effort, matching the read side: an unwritable cache dir
            # (read-only checkout, permissions) must not fail a fetch whose
            # payload was already fetched and validated.
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(
                    json.dumps(catalog_data, indent=2), encoding="utf-8"
                )
                cache_meta_file.write_text(
                    json.dumps(
                        {
                            "cached_at": datetime.now(timezone.utc).isoformat(),
                            "catalog_url": entry.url,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass  # Cache is best-effort; proceed with fetched data

            return catalog_data

        except urllib.error.URLError as e:
            raise ExtensionError(f"Failed to fetch catalog from {entry.url}: {e}")
        except json.JSONDecodeError as e:
            raise ExtensionError(f"Invalid JSON in catalog from {entry.url}: {e}")

    def _get_merged_extensions(
        self, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch and merge extensions from all active catalogs.

        Higher-priority (lower priority number) catalogs win on conflicts
        (same extension id in two catalogs). Each extension dict is annotated with:
          - _catalog_name: name of the source catalog
          - _install_allowed: whether installation is allowed from this catalog

        Catalogs that fail to fetch are skipped. Raises ExtensionError only if
        ALL catalogs fail.

        Args:
            force_refresh: If True, bypass all caches

        Returns:
            List of merged extension dicts

        Raises:
            ExtensionError: If all catalogs fail to fetch
        """
        import sys

        active_catalogs = self.get_active_catalogs()
        merged: Dict[str, Dict[str, Any]] = {}
        any_success = False

        for catalog_entry in active_catalogs:
            try:
                catalog_data = self._fetch_single_catalog(catalog_entry, force_refresh)
                any_success = True
            except ExtensionError as e:
                print(
                    f"Warning: Could not fetch catalog '{catalog_entry.name}': {e}",
                    file=sys.stderr,
                )
                continue

            for ext_id, ext_data in catalog_data.get("extensions", {}).items():
                # Per-entry guard: ``_fetch_single_catalog`` already validates
                # that ``catalog_data["extensions"]`` is a mapping, but it
                # does not (and should not) validate every entry shape there
                # — one malformed entry shouldn't poison an otherwise valid
                # catalog. Skip non-mapping entries here so a payload like
                # ``{"extensions": {"foo": [], "bar": {...}}}`` still merges
                # the valid entries without crashing on ``**ext_data``.
                # Mirrors ``integrations/catalog.py:245``.
                if not isinstance(ext_data, dict):
                    continue
                if ext_id not in merged:  # Higher-priority catalog wins
                    merged[ext_id] = {
                        **ext_data,
                        "id": ext_id,
                        "_catalog_name": catalog_entry.name,
                        "_install_allowed": catalog_entry.install_allowed,
                    }

        if not any_success and active_catalogs:
            raise ExtensionError("Failed to fetch any extension catalog")

        return list(merged.values())

    def is_cache_valid(self) -> bool:
        """Check if cached catalog is still valid.

        Returns ``False`` for any read/decoding failure on the metadata
        file (missing fields, malformed JSON, permissions / disk errors,
        wrong text encoding) so callers fall through to a network refetch
        instead of crashing. Treating cache validity as best-effort
        matches the contract used by the per-URL cache check below.

        Returns:
            True if cache exists and is within cache duration
        """
        if not self.cache_file.exists() or not self.cache_metadata_file.exists():
            return False

        try:
            metadata = json.loads(self.cache_metadata_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
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
            # ``AttributeError`` covers the case where the metadata file is
            # valid JSON but parses to a non-mapping (``[]``, ``"oops"``,
            # ``42``) so ``metadata.get(...)`` would otherwise crash. All
            # decode/shape failures degrade to "cache invalid" so the
            # caller falls through to a network refetch.
            return False

    def fetch_catalog(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch extension catalog from URL or cache.

        Args:
            force_refresh: If True, bypass cache and fetch from network

        Returns:
            Catalog data dictionary

        Raises:
            ExtensionError: If catalog cannot be fetched
        """
        catalog_url = self.get_catalog_url()

        # Check the cache first unless ``force_refresh`` was requested,
        # then fall through to a network fetch. Match the
        # ``_fetch_single_catalog`` cache contract: a poisoned or
        # unreadable cache silently falls through to a network refetch
        # rather than crashing the caller. ``_validate_catalog_payload``
        # is reused here so a cache written by an older client
        # (pre-validation) is rejected and refreshed instead of returning
        # the stale malformed payload. ``is_cache_valid`` itself swallows
        # OSError/UnicodeError on the metadata read, so a cache-validity
        # check can't crash this method before the read-side fallback
        # runs.
        if not force_refresh and self.is_cache_valid():
            try:
                cached_data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                self._validate_catalog_payload(cached_data, catalog_url)
                return cached_data
            except (json.JSONDecodeError, OSError, UnicodeError, ExtensionError):
                pass  # Fall through to network fetch

        try:
            import urllib.error

            with self._open_url(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            # Validate catalog structure. Reuses the same helper as
            # ``_fetch_single_catalog`` so all three branches (root type,
            # missing keys, nested-mapping type) stay consistent.
            self._validate_catalog_payload(catalog_data, catalog_url)

            # Save to cache. Explicit UTF-8 on both writes mirrors the
            # ``read_text(encoding="utf-8")`` on the read side and the
            # ``integrations/catalog.py`` precedent — otherwise platforms
            # whose default encoding isn't UTF-8 would write locale-encoded
            # bytes the read path can't decode, forcing an unnecessary
            # refetch on every invocation. Like the read side, the write
            # is best-effort: an unwritable cache dir must not abort a
            # fetch whose payload was already fetched and validated.
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.cache_file.write_text(
                    json.dumps(catalog_data, indent=2), encoding="utf-8"
                )

                # Save cache metadata
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

        except urllib.error.URLError as e:
            raise ExtensionError(f"Failed to fetch catalog from {catalog_url}: {e}")
        except json.JSONDecodeError as e:
            raise ExtensionError(f"Invalid JSON in catalog: {e}")

    def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        verified_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search catalog for extensions across all active catalogs.

        Args:
            query: Search query (searches name, description, tags)
            tag: Filter by specific tag
            author: Filter by author name
            verified_only: If True, show only verified extensions

        Returns:
            List of matching extension metadata, each annotated with
            ``_catalog_name`` and ``_install_allowed`` from its source catalog.
        """
        all_extensions = self._get_merged_extensions()

        results = []

        for ext_data in all_extensions:
            ext_id = ext_data["id"]

            # Apply filters
            if verified_only and not ext_data.get("verified", False):
                continue

            if author and ext_data.get("author", "").lower() != author.lower():
                continue

            if tag and tag.lower() not in [t.lower() for t in ext_data.get("tags", [])]:
                continue

            if query:
                # Search in name, description, and tags
                query_lower = query.lower()
                searchable_text = " ".join(
                    [
                        ext_data.get("name", ""),
                        ext_data.get("description", ""),
                        ext_id,
                    ]
                    + ext_data.get("tags", [])
                ).lower()

                if query_lower not in searchable_text:
                    continue

            results.append(ext_data)

        return results

    def get_extension_info(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific extension.

        Searches all active catalogs in priority order.

        Args:
            extension_id: ID of the extension

        Returns:
            Extension metadata (annotated with ``_catalog_name`` and
            ``_install_allowed``) or None if not found.
        """
        all_extensions = self._get_merged_extensions()
        for ext_data in all_extensions:
            if ext_data["id"] == extension_id:
                return ext_data
        return None

    def download_extension(
        self, extension_id: str, target_dir: Optional[Path] = None
    ) -> Path:
        """Download extension ZIP from catalog.

        Args:
            extension_id: ID of the extension to download
            target_dir: Directory to save ZIP file (defaults to temp directory)

        Returns:
            Path to downloaded ZIP file

        Raises:
            ExtensionError: If extension not found or download fails
        """
        import urllib.error

        # Get extension info from catalog
        ext_info = self.get_extension_info(extension_id)
        if not ext_info:
            raise ExtensionError(f"Extension '{extension_id}' not found in catalog")

        # Bundled extensions without a download URL must be installed locally
        if ext_info.get("bundled") and not ext_info.get("download_url"):
            raise ExtensionError(
                f"Extension '{extension_id}' is bundled with spec-kit and has no download URL. "
                f"It should be installed from the local package. "
                f"Try reinstalling: {REINSTALL_COMMAND}"
            )

        download_url = ext_info.get("download_url")
        if not download_url:
            raise ExtensionError(f"Extension '{extension_id}' has no download URL")

        # Validate download URL requires HTTPS (prevent man-in-the-middle attacks)
        from urllib.parse import urlparse

        parsed = urlparse(download_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            raise ExtensionError(
                f"Extension download URL must use HTTPS: {download_url}"
            )

        # Determine target path
        if target_dir is None:
            target_dir = self.cache_dir / "downloads"
        target_dir.mkdir(parents=True, exist_ok=True)

        version = ext_info.get("version", "unknown")
        zip_filename = f"{extension_id}-{version}.zip"
        zip_path = target_dir / zip_filename

        extra_headers = None
        resolved_download_url = self._resolve_github_release_asset_api_url(download_url)
        if resolved_download_url:
            download_url = resolved_download_url
            extra_headers = {"Accept": "application/octet-stream"}

        # Download the ZIP file
        try:
            with self._open_url(
                download_url, timeout=60, extra_headers=extra_headers
            ) as response:
                zip_data = response.read()

            verify_archive_sha256(
                zip_data, ext_info.get("sha256"), extension_id, ExtensionError
            )

            zip_path.write_bytes(zip_data)
            return zip_path

        except urllib.error.URLError as e:
            raise ExtensionError(
                f"Failed to download extension from {download_url}: {e}"
            )
        except IOError as e:
            raise ExtensionError(f"Failed to save extension ZIP: {e}")

    def clear_cache(self):
        """Clear the catalog cache (both legacy and URL-hash-based files)."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        if self.cache_metadata_file.exists():
            self.cache_metadata_file.unlink()
        # Also clear any per-URL hash-based cache files
        if self.cache_dir.exists():
            for extra_cache in self.cache_dir.glob("catalog-*.json"):
                if extra_cache != self.cache_file:
                    extra_cache.unlink(missing_ok=True)
            for extra_meta in self.cache_dir.glob("catalog-*-metadata.json"):
                extra_meta.unlink(missing_ok=True)


class ConfigManager:
    """Manages layered configuration for extensions.

    Configuration layers (in order of precedence from lowest to highest):
    1. Defaults (from extension.yml)
    2. Project config (.specify/extensions/{ext-id}/{ext-id}-config.yml)
    3. Local config (.specify/extensions/{ext-id}/local-config.yml) - gitignored
    4. Environment variables (SPECKIT_{EXT_ID}_{KEY})
    """

    def __init__(self, project_root: Path, extension_id: str):
        """Initialize config manager for an extension.

        Args:
            project_root: Root directory of the spec-kit project
            extension_id: ID of the extension
        """
        self.project_root = project_root
        self.extension_id = extension_id
        self.extension_dir = project_root / ".specify" / "extensions" / extension_id

    def _load_yaml_config(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Configuration dictionary
        """
        if not file_path.exists():
            return {}

        try:
            data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
            # Coerce a non-mapping root (list/scalar, or None for an empty
            # file) to {} so callers that iterate/merge the result — e.g.
            # _merge_configs' .items() — never crash. Mirrors the same
            # non-dict-root guard in get_project_config().
            return data if isinstance(data, dict) else {}
        except (yaml.YAMLError, OSError, UnicodeError):
            return {}

    def _get_extension_defaults(self) -> Dict[str, Any]:
        """Get default configuration from extension manifest.

        Returns:
            Default configuration dictionary
        """
        manifest_path = self.extension_dir / "extension.yml"
        if not manifest_path.exists():
            return {}

        manifest_data = self._load_yaml_config(manifest_path)
        return manifest_data.get("config", {}).get("defaults", {})

    def _get_project_config(self) -> Dict[str, Any]:
        """Get project-level configuration.

        Returns:
            Project configuration dictionary
        """
        config_file = self.extension_dir / f"{self.extension_id}-config.yml"
        return self._load_yaml_config(config_file)

    def _get_local_config(self) -> Dict[str, Any]:
        """Get local configuration (gitignored, machine-specific).

        Returns:
            Local configuration dictionary
        """
        config_file = self.extension_dir / "local-config.yml"
        return self._load_yaml_config(config_file)

    def _get_env_config(self) -> Dict[str, Any]:
        """Get configuration from environment variables.

        Environment variables follow the pattern:
        SPECKIT_{EXT_ID}_{SECTION}_{KEY}

        For example:
        - SPECKIT_JIRA_CONNECTION_URL
        - SPECKIT_JIRA_PROJECT_KEY

        Returns:
            Configuration dictionary from environment variables
        """
        import os

        env_config = {}
        ext_id_upper = self.extension_id.replace("-", "_").upper()
        prefix = f"SPECKIT_{ext_id_upper}_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Remove prefix and split into parts
            config_path = key[len(prefix) :].lower().split("_")

            # Build nested dict
            current = env_config
            for part in config_path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the final value
            current[config_path[-1]] = value

        return env_config

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Configuration to merge on top

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursive merge for nested dicts
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    def get_config(self) -> Dict[str, Any]:
        """Get final merged configuration for the extension.

        Merges configuration layers in order:
        defaults -> project -> local -> env

        Returns:
            Final merged configuration dictionary
        """
        # Start with defaults
        config = self._get_extension_defaults()

        # Merge project config
        config = self._merge_configs(config, self._get_project_config())

        # Merge local config
        config = self._merge_configs(config, self._get_local_config())

        # Merge environment config
        config = self._merge_configs(config, self._get_env_config())

        return config

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """Get a specific configuration value by dot-notation path.

        Args:
            key_path: Dot-separated path to config value (e.g., "connection.url")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config = ConfigManager(project_root, "jira")
            >>> url = config.get_value("connection.url")
            >>> timeout = config.get_value("connection.timeout", 30)
        """
        config = self.get_config()
        keys = key_path.split(".")

        current = config
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]

        return current

    def has_value(self, key_path: str) -> bool:
        """Check if a configuration value exists.

        Args:
            key_path: Dot-separated path to config value

        Returns:
            True if value exists (even if None), False otherwise
        """
        config = self.get_config()
        keys = key_path.split(".")

        current = config
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]

        return True


class HookExecutor:
    """Manages extension hook execution."""

    def __init__(self, project_root: Path):
        """Initialize hook executor.

        Args:
            project_root: Root directory of the spec-kit project
        """
        self.project_root = project_root
        self.extensions_dir = project_root / ".specify" / "extensions"
        self.config_file = project_root / ".specify" / "extensions.yml"
        self._init_options_cache: Optional[Dict[str, Any]] = None

    def _load_init_options(self) -> Dict[str, Any]:
        """Load persisted init options used to determine invocation style.

        Uses the shared helper from specify_cli and caches values per executor
        instance to avoid repeated filesystem reads during hook rendering.
        """
        if self._init_options_cache is None:
            from .. import load_init_options

            payload = load_init_options(self.project_root)
            self._init_options_cache = payload if isinstance(payload, dict) else {}
        return self._init_options_cache

    @staticmethod
    def _skill_name_from_command(command: Any) -> str:
        """Map a command id like speckit.plan to speckit-plan skill name."""
        if not isinstance(command, str):
            return ""
        command_id = command.strip()
        if not command_id.startswith("speckit."):
            return ""
        return f"speckit-{command_id[len('speckit.') :].replace('.', '-')}"

    def _render_hook_invocation(self, command: Any) -> str:
        """Render an agent-specific invocation string for a hook command."""
        if not isinstance(command, str):
            return ""

        command_id = command.strip()
        if not command_id:
            return ""

        init_options = self._load_init_options()
        selected_ai = init_options.get("ai")
        ai_skills_enabled = is_ai_skills_enabled(init_options)

        dollar_skill_mode = is_dollar_skills_agent(selected_ai, ai_skills_enabled)
        kimi_skill_mode = selected_ai == "kimi"
        cline_mode = selected_ai == "cline"

        skill_name = self._skill_name_from_command(command_id)
        if dollar_skill_mode and skill_name:
            return f"${skill_name}"
        if kimi_skill_mode and skill_name:
            return f"/skill:{skill_name}"
        if cline_mode:
            from ..integrations.cline import format_cline_command_name

            return f"/{format_cline_command_name(command_id)}"

        use_slash = is_slash_skills_agent(selected_ai, ai_skills_enabled)

        if skill_name and use_slash:
            return f"/{skill_name}"

        return f"/{command_id}"

    def get_project_config(self) -> Dict[str, Any]:
        """Load project-level extension configuration.

        Returns:
            Extension configuration dictionary
        """
        if not self.config_file.exists():
            return {
                "installed": [],
                "settings": {"auto_execute_hooks": True},
                "hooks": {},
            }

        try:
            result = yaml.safe_load(self.config_file.read_text(encoding="utf-8"))
            # Coerce non-dict root (including None for an empty file) to the
            # fully-normalized default so callers always get guaranteed fields.
            if not isinstance(result, dict):
                return {
                    "installed": [],
                    "settings": {"auto_execute_hooks": True},
                    "hooks": {},
                }
            # Normalize nested fields so read-only callers like get_hooks_for_event()
            # never see non-dict hooks or non-list installed (Feedback)
            if not isinstance(result.get("hooks"), dict):
                result["hooks"] = {}
            if not isinstance(result.get("installed"), list):
                result["installed"] = []
            if not isinstance(result.get("settings"), dict):
                result["settings"] = {"auto_execute_hooks": True}
            # Sanitize hook event values: coerce non-list values to [] and filter
            # non-dict items so get_hooks_for_event() can safely call .get() (Feedback)
            for event_key in list(result["hooks"]):
                event_val = result["hooks"][event_key]
                if not isinstance(event_val, list):
                    result["hooks"][event_key] = []
                else:
                    result["hooks"][event_key] = [
                        h for h in event_val if isinstance(h, dict)
                    ]
            return result
        except (yaml.YAMLError, OSError, UnicodeError):
            return {
                "installed": [],
                "settings": {"auto_execute_hooks": True},
                "hooks": {},
            }

    def save_project_config(self, config: Dict[str, Any]):
        """Save project-level extension configuration.

        Args:
            config: Configuration dictionary to save
        """
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(
            yaml.dump(
                config, default_flow_style=False, sort_keys=False, allow_unicode=True
            ),
            encoding="utf-8",
        )

    def register_extension(self, extension_id: str):
        """Add extension to the installed list in project config.

        Args:
            extension_id: ID of extension to register
        """
        config = self.get_project_config()

        # Ensure config is a dict (defensive)
        if not isinstance(config, dict):
            config = {}

        raw_installed = config.get("installed")
        sanitized = self._sanitize_installed_list(raw_installed, add_id=extension_id)

        if sanitized != raw_installed:
            config["installed"] = sanitized
            self.save_project_config(config)

    def unregister_extension(self, extension_id: str):
        """Remove extension from the installed list in project config.

        Args:
            extension_id: ID of extension to unregister
        """
        config = self.get_project_config()

        if not isinstance(config, dict):
            config = {}

        raw_installed = config.get("installed")
        sanitized = self._sanitize_installed_list(raw_installed, remove_id=extension_id)

        # Always persist if sanitized state differs from raw config (ensures normalization)
        if sanitized != raw_installed:
            config["installed"] = sanitized
            self.save_project_config(config)

    @staticmethod
    def _sanitize_installed_list(
        raw: object,
        *,
        add_id: str = "",
        remove_id: str = "",
    ) -> list:
        """Normalize, deduplicate, and optionally add/remove an extension id.

        Shared by register_extension() and unregister_extension() to prevent
        the two paths from drifting.

        Args:
            raw: The raw value from config["installed"] (may be non-list).
            add_id: If non-empty, ensure this id is present (plain-string fallback).
            remove_id: If non-empty, remove this id from the list.

        Returns:
            A sanitized, deduplicated, alphabetically-sorted list.
        """
        _VALID_ID = re.compile(r"^[a-z0-9-]+$")

        installed = raw if isinstance(raw, list) else []

        # Keep only entries whose resolved id is a non-empty string matching
        # the extension-id format (^[a-z0-9-]+$), same rule ExtensionManifest enforces.
        def _valid_entry(x: object) -> bool:
            if isinstance(x, str):
                return bool(_VALID_ID.match(x.strip()))
            if isinstance(x, dict):
                eid = x.get("id")
                return isinstance(eid, str) and bool(_VALID_ID.match(eid.strip()))
            return False

        valid = [x for x in installed if _valid_entry(x)]

        # Deduplicate by id: prefer dict (richer metadata) over plain string
        seen: dict = {}  # id -> entry (dict preferred over str)
        for x in valid:
            eid = x.strip() if isinstance(x, str) else x.get("id", "").strip()
            if eid not in seen or isinstance(x, dict):
                seen[eid] = x

        # Validate add_id against the same regex before inserting
        if add_id and _VALID_ID.match(add_id.strip()) and add_id not in seen:
            seen[add_id] = add_id

        if remove_id:
            seen.pop(remove_id, None)

        def _sort_key(x: object) -> str:
            return x if isinstance(x, str) else x.get("id", "")  # type: ignore[return-value]

        return sorted(seen.values(), key=_sort_key)

    def register_hooks(self, manifest: ExtensionManifest):
        """Register extension hooks in project config.

        Args:
            manifest: Extension manifest with hooks to register
        """
        # Always ensure the extension is in the installed list
        self.register_extension(manifest.id)

        config = self.get_project_config()

        # Ensure config is a dict (defensive)
        changed = False
        if not isinstance(config, dict):
            config = {}
            changed = True

        # Ensure hooks dict exists and is a mapping
        if "hooks" not in config or not isinstance(config["hooks"], dict):
            config["hooks"] = {}
            changed = True
        else:
            # Sanitize existing hook lists to prevent crashes in downstream code (Feedback)
            for h_name in list(config["hooks"].keys()):
                h_list = config["hooks"][h_name]
                if not isinstance(h_list, list):
                    config["hooks"][h_name] = []
                    changed = True
                else:
                    sanitized_h_list = [h for h in h_list if isinstance(h, dict)]
                    if len(sanitized_h_list) != len(h_list):
                        config["hooks"][h_name] = sanitized_h_list
                        changed = True

        # Purge this extension's entries from events the new manifest no longer
        # declares, so dropping an event on reinstall leaves no orphans.
        declared_events = set(manifest.hooks.keys())
        for h_name in list(config["hooks"].keys()):
            if h_name in declared_events:
                continue
            kept = [
                h
                for h in config["hooks"][h_name]
                if not (isinstance(h, dict) and h.get("extension") == manifest.id)
            ]
            if kept != config["hooks"][h_name]:
                config["hooks"][h_name] = kept
                changed = True

        # Register each hook
        for hook_name, hook_config in manifest.hooks.items():
            if hook_name not in config["hooks"] or not isinstance(
                config["hooks"][hook_name], list
            ):
                config["hooks"][hook_name] = []
                changed = True

            # Key by command to dedup within the manifest. Deleting before
            # re-insert moves a duplicate to the end so "last wins" also breaks ties.
            new_entries: Dict[str, Dict[str, Any]] = {}
            for entry in coerce_hook_entries(hook_config):
                if not isinstance(entry, dict):
                    continue
                command = entry.get("command")
                if not command:
                    continue
                if command in new_entries:
                    del new_entries[command]
                new_entries[command] = {
                    "extension": manifest.id,
                    "command": command,
                    "enabled": True,
                    "optional": entry.get("optional", True),
                    "priority": normalize_priority(
                        entry.get("priority"), DEFAULT_HOOK_PRIORITY
                    ),
                    "prompt": entry.get("prompt", f"Execute {command}?"),
                    "description": entry.get("description", ""),
                    "condition": entry.get("condition"),
                }

            # Purge then re-add all of this extension's entries for the event.
            # A reinstall with a changed shape (single<->list or a shorter list)
            # then leaves no orphaned entries behind.
            original_list = config["hooks"][hook_name]
            deduped = [
                h
                for h in original_list
                if not (isinstance(h, dict) and h.get("extension") == manifest.id)
            ]
            deduped.extend(new_entries.values())
            if deduped != original_list:
                config["hooks"][hook_name] = deduped
                changed = True

        non_empty = {name: hooks for name, hooks in config["hooks"].items() if hooks}
        if non_empty != config["hooks"]:
            config["hooks"] = non_empty
            changed = True

        if changed:
            self.save_project_config(config)

    def unregister_hooks(self, extension_id: str):
        """Remove extension hooks from project config.

        Args:
            extension_id: ID of extension to unregister
        """
        # Always remove from installed list (Feedback from review)
        self.unregister_extension(extension_id)

        config = self.get_project_config()

        if not isinstance(config, dict):
            config = {}
            # We don't save yet, as there are no hooks to unregister,
            # but unregister_extension above might have already saved a normalized config.
            return

        if "hooks" not in config or not isinstance(config["hooks"], dict):
            return

        # Remove hooks for this extension
        for hook_name in list(config["hooks"].keys()):
            hook_list = config["hooks"][hook_name]
            if not isinstance(hook_list, list):
                config["hooks"][hook_name] = []
                continue
            config["hooks"][hook_name] = [
                h
                for h in hook_list
                if isinstance(h, dict) and h.get("extension") != extension_id
            ]

        # Clean up empty hook arrays
        config["hooks"] = {
            name: hooks for name, hooks in config["hooks"].items() if hooks
        }

        self.save_project_config(config)

    def get_hooks_for_event(self, event_name: str) -> List[Dict[str, Any]]:
        """Get all enabled hooks for a specific event, sorted by priority ascending.

        Lower ``priority`` runs first. Ties keep insertion order via a stable
        sort. Missing or corrupted on-disk priorities fall back to the default.

        Args:
            event_name: Name of the event (e.g., 'after_tasks')

        Returns:
            List of enabled hook configurations sorted by priority.
        """
        config = self.get_project_config()
        hooks = config.get("hooks", {}).get(event_name, [])

        # Filter to enabled hooks only
        enabled = [h for h in hooks if h.get("enabled", True)]
        return sorted(
            enabled,
            key=lambda h: normalize_priority(h.get("priority"), DEFAULT_HOOK_PRIORITY),
        )

    def should_execute_hook(self, hook: Dict[str, Any]) -> bool:
        """Determine if a hook should be executed based on its condition.

        Args:
            hook: Hook configuration

        Returns:
            True if hook should execute, False otherwise
        """
        condition = hook.get("condition")

        if not condition:
            return True

        # Parse and evaluate condition
        try:
            return self._evaluate_condition(condition, hook.get("extension"))
        except Exception:
            # If condition evaluation fails, default to not executing
            return False

    def _evaluate_condition(self, condition: str, extension_id: Optional[str]) -> bool:
        """Evaluate a hook condition expression.

        Supported condition patterns:
        - "config.key.path is set" - checks if config value exists
        - "config.key.path == 'value'" - checks if config equals value
        - "config.key.path != 'value'" - checks if config not equals value
        - "env.VAR_NAME is set" - checks if environment variable exists
        - "env.VAR_NAME == 'value'" - checks if env var equals value

        Args:
            condition: Condition expression string
            extension_id: Extension ID for config lookup

        Returns:
            True if condition is met, False otherwise
        """
        import os

        condition = condition.strip()

        # Pattern: "config.key.path is set"
        if match := re.match(
            r"config\.([a-z0-9_.]+)\s+is\s+set", condition, re.IGNORECASE
        ):
            key_path = match.group(1)
            if not extension_id:
                return False

            config_manager = ConfigManager(self.project_root, extension_id)
            return config_manager.has_value(key_path)

        # Pattern: "config.key.path == 'value'" or "config.key.path != 'value'"
        if match := re.match(
            r'config\.([a-z0-9_.]+)\s*(==|!=)\s*["\']([^"\']+)["\']',
            condition,
            re.IGNORECASE,
        ):
            key_path = match.group(1)
            operator = match.group(2)
            expected_value = match.group(3)

            if not extension_id:
                return False

            config_manager = ConfigManager(self.project_root, extension_id)
            actual_value = config_manager.get_value(key_path)

            # Normalize boolean values to lowercase for comparison
            # (YAML True/False vs condition strings 'true'/'false')
            if isinstance(actual_value, bool):
                normalized_value = "true" if actual_value else "false"
            else:
                normalized_value = str(actual_value)

            if operator == "==":
                return normalized_value == expected_value
            else:  # !=
                return normalized_value != expected_value

        # Pattern: "env.VAR_NAME is set"
        if match := re.match(r"env\.([A-Z0-9_]+)\s+is\s+set", condition, re.IGNORECASE):
            var_name = match.group(1).upper()
            return var_name in os.environ

        # Pattern: "env.VAR_NAME == 'value'" or "env.VAR_NAME != 'value'"
        if match := re.match(
            r'env\.([A-Z0-9_]+)\s*(==|!=)\s*["\']([^"\']+)["\']',
            condition,
            re.IGNORECASE,
        ):
            var_name = match.group(1).upper()
            operator = match.group(2)
            expected_value = match.group(3)

            actual_value = os.environ.get(var_name, "")

            if operator == "==":
                return actual_value == expected_value
            else:  # !=
                return actual_value != expected_value

        # Unknown condition format, default to False for safety
        return False

    def format_hook_message(self, event_name: str, hooks: List[Dict[str, Any]]) -> str:
        """Format hook execution message for display in command output.

        Args:
            event_name: Name of the event
            hooks: List of hooks to execute

        Returns:
            Formatted message string
        """
        if not hooks:
            return ""

        lines = ["\n## Extension Hooks\n"]
        lines.append(f"Hooks available for event '{event_name}':\n")

        for hook in hooks:
            extension = hook.get("extension")
            command = hook.get("command")
            invocation = self._render_hook_invocation(command)
            command_text = (
                command
                if isinstance(command, str) and command.strip()
                else "<missing command>"
            )
            display_invocation = invocation or (
                f"/{command_text}"
                if command_text != "<missing command>"
                else "/<missing command>"
            )
            optional = hook.get("optional", True)
            prompt = hook.get("prompt", "")
            description = hook.get("description", "")

            if optional:
                lines.append(f"\n**Optional Hook**: {extension}")
                lines.append(f"Command: `{display_invocation}`")
                if description:
                    lines.append(f"Description: {description}")
                lines.append(f"\nPrompt: {prompt}")
                lines.append(f"To execute: `{display_invocation}`")
            else:
                lines.append(f"\n**Automatic Hook**: {extension}")
                lines.append(f"Executing: `{display_invocation}`")
                lines.append(f"EXECUTE_COMMAND: {command_text}")
                lines.append(f"EXECUTE_COMMAND_INVOCATION: {display_invocation}")

        return "\n".join(lines)

    def check_hooks_for_event(self, event_name: str) -> Dict[str, Any]:
        """Check for hooks registered for a specific event.

        This method is designed to be called by AI agents after core commands complete.

        Args:
            event_name: Name of the event (e.g., 'after_spec', 'after_tasks')

        Returns:
            Dictionary with hook information:
            - has_hooks: bool - Whether hooks exist for this event
            - hooks: List[Dict] - List of hooks (with condition evaluation applied)
            - message: str - Formatted message for display
        """
        hooks = self.get_hooks_for_event(event_name)

        if not hooks:
            return {"has_hooks": False, "hooks": [], "message": ""}

        # Filter hooks by condition
        executable_hooks = []
        for hook in hooks:
            if self.should_execute_hook(hook):
                executable_hooks.append(hook)

        if not executable_hooks:
            return {
                "has_hooks": False,
                "hooks": [],
                "message": f"# No executable hooks for event '{event_name}' (conditions not met)",
            }

        return {
            "has_hooks": True,
            "hooks": executable_hooks,
            "message": self.format_hook_message(event_name, executable_hooks),
        }

    def execute_hook(self, hook: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single hook command.

        Note: This returns information about how to execute the hook.
        The actual execution is delegated to the AI agent.

        Args:
            hook: Hook configuration

        Returns:
            Dictionary with execution information:
            - command: str - Command to execute
            - extension: str - Extension ID
            - optional: bool - Whether hook is optional
            - description: str - Hook description
        """
        return {
            "command": hook.get("command"),
            "invocation": self._render_hook_invocation(hook.get("command")),
            "extension": hook.get("extension"),
            "optional": hook.get("optional", True),
            "description": hook.get("description", ""),
            "prompt": hook.get("prompt", ""),
        }

    def enable_hooks(self, extension_id: str):
        """Enable all hooks for an extension.

        Args:
            extension_id: Extension ID
        """
        config = self.get_project_config()

        if "hooks" not in config:
            return

        # Enable all hooks for this extension
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = True

        self.save_project_config(config)

    def disable_hooks(self, extension_id: str):
        """Disable all hooks for an extension.

        Args:
            extension_id: Extension ID
        """
        config = self.get_project_config()

        if "hooks" not in config:
            return

        # Disable all hooks for this extension
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = False

        self.save_project_config(config)
