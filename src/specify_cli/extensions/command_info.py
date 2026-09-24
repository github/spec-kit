"""Implementation and private helpers for ``specify extension info``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from . import _commands


@_commands.extension_app.command("info")
def extension_info(
    extension: str = typer.Argument(help="Extension ID or name"),
    versions: bool = typer.Option(False, "--versions", help="List catalog versions"),
):
    """Show detailed information about an extension."""
    from . import ExtensionCatalog, ExtensionManager, ExtensionError, normalize_priority

    project_root = _commands._require_specify_project()
    catalog = ExtensionCatalog(project_root)
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    # Try to resolve from installed extensions first (by ID or name)
    # Use allow_not_found=True since the extension may be catalog-only
    resolved_installed_id, resolved_installed_name = _commands._resolve_installed_extension(
        extension, installed, "info", allow_not_found=True
    )

    # Try catalog lookup (with error handling)
    # If we resolved an installed extension by display name, use its ID for catalog lookup
    # to ensure we get the correct catalog entry (not a different extension with same name)
    lookup_key = resolved_installed_id if resolved_installed_id else extension
    ext_info, catalog_error = _commands._resolve_catalog_extension(
        lookup_key, catalog, "info"
    )
    # Direct compatibility callers receive Typer's OptionInfo default rather
    # than a parsed bool; only the CLI's explicit True enables this view.
    show_versions = versions is True

    # Case 1: Found in catalog - show full catalog info
    if ext_info:
        if show_versions:
            try:
                available = catalog.get_extension_versions(ext_info["id"])
            except ExtensionError as exc:
                _commands.console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
                raise typer.Exit(1) from exc
            _commands.console.print(
                f"Catalog versions for {_escape_markup(str(ext_info['id']))}:"
            )
            for index, available_version in enumerate(available):
                current = " (current)" if index == 0 else ""
                _commands.console.print(f"  {_escape_markup(available_version)}{current}")
            if not ext_info.get("_install_allowed", True):
                _commands.console.print("[yellow]Discovery only; catalog installation is disabled.[/yellow]")
            return
        _print_extension_info(ext_info, manager)
        return

    if show_versions:
        _commands.console.print(
            f"[red]Error:[/red] No catalog versions found for {_escape_markup(extension)}."
        )
        raise typer.Exit(1)

    # Case 2: Installed locally but catalog lookup failed or not in catalog
    if resolved_installed_id:
        # Get local manifest info
        ext_manifest = manager.get_extension(resolved_installed_id)
        metadata = manager.registry.get(resolved_installed_id)
        metadata_is_dict = isinstance(metadata, dict)
        if not metadata_is_dict:
            _commands.console.print(
                "[yellow]Warning:[/yellow] Extension metadata appears to be corrupted; "
                "some information may be unavailable."
            )
        version = metadata.get("version", "unknown") if metadata_is_dict else "unknown"

        _commands.console.print(f"\n[bold]{_escape_markup(str(resolved_installed_name))}[/bold] (v{_escape_markup(str(version))})")
        _commands.console.print(f"ID: {_escape_markup(str(resolved_installed_id))}")
        _commands.console.print()

        if ext_manifest:
            _commands.console.print(f"{_escape_markup(str(ext_manifest.description))}")
            _commands.console.print()
            # Author is optional in extension.yml, safely retrieve it
            author = ext_manifest.data.get("extension", {}).get("author")
            if author:
                _commands.console.print(f"[dim]Author:[/dim] {_escape_markup(str(author))}")
            if ext_manifest.category:
                _commands.console.print(f"[dim]Category:[/dim] {_escape_markup(str(ext_manifest.category))}")
            if ext_manifest.effect:
                _commands.console.print(f"[dim]Effect:[/dim] {_escape_markup(str(ext_manifest.effect))}")
            _commands.console.print()

            if ext_manifest.commands:
                # Print each command the way the active agent registers it.
                # Cline and Forge hyphenate command names (e.g. Forge invokes
                # `/speckit-jira-sync`, not the manifest's dotted
                # `speckit.jira.sync`), so mirror the same formatting used by
                # `extension add`'s "Provided commands" listing — otherwise the
                # names shown here don't match what the user actually types.
                selected_ai = _commands.load_init_options(project_root).get("ai")
                if selected_ai == "cline":
                    from specify_cli.integrations.cline import (
                        format_cline_command_name as _format_command_name,
                    )
                elif selected_ai == "forge":
                    from specify_cli.integrations.forge import (
                        format_forge_command_name as _format_command_name,
                    )
                else:
                    _format_command_name = None

                _commands.console.print("[bold]Commands:[/bold]")
                for cmd in ext_manifest.commands:
                    cmd_name = cmd['name']
                    if _format_command_name is not None:
                        cmd_name = _format_command_name(cmd_name)
                    _commands.console.print(f"  • {_escape_markup(str(cmd_name))}: {_escape_markup(str(cmd.get('description', '')))}")
                _commands.console.print()

        # Show catalog status
        if catalog_error:
            _commands.console.print(f"[yellow]Catalog unavailable:[/yellow] {_escape_markup(str(catalog_error))}")
            _commands.console.print("[dim]Note: Using locally installed extension; catalog info could not be verified.[/dim]")
        else:
            _commands.console.print("[yellow]Note:[/yellow] Not found in catalog (custom/local extension)")

        _commands.console.print()
        _commands.console.print("[green]✓ Installed[/green]")
        priority = normalize_priority(metadata.get("priority") if metadata_is_dict else None)
        _commands.console.print(f"[dim]Priority:[/dim] {priority}")
        _commands.console.print(f"\nTo remove: specify extension remove {_escape_markup(str(resolved_installed_id))}")
        return

    # Case 3: Not found anywhere
    if catalog_error:
        _commands.console.print(f"[red]Error:[/red] Could not query extension catalog: {_escape_markup(str(catalog_error))}")
        _commands.console.print("\nTry again when online, or use the extension ID directly.")
    else:
        _commands.console.print(f"[red]Error:[/red] Extension '{_escape_markup(extension)}' not found")
        _commands.console.print("\nTry: specify extension search")
    raise typer.Exit(1)


def _print_extension_info(ext_info: dict, manager):
    """Print formatted extension info from catalog data."""
    from . import normalize_priority

    # Header
    verified_badge = " [green]✓ Verified[/green]" if ext_info.get("verified") else ""
    _commands.console.print(f"\n[bold]{_escape_markup(str(ext_info['name']))}[/bold] (v{_escape_markup(str(ext_info['version']))}){verified_badge}")
    _commands.console.print(f"ID: {_escape_markup(str(ext_info['id']))}")
    _commands.console.print()

    # Description
    _commands.console.print(f"{_escape_markup(str(ext_info['description']))}")
    _commands.console.print()

    # Author and License
    _commands.console.print(f"[dim]Author:[/dim] {_escape_markup(str(ext_info.get('author', 'Unknown')))}")
    _commands.console.print(f"[dim]License:[/dim] {_escape_markup(str(ext_info.get('license', 'Unknown')))}")

    # Category and Effect
    if ext_info.get('category'):
        _commands.console.print(f"[dim]Category:[/dim] {_escape_markup(str(ext_info['category']))}")
    if ext_info.get('effect'):
        _commands.console.print(f"[dim]Effect:[/dim] {_escape_markup(str(ext_info['effect']))}")

    # Source catalog
    if ext_info.get("_catalog_name"):
        install_allowed = ext_info.get("_install_allowed", True)
        install_note = "" if install_allowed else " [yellow](discovery only)[/yellow]"
        _commands.console.print(f"[dim]Source catalog:[/dim] {_escape_markup(str(ext_info['_catalog_name']))}{install_note}")
    _commands.console.print()

    # Requirements
    if ext_info.get('requires'):
        _commands.console.print("[bold]Requirements:[/bold]")
        reqs = ext_info['requires']
        if reqs.get('speckit_version'):
            _commands.console.print(f"  • Spec Kit: {_escape_markup(str(reqs['speckit_version']))}")
        if reqs.get('tools'):
            for tool in reqs['tools']:
                tool_name = _escape_markup(str(tool['name']))
                tool_version = _escape_markup(str(tool.get('version', 'any')))
                required = " (required)" if tool.get('required') else " (optional)"
                _commands.console.print(f"  • {tool_name}: {tool_version}{required}")
        _commands.console.print()

    # Provides
    if ext_info.get('provides'):
        _commands.console.print("[bold]Provides:[/bold]")
        provides = ext_info['provides']
        if provides.get('commands'):
            _commands.console.print(f"  • Commands: {_escape_markup(str(provides['commands']))}")
        if provides.get('hooks'):
            _commands.console.print(f"  • Hooks: {_escape_markup(str(provides['hooks']))}")
        _commands.console.print()

    # Tags
    info_tags = ext_info.get('tags', [])
    if isinstance(info_tags, list) and info_tags:
        tags_str = ", ".join(str(t) for t in info_tags)
        _commands.console.print(f"[bold]Tags:[/bold] {_escape_markup(tags_str)}")
        _commands.console.print()

    # Statistics
    stats = []
    downloads = ext_info.get('downloads')
    if downloads is not None:
        # Catalog fields are untrusted; a non-numeric ``downloads`` (e.g. the
        # JSON string "1500") would crash the ``:,`` format with "Cannot
        # specify ',' with 's'". Only group-format numbers, and escape the
        # fallback: the joined stats are rendered as Rich markup, so a value
        # like "[/red]foo" would raise MarkupError (matching how every other
        # catalog field here is escaped).
        stats.append(
            f"Downloads: {downloads:,}"
            if isinstance(downloads, (int, float))
            else f"Downloads: {_escape_markup(str(downloads))}"
        )
    stars = ext_info.get('stars')
    if stars is not None:
        # Same untrusted-value/Rich-markup hazard as `downloads` above, in the
        # same joined string.
        stats.append(f"Stars: {_escape_markup(str(stars))}")
    if stats:
        _commands.console.print(f"[bold]Statistics:[/bold] {' | '.join(stats)}")
        _commands.console.print()

    # Links
    _commands.console.print("[bold]Links:[/bold]")
    if ext_info.get('repository'):
        _commands.console.print(f"  • Repository: {_escape_markup(str(ext_info['repository']))}")
    if ext_info.get('homepage'):
        _commands.console.print(f"  • Homepage: {_escape_markup(str(ext_info['homepage']))}")
    if ext_info.get('documentation'):
        _commands.console.print(f"  • Documentation: {_escape_markup(str(ext_info['documentation']))}")
    if ext_info.get('changelog'):
        _commands.console.print(f"  • Changelog: {_escape_markup(str(ext_info['changelog']))}")
    _commands.console.print()

    # Installation status and command
    is_installed = manager.registry.is_installed(ext_info['id'])
    install_allowed = ext_info.get("_install_allowed", True)
    safe_id = _escape_markup(str(ext_info['id']))
    cmd_id = _commands._command_safe_id(ext_info['id'])
    if is_installed:
        _commands.console.print("[green]✓ Installed[/green]")
        metadata = manager.registry.get(ext_info['id'])
        priority = normalize_priority(metadata.get("priority") if isinstance(metadata, dict) else None)
        _commands.console.print(f"[dim]Priority:[/dim] {priority}")
        _commands.console.print(f"\nTo remove: specify extension remove {cmd_id}")
    elif install_allowed:
        _commands.console.print("[yellow]Not installed[/yellow]")
        _commands.console.print(f"\n[cyan]Install:[/cyan] specify extension add {cmd_id}")
    else:
        catalog_name = _escape_markup(str(ext_info.get("_catalog_name", "community")))
        _commands.console.print("[yellow]Not installed[/yellow]")
        _commands.console.print(
            f"\n[yellow]⚠[/yellow]  '{safe_id}' is in the '{catalog_name}' catalog, which is "
            f"discovery-only (a search surface, not an install source)."
        )
        download_url = ext_info.get("download_url")
        if download_url:
            _commands.console.print(
                f"Candidate archive (vet before installing): {_escape_markup(str(download_url))}"
            )
            _commands.console.print(
                f"Once vetted, install directly: specify extension add {cmd_id} --from <archive-url>"
            )
        else:
            _commands.console.print(
                f"Once you've vetted its release archive, install directly: "
                f"specify extension add {cmd_id} --from <archive-url>"
            )
        _commands.console.print(
            "Discovery-only catalogs are intentionally not install sources — don't set "
            "install_allowed on them."
        )
