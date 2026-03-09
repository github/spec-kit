"""
Template Pack Manager for Spec Kit

Handles installation, removal, and management of Spec Kit template packs.
Template packs are self-contained, versioned collections of templates
(artifact, command, and script templates) that can be installed to
customize the Spec-Driven Development workflow.
"""

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


class TemplateError(Exception):
    """Base exception for template-related errors."""
    pass


class TemplateValidationError(TemplateError):
    """Raised when template pack manifest validation fails."""
    pass


class TemplateCompatibilityError(TemplateError):
    """Raised when template pack is incompatible with current environment."""
    pass


VALID_TEMPLATE_TYPES = {"artifact", "command", "script"}


class TemplatePackManifest:
    """Represents and validates a template pack manifest (template-pack.yml)."""

    SCHEMA_VERSION = "1.0"
    REQUIRED_FIELDS = ["schema_version", "template_pack", "requires", "provides"]

    def __init__(self, manifest_path: Path):
        """Load and validate template pack manifest.

        Args:
            manifest_path: Path to template-pack.yml file

        Raises:
            TemplateValidationError: If manifest is invalid
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
            raise TemplateValidationError(f"Invalid YAML in {path}: {e}")
        except FileNotFoundError:
            raise TemplateValidationError(f"Manifest not found: {path}")

    def _validate(self):
        """Validate manifest structure and required fields."""
        # Check required top-level fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.data:
                raise TemplateValidationError(f"Missing required field: {field}")

        # Validate schema version
        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise TemplateValidationError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        # Validate template_pack metadata
        pack = self.data["template_pack"]
        for field in ["id", "name", "version", "description"]:
            if field not in pack:
                raise TemplateValidationError(f"Missing template_pack.{field}")

        # Validate pack ID format
        if not re.match(r'^[a-z0-9-]+$', pack["id"]):
            raise TemplateValidationError(
                f"Invalid template pack ID '{pack['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        # Validate semantic version
        try:
            pkg_version.Version(pack["version"])
        except pkg_version.InvalidVersion:
            raise TemplateValidationError(f"Invalid version: {pack['version']}")

        # Validate requires section
        requires = self.data["requires"]
        if "speckit_version" not in requires:
            raise TemplateValidationError("Missing requires.speckit_version")

        # Validate provides section
        provides = self.data["provides"]
        if "templates" not in provides or not provides["templates"]:
            raise TemplateValidationError(
                "Template pack must provide at least one template"
            )

        # Validate templates
        for tmpl in provides["templates"]:
            if "type" not in tmpl or "name" not in tmpl or "file" not in tmpl:
                raise TemplateValidationError(
                    "Template missing 'type', 'name', or 'file'"
                )

            if tmpl["type"] not in VALID_TEMPLATE_TYPES:
                raise TemplateValidationError(
                    f"Invalid template type '{tmpl['type']}': "
                    f"must be one of {sorted(VALID_TEMPLATE_TYPES)}"
                )

            # Validate template name format
            if not re.match(r'^[a-z0-9-]+$', tmpl["name"]):
                raise TemplateValidationError(
                    f"Invalid template name '{tmpl['name']}': "
                    "must be lowercase alphanumeric with hyphens only"
                )

    @property
    def id(self) -> str:
        """Get template pack ID."""
        return self.data["template_pack"]["id"]

    @property
    def name(self) -> str:
        """Get template pack name."""
        return self.data["template_pack"]["name"]

    @property
    def version(self) -> str:
        """Get template pack version."""
        return self.data["template_pack"]["version"]

    @property
    def description(self) -> str:
        """Get template pack description."""
        return self.data["template_pack"]["description"]

    @property
    def author(self) -> str:
        """Get template pack author."""
        return self.data["template_pack"].get("author", "")

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
        """Get template pack tags."""
        return self.data.get("tags", [])

    def get_hash(self) -> str:
        """Calculate SHA256 hash of manifest file."""
        with open(self.path, 'rb') as f:
            return f"sha256:{hashlib.sha256(f.read()).hexdigest()}"


class TemplatePackRegistry:
    """Manages the registry of installed template packs."""

    REGISTRY_FILE = ".registry"
    SCHEMA_VERSION = "1.0"

    def __init__(self, packs_dir: Path):
        """Initialize registry.

        Args:
            packs_dir: Path to .specify/templates/packs/ directory
        """
        self.packs_dir = packs_dir
        self.registry_path = packs_dir / self.REGISTRY_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return {
                "schema_version": self.SCHEMA_VERSION,
                "template_packs": {}
            }

        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "schema_version": self.SCHEMA_VERSION,
                "template_packs": {}
            }

    def _save(self):
        """Save registry to disk."""
        self.packs_dir.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add(self, pack_id: str, metadata: dict):
        """Add template pack to registry.

        Args:
            pack_id: Template pack ID
            metadata: Pack metadata (version, source, etc.)
        """
        self.data["template_packs"][pack_id] = {
            **metadata,
            "installed_at": datetime.now(timezone.utc).isoformat()
        }
        self._save()

    def remove(self, pack_id: str):
        """Remove template pack from registry.

        Args:
            pack_id: Template pack ID
        """
        if pack_id in self.data["template_packs"]:
            del self.data["template_packs"][pack_id]
            self._save()

    def get(self, pack_id: str) -> Optional[dict]:
        """Get template pack metadata from registry.

        Args:
            pack_id: Template pack ID

        Returns:
            Pack metadata or None if not found
        """
        return self.data["template_packs"].get(pack_id)

    def list(self) -> Dict[str, dict]:
        """Get all installed template packs.

        Returns:
            Dictionary of pack_id -> metadata
        """
        return self.data["template_packs"]

    def is_installed(self, pack_id: str) -> bool:
        """Check if template pack is installed.

        Args:
            pack_id: Template pack ID

        Returns:
            True if pack is installed
        """
        return pack_id in self.data["template_packs"]


class TemplatePackManager:
    """Manages template pack lifecycle: installation, removal, updates."""

    def __init__(self, project_root: Path):
        """Initialize template pack manager.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.templates_dir = project_root / ".specify" / "templates"
        self.packs_dir = self.templates_dir / "packs"
        self.registry = TemplatePackRegistry(self.packs_dir)

    def check_compatibility(
        self,
        manifest: TemplatePackManifest,
        speckit_version: str
    ) -> bool:
        """Check if template pack is compatible with current spec-kit version.

        Args:
            manifest: Template pack manifest
            speckit_version: Current spec-kit version

        Returns:
            True if compatible

        Raises:
            TemplateCompatibilityError: If pack is incompatible
        """
        required = manifest.requires_speckit_version
        current = pkg_version.Version(speckit_version)

        try:
            specifier = SpecifierSet(required)
            if current not in specifier:
                raise TemplateCompatibilityError(
                    f"Template pack requires spec-kit {required}, "
                    f"but {speckit_version} is installed.\n"
                    f"Upgrade spec-kit with: uv tool install specify-cli --force"
                )
        except InvalidSpecifier:
            raise TemplateCompatibilityError(
                f"Invalid version specifier: {required}"
            )

        return True

    def install_from_directory(
        self,
        source_dir: Path,
        speckit_version: str,
    ) -> TemplatePackManifest:
        """Install template pack from a local directory.

        Args:
            source_dir: Path to template pack directory
            speckit_version: Current spec-kit version

        Returns:
            Installed template pack manifest

        Raises:
            TemplateValidationError: If manifest is invalid
            TemplateCompatibilityError: If pack is incompatible
        """
        manifest_path = source_dir / "template-pack.yml"
        manifest = TemplatePackManifest(manifest_path)

        self.check_compatibility(manifest, speckit_version)

        if self.registry.is_installed(manifest.id):
            raise TemplateError(
                f"Template pack '{manifest.id}' is already installed. "
                f"Use 'specify template remove {manifest.id}' first."
            )

        dest_dir = self.packs_dir / manifest.id
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir)

        self.registry.add(manifest.id, {
            "version": manifest.version,
            "source": "local",
            "manifest_hash": manifest.get_hash(),
            "enabled": True,
        })

        return manifest

    def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str
    ) -> TemplatePackManifest:
        """Install template pack from ZIP file.

        Args:
            zip_path: Path to template pack ZIP file
            speckit_version: Current spec-kit version

        Returns:
            Installed template pack manifest

        Raises:
            TemplateValidationError: If manifest is invalid
            TemplateCompatibilityError: If pack is incompatible
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                temp_path_resolved = temp_path.resolve()
                for member in zf.namelist():
                    member_path = (temp_path / member).resolve()
                    try:
                        member_path.relative_to(temp_path_resolved)
                    except ValueError:
                        raise TemplateValidationError(
                            f"Unsafe path in ZIP archive: {member} "
                            "(potential path traversal)"
                        )
                zf.extractall(temp_path)

            pack_dir = temp_path
            manifest_path = pack_dir / "template-pack.yml"

            if not manifest_path.exists():
                subdirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    pack_dir = subdirs[0]
                    manifest_path = pack_dir / "template-pack.yml"

            if not manifest_path.exists():
                raise TemplateValidationError(
                    "No template-pack.yml found in ZIP file"
                )

            return self.install_from_directory(pack_dir, speckit_version)

    def remove(self, pack_id: str) -> bool:
        """Remove an installed template pack.

        Args:
            pack_id: Template pack ID

        Returns:
            True if pack was removed
        """
        if not self.registry.is_installed(pack_id):
            return False

        pack_dir = self.packs_dir / pack_id
        if pack_dir.exists():
            shutil.rmtree(pack_dir)

        self.registry.remove(pack_id)
        return True

    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed template packs with metadata.

        Returns:
            List of template pack metadata dictionaries
        """
        result = []

        for pack_id, metadata in self.registry.list().items():
            pack_dir = self.packs_dir / pack_id
            manifest_path = pack_dir / "template-pack.yml"

            try:
                manifest = TemplatePackManifest(manifest_path)
                result.append({
                    "id": pack_id,
                    "name": manifest.name,
                    "version": metadata["version"],
                    "description": manifest.description,
                    "enabled": metadata.get("enabled", True),
                    "installed_at": metadata.get("installed_at"),
                    "template_count": len(manifest.templates),
                    "tags": manifest.tags,
                })
            except TemplateValidationError:
                result.append({
                    "id": pack_id,
                    "name": pack_id,
                    "version": metadata.get("version", "unknown"),
                    "description": "⚠️ Corrupted template pack",
                    "enabled": False,
                    "installed_at": metadata.get("installed_at"),
                    "template_count": 0,
                    "tags": [],
                })

        return result

    def get_pack(self, pack_id: str) -> Optional[TemplatePackManifest]:
        """Get manifest for an installed template pack.

        Args:
            pack_id: Template pack ID

        Returns:
            Template pack manifest or None if not installed
        """
        if not self.registry.is_installed(pack_id):
            return None

        pack_dir = self.packs_dir / pack_id
        manifest_path = pack_dir / "template-pack.yml"

        try:
            return TemplatePackManifest(manifest_path)
        except TemplateValidationError:
            return None


