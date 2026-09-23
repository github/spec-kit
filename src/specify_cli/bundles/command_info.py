"""Implementation of ``specify bundle info``."""

from __future__ import annotations

import json as _json
from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import (
    _build_stack,
    _bundle_overlaps,
    _fail,
    _trust_badge,
    _trust_level,
    bundle_app,
)
from .project import find_project_root
from .sources import _download_manifest


@bundle_app.command("info")
def bundle_info(
    bundle_id: str = typer.Argument(..., help="Bundle id to inspect"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
) -> None:
    """Show full metadata and the fully expanded component set (== what install adds)."""
    try:
        project_root = find_project_root() or Path.cwd()
        stack = _build_stack(project_root, offline=offline)
        resolved = stack.resolve(bundle_id)
        # `info` must show the fully expanded component set that `install` would
        # apply (contracts/cli-commands.md). Expansion happens regardless of
        # install policy — discovery-only bundles stay inspectable; only
        # `install` is refused. But if the manifest itself can't be resolved
        # (e.g. --offline against an https:// download_url, or a download
        # failure), fail loudly and exit non-zero rather than silently
        # degrading to catalog `provides` counts, so users never mistake an
        # unverifiable bundle for a known/installable one.
        manifest = _download_manifest(resolved, offline=offline)
    except BundlerError as exc:
        _fail(str(exc))
        return

    overlaps = _bundle_overlaps(project_root, manifest, offline=offline)
    components = _manifest_component_view(manifest)

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


def _manifest_component_view(manifest) -> list[dict]:
    """Flatten a manifest's components to JSON-friendly dicts (id, version, ...)."""
    if manifest is None:
        return []
    view: list[dict] = []
    for component in manifest.components:
        item = {
            "kind": component.kind,
            "id": component.id,
            "version": component.version,
        }
        if component.priority is not None:
            item["priority"] = component.priority
        if component.strategy is not None:
            item["strategy"] = component.strategy
        view.append(item)
    return view


def _format_component(item: dict) -> str:
    label = f"{item['id']} v{item['version']}" if item.get("version") else item["id"]
    extras = []
    if item.get("priority") is not None:
        extras.append(f"priority={item['priority']}")
    if item.get("strategy") is not None:
        extras.append(f"strategy={item['strategy']}")
    if extras:
        label += f" ({', '.join(extras)})"
    return label
