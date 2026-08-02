"""specify extension * and catalog * command handlers — app objects and register().

Moved out of __init__.py (PR-7/8). Handlers reference helpers that remain in
the package root (`_require_specify_project`, `_locate_bundled_extension`,
`load_init_options`, `_display_project_path`) through the thin shims below,
which re-fetch from the parent package at call time so test monkeypatching of
`specify_cli.<helper>` keeps working.
"""
from __future__ import annotations

import errno
import hashlib
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

import typer
import yaml
from rich.markup import escape as _escape_markup
from rich.panel import Panel
from rich.table import Table

from .._console import console
from .._assets import get_speckit_version
from .._download_security import (
    archive_format_from_name,
    detect_archive_format,
    is_https_or_localhost_http,
    read_response_limited,
    safe_extract_archive,
)
from .._init_options import is_ai_skills_enabled

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


def _refresh_events_and_warn(project_root: Path) -> None:
    """Refresh native event config and surface failures (R3).

    The extension has already been added/removed/enabled/disabled by the time
    this runs, so a refresh failure must not abort the command — but it must
    be surfaced, because a stale native hook may still be active (e.g. a
    disabled extension's hook still resolves and runs). Prints a warning with
    the per-integration failures so the user knows deactivation was incomplete.
    """
    from ..events import EventRefreshError, refresh_integration_events

    try:
        refresh_integration_events(project_root)
    except EventRefreshError as exc:
        console.print(
            f"\n[yellow]⚠[/yellow]  Extension updated, but event refresh failed "
            f"for {len(exc.failures)} integration(s); a stale native hook may "
            f"still be active. Re-run [cyan]specify integration upgrade "
            f"<key>[cyan][/cyan][/cyan] to retry."
        )
        for key, detail in exc.failures:
            console.print(f"    {key}: {_escape_markup(detail)}")


def install_extension_from_url(
    manager,
    project_root: Path,
    url: str,
    speckit_version: str,
    *,
    priority: int = 10,
    force: bool = False,
):
    """Download an archive from *url* and install it, reusing the hardened path.

    Shares the same download hardening as ``extension add --from``:
    HTTPS enforcement, the catalog's authenticated + redirect-guarded
    ``_open_url`` fetch, a bounded (50 MiB) response read, archive-format
    detection (ZIP or tar.gz/tgz), and a TOCTOU-safe transient download file
    consumed directly by ``install_from_zip``.

    Returns the installed manifest. Raises ``ExtensionError`` on any failure so
    callers can present a uniform message without a second downloader.
    """
    import urllib.error

    from . import ExtensionCatalog, ExtensionError

    if not is_https_or_localhost_http(url):
        raise ExtensionError(
            "URL must use HTTPS (HTTP is only allowed for localhost)"
        )

    download_dir = _validate_safe_cache_dir(project_root)
    archive_filename = f"extension-url-download-{uuid4().hex}.archive"
    # Only used for diagnostic messages: the real archive is a transient inode
    # (unlinked on POSIX, O_TEMPORARY on Windows) consumed via ``archive_file``
    # below, so this path is never opened again.
    archive_path = download_dir / archive_filename

    try:
        dl_catalog = ExtensionCatalog(project_root)
        download_url = url
        extra_headers = None
        resolved_url = dl_catalog._resolve_github_release_asset_api_url(download_url)
        if resolved_url:
            download_url = resolved_url
            extra_headers = {"Accept": "application/octet-stream"}

        with dl_catalog._open_url(
            download_url, timeout=60, extra_headers=extra_headers
        ) as response:
            archive_data = read_response_limited(
                response,
                error_type=ExtensionError,
                label=f"extension {url}",
            )
            final_url = (
                response.geturl() if hasattr(response, "geturl") else download_url
            )
            content_type = (
                response.getheader("Content-Type")
                if hasattr(response, "getheader")
                else None
            )
    except urllib.error.URLError as exc:
        raise ExtensionError(f"Failed to download from {url}: {exc}") from exc

    download_fd = -1
    download_file = None
    try:
        try:
            download_fd = _safe_open_download_zip(
                project_root, download_dir, archive_filename
            )
        except OSError as exc:
            raise ExtensionError(
                f"Could not safely create download file: {exc}"
            ) from exc

        try:
            download_file = os.fdopen(download_fd, "w+b")
            download_fd = -1
            download_file.write(archive_data)
            download_file.flush()
            download_file.seek(0)
        except OSError as exc:
            raise ExtensionError(
                f"Could not safely write download file: {exc}"
            ) from exc

        format_source = (
            final_url
            if archive_format_from_name(final_url) is not None
            else url
        )
        try:
            detect_archive_format(
                archive_path,
                archive_file=download_file,
                source_name=format_source,
                content_type=content_type,
                error_type=ExtensionError,
            )
        except ExtensionError as exc:
            raise ExtensionError(
                f"{url} did not return a ZIP archive or tar.gz/tgz archive "
                f"(got {len(archive_data)} bytes). This usually means the request "
                "was not authenticated and a login/HTML page was returned. "
                "Verify the URL and configured credentials."
            ) from exc

        # Consume the transient inode reserved above rather than reopening the
        # cache pathname during extraction.
        try:
            return manager.install_from_zip(
                archive_path,
                speckit_version,
                priority=priority,
                force=force,
                archive_file=download_file,
            )
        except OSError as exc:
            raise ExtensionError(
                f"Could not install extension from downloaded archive: {exc}"
            ) from exc
    finally:
        if download_file is not None:
            try:
                download_file.close()
            except OSError:
                pass
        elif download_fd >= 0:
            try:
                os.close(download_fd)
            except OSError:
                pass


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

        # Try by display name - search using argument as query, then filter for exact match.
        # Coerce name defensively: catalog JSON is user-editable, so a hand-authored
        # non-string/missing name must not crash the match (the ambiguous-match display
        # below already str()-coerces name for the same reason).
        search_results = catalog.search()
        argument_lower = argument.lower()
        name_matches = [
            ext
            for ext in search_results
            if str(ext.get("name", "")).lower() == argument_lower
        ]

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


