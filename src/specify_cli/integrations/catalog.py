"""Integration catalog — discovery, validation, and upgrade support.

Provides:
- ``IntegrationCatalogEntry`` — single catalog source metadata.
- ``IntegrationCatalog``      — fetches, caches, and searches integration
  catalogs (built-in + community).
- ``IntegrationDescriptor``   — loads and validates ``integration.yml``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from packaging import version as pkg_version

from .._download_security import read_response_limited
from ..catalogs import CatalogEntry, CatalogStackBase


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class IntegrationCatalogError(Exception):
    """Raised when a catalog operation fails."""


class IntegrationValidationError(IntegrationCatalogError):
    """Validation error for catalog config or catalog management operations."""


class IntegrationDescriptorError(Exception):
    """Raised when an integration.yml descriptor is invalid."""


# ---------------------------------------------------------------------------
# IntegrationCatalogEntry
# ---------------------------------------------------------------------------

@dataclass
class IntegrationCatalogEntry(CatalogEntry):
    """Represents a single catalog source in the catalog stack."""


# ---------------------------------------------------------------------------
# IntegrationCatalog
# ---------------------------------------------------------------------------

class IntegrationCatalog(CatalogStackBase):
    """Manages integration catalog fetching, caching, and searching."""

    DEFAULT_CATALOG_URL = (
        "https://raw.githubusercontent.com/github/spec-kit/main/integrations/catalog.json"
    )
    COMMUNITY_CATALOG_URL = (
        "https://raw.githubusercontent.com/github/spec-kit/main/integrations/catalog.community.json"
    )
    CACHE_DURATION = 3600  # 1 hour
    CONFIG_FILENAME = "integration-catalogs.yml"
    ENTRY_CLASS = IntegrationCatalogEntry
    ERROR_TYPE = IntegrationCatalogError
    VALIDATION_ERROR_TYPE = IntegrationValidationError

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.cache_dir = project_root / ".specify" / "integrations" / ".cache"

    def get_active_catalogs(self) -> List[IntegrationCatalogEntry]:
        """Return the ordered list of active integration catalogs.

        Resolution:
        1. ``SPECKIT_INTEGRATION_CATALOG_URL`` env var
        2. Project ``.specify/integration-catalogs.yml``
        3. User ``~/.specify/integration-catalogs.yml``
        4. Built-in defaults (built-in + community)
        """
        import sys

        env_value = os.environ.get("SPECKIT_INTEGRATION_CATALOG_URL", "").strip()
        if env_value:
            self._validate_catalog_url(env_value)
            if env_value != self.DEFAULT_CATALOG_URL:
                if not getattr(self, "_non_default_catalog_warning_shown", False):
                    print(
                        "Warning: Using non-default integration catalog. "
                        "Only use catalogs from sources you trust.",
                        file=sys.stderr,
                    )
                    self._non_default_catalog_warning_shown = True
            return [
                IntegrationCatalogEntry(
                    url=env_value,
                    name="custom",
                    priority=1,
                    install_allowed=True,
                    description="Custom catalog via SPECKIT_INTEGRATION_CATALOG_URL",
                )
            ]

        project_cfg = self.project_root / ".specify" / self.CONFIG_FILENAME
        catalogs = self._load_catalog_config(project_cfg)
        if catalogs is not None:
            return catalogs

        user_cfg = Path.home() / ".specify" / self.CONFIG_FILENAME
        catalogs = self._load_catalog_config(user_cfg)
        if catalogs is not None:
            return catalogs

        return [
            IntegrationCatalogEntry(
                url=self.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
                description="Built-in catalog of installable integrations",
            ),
            IntegrationCatalogEntry(
                url=self.COMMUNITY_CATALOG_URL,
                name="community",
                priority=2,
                install_allowed=False,
                description="Community-contributed integrations (discovery only)",
            ),
        ]

    # -- Fetching ---------------------------------------------------------

    def _fetch_single_catalog(
        self,
        entry: IntegrationCatalogEntry,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Fetch one catalog, with per-URL caching."""
        import urllib.error

        url_hash = hashlib.sha256(entry.url.encode()).hexdigest()[:16]
        cache_file = self.cache_dir / f"catalog-{url_hash}.json"
        cache_meta = self.cache_dir / f"catalog-{url_hash}-metadata.json"

        if not force_refresh and cache_file.exists() and cache_meta.exists():
            try:
                meta = json.loads(cache_meta.read_text(encoding="utf-8"))
                cached_at = datetime.fromisoformat(meta.get("cached_at", ""))
                if cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if age < self.CACHE_DURATION:
                    return json.loads(cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError, OSError, UnicodeError):
                # Cache is invalid or stale metadata; delete and refetch from source.
                try:
                    cache_file.unlink(missing_ok=True)
                    cache_meta.unlink(missing_ok=True)
                except OSError:
                    pass  # Cache cleanup is best-effort; ignore deletion failures.

        try:
            from specify_cli.authentication.http import open_url

            with open_url(entry.url, timeout=10, strict_redirects=True) as resp:
                # Validate final URL after redirects
                final_url = resp.geturl()
                if final_url != entry.url:
                    self._validate_catalog_url(final_url)
                catalog_data = json.loads(
                    read_response_limited(
                        resp,
                        error_type=IntegrationCatalogError,
                        label=f"integration catalog {entry.url}",
                    )
                )

            if not isinstance(catalog_data, dict):
                raise IntegrationCatalogError(
                    f"Invalid catalog format from {entry.url}: expected a JSON object"
                )
            if (
                "schema_version" not in catalog_data
                or "integrations" not in catalog_data
            ):
                raise IntegrationCatalogError(
                    f"Invalid catalog format from {entry.url}"
                )
            if not isinstance(catalog_data.get("integrations"), dict):
                raise IntegrationCatalogError(
                    f"Invalid catalog format from {entry.url}: 'integrations' must be a JSON object"
                )

            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")
                cache_meta.write_text(
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

        except urllib.error.URLError as exc:
            raise IntegrationCatalogError(
                f"Failed to fetch catalog from {entry.url}: {exc}"
            )
        except json.JSONDecodeError as exc:
            raise IntegrationCatalogError(
                f"Invalid JSON in catalog from {entry.url}: {exc}"
            )

    def _get_merged_integrations(
        self, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch and merge integrations from all active catalogs.

        Catalogs are processed in the order returned by
        :meth:`get_active_catalogs`.  On conflicts, the first catalog in that
        order wins (lower numeric priority = higher precedence).  Each dict is
        annotated with ``_catalog_name`` and ``_install_allowed``.
        """
        import sys

        active = self.get_active_catalogs()
        merged: Dict[str, Dict[str, Any]] = {}
        any_success = False

        for entry in active:
            try:
                data = self._fetch_single_catalog(entry, force_refresh)
                any_success = True
            except IntegrationCatalogError as exc:
                print(
                    f"Warning: Could not fetch catalog '{entry.name}': {exc}",
                    file=sys.stderr,
                )
                continue

            for integ_id, integ_data in data.get("integrations", {}).items():
                if not isinstance(integ_data, dict):
                    continue
                if integ_id not in merged:
                    merged[integ_id] = {
                        **integ_data,
                        "id": integ_id,
                        "_catalog_name": entry.name,
                        "_install_allowed": entry.install_allowed,
                    }

        if not any_success and active:
            raise IntegrationCatalogError(
                "Failed to fetch any integration catalog"
            )

        return list(merged.values())

    # -- Search / info ----------------------------------------------------

    def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search catalogs for integrations matching the given filters."""
        results: List[Dict[str, Any]] = []
        for item in self._get_merged_integrations():
            author_val = item.get("author", "")
            if not isinstance(author_val, str):
                author_val = str(author_val) if author_val is not None else ""
            if author and author_val.lower() != author.lower():
                continue
            if tag:
                raw_tags = item.get("tags", [])
                tags_list = raw_tags if isinstance(raw_tags, list) else []
                if tag.lower() not in [t.lower() for t in tags_list if isinstance(t, str)]:
                    continue
            if query:
                raw_tags = item.get("tags", [])
                tags_list = raw_tags if isinstance(raw_tags, list) else []
                name_val = item.get("name", "")
                desc_val = item.get("description", "")
                id_val = item.get("id", "")
                haystack = " ".join(
                    [
                        str(name_val) if name_val else "",
                        str(desc_val) if desc_val else "",
                        str(id_val) if id_val else "",
                    ]
                    + [t for t in tags_list if isinstance(t, str)]
                ).lower()
                if query.lower() not in haystack:
                    continue
            results.append(item)
        return results

    def get_integration_info(
        self, integration_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return catalog metadata for a single integration, or None."""
        for item in self._get_merged_integrations():
            if item["id"] == integration_id:
                return item
        return None

    # -- Cache management -------------------------------------------------

    def clear_cache(self) -> None:
        """Remove all cached catalog files."""
        if self.cache_dir.exists():
            for pattern in ("catalog-*.json", "catalog-*-metadata.json"):
                for f in self.cache_dir.glob(pattern):
                    f.unlink(missing_ok=True)

    # -- Catalog-source management ----------------------------------------

    def get_catalog_configs(self) -> List[Dict[str, Any]]:
        """Return the active catalog stack as a list of dicts.

        Thin adapter over :meth:`get_active_catalogs` that yields plain dicts
        suitable for CLI rendering and JSON-like consumers.
        """
        return [
            {
                "name": e.name,
                "url": e.url,
                "priority": e.priority,
                "install_allowed": e.install_allowed,
                "description": e.description,
            }
            for e in self.get_active_catalogs()
        ]

    def get_project_catalog_configs(self) -> Optional[List[Dict[str, Any]]]:
        """Return removable project-level catalog config entries, if configured."""
        config_path = self.project_root / ".specify" / self.CONFIG_FILENAME
        entries = self._load_catalog_config(config_path)
        if entries is None:
            return None
        return [
            {
                "name": e.name,
                "url": e.url,
                "priority": e.priority,
                "install_allowed": e.install_allowed,
                "description": e.description,
            }
            for e in entries
        ]

    def add_catalog(self, url: str, name: Optional[str] = None) -> None:
        """Add a catalog source to the project-level config file.

        The URL is normalized (whitespace stripped) and validated before being
        written. Duplicate URLs are rejected, including near-duplicates that
        differ only by surrounding whitespace. Priority is derived as
        ``max(existing) + 1`` so the new entry sorts last in the resolution
        order unless the user edits the file manually.
        """
        url = url.strip()
        if not url:
            raise IntegrationValidationError("Catalog URL must be non-empty.")
        self._validate_catalog_url(url)
        config_path = self.project_root / ".specify" / self.CONFIG_FILENAME

        data: Dict[str, Any] = {"catalogs": []}
        if config_path.exists():
            try:
                raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            except (yaml.YAMLError, OSError, UnicodeError) as exc:
                raise IntegrationValidationError(
                    f"Failed to read catalog config {config_path}: {exc}"
                ) from exc
            if raw is None:
                raw = {}
            if not isinstance(raw, dict):
                raise IntegrationValidationError(
                    f"Catalog config file {config_path} is corrupted "
                    "(expected a mapping)."
                )
            data = raw

        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list):
            raise IntegrationValidationError(
                f"Catalog config {config_path} has invalid 'catalogs' value: "
                "must be a list."
            )

        # Validate each existing entry before mutating anything. Fail fast so
        # we don't silently preserve a corrupt sibling entry or derive a new
        # priority from a bogus value.
        existing_priorities: List[int] = []
        valid_catalog_count = 0
        for idx, cat in enumerate(catalogs):
            if not isinstance(cat, dict):
                raise IntegrationValidationError(
                    f"Invalid catalog entry at index {idx} in {config_path}: "
                    f"expected a mapping, got {type(cat).__name__}."
                )
            existing_url = str(cat.get("url", "")).strip()
            if not existing_url:
                continue
            # Re-run the same URL validation used when loading, so a corrupt
            # entry surfaces here instead of at the next `integration` call.
            try:
                self._validate_catalog_url(existing_url)
            except IntegrationCatalogError as exc:
                raise IntegrationValidationError(
                    f"Invalid catalog entry at index {idx} in {config_path}: {exc}"
                ) from exc
            if existing_url == url:
                raise IntegrationValidationError(
                    f"Catalog URL already configured: {url}"
                )
            valid_catalog_count += 1
            if "priority" in cat:
                raw_priority = cat.get("priority")
                if isinstance(raw_priority, bool):
                    raise IntegrationValidationError(
                        f"Invalid catalog entry at index {idx} in {config_path}: "
                        f"'priority' must be an integer, got "
                        f"{type(raw_priority).__name__}."
                    )
                try:
                    normalized_priority = int(raw_priority)
                except (TypeError, ValueError):
                    raise IntegrationValidationError(
                        f"Invalid catalog entry at index {idx} in {config_path}: "
                        f"'priority' must be an integer, got "
                        f"{raw_priority!r}."
                    ) from None
                existing_priorities.append(normalized_priority)
            else:
                # Match `_load_catalog_config()`'s defaulting rule so the new
                # entry still sorts after implicit-priority siblings.
                existing_priorities.append(idx + 1)

        max_priority = max(existing_priorities, default=0)
        normalized_name = str(name).strip() if name is not None else ""
        generated_name = f"catalog-{valid_catalog_count + 1}"
        catalogs.append(
            {
                "name": normalized_name or generated_name,
                "url": url,
                "priority": max_priority + 1,
                "install_allowed": True,
                "description": "",
            }
        )
        data["catalogs"] = catalogs

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def remove_catalog(self, index: int) -> str:
        """Remove a catalog source by 0-based index.

        ``index`` is interpreted in the same display order shown by
        ``integration catalog list`` (i.e. sorted ascending by priority,
        with missing priority defaulting to ``yaml_index + 1``, matching
        ``_load_catalog_config()``). This way, the index a user sees in
        ``catalog list`` is the index they pass to ``catalog remove``,
        even if the underlying YAML lists entries in a different order
        from how they sort by priority.

        Returns the removed catalog's name.
        """
        config_path = self.project_root / ".specify" / self.CONFIG_FILENAME
        if not config_path.exists():
            raise IntegrationValidationError("No catalog config file found.")

        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeError) as exc:
            raise IntegrationValidationError(
                f"Failed to read catalog config {config_path}: {exc}"
            ) from exc
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise IntegrationValidationError(
                f"Catalog config file {config_path} is corrupted "
                "(expected a mapping)."
            )

        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list):
            raise IntegrationValidationError(
                f"Catalog config {config_path} has invalid 'catalogs' value: "
                "must be a list."
            )

        if not catalogs:
            # An empty list is the kind of state that only happens if the
            # user hand-edited the file; our own `remove_catalog` deletes
            # the file when the last entry is popped. Surface a clear
            # message instead of `out of range (0--1)`.
            raise IntegrationValidationError(
                "Catalog config contains no catalog entries."
            )

        # Map displayed index -> raw YAML index using the same priority
        # defaulting as ``_load_catalog_config``. We deliberately stay
        # tolerant here (no new validation errors) because the goal is
        # only to mirror the order shown by ``catalog list``; entries
        # that ``_load_catalog_config`` would have rejected outright
        # would have failed ``catalog list`` already.
        def _is_removable_catalog_entry(item: Any) -> bool:
            if not isinstance(item, dict):
                return False
            raw_url = item.get("url")
            if raw_url is None:
                return False
            return bool(str(raw_url).strip())

        priority_pairs: List[Tuple[int, int]] = []
        for yaml_idx, item in enumerate(catalogs):
            if not _is_removable_catalog_entry(item):
                continue

            raw_priority = item.get("priority", yaml_idx + 1)
            if isinstance(raw_priority, bool):
                priority = yaml_idx + 1
            else:
                try:
                    priority = int(raw_priority)
                except (TypeError, ValueError):
                    priority = yaml_idx + 1
            priority_pairs.append((priority, yaml_idx))
        if not priority_pairs:
            raise IntegrationValidationError(
                "Catalog config contains no removable catalog entries."
            )
        # Stable sort: ties keep their YAML order, matching list-view ordering.
        priority_pairs.sort(key=lambda p: p[0])
        display_order: List[int] = [yaml_idx for _, yaml_idx in priority_pairs]

        if index < 0 or index >= len(display_order):
            raise IntegrationValidationError(
                f"Catalog index {index} out of range (0-{len(display_order) - 1})."
            )

        target_yaml_idx = display_order[index]
        removed = catalogs.pop(target_yaml_idx)

        if any(_is_removable_catalog_entry(item) for item in catalogs):
            data["catalogs"] = catalogs
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
        else:
            # Removing the final entry: delete the config file rather than
            # leaving behind an empty `catalogs:` list. `_load_catalog_config`
            # treats an empty list as an error, so leaving the file would
            # break every subsequent `integration` command until the user
            # manually deletes `.specify/integration-catalogs.yml`.
            # Deleting the file lets the project fall back to built-in
            # defaults, which matches the behavior before any
            # `catalog add` was ever run.
            try:
                config_path.unlink(missing_ok=True)
            except OSError as exc:
                raise IntegrationValidationError(
                    f"Failed to delete catalog config {config_path}: {exc}"
                ) from exc

        fallback_name = f"catalog-{index + 1}"
        if isinstance(removed, dict):
            removed_name = removed.get("name")
            if removed_name is not None:
                normalized_name = str(removed_name).strip()
                if normalized_name:
                    return normalized_name

            removed_url = removed.get("url")
            if removed_url is not None:
                normalized_url = str(removed_url).strip()
                if normalized_url:
                    return normalized_url
        return fallback_name


# ---------------------------------------------------------------------------
# IntegrationDescriptor  (integration.yml)
# ---------------------------------------------------------------------------

class IntegrationDescriptor:
    """Loads and validates an ``integration.yml`` descriptor.

    The descriptor mirrors ``extension.yml`` and ``preset.yml``::

        schema_version: "1.0"
        integration:
          id: "my-agent"
          name: "My Agent"
          version: "1.0.0"
          description: "Integration for My Agent"
          author: "my-org"
        requires:
          speckit_version: ">=0.6.0"
          tools: [...]
        provides:
          commands: [...]
          scripts: [...]
    """

    SCHEMA_VERSION = "1.0"
    REQUIRED_TOP_LEVEL = ["schema_version", "integration", "requires", "provides"]

    def __init__(self, descriptor_path: Path) -> None:
        self.path = descriptor_path
        self.data = self._load(descriptor_path)
        self._validate()

    # -- Loading ----------------------------------------------------------

    @staticmethod
    def _load(path: Path) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise IntegrationDescriptorError(f"Invalid YAML in {path}: {exc}")
        except FileNotFoundError:
            raise IntegrationDescriptorError(f"Descriptor not found: {path}")
        except (OSError, UnicodeError) as exc:
            raise IntegrationDescriptorError(
                f"Unable to read descriptor {path}: {exc}"
            )

    # -- Validation -------------------------------------------------------

    def _validate(self) -> None:
        if not isinstance(self.data, dict):
            raise IntegrationDescriptorError(
                f"Descriptor root must be a YAML mapping, got {type(self.data).__name__}"
            )
        for field in self.REQUIRED_TOP_LEVEL:
            if field not in self.data:
                raise IntegrationDescriptorError(
                    f"Missing required field: {field}"
                )

        if self.data["schema_version"] != self.SCHEMA_VERSION:
            raise IntegrationDescriptorError(
                f"Unsupported schema version: {self.data['schema_version']} "
                f"(expected {self.SCHEMA_VERSION})"
            )

        integ = self.data["integration"]
        if not isinstance(integ, dict):
            raise IntegrationDescriptorError(
                "'integration' must be a mapping"
            )
        for field in ("id", "name", "version", "description"):
            if field not in integ:
                raise IntegrationDescriptorError(
                    f"Missing integration.{field}"
                )
            if not isinstance(integ[field], str):
                raise IntegrationDescriptorError(
                    f"integration.{field} must be a string, got {type(integ[field]).__name__}"
                )

        if not re.match(r"^[a-z0-9-]+$", integ["id"]):
            raise IntegrationDescriptorError(
                f"Invalid integration ID '{integ['id']}': "
                "must be lowercase alphanumeric with hyphens only"
            )

        try:
            pkg_version.Version(integ["version"])
        except (pkg_version.InvalidVersion, TypeError):
            raise IntegrationDescriptorError(
                f"Invalid version '{integ['version']}'"
            )

        requires = self.data["requires"]
        if not isinstance(requires, dict):
            raise IntegrationDescriptorError(
                "'requires' must be a mapping"
            )
        if "speckit_version" not in requires:
            raise IntegrationDescriptorError(
                "Missing requires.speckit_version"
            )
        if not isinstance(requires["speckit_version"], str) or not requires["speckit_version"].strip():
            raise IntegrationDescriptorError(
                "requires.speckit_version must be a non-empty string"
            )
        tools = requires.get("tools")
        if tools is not None:
            if not isinstance(tools, list):
                raise IntegrationDescriptorError(
                    "requires.tools must be a list"
                )
            for tool in tools:
                if not isinstance(tool, dict):
                    raise IntegrationDescriptorError(
                        "Each requires.tools entry must be a mapping"
                    )
                tool_name = tool.get("name")
                if not isinstance(tool_name, str) or not tool_name.strip():
                    raise IntegrationDescriptorError(
                        "requires.tools entry 'name' must be a non-empty string"
                    )

        provides = self.data["provides"]
        if not isinstance(provides, dict):
            raise IntegrationDescriptorError(
                "'provides' must be a mapping"
            )
        commands = provides.get("commands", [])
        scripts = provides.get("scripts", [])
        if "commands" in provides and not isinstance(commands, list):
            raise IntegrationDescriptorError(
                "Invalid provides.commands: expected a list"
            )
        if "scripts" in provides and not isinstance(scripts, list):
            raise IntegrationDescriptorError(
                "Invalid provides.scripts: expected a list"
            )
        if not commands and not scripts:
            raise IntegrationDescriptorError(
                "Integration must provide at least one command or script"
            )
        for cmd in commands:
            if not isinstance(cmd, dict):
                raise IntegrationDescriptorError(
                    "Each command entry must be a mapping"
                )
            if "name" not in cmd or "file" not in cmd:
                raise IntegrationDescriptorError(
                    "Command entry missing 'name' or 'file'"
                )
            cmd_name = cmd["name"]
            cmd_file = cmd["file"]
            if not isinstance(cmd_name, str) or not cmd_name.strip():
                raise IntegrationDescriptorError(
                    "Command entry 'name' must be a non-empty string"
                )
            if not isinstance(cmd_file, str) or not cmd_file.strip():
                raise IntegrationDescriptorError(
                    "Command entry 'file' must be a non-empty string"
                )
            if os.path.isabs(cmd_file) or ".." in Path(cmd_file).parts or Path(cmd_file).drive or Path(cmd_file).anchor:
                raise IntegrationDescriptorError(
                    f"Command entry 'file' must be a relative path without '..': {cmd_file}"
                )
        for script_entry in scripts:
            if not isinstance(script_entry, str) or not script_entry.strip():
                raise IntegrationDescriptorError(
                    "Script entry must be a non-empty string"
                )
            if os.path.isabs(script_entry) or ".." in Path(script_entry).parts or Path(script_entry).drive or Path(script_entry).anchor:
                raise IntegrationDescriptorError(
                    f"Script entry must be a relative path without '..': {script_entry}"
                )

    # -- Property accessors -----------------------------------------------

    @property
    def id(self) -> str:
        return self.data["integration"]["id"]

    @property
    def name(self) -> str:
        return self.data["integration"]["name"]

    @property
    def version(self) -> str:
        return self.data["integration"]["version"]

    @property
    def description(self) -> str:
        return self.data["integration"]["description"]

    @property
    def requires_speckit_version(self) -> str:
        return self.data["requires"]["speckit_version"]

    @property
    def commands(self) -> List[Dict[str, Any]]:
        return self.data.get("provides", {}).get("commands", [])

    @property
    def scripts(self) -> List[str]:
        return self.data.get("provides", {}).get("scripts", [])

    @property
    def tools(self) -> List[Dict[str, Any]]:
        return self.data.get("requires", {}).get("tools") or []

    def get_hash(self) -> str:
        """SHA-256 hash of the descriptor file."""
        with open(self.path, "rb") as fh:
            return f"sha256:{hashlib.sha256(fh.read()).hexdigest()}"
