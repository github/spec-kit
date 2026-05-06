"""specify preset * commands."""

import os
import yaml
from pathlib import Path

import typer

from .._console import console
from .._assets import _asset_service as _svc
from .._helpers import get_speckit_version

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
def preset_list() -> None:
    """List installed presets."""
    from ..presets import PresetManager

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    manager = PresetManager(project_root)
    installed = manager.list_installed()

    if not installed:
        console.print("[yellow]No presets installed.[/yellow]")
        console.print("\nInstall a preset with:")
        console.print("  [cyan]specify preset add <pack-name>[/cyan]")
        return

    console.print("\n[bold cyan]Installed Presets:[/bold cyan]\n")
    for pack in installed:
        status = "[green]enabled[/green]" if pack.get("enabled", True) else "[red]disabled[/red]"
        pri = pack.get('priority', 10)
        console.print(f"  [bold]{pack['name']}[/bold] ({pack['id']}) v{pack['version']} — {status} — priority {pri}")
        console.print(f"    {pack['description']}")
        if pack.get("tags"):
            tags_str = ", ".join(pack["tags"])
            console.print(f"    [dim]Tags: {tags_str}[/dim]")
        console.print(f"    [dim]Templates: {pack['template_count']}[/dim]")
        console.print()


@preset_app.command("add")
def preset_add(
    preset_id: str = typer.Argument(None, help="Preset ID to install from catalog"),
    from_url: str = typer.Option(None, "--from", help="Install from a URL (ZIP file)"),
    dev: str = typer.Option(None, "--dev", help="Install from local directory (development mode)"),
    priority: int = typer.Option(10, "--priority", help="Resolution priority (lower = higher precedence, default 10)"),
) -> None:
    """Install a preset."""
    from ..presets import (
        PresetManager,
        PresetCatalog,
        PresetError,
        PresetValidationError,
        PresetCompatibilityError,
    )

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

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
            _parsed = _urlparse(from_url)
            _is_localhost = _parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if _parsed.scheme != "https" and not (_parsed.scheme == "http" and _is_localhost):
                console.print(f"[red]Error:[/red] URL must use HTTPS (got {_parsed.scheme}://). HTTP is only allowed for localhost.")
                raise typer.Exit(1)

            console.print(f"Installing preset from [cyan]{from_url}[/cyan]...")
            import urllib.request
            import urllib.error
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "preset.zip"
                try:
                    with urllib.request.urlopen(from_url, timeout=60) as response:
                        zip_path.write_bytes(response.read())
                except urllib.error.URLError as e:
                    console.print(f"[red]Error:[/red] Failed to download: {e}")
                    raise typer.Exit(1)

                manifest = manager.install_from_zip(zip_path, speckit_version, priority)

            console.print(f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})")

        elif preset_id:
            # Try bundled preset first, then catalog
            bundled_path = _svc.locate_bundled_preset(preset_id)
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
                    zip_path = catalog.download_pack(preset_id)
                    manifest = manager.install_from_zip(zip_path, speckit_version, priority)
                    console.print(f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})")
                finally:
                    if 'zip_path' in locals() and zip_path.exists():
                        zip_path.unlink(missing_ok=True)
        else:
            console.print("[red]Error:[/red] Specify a preset ID, --from URL, or --dev path")
            raise typer.Exit(1)

    except PresetCompatibilityError as e:
        console.print(f"[red]Compatibility Error:[/red] {e}")
        raise typer.Exit(1)
    except PresetValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}")
        raise typer.Exit(1)
    except PresetError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@preset_app.command("remove")
def preset_remove(
    preset_id: str = typer.Argument(..., help="Preset ID to remove"),
) -> None:
    """Remove an installed preset."""
    from ..presets import PresetManager

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

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
) -> None:
    """Search for presets in the catalog."""
    from ..presets import PresetCatalog, PresetError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    catalog = PresetCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag, author=author)
    except PresetError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not results:
        console.print("[yellow]No presets found matching your criteria.[/yellow]")
        return

    console.print(f"\n[bold cyan]Presets ({len(results)} found):[/bold cyan]\n")
    for pack in results:
        console.print(f"  [bold]{pack.get('name', pack['id'])}[/bold] ({pack['id']}) v{pack.get('version', '?')}")
        console.print(f"    {pack.get('description', '')}")
        if pack.get("tags"):
            tags_str = ", ".join(pack["tags"])
            console.print(f"    [dim]Tags: {tags_str}[/dim]")
        console.print()