# Relative path, below the project root, of the extension URL download cache.
_CACHE_REL_PARTS = (".specify", "extensions", ".cache", "downloads")


def _has_secure_dir_fd() -> bool:
    """Whether this platform supports the strongest (POSIX) hardening path.

    The descriptor-anchored walk needs ``O_NOFOLLOW`` plus ``dir_fd`` support
    for ``os.open``/``os.mkdir``/``os.unlink``. When any of those is missing
    (notably on Windows) the caller falls back to the portable path-wise walk,
    which reproduces the same guarantees using symlink/reparse-point rejection,
    resolve-under-root containment checks, and post-open inode-identity
    verification instead of file descriptors.
    """
    return bool(
        getattr(os, "O_NOFOLLOW", 0)
        and os.open in os.supports_dir_fd
        and os.mkdir in os.supports_dir_fd
        and os.unlink in os.supports_dir_fd
    )


def _is_symlink_refusal_errno(exc: OSError) -> bool:
    """Whether an ``os.open``/``os.mkdir`` error means a component is a symlink.

    Opening an ``O_NOFOLLOW`` path whose final component is a symlink raises
    ``ELOOP`` on Linux and ``EMLINK`` on some BSDs, while a symlinked component
    that no longer resolves to a directory surfaces as ``ENOTDIR``.
    """
    return exc.errno in (errno.ELOOP, errno.ENOTDIR, getattr(errno, "EMLINK", -1))


def _verify_leaf_identity(fd: int, path: Path) -> None:
    """Confirm ``fd`` still refers to the regular file at ``path``.

    Mirrors the workflow installer's staged-file check: comparing the open
    descriptor's ``fstat`` against a ``lstat`` of the pathname detects a leaf
    that was swapped for a symlink/reparse point between creation and use, so
    the portable (dir_fd-less) path is not vulnerable to an ancestor swap race.
    """
    path_stat = path.stat(follow_symlinks=False)
    open_stat = os.fstat(fd)
    if (
        not stat.S_ISREG(path_stat.st_mode)
        or path_stat.st_dev != open_stat.st_dev
        or path_stat.st_ino != open_stat.st_ino
    ):
        raise OSError(
            errno.ENOTDIR, "Download file changed between creation and open"
        )


