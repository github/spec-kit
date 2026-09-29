"""Implementation of the ``specify preset info`` command."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from ._commands import preset_app


def _diagnostic_selector_matches(resolver, preset_dir, selector, resource_type):
    import os
    from ._selectors import is_regex_selector, selector_matches

    ordered_presets = resolver._get_all_presets_by_priority()
    try:
        current_index = next(
            index
            for index, (preset_id, _meta) in enumerate(ordered_presets)
            if preset_id == preset_dir.name
        )
    except StopIteration:
        return []
    lower_presets = [
        resolver.presets_dir / preset_id
        for preset_id, _meta in ordered_presets[current_index + 1 :]
    ]
    lower_extensions = [
        resolver.extensions_dir / ext_id
        for _priority, ext_id, _meta in resolver._get_all_extensions_by_priority()
    ]
    candidates = set()
    for base in [*lower_presets, *lower_extensions]:
        if base.parent == resolver.presets_dir:
            manifest = resolver._get_manifest(base)
            declarations = manifest.templates if manifest is not None else []
        else:
            from ..extensions import ExtensionManifest

            manifest_path = base / "extension.yml"
            try:
                manifest = (
                    ExtensionManifest(manifest_path)
                    if manifest_path.is_file()
                    else None
                )
            except Exception:
                manifest = None
            declarations = []
            if manifest is not None:
                provides = manifest.data.get("provides", {})
                key = {"template": "templates", "script": "scripts"}.get(resource_type)
                declarations = provides.get(key, []) if key else []
        candidates.update(
            item["name"]
            for item in declarations
            if isinstance(item, dict)
            and item.get("type", resource_type) == resource_type
            and isinstance(item.get("name"), str)
            and not is_regex_selector(item["name"])
        )
        subdir = "templates" if resource_type == "template" else "scripts"
        suffix = ".sh" if resource_type == "script" else ".md"
        root = base / subdir
        for path in root.glob("**/*") if root.is_dir() else []:
            if path.is_file() and path.name.endswith(suffix):
                candidates.add(
                    os.path.relpath(path, root)[: -len(suffix)].replace(os.sep, "-")
                )
    suffix = ".sh" if resource_type == "script" else ".md"
    core_roots = [
        resolver.templates_dir / ("scripts" if resource_type == "script" else ""),
    ]
    for root in core_roots:
        for path in root.glob("**/*") if root.is_dir() else []:
            if path.is_file() and path.name.endswith(suffix):
                candidates.add(
                    os.path.relpath(path, root)[: -len(suffix)].replace(os.sep, "-")
                )
    matches = []
    for name in candidates:
        if (
            not isinstance(name, str)
            or is_regex_selector(name)
            or not selector_matches(selector, name)
        ):
            continue
        exists = (
            any(
                resolver._has_concrete_resource(base, name, resource_type)
                for base in lower_presets
            )
            or any(
                resolver._has_concrete_resource(
                    base, name, resource_type, is_extension=True
                )
                for base in lower_extensions
            )
            or resolver._core_has_concrete_resource(name, resource_type)
        )
        if exists:
            matches.append(name)
    return sorted(matches)


@preset_app.command("info")
def preset_info(
    preset_id: str = typer.Argument(..., help="Preset ID to get info about"),
):
    """Show detailed information about a preset."""
    from .. import _require_specify_project
    from ..extensions import normalize_priority
    from . import PresetCatalog, PresetError, PresetManager

    project_root = _require_specify_project()
    safe_preset_id = _escape_markup(str(preset_id))
    # Check if installed locally first
    manager = PresetManager(project_root)
    local_pack = manager.get_pack(preset_id)

    if local_pack:
        console.print(
            f"\n[bold cyan]Preset: {_escape_markup(str(local_pack.name))}[/bold cyan]\n"
        )
        console.print(f"  ID:          {_escape_markup(str(local_pack.id))}")
        console.print(f"  Version:     {_escape_markup(str(local_pack.version))}")
        console.print(f"  Description: {_escape_markup(str(local_pack.description))}")
        if local_pack.author:
            console.print(f"  Author:      {_escape_markup(str(local_pack.author))}")
        local_tags = local_pack.tags
        if isinstance(local_tags, list) and local_tags:
            tags_str = _escape_markup(", ".join(str(t) for t in local_tags))
            console.print(f"  Tags:        {tags_str}")
        from ._selectors import is_regex_selector
        from ._resolver import PresetResolver

        resolver = PresetResolver(project_root)
        preset_dir = manager.presets_dir / local_pack.id
        for tmpl in local_pack.templates:
            tmpl_name = _escape_markup(str(tmpl["name"]))
            tmpl_type = _escape_markup(str(tmpl["type"]))
            tmpl_desc = _escape_markup(str(tmpl.get("description", "")))
            console.print(f"    - {tmpl_name} ({tmpl_type}): {tmpl_desc}")
            if (
                tmpl.get("type") == "command"
                and isinstance(tmpl.get("name"), str)
                and is_regex_selector(tmpl["name"])
            ):
                matches = manager._expand_command_selectors(
                    resolver, preset_dir, [tmpl]
                )
            elif (
                tmpl.get("type") in {"template", "script"}
                and isinstance(tmpl.get("name"), str)
                and is_regex_selector(tmpl["name"])
            ):
                matches = [
                    {"name": name}
                    for name in _diagnostic_selector_matches(
                        resolver, preset_dir, tmpl["name"], tmpl["type"]
                    )
                ]
            else:
                matches = []
            if is_regex_selector(str(tmpl.get("name", ""))):
                if matches:
                    for match in matches:
                        console.print(f"      - {_escape_markup(str(match['name']))}")
                else:
                    console.print("      [dim]No current matches[/dim]")
        repo = local_pack.data.get("preset", {}).get("repository")
        if repo:
            console.print(f"  Repository:  {_escape_markup(str(repo))}")
        license_val = local_pack.data.get("preset", {}).get("license")
        if license_val:
            console.print(f"  License:     {_escape_markup(str(license_val))}")
        console.print("\n  [green]Status: installed[/green]")
        # Get priority from registry
        pack_metadata = manager.registry.get(preset_id)
        priority = normalize_priority(
            pack_metadata.get("priority") if isinstance(pack_metadata, dict) else None
        )
        console.print(f"  [dim]Priority:[/dim] {priority}")
        console.print()
        return

    # Fall back to catalog
    catalog = PresetCatalog(project_root)
    try:
        pack_info = catalog.get_pack_info(preset_id)
    except PresetError:
        pack_info = None

    if not pack_info:
        console.print(
            f"[red]Error:[/red] Preset '{preset_id}' not found (not installed and not in catalog)"
        )
        raise typer.Exit(1)

    name = _escape_markup(str(pack_info.get("name", preset_id)))
    console.print(f"\n[bold cyan]Preset: {name}[/bold cyan]\n")
    console.print(f"  ID:          {_escape_markup(str(pack_info['id']))}")
    console.print(
        f"  Version:     {_escape_markup(str(pack_info.get('version', '?')))}"
    )
    console.print(
        f"  Description: {_escape_markup(str(pack_info.get('description', '')))}"
    )
    if pack_info.get("author"):
        console.print(f"  Author:      {_escape_markup(str(pack_info['author']))}")
    catalog_tags = pack_info.get("tags", [])
    if isinstance(catalog_tags, list) and catalog_tags:
        catalog_tags_str = _escape_markup(", ".join(str(t) for t in catalog_tags))
        console.print(f"  Tags:        {catalog_tags_str}")
    if pack_info.get("repository"):
        console.print(f"  Repository:  {_escape_markup(str(pack_info['repository']))}")
    if pack_info.get("license"):
        console.print(f"  License:     {_escape_markup(str(pack_info['license']))}")
    console.print("\n  [yellow]Status: not installed[/yellow]")
    console.print(f"  Install with: [cyan]specify preset add {safe_preset_id}[/cyan]")
    console.print()