class TemplateCatalog:
    """Manages template pack catalog fetching, caching, and searching."""

    DEFAULT_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/templates/catalog.json"
    COMMUNITY_CATALOG_URL = "https://raw.githubusercontent.com/github/spec-kit/main/templates/catalog.community.json"
    CACHE_DURATION = 3600  # 1 hour in seconds

    def __init__(self, project_root: Path):
        """Initialize template catalog manager.

        Args:
            project_root: Root directory of the spec-kit project
        """
        self.project_root = project_root
        self.templates_dir = project_root / ".specify" / "templates"
        self.cache_dir = self.templates_dir / "packs" / ".cache"
        self.cache_file = self.cache_dir / "catalog.json"
        self.cache_metadata_file = self.cache_dir / "catalog-metadata.json"

    def _validate_catalog_url(self, url: str) -> None:
        """Validate that a catalog URL uses HTTPS (localhost HTTP allowed).

        Args:
            url: URL to validate

        Raises:
            TemplateValidationError: If URL is invalid or uses non-HTTPS scheme
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise TemplateValidationError(
                f"Catalog URL must use HTTPS (got {parsed.scheme}://). "
                "HTTP is only allowed for localhost."
            )
        if not parsed.netloc:
            raise TemplateValidationError(
                "Catalog URL must be a valid URL with a host."
            )

    def get_catalog_url(self) -> str:
        """Get the primary catalog URL.

        Returns:
            URL of the primary catalog
        """
        env_value = os.environ.get("SPECKIT_TEMPLATE_CATALOG_URL")
        if env_value:
            catalog_url = env_value.strip()
            self._validate_catalog_url(catalog_url)
            return catalog_url
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
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age_seconds = (
                datetime.now(timezone.utc) - cached_at
            ).total_seconds()
            return age_seconds < self.CACHE_DURATION
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            return False

    def fetch_catalog(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch template pack catalog from URL or cache.

        Args:
            force_refresh: If True, bypass cache and fetch from network

        Returns:
            Catalog data dictionary

        Raises:
            TemplateError: If catalog cannot be fetched
        """
        if not force_refresh and self.is_cache_valid():
            try:
                return json.loads(self.cache_file.read_text())
            except json.JSONDecodeError:
                pass

        catalog_url = self.get_catalog_url()

        try:
            import urllib.request
            import urllib.error

            with urllib.request.urlopen(catalog_url, timeout=10) as response:
                catalog_data = json.loads(response.read())

            if (
                "schema_version" not in catalog_data
                or "template_packs" not in catalog_data
            ):
                raise TemplateError("Invalid template catalog format")

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
            if isinstance(e, TemplateError):
                raise
            raise TemplateError(
                f"Failed to fetch template catalog from {catalog_url}: {e}"
            )

    def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search catalog for template packs.

        Args:
            query: Search query (searches name, description, tags)
            tag: Filter by specific tag
            author: Filter by author name

        Returns:
            List of matching template pack metadata
        """
        try:
            catalog_data = self.fetch_catalog()
        except TemplateError:
            return []

        results = []
        packs = catalog_data.get("template_packs", {})

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
        """Get detailed information about a specific template pack.

        Args:
            pack_id: ID of the template pack

        Returns:
            Pack metadata or None if not found
        """
        try:
            catalog_data = self.fetch_catalog()
        except TemplateError:
            return None

        packs = catalog_data.get("template_packs", {})
        if pack_id in packs:
            return {**packs[pack_id], "id": pack_id}
        return None

    def download_pack(
        self, pack_id: str, target_dir: Optional[Path] = None
    ) -> Path:
        """Download template pack ZIP from catalog.

        Args:
            pack_id: ID of the template pack to download
            target_dir: Directory to save ZIP file (defaults to cache directory)

        Returns:
            Path to downloaded ZIP file

        Raises:
            TemplateError: If pack not found or download fails
        """
        import urllib.request
        import urllib.error

        pack_info = self.get_pack_info(pack_id)
        if not pack_info:
            raise TemplateError(
                f"Template pack '{pack_id}' not found in catalog"
            )

        download_url = pack_info.get("download_url")
        if not download_url:
            raise TemplateError(
                f"Template pack '{pack_id}' has no download URL"
            )

        from urllib.parse import urlparse

        parsed = urlparse(download_url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise TemplateError(
                f"Template pack download URL must use HTTPS: {download_url}"
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
            raise TemplateError(
                f"Failed to download template pack from {download_url}: {e}"
            )
        except IOError as e:
            raise TemplateError(f"Failed to save template pack ZIP: {e}")

    def clear_cache(self):
        """Clear the catalog cache."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        if self.cache_metadata_file.exists():
            self.cache_metadata_file.unlink()


