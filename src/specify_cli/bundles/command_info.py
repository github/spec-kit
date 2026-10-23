"""Implementation of ``specify bundle info``."""

from __future__ import annotations

import json as _json
from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from .._file_policy import ProjectPolicyError
from . import BundlerError
from ._commands import (
    _build_stack,
    _bundle_overlaps,
    _expand_manifest,
    _fail,
    _trust_badge,
    _trust_level,
    bundle_app,
)
from .project import find_project_root
from .sources import _download_manifest
from .versioning import same_version


@bundle_app.command("info")
def bundle_info(
    bundle_id: str = typer.Argument(..., help="Bundle id to inspect"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
    versions: bool = typer.Option(False, "--versions", help="List catalog versions"),
) -> None:
    """Show full metadata and the fully expanded component set (== what install adds)."""
    try:
        if Path(bundle_id).expanduser().exists():
            raise BundlerError(
                "Local bundle preview is not supported; 'specify bundle info' "
                "accepts a catalog bundle ID. Add the bundle to a catalog to preview it."
            )
        project_root = find_project_root() or Path.cwd()
        stack = _build_stack(project_root, offline=offline)
        resolved = stack.resolve(bundle_id)
        if versions is True:
            from .catalog_versions import available_versions

            available = available_versions(resolved.entry)
            if as_json:
                print(
                    _json.dumps(
                        {
                            "id": resolved.entry.id,
                            "versions": available,
                            "current": resolved.entry.version,
                            "source": resolved.source.id,
                            "install_policy": resolved.source.install_policy.value,
                        },
                        indent=2,
                    )
                )
                return
            console.print(
                f"Catalog versions for {_escape_markup(str(resolved.entry.id))}:"
            )
            for index, available_version in enumerate(available):
                current = " (current)" if index == 0 else ""
                console.print(f"  {_escape_markup(available_version)}{current}")
            console.print(
                f"  Source: {_escape_markup(str(resolved.source.id))} "
                f"({resolved.source.install_policy.value})"
            )
            if not resolved.install_allowed:
                console.print(
                    "[yellow]Discovery only; catalog installation is disabled.[/yellow]"
                )
            return
        # `info` must show the fully expanded component set that `install` would
        # apply (contracts/cli-commands.md). Expansion happens regardless of
        # install policy — discovery-only bundles stay inspectable; only
        # `install` is refused. But if the manifest itself can't be resolved
        # (e.g. --offline against an https:// download_url, or a download
        # failure), fail loudly and exit non-zero rather than silently
        # degrading to catalog `provides` counts, so users never mistake an
        # unverifiable bundle for a known/installable one.
        manifest = _download_manifest(resolved, offline=offline)
        expanded = _expand_manifest(
            project_root,
            manifest,
            offline=offline,
            stack=stack,
            download=_download_manifest,
        )
    except BundlerError as exc:
        _fail(str(exc), as_json=as_json and isinstance(exc.__cause__, ProjectPolicyError))
        return

    if expanded.has_references:
        overlaps = _bundle_overlaps(
            project_root,
            manifest,
            offline=offline,
            components=expanded.components,
        )
    else:
        # Preserve the flat command's established call shape and rendering.
        overlaps = _bundle_overlaps(project_root, manifest, offline=offline)
    components = _manifest_component_view(expanded)

    entry = resolved.entry
    if as_json:
        payload = {
            "id": entry.id,
            "name": entry.name,
            "version": entry.version,
            "role": entry.role,
            "description": entry.description,
            "author": entry.author,
            "license": entry.license,
            "source": resolved.source.id,
            "install_policy": resolved.source.install_policy.value,
            "provides": entry.provides,
            "requires": {"speckit_version": entry.requires_speckit_version},
            "verified": entry.verified,
            "trust": _trust_level(entry.verified),
            "integration": (
                manifest.integration.id if manifest and manifest.integration else None
            ),
            "components": components,
            "overlaps": overlaps,
        }
        if expanded.has_references:
            payload["references"] = _reference_view(expanded)
        print(_json.dumps(payload, indent=2))
        return

    console.print(
        f"\n[bold cyan]{_escape_markup(str(entry.id))}[/bold cyan] "
        f"v{_escape_markup(str(entry.version))} — "
        f"{_escape_markup(str(entry.name))}"
    )
    console.print(f"  Role: {_escape_markup(str(entry.role))}")
    console.print(f"  {_escape_markup(str(entry.description))}")
    console.print(
        f"  Author: {_escape_markup(str(entry.author))}   "
        f"License: {_escape_markup(str(entry.license))}"
    )
    console.print(
        f"  Source: {_escape_markup(str(resolved.source.id))} "
        f"({resolved.source.install_policy.value})"
    )
    console.print(f"  Trust: {_trust_badge(entry.verified)}")
    if entry.requires_speckit_version:
        console.print(
            f"  Requires Spec Kit: "
            f"{_escape_markup(str(entry.requires_speckit_version))}"
        )
    if manifest and manifest.integration:
        console.print(f"  Integration: {_escape_markup(str(manifest.integration.id))}")

    if expanded.has_references:
        console.print("\n  [bold]References:[/bold]")
        for reference in expanded.references:
            console.print(f"    - {_escape_markup(_format_reference(reference))}")

    if components:
        console.print("\n  [bold]Components[/bold] (added on install):")
        for kind in ("extensions", "presets", "steps", "workflows"):
            items = [c for c in components if c["kind"] == kind]
            if not items:
                continue
            console.print(f"    [bold]{kind}:[/bold]")
            for item in items:
                console.print(f"      - {_escape_markup(_format_component(item))}")
    else:
        console.print("\n  [bold]Provides:[/bold]")
        for kind in ("extensions", "presets", "steps", "workflows"):
            count = entry.provides.get(kind, 0)
            if count:
                console.print(f"    {kind}: {_escape_markup(str(count))}")

    if overlaps:
        console.print("\n  [yellow]Overlaps with already-installed bundles:[/yellow]")
        for overlap in overlaps:
            console.print(f"    [yellow]-[/yellow] {_escape_markup(str(overlap))}")

    if not resolved.install_allowed:
        console.print(
            "\n  [yellow]This source is discovery-only; the bundle cannot be "
            "installed from here.[/yellow]"
        )


def _manifest_component_view(expanded) -> list[dict]:
    """Flatten an expanded manifest to JSON-friendly component dictionaries."""
    if expanded is None:
        return []
    view: list[dict] = []
    for component in expanded.components:
        item = {
            "kind": component.kind,
            "id": component.id,
            "version": component.version,
        }
        if expanded.has_references and component.source is not None:
            item["source"] = component.source
        if component.priority is not None:
            item["priority"] = component.priority
        if component.strategy is not None:
            item["strategy"] = component.strategy
        if expanded.has_references:
            origin = expanded.origins.get((component.kind, component.id))
            if origin is not None and origin.origin:
                item["origin"] = list(origin.origin)
            if origin is not None and origin.overrides:
                item["overrides"] = [
                    _component_provenance(override.component, override.origin)
                    for override in origin.overrides
                ]
        view.append(item)
    return view


def _component_provenance(component, origin: tuple[str, ...]) -> dict:
    item = {
        "version": component.version,
        "origin": list(origin),
    }
    if component.source is not None:
        item["source"] = component.source
    if component.priority is not None:
        item["priority"] = component.priority
    if component.strategy is not None:
        item["strategy"] = component.strategy
    return item


def _reference_view(expanded) -> list[dict]:
    return [
        {
            "id": reference.id,
            "version": reference.version,
            "source": reference.source_id,
            "install_policy": (
                "install-allowed" if reference.install_allowed else "discovery-only"
            ),
            "via": list(reference.via),
        }
        for reference in expanded.references
    ]


def _format_reference(reference) -> str:
    label = f"{reference.id} v{reference.version} ({reference.source_id}"
    if reference.via:
        label += f"; via {' → '.join(reference.via)}"
    if not reference.install_allowed:
        label += "; discovery-only, not installable"
    label += ")"
    return label


def _format_component(item: dict) -> str:
    label = f"{item['id']} v{item['version']}" if item.get("version") else item["id"]
    extras = []
    if item.get("priority") is not None:
        extras.append(f"priority={item['priority']}")
    if item.get("strategy") is not None:
        extras.append(f"strategy={item['strategy']}")
    origin = item.get("origin")
    if origin:
        extras.append(f"from {' → '.join(origin)}")
    for override in item.get("overrides", []):
        extras.append(_format_override(item, override))
    if extras:
        label += f" ({', '.join(extras)})"
    return label


def _format_override(item: dict, override: dict) -> str:
    """Describe the settings replaced by an overriding component."""
    changed: list[str] = []
    old_version = override.get("version")
    current_version = item.get("version")
    versions_differ = (old_version is None) != (current_version is None)
    if (
        versions_differ
        or (
            old_version is not None
            and current_version is not None
            and not same_version(current_version, old_version)
        )
    ):
        changed.append(str(old_version) if old_version else "unpinned")

    for field in ("source", "priority", "strategy"):
        if override.get(field) != item.get(field):
            value = override.get(field)
            changed.append(f"{field}={value if value is not None else '<unset>'}")

    # An override always differs in at least one install-affecting field, but
    # retain the historical version-only marker if a caller supplies an
    # incomplete provenance dictionary.
    if not changed:
        changed.append(str(old_version) if old_version else "unpinned")
    marker = ", ".join(changed)
    origin = " → ".join(override.get("origin", []))
    return f"overrides {marker} from {origin}"
