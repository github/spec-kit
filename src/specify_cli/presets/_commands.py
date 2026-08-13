"""specify preset * command handlers — app objects and register() entry point.

Moved out of __init__.py (PR-6/8). Handlers reference helpers that remain in
the package root (`_require_specify_project`, `get_speckit_version`,
`_locate_bundled_preset`, `_display_project_path`) via lazy `from .. import`
calls inside each function so test monkeypatching of `specify_cli.<helper>`
keeps working.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import typer
import yaml
from rich.markup import escape as _escape_markup

from .._console import console
from .._download_security import (
    archive_format_from_name,
    archive_suffix,
    detect_archive_format,
    is_https_or_localhost_http,
    is_safe_download_redirect,
    read_response_limited,
)

preset_app = typer.Typer(
    name="preset",
    help="Manage spec-kit presets",
    add_completion=False,
)

preset_catalog_app = typer.Typer(
    name="catalog",
    help="Manage preset catalogs",
    add_completion=False,
)
preset_app.add_typer(preset_catalog_app, name="catalog")


# ===== Preset Commands =====


@preset_app.command("list")
def preset_list():
    """List installed presets."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    manager = PresetManager(project_root)
    installed = manager.list_installed()

    if not installed:
        console.print("[yellow]No presets installed.[/yellow]")
        console.print("\nInstall a preset with:")
        console.print("  [cyan]specify preset add <pack-name>[/cyan]")
        return

    # Sort by actual resolution precedence: lower priority number wins, ties
    # broken by preset id (matching PresetRegistry.list_by_priority()). This
    # keeps the printed order aligned with how presets are composed/resolved.
    installed = sorted(
        installed,
        key=lambda pack: (pack.get("priority", 10), str(pack.get("id", ""))),
    )

    console.print("\n[bold cyan]Installed Presets[/bold cyan] [dim](in resolution order — highest precedence first)[/dim]\n")
    for pack in installed:
        status = "[green]enabled[/green]" if pack.get("enabled", True) else "[red]disabled[/red]"
        pri = pack.get('priority', 10)
        name = _escape_markup(str(pack['name']))
        pack_id = _escape_markup(str(pack['id']))
        version = _escape_markup(str(pack['version']))
        console.print(f"  [bold]{name}[/bold] ({pack_id}) v{version} — {status} — priority {pri}")
        console.print(f"    {_escape_markup(str(pack['description']))}")
        tags = pack.get("tags", [])
        if isinstance(tags, list) and tags:
            tags_str = _escape_markup(", ".join(str(t) for t in tags))
            console.print(f"    [dim]Tags: {tags_str}[/dim]")
        console.print(f"    [dim]Templates: {pack['template_count']}[/dim]")
        console.print()

    console.print("[dim]Lower priority number = higher precedence. Ties are broken by preset id (alphabetical).[/dim]")


