"""Shared catalog stack config primitives.

Catalog-backed features use the same local config shape and URL validation
rules. This module keeps those narrow primitives in one place while individual
catalog types keep their active source resolution, fetch, cache, and
domain-specific validation behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import yaml


@dataclass
class CatalogEntry:
    """Represents a single catalog source in a catalog stack."""

    url: str
    name: str
    priority: int
    install_allowed: bool
    description: str = ""


class CatalogStackBase:
    """Base class for ordered catalog-source resolution.

    Subclasses provide catalog-specific metadata and exception classes. Fetching
    and schema validation stay in each concrete catalog because those formats
    differ across integrations, extensions, presets, and workflows.
    """

    ENTRY_CLASS: ClassVar[type[CatalogEntry]] = CatalogEntry
    ERROR_TYPE: ClassVar[type[Exception]] = ValueError
    VALIDATION_ERROR_TYPE: ClassVar[type[Exception]] = ValueError

    CONFIG_FILENAME: ClassVar[str]

    @classmethod
    def _error(cls, message: str) -> Exception:
        return cls.ERROR_TYPE(message)

    @classmethod
    def _validation_error(cls, message: str) -> Exception:
        return cls.VALIDATION_ERROR_TYPE(message)

    @classmethod
    def _entry(
        cls,
        *,
        url: str,
        name: str,
        priority: int,
        install_allowed: bool,
        description: str = "",
    ) -> CatalogEntry:
        return cls.ENTRY_CLASS(
            url=url,
            name=name,
            priority=priority,
            install_allowed=install_allowed,
            description=description,
        )

    @classmethod
    def _validate_catalog_url(cls, url: str) -> None:
        """Validate that a catalog URL uses HTTPS, except localhost HTTP."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            raise cls._error(
                f"Catalog URL must use HTTPS (got {parsed.scheme}://). "
                "HTTP is only allowed for localhost."
            )
        if not parsed.netloc:
            raise cls._error("Catalog URL must be a valid URL with a host.")

    def _load_catalog_config(self, config_path: Path) -> list[CatalogEntry] | None:
        """Load catalog stack configuration from a YAML file.

        Returns ``None`` when the file does not exist. Existing files fail
        closed when they are malformed, empty, or contain no usable URLs.
        """
        if not config_path.exists():
            return None
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeError) as exc:
            raise self._validation_error(
                f"Failed to read catalog config {config_path}: {exc}"
            ) from exc
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise self._validation_error(
                f"Invalid catalog config {config_path}: expected a YAML mapping at the root"
            )

        catalogs_data = data.get("catalogs", [])
        if not isinstance(catalogs_data, list):
            raise self._validation_error(
                f"Invalid catalog config {config_path}: 'catalogs' must be a list, "
                f"got {type(catalogs_data).__name__}"
            )
        if not catalogs_data:
            raise self._validation_error(
                f"Catalog config {config_path} exists but contains no 'catalogs' entries. "
                f"Remove the file to use built-in defaults, or add valid catalog entries."
            )

        entries: list[CatalogEntry] = []
        skipped: list[int] = []
        for idx, item in enumerate(catalogs_data):
            if not isinstance(item, dict):
                raise self._validation_error(
                    f"Invalid catalog config {config_path}: catalog entry at index {idx}: "
                    f"expected a mapping, got {type(item).__name__}"
                )
            url = str(item.get("url", "")).strip()
            if not url:
                skipped.append(idx)
                continue
            try:
                self._validate_catalog_url(url)
            except self.ERROR_TYPE as exc:
                raise self._validation_error(
                    f"Invalid catalog URL in {config_path} at index {idx}: {exc}"
                ) from exc

            raw_priority = item.get("priority", idx + 1)
            if isinstance(raw_priority, bool):
                raise self._validation_error(
                    f"Invalid catalog config {config_path}: "
                    f"Invalid priority for catalog '{item.get('name', idx + 1)}': "
                    f"expected integer, got {raw_priority!r}"
                )
            try:
                priority = int(raw_priority)
            except (TypeError, ValueError):
                raise self._validation_error(
                    f"Invalid catalog config {config_path}: "
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

            entries.append(
                self._entry(
                    url=url,
                    name=name,
                    priority=priority,
                    install_allowed=install_allowed,
                    description=str(item.get("description", "")),
                )
            )

        entries.sort(key=lambda e: e.priority)
        if not entries:
            raise self._validation_error(
                f"Catalog config {config_path} contains {len(catalogs_data)} "
                f"entries but none have valid URLs (entries at indices {skipped} "
                f"were skipped). Each catalog entry must have a 'url' field."
            )
        return entries
