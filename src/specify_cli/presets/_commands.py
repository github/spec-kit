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
import shutil
import tempfile
from pathlib import Path

import typer
import yaml
from rich.markup import escape as _escape_markup

from .._console import console
from .._download_security import (
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


def _fetch_preset_archive_data(
    url: str,
    error_type: type[Exception],
) -> tuple[bytes, str | None, str]:
    """Fetch bounded archive bytes after validating URL and redirects."""
    import urllib.error
    from urllib.parse import urlparse

    from specify_cli._github_http import resolve_github_release_asset_api_url
    from specify_cli.authentication.http import github_provider_hosts, open_url

    try:
        parsed = urlparse(url)
        _ = parsed.port
    except ValueError as exc:
        raise error_type(f"Invalid URL: {url}") from exc
    if not is_https_or_localhost_http(url):
        raise error_type("URL must use HTTPS (HTTP is only allowed for localhost)")

    def validate_redirect(old_url, new_url):
        if not is_safe_download_redirect(old_url, new_url):
            raise error_type(
                "redirect target must use HTTPS or remain on localhost"
            )

    try:
        resolved_url = resolve_github_release_asset_api_url(
            url, open_url, github_hosts=github_provider_hosts()
        )
        download_url = resolved_url or url
        extra_headers = {"Accept": "application/octet-stream"} if resolved_url else None
        with open_url(
            download_url,
            timeout=60,
            extra_headers=extra_headers,
            redirect_validator=validate_redirect,
        ) as response:
            final_url = (
                response.geturl() if hasattr(response, "geturl") else download_url
            )
            if not is_https_or_localhost_http(final_url):
                raise error_type(
                    "Preset URL redirected to a disallowed URL: "
                    f"{final_url}. Redirect targets must use HTTPS with a hostname, "
                    "or HTTP for localhost (127.0.0.1, ::1)."
                )
            data = read_response_limited(
                response, error_type=error_type, label=f"preset {url}"
            )
            content_type = (
                response.getheader("Content-Type")
                if hasattr(response, "getheader")
                else None
            )
    except urllib.error.URLError as exc:
        raise error_type(f"Failed to download preset: {exc}") from exc
    return data, content_type, final_url


def _write_preset_archive(
    data: bytes,
    source_url: str,
    content_type: str | None,
    error_type: type[Exception],
) -> Path:
    """Write downloaded bytes to a temporary archive with a detected suffix."""
    fd, name = tempfile.mkstemp(prefix="speckit-preset-update-", suffix=".archive")
    path = Path(name)
    try:
        os.close(fd)
        path.write_bytes(data)
        detected = detect_archive_format(
            path,
            source_name=source_url,
            content_type=content_type,
            error_type=error_type,
        )
        detected_path = path.with_suffix(archive_suffix(detected))
        os.replace(path, detected_path)
        path = detected_path
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _download_preset_archive(url: str, error_type: type[Exception]) -> Path:
    """Download and classify a preset archive into a temporary file."""
    data, content_type, final_url = _fetch_preset_archive_data(url, error_type)
    return _write_preset_archive(data, final_url, content_type, error_type)


def _cleanup_archive(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        console.print(
            f"[yellow]Warning:[/yellow] Could not remove temporary archive "
            f"'{path}': {exc}"
        )


def _warn_unmet_extension_dependencies(manager, manifest) -> None:
    """Warn when a preset's declared extension dependencies are unsatisfied.

    A preset whose command overrides call into an extension is inert without
    it, but the overrides still fall through to the core workflow, so nothing
    breaks -- it just silently does less than the user expects. Naming the
    missing extension and the command that installs it turns that silence into
    something actionable. See issue #4231.
    """
    from ..extensions._commands import _command_safe_id

    unmet = manager.find_unmet_extension_dependencies(manifest)
    if not unmet:
        return

    console.print()
    console.print("[yellow]![/yellow]  This preset depends on extensions that are not satisfied:")
    needs_catalog = False
    for dep in unmet:
        uses_catalog = False
        extension_id = _escape_markup(dep["id"])
        # The displayed id only needs Rich escaping, but a suggested command
        # has to survive Typer's parser: `^[a-z0-9-]+$` admits a leading
        # hyphen, so an id like `--force` would render as an option rather
        # than the positional argument. _command_safe_id substitutes a
        # placeholder in that case, the same way extension commands do.
        command_id = _command_safe_id(dep["id"])
        reason = dep["reason"]
        # The remediation has to match the reason. `extension add` refuses an
        # already-installed extension without --force, and `extension update`
        # only moves forward to the catalog release. A general PEP 440
        # constraint may require an exact version, an upper bound, or a
        # downgrade, so do not promise that update will satisfy it.
        if reason == "missing":
            console.print(f"    [yellow]{extension_id}[/yellow] is not installed")
            label, remedy = "Install with", f"specify extension add {command_id}"
            uses_catalog = True
        elif reason == "corrupt":
            console.print(
                f"    [yellow]{extension_id}[/yellow] has an unreadable "
                "registry entry"
            )
            # is_installed() still counts the key, so a plain add is refused.
            label = "Reinstall with"
            remedy = f"specify extension add {command_id} --force"
            uses_catalog = True
        elif reason == "stale":
            console.print(
                f"    [yellow]{extension_id}[/yellow] is registered but its "
                "files are missing"
            )
            label = "Reinstall with"
            remedy = f"specify extension add {command_id} --force"
            uses_catalog = True
        elif reason == "disabled":
            console.print(f"    [yellow]{extension_id}[/yellow] is installed but disabled")
            label, remedy = "Enable with", f"specify extension enable {command_id}"
        else:
            console.print(
                f"    [yellow]{extension_id}[/yellow] "
                f"{_escape_markup(dep['installed'])} does not satisfy "
                f"{_escape_markup(dep['version'])}"
            )
            label = "Needs"
            remedy = (
                f"a release of {command_id} satisfying "
                f"{_escape_markup(dep['version'])}"
            )
        console.print(f"      {label}: {remedy}")
        needs_catalog = needs_catalog or uses_catalog
    console.print()
    # The consequence differs by reason and must not be overstated. An
    # unavailable extension contributes nothing, so those features are simply
    # inert. A version mismatch is the opposite: the extension is installed and
    # enabled, so the preset does invoke it -- the combination is just untested
    # against the declared constraint, which is not the same as "safe".
    console.print("[dim]The preset is installed.[/dim]")
    if any(
        dep["reason"] in ("missing", "corrupt", "stale", "disabled")
        for dep in unmet
    ):
        console.print(
            "[dim]Anything relying on an unavailable extension does nothing "
            "until that is resolved.[/dim]"
        )
    if any(dep["reason"] == "version" for dep in unmet):
        console.print(
            "[dim]Where only a version constraint is unmet the extension is "
            "still used, so it may not behave as the preset expects.[/dim]"
        )
    if needs_catalog:
        # `extension add <id>` resolves through the catalogs, and the default
        # community catalog is discovery-only, so installing by id is refused
        # for anything listed only there -- true of every extension motivating
        # this feature. Knowing which applies would mean a catalog fetch, and
        # this runs on an install path that touches no network, so describe
        # the outcome instead of asserting the command succeeds. The rejection
        # itself prints the exact --from form, so this is a signpost rather
        # than a dead end.
        console.print(
            "[dim]If an extension is listed only in a discovery-only catalog, "
            "that command is refused and prints the "
            "--from <archive-url> form to use instead.[/dim]"
        )


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
        PresetCatalog,
        PresetCompatibilityError,
        PresetError,
        PresetManager,
        PresetValidationError,
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
                _ = _parsed.port
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(from_url)}")
                raise typer.Exit(1)

            if not is_https_or_localhost_http(from_url):
                console.print(
                    "[red]Error:[/red] URL must use HTTPS with a hostname and be "
                    "a valid URL with a host. HTTP is only allowed for localhost, "
                    "127.0.0.1, and ::1."
                )
                raise typer.Exit(1)

            console.print(f"Installing preset from [cyan]{_escape_markup(from_url)}[/cyan]...")
            archive_path = None
            try:
                archive_path = _download_preset_archive(from_url, PresetError)
            except PresetError as e:
                console.print(
                    f"[red]Error:[/red] Failed to download: "
                    f"{_escape_markup(str(e))}"
                )
                raise typer.Exit(1)
            try:
                manifest = manager.install_from_zip(
                    archive_path,
                    speckit_version,
                    priority,
                )
            finally:
                if archive_path is not None and archive_path.exists():
                    _cleanup_archive(archive_path)
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
                        _cleanup_archive(archive_path)
        else:
            console.print("[red]Error:[/red] Specify a preset ID, --from URL, or --dev path")
            raise typer.Exit(1)

        # Every install path above binds `manifest` and the no-source branch
        # exits, so one call here covers --dev, --from, and catalog installs
        # alike. Warns rather than fails: the preset is installed and its
        # overrides fall through to the core workflow without the extension.
        _warn_unmet_extension_dependencies(manager, manifest)

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


@preset_app.command("update")
def preset_update(
    preset_id: str = typer.Argument(None, help="Preset ID to update (or all)"),
    from_url: str = typer.Option(None, "--from", help="Update from an archive URL"),
    dev: str = typer.Option(None, "--dev", help="Update from a local directory"),
    priority: int = typer.Option(None, "--priority", help="New priority"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without writing"),
    all_presets: bool = typer.Option(False, "--all", help="Update all installed presets"),
):
    """Update one preset, or all installed presets."""
    from packaging import version as pkg_version

    from .. import (
        _locate_bundled_preset,
        _require_specify_project,
        get_speckit_version,
    )
    from . import (
        PresetCatalog,
        PresetCompatibilityError,
        PresetError,
        PresetManager,
        PresetResolver,
        PresetValidationError,
        _constitution_is_generated,
    )

    project_root = _require_specify_project()
    manager = PresetManager(project_root)
    if priority is not None and not (all_presets or not preset_id) and priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)
    if from_url and dev:
        console.print("[red]Error:[/red] Use only one of --from or --dev")
        raise typer.Exit(1)
    if preset_id and all_presets:
        console.print("[red]Error:[/red] Use either a preset ID or --all, not both")
        raise typer.Exit(1)
    if (from_url or dev) and (not preset_id or all_presets):
        console.print("[red]Error:[/red] --from and --dev require a preset ID")
        raise typer.Exit(1)

    installed = manager.list_installed()
    bulk = all_presets or not preset_id
    effective_priority = None if bulk else priority
    ids = [preset_id] if not bulk else [item["id"] for item in installed]
    if not ids:
        console.print("[yellow]No presets installed.[/yellow]")
        return

    dry_run_cache = (
        Path(tempfile.mkdtemp(prefix="speckit-preset-dry-run-"))
        if dry_run
        else None
    )
    catalog = PresetCatalog(project_root, cache_dir=dry_run_cache)
    speckit_version = get_speckit_version()
    outcomes = []
    catalog_candidates = {}
    catalog_sources = {}

    if bulk:
        actionable_ids = []
        catalog_archives = {}
        for item_id in ids:
            safe_id = _escape_markup(str(item_id))
            metadata = manager.registry.get(item_id)
            archive_path = None
            try:
                if not manager.registry.is_installed(item_id):
                    raise PresetError(
                        f"Preset '{item_id}' is not installed; use 'preset add' instead"
                    )
                if metadata is None or "version" not in metadata:
                    raise PresetError("registry entry is missing or corrupt")
                installed_version = pkg_version.Version(str(metadata["version"]))
                pack_info = catalog.get_pack_info(item_id)
                if not pack_info:
                    raise PresetError(
                        "source not re-resolvable — supply --from/--dev explicitly"
                    )
                if not pack_info.get("_install_allowed", True):
                    raise PresetError(
                        f"updates are not allowed from "
                        f"'{pack_info.get('_catalog_name', 'catalog')}'"
                    )
                catalog_version = pkg_version.Version(str(pack_info["version"]))
                if catalog_version <= installed_version and effective_priority is None:
                    console.print(
                        f"[dim]• {safe_id}: Up to date, skipped "
                        f"(v{installed_version})[/dim]"
                    )
                    outcomes.append("skipped")
                    continue
                if pack_info.get("bundled") and not pack_info.get("download_url"):
                    source_path = _locate_bundled_preset(item_id)
                    if source_path is None:
                        raise PresetError(
                            f"Preset '{item_id}' is bundled with spec-kit but "
                            "could not be found in the installed package"
                        )
                    manager.update_from_directory(
                        source_path,
                        speckit_version,
                        pack_id=item_id,
                        priority=effective_priority,
                        dry_run=True,
                        expected_version=str(pack_info["version"]),
                    )
                    catalog_sources[item_id] = source_path
                else:
                    archive_path = catalog.download_pack(item_id)
                    manager.update_from_archive(
                        archive_path,
                        speckit_version,
                        pack_id=item_id,
                        priority=effective_priority,
                        dry_run=True,
                        expected_version=str(pack_info["version"]),
                    )
                catalog_candidates[item_id] = pack_info
                catalog_archives[item_id] = archive_path
                actionable_ids.append(item_id)
            except PresetCompatibilityError as exc:
                detail = _escape_markup(str(exc).replace("\n", " "))
                console.print(
                    f"[yellow]•[/yellow] {safe_id}: skipped — {detail}"
                )
                outcomes.append("skipped")
                if archive_path is not None:
                    _cleanup_archive(archive_path)
            except (KeyError, TypeError, ValueError):
                detail = _escape_markup(
                    f"invalid version metadata for preset '{item_id}'"
                )
                console.print(f"[yellow]•[/yellow] {safe_id}: failed — {detail}")
                outcomes.append("failed")
                if archive_path is not None:
                    _cleanup_archive(archive_path)
            except (OSError, PresetValidationError, PresetError) as exc:
                detail = _escape_markup(str(exc).replace("\n", " "))
                console.print(f"[yellow]•[/yellow] {safe_id}: failed — {detail}")
                outcomes.append("failed")
                if archive_path is not None:
                    _cleanup_archive(archive_path)

        ids = actionable_ids
        if not ids:
            if any(outcome == "failed" for outcome in outcomes):
                if dry_run_cache is not None:
                    shutil.rmtree(dry_run_cache, ignore_errors=True)
                raise typer.Exit(1)
            if dry_run_cache is not None:
                shutil.rmtree(dry_run_cache, ignore_errors=True)
            return
        if priority is not None:
            console.print(
                "[yellow]Note:[/yellow] --priority is ignored for bulk updates; "
                "existing preset priorities will be preserved."
            )
        if not typer.confirm("Update all installed presets?"):
            for archive_path in catalog_archives.values():
                if archive_path is not None:
                    _cleanup_archive(archive_path)
            console.print("Cancelled")
            if dry_run_cache is not None:
                shutil.rmtree(dry_run_cache, ignore_errors=True)
            return

    for item_id in ids:
        safe_id = _escape_markup(str(item_id))
        source_kind = "catalog"
        archive_path = catalog_archives.get(item_id) if bulk else None
        try:
            metadata = manager.registry.get(item_id)
            if not manager.registry.is_installed(item_id):
                raise PresetError(
                    f"Preset '{item_id}' is not installed; use 'preset add' instead"
                )
            if metadata is None or "version" not in metadata:
                raise PresetError("registry entry is missing or corrupt")
            try:
                installed_version = pkg_version.Version(str(metadata["version"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise PresetError(
                    f"invalid installed version for preset '{item_id}'"
                ) from exc
            source_path = None
            pack_info = None
            if dev:
                source_kind = "dev"
                source_path = Path(dev).resolve()
                if not source_path.is_dir():
                    raise PresetError(f"Directory not found: {dev}")
            elif from_url:
                source_kind = "url"
                archive_path = _download_preset_archive(from_url, PresetError)
            else:
                pack_info = catalog_candidates.get(item_id) or catalog.get_pack_info(item_id)
                if not pack_info:
                    raise PresetError(
                        "source not re-resolvable — supply --from/--dev explicitly"
                    )
                if not pack_info.get("_install_allowed", True):
                    raise PresetError(
                        f"updates are not allowed from "
                        f"'{pack_info.get('_catalog_name', 'catalog')}'"
                    )
                try:
                    catalog_version = pkg_version.Version(str(pack_info["version"]))
                except (KeyError, TypeError, ValueError) as exc:
                    raise PresetError(
                        f"catalog entry for preset '{item_id}' has an invalid version"
                    ) from exc
                if catalog_version < installed_version or (
                    catalog_version == installed_version and effective_priority is None
                ):
                    console.print(
                        f"[dim]• {safe_id}: Up to date, skipped "
                        f"(v{installed_version})[/dim]"
                    )
                    outcomes.append("skipped")
                    continue
                if pack_info.get("bundled") and not pack_info.get("download_url"):
                    source_path = catalog_sources.get(item_id) or _locate_bundled_preset(
                        item_id
                    )
                    if source_path is None:
                        raise PresetError(
                            f"Preset '{item_id}' is bundled with spec-kit but "
                            "could not be found in the installed package"
                        )
                elif archive_path is None:
                    archive_path = catalog.download_pack(item_id)

            constitution_path = (
                project_root / ".specify" / "memory" / "constitution.md"
            )
            constitution_before = (
                constitution_path.read_bytes() if constitution_path.exists() else None
            )
            if source_kind == "dev" or source_path is not None:
                manifest, diff = manager.update_from_directory(
                    source_path,
                    speckit_version,
                    pack_id=item_id,
                    priority=effective_priority,
                    dry_run=dry_run,
                    expected_version=(
                        str(pack_info["version"]) if pack_info is not None else None
                    ),
                )
            else:
                manifest, diff = manager.update_from_archive(
                    archive_path,
                    speckit_version,
                    pack_id=item_id,
                    priority=effective_priority,
                    dry_run=dry_run,
                    expected_version=(
                        str(pack_info["version"]) if pack_info is not None else None
                    ),
                )
            action = "would update" if dry_run else "updated"
            added_commands = sum(
                entry["identity"][1] == "command" for entry in diff["added"]
            )
            removed_commands = sum(
                entry["identity"][1] == "command" for entry in diff["removed"]
            )
            changed_commands = sum(
                entry["identity"][1] == "command" for entry in diff["changed"]
            )
            constitution_after = (
                constitution_path.read_bytes() if constitution_path.exists() else None
            )
            constitution_diff = diff.get("_constitution_changed", False) or any(
                entry["identity"] == ("constitution-template", "template")
                for category in ("added", "removed", "changed")
                for entry in diff[category]
            )
            if dry_run:
                sync_metadata = manager.registry.get("constitution-sync")
                constitution_can_reconcile = (
                    bool(diff.get("_constitution_layer"))
                    and isinstance(sync_metadata, dict)
                    and sync_metadata.get("enabled", True)
                    and constitution_path.exists()
                    and _constitution_is_generated(
                        project_root,
                        constitution_path,
                        PresetResolver(project_root),
                    )
                )
                constitution_status = (
                    "constitution change planned"
                    if constitution_can_reconcile
                    and (constitution_diff or priority is not None)
                    else "constitution unchanged"
                )
            else:
                constitution_status = (
                    "constitution unchanged"
                    if constitution_before == constitution_after
                    else "constitution reconciled"
                )
            console.print(
                f"[green]✓[/green] {safe_id}: {action} to v{manifest.version} "
                f"(+{added_commands} commands, -{removed_commands} commands, "
                f"~{changed_commands} commands, "
                f"{constitution_status}, "
                f"priority {'kept at ' + str(metadata.get('priority', 10)) if effective_priority is None else 'set to ' + str(effective_priority)})"
            )
            if dry_run:
                for category in ("added", "removed", "changed", "unchanged"):
                    identities = [
                        f"{name} ({template_type})"
                        for (name, template_type) in (
                            entry["identity"] for entry in diff[category]
                        )
                    ]
                    if identities:
                        console.print(
                            f"  {category}: {', '.join(identities)}"
                        )
                console.print("  planned actions: stage, validate, atomically swap, reconcile")
            else:
                _warn_unmet_extension_dependencies(manager, manifest)
            outcomes.append("updated")
        except OSError as exc:
            detail = _escape_markup(str(exc).replace("\n", " "))
            console.print(f"[yellow]•[/yellow] {safe_id}: failed — {detail}")
            outcomes.append("failed")
        except (PresetCompatibilityError, PresetValidationError, PresetError) as exc:
            detail = _escape_markup(str(exc).replace("\n", " "))
            prefix = (
                "skipped"
                if bulk and isinstance(exc, PresetCompatibilityError)
                else "failed"
            )
            console.print(f"[yellow]•[/yellow] {safe_id}: {prefix} — {detail}")
            outcomes.append(prefix)
        finally:
            if archive_path is not None:
                _cleanup_archive(archive_path)

    if any(outcome == "failed" for outcome in outcomes):
        if dry_run_cache is not None:
            shutil.rmtree(dry_run_cache, ignore_errors=True)
        raise typer.Exit(1)
    if dry_run_cache is not None:
        shutil.rmtree(dry_run_cache, ignore_errors=True)


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
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            config_label = _display_project_path(project_root, config_path)
            console.print(f"[red]Error:[/red] Failed to read {_escape_markup(str(config_label))}: {_escape_markup(str(e))}")
            raise typer.Exit(1)
        if config is None:
            config = {}
        elif not isinstance(config, dict):
            console.print("[red]Error:[/red] Invalid catalog config: expected a mapping.")
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
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to read preset catalog config: {e}")
        raise typer.Exit(1)
    if config is None:
        config = {}
    elif not isinstance(config, dict):
        console.print("[red]Error:[/red] Invalid catalog config: expected a mapping.")
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
