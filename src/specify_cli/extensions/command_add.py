"""Implementation of ``specify extension add``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.markup import escape as _escape_markup
from rich.panel import Panel

from .._console import console
from . import _commands


@_commands.extension_app.command("add")
def extension_add(
    extension: str = typer.Argument(help="Extension name or path"),
    dev: bool = typer.Option(False, "--dev", help="Install from local directory"),
    from_url: Optional[str] = typer.Option(None, "--from", help="Install from custom URL"),
    force: bool = typer.Option(False, "--force", help="Overwrite if already installed"),
    priority: int = typer.Option(10, "--priority", help="Resolution priority (lower = higher precedence, default 10)"),
    version: Optional[str] = typer.Option(None, "--version", help="Install an exact version from a catalog"),
):
    """Install an extension."""
    from . import ExtensionManager, ExtensionCatalog, ExtensionError, ValidationError, CompatibilityError, REINSTALL_COMMAND

    # Compatibility callers invoke this function directly, in which case
    # Typer supplies its OptionInfo object instead of a parsed option value.
    if not isinstance(version, str):
        version = None

    project_root = _commands._require_specify_project()
    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)
    if version is not None and (not version.strip() or dev or from_url):
        console.print("[red]Error:[/red] --version requires a catalog install (without --dev or --from).")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    speckit_version = _commands.get_speckit_version()

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
            # Read .hostname inside the try: parsing a malformed authority -- or
            # accessing .hostname on one, e.g. an invalid bracketed IPv6 host like
            # "https://[not-an-ip]/x.zip" -- can raise ValueError. Keeping both the
            # parse and the .hostname read inside the guard surfaces a clean
            # "Invalid URL" message instead of leaking a raw traceback past the
            # CLI. Reuse the value below.
            hostname = parsed.hostname
            parsed.port
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(from_url)}")
            raise typer.Exit(1)
        if not hostname:
            console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(from_url)}")
            raise typer.Exit(1)

        if not _commands.is_https_or_localhost_http(from_url):
            console.print("[red]Error:[/red] URL must use HTTPS for security.")
            console.print("HTTP is only allowed for loopback URLs.")
            raise typer.Exit(1)

        safe_url = _escape_markup(from_url)

        # Warn about untrusted sources — default-deny confirmation
        console.print()
        console.print(Panel(
            f"[bold]You are installing an extension directly from an external URL,\n"
            f"bypassing your trusted (install-allowed) extension catalogs.[/bold]\n\n"
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
                # Install from URL archive via the shared hardened downloader
                # (HTTPS enforcement, authenticated redirect-guarded fetch,
                # bounded read, archive-format detection, TOCTOU-safe transient
                # archive). Same path used by ``specify init --extension <url>``.
                console.print(f"Downloading from {safe_url}...")
                manifest = _commands.install_extension_from_url(
                    manager,
                    project_root,
                    from_url,
                    speckit_version,
                    priority=priority,
                    force=force,
                )

            else:
                # Try bundled extensions first (shipped with spec-kit)
                bundled_path = (
                    _commands._locate_bundled_extension(extension)
                    if version is None else None
                )
                if bundled_path is not None:
                    manifest = manager.install_from_directory(
                        bundled_path, speckit_version, priority=priority, force=force
                    )
                else:
                    # Install from catalog (also resolves display names to IDs)
                    catalog = ExtensionCatalog(project_root)

                    # Check if extension exists in catalog (supports both ID and display name)
                    ext_info, catalog_error = _commands._resolve_catalog_extension(
                        extension, catalog, "add"
                    )
                    if catalog_error:
                        console.print(f"[red]Error:[/red] Could not query extension catalog: {_escape_markup(str(catalog_error))}")
                        raise typer.Exit(1)
                    if not ext_info:
                        console.print(f"[red]Error:[/red] Extension '{safe_extension}' not found in catalog")
                        console.print("\nSearch available extensions:")
                        console.print("  specify extension search")
                        raise typer.Exit(1)

                    if version is not None:
                        # Resolve within the winning catalog source. A missing
                        # historical release must not fall through to a lower
                        # priority (or discovery-only) catalog.
                        selected = catalog.get_extension_info(ext_info["id"], version)
                        if selected is None:
                            console.print(
                                f"[red]Error:[/red] Extension '{_escape_markup(str(ext_info['id']))}' "
                                f"has no catalog release for version {_escape_markup(version)}."
                            )
                            raise typer.Exit(1)
                        ext_info = selected
                        if not ext_info.get("_install_allowed", True):
                            console.print(
                                f"[red]Error:[/red] Extension '{_escape_markup(str(ext_info['id']))}' "
                                "is from a discovery-only catalog and cannot be installed."
                            )
                            raise typer.Exit(1)

                    # If catalog resolved a display name to an ID, check bundled again
                    resolved_id = ext_info['id']
                    if version is not None and ext_info.get("bundled") and not ext_info.get("download_url"):
                        from . import ExtensionManifest

                        candidate = _commands._locate_bundled_extension(resolved_id)
                        if candidate is not None:
                            bundled_manifest = ExtensionManifest(candidate / "extension.yml")
                            if bundled_manifest.version == version:
                                bundled_path = candidate
                                manifest = manager.install_from_directory(
                                    bundled_path, speckit_version, priority=priority, force=force
                                )
                        if bundled_path is None:
                            console.print(
                                f"[red]Error:[/red] Bundled extension '{_escape_markup(resolved_id)}' "
                                f"version {_escape_markup(version)} is not shipped with this Spec Kit release. "
                                "Upgrade Spec Kit or choose an available catalog archive."
                            )
                            raise typer.Exit(1)
                    if version is None and resolved_id != extension:
                        bundled_path = _commands._locate_bundled_extension(resolved_id)
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
                            resolved_id = _commands._command_safe_id(ext_info["id"])
                            console.print(
                                f"[red]Error:[/red] '{safe_extension}' was found in the "
                                f"'{catalog_name}' catalog, which is discovery-only — a search "
                                f"surface, not an install source."
                            )
                            console.print(
                                "\nDiscovery-only catalogs are intentionally not installable so "
                                "unvetted extensions can't be pulled in without review. Don't flip "
                                "such a catalog to install_allowed. Instead, once you've vetted this "
                                "extension:"
                            )
                            console.print(
                                f"  • install it directly from its archive URL:\n"
                                f"      specify extension add {resolved_id} --from <archive-url>"
                            )
                            console.print(
                                "  • or add it to a catalog you curate and control "
                                "(install_allowed: true)."
                            )
                            raise typer.Exit(1)

                        # Download extension archive (use the resolved catalog ID).
                        extension_id = ext_info['id']
                        console.print(f"Downloading {_escape_markup(str(ext_info['name']))} v{_escape_markup(str(ext_info.get('version', 'unknown')))}...")
                        archive_path = (
                            catalog.download_extension_info(ext_info)
                            if version is not None
                            else catalog.download_extension(extension_id)
                        )

                        try:
                            manifest = manager.install_from_zip(
                                archive_path,
                                speckit_version,
                                priority=priority,
                                force=force,
                                catalog_name=ext_info.get("_catalog_name"),
                                **(
                                    {"expected_id": extension_id, "expected_version": version}
                                    if version is not None else {}
                                ),
                            )
                        finally:
                            archive_path.unlink(missing_ok=True)

        console.print("\n[green]✓[/green] Extension installed successfully!")
        console.print(f"\n[bold]{_escape_markup(str(manifest.name))}[/bold] (v{_escape_markup(str(manifest.version))})")
        console.print(f"  {_escape_markup(str(manifest.description))}")

        # #1: regenerate native event config for installed event-capable
        # integrations so the new extension's events take effect immediately.
        _commands._refresh_events_and_warn(project_root)

        for warning in manifest.warnings:
            console.print(f"\n[yellow]⚠  Compatibility warning:[/yellow] {_escape_markup(str(warning))}")

        selected_ai = _commands.load_init_options(project_root).get("ai")
        is_cline = selected_ai == "cline"
        is_forge = selected_ai == "forge"

        if is_cline:
            from specify_cli.integrations.cline import format_cline_command_name
        if is_forge:
            from specify_cli.integrations.forge import format_forge_command_name

        console.print("\n[bold cyan]Provided commands:[/bold cyan]")
        for cmd in manifest.commands:
            cmd_name = cmd['name']
            if is_cline:
                cmd_name = format_cline_command_name(cmd_name)
            elif is_forge:
                cmd_name = format_forge_command_name(cmd_name)
            console.print(f"  • {_escape_markup(str(cmd_name))} - {_escape_markup(str(cmd.get('description', '')))}")

        # Report agent skills registration
        reg_meta = manager.registry.get(manifest.id)
        reg_skills = reg_meta.get("registered_skills", []) if reg_meta else []
        # Normalize to guard against corrupted registry entries
        if not isinstance(reg_skills, list):
            reg_skills = []
        if reg_skills:
            console.print(f"\n[green]✓[/green] {len(reg_skills)} agent skill(s) auto-registered")

        # Scaffold config templates automatically
        deployed, skipped, failed = manager.scaffold_config(manifest.id)
        config_home = f".specify/extensions/{_escape_markup(str(manifest.id))}"
        if deployed:
            console.print("\n[bold cyan]Config scaffolded:[/bold cyan]")
            for cfg in deployed:
                console.print(f"  • {config_home}/{_escape_markup(str(cfg))}")
        if skipped:
            console.print(f"\n[dim]Config files already exist (preserved): {_escape_markup(', '.join(skipped))}[/dim]")
        if failed:
            console.print(
                f"\n[yellow]Warning:[/yellow] Config templates not scaffolded: "
                f"{_escape_markup(', '.join(failed))}. "
                "Verify the extension manifest and template files."
            )

        # Only warn when configuration is actually unresolved. Scaffolding that
        # deployed or preserved every template has already answered this, and an
        # extension without provides.config has nothing to configure; the blanket
        # warning contradicted the output directly above it.
        if failed or not (deployed or skipped):
            console.print("\n[yellow]⚠[/yellow]  Configuration may be required")
            console.print(f"   Check: {config_home}/")

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except CompatibilityError as e:
        console.print(f"\n[red]Compatibility Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