@preset_app.command("resolve")
def preset_resolve(
    template_name: str = typer.Argument(..., help="Template name to resolve (e.g., spec-template)"),
) -> None:
    """Show which template will be resolved for a given name."""
    from ..presets import PresetResolver

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    resolver = PresetResolver(project_root)
    layers = resolver.collect_all_layers(template_name)

    if layers:
        # Use the highest-priority layer for display because the final output
        # may be composed and may not map to resolve_with_source()'s single path.
        display_layer = layers[0]
        console.print(f"  [bold]{template_name}[/bold]: {display_layer['path']}")
        console.print(f"    [dim](top layer from: {display_layer['source']})[/dim]")

        has_composition = (
            layers[0]["strategy"] != "replace"
            and any(layer["strategy"] != "replace" for layer in layers)
        )
        if has_composition:
            # Verify composition is actually possible
            try:
                composed = resolver.resolve_content(template_name)
            except Exception as exc:
                composed = None
                console.print(f"    [yellow]Warning: composition error: {exc}[/yellow]")
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
                console.print(f"    {i + 1}. [{strategy_label}] {layer['source']} → {layer['path']}")
    else:
        # No layers found — fall back to resolve_with_source for non-composition cases
        result = resolver.resolve_with_source(template_name)
        if result:
            console.print(f"  [bold]{template_name}[/bold]: {result['path']}")
            console.print(f"    [dim](from: {result['source']})[/dim]")
        else:
            console.print(f"  [yellow]{template_name}[/yellow]: not found")
            console.print("    [dim]No template with this name exists in the resolution stack[/dim]")


@preset_app.command("info")
def preset_info(
    preset_id: str = typer.Argument(..., help="Preset ID to get info about"),
) -> None:
    """Show detailed information about a preset."""
    from ..extensions import normalize_priority
    from ..presets import PresetCatalog, PresetManager, PresetError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    # Check if installed locally first
    manager = PresetManager(project_root)
    local_pack = manager.get_pack(preset_id)

    if local_pack:
        console.print(f"\n[bold cyan]Preset: {local_pack.name}[/bold cyan]\n")
        console.print(f"  ID:          {local_pack.id}")
        console.print(f"  Version:     {local_pack.version}")
        console.print(f"  Description: {local_pack.description}")
        if local_pack.author:
            console.print(f"  Author:      {local_pack.author}")
        if local_pack.tags:
            console.print(f"  Tags:        {', '.join(local_pack.tags)}")
        console.print(f"  Templates:   {len(local_pack.templates)}")
        for tmpl in local_pack.templates:
            console.print(f"    - {tmpl['name']} ({tmpl['type']}): {tmpl.get('description', '')}")
        repo = local_pack.data.get("preset", {}).get("repository")
        if repo:
            console.print(f"  Repository:  {repo}")
        license_val = local_pack.data.get("preset", {}).get("license")
        if license_val:
            console.print(f"  License:     {license_val}")
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

    console.print(f"\n[bold cyan]Preset: {pack_info.get('name', preset_id)}[/bold cyan]\n")
    console.print(f"  ID:          {pack_info['id']}")
    console.print(f"  Version:     {pack_info.get('version', '?')}")
    console.print(f"  Description: {pack_info.get('description', '')}")
    if pack_info.get("author"):
        console.print(f"  Author:      {pack_info['author']}")
    if pack_info.get("tags"):
        console.print(f"  Tags:        {', '.join(pack_info['tags'])}")
    if pack_info.get("repository"):
        console.print(f"  Repository:  {pack_info['repository']}")
    if pack_info.get("license"):
        console.print(f"  License:     {pack_info['license']}")
    console.print("\n  [yellow]Status: not installed[/yellow]")
    console.print(f"  Install with: [cyan]specify preset add {preset_id}[/cyan]")
    console.print()


@preset_app.command("set-priority")
def preset_set_priority(
    preset_id: str = typer.Argument(help="Preset ID"),
    priority: int = typer.Argument(help="New priority (lower = higher precedence)"),
) -> None:
    """Set the resolution priority of an installed preset."""
    from ..presets import PresetManager

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

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
    if isinstance(raw_priority, int) and raw_priority == priority:
        console.print(f"[yellow]Preset '{preset_id}' already has priority {priority}[/yellow]")
        raise typer.Exit(0)

    old_priority = normalize_priority(raw_priority)

    # Update priority
    manager.registry.update(preset_id, {"priority": priority})

    console.print(f"[green]✓[/green] Preset '{preset_id}' priority changed: {old_priority} → {priority}")
    console.print("\n[dim]Lower priority = higher precedence in template resolution[/dim]")


