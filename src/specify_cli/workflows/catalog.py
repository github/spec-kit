"""Workflow catalog — discovery, install, and management of workflows.

Mirrors the existing extension/preset catalog pattern with:
- Multi-catalog stack (env var → project → user → built-in)
- SHA256-hashed per-URL caching with 1-hour TTL
- Workflow registry for installed workflow tracking
- Search across all configured catalog sources
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class WorkflowCatalogError(Exception):
    """Base error for workflow catalog operations."""


class WorkflowValidationError(WorkflowCatalogError):
    """Validation error for catalog config or workflow data."""


# ---------------------------------------------------------------------------
# CatalogEntry
# ---------------------------------------------------------------------------


@dataclass
class WorkflowCatalogEntry:
    """Represents a single catalog source in the catalog stack."""

    url: str
    name: str
    priority: int
    install_allowed: bool
    description: str = ""


# ---------------------------------------------------------------------------
# WorkflowRegistry
# ---------------------------------------------------------------------------


class WorkflowRegistry:
    """Manages the registry of installed workflows.

    Tracks installed workflows and their metadata in
    ``.specify/workflows/workflow-registry.json``.
    """

    REGISTRY_FILE = "workflow-registry.json"
    SCHEMA_VERSION = "1.0"

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.workflows_dir = project_root / ".specify" / "workflows"
        self.registry_path = self.workflows_dir / self.REGISTRY_FILE
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        """Load registry from disk or create default."""
        default = {"schema_version": self.SCHEMA_VERSION, "workflows": {}}
        if self.registry_path.exists():
            try:
                with open(self.registry_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                return default
            if not isinstance(data, dict):
                return default
            # Normalize 'workflows' to a dict in case the file is corrupted
            if not isinstance(data.get("workflows"), dict):
                data["workflows"] = {}
            return data
        return default

    def save(self) -> None:
        """Persist registry to disk atomically (write to temp, then rename)."""
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

        # Capture existing file permissions to preserve after replace
        existing_stat = None
        if self.registry_path.exists():
            try:
                existing_stat = self.registry_path.stat()
            except OSError:
                pass

        fd, tmp_path = tempfile.mkstemp(
            suffix=".json", dir=self.workflows_dir
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            if existing_stat is not None:
                try:
                    os.chmod(tmp_path, existing_stat.st_mode & 0o7777)
                except OSError:
                    pass
            os.replace(tmp_path, self.registry_path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def add(self, workflow_id: str, metadata: dict[str, Any]) -> None:
        """Add or update an installed workflow entry."""
        from datetime import datetime, timezone

        existing = self.data["workflows"].get(workflow_id, {})
        metadata["installed_at"] = existing.get(
            "installed_at", datetime.now(timezone.utc).isoformat()
        )
        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.data["workflows"][workflow_id] = metadata
        self.save()

    def remove(self, workflow_id: str) -> bool:
        """Remove an installed workflow entry. Returns True if found."""
        if workflow_id in self.data["workflows"]:
            del self.data["workflows"][workflow_id]
            self.save()
            return True
        return False

    def update(self, workflow_id: str, fields: dict[str, Any]) -> None:
        """Update specific fields on an installed workflow entry."""
        from datetime import datetime, timezone

        if workflow_id not in self.data["workflows"]:
            return

        existing = self.data["workflows"][workflow_id]
        if not isinstance(existing, dict):
            now = datetime.now(timezone.utc).isoformat()
            repaired = dict(fields)
            repaired.setdefault("installed_at", now)
            repaired["updated_at"] = now
            self.data["workflows"][workflow_id] = repaired
            self.save()
            return
        installed_at = existing.get("installed_at")

        existing.update(fields)
        if installed_at is not None and "installed_at" not in fields:
            existing["installed_at"] = installed_at
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def get(self, workflow_id: str) -> dict[str, Any] | None:
        """Get metadata for an installed workflow."""
        return self.data["workflows"].get(workflow_id)

    def list(self) -> dict[str, dict[str, Any]]:
        """Return all installed workflows."""
        return dict(self.data["workflows"])

    def is_installed(self, workflow_id: str) -> bool:
        """Check if a workflow is installed."""
        return workflow_id in self.data["workflows"]


# ---------------------------------------------------------------------------
# WorkflowCatalog
# ---------------------------------------------------------------------------


class WorkflowCatalog:
    """Manages workflow catalog fetching, caching, and searching.

    Resolution order for catalog sources:
    1. ``SPECKIT_WORKFLOW_CATALOG_URL`` env var (overrides all)
    2. Project-level ``.specify/workflow-catalogs.yml``
    3. User-level ``~/.specify/workflow-catalogs.yml``
    4. Built-in defaults (official + community)
    """

    DEFAULT_CATALOG_URL = (
        "https://raw.githubusercontent.com/github/spec-kit/main/"
        "workflows/catalog.json"
    )
    COMMUNITY_CATALOG_URL = (
        "https://raw.githubusercontent.com/github/spec-kit/main/"
        "workflows/catalog.community.json"
    )
    CACHE_DURATION = 3600  # 1 hour

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.workflows_dir = project_root / ".specify" / "workflows"
        self.cache_dir = self.workflows_dir / ".cache"

    # -- Catalog resolution -----------------------------------------------

    def _validate_catalog_url(self, url: str) -> None:
        """Validate that a catalog URL uses HTTPS (localhost HTTP allowed)."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and is_localhost
        ):
            raise WorkflowValidationError(
                f"Catalog URL must use HTTPS (got {parsed.scheme}://). "
                "HTTP is only allowed for localhost."
            )
        if not parsed.netloc:
            raise WorkflowValidationError(
                "Catalog URL must be a valid URL with a host."
            )

    def _load_catalog_config(
        self, config_path: Path
    ) -> list[WorkflowCatalogEntry] | None:
        """Load catalog stack configuration from a YAML file."""
        if not config_path.exists():
            return None
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError, UnicodeError) as exc:
            raise WorkflowValidationError(
                f"Failed to read catalog config {config_path}: {exc}"
            )
        catalogs_data = data.get("catalogs", [])
        if not catalogs_data:
            # Empty catalogs list (e.g. after removing last entry)
            # is valid — fall back to built-in defaults.
            return None
        if not isinstance(catalogs_data, list):
            raise WorkflowValidationError(
                f"Invalid catalog config: 'catalogs' must be a list, "
                f"got {type(catalogs_data).__name__}"
            )

        entries: list[WorkflowCatalogEntry] = []
        for idx, item in enumerate(catalogs_data):
            if not isinstance(item, dict):
                raise WorkflowValidationError(
                    f"Invalid catalog entry at index {idx}: "
                    f"expected a mapping, got {type(item).__name__}"
                )
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            self._validate_catalog_url(url)
            try:
                priority = int(item.get("priority", idx + 1))
            except (TypeError, ValueError):
                raise WorkflowValidationError(
                    f"Invalid priority for catalog "
                    f"'{item.get('name', idx + 1)}': "
                    f"expected integer, got {item.get('priority')!r}"
                )
            raw_install = item.get("install_allowed", False)
            if isinstance(raw_install, str):
                install_allowed = raw_install.strip().lower() in (
                    "true",
                    "yes",
                    "1",
                )
            else:
                install_allowed = bool(raw_install)
            entries.append(
                WorkflowCatalogEntry(
                    url=url,
                    name=str(item.get("name", f"catalog-{idx + 1}")),
                    priority=priority,
                    install_allowed=install_allowed,
                    description=str(item.get("description", "")),
                )
            )
        entries.sort(key=lambda e: e.priority)
        if not entries:
            raise WorkflowValidationError(
                f"Catalog config {config_path} contains {len(catalogs_data)} "
                f"entries but none have valid URLs."
            )
        return entries

    def get_active_catalogs(self) -> list[WorkflowCatalogEntry]:
        """Get the ordered list of active catalogs."""
        # 1. Environment variable override
        env_url = os.environ.get("SPECKIT_WORKFLOW_CATALOG_URL", "").strip()
        if env_url:
            self._validate_catalog_url(env_url)
            return [
                WorkflowCatalogEntry(
                    url=env_url,
                    name="env-override",
                    priority=1,
                    install_allowed=True,
                    description="From SPECKIT_WORKFLOW_CATALOG_URL",
                )
            ]

        # 2. Project-level config
        project_config = self.project_root / ".specify" / "workflow-catalogs.yml"
        project_entries = self._load_catalog_config(project_config)
        if project_entries is not None:
            return project_entries

        # 3. User-level config
        home = Path.home()
        user_config = home / ".specify" / "workflow-catalogs.yml"
        user_entries = self._load_catalog_config(user_config)
        if user_entries is not None:
            return user_entries

        # 4. Built-in defaults
        return [
            WorkflowCatalogEntry(
                url=self.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
                description="Official workflows",
            ),
            WorkflowCatalogEntry(
                url=self.COMMUNITY_CATALOG_URL,
                name="community",
                priority=2,
                install_allowed=False,
                description="Community-contributed workflows (discovery only)",
            ),
        ]

    # -- Caching ----------------------------------------------------------

    def _get_cache_paths(self, url: str) -> tuple[Path, Path]:
        """Get cache file paths for a URL (hash-based)."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = self.cache_dir / f"workflow-catalog-{url_hash}.json"
        meta_file = self.cache_dir / f"workflow-catalog-{url_hash}-meta.json"
        return cache_file, meta_file

    def _is_url_cache_valid(self, url: str) -> bool:
        """Check if cached data for a URL is still fresh."""
        _, meta_file = self._get_cache_paths(url)
        if not meta_file.exists():
            return False
        try:
            with open(meta_file, encoding="utf-8") as f:
                meta = json.load(f)
            fetched_at = meta.get("fetched_at", 0)
            return (time.time() - fetched_at) < self.CACHE_DURATION
        except (json.JSONDecodeError, OSError):
            return False

    def _fetch_single_catalog(
        self, entry: WorkflowCatalogEntry, force_refresh: bool = False
    ) -> dict[str, Any]:
        """Fetch a single catalog, using cache when possible."""
        cache_file, meta_file = self._get_cache_paths(entry.url)

        if not force_refresh and self._is_url_cache_valid(entry.url):
            try:
                with open(cache_file, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Fetch from URL — validate scheme before opening and after redirects
        from urllib.parse import urlparse
        from urllib.request import urlopen

        def _validate_catalog_url(url: str) -> None:
            parsed = urlparse(url)
            is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if parsed.scheme != "https" and not (
                parsed.scheme == "http" and is_localhost
            ):
                raise WorkflowCatalogError(
                    f"Refusing to fetch catalog from non-HTTPS URL: {url}"
                )

        _validate_catalog_url(entry.url)

        try:
            with urlopen(entry.url, timeout=30) as resp:  # noqa: S310
                _validate_catalog_url(resp.geturl())
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            # Fall back to cache if available
            if cache_file.exists():
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, ValueError, OSError):
                    pass
            raise WorkflowCatalogError(
                f"Failed to fetch catalog from {entry.url}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise WorkflowCatalogError(
                f"Catalog from {entry.url} is not a valid JSON object."
            )

        # Write cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({"url": entry.url, "fetched_at": time.time()}, f)

        return data

    def _get_merged_workflows(
        self, force_refresh: bool = False
    ) -> dict[str, dict[str, Any]]:
        """Merge workflows from all active catalogs (lower priority number wins)."""
        catalogs = self.get_active_catalogs()
        merged: dict[str, dict[str, Any]] = {}
        fetch_errors = 0

        # Process later/higher-numbered entries first so earlier/lower-numbered
        # entries overwrite them on workflow ID conflicts.
        for entry in reversed(catalogs):
            try:
                data = self._fetch_single_catalog(entry, force_refresh)
            except WorkflowCatalogError:
                fetch_errors += 1
                continue
            workflows = data.get("workflows", {})
            # Handle both dict and list formats
            if isinstance(workflows, dict):
                for wf_id, wf_data in workflows.items():
                    if not isinstance(wf_data, dict):
                        continue
                    wf_data["_catalog_name"] = entry.name
                    wf_data["_install_allowed"] = entry.install_allowed
                    merged[wf_id] = wf_data
            elif isinstance(workflows, list):
                for wf_data in workflows:
                    if not isinstance(wf_data, dict):
                        continue
                    wf_id = wf_data.get("id", "")
                    if wf_id:
                        wf_data["_catalog_name"] = entry.name
                        wf_data["_install_allowed"] = entry.install_allowed
                        merged[wf_id] = wf_data
        if fetch_errors == len(catalogs) and catalogs:
            raise WorkflowCatalogError(
                "All configured catalogs failed to fetch."
            )
        return merged

    # -- Public API -------------------------------------------------------

    def search(
        self,
        query: str | None = None,
        tag: str | None = None,
        author: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search workflows across all configured catalogs."""
        merged = self._get_merged_workflows()
        results: list[dict[str, Any]] = []

        for wf_id, wf_data in merged.items():
            wf_data.setdefault("id", wf_id)
            if author:
                raw_author = wf_data.get("author", "")
                normalized_author = raw_author if isinstance(raw_author, str) else ""
                if normalized_author.lower() != author.lower():
                    continue
            if query:
                q = query.lower()
                searchable = " ".join(
                    [
                        wf_data.get("name", ""),
                        wf_data.get("description", ""),
                        wf_data.get("id", ""),
                    ]
                ).lower()
                if q not in searchable:
                    continue
            if tag:
                raw_tags = wf_data.get("tags", [])
                tags = raw_tags if isinstance(raw_tags, list) else []
                normalized_tags = [t.lower() for t in tags if isinstance(t, str)]
                if tag.lower() not in normalized_tags:
                    continue
            results.append(wf_data)
        return results

    def get_workflow_info(self, workflow_id: str) -> dict[str, Any] | None:
        """Get details for a specific workflow from the catalog."""
        merged = self._get_merged_workflows()
        wf = merged.get(workflow_id)
        if wf:
            wf.setdefault("id", workflow_id)
        return wf

    def get_catalog_configs(self) -> list[dict[str, Any]]:
        """Return current catalog configuration as a list of dicts."""
        entries = self.get_active_catalogs()
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

    def add_catalog(self, url: str, name: str | None = None) -> None:
        """Add a catalog source to the project-level config."""
        self._validate_catalog_url(url)
        config_path = self.project_root / ".specify" / "workflow-catalogs.yml"

        data: dict[str, Any] = {"catalogs": []}
        if config_path.exists():
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise WorkflowValidationError(
                    "Catalog config file is corrupted (expected a mapping)."
                )
            data = raw

        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list):
            raise WorkflowValidationError(
                "Catalog config 'catalogs' must be a list."
            )
        # Check for duplicate URL (guard against non-dict entries)
        for cat in catalogs:
            if isinstance(cat, dict) and cat.get("url") == url:
                raise WorkflowValidationError(
                    f"Catalog URL already configured: {url}"
                )

        # Derive priority from the highest existing priority + 1
        max_priority = max(
            (cat.get("priority", 0) for cat in catalogs if isinstance(cat, dict)),
            default=0,
        )
        catalogs.append(
            {
                "name": name or f"catalog-{len(catalogs) + 1}",
                "url": url,
                "priority": max_priority + 1,
                "install_allowed": True,
                "description": "",
            }
        )
        data["catalogs"] = catalogs

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def remove_catalog(self, index: int) -> str:
        """Remove a catalog source by index (0-based). Returns the removed name."""
        config_path = self.project_root / ".specify" / "workflow-catalogs.yml"
        if not config_path.exists():
            raise WorkflowValidationError("No catalog config file found.")

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise WorkflowValidationError(
                "Catalog config file is corrupted (expected a mapping)."
            )
        catalogs = data.get("catalogs", [])
        if not isinstance(catalogs, list):
            raise WorkflowValidationError(
                "Catalog config 'catalogs' must be a list."
            )

        if index < 0 or index >= len(catalogs):
            raise WorkflowValidationError(
                f"Catalog index {index} out of range (0-{len(catalogs) - 1})."
            )

        removed = catalogs.pop(index)
        data["catalogs"] = catalogs

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        if isinstance(removed, dict):
            return removed.get("name", f"catalog-{index + 1}")
        return f"catalog-{index + 1}"