@preset_app.command("add")
def preset_add(
    preset_id: str = typer.Argument(None, help="Preset ID to install from catalog"),
    from_url: str = typer.Option(
        None,
        "--from",
        help="Install from a .zip, .tar.gz, or .tgz URL",
    ),
    dev: str = typer.Option(None, "--dev", help="Install from local directory (development mode)"),
    priority: int = typer.Option(10, "--priority", help="Resolution priority (lower = higher precedence, default 10)"),
):
    """Install a preset."""
    from .. import _locate_bundled_preset, _require_specify_project, get_speckit_version
    from . import (
        PresetManager,
        PresetCatalog,
        PresetError,
        PresetValidationError,
        PresetCompatibilityError,
    )

    project_root = _require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = PresetManager(project_root)
    speckit_version = get_speckit_version()

    try:
        if dev:
            dev_path = Path(dev).resolve()
            if not dev_path.exists():
                console.print(f"[red]Error:[/red] Directory not found: {dev}")
                raise typer.Exit(1)

            console.print(f"Installing preset from [cyan]{dev_path}[/cyan]...")
            manifest = manager.install_from_directory(dev_path, speckit_version, priority)
            console.print(f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})")

        elif from_url:
            # Validate URL scheme before downloading
            from urllib.parse import urlparse as _urlparse

            try:
                _parsed = _urlparse(from_url)
                _parsed.port
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(from_url)}")
                raise typer.Exit(1)

            def _validate_download_redirect(old_url, new_url):
                if not is_safe_download_redirect(old_url, new_url):
                    import urllib.error

                    raise urllib.error.URLError(
                        "redirect target must use HTTPS without entering a local "
                        "target, or stay within loopback over HTTP"
                    )

            if not is_https_or_localhost_http(from_url):
                console.print(
                    "[red]Error:[/red] URL must use HTTPS with a hostname and be "
                    "a valid URL with a host. HTTP is only allowed for localhost, "
                    "127.0.0.1, and ::1."
                )
                raise typer.Exit(1)

            console.print(f"Installing preset from [cyan]{_escape_markup(from_url)}[/cyan]...")
            import urllib.error
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                archive_path = Path(tmpdir) / "preset.archive"
                try:
                    from specify_cli.authentication.http import open_url as _open_url
                    from specify_cli.authentication.http import github_provider_hosts
                    from specify_cli._github_http import resolve_github_release_asset_api_url

                    _preset_extra_headers = None
                    _resolved_from_url = resolve_github_release_asset_api_url(
                        from_url, _open_url, github_hosts=github_provider_hosts()
                    )
                    if _resolved_from_url:
                        from_url = _resolved_from_url
                        _preset_extra_headers = {"Accept": "application/octet-stream"}

                    with _open_url(
                        from_url,
                        timeout=60,
                        extra_headers=_preset_extra_headers,
                        redirect_validator=_validate_download_redirect,
                    ) as response:
                        final_url = response.geturl() if hasattr(response, "geturl") else from_url
                        if not is_https_or_localhost_http(final_url):
                            console.print(
                                "[red]Error:[/red] Preset URL redirected to a disallowed URL: "
                                f"{final_url}. Redirect targets must use HTTPS with a hostname, "
                                "or HTTP for localhost (127.0.0.1, ::1)."
                            )
                            raise typer.Exit(1)
                        archive_data = read_response_limited(
                            response,
                            error_type=PresetError,
                            label=f"preset {from_url}",
                        )
                        content_type = (
                            response.getheader("Content-Type")
                            if hasattr(response, "getheader")
                            else None
                        )
                    archive_path.write_bytes(archive_data)
                    format_source = (
                        final_url
                        if archive_format_from_name(final_url) is not None
                        else from_url
                    )
                    archive_format = detect_archive_format(
                        archive_path,
                        source_name=format_source,
                        content_type=content_type,
                        error_type=PresetError,
                    )
                    detected_path = archive_path.with_suffix(
                        archive_suffix(archive_format)
                    )
                    os.replace(archive_path, detected_path)
                    archive_path = detected_path
                except (urllib.error.URLError, PresetError) as e:
                    console.print(
                        f"[red]Error:[/red] Failed to download: "
                        f"{_escape_markup(str(e))}"
                    )
                    raise typer.Exit(1)

                manifest = manager.install_from_zip(
                    archive_path,
                    speckit_version,
                    priority,
                )

            console.print(f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})")

        elif preset_id:
            # Try bundled preset first, then catalog
            bundled_path = _locate_bundled_preset(preset_id)
            if bundled_path:
                console.print(f"Installing bundled preset [cyan]{preset_id}[/cyan]...")
                manifest = manager.install_from_directory(bundled_path, speckit_version, priority)
                console.print(f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})")
            else:
                catalog = PresetCatalog(project_root)
                pack_info = catalog.get_pack_info(preset_id)

                if not pack_info:
                    console.print(f"[red]Error:[/red] Preset '{preset_id}' not found in catalog")
                    raise typer.Exit(1)

                # Bundled presets should have been caught above; if we reach
                # here the bundled files are missing from the installation.
                if pack_info.get("bundled") and not pack_info.get("download_url"):
                    from ..extensions import REINSTALL_COMMAND
                    console.print(
                        f"[red]Error:[/red] Preset '{preset_id}' is bundled with spec-kit "
                        f"but could not be found in the installed package."
                    )
                    console.print(
                        "\nThis usually means the spec-kit installation is incomplete or corrupted."
                    )
                    console.print("Try reinstalling spec-kit:")
                    console.print(f"  {REINSTALL_COMMAND}")
                    raise typer.Exit(1)

                if not pack_info.get("_install_allowed", True):
                    catalog_name = pack_info.get("_catalog_name", "unknown")
                    console.print(f"[red]Error:[/red] Preset '{preset_id}' is from the '{catalog_name}' catalog which is discovery-only (install not allowed).")
                    console.print("Add the catalog with --install-allowed or install from the preset's repository directly with --from.")
                    raise typer.Exit(1)

                console.print(f"Installing preset [cyan]{pack_info.get('name', preset_id)}[/cyan]...")

                try:
                    archive_path = catalog.download_pack(preset_id)
                    manifest = manager.install_from_zip(
                        archive_path,
                        speckit_version,
                        priority,
                    )
                    console.print(f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})")
                finally:
                    if 'archive_path' in locals() and archive_path.exists():
                        archive_path.unlink(missing_ok=True)
        else:
            console.print("[red]Error:[/red] Specify a preset ID, --from URL, or --dev path")
            raise typer.Exit(1)

    except PresetCompatibilityError as e:
        console.print(f"[red]Compatibility Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except PresetValidationError as e:
        console.print(f"[red]Validation Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except PresetError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)


@preset_app.command("remove")
def preset_remove(
    preset_id: str = typer.Argument(..., help="Preset ID to remove"),
):
    """Remove an installed preset."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    manager = PresetManager(project_root)

    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    if manager.remove(preset_id):
        console.print(f"[green]✓[/green] Preset '{preset_id}' removed successfully")
    else:
        console.print(f"[red]Error:[/red] Failed to remove preset '{preset_id}'")
        raise typer.Exit(1)


@preset_app.command("search")
def preset_search(
    query: str = typer.Argument(None, help="Search query"),
    tag: str = typer.Option(None, "--tag", help="Filter by tag"),
    author: str = typer.Option(None, "--author", help="Filter by author"),
):
    """Search for presets in the catalog."""
    from .. import _require_specify_project
    from . import PresetCatalog, PresetError

    project_root = _require_specify_project()
    catalog = PresetCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag, author=author)
    except PresetError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    if not results:
        console.print("[yellow]No presets found matching your criteria.[/yellow]")
        return

    console.print(f"\n[bold cyan]Presets ({len(results)} found):[/bold cyan]\n")
    for pack in results:
        name = _escape_markup(str(pack.get("name", pack["id"])))
        pack_id = _escape_markup(str(pack["id"]))
        version = _escape_markup(str(pack.get("version", "?")))
        console.print(f"  [bold]{name}[/bold] ({pack_id}) v{version}")
        console.print(
            f"    {_escape_markup(str(pack.get('description', '')))}"
        )
        tags = pack.get("tags", [])
        if isinstance(tags, list) and tags:
            tags_str = _escape_markup(", ".join(str(t) for t in tags))
            console.print(f"    [dim]Tags: {tags_str}[/dim]")
        console.print()


@preset_app.command("resolve")
def preset_resolve(
    template_name: str = typer.Argument(..., help="Template name to resolve (e.g., spec-template)"),
):
    """Show which template will be resolved for a given name."""
    from .. import _require_specify_project
    from . import PresetResolver

    is_command = "." in template_name
    valid_name = (
        re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", template_name)
        if is_command
        else re.fullmatch(r"[a-z0-9-]+", template_name)
    )
    if valid_name is None:
        typer.echo(
            f"Error: invalid template name '{template_name}'; "
            "use lowercase letters, digits, and hyphens, with non-empty "
            "dot-separated segments for commands",
            err=True,
        )
        raise typer.Exit(1)

    project_root = _require_specify_project()
    resolver = PresetResolver(project_root)
    template_type = "command" if is_command else "template"

    layers = resolver.collect_all_layers(template_name, template_type)
    safe_template_name = _escape_markup(str(template_name))

    if layers:
        # Use the highest-priority layer for display because the final output
        # may be composed and may not map to resolve_with_source()'s single path.
        display_layer = layers[0]
        console.print(
            f"  [bold]{safe_template_name}[/bold]: "
            f"{_escape_markup(str(display_layer['path']))}"
        )
        console.print(
            f"    [dim](top layer from: "
            f"{_escape_markup(str(display_layer['source']))})[/dim]"
        )

        has_composition = (
            layers[0]["strategy"] != "replace"
            and any(layer["strategy"] != "replace" for layer in layers)
        )
        if has_composition:
            # Verify composition is actually possible
            try:
                composed = resolver.resolve_content(template_name, template_type)
            except Exception as exc:
                composed = None
                console.print(
                    f"    [yellow]Warning: composition error: "
                    f"{_escape_markup(str(exc))}[/yellow]"
                )
            if composed is None:
                console.print("    [yellow]Warning: composition cannot produce output (no base layer with 'replace' strategy)[/yellow]")
            else:
                console.print("    [dim]Final output is composed from multiple preset layers; the path above is the highest-priority contributing layer.[/dim]")
            console.print("\n  [bold]Composition chain:[/bold]")
            # Compute the effective base: first replace layer scanning from
            # highest priority (matching resolve_content top-down logic).
            # Only show layers from the base upward (lower layers are ignored).
            effective_base_idx = None
            for idx, lyr in enumerate(layers):
                if lyr["strategy"] == "replace":
                    effective_base_idx = idx
                    break
            # Show only contributing layers (base and above)
            if effective_base_idx is not None:
                contributing = layers[:effective_base_idx + 1]
            else:
                contributing = layers
            for i, layer in enumerate(reversed(contributing)):
                strategy_label = layer["strategy"]
                if strategy_label == "replace" and i == 0:
                    strategy_label = "base"
                # Escape the literal bracket (\[) so Rich renders `[<strategy>]`
                # instead of parsing it as a style tag and swallowing the label,
                # mirroring `workflow info`'s step-graph line.
                console.print(
                    f"    {i + 1}. \\[{_escape_markup(str(strategy_label))}] "
                    f"{_escape_markup(str(layer['source']))} → "
                    f"{_escape_markup(str(layer['path']))}"
                )
    else:
        # No layers found — fall back to resolve_with_source for non-composition cases
        result = resolver.resolve_with_source(template_name, template_type)
        if result:
            console.print(
                f"  [bold]{safe_template_name}[/bold]: "
                f"{_escape_markup(str(result['path']))}"
            )
            console.print(
                f"    [dim](from: {_escape_markup(str(result['source']))})[/dim]"
            )
        else:
            console.print(f"  [yellow]{safe_template_name}[/yellow]: not found")
            console.print("    [dim]No template with this name exists in the resolution stack[/dim]")


@preset_app.command("info")
def preset_info(
    preset_id: str = typer.Argument(..., help="Preset ID to get info about"),
):
    """Show detailed information about a preset."""
    from .. import _require_specify_project
    from ..extensions import normalize_priority
    from . import PresetCatalog, PresetManager, PresetError

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
        console.print(
            f"  Description: {_escape_markup(str(local_pack.description))}"
        )
        if local_pack.author:
            console.print(f"  Author:      {_escape_markup(str(local_pack.author))}")
        local_tags = local_pack.tags
        if isinstance(local_tags, list) and local_tags:
            tags_str = _escape_markup(", ".join(str(t) for t in local_tags))
            console.print(f"  Tags:        {tags_str}")
        console.print(f"  Templates:   {len(local_pack.templates)}")
        for tmpl in local_pack.templates:
            tmpl_name = _escape_markup(str(tmpl['name']))
            tmpl_type = _escape_markup(str(tmpl['type']))
            tmpl_desc = _escape_markup(str(tmpl.get('description', '')))
            console.print(f"    - {tmpl_name} ({tmpl_type}): {tmpl_desc}")
        repo = local_pack.data.get("preset", {}).get("repository")
        if repo:
            console.print(f"  Repository:  {_escape_markup(str(repo))}")
        license_val = local_pack.data.get("preset", {}).get("license")
        if license_val:
            console.print(f"  License:     {_escape_markup(str(license_val))}")
        console.print("\n  [green]Status: installed[/green]")
        # Get priority from registry
        pack_metadata = manager.registry.get(preset_id)
        priority = normalize_priority(pack_metadata.get("priority") if isinstance(pack_metadata, dict) else None)
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
        console.print(f"[red]Error:[/red] Preset '{preset_id}' not found (not installed and not in catalog)")
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
        console.print(
            f"  Author:      {_escape_markup(str(pack_info['author']))}"
        )
    catalog_tags = pack_info.get("tags", [])
    if isinstance(catalog_tags, list) and catalog_tags:
        catalog_tags_str = _escape_markup(", ".join(str(t) for t in catalog_tags))
        console.print(f"  Tags:        {catalog_tags_str}")
    if pack_info.get("repository"):
        console.print(
            f"  Repository:  {_escape_markup(str(pack_info['repository']))}"
        )
    if pack_info.get("license"):
        console.print(
            f"  License:     {_escape_markup(str(pack_info['license']))}"
        )
    console.print("\n  [yellow]Status: not installed[/yellow]")
    console.print(f"  Install with: [cyan]specify preset add {safe_preset_id}[/cyan]")
    console.print()


@preset_app.command("set-priority")
def preset_set_priority(
    preset_id: str = typer.Argument(help="Preset ID"),
    priority: int = typer.Argument(help="New priority (lower = higher precedence)"),
):
    """Set the resolution priority of an installed preset."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = PresetManager(project_root)

    # Check if preset is installed
    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    # Get current metadata
    metadata = manager.registry.get(preset_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' not found in registry (corrupted state)")
        raise typer.Exit(1)

    from ..extensions import normalize_priority
    raw_priority = metadata.get("priority")
    # Only skip if the stored value is already a valid int equal to requested priority
    # This ensures corrupted values (e.g., "high") get repaired even when setting to default (10)
    # A bool is an int in Python (isinstance(True, int) is True), so exclude it explicitly —
    # mirroring normalize_priority's bool guard — otherwise a corrupted True/False priority
    # equals 1/0 here and is never repaired.
    if (
        isinstance(raw_priority, int)
        and not isinstance(raw_priority, bool)
        and raw_priority == priority
    ):
        console.print(f"[yellow]Preset '{preset_id}' already has priority {priority}[/yellow]")
        raise typer.Exit(0)

    old_priority = normalize_priority(raw_priority)

    # Update priority
    manager.registry.update(preset_id, {"priority": priority})
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after changing priority for preset {preset_id}"
    )

    console.print(f"[green]✓[/green] Preset '{preset_id}' priority changed: {old_priority} → {priority}")
    console.print("\n[dim]Lower priority = higher precedence in template resolution[/dim]")


@preset_app.command("enable")
def preset_enable(
    preset_id: str = typer.Argument(help="Preset ID to enable"),
):
    """Enable a disabled preset."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    manager = PresetManager(project_root)

    # Check if preset is installed
    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    # Get current metadata
    metadata = manager.registry.get(preset_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' not found in registry (corrupted state)")
        raise typer.Exit(1)

    if metadata.get("enabled", True):
        console.print(f"[yellow]Preset '{preset_id}' is already enabled[/yellow]")
        raise typer.Exit(0)

    # Enable the preset
    manager.registry.update(preset_id, {"enabled": True})
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after enabling preset {preset_id}"
    )

    console.print(f"[green]✓[/green] Preset '{preset_id}' enabled")
    console.print("\nTemplates from this preset will now be included in resolution.")
    console.print("[dim]Note: Previously registered commands/skills remain active.[/dim]")


@preset_app.command("disable")
def preset_disable(
    preset_id: str = typer.Argument(help="Preset ID to disable"),
):
    """Disable a preset without removing it."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    manager = PresetManager(project_root)

    # Check if preset is installed
    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    # Get current metadata
    metadata = manager.registry.get(preset_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' not found in registry (corrupted state)")
        raise typer.Exit(1)

    if not metadata.get("enabled", True):
        console.print(f"[yellow]Preset '{preset_id}' is already disabled[/yellow]")
        raise typer.Exit(0)

    # Disable the preset
    manager.registry.update(preset_id, {"enabled": False})
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after disabling preset {preset_id}"
    )

    console.print(f"[green]✓[/green] Preset '{preset_id}' disabled")
    console.print("\nTemplates from this preset will be skipped during resolution.")
    console.print("[dim]Note: Previously registered commands/skills remain active until preset removal.[/dim]")
    console.print(f"To re-enable: specify preset enable {preset_id}")


# ===== Preset Catalog Commands =====


@preset_catalog_app.command("list")
def preset_catalog_list():
    """List all active preset catalogs."""
    from .. import _display_project_path, _require_specify_project
    from . import PresetCatalog, PresetValidationError

    project_root = _require_specify_project()
    catalog = PresetCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except PresetValidationError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Active Preset Catalogs:[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]install allowed[/green]"
            if entry.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [bold]{_escape_markup(str(entry.name))}[/bold] (priority {entry.priority})")
        if entry.description:
            console.print(f"     {_escape_markup(str(entry.description))}")
        console.print(f"     URL: {_escape_markup(str(entry.url))}")
        console.print(f"     Install: {install_str}")
        console.print()

    config_path = project_root / ".specify" / "preset-catalogs.yml"
    user_config_path = Path.home() / ".specify" / "preset-catalogs.yml"
    if os.environ.get("SPECKIT_PRESET_CATALOG_URL"):
        console.print("[dim]Catalog configured via SPECKIT_PRESET_CATALOG_URL environment variable.[/dim]")
    else:
        try:
            proj_loaded = config_path.exists() and catalog._load_catalog_config(config_path) is not None
        except PresetValidationError:
            proj_loaded = False
        if proj_loaded:
            console.print(f"[dim]Config: {_display_project_path(project_root, config_path)}[/dim]")
        else:
            try:
                user_loaded = user_config_path.exists() and catalog._load_catalog_config(user_config_path) is not None
            except PresetValidationError:
                user_loaded = False
            if user_loaded:
                console.print("[dim]Config: ~/.specify/preset-catalogs.yml[/dim]")
            else:
                console.print("[dim]Using built-in default catalog stack.[/dim]")
                console.print(
                    "[dim]Add .specify/preset-catalogs.yml to customize.[/dim]"
                )


@preset_catalog_app.command("add")
def preset_catalog_add(
    url: str = typer.Argument(help="Catalog URL (must use HTTPS)"),
    name: str = typer.Option(..., "--name", help="Catalog name"),
    priority: int = typer.Option(10, "--priority", help="Priority (lower = higher priority)"),
    install_allowed: bool = typer.Option(
        False, "--install-allowed/--no-install-allowed",
        help="Allow presets from this catalog to be installed",
    ),
    description: str = typer.Option("", "--description", help="Description of the catalog"),
):
    """Add a catalog to .specify/preset-catalogs.yml."""
    from .. import _display_project_path, _require_specify_project
    from . import PresetCatalog, PresetValidationError

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Validate URL
    tmp_catalog = PresetCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except PresetValidationError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    config_path = specify_dir / "preset-catalogs.yml"

    # Load existing config
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            config_label = _display_project_path(project_root, config_path)
            console.print(f"[red]Error:[/red] Failed to read {_escape_markup(str(config_label))}: {_escape_markup(str(e))}")
            raise typer.Exit(1)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)

    # Only rendering is escaped — the raw values are what get persisted and
    # compared below, so a name containing markup still round-trips exactly.
    safe_name = _escape_markup(str(name))
    safe_url = _escape_markup(str(url))

    # Check for duplicate name
    for existing in catalogs:
        if isinstance(existing, dict) and existing.get("name") == name:
            console.print(f"[yellow]Warning:[/yellow] A catalog named '{safe_name}' already exists.")
            console.print("Use 'specify preset catalog remove' first, or choose a different name.")
            raise typer.Exit(1)

    catalogs.append({
        "name": name,
        "url": url,
        "priority": priority,
        "install_allowed": install_allowed,
        "description": description,
    })

    config["catalogs"] = catalogs
    config_path.write_text(yaml.safe_dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")

    install_label = "install allowed" if install_allowed else "discovery only"
    console.print(f"\n[green]✓[/green] Added catalog '[bold]{safe_name}[/bold]' ({install_label})")
    console.print(f"  URL: {safe_url}")
    console.print(f"  Priority: {priority}")
    config_label = _escape_markup(str(_display_project_path(project_root, config_path)))
    console.print(f"\nConfig saved to {config_label}")


@preset_catalog_app.command("remove")
def preset_catalog_remove(
    name: str = typer.Argument(help="Catalog name to remove"),
):
    """Remove a catalog from .specify/preset-catalogs.yml."""
    from .. import _require_specify_project

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    config_path = specify_dir / "preset-catalogs.yml"
    if not config_path.exists():
        console.print("[red]Error:[/red] No preset catalog config found. Nothing to remove.")
        raise typer.Exit(1)

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to read preset catalog config: {e}")
        raise typer.Exit(1)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)
    # Rendering only — the raw name drives the comparison below.
    safe_name = _escape_markup(str(name))

    original_count = len(catalogs)
    catalogs = [c for c in catalogs if isinstance(c, dict) and c.get("name") != name]

    if len(catalogs) == original_count:
        console.print(f"[red]Error:[/red] Catalog '{safe_name}' not found.")
        raise typer.Exit(1)

    config["catalogs"] = catalogs
    config_path.write_text(yaml.safe_dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")

    console.print(f"[green]✓[/green] Removed catalog '{safe_name}'")
    if not catalogs:
        console.print("\n[dim]No catalogs remain in config. Built-in defaults will be used.[/dim]")


def register(app: typer.Typer) -> None:
    """Attach the preset command group to the root Typer app."""
    app.add_typer(preset_app, name="preset")
