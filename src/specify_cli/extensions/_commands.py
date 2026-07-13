"""specify extension * and catalog * command handlers — app objects and register().

Moved out of __init__.py (PR-7/8). Handlers reference helpers that remain in
the package root (`_require_specify_project`, `_locate_bundled_extension`,
`load_init_options`, `_display_project_path`) through the thin shims below,
which re-fetch from the parent package at call time so test monkeypatching of
`specify_cli.<helper>` keeps working.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.markup import escape as _escape_markup
from rich.panel import Panel
from rich.table import Table

from .._console import console
from .._assets import get_speckit_version

extension_app = typer.Typer(
    name="extension",
    help="Manage spec-kit extensions",
    add_completion=False,
)

catalog_app = typer.Typer(
    name="catalog",
    help="Manage extension catalogs",
    add_completion=False,
)
extension_app.add_typer(catalog_app, name="catalog")


# Root helpers re-fetched at call time so test monkeypatching of
# `specify_cli.<name>` keeps working after the move.
def _require_specify_project(*args, **kwargs):
    from .. import _require_specify_project as _f
    return _f(*args, **kwargs)


def _locate_bundled_extension(*args, **kwargs):
    from .. import _locate_bundled_extension as _f
    return _f(*args, **kwargs)


def load_init_options(*args, **kwargs):
    from .. import load_init_options as _f
    return _f(*args, **kwargs)


def _display_project_path(*args, **kwargs):
    from .. import _display_project_path as _f
    return _f(*args, **kwargs)


def _load_catalog_command_config(project_root: Path, config_path: Path) -> dict:
    """Load extension catalog CLI config with user-facing shape errors."""
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        config_label = _escape_markup(str(_display_project_path(project_root, config_path)))
        console.print(f"[red]Error:[/red] Failed to read {config_label}: {_escape_markup(str(e))}")
        raise typer.Exit(1)

    if config is None:
        return {}
    if not isinstance(config, dict):
        config_label = _escape_markup(str(_display_project_path(project_root, config_path)))
        console.print(
            f"[red]Error:[/red] Invalid catalog config {config_label}: "
            "expected a YAML mapping at the root."
        )
        raise typer.Exit(1)
    return config


def _resolve_installed_extension(
    argument: str,
    installed_extensions: list,
    command_name: str = "command",
    allow_not_found: bool = False,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve an extension argument (ID or display name) to an installed extension.

    Args:
        argument: Extension ID or display name provided by user
        installed_extensions: List of installed extension dicts from manager.list_installed()
        command_name: Name of the command for error messages (e.g., "enable", "disable")
        allow_not_found: If True, return (None, None) when not found instead of raising

    Returns:
        Tuple of (extension_id, display_name), or (None, None) if allow_not_found=True and not found

    Raises:
        typer.Exit: If extension not found (and allow_not_found=False) or name is ambiguous
    """
    # First, try exact ID match
    for ext in installed_extensions:
        if ext["id"] == argument:
            return (ext["id"], ext["name"])

    # If not found by ID, try display name match
    name_matches = [ext for ext in installed_extensions if ext["name"].lower() == argument.lower()]

    if len(name_matches) == 1:
        # Unique display-name match
        return (name_matches[0]["id"], name_matches[0]["name"])
    elif len(name_matches) > 1:
        # Ambiguous display-name match
        console.print(
            f"[red]Error:[/red] Extension name '{_escape_markup(argument)}' is ambiguous. "
            "Multiple installed extensions share this name:"
        )
        table = Table(title="Matching extensions")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Version", style="green")
        for ext in name_matches:
            table.add_row(
                _escape_markup(str(ext.get("id", ""))),
                _escape_markup(str(ext.get("name", ""))),
                _escape_markup(str(ext.get("version", ""))),
            )
        console.print(table)
        console.print("\nPlease rerun using the extension ID:")
        console.print(f"  [bold]specify extension {command_name} <extension-id>[/bold]")
        raise typer.Exit(1)
    else:
        # No match by ID or display name
        if allow_not_found:
            return (None, None)
        console.print(f"[red]Error:[/red] Extension '{_escape_markup(argument)}' is not installed")
        raise typer.Exit(1)


def _resolve_catalog_extension(
    argument: str,
    catalog,
    command_name: str = "info",
) -> tuple[Optional[dict], Optional[Exception]]:
    """Resolve an extension argument (ID or display name) from the catalog.

    Args:
        argument: Extension ID or display name provided by user
        catalog: ExtensionCatalog instance
        command_name: Name of the command for error messages

    Returns:
        Tuple of (extension_info, catalog_error)
        - If found: (ext_info_dict, None)
        - If catalog error: (None, error)
        - If not found: (None, None)
    """
    from . import ExtensionError

    try:
        # First try by ID
        ext_info = catalog.get_extension_info(argument)
        if ext_info:
            return (ext_info, None)

        # Try by display name - search using argument as query, then filter for exact match
        search_results = catalog.search(query=argument)
        name_matches = [ext for ext in search_results if ext["name"].lower() == argument.lower()]

        if len(name_matches) == 1:
            return (name_matches[0], None)
        elif len(name_matches) > 1:
            # Ambiguous display-name match in catalog
            console.print(
                f"[red]Error:[/red] Extension name '{_escape_markup(argument)}' is ambiguous. "
                "Multiple catalog extensions share this name:"
            )
            table = Table(title="Matching extensions")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="white")
            table.add_column("Version", style="green")
            table.add_column("Catalog", style="dim")
            for ext in name_matches:
                table.add_row(
                    _escape_markup(str(ext.get("id", ""))),
                    _escape_markup(str(ext.get("name", ""))),
                    _escape_markup(str(ext.get("version", ""))),
                    _escape_markup(str(ext.get("_catalog_name", ""))),
                )
            console.print(table)
            console.print("\nPlease rerun using the extension ID:")
            console.print(f"  [bold]specify extension {command_name} <extension-id>[/bold]")
            raise typer.Exit(1)

        # Not found
        return (None, None)

    except ExtensionError as e:
        return (None, e)


