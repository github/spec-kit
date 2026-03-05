"""
Extension Manager for Spec Kit

Handles installation, removal, and management of Spec Kit extensions.
Extensions are modular packages that add commands and functionality to spec-kit
without bloating the core framework.
"""

import json
import hashlib
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import re

import yaml
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet, InvalidSpecifier


class ExtensionError(Exception):
    """Base exception for extension-related errors."""
    pass


class ValidationError(ExtensionError):
    """Raised when extension manifest validation fails."""
    pass


class CompatibilityError(ExtensionError):
    """Raised when extension is incompatible with current environment."""
    pass


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
        self.data = self._load_yaml(manifest_path)
        self._validate()

    def _load_yaml(self, path: Path) -> dict:
        """Load YAML file safely."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {path}: {e}")
        except FileNotFoundError:
            raise ValidationError(f"Manifest not found: {path}")

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
        if not re.match(r'^[a-z0-9-]+$', ext["id"]):
            raise ValidationError(
                f"Invalid extension ID '{ext['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(ext["version"])
        except pkg_version.InvalidVersion:
            raise ValidationError(f"Invalid version: {ext['version']}")

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise ValidationError("Missing requires.speckit_version")

        # Validate provides section
        provides = self.data["provides"]
        if "commands" not in provides or not provides["commands"]:
            raise ValidationError("Extension must provide at least one command")

        # Validate commands
        for cmd in provides["commands"]:
            if "name" not in cmd or "file" not in cmd:
                raise ValidationError("Command missing 'name' or 'file'")

            # Validate command name format
            if not re.match(r'^speckit\.[a-z0-9-]+\.[a-z0-9-]+$', cmd["name"]):
                raise ValidationError(
                    f"Invalid command name '{cmd['name']}': "
                    "must follow pattern 'speckit.{extension}.{command}'"
                )

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
    def requires_speckit_version(self) -> str:
        """Get required spec-kit version range."""
        return self.data["requires"]["speckit_version"]

    @property
    def commands(self) -> List[Dict[str, Any]]:
        """Get list of provided commands."""
        return self.data["provides"]["commands"]

    @property
    def hooks(self) -> Dict[str, Any]:
        """Get hook definitions."""
        return self.data.get("hooks", {})

    def get_hash(self) -> str:
        """Calculate SHA256 hash of manifest file."""
        with open(self.path, 'rb') as f:
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
            return {
                "schema_version": self.SCHEMA_VERSION,
                "extensions": {}
            }

        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Corrupted or missing registry, start fresh
            return {
                "schema_version": self.SCHEMA_VERSION,
                "extensions": {}
            }

    def _save(self):
        """Save registry to disk."""
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add(self, extension_id: str, metadata: dict):
        """Add extension to registry.

        Args:
            extension_id: Extension ID
            metadata: Extension metadata (version, source, etc.)
        """
        self.data["extensions"][extension_id] = {
            **metadata,
            "installed_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()

    def remove(self, extension_id: str):
        """Remove extension from registry.

        Args:
            extension_id: Extension ID
        """
        if extension_id in self.data["extensions"]:
            del self.data["extensions"][extension_id]
            self._save()

    def get(self, extension_id: str) -> Optional[dict]:
        """Get extension metadata from registry.

        Args:
            extension_id: Extension ID

        Returns:
            Extension metadata or None if not found
        """
        return self.data["extensions"].get(extension_id)

    def list(self) -> Dict[str, dict]:
        """Get all installed extensions.

        Returns:
            Dictionary of extension_id -> metadata
        """
        return self.data["extensions"]

    def is_installed(self, extension_id: str) -> bool:
        """Check if extension is installed.

        Args:
            extension_id: Extension ID

        Returns:
            True if extension is installed
        """
        return extension_id in self.data["extensions"]


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

    def check_compatibility(
        self,
        manifest: ExtensionManifest,
        speckit_version: str
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
        current = pkg_version.Version(speckit_version)

        # Parse version specifier (e.g., ">=0.1.0,<2.0.0")
        try:
            specifier = SpecifierSet(required)
            if current not in specifier:
                raise CompatibilityError(
                    f"Extension requires spec-kit {required}, "
                    f"but {speckit_version} is installed.\n"
                    f"Upgrade spec-kit with: uv tool install specify-cli --force"
                )
        except InvalidSpecifier:
            raise CompatibilityError(f"Invalid version specifier: {required}")

        return True

    def install_from_directory(
        self,
        source_dir: Path,
        speckit_version: str,
        register_commands: bool = True
    ) -> ExtensionManifest:
        """Install extension from a local directory.

        Args:
            source_dir: Path to extension directory
            speckit_version: Current spec-kit version
            register_commands: If True, register commands with AI agents

        Returns:
            Installed extension manifest

        Raises:
            ValidationError: If manifest is invalid
            CompatibilityError: If extension is incompatible
        """
        # Load and validate manifest
        manifest_path = source_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        # Check compatibility
        self.check_compatibility(manifest, speckit_version)

        # Check if already installed
        if self.registry.is_installed(manifest.id):
            raise ExtensionError(
                f"Extension '{manifest.id}' is already installed. "
                f"Use 'specify extension remove {manifest.id}' first."
            )

        # Install extension
        dest_dir = self.extensions_dir / manifest.id
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir)

        # Register commands with AI agents
        registered_commands = {}
        if register_commands:
            registrar = CommandRegistrar()
            # Register for all detected agents
            registered_commands = registrar.register_commands_for_all_agents(
                manifest, dest_dir, self.project_root
            )

        # Register hooks
        hook_executor = HookExecutor(self.project_root)
        hook_executor.register_hooks(manifest)

        # Update registry
        self.registry.add(manifest.id, {
            "version": manifest.version,
            "source": "local",
            "manifest_hash": manifest.get_hash(),
            "enabled": True,
            "registered_commands": registered_commands
        })

        return manifest

    def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str
    ) -> ExtensionManifest:
        """Install extension from ZIP file.

        Args:
            zip_path: Path to extension ZIP file
            speckit_version: Current spec-kit version

        Returns:
            Installed extension manifest

        Raises:
            ValidationError: If manifest is invalid
            CompatibilityError: If extension is incompatible
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Extract ZIP safely (prevent Zip Slip attack)
            with zipfile.ZipFile(zip_path, 'r') as zf:
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
            return self.install_from_directory(extension_dir, speckit_version)

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

        # Get registered commands before removal
        metadata = self.registry.get(extension_id)
        registered_commands = metadata.get("registered_commands", {})

        extension_dir = self.extensions_dir / extension_id

        # Unregister commands from all AI agents
        if registered_commands:
            registrar = CommandRegistrar()
            for agent_name, cmd_names in registered_commands.items():
                if agent_name not in registrar.AGENT_CONFIGS:
                    continue

                agent_config = registrar.AGENT_CONFIGS[agent_name]
                commands_dir = self.project_root / agent_config["dir"]

                for cmd_name in cmd_names:
                    cmd_file = commands_dir / f"{cmd_name}{agent_config['extension']}"
                    if cmd_file.exists():
                        cmd_file.unlink()

        if keep_config:
            # Preserve config files, only remove non-config files
            if extension_dir.exists():
                for child in extension_dir.iterdir():
                    # Keep top-level *-config.yml and *-config.local.yml files
                    if child.is_file() and (
                        child.name.endswith("-config.yml") or
                        child.name.endswith("-config.local.yml")
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

    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed extensions with metadata.

        Returns:
            List of extension metadata dictionaries
        """
        result = []

        for ext_id, metadata in self.registry.list().items():
            ext_dir = self.extensions_dir / ext_id
            manifest_path = ext_dir / "extension.yml"

            try:
                manifest = ExtensionManifest(manifest_path)
                result.append({
                    "id": ext_id,
                    "name": manifest.name,
                    "version": metadata["version"],
                    "description": manifest.description,
                    "enabled": metadata.get("enabled", True),
                    "installed_at": metadata.get("installed_at"),
                    "command_count": len(manifest.commands),
                    "hook_count": len(manifest.hooks)
                })
            except ValidationError:
                # Corrupted extension
                result.append({
                    "id": ext_id,
                    "name": ext_id,
                    "version": metadata.get("version", "unknown"),
                    "description": "⚠️ Corrupted extension",
                    "enabled": False,
                    "installed_at": metadata.get("installed_at"),
                    "command_count": 0,
                    "hook_count": 0
                })

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


def version_satisfies(current: str, required: str) -> bool:
    """Check if current version satisfies required version specifier.

    Args:
        current: Current version (e.g., "0.1.5")
        required: Required version specifier (e.g., ">=0.1.0,<2.0.0")

    Returns:
        True if version satisfies requirement
    """
    try:
        current_ver = pkg_version.Version(current)
        specifier = SpecifierSet(required)
        return current_ver in specifier
    except (pkg_version.InvalidVersion, InvalidSpecifier):
        return False


class CommandRegistrar:
    """Handles registration of extension commands with AI agents."""

    # Agent configurations with directory, format, and argument placeholder
    AGENT_CONFIGS = {
        "claude": {
            "dir": ".claude/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "gemini": {
            "dir": ".gemini/commands",
            "format": "toml",
            "args": "{{args}}",
            "extension": ".toml"
        },
        "copilot": {
            "dir": ".github/agents",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "cursor": {
            "dir": ".cursor/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "qwen": {
            "dir": ".qwen/commands",
            "format": "toml",
            "args": "{{args}}",
            "extension": ".toml"
        },
        "opencode": {
            "dir": ".opencode/command",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "windsurf": {
            "dir": ".windsurf/workflows",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "kilocode": {
            "dir": ".kilocode/rules",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "auggie": {
            "dir": ".augment/rules",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "roo": {
            "dir": ".roo/rules",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "codebuddy": {
            "dir": ".codebuddy/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "qoder": {
            "dir": ".qoder/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "q": {
            "dir": ".amazonq/prompts",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "amp": {
            "dir": ".agents/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "shai": {
            "dir": ".shai/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "bob": {
            "dir": ".bob/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        }
    }

    @staticmethod
    def parse_frontmatter(content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from Markdown content.

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        if not content.startswith("---"):
            return {}, content

        # Find second ---
        end_marker = content.find("---", 3)
        if end_marker == -1:
            return {}, content

        frontmatter_str = content[3:end_marker].strip()
        body = content[end_marker + 3:].strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError:
            frontmatter = {}

        return frontmatter, body

    @staticmethod
    def render_frontmatter(fm: dict) -> str:
        """Render frontmatter dictionary as YAML.

        Args:
            fm: Frontmatter dictionary

        Returns:
            YAML-formatted frontmatter with delimiters
        """
        if not fm:
            return ""

        yaml_str = yaml.dump(fm, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n"

    def _adjust_script_paths(self, frontmatter: dict) -> dict:
        """Adjust script paths from extension-relative to repo-relative.

        Args:
            frontmatter: Frontmatter dictionary

        Returns:
            Modified frontmatter with adjusted paths
        """
        if "scripts" in frontmatter:
            for key in frontmatter["scripts"]:
                script_path = frontmatter["scripts"][key]
                if script_path.startswith("../../scripts/"):
                    frontmatter["scripts"][key] = f".specify/scripts/{script_path[14:]}"
        return frontmatter

    def _render_markdown_command(
        self,
        frontmatter: dict,
        body: str,
        ext_id: str
    ) -> str:
        """Render command in Markdown format.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            ext_id: Extension ID

        Returns:
            Formatted Markdown command file content
        """
        context_note = f"\n<!-- Extension: {ext_id} -->\n<!-- Config: .specify/extensions/{ext_id}/ -->\n"
        return self.render_frontmatter(frontmatter) + "\n" + context_note + body

    def _render_toml_command(
        self,
        frontmatter: dict,
        body: str,
        ext_id: str
    ) -> str:
        """Render command in TOML format.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            ext_id: Extension ID

        Returns:
            Formatted TOML command file content
        """
        # TOML format for Gemini/Qwen
        toml_lines = []

        # Add description if present
        if "description" in frontmatter:
            # Escape quotes in description
            desc = frontmatter["description"].replace('"', '\\"')
            toml_lines.append(f'description = "{desc}"')
            toml_lines.append("")

        # Add extension context as comments
        toml_lines.append(f"# Extension: {ext_id}")
        toml_lines.append(f"# Config: .specify/extensions/{ext_id}/")
        toml_lines.append("")

        # Add prompt content
        toml_lines.append('prompt = """')
        toml_lines.append(body)
        toml_lines.append('"""')

        return "\n".join(toml_lines)

    def _convert_argument_placeholder(self, content: str, from_placeholder: str, to_placeholder: str) -> str:
        """Convert argument placeholder format.

        Args:
            content: Command content
            from_placeholder: Source placeholder (e.g., "$ARGUMENTS")
            to_placeholder: Target placeholder (e.g., "{{args}}")

        Returns:
            Content with converted placeholders
        """
        return content.replace(from_placeholder, to_placeholder)

    def register_commands_for_agent(
        self,
        agent_name: str,
        manifest: ExtensionManifest,
        extension_dir: Path,
        project_root: Path
    ) -> List[str]:
        """Register extension commands for a specific agent.

        Args:
            agent_name: Agent name (claude, gemini, copilot, etc.)
            manifest: Extension manifest
            extension_dir: Path to extension directory
            project_root: Path to project root

        Returns:
            List of registered command names

        Raises:
            ExtensionError: If agent is not supported
        """
        if agent_name not in self.AGENT_CONFIGS:
            raise ExtensionError(f"Unsupported agent: {agent_name}")

        agent_config = self.AGENT_CONFIGS[agent_name]
        commands_dir = project_root / agent_config["dir"]
        commands_dir.mkdir(parents=True, exist_ok=True)

        registered = []

        for cmd_info in manifest.commands:
            cmd_name = cmd_info["name"]
            cmd_file = cmd_info["file"]

            # Read source command file
            source_file = extension_dir / cmd_file
            if not source_file.exists():
                continue

            content = source_file.read_text()
            frontmatter, body = self.parse_frontmatter(content)

            # Adjust script paths
            frontmatter = self._adjust_script_paths(frontmatter)

            # Convert argument placeholders
            body = self._convert_argument_placeholder(
                body, "$ARGUMENTS", agent_config["args"]
            )

            # Render in agent-specific format
            if agent_config["format"] == "markdown":
                output = self._render_markdown_command(frontmatter, body, manifest.id)
            elif agent_config["format"] == "toml":
                output = self._render_toml_command(frontmatter, body, manifest.id)
            else:
                raise ExtensionError(f"Unsupported format: {agent_config['format']}")

            # Write command file
            dest_file = commands_dir / f"{cmd_name}{agent_config['extension']}"
            dest_file.write_text(output)

            registered.append(cmd_name)

            # Register aliases
            for alias in cmd_info.get("aliases", []):
                alias_file = commands_dir / f"{alias}{agent_config['extension']}"
                alias_file.write_text(output)
                registered.append(alias)

        return registered

    def register_commands_for_all_agents(
        self,
        manifest: ExtensionManifest,
        extension_dir: Path,
        project_root: Path
    ) -> Dict[str, List[str]]:
        """Register extension commands for all detected agents.

        Args:
            manifest: Extension manifest
            extension_dir: Path to extension directory
            project_root: Path to project root

        Returns:
            Dictionary mapping agent names to list of registered commands
        """
        results = {}

        # Detect which agents are present in the project
        for agent_name, agent_config in self.AGENT_CONFIGS.items():
            agent_dir = project_root / agent_config["dir"].split("/")[0]

            # Register if agent directory exists
            if agent_dir.exists():
                try:
                    registered = self.register_commands_for_agent(
                        agent_name, manifest, extension_dir, project_root
                    )
                    if registered:
                        results[agent_name] = registered
                except ExtensionError:
                    # Skip agent on error
                    continue

        return results

    def register_commands_for_claude(
        self,
        manifest: ExtensionManifest,
        extension_dir: Path,
        project_root: Path
    ) -> List[str]:
        """Register extension commands for Claude Code agent.

        Args:
            manifest: Extension manifest
            extension_dir: Path to extension directory
            project_root: Path to project root

        Returns:
            List of registered command names
        """
        return self.register_commands_for_agent("claude", manifest, extension_dir, project_root)


class ExtensionCatalog:
    """Manages extension catalog fetching, caching, and searching."""

    DEFAULT_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.json"
    CACHE_DURATION = 3600  # 1 hour in seconds

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

    def get_catalog_url(self) -> str:
        """Get catalog URL from config or use default.

        Checks in order:
        1. SPECKIT_CATALOG_URL environment variable
        2. Default catalog URL

        Returns:
            URL to fetch catalog from

        Raises:
            ValidationError: If custom URL is invalid (non-HTTPS)
        """
        import os
        import sys
        from urllib.parse import urlparse

        # Environment variable override (useful for testing)
        if env_value := os.environ.get("SPECKIT_CATALOG_URL"):
            catalog_url = env_value.strip()
            parsed = urlparse(catalog_url)

            # Require HTTPS for security (prevent man-in-the-middle attacks)
            # Allow http://localhost for local development/testing
            is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
                raise ValidationError(
                    f"Invalid SPECKIT_CATALOG_URL: must use HTTPS (got {parsed.scheme}://). "
                    "HTTP is only allowed for localhost."
                )

            if not parsed.netloc:
                raise ValidationError(
                    "Invalid SPECKIT_CATALOG_URL: must be a valid URL with a host."
                )

            # Warn users when using a non-default catalog (once per instance)
            if catalog_url != self.DEFAULT_CATALOG_URL:
                if not getattr(self, "_non_default_catalog_warning_shown", False):
                    print(
                        "Warning: Using non-default extension catalog. "
                        "Only use catalogs from sources you trust.",
                        file=sys.stderr,
                    )
                    self._non_default_catalog_warning_shown = True

            return catalog_url

        # TODO: Support custom catalogs from .specify/extension-catalogs.yml
        return self.DEFAULT_CATALOG_URL

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
            age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
            return age_seconds < self.CACHE_DURATION
        except (json.JSONDecodeError, ValueError, KeyError):
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
        # Check cache first unless force refresh
        if not force_refresh and self.is_cache_valid():
            try:
                return json.loads(self.cache_file.read_text())
            except json.JSONDecodeError:
                pass  # Fall through to network fetch

        # Fetch from network
        catalog_url = self.get_catalog_url()

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            # Validate catalog structure
            if "schema_version" not in catalog_data or "extensions" not in catalog_data:
                raise ExtensionError("Invalid catalog format")

            # Save to cache
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(catalog_data, indent=2))

            # Save cache metadata
            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "catalog_url": catalog_url,
            }
            self.cache_metadata_file.write_text(json.dumps(metadata, indent=2))

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
        """Search catalog for extensions.

        Args:
            query: Search query (searches name, description, tags)
            tag: Filter by specific tag
            author: Filter by author name
            verified_only: If True, show only verified extensions

        Returns:
            List of matching extension metadata
        """
        catalog = self.fetch_catalog()
        extensions = catalog.get("extensions", {})

        results = []

        for ext_id, ext_data in extensions.items():
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

            results.append({"id": ext_id, **ext_data})

        return results

    def get_extension_info(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific extension.

        Args:
            extension_id: ID of the extension

        Returns:
            Extension metadata or None if not found
        """
        catalog = self.fetch_catalog()
        extensions = catalog.get("extensions", {})

        if extension_id in extensions:
            return {"id": extension_id, **extensions[extension_id]}

        return None

    def download_extension(self, extension_id: str, target_dir: Optional[Path] = None) -> Path:
        """Download extension ZIP from catalog.

        Args:
            extension_id: ID of the extension to download
            target_dir: Directory to save ZIP file (defaults to temp directory)

        Returns:
            Path to downloaded ZIP file

        Raises:
            ExtensionError: If extension not found or download fails
        """
        import urllib.request
        import urllib.error

        # Get extension info from catalog
        ext_info = self.get_extension_info(extension_id)
        if not ext_info:
            raise ExtensionError(f"Extension '{extension_id}' not found in catalog")

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

        # Download the ZIP file
        try:
            with urllib.request.urlopen(download_url, timeout=60) as response:
                zip_data = response.read()

            zip_path.write_bytes(zip_data)
            return zip_path

        except urllib.error.URLError as e:
            raise ExtensionError(f"Failed to download extension from {download_url}: {e}")
        except IOError as e:
            raise ExtensionError(f"Failed to save extension ZIP: {e}")

    def clear_cache(self):
        """Clear the catalog cache."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        if self.cache_metadata_file.exists():
            self.cache_metadata_file.unlink()


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
            return yaml.safe_load(file_path.read_text()) or {}
        except (yaml.YAMLError, OSError):
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
            config_path = key[len(prefix):].lower().split("_")

            # Build nested dict
            current = env_config
            for part in config_path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the final value
            current[config_path[-1]] = value

        return env_config

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Configuration to merge on top

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
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
            return yaml.safe_load(self.config_file.read_text()) or {}
        except (yaml.YAMLError, OSError):
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
            yaml.dump(config, default_flow_style=False, sort_keys=False)
        )

    def register_hooks(self, manifest: ExtensionManifest):
        """Register extension hooks in project config.

        Args:
            manifest: Extension manifest with hooks to register
        """
        if not hasattr(manifest, "hooks") or not manifest.hooks:
            return

        config = self.get_project_config()

        # Ensure hooks dict exists
        if "hooks" not in config:
            config["hooks"] = {}

        # Register each hook
        for hook_name, hook_config in manifest.hooks.items():
            if hook_name not in config["hooks"]:
                config["hooks"][hook_name] = []

            # Add hook entry
            hook_entry = {
                "extension": manifest.id,
                "command": hook_config.get("command"),
                "enabled": True,
                "optional": hook_config.get("optional", True),
                "prompt": hook_config.get(
                    "prompt", f"Execute {hook_config.get('command')}?"
                ),
                "description": hook_config.get("description", ""),
                "condition": hook_config.get("condition"),
            }

            # Check if already registered
            existing = [
                h
                for h in config["hooks"][hook_name]
                if h.get("extension") == manifest.id
            ]

            if not existing:
                config["hooks"][hook_name].append(hook_entry)
            else:
                # Update existing
                for i, h in enumerate(config["hooks"][hook_name]):
                    if h.get("extension") == manifest.id:
                        config["hooks"][hook_name][i] = hook_entry

        self.save_project_config(config)

    def unregister_hooks(self, extension_id: str):
        """Remove extension hooks from project config.

        Args:
            extension_id: ID of extension to unregister
        """
        config = self.get_project_config()

        if "hooks" not in config:
            return

        # Remove hooks for this extension
        for hook_name in config["hooks"]:
            config["hooks"][hook_name] = [
                h
                for h in config["hooks"][hook_name]
                if h.get("extension") != extension_id
            ]

        # Clean up empty hook arrays
        config["hooks"] = {
            name: hooks for name, hooks in config["hooks"].items() if hooks
        }

        self.save_project_config(config)

    def get_hooks_for_event(self, event_name: str) -> List[Dict[str, Any]]:
        """Get all registered hooks for a specific event.

        Args:
            event_name: Name of the event (e.g., 'after_tasks')

        Returns:
            List of hook configurations
        """
        config = self.get_project_config()
        hooks = config.get("hooks", {}).get(event_name, [])

        # Filter to enabled hooks only
        return [h for h in hooks if h.get("enabled", True)]

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
        if match := re.match(r'config\.([a-z0-9_.]+)\s+is\s+set', condition, re.IGNORECASE):
            key_path = match.group(1)
            if not extension_id:
                return False

            config_manager = ConfigManager(self.project_root, extension_id)
            return config_manager.has_value(key_path)

        # Pattern: "config.key.path == 'value'" or "config.key.path != 'value'"
        if match := re.match(r'config\.([a-z0-9_.]+)\s*(==|!=)\s*["\']([^"\']+)["\']', condition, re.IGNORECASE):
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
        if match := re.match(r'env\.([A-Z0-9_]+)\s+is\s+set', condition, re.IGNORECASE):
            var_name = match.group(1).upper()
            return var_name in os.environ

        # Pattern: "env.VAR_NAME == 'value'" or "env.VAR_NAME != 'value'"
        if match := re.match(r'env\.([A-Z0-9_]+)\s*(==|!=)\s*["\']([^"\']+)["\']', condition, re.IGNORECASE):
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

    def format_hook_message(
        self, event_name: str, hooks: List[Dict[str, Any]]
    ) -> str:
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
            optional = hook.get("optional", True)
            prompt = hook.get("prompt", "")
            description = hook.get("description", "")

            if optional:
                lines.append(f"\n**Optional Hook**: {extension}")
                lines.append(f"Command: `/{command}`")
                if description:
                    lines.append(f"Description: {description}")
                lines.append(f"\nPrompt: {prompt}")
                lines.append(f"To execute: `/{command}`")
            else:
                lines.append(f"\n**Automatic Hook**: {extension}")
                lines.append(f"Executing: `/{command}`")
                lines.append(f"EXECUTE_COMMAND: {command}")

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
            return {
                "has_hooks": False,
                "hooks": [],
                "message": ""
            }

        # Filter hooks by condition
        executable_hooks = []
        for hook in hooks:
            if self.should_execute_hook(hook):
                executable_hooks.append(hook)

        if not executable_hooks:
            return {
                "has_hooks": False,
                "hooks": [],
                "message": f"# No executable hooks for event '{event_name}' (conditions not met)"
            }

        return {
            "has_hooks": True,
            "hooks": executable_hooks,
            "message": self.format_hook_message(event_name, executable_hooks)
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
            "extension": hook.get("extension"),
            "optional": hook.get("optional", True),
            "description": hook.get("description", ""),
            "prompt": hook.get("prompt", "")
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