@preset_app.command("enable")
def preset_enable(
    preset_id: str = typer.Argument(help="Preset ID to enable"),
) -> None:
    """Enable a disabled preset."""
    from ..presets import PresetManager

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
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

    if metadata.get("enabled", True):
        console.print(f"[yellow]Preset '{preset_id}' is already enabled[/yellow]")
        raise typer.Exit(0)

    # Enable the preset
    manager.registry.update(preset_id, {"enabled": True})

    console.print(f"[green]✓[/green] Preset '{preset_id}' enabled")
    console.print("\nTemplates from this preset will now be included in resolution.")
    console.print("[dim]Note: Previously registered commands/skills remain active.[/dim]")


@preset_app.command("disable")
def preset_disable(
    preset_id: str = typer.Argument(help="Preset ID to disable"),
) -> None:
    """Disable a preset without removing it."""
    from ..presets import PresetManager

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
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

    if not metadata.get("enabled", True):
        console.print(f"[yellow]Preset '{preset_id}' is already disabled[/yellow]")
        raise typer.Exit(0)

    # Disable the preset
    manager.registry.update(preset_id, {"enabled": False})

    console.print(f"[green]✓[/green] Preset '{preset_id}' disabled")
    console.print("\nTemplates from this preset will be skipped during resolution.")
    console.print("[dim]Note: Previously registered commands/skills remain active until preset removal.[/dim]")
    console.print(f"To re-enable: specify preset enable {preset_id}")


# ===== Preset Catalog Commands =====


@preset_catalog_app.command("list")
def preset_catalog_list() -> None:
    """List all active preset catalogs."""
    from ..presets import PresetCatalog, PresetValidationError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    catalog = PresetCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except PresetValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Active Preset Catalogs:[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]install allowed[/green]"
            if entry.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [bold]{entry.name}[/bold] (priority {entry.priority})")
        if entry.description:
            console.print(f"     {entry.description}")
        console.print(f"     URL: {entry.url}")
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
            console.print(f"[dim]Config: {config_path.relative_to(project_root).as_posix()}[/dim]")
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
) -> None:
    """Add a catalog to .specify/preset-catalogs.yml."""
    from ..presets import PresetCatalog, PresetValidationError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    # Validate URL
    tmp_catalog = PresetCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except PresetValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    config_path = specify_dir / "preset-catalogs.yml"

    # Load existing config
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to read {config_path}: {e}")
            raise typer.Exit(1)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)

    # Check for duplicate name
    for existing in catalogs:
        if isinstance(existing, dict) and existing.get("name") == name:
            console.print(f"[yellow]Warning:[/yellow] A catalog named '{name}' already exists.")
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
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")

    install_label = "install allowed" if install_allowed else "discovery only"
    console.print(f"\n[green]✓[/green] Added catalog '[bold]{name}[/bold]' ({install_label})")
    console.print(f"  URL: {url}")
    console.print(f"  Priority: {priority}")
    console.print(f"\nConfig saved to {config_path.relative_to(project_root).as_posix()}")


@preset_catalog_app.command("remove")
def preset_catalog_remove(
    name: str = typer.Argument(help="Catalog name to remove"),
) -> None:
    """Remove a catalog from .specify/preset-catalogs.yml."""
    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.is_dir():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    config_path = specify_dir / "preset-catalogs.yml"
    if not config_path.exists():
        console.print("[red]Error:[/red] No preset catalog config found. Nothing to remove.")
        raise typer.Exit(1)

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        console.print("[red]Error:[/red] Failed to read preset catalog config.")
        raise typer.Exit(1)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)
    original_count = len(catalogs)
    catalogs = [c for c in catalogs if isinstance(c, dict) and c.get("name") != name]

    if len(catalogs) == original_count:
        console.print(f"[red]Error:[/red] Catalog '{name}' not found.")
        raise typer.Exit(1)

    config["catalogs"] = catalogs
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True), encoding="utf-8")

    console.print(f"[green]✓[/green] Removed catalog '{name}'")
    if not catalogs:
        console.print("\n[dim]No catalogs remain in config. Built-in defaults will be used.[/dim]")
