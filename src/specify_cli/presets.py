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
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import re

import yaml
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet, InvalidSpecifier

from .extensions import ExtensionRegistry, normalize_priority


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
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise PresetValidationError(f"Invalid YAML in {path}: {e}")
        except FileNotFoundError:
            raise PresetValidationError(f"Manifest not found: {path}")

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
                return json.load(f)
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
            **metadata,
            "installed_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()

    def remove(self, pack_id: str):
        """Remove preset from registry.

        Args:
            pack_id: Preset ID
        """
        if pack_id in self.data["presets"]:
            del self.data["presets"][pack_id]
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
        if pack_id not in self.data["presets"]:
            raise KeyError(f"Preset '{pack_id}' not found in registry")
        existing = self.data["presets"][pack_id]
        # Merge: existing fields preserved, new fields override
        merged = {**existing, **updates}
        # Always preserve original installed_at based on key existence, not truthiness,
        # to handle cases where the field exists but may be falsy (legacy/corruption)
        if "installed_at" in existing:
            merged["installed_at"] = existing["installed_at"]
        else:
            # If not present in existing, explicitly remove from merged if caller provided it
            merged.pop("installed_at", None)
        self.data["presets"][pack_id] = merged
        self._save()

    def get(self, pack_id: str) -> Optional[dict]:
        """Get preset metadata from registry.

        Args:
            pack_id: Preset ID

        Returns:
            Pack metadata or None if not found
        """
        return self.data["presets"].get(pack_id)

    def list(self) -> Dict[str, dict]:
        """Get all installed presets.

        Returns:
            Dictionary of pack_id -> metadata
        """
        return self.data["presets"]

    def list_by_priority(self) -> List[tuple]:
        """Get all installed presets sorted by priority.

        Lower priority number = higher precedence (checked first).
        Presets with equal priority are sorted alphabetically by ID
        for deterministic ordering.

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
            True if pack is installed
        """
        return pack_id in self.data["presets"]


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
        current = pkg_version.Version(speckit_version)

        try:
            specifier = SpecifierSet(required)
            if current not in specifier:
                raise PresetCompatibilityError(
                    f"Preset requires spec-kit {required}, "
                    f"but {speckit_version} is installed.\n"
                    f"Upgrade spec-kit with: uv tool install specify-cli --force"
                )
        except InvalidSpecifier:
            raise PresetCompatibilityError(
                f"Invalid version specifier: {required}"
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

        try:
            from .agents import CommandRegistrar
        except ImportError:
            return {}

        registrar = CommandRegistrar()
        return registrar.register_commands_for_all_agents(
            filtered, manifest.id, preset_dir, self.project_root
        )

    def _unregister_commands(self, registered_commands: Dict[str, List[str]]) -> None:
        """Remove previously registered command files from agent directories.

        Args:
            registered_commands: Dict mapping agent names to command name lists
        """
        try:
            from .agents import CommandRegistrar
        except ImportError:
            return

        registrar = CommandRegistrar()
        registrar.unregister_commands(registered_commands, self.project_root)

    def _get_skills_dir(self) -> Optional[Path]:
        """Return the skills directory if ``--ai-skills`` was used during init.

        Reads ``.specify/init-options.json`` to determine whether skills
        are enabled and which agent was selected, then delegates to
        the module-level ``_get_skills_dir()`` helper for the concrete path.

        Returns:
            The skills directory ``Path``, or ``None`` if skills were not
            enabled or the init-options file is missing.
        """
        from . import load_init_options, _get_skills_dir

        opts = load_init_options(self.project_root)
        if not opts.get("ai_skills"):
            return None

        agent = opts.get("ai")
        if not agent:
            return None

        skills_dir = _get_skills_dir(self.project_root, agent)
        if not skills_dir.is_dir():
            return None

        return skills_dir

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
        layer when ``--ai-skills`` was used during project initialisation.

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

        from . import SKILL_DESCRIPTIONS, load_init_options

        opts = load_init_options(self.project_root)
        selected_ai = opts.get("ai", "")

        written: List[str] = []

        for cmd_tmpl in filtered:
            cmd_name = cmd_tmpl["name"]
            cmd_file_rel = cmd_tmpl["file"]
            source_file = preset_dir / cmd_file_rel
            if not source_file.exists():
                continue

            # Derive the short command name (e.g. "specify" from "speckit.specify")
            short_name = cmd_name
            if short_name.startswith("speckit."):
                short_name = short_name[len("speckit."):]
            # Kimi CLI discovers skills by directory name and invokes them as
            # /skill:<name> — use dot separator to match packaging convention.
            if selected_ai == "kimi":
                skill_name = f"speckit.{short_name}"
            else:
                skill_name = f"speckit-{short_name}"

            # Only overwrite if the skill already exists (i.e. --ai-skills was used)
            skill_subdir = skills_dir / skill_name
            if not skill_subdir.exists():
                continue

            # Parse the command file
            content = source_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if not isinstance(frontmatter, dict):
                        frontmatter = {}
                    body = parts[2].strip()
                else:
                    frontmatter = {}
                    body = content
            else:
                frontmatter = {}
                body = content

            original_desc = frontmatter.get("description", "")
            enhanced_desc = SKILL_DESCRIPTIONS.get(
                short_name,
                original_desc or f"Spec-kit workflow command: {short_name}",
            )

            frontmatter_data = {
                "name": skill_name,
                "description": enhanced_desc,
                "compatibility": "Requires spec-kit project structure with .specify/ directory",
                "metadata": {
                    "author": "github-spec-kit",
                    "source": f"preset:{manifest.id}",
                },
            }
            frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
            skill_content = (
                f"---\n"
                f"{frontmatter_text}\n"
                f"---\n\n"
                f"# Speckit {short_name.title()} Skill\n\n"
                f"{body}\n"
            )

            skill_file = skill_subdir / "SKILL.md"
            skill_file.write_text(skill_content, encoding="utf-8")
            written.append(skill_name)

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

        from . import SKILL_DESCRIPTIONS

        # Locate core command templates from the project's installed templates
        core_templates_dir = self.project_root / ".specify" / "templates" / "commands"

        for skill_name in skill_names:
            # Derive command name from skill name (speckit-specify -> specify)
            short_name = skill_name
            if short_name.startswith("speckit-"):
                short_name = short_name[len("speckit-"):]
            elif short_name.startswith("speckit."):
                short_name = short_name[len("speckit."):]

            skill_subdir = skills_dir / skill_name
            skill_file = skill_subdir / "SKILL.md"
            if not skill_file.exists():
                continue

            # Try to find the core command template
            core_file = core_templates_dir / f"{short_name}.md" if core_templates_dir.exists() else None
            if core_file and not core_file.exists():
                core_file = None

            if core_file:
                # Restore from core template
                content = core_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        if not isinstance(frontmatter, dict):
                            frontmatter = {}
                        body = parts[2].strip()
                    else:
                        frontmatter = {}
                        body = content
                else:
                    frontmatter = {}
                    body = content

                original_desc = frontmatter.get("description", "")
                enhanced_desc = SKILL_DESCRIPTIONS.get(
                    short_name,
                    original_desc or f"Spec-kit workflow command: {short_name}",
                )

                frontmatter_data = {
                    "name": skill_name,
                    "description": enhanced_desc,
                    "compatibility": "Requires spec-kit project structure with .specify/ directory",
                    "metadata": {
                        "author": "github-spec-kit",
                        "source": f"templates/commands/{short_name}.md",
                    },
                }
                frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
                skill_content = (
                    f"---\n"
                    f"{frontmatter_text}\n"
                    f"---\n\n"
                    f"# Speckit {short_name.title()} Skill\n\n"
                    f"{body}\n"
                )
                skill_file.write_text(skill_content, encoding="utf-8")
            else:
                # No core template — remove the skill entirely
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

        # Register command overrides with AI agents
        registered_commands = self._register_commands(manifest, dest_dir)

        # Update corresponding skills when --ai-skills was previously used
        registered_skills = self._register_skills(manifest, dest_dir)

        self.registry.add(manifest.id, {
            "version": manifest.version,
            "source": "local",
            "manifest_hash": manifest.get_hash(),
            "enabled": True,
            "priority": priority,
            "registered_commands": registered_commands,
            "registered_skills": registered_skills,
        })

        return manifest

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

        # Unregister commands from AI agents
        metadata = self.registry.get(pack_id)
        registered_commands = metadata.get("registered_commands", {}) if metadata else {}
        if registered_commands:
            self._unregister_commands(registered_commands)

        # Restore original skills when preset is removed
        registered_skills = metadata.get("registered_skills", []) if metadata else []
        pack_dir = self.presets_dir / pack_id
        if registered_skills:
            self._unregister_skills(registered_skills, pack_dir)

        if pack_dir.exists():
            shutil.rmtree(pack_dir)

        self.registry.remove(pack_id)
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
                    "version": metadata["version"],
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

        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise PresetValidationError(
                f"Catalog URL must use HTTPS (got {parsed.scheme}://). "
                "HTTP is only allowed for localhost."
            )
        if not parsed.netloc:
            raise PresetValidationError(
                "Catalog URL must be a valid URL with a host."
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
            data = yaml.safe_load(config_path.read_text()) or {}
        except (yaml.YAMLError, OSError) as e:
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
            try:
                priority = int(item.get("priority", idx + 1))
            except (TypeError, ValueError):
                raise PresetValidationError(
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {item.get('priority')!r}"
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
            metadata = json.loads(metadata_file.read_text())
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age_seconds = (
                datetime.now(timezone.utc) - cached_at
            ).total_seconds()
            return age_seconds < self.CACHE_DURATION
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
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

        if not force_refresh and self._is_url_cache_valid(entry.url):
            try:
                return json.loads(cache_file.read_text())
            except json.JSONDecodeError:
                pass

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(entry.url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            if (
                "schema_version" not in catalog_data
                or "presets" not in catalog_data
            ):
                raise PresetError("Invalid preset catalog format")

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(catalog_data, indent=2))
            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": entry.url,
            }
            metadata_file.write_text(json.dumps(metadata, indent=2))

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
                    pack_data_with_catalog = {**pack_data, "_catalog_name": entry.name, "_install_allowed": entry.install_allowed}
                    merged[pack_id] = pack_data_with_catalog
            except PresetError:
                continue

        return merged

    def is_cache_valid(self) -> bool:
        """Check if cached catalog is still valid.

        Returns:
            True if cache exists and is within cache duration
        """
        if not self.cache_file.exists() or not self.cache_metadata_file.exists():
            return False

        try:
            metadata = json.loads(self.cache_metadata_file.read_text())
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age_seconds = (
                datetime.now(timezone.utc) - cached_at
            ).total_seconds()
            return age_seconds < self.CACHE_DURATION
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
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

        if not force_refresh and self.is_cache_valid():
            try:
                metadata = json.loads(self.cache_metadata_file.read_text())
                if metadata.get("catalog_url") == catalog_url:
                    return json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, OSError):
                # Cache is corrupt or unreadable; fall through to network fetch
                pass

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            if (
                "schema_version" not in catalog_data
                or "presets" not in catalog_data
            ):
                raise PresetError("Invalid preset catalog format")

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(catalog_data, indent=2))

            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": catalog_url,
            }
            self.cache_metadata_file.write_text(
                json.dumps(metadata, indent=2)
            )

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
        import urllib.request
        import urllib.error

        pack_info = self.get_pack_info(pack_id)
        if not pack_info:
            raise PresetError(
                f"Preset '{pack_id}' not found in catalog"
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

        try:
            with urllib.request.urlopen(download_url, timeout=60) as response:
                zip_data = response.read()

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
        registered_extensions = registry.list_by_priority()
        registered_extension_ids = {ext_id for ext_id, _ in registered_extensions}

        all_extensions: list[tuple[int, str, dict | None]] = []

        for ext_id, metadata in registered_extensions:
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

    def resolve(
        self,
        template_name: str,
        template_type: str = "template",
    ) -> Optional[Path]:
        """Resolve a template name to its file path.

        Walks the priority stack and returns the first match.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("template", "command", or "script")

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
        if self.presets_dir.exists():
            registry = PresetRegistry(self.presets_dir)
            for pack_id, _metadata in registry.list_by_priority():
                pack_dir = self.presets_dir / pack_id
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
        elif template_type == "script":
            core = self.templates_dir / "scripts" / f"{template_name}{ext}"
            if core.exists():
                return core

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