class TemplateResolver:
    """Resolves template names to file paths using a priority stack.

    Resolution order:
    1. .specify/templates/overrides/          - Project-local overrides
    2. .specify/templates/packs/<pack-id>/    - Installed template packs
    3. .specify/extensions/<ext-id>/templates/ - Extension-provided templates
    4. .specify/templates/                    - Core templates (shipped with Spec Kit)
    """

    def __init__(self, project_root: Path):
        """Initialize template resolver.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.templates_dir = project_root / ".specify" / "templates"
        self.packs_dir = self.templates_dir / "packs"
        self.overrides_dir = self.templates_dir / "overrides"
        self.extensions_dir = project_root / ".specify" / "extensions"

    def resolve(
        self,
        template_name: str,
        template_type: str = "artifact",
    ) -> Optional[Path]:
        """Resolve a template name to its file path.

        Walks the priority stack and returns the first match.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("artifact", "command", or "script")

        Returns:
            Path to the resolved template file, or None if not found
        """
        # Determine subdirectory based on template type
        if template_type == "artifact":
            subdirs = ["templates", ""]
        elif template_type == "command":
            subdirs = ["commands"]
        elif template_type == "script":
            subdirs = ["scripts"]
        else:
            subdirs = [""]

        # Priority 1: Project-local overrides
        for subdir in subdirs:
            if template_type == "script":
                override = self.overrides_dir / "scripts" / f"{template_name}.sh"
            elif subdir:
                override = self.overrides_dir / f"{template_name}.md"
            else:
                override = self.overrides_dir / f"{template_name}.md"
            if override.exists():
                return override

        # Priority 2: Installed packs (by registry order)
        if self.packs_dir.exists():
            registry = TemplatePackRegistry(self.packs_dir)
            for pack_id in registry.list():
                pack_dir = self.packs_dir / pack_id
                for subdir in subdirs:
                    if subdir:
                        candidate = (
                            pack_dir / subdir / f"{template_name}.md"
                        )
                    else:
                        candidate = pack_dir / f"{template_name}.md"
                    if candidate.exists():
                        return candidate

        # Priority 3: Extension-provided templates
        if self.extensions_dir.exists():
            for ext_dir in sorted(self.extensions_dir.iterdir()):
                if not ext_dir.is_dir() or ext_dir.name.startswith("."):
                    continue
                for subdir in subdirs:
                    if subdir:
                        candidate = (
                            ext_dir / "templates" / f"{template_name}.md"
                        )
                    else:
                        candidate = (
                            ext_dir / "templates" / f"{template_name}.md"
                        )
                    if candidate.exists():
                        return candidate

        # Priority 4: Core templates
        if template_type == "artifact":
            core = self.templates_dir / f"{template_name}.md"
            if core.exists():
                return core
        elif template_type == "command":
            core = self.templates_dir / "commands" / f"{template_name}.md"
            if core.exists():
                return core

        return None

    def resolve_with_source(
        self,
        template_name: str,
        template_type: str = "artifact",
    ) -> Optional[Dict[str, str]]:
        """Resolve a template name and return source attribution.

        Args:
            template_name: Template name (e.g., "spec-template")
            template_type: Template type ("artifact", "command", or "script")

        Returns:
            Dictionary with 'path' and 'source' keys, or None if not found
        """
        # Priority 1: Project-local overrides
        override = self.overrides_dir / f"{template_name}.md"
        if override.exists():
            return {"path": str(override), "source": "project override"}

        # Priority 2: Installed packs
        if self.packs_dir.exists():
            registry = TemplatePackRegistry(self.packs_dir)
            for pack_id in registry.list():
                pack_dir = self.packs_dir / pack_id
                # Check templates/ subdirectory first, then root
                for subdir in ["templates", "commands", "scripts", ""]:
                    if subdir:
                        candidate = (
                            pack_dir / subdir / f"{template_name}.md"
                        )
                    else:
                        candidate = pack_dir / f"{template_name}.md"
                    if candidate.exists():
                        meta = registry.get(pack_id)
                        version = meta.get("version", "?") if meta else "?"
                        return {
                            "path": str(candidate),
                            "source": f"{pack_id} v{version}",
                        }

        # Priority 3: Extension-provided templates
        if self.extensions_dir.exists():
            for ext_dir in sorted(self.extensions_dir.iterdir()):
                if not ext_dir.is_dir() or ext_dir.name.startswith("."):
                    continue
                candidate = ext_dir / "templates" / f"{template_name}.md"
                if candidate.exists():
                    return {
                        "path": str(candidate),
                        "source": f"extension:{ext_dir.name}",
                    }

        # Priority 4: Core templates
        core = self.templates_dir / f"{template_name}.md"
        if core.exists():
            return {"path": str(core), "source": "core"}

        # Also check commands subdirectory for core
        core_cmd = self.templates_dir / "commands" / f"{template_name}.md"
        if core_cmd.exists():
            return {"path": str(core_cmd), "source": "core"}

        return None
