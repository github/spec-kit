"""Preset catalog retrieval and downloads (private domain implementation)."""

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .._download_security import (
    archive_format_from_name,
    archive_suffix,
    build_safe_download_path,
    detect_archive_format,
    is_https_or_localhost_http,
)
from ._manifest import PresetError, PresetValidationError


@dataclass
class PresetCatalogEntry:
    """Represents a single entry in the preset catalog stack."""
    url: str
    name: str
    priority: int
    install_allowed: bool
    description: str = ""


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
            # Accessing ``port`` performs urllib's syntax/range validation;
            # ``hostname`` alone does not, so a non-numeric or out-of-range
            # port would otherwise pass validation here and only fail later,
            # at fetch time, as a raw error this function does not translate
            # into PresetValidationError. Mirrors specify_cli.catalogs and
            # bundler/services/adapters.py's copy of this same guard.
            _ = parsed.port
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
        redirect_validator=None,
    ):
        """Open a URL with provider-based auth, trying each configured provider.

        Delegates to :func:`specify_cli.authentication.http.open_url`.
        *redirect_validator*, when provided, is invoked as ``(old_url, new_url)``
        before EACH redirect hop, so an HTTPS host guarantee can be enforced on
        every intermediate URL, not just the terminal one.
        """
        from specify_cli.authentication.http import open_url
        return open_url(
            url,
            timeout,
            extra_headers=extra_headers,
            redirect_validator=redirect_validator,
        )

    def _resolve_github_release_asset_api_url(
        self,
        download_url: str,
        timeout: int = 60,
    ) -> Optional[str]:
        """Resolve a GitHub release asset URL to its REST API asset URL.

        Passes the ``github`` provider hosts from ``auth.json`` so GitHub
        Enterprise Server release assets resolve via ``/api/v3``.
        """
        from specify_cli.authentication.github_http import (
            resolve_github_release_asset_api_url,
        )
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
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeError) as e:
            raise PresetValidationError(
                f"Failed to read catalog config {config_path}: {e}"
            )
        # Do NOT coerce with ``or {}`` here: that also turns a FALSY
        # non-mapping top level (``[]``, ``false``, ``0``, ``''``) into ``{}``
        # and silently swallows it, while a TRUTHY non-mapping (``5``, a bare
        # list) correctly raises below. Only an empty document/explicit
        # ``null`` means "no document".
        if data is None:
            return None
        if not isinstance(data, dict):
            raise PresetValidationError(
                f"Invalid catalog config {config_path}: expected a mapping at root, got {type(data).__name__}"
            )
        # Same asymmetry one nesting level down: the shape check has to run
        # BEFORE the emptiness check, or a FALSY non-list ``catalogs`` value
        # (``{}``, ``''``, ``0``, ``false``) is silently swallowed as "no
        # catalogs" while a TRUTHY non-list (``catalogs: "not-a-list"``)
        # correctly raises. An absent key or an explicit ``catalogs: null``
        # both keep their existing "nothing configured here" behavior.
        catalogs_data = data.get("catalogs")
        if catalogs_data is None:
            return None
        if not isinstance(catalogs_data, list):
            raise PresetValidationError(
                f"Invalid catalog config: 'catalogs' must be a list, got {type(catalogs_data).__name__}"
            )
        if not catalogs_data:
            return None
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
            except (TypeError, ValueError, OverflowError):
                # OverflowError: int(float("inf")) — a YAML ``priority: .inf``
                # would otherwise escape as an uncaught traceback instead of the
                # clean validation error (mirrors catalogs.py).
                raise PresetValidationError(
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {raw_priority!r}"
                )
            raw_install = item.get("install_allowed", False)
            if isinstance(raw_install, str):
                install_allowed = raw_install.strip().lower() in ("true", "yes", "1")
            else:
                install_allowed = bool(raw_install)
            raw_name = item.get("name")
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name:
                name = f"catalog-{len(entries) + 1}"

            entries.append(PresetCatalogEntry(
                url=url,
                name=name,
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
        # Honor the established package-level patch points during extraction.
        from . import MAX_JSON_CATALOG_BYTES, read_response_limited

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
            # Validate EVERY redirect hop (not just the terminal URL): an
            # https -> http -> attacker-controlled-https chain would pass a
            # final-URL-only check while the insecure intermediate hop lets a
            # network attacker rewrite the next redirect. redirect_validator runs
            # before each hop; the final geturl() check is retained as a
            # belt-and-braces guard. Mirrors bundler/services/adapters.py.
            def _validate_redirect(_old_url: str, new_url: str) -> None:
                self._validate_catalog_url(new_url)

            with self._open_url(
                entry.url, timeout=10, redirect_validator=_validate_redirect
            ) as response:
                final_url = response.geturl()
                if final_url != entry.url:
                    self._validate_catalog_url(final_url)
                catalog_data = json.loads(
                    read_response_limited(
                        response,
                        max_bytes=MAX_JSON_CATALOG_BYTES,
                        error_type=PresetError,
                        label=f"preset catalog {entry.url}",
                    )
                )

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
        from . import MAX_JSON_CATALOG_BYTES, read_response_limited

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
            # Same redirect hardening as _fetch_single_catalog: validate every
            # redirect hop AND the final URL so this legacy single-catalog path
            # is not vulnerable to an HTTPS->HTTP redirected payload either.
            def _validate_redirect(_old_url: str, new_url: str) -> None:
                self._validate_catalog_url(new_url)

            with self._open_url(
                catalog_url, timeout=10, redirect_validator=_validate_redirect
            ) as response:
                final_url = response.geturl()
                if final_url != catalog_url:
                    self._validate_catalog_url(final_url)
                catalog_data = json.loads(
                    read_response_limited(
                        response,
                        max_bytes=MAX_JSON_CATALOG_BYTES,
                        error_type=PresetError,
                        label=f"preset catalog {catalog_url}",
                    )
                )

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
            if author:
                author_val = pack_data.get("author", "")
                if not isinstance(author_val, str):
                    author_val = str(author_val) if author_val is not None else ""
                if author_val.lower() != author.lower():
                    continue

            if tag:
                raw_tags = pack_data.get("tags", [])
                tags_list = raw_tags if isinstance(raw_tags, list) else []
                if tag.lower() not in [
                    str(t).lower() for t in tags_list
                ]:
                    continue

            if query:
                query_lower = query.lower()
                raw_tags = pack_data.get("tags", [])
                tags_list = raw_tags if isinstance(raw_tags, list) else []
                name_val = pack_data.get("name", "")
                desc_val = pack_data.get("description", "")
                searchable_text = " ".join(
                    [
                        str(name_val) if name_val is not None else "",
                        str(desc_val) if desc_val is not None else "",
                        pack_id,
                    ]
                    + [str(t) for t in tags_list]
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
        """Download a preset archive from a catalog.

        Args:
            pack_id: ID of the preset to download
            target_dir: Directory to save the archive

        Returns:
            Path to the downloaded archive

        Raises:
            PresetError: If pack not found or download fails
        """
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
        if not isinstance(download_url, str):
            raise PresetError(
                f"Preset download URL is malformed: {download_url}"
            )

        return self.download_pack_url(
            download_url,
            pack_id,
            pack_info.get("version"),
            sha256=pack_info.get("sha256"),
            target_dir=target_dir,
        )

    def download_pack_url(
        self,
        download_url: str,
        pack_id: str,
        version: Optional[str] = None,
        *,
        sha256: Optional[str] = None,
        target_dir: Optional[Path] = None,
    ) -> Path:
        """Download a preset archive from an explicit URL.

        The same pipeline ``download_pack`` applies to a catalog entry's
        ``download_url`` (HTTPS validation, size-limited fetch, optional
        SHA-256 verification, archive-format detection, safe cache path),
        without a catalog lookup, so callers can retrieve a specific release
        by URL -- e.g. a bundle pin the catalog no longer advertises.
        ``sha256`` defaults to ``None`` (no digest check): a release that is
        not the catalog's advertised one has no catalog-declared digest to
        verify against.

        Args:
            download_url: HTTPS URL of the archive to download
            pack_id: ID used to name the cached archive
            version: Version used to name the cached archive ("unknown"
                when None)
            sha256: Expected SHA-256 hex digest, or None to skip the check
            target_dir: Directory to save the archive

        Returns:
            Path to the downloaded archive

        Raises:
            PresetError: If the URL is invalid or the download fails
        """
        import urllib.error

        from . import read_response_limited, verify_archive_sha256

        if not isinstance(download_url, str):
            raise PresetError(
                f"Preset download URL is malformed: {download_url}"
            )

        from urllib.parse import urlparse

        # A malformed authority (e.g., an unterminated IPv6 bracket
        # "https://[::1") makes urlparse / hostname access raise ValueError.
        # The URL comes from caller data (a catalog payload field or a
        # derived pinned-release URL), so surface a clean PresetError rather
        # than leaking a raw ValueError past the command handler (which only
        # catches PresetError). Mirrors catalogs (#3435) and
        # workflows/catalog.py (#3484).
        try:
            parsed = urlparse(download_url)
            hostname = parsed.hostname
            parsed.port
        except ValueError:
            raise PresetError(
                f"Preset download URL is malformed: {download_url}"
            ) from None
        if not hostname:
            raise PresetError(
                f"Preset download URL is malformed: {download_url}"
            )
        if not is_https_or_localhost_http(download_url):
            raise PresetError(
                f"Preset download URL must use HTTPS: {download_url}"
            )

        if target_dir is None:
            target_dir = self.cache_dir / "downloads"
        target_dir = Path(target_dir)
        version = "unknown" if version is None else version
        declared_format = archive_format_from_name(download_url)
        build_safe_download_path(
            target_dir,
            pack_id,
            version,
            error_type=PresetError,
            label="preset",
            suffix=archive_suffix(declared_format or "tar.gz"),
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        original_download_url = download_url
        extra_headers = None
        resolved_download_url = self._resolve_github_release_asset_api_url(download_url)
        if resolved_download_url:
            download_url = resolved_download_url
            extra_headers = {"Accept": "application/octet-stream"}

        staging_path: Path | None = None
        try:
            with self._open_url(download_url, timeout=60, extra_headers=extra_headers) as response:
                archive_data = read_response_limited(
                    response,
                    error_type=PresetError,
                    label=f"preset '{pack_id}' download",
                )
                final_url = (
                    response.geturl()
                    if hasattr(response, "geturl")
                    else download_url
                )
                content_type = (
                    response.getheader("Content-Type")
                    if hasattr(response, "getheader")
                    else None
                )

            verify_archive_sha256(
                archive_data, sha256, pack_id, PresetError
            )

            with tempfile.NamedTemporaryFile(
                prefix="preset-download-",
                suffix=".archive",
                dir=target_dir,
                delete=False,
            ) as staging_file:
                staging_path = Path(staging_file.name)
                staging_file.write(archive_data)
            archive_format = detect_archive_format(
                staging_path,
                source_name=(
                    final_url
                    if archive_format_from_name(final_url) is not None
                    else original_download_url
                ),
                content_type=content_type,
                error_type=PresetError,
            )
            archive_path = build_safe_download_path(
                target_dir,
                pack_id,
                version,
                error_type=PresetError,
                label="preset",
                suffix=archive_suffix(archive_format),
            )
            os.replace(staging_path, archive_path)
            staging_path = None
            return archive_path

        except urllib.error.URLError as e:
            raise PresetError(
                f"Failed to download preset from {download_url}: {e}"
            )
        except IOError as e:
            raise PresetError(f"Failed to save preset archive: {e}")
        finally:
            if staging_path is not None:
                staging_path.unlink(missing_ok=True)

    def clear_cache(self):
        """Clear all catalog cache files, including per-URL hashed caches."""
        if self.cache_dir.exists():
            for f in self.cache_dir.iterdir():
                if f.is_file() and f.name.startswith("catalog"):
                    f.unlink(missing_ok=True)