def _validate_safe_cache_dir(project_root: Path) -> Path:
    """Create and validate the extension URL download cache one component at a
    time, refusing symlinked/junctioned components on every supported platform."""
    download_dir = project_root.joinpath(*_CACHE_REL_PARTS)
    try:
        if _has_secure_dir_fd():
            _validate_cache_dir_via_dir_fd(project_root, download_dir)
        else:
            _validate_cache_dir_via_paths(project_root, download_dir)
    except typer.Exit:
        raise
    except FileExistsError:
        console.print(
            "[red]Error:[/red] Refusing to use symlinked download cache directory"
        )
        raise typer.Exit(1)
    except OSError as exc:
        if _is_symlink_refusal_errno(exc):
            console.print(
                "[red]Error:[/red] Refusing to use symlinked download cache directory"
            )
            raise typer.Exit(1)
        console.print(
            "[red]Error:[/red] Could not prepare download cache directory: "
            f"{_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)

    return download_dir


def _validate_cache_dir_via_dir_fd(project_root: Path, download_dir: Path) -> None:
    """POSIX cache-dir walk anchored on ``dir_fd`` + ``O_NOFOLLOW`` descriptors."""
    o_nofollow = getattr(os, "O_NOFOLLOW", 0)
    o_directory = getattr(os, "O_DIRECTORY", 0)
    o_cloexec = getattr(os, "O_CLOEXEC", 0)
    walk_flags = os.O_RDONLY | o_directory | o_nofollow | o_cloexec

    project_root_resolved = project_root.resolve()
    parent_fd = os.open(project_root, walk_flags)
    current_path = project_root
    try:
        for part in _CACHE_REL_PARTS:
            current_path = current_path / part

            try:
                child_fd = os.open(part, walk_flags, dir_fd=parent_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, dir_fd=parent_fd)
                except FileExistsError:
                    pass
                child_fd = os.open(part, walk_flags, dir_fd=parent_fd)

            try:
                current_path.resolve().relative_to(project_root_resolved)
            except (OSError, ValueError):
                try:
                    os.close(child_fd)
                except OSError:
                    pass
                console.print(
                    "[red]Error:[/red] Download cache directory escapes project root"
                )
                raise typer.Exit(1)

            os.close(parent_fd)
            parent_fd = child_fd
    finally:
        if parent_fd >= 0:
            try:
                os.close(parent_fd)
            except OSError:
                pass


def _validate_cache_dir_via_paths(project_root: Path, download_dir: Path) -> None:
    """Portable cache-dir walk for platforms without ``dir_fd`` (e.g. Windows).

    Each component is created individually while a symlink/junction is rejected
    both before and after creation, and every component is required to resolve
    back under the project root so a mount-point alias or reparse point cannot
    redirect the cache outside the project.
    """
    project_root_resolved = project_root.resolve()
    current_path = project_root
    for part in _CACHE_REL_PARTS:
        current_path = current_path / part

        if current_path.is_symlink():
            console.print(
                "[red]Error:[/red] Refusing to use symlinked download cache directory"
            )
            raise typer.Exit(1)

        try:
            current_path.mkdir()
        except FileExistsError:
            pass

        # Re-check after creation: a component swapped for a symlink/junction
        # (or an existing non-directory) between the check and mkdir is caught
        # here before the walk descends into it.
        if current_path.is_symlink() or not current_path.is_dir():
            console.print(
                "[red]Error:[/red] Refusing to use symlinked download cache directory"
            )
            raise typer.Exit(1)

        try:
            current_path.resolve().relative_to(project_root_resolved)
        except (OSError, ValueError):
            console.print(
                "[red]Error:[/red] Download cache directory escapes project root"
            )
            raise typer.Exit(1)


def _safe_open_download_zip(
    project_root: Path, download_dir: Path, zip_filename: str
) -> int:
    """Exclusively create a download ZIP and return an owned descriptor.

    The archive never persists as a nameable on-disk file: the POSIX path
    unlinks the leaf immediately after exclusive creation (anonymous inode),
    while the portable path opens it with ``O_TEMPORARY`` so the OS deletes it
    when the last handle closes. Installation proceeds entirely through the
    returned descriptor, removing the pathname-reopen and cleanup-walk TOCTOU
    classes on every supported platform.
    """
    if _has_secure_dir_fd():
        return _open_download_zip_via_dir_fd(
            project_root, download_dir, zip_filename
        )
    return _open_download_zip_via_paths(project_root, download_dir, zip_filename)


def _open_download_zip_via_dir_fd(
    project_root: Path, download_dir: Path, zip_filename: str
) -> int:
    """POSIX leaf create: descriptor walk, ``O_EXCL`` create, immediate unlink."""
    o_nofollow = getattr(os, "O_NOFOLLOW", 0)
    o_directory = getattr(os, "O_DIRECTORY", 0)
    o_cloexec = getattr(os, "O_CLOEXEC", 0)
    walk_flags = os.O_RDONLY | o_directory | o_nofollow | o_cloexec

    rel_parts = download_dir.relative_to(project_root).parts
    parent_fd = os.open(project_root, walk_flags)
    try:
        for part in rel_parts:
            new_fd = os.open(part, walk_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = new_fd

        download_fd = os.open(
            zip_filename,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | o_nofollow | o_cloexec,
            0o600,
            dir_fd=parent_fd,
        )
        try:
            os.unlink(zip_filename, dir_fd=parent_fd)
        except OSError:
            os.close(download_fd)
            raise
        return download_fd
    finally:
        os.close(parent_fd)


def _open_download_zip_via_paths(
    project_root: Path, download_dir: Path, zip_filename: str
) -> int:
    """Portable leaf create for platforms without ``dir_fd`` (e.g. Windows).

    The cache directory is re-validated (real directory, under the project
    root) immediately before an exclusive create. ``O_EXCL`` guarantees an
    attacker cannot pre-stage the leaf as a symlink/junction, ``O_TEMPORARY``
    makes the OS delete it on close, and a post-open inode-identity check
    detects a leaf swapped underneath us. The returned descriptor is the only
    handle installation ever uses, so the cache pathname is never reopened.
    """
    zip_path = download_dir / zip_filename
    project_root_resolved = project_root.resolve()

    if download_dir.is_symlink() or not download_dir.is_dir():
        raise OSError(
            errno.ENOTDIR, "Download cache directory is not a real directory"
        )
    try:
        download_dir.resolve().relative_to(project_root_resolved)
    except (OSError, ValueError):
        raise OSError(errno.ENOTDIR, "Download cache directory escapes project root")
    if zip_path.is_symlink():
        raise OSError(errno.ELOOP, "Refusing to write through a symlinked download file")

    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_BINARY", 0)
    o_temporary = getattr(os, "O_TEMPORARY", 0)
    flags |= o_temporary

    download_fd = os.open(zip_path, flags, 0o600)
    try:
        _verify_leaf_identity(download_fd, zip_path)
    except OSError:
        os.close(download_fd)
        # Without O_TEMPORARY the leaf is not auto-deleted, so remove the file
        # we just exclusively created (best effort, never through a symlink).
        if not o_temporary:
            try:
                if not zip_path.is_symlink():
                    zip_path.unlink()
            except OSError:
                pass
        raise
    return download_fd


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

        if not is_https_or_localhost_http(from_url):
            console.print("[red]Error:[/red] URL must use HTTPS for security.")
            console.print("HTTP is only allowed for loopback URLs.")
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
                # Install from URL archive via the shared hardened downloader
                # (HTTPS enforcement, authenticated redirect-guarded fetch,
                # bounded read, archive-format detection, TOCTOU-safe transient
                # archive). Same path used by ``specify init --extension <url>``.
                console.print(f"Downloading from {safe_url}...")
                manifest = install_extension_from_url(
                    manager,
                    project_root,
                    from_url,
                    speckit_version,
                    priority=priority,
                    force=force,
                )

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

                        # Download extension archive (use the resolved catalog ID).
                        extension_id = ext_info['id']
                        console.print(f"Downloading {_escape_markup(str(ext_info['name']))} v{_escape_markup(str(ext_info.get('version', 'unknown')))}...")
                        archive_path = catalog.download_extension(extension_id)

                        try:
                            manifest = manager.install_from_zip(
                                archive_path,
                                speckit_version,
                                priority=priority,
                                force=force,
                            )
                        finally:
                            if archive_path.exists():
                                archive_path.unlink()

        console.print("\n[green]✓[/green] Extension installed successfully!")
        console.print(f"\n[bold]{_escape_markup(str(manifest.name))}[/bold] (v{_escape_markup(str(manifest.version))})")
        console.print(f"  {_escape_markup(str(manifest.description))}")

        # #1: regenerate native event config for installed event-capable
        # integrations so the new extension's events take effect immediately.
        _refresh_events_and_warn(project_root)

        for warning in manifest.warnings:
            console.print(f"\n[yellow]⚠  Compatibility warning:[/yellow] {_escape_markup(str(warning))}")

        selected_ai = load_init_options(project_root).get("ai")
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

        # #1: regenerate native event config so the removed extension's events
        # are stripped from installed integrations.
        _refresh_events_and_warn(project_root)
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
            ext_tags = ext.get('tags', [])
            if isinstance(ext_tags, list) and ext_tags:
                tags_str = ", ".join(str(t) for t in ext_tags)
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
            downloads = ext.get('downloads')
            if downloads is not None:
                # Catalog fields are untrusted; a non-numeric ``downloads``
                # (e.g. the JSON string "1500") would crash the ``:,`` format
                # with "Cannot specify ',' with 's'". Only group-format numbers,
                # and escape the fallback: the joined stats are rendered as Rich
                # markup, so a value like "[/red]foo" would raise MarkupError
                # (matching how every other catalog field here is escaped).
                stats.append(
                    f"Downloads: {downloads:,}"
                    if isinstance(downloads, (int, float))
                    else f"Downloads: {_escape_markup(str(downloads))}"
                )
            stars = ext.get('stars')
            if stars is not None:
                # Same untrusted-value/Rich-markup hazard as `downloads` above,
                # in the same joined string.
                stats.append(f"Stars: {_escape_markup(str(stars))}")
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
                    f"or install from an archive URL: specify extension add {safe_id} --from <archive-url>"
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
                # Print each command the way the active agent registers it.
                # Cline and Forge hyphenate command names (e.g. Forge invokes
                # `/speckit-jira-sync`, not the manifest's dotted
                # `speckit.jira.sync`), so mirror the same formatting used by
                # `extension add`'s "Provided commands" listing — otherwise the
                # names shown here don't match what the user actually types.
                selected_ai = load_init_options(project_root).get("ai")
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

                console.print("[bold]Commands:[/bold]")
                for cmd in ext_manifest.commands:
                    cmd_name = cmd['name']
                    if _format_command_name is not None:
                        cmd_name = _format_command_name(cmd_name)
                    console.print(f"  • {_escape_markup(str(cmd_name))}: {_escape_markup(str(cmd.get('description', '')))}")
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
    info_tags = ext_info.get('tags', [])
    if isinstance(info_tags, list) and info_tags:
        tags_str = ", ".join(str(t) for t in info_tags)
        console.print(f"[bold]Tags:[/bold] {_escape_markup(tags_str)}")
        console.print()

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
        ExtensionManifest,
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
            backup_root = manager.extensions_dir / ".backup"
            backup_key = hashlib.sha256(
                extension_id.encode("utf-8")
            ).hexdigest()[:16]
            backup_base = (
                backup_root
                / f"update-{backup_key}-{uuid4().hex}"
            )
            backup_ext_dir = backup_base / "extension"
            backup_commands_dir = backup_base / "commands"
            backup_skills_dir = backup_base / "skills"
            backup_config_dir = backup_base / "config"

            # Store backup state
            backup_registry_entry = None  # None means registry entry not yet captured
            backup_installed = UNSET  # Original installed list from extensions.yml
            backup_hooks = None  # None means backup step 4 not yet reached; {} or {...} means backup was captured
            backed_up_command_files = {}
            backed_up_command_symlinks = {}
            backed_up_skill_dirs = {}
            new_command_dirs_absent_before_update = []
            new_command_paths_absent_before_update = []
            new_skill_names = []
            new_skill_paths_absent_before_update = []
            # Validation failures must not rewrite an untouched installation.
            installation_modified = False
            zip_cleanup_error = None
            backup_created_by_attempt = False

            def backup_command_artifact(original_file, backup_file):
                """Back up one command artifact once, preserving its full path."""
                nonlocal backup_created_by_attempt
                original_key = str(original_file)
                if original_key in backed_up_command_files:
                    return
                if original_file.is_symlink():
                    backed_up_command_symlinks[original_key] = os.readlink(
                        original_file
                    )
                else:
                    if original_file.stat().st_nlink > 1:
                        raise RuntimeError(
                            "Cannot safely update hard-linked generated "
                            f"artifact '{original_file}'"
                        )
                    backup_created_by_attempt = True
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original_file, backup_file)
                backed_up_command_files[original_key] = str(backup_file)

            def restore_command_artifact(original_path, backup_path):
                """Restore one regular file or symlink without following it."""
                original_key = str(original_path)
                original_file = Path(original_path)
                backup_file = Path(backup_path)
                symlink_state = backed_up_command_symlinks.get(
                    original_key
                )

                if symlink_state is not None:
                    if original_file.is_symlink() or original_file.is_file():
                        original_file.unlink()
                    elif original_file.exists():
                        raise RuntimeError(
                            "Command rollback found an unexpected directory "
                            f"at '{original_file}'"
                        )
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(symlink_state, original_file)
                    return

                if not backup_file.is_file() or backup_file.is_symlink():
                    raise RuntimeError(
                        "Command rollback backup is missing for "
                        f"'{original_file}'"
                    )
                if original_file.is_symlink() or original_file.is_file():
                    original_file.unlink()
                elif original_file.exists():
                    raise RuntimeError(
                        "Command rollback found an unexpected directory "
                        f"at '{original_file}'"
                    )
                original_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, original_file)

            def remember_absent_parent_dirs(artifact_path, root_dir):
                """Remember absent parents a failed renderer may create."""
                boundary = root_dir.parent
                if root_dir.is_relative_to(project_root):
                    boundary = project_root
                parent = artifact_path.parent
                while parent != boundary:
                    if parent.exists() or parent.is_symlink():
                        break
                    new_command_dirs_absent_before_update.append(parent)
                    parent = parent.parent

            def backup_extension_skills(skill_names, *, skills_dir=None):
                """Back up every owned skill directory that remove() may delete."""
                nonlocal backup_created_by_attempt
                for skill_dir in manager._find_extension_skill_dirs(
                    skill_names,
                    extension_id,
                    skills_dir=skills_dir,
                    create_skills_dir=False,
                ):
                    original_key = str(skill_dir)
                    if original_key in backed_up_skill_dirs:
                        continue
                    backup_created_by_attempt = True
                    backup_skills_dir.mkdir(parents=True, exist_ok=True)
                    backup_skill_dir = backup_skills_dir / str(
                        len(backed_up_skill_dirs)
                    )
                    shutil.copytree(skill_dir, backup_skill_dir, symlinks=True)
                    backed_up_skill_dirs[original_key] = str(backup_skill_dir)

            try:
                if backup_root.is_symlink():
                    raise RuntimeError(
                        "Cannot safely create update backup under symlinked "
                        f"directory '{backup_root}'"
                    )
                if backup_base.exists() or backup_base.is_symlink():
                    raise RuntimeError(
                        "Cannot safely reuse an existing update backup "
                        f"directory '{backup_base}'"
                    )

                # 1. Backup registry entry (always, even if extension dir doesn't exist)
                backup_registry_entry = manager.registry.get(extension_id)

                # 2. Backup extension directory
                extension_dir = manager.extensions_dir / extension_id
                if extension_dir.exists():
                    backup_created_by_attempt = True
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
                    dirs_to_backup = [commands_dir]
                    legacy = agent_config.get("legacy_dir")
                    if legacy:
                        legacy_dir = project_root / legacy
                        if (
                            legacy_dir.exists()
                            and legacy_dir != commands_dir
                        ):
                            dirs_to_backup.append(legacy_dir)

                    for cmd_name in cmd_names:
                        output_name = _AgentReg._compute_output_name(
                            agent_name, cmd_name, agent_config
                        )
                        names_to_backup = [output_name]
                        if (
                            output_name != cmd_name
                            and _AgentReg._is_safe_command_name(cmd_name)
                        ):
                            names_to_backup.append(cmd_name)

                        for dir_index, target_dir in enumerate(
                            dirs_to_backup
                        ):
                            for name in names_to_backup:
                                cmd_file = (
                                    target_dir
                                    / f"{name}{agent_config['extension']}"
                                )
                                try:
                                    _AgentReg._ensure_inside(
                                        cmd_file, target_dir
                                    )
                                except ValueError:
                                    continue
                                if (
                                    cmd_file.exists()
                                    or cmd_file.is_symlink()
                                ):
                                    # Keep both the directory location and
                                    # relative path unique. unregister_commands()
                                    # removes legacy and canonical copies, and
                                    # skills agents place every SKILL.md in its
                                    # own command subdirectory.
                                    backup_cmd_path = (
                                        backup_commands_dir
                                        / agent_name
                                        / f"location-{dir_index}"
                                        / cmd_file.relative_to(target_dir)
                                    )
                                    backup_command_artifact(
                                        cmd_file, backup_cmd_path
                                    )

                        # Also backup copilot prompt files
                        if agent_name == "copilot":
                            prompts_dir = (
                                project_root / ".github" / "prompts"
                            )
                            prompt_file = (
                                prompts_dir / f"{cmd_name}.prompt.md"
                            )
                            try:
                                _AgentReg._ensure_inside(
                                    prompt_file, prompts_dir
                                )
                            except ValueError:
                                continue
                            if prompt_file.exists() or prompt_file.is_symlink():
                                backup_prompt_path = (
                                    backup_commands_dir
                                    / "copilot-prompts"
                                    / prompt_file.relative_to(prompts_dir)
                                )
                                backup_command_artifact(
                                    prompt_file, backup_prompt_path
                                )

                raw_registered_skills = (
                    backup_registry_entry.get("registered_skills", [])
                    if isinstance(backup_registry_entry, dict)
                    else []
                )
                registered_skills = manager._valid_name_list(raw_registered_skills)
                backup_extension_skills(registered_skills)

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
                archive_path = catalog.download_extension(extension_id)
                try:
                    # 6. Validate the archive and extension ID before modifying
                    # the existing installation. The shared extractor applies
                    # the same bounded security checks to ZIP and tar archives.
                    with tempfile.TemporaryDirectory(
                        prefix="speckit-update-archive-"
                    ) as archive_tmpdir:
                        extracted_root = Path(archive_tmpdir)
                        try:
                            safe_extract_archive(archive_path, extracted_root)
                        except ValueError as exc:
                            if (
                                "Conflicting path" in str(exc)
                                and "extension.yml" in str(exc).casefold()
                            ):
                                raise ValueError(
                                    "Downloaded extension archive contains multiple "
                                    "extension.yml manifests"
                                ) from exc
                            raise
                        manifest_root = extracted_root
                        top_level = list(extracted_root.iterdir())
                        root_manifest_entries = [
                            entry
                            for entry in top_level
                            if entry.name.casefold() == "extension.yml"
                        ]
                        if any(
                            entry.name != "extension.yml"
                            for entry in root_manifest_entries
                        ):
                            raise ValueError(
                                "Archive must use canonical 'extension.yml' casing"
                            )
                        canonical_root_manifest = next(
                            (
                                entry
                                for entry in root_manifest_entries
                                if entry.name == "extension.yml"
                            ),
                            None,
                        )
                        if canonical_root_manifest is not None:
                            manifest_path = canonical_root_manifest
                        else:
                            top_level_dirs = [
                                entry for entry in top_level if entry.is_dir()
                            ]
                            if len(top_level_dirs) != 1:
                                raise ValueError(
                                    "Downloaded extension archive must contain exactly "
                                    "one top-level directory"
                                )
                            manifest_root = top_level_dirs[0]
                            nested_manifest_entries = [
                                entry
                                for entry in manifest_root.iterdir()
                                if entry.name.casefold() == "extension.yml"
                            ]
                            if any(
                                entry.name != "extension.yml"
                                for entry in nested_manifest_entries
                            ):
                                raise ValueError(
                                    "Archive must use canonical 'extension.yml' casing"
                                )
                            manifest_path = next(
                                (
                                    entry
                                    for entry in nested_manifest_entries
                                    if entry.name == "extension.yml"
                                ),
                                manifest_root / "extension.yml",
                            )
                        if not manifest_path.is_file():
                            raise ValueError(
                                "Downloaded extension archive is missing 'extension.yml'"
                            )
                        manifest_bytes = manifest_path.read_bytes()
                        parsed_manifest = yaml.safe_load(manifest_bytes)
                        manifest_data = (
                            parsed_manifest if parsed_manifest is not None else {}
                        )
                        if not isinstance(manifest_data, dict):
                            raise ValueError(
                                "Invalid extension manifest in downloaded archive: "
                                "expected YAML mapping"
                            )
                        extension_data = manifest_data.get("extension", {})
                        if not isinstance(extension_data, dict):
                            raise ValueError(
                                "Invalid extension manifest in downloaded archive: "
                                "expected 'extension' mapping"
                            )

                    # Run the same manifest and compatibility validation as a
                    # normal install while the existing extension is still
                    # untouched. Reuse the exact bounded bytes selected above.
                    with tempfile.TemporaryDirectory(
                        prefix="speckit-update-manifest-"
                    ) as manifest_tmpdir:
                        manifest_file = Path(manifest_tmpdir) / "extension.yml"
                        manifest_file.write_bytes(manifest_bytes)
                        preflight_manifest = ExtensionManifest(manifest_file)
                        manager.check_compatibility(
                            preflight_manifest, speckit_version
                        )

                    zip_extension_id = preflight_manifest.id
                    if zip_extension_id != extension_id:
                        raise ValueError(
                            f"Extension ID mismatch: expected '{extension_id}', got '{zip_extension_id}'"
                        )

                    expected_version = pkg_version.Version(update["available"])
                    archive_version = pkg_version.Version(
                        preflight_manifest.version
                    )
                    if archive_version != expected_version:
                        raise ValueError(
                            "Extension version mismatch: "
                            f"expected '{update['available']}', "
                            f"got '{preflight_manifest.version}'"
                        )

                    # Match the remaining deterministic install validation
                    # before crossing the destructive boundary. The helper
                    # excludes this extension's current registry entry while
                    # still detecting namespace, core, duplicate, and
                    # cross-extension command conflicts.
                    manager._validate_install_conflicts(preflight_manifest)

                    new_command_names = list(
                        manager._collect_manifest_command_names(
                            preflight_manifest
                        )
                    )
                    new_skill_names = list(
                        dict.fromkeys(
                            manager._skill_name_for_command(command_name)
                            for command_name in new_command_names
                        )
                    )

                    # Command rendering happens before hook registration and
                    # registry.add(). Preserve every candidate output that
                    # already exists, and remember paths that are absent now so
                    # rollback can remove files created before registry state is
                    # available. Include aliases and Copilot companion prompts.
                    for (
                        agent_name,
                        commands_dir,
                    ) in manager._command_registration_targets().items():
                        agent_config = registrar.AGENT_CONFIGS[agent_name]
                        for command_name in new_command_names:
                            output_name = _AgentReg._compute_output_name(
                                agent_name, command_name, agent_config
                            )
                            command_file = (
                                commands_dir
                                / f"{output_name}{agent_config['extension']}"
                            )
                            _AgentReg._ensure_inside(command_file, commands_dir)
                            backup_command_path = (
                                backup_commands_dir
                                / agent_name
                                / command_file.relative_to(commands_dir)
                            )
                            if command_file.exists() or command_file.is_symlink():
                                backup_command_artifact(
                                    command_file, backup_command_path
                                )
                            else:
                                new_command_paths_absent_before_update.append(
                                    command_file
                                )
                                remember_absent_parent_dirs(
                                    command_file, commands_dir
                                )

                            if agent_name == "copilot":
                                prompts_dir = (
                                    project_root / ".github" / "prompts"
                                )
                                prompt_file = (
                                    prompts_dir / f"{command_name}.prompt.md"
                                )
                                _AgentReg._ensure_inside(
                                    prompt_file, prompts_dir
                                )
                                if prompt_file.is_symlink():
                                    raise RuntimeError(
                                        "Cannot safely update symlinked Copilot "
                                        f"prompt artifact '{prompt_file}'"
                                    )
                                backup_prompt_path = (
                                    backup_commands_dir
                                    / "copilot-prompts"
                                    / prompt_file.relative_to(prompts_dir)
                                )
                                if (
                                    prompt_file.exists()
                                    or prompt_file.is_symlink()
                                ):
                                    backup_command_artifact(
                                        prompt_file, backup_prompt_path
                                    )
                                else:
                                    new_command_paths_absent_before_update.append(
                                        prompt_file
                                    )
                                    remember_absent_parent_dirs(
                                        prompt_file, prompts_dir
                                    )

                    new_command_paths_absent_before_update = list(
                        dict.fromkeys(
                            new_command_paths_absent_before_update
                        )
                    )
                    new_command_dirs_absent_before_update = list(
                        dict.fromkeys(
                            new_command_dirs_absent_before_update
                        )
                    )

                    # A newly introduced command may reuse an existing
                    # extension-owned skill directory that was not present in
                    # the old registry. Back it up before cleanup can touch it.
                    backup_extension_skills(new_skill_names)
                    new_skills_dir = manager._get_skills_dir(create=False)
                    if new_skills_dir is not None:
                        # Unscoped removal deliberately ignores home-scoped
                        # outputs because the flat registry cannot establish
                        # project ownership. The active install can still
                        # replace a marker-owned skill in its explicit root,
                        # so back up that exact project/home target separately.
                        backup_extension_skills(
                            list(
                                dict.fromkeys(
                                    registered_skills + new_skill_names
                                )
                            ),
                            skills_dir=new_skills_dir,
                        )
                        init_options = load_init_options(project_root)
                        if (
                            isinstance(init_options, dict)
                            and is_ai_skills_enabled(init_options)
                            and isinstance(init_options.get("ai"), str)
                            and init_options["ai"]
                        ):
                            # resolve_active_skills_dir() first creates the
                            # configured project-local skills marker. Some
                            # agents (notably Hermes) then redirect rendered
                            # skills to a different global root, so snapshot
                            # both locations for exact rollback.
                            from .. import _get_skills_dir

                            configured_skills_dir = _get_skills_dir(
                                project_root, init_options["ai"]
                            )
                            remember_absent_parent_dirs(
                                configured_skills_dir / ".update-marker",
                                configured_skills_dir,
                            )
                        new_skills_root = new_skills_dir.resolve()
                        for skill_name in new_skill_names:
                            skill_path = new_skills_dir / skill_name
                            resolved_skill_path = skill_path.resolve(strict=False)
                            resolved_skill_path.relative_to(new_skills_root)
                            if not (
                                skill_path.exists() or skill_path.is_symlink()
                            ):
                                new_skill_paths_absent_before_update.append(
                                    skill_path
                                )
                                remember_absent_parent_dirs(
                                    skill_path / "SKILL.md",
                                    new_skills_dir,
                                )

                    new_command_dirs_absent_before_update = list(
                        dict.fromkeys(
                            new_command_dirs_absent_before_update
                        )
                    )

                    # 7. Remove old extension (handles command file cleanup and registry removal)
                    installation_modified = True
                    manager.remove(extension_id, keep_config=True)

                    # 8. Install new version
                    _ = manager.install_from_zip(archive_path, speckit_version)

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
                    # Archive cleanup is housekeeping: never replace an install
                    # error or roll back an already committed update because a
                    # scanner temporarily locks the download on Windows.
                    if archive_path.exists():
                        try:
                            archive_path.unlink()
                        except OSError as error:
                            zip_cleanup_error = error

                # 10. Clean up backup on success. The update has committed at
                # this point, so a locked backup file must not trigger rollback
                # of an otherwise successful installation.
                cleanup_error = None
                if backup_created_by_attempt and backup_base.exists():
                    try:
                        shutil.rmtree(backup_base)
                    except OSError as error:
                        cleanup_error = error

                console.print(f"   [green]✓[/green] Updated to v{update['available']}")
                if cleanup_error is not None:
                    console.print(
                        "   [yellow]Warning:[/yellow] Could not fully remove "
                        "update backup: "
                        f"{_escape_markup(str(cleanup_error))}"
                    )
                    console.print(
                        "   [dim]Backup may remain at: "
                        f"{_escape_markup(str(backup_base))}[/dim]"
                    )
                if zip_cleanup_error is not None:
                    console.print(
                        "   [yellow]Warning:[/yellow] Could not remove "
                        "downloaded update archive: "
                        f"{_escape_markup(str(zip_cleanup_error))}"
                    )
                updated_extensions.append(ext_name)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"   [red]✗[/red] Failed: {_escape_markup(str(e))}")
                failed_updates.append((ext_name, str(e)))
                if zip_cleanup_error is not None:
                    console.print(
                        "   [yellow]Warning:[/yellow] Could not remove "
                        "downloaded update archive: "
                        f"{_escape_markup(str(zip_cleanup_error))}"
                    )

                if not installation_modified:
                    if backup_created_by_attempt and backup_base.exists():
                        try:
                            shutil.rmtree(backup_base)
                        except OSError as cleanup_error:
                            console.print(
                                "   [yellow]Warning:[/yellow] Could not remove "
                                "untouched-update backup: "
                                f"{_escape_markup(str(cleanup_error))}"
                            )
                    continue

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
                    # (files that weren't in the original backup). Registration
                    # writes before registry.add(), so start with the paths that
                    # were absent at the destructive boundary instead of relying
                    # only on a possibly missing new registry entry.
                    for command_path in new_command_paths_absent_before_update:
                        if command_path.is_symlink() or command_path.is_file():
                            command_path.unlink()
                        elif command_path.exists():
                            raise RuntimeError(
                                "Command rollback found an unexpected directory "
                                f"at '{command_path}'"
                            )
                    new_registered_skills = []
                    try:
                        new_registry_entry = manager.registry.get(extension_id)
                        if new_registry_entry is None or not isinstance(new_registry_entry, dict):
                            new_registered_commands = {}
                        else:
                            new_registered_commands = new_registry_entry.get("registered_commands", {})
                            new_registered_skills = manager._valid_name_list(
                                new_registry_entry.get("registered_skills", [])
                            )
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

                    # Restore command artifacts that existed before the update
                    # before extension-skill cleanup inspects ownership. A
                    # failed skills registrar may have overwritten a user's
                    # pre-existing SKILL.md with extension metadata; restoring
                    # it first prevents the conservative skill unregistrar from
                    # misclassifying and deleting the user's whole directory.
                    for original_path, backup_path in backed_up_command_files.items():
                        restore_command_artifact(
                            original_path, backup_path
                        )

                    # Skill generation happens before hooks and registry.add(),
                    # so a failed install may have created skills that are not
                    # recorded in any registry entry yet. Derive names from the
                    # preflighted manifest as well as any partial new entry.
                    skills_to_remove = list(
                        dict.fromkeys(new_skill_names + new_registered_skills)
                    )
                    # A write failure can leave a partial skill without valid
                    # ownership metadata, which the normal conservative
                    # unregistrar intentionally refuses to delete. Paths that
                    # were absent at the destructive boundary are safe to
                    # remove directly during rollback.
                    for skill_path in new_skill_paths_absent_before_update:
                        if skill_path.is_symlink() or skill_path.is_file():
                            skill_path.unlink()
                        elif skill_path.exists():
                            shutil.rmtree(skill_path)
                    manager._unregister_extension_skills(
                        skills_to_remove, extension_id
                    )

                    # Restore all original registered skill artifacts after
                    # removing skills created by the failed installation.
                    for original_path, backup_path in backed_up_skill_dirs.items():
                        backup_skill_dir = Path(backup_path)
                        if not backup_skill_dir.is_dir():
                            raise RuntimeError(
                                "Skill rollback backup is missing for "
                                f"'{original_path}'"
                            )
                        original_skill_dir = Path(original_path)
                        if (
                            original_skill_dir.is_symlink()
                            or original_skill_dir.is_file()
                        ):
                            original_skill_dir.unlink()
                        elif original_skill_dir.exists():
                            shutil.rmtree(original_skill_dir)
                        original_skill_dir.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(
                            backup_skill_dir,
                            original_skill_dir,
                            symlinks=True,
                        )

                    # Remove empty artifact directories that did not exist at
                    # the destructive boundary. Do this after skill cleanup and
                    # restoration so newly created skills roots and their
                    # project-local parents can also be removed exactly.
                    for command_dir in sorted(
                        new_command_dirs_absent_before_update,
                        key=lambda path: len(path.parts),
                        reverse=True,
                    ):
                        if command_dir.is_dir() and not command_dir.is_symlink():
                            try:
                                command_dir.rmdir()
                            except OSError:
                                # Preserve any non-empty directory: other
                                # content may belong to the user.
                                pass

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

                    # Backup cleanup is post-rollback housekeeping. A locked
                    # file (notably on Windows) must not turn successfully
                    # restored state into a contradictory "Rollback failed".
                    cleanup_error = None
                    if backup_created_by_attempt and backup_base.exists():
                        try:
                            shutil.rmtree(backup_base)
                        except OSError as error:
                            cleanup_error = error
                    console.print("   [green]✓[/green] Rollback successful")
                    if cleanup_error is not None:
                        console.print(
                            "   [yellow]Warning:[/yellow] Could not fully "
                            "remove rollback backup: "
                            f"{_escape_markup(str(cleanup_error))}"
                        )
                        console.print(
                            "   [dim]Backup may remain at: "
                            f"{_escape_markup(str(backup_base))}[/dim]"
                        )
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

        # S4: regenerate native event config after a successful update. An
        # update replaces the installed extension.yml, so any added/removed/
        # changed event declarations would otherwise leave native configs
        # stale until a manual integration upgrade.
        if updated_extensions:
            _refresh_events_and_warn(project_root)

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

    # #1: regenerate native event config so the enabled extension's events
    # are re-emitted in installed integrations.
    _refresh_events_and_warn(project_root)

    # Scaffold config templates on enable
    try:
        deployed, skipped, failed = manager.scaffold_config(extension_id)
    except Exception as exc:
        console.print(
            f"\n[yellow]Warning:[/yellow] Failed to scaffold config for extension "
            f"'{_escape_markup(str(display_name))}'."
        )
        console.print(f"[dim]Details: {_escape_markup(str(exc))}[/dim]")
        deployed, skipped, failed = [], [], []
    config_home = f".specify/extensions/{_escape_markup(str(extension_id))}"
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

    # #1: regenerate native event config so the disabled extension's events
    # are stripped from installed integrations.
    _refresh_events_and_warn(project_root)


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