@extension_app.command("list")
def extension_list(
    available: bool = typer.Option(False, "--available", help="Show available extensions from catalog"),
    all_extensions: bool = typer.Option(False, "--all", help="Show both installed and available"),
):
    """List installed extensions."""
    from . import ExtensionManager

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    if not installed and not (available or all_extensions):
        console.print("[yellow]No extensions installed.[/yellow]")
        console.print("\nInstall an extension with:")
        console.print("  specify extension add <extension-name>")
        return

    if installed:
        console.print("\n[bold cyan]Installed Extensions:[/bold cyan]\n")

        for ext in installed:
            status_icon = "✓" if ext["enabled"] else "✗"
            status_color = "green" if ext["enabled"] else "red"

            console.print(f"  [{status_color}]{status_icon}[/{status_color}] [bold]{_escape_markup(ext['name'])}[/bold] (v{_escape_markup(str(ext['version']))})")
            console.print(f"     [dim]{_escape_markup(ext['id'])}[/dim]")
            console.print(f"     {_escape_markup(ext['description'])}")
            console.print(f"     Commands: {ext['command_count']} | Hooks: {ext['hook_count']} | Priority: {ext['priority']} | Status: {'Enabled' if ext['enabled'] else 'Disabled'}")
            console.print()

    if available or all_extensions:
        console.print("\nInstall an extension:")
        console.print("  [cyan]specify extension add <name>[/cyan]")


@catalog_app.command("list")
def catalog_list():
    """List all active extension catalogs."""
    from . import ExtensionCatalog, ValidationError

    project_root = _require_specify_project()
    catalog = ExtensionCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Active Extension Catalogs:[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]install allowed[/green]"
            if entry.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [bold]{_escape_markup(entry.name)}[/bold] (priority {entry.priority})")
        if entry.description:
            console.print(f"     {_escape_markup(entry.description)}")
        console.print(f"     URL: {_escape_markup(str(entry.url))}")
        console.print(f"     Install: {install_str}")
        console.print()

    config_path = project_root / ".specify" / "extension-catalogs.yml"
    user_config_path = Path.home() / ".specify" / "extension-catalogs.yml"
    if os.environ.get("SPECKIT_CATALOG_URL"):
        console.print("[dim]Catalog configured via SPECKIT_CATALOG_URL environment variable.[/dim]")
    else:
        try:
            proj_loaded = config_path.exists() and catalog._load_catalog_config(config_path) is not None
        except ValidationError:
            proj_loaded = False
        if proj_loaded:
            config_label = _escape_markup(str(_display_project_path(project_root, config_path)))
            console.print(f"[dim]Config: {config_label}[/dim]")
        else:
            try:
                user_loaded = user_config_path.exists() and catalog._load_catalog_config(user_config_path) is not None
            except ValidationError:
                user_loaded = False
            if user_loaded:
                console.print("[dim]Config: ~/.specify/extension-catalogs.yml[/dim]")
            else:
                console.print("[dim]Using built-in default catalog stack.[/dim]")
                console.print(
                    "[dim]Add .specify/extension-catalogs.yml to customize.[/dim]"
                )


@catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(help="Catalog URL (must use HTTPS)"),
    name: str = typer.Option(..., "--name", help="Catalog name"),
    priority: int = typer.Option(10, "--priority", help="Priority (lower = higher priority)"),
    install_allowed: bool = typer.Option(
        False, "--install-allowed/--no-install-allowed",
        help="Allow extensions from this catalog to be installed",
    ),
    description: str = typer.Option("", "--description", help="Description of the catalog"),
):
    """Add a catalog to .specify/extension-catalogs.yml."""
    from . import ExtensionCatalog, ValidationError

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Validate URL
    tmp_catalog = ExtensionCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    config_path = specify_dir / "extension-catalogs.yml"

    # Load existing config
    if config_path.exists():
        config = _load_catalog_command_config(project_root, config_path)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)

    safe_name = _escape_markup(name)
    safe_url = _escape_markup(url)

    # Check for duplicate name
    for existing in catalogs:
        if isinstance(existing, dict) and existing.get("name") == name:
            console.print(f"[yellow]Warning:[/yellow] A catalog named '{safe_name}' already exists.")
            console.print("Use 'specify extension catalog remove' first, or choose a different name.")
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


@catalog_app.command("remove")
def catalog_remove(
    name: str = typer.Argument(help="Catalog name to remove"),
):
    """Remove a catalog from .specify/extension-catalogs.yml."""
    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    config_path = specify_dir / "extension-catalogs.yml"
    if not config_path.exists():
        console.print("[red]Error:[/red] No catalog config found. Nothing to remove.")
        raise typer.Exit(1)

    config = _load_catalog_command_config(project_root, config_path)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print("[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list.")
        raise typer.Exit(1)
    safe_name = _escape_markup(name)
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


