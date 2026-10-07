"""Resolve bundle components from the first trustworthy catalog source."""

from __future__ import annotations

import ssl
from http.client import HTTPException
from urllib.error import HTTPError, URLError

from ..authentication.http import RedirectPolicyError
from . import BundlerError
from .manifest import ComponentRef


class CatalogUnavailable(BundlerError):
    """The winning component source cannot be determined right now."""


def _is_unavailable(exc: BaseException) -> bool:
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if isinstance(exc, RedirectPolicyError):
            return False
        if isinstance(exc, HTTPError):
            return exc.code in (408, 429) or 500 <= exc.code <= 599
        if isinstance(exc, URLError):
            return not isinstance(exc.reason, (ssl.SSLError, ValueError))
        if isinstance(exc, (ConnectionError, TimeoutError, HTTPException)):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def _source_entries(data: object, component: ComponentRef, url: str) -> dict | list:
    entries = data.get(component.kind) if isinstance(data, dict) else None
    if not isinstance(entries, (dict, list)):
        raise BundlerError(
            f"Invalid {component.kind[:-1]} catalog from {url}: "
            f"missing or malformed {component.kind} metadata."
        )
    return entries


def _matching_entry(entries: dict | list, component: ComponentRef, url: str) -> dict | None:
    if isinstance(entries, dict):
        if component.id not in entries:
            return None
        found = entries[component.id]
        if not isinstance(found, dict):
            raise BundlerError(
                f"Invalid {component.kind[:-1]} catalog entry for '{component.id}' "
                f"from {url}: expected an object."
            )
        return {**found, "id": component.id}

    seen: set[str] = set()
    found = None
    for item in entries:
        if not isinstance(item, dict):
            raise BundlerError(
                f"Invalid {component.kind[:-1]} catalog entry from {url}: "
                "expected an object."
            )
        item_id = item.get("id")
        if not isinstance(item_id, str):
            raise BundlerError(
                f"Invalid {component.kind[:-1]} ID in catalog {url}: expected a string."
            )
        item_id = item_id.strip() if component.kind == "steps" else item_id
        if not item_id:
            raise BundlerError(
                f"Invalid {component.kind[:-1]} ID in catalog {url}: empty ID."
            )
        if item_id in seen:
            raise BundlerError(
                f"Duplicate {component.kind[:-1]} ID '{item_id}' in catalog {url}."
            )
        seen.add(item_id)
        if item_id == component.id:
            found = {**item, "id": item_id}
    return found


def winning_catalog_entry(catalog, component: ComponentRef) -> dict | None:
    """Read sources in priority order rather than accepting a lower match on error.

    The component catalogs' public ID lookup skips failed catalogs. Bundles
    cannot do that: an unreadable higher source may own the requested ID.
    Reuse each catalog's authenticated, cached, redirect-checked fetcher and
    its existing release selector; only the strict winner policy lives here.
    """
    from ..extensions import ExtensionError
    from ..presets import PresetError
    from ..workflows.catalog import StepCatalogError, WorkflowCatalogError

    sources = catalog.get_active_catalogs()
    if component.source and sum(
        source.name == component.source for source in sources
    ) > 1:
        raise BundlerError(
            f"{component.kind[:-1]} '{component.id}' requests ambiguous catalog "
            f"source '{component.source}': multiple active catalogs share this name. "
            "Give each catalog a unique name before installing."
        )

    for source in sources:
        try:
            data = catalog._fetch_single_catalog(source)
        except (
            ExtensionError, PresetError, WorkflowCatalogError, StepCatalogError,
            OSError, HTTPException, UnicodeError, ValueError, TypeError,
            RecursionError,
        ) as exc:
            if _is_unavailable(exc):
                raise CatalogUnavailable(
                    f"Catalog '{source.name}' is unreachable: {exc}"
                ) from exc
            raise BundlerError(
                f"Invalid {component.kind[:-1]} catalog from {source.url}: {exc}"
            ) from exc

        entries = _source_entries(data, component, source.url)
        found = _matching_entry(entries, component, source.url)
        if found is not None:
            return {
                **found,
                "_catalog_name": source.name,
                "_install_allowed": source.install_allowed,
            }
    return None


def select_catalog_release(component: ComponentRef, entry: dict) -> dict | None:
    """Select from the already-fetched winning entry without a second lookup."""
    if component.kind == "extensions":
        from ..extensions._catalog_versions import select_release

        return select_release(entry, component.version)
    if component.kind == "presets":
        from ..presets._catalog_versions import select_release

        return select_release(entry, component.version)
    if component.kind == "workflows":
        from ..workflows.catalog._versions import select_release

        return select_release(entry, component.version)
    from ..workflows.step.catalog._versions import select_release

    return select_release(entry, component.id, component.version)
