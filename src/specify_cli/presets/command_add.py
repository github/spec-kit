"""Implementation of the ``specify preset add`` command."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from .._download_security import (
    archive_format_from_name,
    archive_suffix,
    detect_archive_format,
    is_https_or_localhost_http,
    is_safe_download_redirect,
)
from . import _commands
from ._commands import preset_app


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
    console.print(
        "[yellow]![/yellow]  This preset depends on extensions that are not satisfied:"
    )
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
                f"    [yellow]{extension_id}[/yellow] has an unreadable registry entry"
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
            console.print(
                f"    [yellow]{extension_id}[/yellow] is installed but disabled"
            )
            label, remedy = "Enable with", f"specify extension enable {command_id}"
        else:
            console.print(
                f"    [yellow]{extension_id}[/yellow] "
                f"{_escape_markup(dep['installed'])} does not satisfy "
                f"{_escape_markup(dep['version'])}"
            )
            label = "Needs"
            remedy = (
                f"a release of {command_id} satisfying {_escape_markup(dep['version'])}"
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
        dep["reason"] in ("missing", "corrupt", "stale", "disabled") for dep in unmet
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


@preset_app.command("add")
def preset_add(
    preset_id: str = typer.Argument(None, help="Preset ID to install from catalog"),
    from_url: str = typer.Option(
        None,
        "--from",
        help="Install from a .zip, .tar.gz, or .tgz URL",
    ),
    dev: str = typer.Option(
        None, "--dev", help="Install from local directory (development mode)"
    ),
    priority: int = typer.Option(
        10,
        "--priority",
        help="Resolution priority (lower = higher precedence, default 10)",
    ),
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
    _commands._validate_priority(priority)

    manager = PresetManager(project_root)
    speckit_version = get_speckit_version()

    try:
        if dev:
            dev_path = Path(dev).resolve()
            if not dev_path.exists():
                console.print(f"[red]Error:[/red] Directory not found: {dev}")
                raise typer.Exit(1)

            console.print(f"Installing preset from [cyan]{dev_path}[/cyan]...")
            manifest = manager.install_from_directory(
                dev_path, speckit_version, priority
            )
            console.print(
                f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})"
            )

        elif from_url:
            # Validate URL scheme before downloading
            from urllib.parse import urlparse as _urlparse

            try:
                _parsed = _urlparse(from_url)
                _ = _parsed.port
            except ValueError:
                console.print(
                    f"[red]Error:[/red] Invalid URL: {_escape_markup(from_url)}"
                )
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

            console.print(
                f"Installing preset from [cyan]{_escape_markup(from_url)}[/cyan]..."
            )
            import tempfile
            import urllib.error

            with tempfile.TemporaryDirectory() as tmpdir:
                archive_path = Path(tmpdir) / "preset.archive"
                try:
                    from specify_cli._github_http import (
                        resolve_github_release_asset_api_url,
                    )
                    from specify_cli.authentication.http import github_provider_hosts
                    from specify_cli.authentication.http import open_url as _open_url

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
                        final_url = (
                            response.geturl()
                            if hasattr(response, "geturl")
                            else from_url
                        )
                        if not is_https_or_localhost_http(final_url):
                            console.print(
                                "[red]Error:[/red] Preset URL redirected to a disallowed URL: "
                                f"{final_url}. Redirect targets must use HTTPS with a hostname, "
                                "or HTTP for localhost (127.0.0.1, ::1)."
                            )
                            raise typer.Exit(1)
                        archive_data = _commands.read_response_limited(
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

            console.print(
                f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})"
            )

        elif preset_id:
            # Try bundled preset first, then catalog
            bundled_path = _locate_bundled_preset(preset_id)
            if bundled_path:
                console.print(f"Installing bundled preset [cyan]{preset_id}[/cyan]...")
                manifest = manager.install_from_directory(
                    bundled_path, speckit_version, priority
                )
                console.print(
                    f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})"
                )
            else:
                catalog = PresetCatalog(project_root)
                pack_info = catalog.get_pack_info(preset_id)

                if not pack_info:
                    console.print(
                        f"[red]Error:[/red] Preset '{preset_id}' not found in catalog"
                    )
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
                    console.print(
                        f"[red]Error:[/red] Preset '{preset_id}' is from the '{catalog_name}' catalog which is discovery-only (install not allowed)."
                    )
                    console.print(
                        "Add the catalog with --install-allowed or install from the preset's repository directly with --from."
                    )
                    raise typer.Exit(1)

                console.print(
                    f"Installing preset [cyan]{pack_info.get('name', preset_id)}[/cyan]..."
                )

                try:
                    archive_path = catalog.download_pack(preset_id)
                    manifest = manager.install_from_zip(
                        archive_path,
                        speckit_version,
                        priority,
                        catalog_name=pack_info.get("_catalog_name"),
                    )
                    console.print(
                        f"[green]✓[/green] Preset '{manifest.name}' v{manifest.version} installed (priority {priority})"
                    )
                finally:
                    if "archive_path" in locals() and archive_path.exists():
                        archive_path.unlink(missing_ok=True)
        else:
            console.print(
                "[red]Error:[/red] Specify a preset ID, --from URL, or --dev path"
            )
            raise typer.Exit(1)

        # Every install path above binds `manifest` and the no-source branch
        # exits, so one call here covers --dev, --from, and catalog installs
        # alike. Warns rather than fails: the preset is installed and its
        # overrides fall through to the core workflow without the extension.
        _commands._warn_unmet_extension_dependencies(manager, manifest)

    except PresetCompatibilityError as e:
        console.print(f"[red]Compatibility Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except PresetValidationError as e:
        console.print(f"[red]Validation Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
    except PresetError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)