@extension_app.command("add")
def extension_add(
    extension: str = typer.Argument(help="Extension name or path"),
    dev: bool = typer.Option(False, "--dev", help="Install from local directory"),
    from_url: Optional[str] = typer.Option(None, "--from", help="Install from custom URL"),
    force: bool = typer.Option(False, "--force", help="Overwrite if already installed"),
    priority: int = typer.Option(10, "--priority", help="Resolution priority (lower = higher precedence, default 10)"),
):
    """Install an extension."""
    from . import ExtensionManager, ExtensionCatalog, ExtensionError, ValidationError, CompatibilityError, REINSTALL_COMMAND

    project_root = _require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    speckit_version = get_speckit_version()

    if force:
        console.print("[yellow]--force:[/yellow] Will overwrite if already installed")

    # Prompt for URL-based installs BEFORE the spinner so the user can
    # actually see and respond to the confirmation (the Rich status
    # spinner overwrites the typer.confirm prompt line, making it appear
    # as though the command is hung).
    # Guard with ``not dev`` so that --dev + --from does not show a
    # confusing confirmation for a URL that will be ignored.
    if from_url and not dev:
        from urllib.parse import urlparse

        try:
            parsed = urlparse(from_url)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(from_url)}")
            raise typer.Exit(1)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")

        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            console.print("[red]Error:[/red] URL must use HTTPS for security.")
            console.print("HTTP is only allowed for localhost URLs.")
            raise typer.Exit(1)

        safe_url = _escape_markup(from_url)

        # Warn about untrusted sources — default-deny confirmation
        console.print()
        console.print(Panel(
            f"[bold]You are installing an extension from an external URL that is not\n"
            f"listed in any of your configured extension catalogs.[/bold]\n\n"
            f"URL: {safe_url}\n\n"
            f"Only install extensions from sources you trust.",
            title="[bold yellow]⚠ Untrusted Source[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))
        console.print()
        confirm = typer.confirm("Continue with installation?", default=False)
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    safe_extension = _escape_markup(extension)

    try:
        with console.status(f"[cyan]Installing extension: {safe_extension}[/cyan]"):
            if dev:
                # Install from local directory
                source_path = Path(extension).expanduser().resolve()
                safe_source_path = _escape_markup(str(source_path))
                if not source_path.exists():
                    console.print(f"[red]Error:[/red] Directory not found: {safe_source_path}")
                    raise typer.Exit(1)

                if not (source_path / "extension.yml").exists():
                    console.print(f"[red]Error:[/red] No extension.yml found in {safe_source_path}")
                    raise typer.Exit(1)

                if force:
                    console.print(f"[yellow]--force:[/yellow] Installing from [cyan]{safe_source_path}[/cyan] (will overwrite if already installed)...")

                manifest = manager.install_from_directory(
                    source_path,
                    speckit_version,
                    priority=priority,
                    link_commands=True,
                    force=force
                )

            elif from_url:
                # Install from URL (ZIP file)
                import io
                import urllib.error

                console.print(f"Downloading from {safe_url}...")

                # Download ZIP to temp location
                download_dir = project_root / ".specify" / "extensions" / ".cache" / "downloads"
                download_dir.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    prefix="extension-url-download-",
                    suffix=".zip",
                    dir=download_dir,
                    delete=False,
                ) as download_file:
                    zip_path = Path(download_file.name)

                try:
                    # Use the catalog's authenticated fetch so configured
                    # credentials (incl. GitHub Enterprise Server) are applied
                    # and GHES release-asset URLs resolve via /api/v3 — keeping
                    # --from consistent with catalog-based installs.
                    dl_catalog = ExtensionCatalog(project_root)
                    download_url = from_url
                    extra_headers = None
                    resolved_url = dl_catalog._resolve_github_release_asset_api_url(download_url)
                    if resolved_url:
                        download_url = resolved_url
                        extra_headers = {"Accept": "application/octet-stream"}

                    with dl_catalog._open_url(
                        download_url, timeout=60, extra_headers=extra_headers
                    ) as response:
                        zip_data = response.read()

                    if not zipfile.is_zipfile(io.BytesIO(zip_data)):
                        console.print(
                            f"[red]Error:[/red] {safe_url} did not return a ZIP archive "
                            f"(got {len(zip_data)} bytes). This usually means the request "
                            f"was not authenticated and a login/HTML page was returned. "
                            f"Verify the URL is correct and that credentials for its host "
                            f"are configured in ~/.specify/auth.json."
                        )
                        raise typer.Exit(1)

                    zip_path.write_bytes(zip_data)

                    # Install from downloaded ZIP
                    manifest = manager.install_from_zip(zip_path, speckit_version, priority=priority, force=force)
                except urllib.error.URLError as e:
                    console.print(
                        f"[red]Error:[/red] Failed to download from {safe_url}: "
                        f"{_escape_markup(str(e))}"
                    )
                    raise typer.Exit(1)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

            else:
                # Try bundled extensions first (shipped with spec-kit)
                bundled_path = _locate_bundled_extension(extension)
                if bundled_path is not None:
                    manifest = manager.install_from_directory(
                        bundled_path, speckit_version, priority=priority, force=force
                    )
                else:
                    # Install from catalog (also resolves display names to IDs)
                    catalog = ExtensionCatalog(project_root)

                    # Check if extension exists in catalog (supports both ID and display name)
                    ext_info, catalog_error = _resolve_catalog_extension(extension, catalog, "add")
                    if catalog_error:
                        console.print(f"[red]Error:[/red] Could not query extension catalog: {_escape_markup(str(catalog_error))}")
                        raise typer.Exit(1)
                    if not ext_info:
                        console.print(f"[red]Error:[/red] Extension '{safe_extension}' not found in catalog")
                        console.print("\nSearch available extensions:")
                        console.print("  specify extension search")
                        raise typer.Exit(1)

                    # If catalog resolved a display name to an ID, check bundled again
                    resolved_id = ext_info['id']
                    if resolved_id != extension:
                        bundled_path = _locate_bundled_extension(resolved_id)
                        if bundled_path is not None:
                            manifest = manager.install_from_directory(
                                bundled_path, speckit_version, priority=priority, force=force
                            )

                    if bundled_path is None:
                        # Bundled extensions without a download URL must come from the local package
                        if ext_info.get("bundled") and not ext_info.get("download_url"):
                            console.print(
                                f"[red]Error:[/red] Extension '{_escape_markup(ext_info['id'])}' is bundled with spec-kit "
                                f"but could not be found in the installed package."
                            )
                            console.print(
                                "\nThis usually means the spec-kit installation is incomplete or corrupted."
                            )
                            console.print("Try reinstalling spec-kit:")
                            console.print(f"  {REINSTALL_COMMAND}")
                            raise typer.Exit(1)

                        # Enforce install_allowed policy
                        if not ext_info.get("_install_allowed", True):
                            catalog_name = _escape_markup(str(ext_info.get("_catalog_name", "community")))
                            console.print(
                                f"[red]Error:[/red] '{safe_extension}' is available in the "
                                f"'{catalog_name}' catalog but installation is not allowed from that catalog."
                            )
                            console.print(
                                f"\nTo enable installation, add '{safe_extension}' to an approved catalog "
                                f"(install_allowed: true) in .specify/extension-catalogs.yml."
                            )
                            raise typer.Exit(1)

                        # Download extension ZIP (use resolved ID, not original argument which may be display name)
                        extension_id = ext_info['id']
                        console.print(f"Downloading {_escape_markup(str(ext_info['name']))} v{_escape_markup(str(ext_info.get('version', 'unknown')))}...")
                        zip_path = catalog.download_extension(extension_id)

                        try:
                            # Install from downloaded ZIP
                            manifest = manager.install_from_zip(zip_path, speckit_version, priority=priority, force=force)
                        finally:
                            # Clean up downloaded ZIP
                            if zip_path.exists():
                                zip_path.unlink()

        console.print("\n[green]✓[/green] Extension installed successfully!")
        console.print(f"\n[bold]{_escape_markup(str(manifest.name))}[/bold] (v{_escape_markup(str(manifest.version))})")
        console.print(f"  {_escape_markup(str(manifest.description))}")

        for warning in manifest.warnings:
            console.print(f"\n[yellow]⚠  Compatibility warning:[/yellow] {_escape_markup(str(warning))}")

        is_cline = load_init_options(project_root).get("ai") == "cline"

        if is_cline:
            from specify_cli.integrations.cline import format_cline_command_name

        console.print("\n[bold cyan]Provided commands:[/bold cyan]")
        for cmd in manifest.commands:
            cmd_name = cmd['name']
            if is_cline:
                cmd_name = format_cline_command_name(cmd_name)
            console.print(f"  • {_escape_markup(str(cmd_name))} - {_escape_markup(str(cmd.get('description', '')))}")

        # Report agent skills registration
        reg_meta = manager.registry.get(manifest.id)
        reg_skills = reg_meta.get("registered_skills", []) if reg_meta else []
        # Normalize to guard against corrupted registry entries
        if not isinstance(reg_skills, list):
            reg_skills = []
        if reg_skills:
            console.print(f"\n[green]✓[/green] {len(reg_skills)} agent skill(s) auto-registered")

        console.print("\n[yellow]⚠[/yellow]  Configuration may be required")
        console.print(f"   Check: .specify/extensions/{_escape_markup(str(manifest.id))}/")

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except CompatibilityError as e:
        console.print(f"\n[red]Compatibility Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)


@extension_app.command("remove")
def extension_remove(
    extension: str = typer.Argument(help="Extension ID or name to remove"),
    keep_config: bool = typer.Option(False, "--keep-config", help="Don't remove config files"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
):
    """Uninstall an extension."""
    from . import ExtensionManager

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "remove")
    safe_extension_id = _escape_markup(str(extension_id))

    # Get extension info for command and skill counts
    ext_manifest = manager.get_extension(extension_id)
    reg_meta = manager.registry.get(extension_id)
    # Derive cmd_count from the registry's registered_commands (includes aliases)
    # rather than from the manifest (primary commands only). Use max() across
    # agents to get the per-agent count; sum() would double-count since users
    # think in logical commands, not per-agent file counts.
    # Use get() without a default so we can distinguish "key missing" (fall back
    # to manifest) from "key present but empty dict" (zero commands registered).
    registered_commands = reg_meta.get("registered_commands") if isinstance(reg_meta, dict) else None
    if isinstance(registered_commands, dict):
        cmd_count = max(
            (len(v) for v in registered_commands.values() if isinstance(v, list)),
            default=0,
        )
    else:
        cmd_count = len(ext_manifest.commands) if ext_manifest else 0
    raw_skills = reg_meta.get("registered_skills") if reg_meta else None
    skill_count = len(raw_skills) if isinstance(raw_skills, list) else 0

    # Confirm removal
    if not force:
        console.print("\n[yellow]⚠  This will remove:[/yellow]")
        console.print(f"   • {cmd_count} command{'s' if cmd_count != 1 else ''} per agent")
        if skill_count:
            console.print(f"   • {skill_count} agent skill(s)")
        console.print(f"   • Extension directory: .specify/extensions/{safe_extension_id}/")
        if not keep_config:
            console.print("   • Config files (will be backed up)")
        console.print()

        confirm = typer.confirm("Continue?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    # Remove extension
    success = manager.remove(extension_id, keep_config=keep_config)

    if success:
        console.print(f"\n[green]✓[/green] Extension '{_escape_markup(str(display_name))}' removed successfully")
        if keep_config:
            console.print(f"\nConfig files preserved in .specify/extensions/{safe_extension_id}/")
        else:
            console.print(f"\nConfig files backed up to .specify/extensions/.backup/{safe_extension_id}/")
        console.print(f"\nTo reinstall: specify extension add {safe_extension_id}")
    else:
        console.print("[red]Error:[/red] Failed to remove extension")
        raise typer.Exit(1)


@extension_app.command("search")
def extension_search(
    query: str = typer.Argument(None, help="Search query (optional)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    author: Optional[str] = typer.Option(None, "--author", help="Filter by author"),
    verified: bool = typer.Option(False, "--verified", help="Show only verified extensions"),
):
    """Search for available extensions in catalog."""
    from . import ExtensionCatalog, ExtensionError

    project_root = _require_specify_project()
    catalog = ExtensionCatalog(project_root)

    try:
        console.print("🔍 Searching extension catalog...")
        results = catalog.search(query=query, tag=tag, author=author, verified_only=verified)

        if not results:
            console.print("\n[yellow]No extensions found matching criteria[/yellow]")
            if query or tag or author or verified:
                console.print("\nTry:")
                console.print("  • Broader search terms")
                console.print("  • Remove filters")
                console.print("  • specify extension search (show all)")
            raise typer.Exit(0)

        console.print(f"\n[green]Found {len(results)} extension(s):[/green]\n")

        for ext in results:
            # Extension header
            verified_badge = " [green]✓ Verified[/green]" if ext.get("verified") else ""
            console.print(f"[bold]{_escape_markup(str(ext['name']))}[/bold] (v{_escape_markup(str(ext['version']))}){verified_badge}")
            console.print(f"  {_escape_markup(str(ext['description']))}")

            # Metadata
            console.print(f"\n  [dim]Author:[/dim] {_escape_markup(str(ext.get('author', 'Unknown')))}")
            if ext.get('tags'):
                tags_str = ", ".join(str(t) for t in ext['tags'])
                console.print(f"  [dim]Tags:[/dim] {_escape_markup(tags_str)}")

            # Source catalog
            catalog_name = _escape_markup(str(ext.get("_catalog_name", "")))
            install_allowed = ext.get("_install_allowed", True)
            if catalog_name:
                if install_allowed:
                    console.print(f"  [dim]Catalog:[/dim] {catalog_name}")
                else:
                    console.print(f"  [dim]Catalog:[/dim] {catalog_name} [yellow](discovery only — not installable)[/yellow]")

            # Stats
            stats = []
            if ext.get('downloads') is not None:
                stats.append(f"Downloads: {ext['downloads']:,}")
            if ext.get('stars') is not None:
                stats.append(f"Stars: {ext['stars']}")
            if stats:
                console.print(f"  [dim]{' | '.join(stats)}[/dim]")

            # Links
            if ext.get('repository'):
                console.print(f"  [dim]Repository:[/dim] {_escape_markup(str(ext['repository']))}")

            # Install command (show warning if not installable)
            safe_id = _escape_markup(str(ext['id']))
            if install_allowed:
                console.print(f"\n  [cyan]Install:[/cyan] specify extension add {safe_id}")
            else:
                console.print(f"\n  [yellow]⚠[/yellow]  Not directly installable from '{catalog_name}'.")
                console.print(
                    f"  Add to an approved catalog with install_allowed: true, "
                    f"or install from a ZIP URL: specify extension add {safe_id} --from <zip-url>"
                )
            console.print()

    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {_escape_markup(str(e))}")
        console.print("\nTip: The catalog may be temporarily unavailable. Try again later.")
        raise typer.Exit(1)


@extension_app.command("info")
def extension_info(
    extension: str = typer.Argument(help="Extension ID or name"),
):
    """Show detailed information about an extension."""
    from . import ExtensionCatalog, ExtensionManager, normalize_priority

    project_root = _require_specify_project()
    catalog = ExtensionCatalog(project_root)
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    # Try to resolve from installed extensions first (by ID or name)
    # Use allow_not_found=True since the extension may be catalog-only
    resolved_installed_id, resolved_installed_name = _resolve_installed_extension(
        extension, installed, "info", allow_not_found=True
    )

    # Try catalog lookup (with error handling)
    # If we resolved an installed extension by display name, use its ID for catalog lookup
    # to ensure we get the correct catalog entry (not a different extension with same name)
    lookup_key = resolved_installed_id if resolved_installed_id else extension
    ext_info, catalog_error = _resolve_catalog_extension(lookup_key, catalog, "info")

    # Case 1: Found in catalog - show full catalog info
    if ext_info:
        _print_extension_info(ext_info, manager)
        return

    # Case 2: Installed locally but catalog lookup failed or not in catalog
    if resolved_installed_id:
        # Get local manifest info
        ext_manifest = manager.get_extension(resolved_installed_id)
        metadata = manager.registry.get(resolved_installed_id)
        metadata_is_dict = isinstance(metadata, dict)
        if not metadata_is_dict:
            console.print(
                "[yellow]Warning:[/yellow] Extension metadata appears to be corrupted; "
                "some information may be unavailable."
            )
        version = metadata.get("version", "unknown") if metadata_is_dict else "unknown"

        console.print(f"\n[bold]{_escape_markup(str(resolved_installed_name))}[/bold] (v{_escape_markup(str(version))})")
        console.print(f"ID: {_escape_markup(str(resolved_installed_id))}")
        console.print()

        if ext_manifest:
            console.print(f"{_escape_markup(str(ext_manifest.description))}")
            console.print()
            # Author is optional in extension.yml, safely retrieve it
            author = ext_manifest.data.get("extension", {}).get("author")
            if author:
                console.print(f"[dim]Author:[/dim] {_escape_markup(str(author))}")
            if ext_manifest.category:
                console.print(f"[dim]Category:[/dim] {_escape_markup(str(ext_manifest.category))}")
            if ext_manifest.effect:
                console.print(f"[dim]Effect:[/dim] {_escape_markup(str(ext_manifest.effect))}")
            console.print()

            if ext_manifest.commands:
                console.print("[bold]Commands:[/bold]")
                for cmd in ext_manifest.commands:
                    console.print(f"  • {_escape_markup(str(cmd['name']))}: {_escape_markup(str(cmd.get('description', '')))}")
                console.print()

        # Show catalog status
        if catalog_error:
            console.print(f"[yellow]Catalog unavailable:[/yellow] {_escape_markup(str(catalog_error))}")
            console.print("[dim]Note: Using locally installed extension; catalog info could not be verified.[/dim]")
        else:
            console.print("[yellow]Note:[/yellow] Not found in catalog (custom/local extension)")

        console.print()
        console.print("[green]✓ Installed[/green]")
        priority = normalize_priority(metadata.get("priority") if metadata_is_dict else None)
        console.print(f"[dim]Priority:[/dim] {priority}")
        console.print(f"\nTo remove: specify extension remove {_escape_markup(str(resolved_installed_id))}")
        return

    # Case 3: Not found anywhere
    if catalog_error:
        console.print(f"[red]Error:[/red] Could not query extension catalog: {_escape_markup(str(catalog_error))}")
        console.print("\nTry again when online, or use the extension ID directly.")
    else:
        console.print(f"[red]Error:[/red] Extension '{_escape_markup(extension)}' not found")
        console.print("\nTry: specify extension search")
    raise typer.Exit(1)


def _print_extension_info(ext_info: dict, manager):
    """Print formatted extension info from catalog data."""
    from . import normalize_priority

    # Header
    verified_badge = " [green]✓ Verified[/green]" if ext_info.get("verified") else ""
    console.print(f"\n[bold]{_escape_markup(str(ext_info['name']))}[/bold] (v{_escape_markup(str(ext_info['version']))}){verified_badge}")
    console.print(f"ID: {_escape_markup(str(ext_info['id']))}")
    console.print()

    # Description
    console.print(f"{_escape_markup(str(ext_info['description']))}")
    console.print()

    # Author and License
    console.print(f"[dim]Author:[/dim] {_escape_markup(str(ext_info.get('author', 'Unknown')))}")
    console.print(f"[dim]License:[/dim] {_escape_markup(str(ext_info.get('license', 'Unknown')))}")

    # Category and Effect
    if ext_info.get('category'):
        console.print(f"[dim]Category:[/dim] {_escape_markup(str(ext_info['category']))}")
    if ext_info.get('effect'):
        console.print(f"[dim]Effect:[/dim] {_escape_markup(str(ext_info['effect']))}")

    # Source catalog
    if ext_info.get("_catalog_name"):
        install_allowed = ext_info.get("_install_allowed", True)
        install_note = "" if install_allowed else " [yellow](discovery only)[/yellow]"
        console.print(f"[dim]Source catalog:[/dim] {_escape_markup(str(ext_info['_catalog_name']))}{install_note}")
    console.print()

    # Requirements
    if ext_info.get('requires'):
        console.print("[bold]Requirements:[/bold]")
        reqs = ext_info['requires']
        if reqs.get('speckit_version'):
            console.print(f"  • Spec Kit: {_escape_markup(str(reqs['speckit_version']))}")
        if reqs.get('tools'):
            for tool in reqs['tools']:
                tool_name = _escape_markup(str(tool['name']))
                tool_version = _escape_markup(str(tool.get('version', 'any')))
                required = " (required)" if tool.get('required') else " (optional)"
                console.print(f"  • {tool_name}: {tool_version}{required}")
        console.print()

    # Provides
    if ext_info.get('provides'):
        console.print("[bold]Provides:[/bold]")
        provides = ext_info['provides']
        if provides.get('commands'):
            console.print(f"  • Commands: {_escape_markup(str(provides['commands']))}")
        if provides.get('hooks'):
            console.print(f"  • Hooks: {_escape_markup(str(provides['hooks']))}")
        console.print()

    # Tags
    if ext_info.get('tags'):
        tags_str = ", ".join(str(t) for t in ext_info['tags'])
        console.print(f"[bold]Tags:[/bold] {_escape_markup(tags_str)}")
        console.print()

    # Statistics
    stats = []
    if ext_info.get('downloads') is not None:
        stats.append(f"Downloads: {ext_info['downloads']:,}")
    if ext_info.get('stars') is not None:
        stats.append(f"Stars: {ext_info['stars']}")
    if stats:
        console.print(f"[bold]Statistics:[/bold] {' | '.join(stats)}")
        console.print()

    # Links
    console.print("[bold]Links:[/bold]")
    if ext_info.get('repository'):
        console.print(f"  • Repository: {_escape_markup(str(ext_info['repository']))}")
    if ext_info.get('homepage'):
        console.print(f"  • Homepage: {_escape_markup(str(ext_info['homepage']))}")
    if ext_info.get('documentation'):
        console.print(f"  • Documentation: {_escape_markup(str(ext_info['documentation']))}")
    if ext_info.get('changelog'):
        console.print(f"  • Changelog: {_escape_markup(str(ext_info['changelog']))}")
    console.print()

    # Installation status and command
    is_installed = manager.registry.is_installed(ext_info['id'])
    install_allowed = ext_info.get("_install_allowed", True)
    safe_id = _escape_markup(str(ext_info['id']))
    if is_installed:
        console.print("[green]✓ Installed[/green]")
        metadata = manager.registry.get(ext_info['id'])
        priority = normalize_priority(metadata.get("priority") if isinstance(metadata, dict) else None)
        console.print(f"[dim]Priority:[/dim] {priority}")
        console.print(f"\nTo remove: specify extension remove {safe_id}")
    elif install_allowed:
        console.print("[yellow]Not installed[/yellow]")
        console.print(f"\n[cyan]Install:[/cyan] specify extension add {safe_id}")
    else:
        catalog_name = _escape_markup(str(ext_info.get("_catalog_name", "community")))
        console.print("[yellow]Not installed[/yellow]")
        console.print(
            f"\n[yellow]⚠[/yellow]  '{safe_id}' is available in the '{catalog_name}' catalog "
            f"but not in your approved catalog. Add it to .specify/extension-catalogs.yml "
            f"with install_allowed: true to enable installation."
        )


@extension_app.command("update")
def extension_update(
    extension: str = typer.Argument(None, help="Extension ID or name to update (or all)"),
):
    """Update extension(s) to latest version."""
    from . import (
        ExtensionManager,
        ExtensionCatalog,
        ExtensionError,
        ValidationError,
        CommandRegistrar,
        HookExecutor,
        normalize_priority,
    )
    from packaging import version as pkg_version

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    catalog = ExtensionCatalog(project_root)
    speckit_version = get_speckit_version()

    try:
        # Get list of extensions to update
        installed = manager.list_installed()
        if extension:
            # Update specific extension - resolve ID from argument (handles ambiguous names)
            extension_id, _ = _resolve_installed_extension(extension, installed, "update")
            extensions_to_update = [extension_id]
        else:
            # Update all extensions
            extensions_to_update = [ext["id"] for ext in installed]

        if not extensions_to_update:
            console.print("[yellow]No extensions installed[/yellow]")
            raise typer.Exit(0)

        console.print("🔄 Checking for updates...\n")

        updates_available = []

        for ext_id in extensions_to_update:
            safe_ext_id = _escape_markup(str(ext_id))
            # Get installed version
            metadata = manager.registry.get(ext_id)
            if metadata is None or not isinstance(metadata, dict) or "version" not in metadata:
                console.print(f"⚠  {safe_ext_id}: Registry entry corrupted or missing (skipping)")
                continue
            try:
                installed_version = pkg_version.Version(metadata["version"])
            except pkg_version.InvalidVersion:
                console.print(
                    f"⚠  {safe_ext_id}: Invalid installed version '{_escape_markup(str(metadata.get('version')))}' in registry (skipping)"
                )
                continue

            # Get catalog info
            ext_info = catalog.get_extension_info(ext_id)
            if not ext_info:
                console.print(f"⚠  {safe_ext_id}: Not found in catalog (skipping)")
                continue

            # Check if installation is allowed from this catalog
            if not ext_info.get("_install_allowed", True):
                console.print(f"⚠  {safe_ext_id}: Updates not allowed from '{_escape_markup(str(ext_info.get('_catalog_name', 'catalog')))}' (skipping)")
                continue

            try:
                catalog_version = pkg_version.Version(ext_info["version"])
            except pkg_version.InvalidVersion:
                console.print(
                    f"⚠  {safe_ext_id}: Invalid catalog version '{_escape_markup(str(ext_info.get('version')))}' (skipping)"
                )
                continue

            if catalog_version > installed_version:
                updates_available.append(
                    {
                        "id": ext_id,
                        "name": ext_info.get("name", ext_id),  # Display name for status messages
                        "installed": str(installed_version),
                        "available": str(catalog_version),
                        "download_url": ext_info.get("download_url"),
                    }
                )
            else:
                console.print(f"✓ {safe_ext_id}: Up to date (v{installed_version})")

        if not updates_available:
            console.print("\n[green]All extensions are up to date![/green]")
            raise typer.Exit(0)

        # Show available updates
        console.print("\n[bold]Updates available:[/bold]\n")
        for update in updates_available:
            console.print(
                f"  • {_escape_markup(str(update['id']))}: {update['installed']} → {update['available']}"
            )

        console.print()
        confirm = typer.confirm("Update these extensions?")
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

        # Perform updates with atomic backup/restore
        console.print()
        updated_extensions = []
        failed_updates = []
        registrar = CommandRegistrar()
        hook_executor = HookExecutor(project_root)
        from ..agents import CommandRegistrar as _AgentReg  # used in backup and rollback paths

        # UNSET sentinel: backup not yet captured (exception before backup step)
        UNSET = object()

        for update in updates_available:
            extension_id = update["id"]
            ext_name = update["name"]  # Use display name for user-facing messages
            safe_ext_name = _escape_markup(str(ext_name))
            console.print(f"📦 Updating {safe_ext_name}...")

            # Backup paths
            backup_base = manager.extensions_dir / ".backup" / f"{extension_id}-update"
            backup_ext_dir = backup_base / "extension"
            backup_commands_dir = backup_base / "commands"
            backup_config_dir = backup_base / "config"

            # Store backup state
            backup_registry_entry = None  # None means registry entry not yet captured
            backup_installed = UNSET  # Original installed list from extensions.yml
            backup_hooks = None  # None means backup step 4 not yet reached; {} or {...} means backup was captured
            backed_up_command_files = {}

            try:
                # 1. Backup registry entry (always, even if extension dir doesn't exist)
                backup_registry_entry = manager.registry.get(extension_id)

                # 2. Backup extension directory
                extension_dir = manager.extensions_dir / extension_id
                if extension_dir.exists():
                    backup_base.mkdir(parents=True, exist_ok=True)
                    if backup_ext_dir.exists():
                        shutil.rmtree(backup_ext_dir)
                    shutil.copytree(extension_dir, backup_ext_dir)

                    # Backup config files separately so they can be restored
                    # after a successful install (install_from_directory clears dest dir).
                    config_files = list(extension_dir.glob("*-config.yml")) + list(
                        extension_dir.glob("*-config.local.yml")
                    )
                    for cfg_file in config_files:
                        backup_config_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(cfg_file, backup_config_dir / cfg_file.name)

                # 3. Backup command files for all agents
                registered_commands = backup_registry_entry.get("registered_commands", {}) if isinstance(backup_registry_entry, dict) else {}
                for agent_name, cmd_names in registered_commands.items():
                    if agent_name not in registrar.AGENT_CONFIGS:
                        continue
                    agent_config = registrar.AGENT_CONFIGS[agent_name]
                    commands_dir = _AgentReg._resolve_agent_dir(
                        agent_name, agent_config, project_root
                    )

                    for cmd_name in cmd_names:
                        output_name = _AgentReg._compute_output_name(agent_name, cmd_name, agent_config)
                        cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                        if cmd_file.exists():
                            # Mirror the real on-disk layout under the backup dir.
                            # Skills agents (extension == "/SKILL.md") name every
                            # command file "SKILL.md", living in a per-command
                            # subdir (e.g. speckit-plan/SKILL.md). Using cmd_file.name
                            # alone would collide all of them onto one backup path and
                            # break rollback; keep the relative path to stay unique.
                            backup_cmd_path = backup_commands_dir / agent_name / cmd_file.relative_to(commands_dir)
                            backup_cmd_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(cmd_file, backup_cmd_path)
                            backed_up_command_files[str(cmd_file)] = str(backup_cmd_path)

                        # Also backup copilot prompt files
                        if agent_name == "copilot":
                            prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                            if prompt_file.exists():
                                backup_prompt_path = backup_commands_dir / "copilot-prompts" / prompt_file.name
                                backup_prompt_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(prompt_file, backup_prompt_path)
                                backed_up_command_files[str(prompt_file)] = str(backup_prompt_path)

                # 4. Backup hooks and installed list from extensions.yml
                # get_project_config() always normalizes installed->[] and hooks->{},
                # so no sentinel is needed to distinguish key-absent from key-empty.
                config = hook_executor.get_project_config()
                if isinstance(config, dict):
                    import copy
                    # Deep-copy so nested mapping entries (e.g. version-pin dicts)
                    # are not affected by in-place mutations during the update.
                    backup_installed = copy.deepcopy(config.get("installed", []))
                    backup_hooks = {}
                    for hook_name, hook_list in config.get("hooks", {}).items():
                        if not isinstance(hook_list, list):
                            continue
                        ext_hooks = [h for h in hook_list if isinstance(h, dict) and h.get("extension") == extension_id]
                        if ext_hooks:
                            backup_hooks[hook_name] = ext_hooks

                # 5. Download new version
                zip_path = catalog.download_extension(extension_id)
                try:
                    # 6. Validate extension ID from ZIP BEFORE modifying installation
                    # Handle both root-level and nested extension.yml (GitHub auto-generated ZIPs)
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        import yaml
                        manifest_data = None
                        namelist = zf.namelist()

                        # First try root-level extension.yml
                        if "extension.yml" in namelist:
                            with zf.open("extension.yml") as f:
                                parsed_manifest = yaml.safe_load(f)
                                manifest_data = parsed_manifest if parsed_manifest is not None else {}
                        else:
                            # Look for extension.yml in a single top-level subdirectory
                            # (e.g., "repo-name-branch/extension.yml")
                            manifest_paths = [n for n in namelist if n.endswith("/extension.yml") and n.count("/") == 1]
                            if len(manifest_paths) == 1:
                                with zf.open(manifest_paths[0]) as f:
                                    parsed_manifest = yaml.safe_load(f)
                                    manifest_data = parsed_manifest if parsed_manifest is not None else {}

                        if manifest_data is None:
                            raise ValueError("Downloaded extension archive is missing 'extension.yml'")
                        if not isinstance(manifest_data, dict):
                            raise ValueError(
                                "Invalid extension manifest in downloaded archive: expected YAML mapping"
                            )
                        extension_data = manifest_data.get("extension", {})
                        if not isinstance(extension_data, dict):
                            raise ValueError(
                                "Invalid extension manifest in downloaded archive: expected 'extension' mapping"
                            )

                    zip_extension_id = extension_data.get("id")
                    if zip_extension_id != extension_id:
                        raise ValueError(
                            f"Extension ID mismatch: expected '{extension_id}', got '{zip_extension_id}'"
                        )

                    # 7. Remove old extension (handles command file cleanup and registry removal)
                    manager.remove(extension_id, keep_config=True)

                    # 8. Install new version
                    _ = manager.install_from_zip(zip_path, speckit_version)

                    # Restore user config files from backup after successful install.
                    new_extension_dir = manager.extensions_dir / extension_id
                    if backup_config_dir.exists() and new_extension_dir.exists():
                        for cfg_file in backup_config_dir.iterdir():
                            if cfg_file.is_file():
                                shutil.copy2(cfg_file, new_extension_dir / cfg_file.name)

                    # 9. Restore metadata from backup (installed_at, enabled state)
                    if backup_registry_entry and isinstance(backup_registry_entry, dict):
                        # Copy current registry entry to avoid mutating internal
                        # registry state before explicit restore().
                        current_metadata = manager.registry.get(extension_id)
                        if current_metadata is None or not isinstance(current_metadata, dict):
                            raise RuntimeError(
                                f"Registry entry for '{extension_id}' missing or corrupted after install — update incomplete"
                            )
                        new_metadata = dict(current_metadata)

                        # Preserve the original installation timestamp
                        if "installed_at" in backup_registry_entry:
                            new_metadata["installed_at"] = backup_registry_entry["installed_at"]

                        # Preserve the original priority (normalized to handle corruption)
                        if "priority" in backup_registry_entry:
                            new_metadata["priority"] = normalize_priority(backup_registry_entry["priority"])

                        # If extension was disabled before update, disable it again
                        if not backup_registry_entry.get("enabled", True):
                            new_metadata["enabled"] = False

                        # Use restore() instead of update() because update() always
                        # preserves the existing installed_at, ignoring our override
                        manager.registry.restore(extension_id, new_metadata)

                        # Also disable hooks in extensions.yml if extension was disabled
                        if not backup_registry_entry.get("enabled", True):
                            config = hook_executor.get_project_config()
                            if "hooks" in config:
                                for hook_name in config["hooks"]:
                                    for hook in config["hooks"][hook_name]:
                                        if hook.get("extension") == extension_id:
                                            hook["enabled"] = False
                                hook_executor.save_project_config(config)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

                # 10. Clean up backup on success
                if backup_base.exists():
                    shutil.rmtree(backup_base)

                console.print(f"   [green]✓[/green] Updated to v{update['available']}")
                updated_extensions.append(ext_name)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"   [red]✗[/red] Failed: {_escape_markup(str(e))}")
                failed_updates.append((ext_name, str(e)))

                # Rollback on failure
                console.print(f"   [yellow]↩[/yellow] Rolling back {safe_ext_name}...")

                try:
                    # Restore extension directory
                    # Only perform destructive rollback if backup exists (meaning we
                    # actually modified the extension). This avoids deleting a valid
                    # installation when failure happened before changes were made.
                    extension_dir = manager.extensions_dir / extension_id
                    if backup_ext_dir.exists():
                        if extension_dir.exists():
                            shutil.rmtree(extension_dir)
                        shutil.copytree(backup_ext_dir, extension_dir)

                    # Remove any NEW command files created by failed install
                    # (files that weren't in the original backup)
                    try:
                        new_registry_entry = manager.registry.get(extension_id)
                        if new_registry_entry is None or not isinstance(new_registry_entry, dict):
                            new_registered_commands = {}
                        else:
                            new_registered_commands = new_registry_entry.get("registered_commands", {})
                        for agent_name, cmd_names in new_registered_commands.items():
                            if agent_name not in registrar.AGENT_CONFIGS:
                                continue
                            agent_config = registrar.AGENT_CONFIGS[agent_name]
                            commands_dir = _AgentReg._resolve_agent_dir(
                                agent_name, agent_config, project_root
                            )

                            for cmd_name in cmd_names:
                                output_name = _AgentReg._compute_output_name(agent_name, cmd_name, agent_config)
                                cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                                # Delete if it exists and wasn't in our backup
                                if cmd_file.exists() and str(cmd_file) not in backed_up_command_files:
                                    cmd_file.unlink()

                                # Also handle copilot prompt files
                                if agent_name == "copilot":
                                    prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                                    if prompt_file.exists() and str(prompt_file) not in backed_up_command_files:
                                        prompt_file.unlink()
                    except KeyError:
                        pass  # No new registry entry exists, nothing to clean up

                    # Restore backed up command files
                    for original_path, backup_path in backed_up_command_files.items():
                        backup_file = Path(backup_path)
                        if backup_file.exists():
                            original_file = Path(original_path)
                            original_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(backup_file, original_file)

                    # Restore metadata in extensions.yml (hooks and installed list).
                    # Only run if backup step 4 was reached (backup_hooks is not None);
                    # otherwise we have no safe baseline to restore from and could corrupt
                    # the config by removing pre-existing hooks.
                    if backup_hooks is not None:
                        config = hook_executor.get_project_config()
                        if not isinstance(config, dict):
                            config = {}

                        modified = False

                        # 1. Restore hooks in extensions.yml
                        if not isinstance(config.get("hooks"), dict):
                            config["hooks"] = {}
                            modified = True

                        # Remove any hooks for this extension added by the failed install
                        for hook_name in list(config["hooks"].keys()):
                            hooks_list = config["hooks"][hook_name]
                            if not isinstance(hooks_list, list):
                                config["hooks"][hook_name] = []
                                modified = True
                                continue

                            original_len = len(hooks_list)
                            config["hooks"][hook_name] = [
                                h for h in hooks_list
                                if isinstance(h, dict) and h.get("extension") != extension_id
                            ]
                            if len(config["hooks"][hook_name]) != original_len:
                                modified = True

                        # Add back the backed-up hooks
                        if backup_hooks:
                            for hook_name, hooks in backup_hooks.items():
                                if not isinstance(config["hooks"].get(hook_name), list):
                                    config["hooks"][hook_name] = []
                                config["hooks"][hook_name].extend(hooks)
                                modified = True

                        # 2. Restore installed list in extensions.yml
                        if backup_installed is not UNSET:
                            if config.get("installed") != backup_installed:
                                config["installed"] = backup_installed
                                modified = True

                        if modified:
                            hook_executor.save_project_config(config)

                    # Restore registry entry (use restore() since entry was removed)
                    if backup_registry_entry:
                        manager.registry.restore(extension_id, backup_registry_entry)

                    console.print("   [green]✓[/green] Rollback successful")
                    # Clean up backup directory only on successful rollback
                    if backup_base.exists():
                        shutil.rmtree(backup_base)
                except Exception as rollback_error:
                    console.print(f"   [red]✗[/red] Rollback failed: {_escape_markup(str(rollback_error))}")
                    console.print(f"   [dim]Backup preserved at: {_escape_markup(str(backup_base))}[/dim]")

        # Summary
        console.print()
        if updated_extensions:
            console.print(f"[green]✓[/green] Successfully updated {len(updated_extensions)} extension(s)")
        if failed_updates:
            console.print(f"[red]✗[/red] Failed to update {len(failed_updates)} extension(s):")
            for ext_name, error in failed_updates:
                console.print(f"   • {_escape_markup(str(ext_name))}: {_escape_markup(str(error))}")
            raise typer.Exit(1)

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)


@extension_app.command("enable")
def extension_enable(
    extension: str = typer.Argument(help="Extension ID or name to enable"),
):
    """Enable a disabled extension."""
    from . import ExtensionManager, HookExecutor

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "enable")

    # Update registry
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    if metadata.get("enabled", True):
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' is already enabled[/yellow]")
        raise typer.Exit(0)

    manager.registry.update(extension_id, {"enabled": True})

    # Enable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = True
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' enabled")


@extension_app.command("disable")
def extension_disable(
    extension: str = typer.Argument(help="Extension ID or name to disable"),
):
    """Disable an extension without removing it."""
    from . import ExtensionManager, HookExecutor

    project_root = _require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "disable")

    # Update registry
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    if not metadata.get("enabled", True):
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' is already disabled[/yellow]")
        raise typer.Exit(0)

    manager.registry.update(extension_id, {"enabled": False})

    # Disable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = False
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' disabled")
    console.print("\nCommands will no longer be available. Hooks will not execute.")
    console.print(f"To re-enable: specify extension enable {_escape_markup(str(extension_id))}")


@extension_app.command("set-priority")
def extension_set_priority(
    extension: str = typer.Argument(help="Extension ID or name"),
    priority: int = typer.Argument(help="New priority (lower = higher precedence)"),
):
    """Set the resolution priority of an installed extension."""
    from . import ExtensionManager

    project_root = _require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _resolve_installed_extension(extension, installed, "set-priority")

    # Get current metadata
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    from . import normalize_priority
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
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' already has priority {priority}[/yellow]")
        raise typer.Exit(0)

    old_priority = normalize_priority(raw_priority)

    # Update priority
    manager.registry.update(extension_id, {"priority": priority})

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' priority changed: {old_priority} → {priority}")
    console.print("\n[dim]Lower priority = higher precedence in template resolution[/dim]")


def register(app: typer.Typer) -> None:
    """Attach the extension command group to the root Typer app."""
    app.add_typer(extension_app, name="extension")
