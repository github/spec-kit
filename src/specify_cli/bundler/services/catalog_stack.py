"""Catalog stack: aggregate bundle entries across sources with precedence + policy.

Loads each source's catalog payload (via an injectable fetcher so tests stay
offline), then resolves a bundle id to the highest-precedence entry while
recording whether installation is permitted by that source's policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .. import BundlerError
from ..models.catalog import (
    CatalogEntry,
    CatalogSource,
    load_catalog_payload,
    load_source_stack,
)

# A fetcher returns the raw JSON payload (a dict) for a given source.
CatalogFetcher = Callable[[CatalogSource], dict]


@dataclass
class ResolvedBundle:
    entry: CatalogEntry
    source: CatalogSource

    @property
    def install_allowed(self) -> bool:
        return self.source.install_allowed


class CatalogStack:
    def __init__(
        self,
        sources: list[CatalogSource],
        fetcher: CatalogFetcher,
    ) -> None:
        # Highest precedence (lowest priority number) first.
        self._sources = sorted(sources, key=lambda s: (s.priority, s.id))
        self._fetcher = fetcher
        self._payloads: dict[str, dict[str, CatalogEntry]] = {}

    @classmethod
    def load(
        cls,
        project_root: Path,
        fetcher: CatalogFetcher,
        user_config_dir: Path | None = None,
    ) -> "CatalogStack":
        sources = load_source_stack(project_root, user_config_dir)
        return cls(sources, fetcher)

    @property
    def sources(self) -> list[CatalogSource]:
        return list(self._sources)

    def _entries_for(self, source: CatalogSource) -> dict[str, CatalogEntry]:
        if source.id not in self._payloads:
            try:
                raw = self._fetcher(source)
            except BundlerError:
                raise
            except Exception as exc:  # noqa: BLE001 - surface as chained BundlerError
                raise BundlerError(
                    f"Failed to load catalog '{source.id}' ({source.url}): {exc}"
                ) from exc
            self._payloads[source.id] = load_catalog_payload(raw)
        return self._payloads[source.id]

    def resolve(self, bundle_id: str) -> ResolvedBundle:
        """Return the highest-precedence entry for *bundle_id* or raise."""
        for source in self._sources:
            entries = self._entries_for(source)
            entry = entries.get(bundle_id)
            if entry is not None:
                return ResolvedBundle(entry=entry.with_provenance(source), source=source)
        raise BundlerError(
            f"Bundle '{bundle_id}' was not found in any configured catalog."
        )

    def search(self, query: str = "") -> list[ResolvedBundle]:
        """Return entries matching *query* (substring over id/name/role/tags/description).

        Each bundle id appears once, resolved at its highest-precedence source.
        Results are sorted by bundle id for deterministic output.
        """
        needle = query.strip().lower()
        # Resolve each id to its highest-precedence entry FIRST, then filter by
        # the query. Claiming an id only when it matches would let a lower-
        # precedence entry with the same id surface when the highest-precedence
        # one doesn't match the query — but that shadowed entry is not what
        # `resolve()`/install would use, so search would advertise a bundle
        # (name, version, author) the user can never actually get.
        resolved: dict[str, ResolvedBundle] = {}
        for source in self._sources:
            for bundle_id, entry in self._entries_for(source).items():
                if bundle_id in resolved:
                    continue
                resolved[bundle_id] = ResolvedBundle(
                    entry=entry.with_provenance(source), source=source
                )
        return [
            resolved[k]
            for k in sorted(resolved)
            if not needle or _matches(resolved[k].entry, needle)
        ]


def _matches(entry: CatalogEntry, needle: str) -> bool:
    haystack = " ".join(
        [
            entry.id,
            entry.name,
            entry.role,
            entry.description,
            " ".join(entry.tags),
        ]
    ).lower()
    return needle in haystack
