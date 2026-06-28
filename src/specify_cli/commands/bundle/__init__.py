"""``specify bundle`` command group — discover, install, author Spec Kit bundles.

This module is the CLI/UX layer only (Principle I: thin commands over services).
Each command resolves a project, builds a catalog stack, delegates to a bundler
service, and renders Rich output. ``--json`` emits machine-readable data on
stdout; human logs go to stderr/console.
"""
from __future__ import annotations

import json as _json
import re
from pathlib import Path

import typer

from ..._console import console
from ...bundler import BundlerError
from ...bundler.lib.project import (
    active_integration,
    find_project_root,
    require_project_root,
)
from ...bundler.models.records import load_records

bundle_app = typer.Typer(
    name="bundle",
    help="Discover, install, and author Spec Kit bundles",
    add_completion=False,
)

bundle_catalog_app = typer.Typer(
    name="catalog",
    help="Manage bundle catalog sources",
    add_completion=False,
)
bundle_app.add_typer(bundle_catalog_app, name="catalog")


# ===== helpers =====


def _fail(message: str) -> None:
    """Print an actionable error to stderr and exit non-zero."""
    console.print(f"[red]Error:[/red] {message}", style=None)
    raise typer.Exit(code=1)


def _user_config_dir() -> Path:
    # User-scope Spec Kit config lives under ~/.specify (same convention as
    # auth.json, extension/preset catalogs). Passing this through to the source
    # stack is what makes the documented project > user > built-in precedence
    # reachable from the CLI.
    return Path.home() / ".specify"


def _build_stack(project_root: Path, *, offline: bool):
    from ...bundler.services.adapters import make_catalog_fetcher
    from ...bundler.services.catalog_stack import CatalogStack

    fetcher = make_catalog_fetcher(allow_network=not offline)
    return CatalogStack.load(project_root, fetcher, user_config_dir=_user_config_dir())


def _speckit_version() -> str:
    from ..._assets import get_speckit_version

    return get_speckit_version()


def _trust_level(verified: bool) -> str:
    """Trust framing for a catalog entry (FR-010): org-curated vs community."""
    return "verified" if verified else "community"


def _trust_badge(verified: bool) -> str:
    return (
        "[green]✔ verified[/green]"
        if verified
        else "[yellow]community[/yellow]"
    )


def _default_script_type() -> str:
    """OS-appropriate default script flavor (FR-013)."""
    import os

    return "ps" if os.name == "nt" else "sh"


def _run_init(integration: str, *, script_type: str, offline: bool = False) -> None:
    """Idempotently scaffold a Spec Kit project here via the existing ``init`` machinery.

    Reuses the real ``specify init`` command callback in-process (Principle I)
    with ``--here --force`` so it is non-interactive and merges into the current
    directory.
    """
    from ... import app

    init_cb = next(
        c.callback
        for c in app.registered_commands
        if c.callback and c.callback.__name__ == "init"
    )
    try:
        init_cb(
            project_name=None,
            script_type=script_type,
            ignore_agent_tools=True,
            here=True,
            force=True,
            skip_tls=False,
            debug=False,
            github_token=None,
            offline=offline,
            preset=None,
            integration=integration,
            integration_options=None,
            plugin=False,
            plugin_out=None,
            yes=False,
        )
    except typer.Exit as exc:
        if exc.exit_code:
            raise BundlerError(
                f"Failed to initialize a Spec Kit project (integration '{integration}')."
            ) from exc


def _resolve_init_integration(override: str | None, manifest) -> str:
    """Precedence (FR-013): explicit override → bundle-declared → default."""
    from ..._agent_config import DEFAULT_INIT_INTEGRATION

    if override:
        return override
    if manifest is not None and manifest.integration is not None:
        return manifest.integration.id
    return DEFAULT_INIT_INTEGRATION


# ===== Consume =====


@bundle_app.command("search")
def bundle_search(
    query: str = typer.Argument("", help="Optional text query"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
) -> None:
    """List matching bundles across the active catalog stack."""
    try:
        project_root = find_project_root() or Path.cwd()
        stack = _build_stack(project_root, offline=offline)
        results = stack.search(query)
    except BundlerError as exc:
        _fail(str(exc))
        return

    if as_json:
        payload = [
            {
                "id": r.entry.id,
                "name": r.entry.name,
                "role": r.entry.role,
                "version": r.entry.version,
                "description": r.entry.description,
                "source": r.source.id,
                "install_policy": r.source.install_policy.value,
                "verified": r.entry.verified,
                "trust": _trust_level(r.entry.verified),
            }
            for r in results
        ]
        print(_json.dumps(payload, indent=2))
        return

    if not results:
        console.print("[yellow]No matching bundles found.[/yellow]")
        return

    console.print("\n[bold cyan]Bundles:[/bold cyan]\n")
    for r in results:
        policy = (
            "[dim](discovery-only)[/dim]"
            if not r.source.install_allowed
            else ""
        )
        console.print(
            f"  [bold]{r.entry.id}[/bold] v{r.entry.version} — {r.entry.name} "
            f"[dim]({r.entry.role})[/dim] {_trust_badge(r.entry.verified)} {policy}"
        )
        console.print(f"    {r.entry.description}")
        console.print(f"    [dim]source: {r.source.id}[/dim]")


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
            "integration": (manifest.integration.id if manifest and manifest.integration else None),
            "components": components,
            "overlaps": overlaps,
        }
        print(_json.dumps(payload, indent=2))
        return

    console.print(f"\n[bold cyan]{entry.id}[/bold cyan] v{entry.version} — {entry.name}")
    console.print(f"  Role: {entry.role}")
    console.print(f"  {entry.description}")
    console.print(f"  Author: {entry.author}   License: {entry.license}")
    console.print(f"  Source: {resolved.source.id} ({resolved.source.install_policy.value})")
    console.print(f"  Trust: {_trust_badge(entry.verified)}")
    if entry.requires_speckit_version:
        console.print(f"  Requires Spec Kit: {entry.requires_speckit_version}")
    if manifest and manifest.integration:
        console.print(f"  Integration: {manifest.integration.id}")

    if components:
        console.print("\n  [bold]Components[/bold] (added on install):")
        for kind in ("extensions", "presets", "steps", "workflows"):
            items = [c for c in components if c["kind"] == kind]
            if not items:
                continue
            console.print(f"    [bold]{kind}:[/bold]")
            for item in items:
                console.print(f"      - {_format_component(item)}")
    else:
        console.print("\n  [bold]Provides:[/bold]")
        for kind in ("extensions", "presets", "steps", "workflows"):
            count = entry.provides.get(kind, 0)
            if count:
                console.print(f"    {kind}: {count}")

    if overlaps:
        console.print("\n  [yellow]Overlaps with already-installed bundles:[/yellow]")
        for overlap in overlaps:
            console.print(f"    [yellow]-[/yellow] {overlap}")

    if not resolved.install_allowed:
        console.print(
            "\n  [yellow]This source is discovery-only; the bundle cannot be "
            "installed from here.[/yellow]"
        )


@bundle_app.command("list")
def bundle_list(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
) -> None:
    """List bundles currently installed in the project with versions."""
    try:
        project_root = require_project_root()
        records = load_records(project_root)
    except BundlerError as exc:
        _fail(str(exc))
        return

    if as_json:
        print(_json.dumps([r.to_dict() for r in records], indent=2))
        return

    if not records:
        console.print("[yellow]No bundles installed.[/yellow]")
        console.print("\nInstall one with: [cyan]specify bundle install <id>[/cyan]")
        return

    console.print("\n[bold cyan]Installed bundles:[/bold cyan]\n")
    for record in records:
        console.print(
            f"  [bold]{record.bundle_id}[/bold] v{record.version} "
            f"[dim]({len(record.contributed_components)} components, "
            f"installed {record.installed_at})[/dim]"
        )


@bundle_app.command("install")
def bundle_install(
    bundle_id: str = typer.Argument(
        ...,
        help="Bundle id (from the catalog stack) or a local path to a .zip "
        "artifact, bundle directory, or bundle.yml",
    ),
    integration: str = typer.Option(None, "--integration", help="Override integration"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
) -> None:
    """Install a bundle's full component set through each primitive's machinery.

    ``bundle_id`` may be a catalog bundle id, or a local path to a built
    artifact (``.zip``), a bundle directory, or a ``bundle.yml`` file. Local
    sources install directly without consulting the catalog stack.
    """
    try:
        from ...bundler.lib.project import find_project_root
        from ...bundler.services.adapters import DefaultPrimitiveInstaller
        from ...bundler.services.installer import install_bundle
        from ...bundler.services.resolver import resolve_install_plan

        project_root = find_project_root()

        local_manifest = _local_manifest_source(bundle_id)
        if local_manifest is not None:
            manifest = local_manifest
        else:
            stack = _build_stack(project_root or Path.cwd(), offline=offline)
            resolved = stack.resolve(bundle_id)

            if not resolved.install_allowed:
                raise BundlerError(
                    f"Bundle '{bundle_id}' resolves only from a discovery-only source "
                    f"('{resolved.source.id}'); it cannot be installed from there."
                )
            manifest = _download_manifest(resolved, offline=offline)

        if project_root is None:
            init_integration = _resolve_init_integration(integration, manifest)
            console.print(
                f"[cyan]No Spec Kit project here; initializing with integration "
                f"'{init_integration}'…[/cyan]"
            )
            _run_init(init_integration, script_type=_default_script_type(), offline=offline)
            project_root = require_project_root()

        for overlap in _bundle_overlaps(project_root, manifest, offline=offline):
            console.print(f"[yellow]![/yellow] {overlap}")

        # For an already-initialized project, the project's recorded active
        # integration is authoritative — an explicit --integration must not be
        # able to bypass the FR-019 integration-clash guard. The override only
        # selects the integration at init time (handled above) or confirms the
        # target when the active integration cannot be determined.
        detected = active_integration(project_root)
        plan = resolve_install_plan(
            manifest,
            speckit_version=_speckit_version(),
            active_integration=detected if detected is not None else integration,
            integration_explicit=bool(integration) and detected is None,
        )
        for warning in plan.warnings:
            console.print(f"[yellow]![/yellow] {warning}")

        result = install_bundle(
            project_root,
            plan,
            DefaultPrimitiveInstaller(allow_network=not offline),
            manifest=manifest,
        )
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Installed '{result.bundle_id}' "
        f"({len(result.installed)} added, {len(result.skipped)} already present)."
    )


@bundle_app.command("update")
def bundle_update(
    bundle_id: str = typer.Argument(None, help="Bundle id, or omit with --all"),
    all_bundles: bool = typer.Option(False, "--all", help="Update every installed bundle"),
    integration: str = typer.Option(None, "--integration", help="Override integration"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
) -> None:
    """Re-resolve and refresh a bundle's components via each primitive's update path."""
    try:
        project_root = require_project_root()
        records = load_records(project_root)
        if not all_bundles and not bundle_id:
            raise BundlerError("Specify a bundle id or use --all.")
        targets = (
            [r.bundle_id for r in records]
            if all_bundles
            else [bundle_id]
        )
        if not targets:
            console.print("[yellow]No installed bundles to update.[/yellow]")
            return

        stack = _build_stack(project_root, offline=offline)
        from ...bundler.services.adapters import DefaultPrimitiveInstaller
        from ...bundler.services.installer import install_bundle
        from ...bundler.services.resolver import resolve_install_plan

        installer = DefaultPrimitiveInstaller(allow_network=not offline)
        for target in targets:
            if not any(r.bundle_id == target for r in records):
                raise BundlerError(f"Bundle '{target}' is not installed.")
            resolved = stack.resolve(target)
            if not resolved.install_allowed:
                raise BundlerError(
                    f"Bundle '{target}' resolves only from a discovery-only source "
                    f"('{resolved.source.id}'); it cannot be updated from there. "
                    "Update requires an install-allowed source (FR-025)."
                )
            manifest = _download_manifest(resolved, offline=offline)
            detected = active_integration(project_root)
            plan = resolve_install_plan(
                manifest,
                speckit_version=_speckit_version(),
                active_integration=detected if detected is not None else integration,
                integration_explicit=bool(integration) and detected is None,
            )
            install_bundle(project_root, plan, installer, manifest=manifest, refresh=True)
            console.print(f"[green]✓[/green] Updated '{target}' to v{plan.version}.")
    except BundlerError as exc:
        _fail(str(exc))
        return


@bundle_app.command("remove")
def bundle_remove(
    bundle_id: str = typer.Argument(..., help="Installed bundle id to remove"),
) -> None:
    """Uninstall only the components this bundle contributed (no collateral removals)."""
    try:
        project_root = require_project_root()
        from ...bundler.services.adapters import DefaultPrimitiveInstaller
        from ...bundler.services.installer import remove_bundle

        result = remove_bundle(project_root, bundle_id, DefaultPrimitiveInstaller())
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Removed '{result.bundle_id}' "
        f"({len(result.uninstalled)} uninstalled, {len(result.skipped)} kept for other bundles)."
    )


# ===== Author =====


@bundle_app.command("validate")
def bundle_validate(
    path: Path = typer.Option(
        None, "--path", help="Bundle directory or bundle.yml (default: cwd)"
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Do not access catalogs; verify references against bundled/installed only",
    ),
) -> None:
    """Report whether the manifest is well-formed and references resolve."""
    try:
        manifest_path = _resolve_manifest_path(path)
        from ...bundler.lib.project import find_project_root
        from ...bundler.models.manifest import BundleManifest
        from ...bundler.services.references import make_reference_checker
        from ...bundler.services.validator import validate_manifest

        manifest = BundleManifest.from_file(manifest_path)
        ref_root = find_project_root(manifest_path.parent) or Path.cwd()
        ref_warnings: list[str] = []
        checker = make_reference_checker(
            ref_root, allow_network=not offline, warnings=ref_warnings
        )
        report = validate_manifest(manifest, reference_checker=checker)
        report.warnings.extend(ref_warnings)
    except BundlerError as exc:
        _fail(str(exc))
        return

    for warning in report.warnings:
        console.print(f"[yellow]![/yellow] {warning}")
    if not report.ok:
        console.print("[red]Manifest is invalid:[/red]")
        for error in report.errors:
            console.print(f"  [red]-[/red] {error}")
        raise typer.Exit(code=1)
    console.print(f"[green]✓[/green] {manifest.bundle.id} is well-formed and valid.")


@bundle_app.command("build")
def bundle_build(
    path: Path = typer.Option(
        None, "--path", help="Bundle directory (default: cwd)"
    ),
    output: Path = typer.Option(None, "--output", help="Output directory for the artifact"),
) -> None:
    """Produce a single versioned distributable artifact (.zip)."""
    try:
        bundle_dir = (path or Path.cwd()).resolve()
        if bundle_dir.is_file():
            bundle_dir = bundle_dir.parent
        from ...bundler.services.packager import build_bundle

        result = build_bundle(bundle_dir, output_dir=output)
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Built {result.artifact_path.name} "
        f"({result.file_count} files) → {result.artifact_path}"
    )


@bundle_app.command("init")
def bundle_init(
    bundle: str = typer.Argument(None, help="Optional bundle to install after init"),
    integration: str = typer.Option(None, "--integration", help="Integration override"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
) -> None:
    """Ensure the project is initialized (idempotent), then optionally install a bundle."""
    from ...bundler.lib.project import find_project_root

    try:
        project_root = find_project_root()
        if project_root is None:
            init_integration = _resolve_init_integration(integration, None)
            console.print(
                f"[cyan]Initializing a Spec Kit project with integration "
                f"'{init_integration}'…[/cyan]"
            )
            _run_init(init_integration, script_type=_default_script_type(), offline=offline)
            project_root = require_project_root()
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(f"[green]✓[/green] Spec Kit project ready at {project_root}.")
    if bundle:
        bundle_install(bundle, integration=integration, offline=offline)


# ===== Catalog management =====


@bundle_catalog_app.command("list")
def catalog_list() -> None:
    """Print the active, priority-ordered catalog stack with scope and policy."""
    try:
        project_root = require_project_root()
        from ...bundler.models.catalog import Scope, load_source_stack

        sources = load_source_stack(project_root, user_config_dir=_user_config_dir())
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print("\n[bold cyan]Catalog stack[/bold cyan] (highest precedence first):\n")
    only_builtin = all(s.scope == Scope.BUILTIN for s in sources)
    for source in sources:
        console.print(
            f"  [bold]{source.id}[/bold]  priority={source.priority}  "
            f"policy={source.install_policy.value}  scope={source.scope.value}"
        )
        console.print(f"    [dim]{source.url}[/dim]")
    if only_builtin:
        console.print("\n[dim]Using the built-in default stack.[/dim]")


@bundle_catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(..., help="Catalog URL"),
    policy: str = typer.Option(
        "install-allowed", "--policy", help="install-allowed | discovery-only"
    ),
    priority: int = typer.Option(10, "--priority", help="Source priority (lower = higher)"),
    source_id: str = typer.Option(None, "--id", help="Explicit source id"),
) -> None:
    """Register a project-scoped catalog source and persist it."""
    try:
        project_root = require_project_root()
        from ...bundler.commands_impl.catalog_config import add_source

        source = add_source(project_root, url, policy=policy, priority=priority, source_id=source_id)
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Added catalog '{source.id}' "
        f"(priority {source.priority}, {source.install_policy.value})."
    )


@bundle_catalog_app.command("remove")
def catalog_remove(
    id_or_url: str = typer.Argument(..., help="Source id or url to remove"),
) -> None:
    """Remove a project-scoped catalog source (built-in defaults can't be deleted)."""
    try:
        project_root = require_project_root()
        from ...bundler.commands_impl.catalog_config import remove_source

        removed = remove_source(project_root, id_or_url)
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(f"[green]✓[/green] Removed catalog source '{removed}'.")


# ===== internal helpers =====


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


def _bundle_overlaps(project_root: Path, manifest, *, offline: bool) -> list[str]:
    """Return informational overlaps between *manifest* and installed bundles."""
    if manifest is None:
        return []
    try:
        from ...bundler.services.conflict import detect_conflicts

        report = detect_conflicts(
            manifest,
            active_integration(project_root),
            load_records(project_root),
        )
        return list(report.overlaps)
    except BundlerError:
        return []


def _local_manifest_source(arg: str):
    """Return a :class:`BundleManifest` if *arg* points at a local bundle.

    Supports a built ``.zip`` artifact, a bundle directory, or a ``bundle.yml``
    file. Returns ``None`` when *arg* is not an existing path, so callers fall
    back to catalog-stack resolution by bundle id.
    """
    from ...bundler.models.manifest import BundleManifest

    candidate = Path(arg).expanduser()
    if not candidate.exists():
        return None

    if candidate.is_dir():
        manifest_path = candidate / "bundle.yml"
        if not manifest_path.exists():
            raise BundlerError(f"No bundle.yml found in '{candidate}'.")
        return BundleManifest.from_file(manifest_path)

    if candidate.suffix == ".zip":
        import io
        import zipfile

        import yaml as _yaml

        with zipfile.ZipFile(candidate) as archive:
            try:
                raw = archive.read("bundle.yml")
            except KeyError as exc:
                raise BundlerError(
                    f"Artifact '{candidate}' does not contain a bundle.yml."
                ) from exc
        data = _yaml.safe_load(io.BytesIO(raw))
        return BundleManifest.from_dict(data)

    if candidate.name == "bundle.yml" or candidate.suffix in (".yml", ".yaml"):
        return BundleManifest.from_file(candidate)

    raise BundlerError(
        f"'{candidate}' is not a recognised bundle source (.zip artifact, bundle "
        "directory, or bundle.yml)."
    )


def _resolve_manifest_path(path: Path | None) -> Path:
    target = (path or Path.cwd()).resolve()
    if target.is_dir():
        target = target / "bundle.yml"
    if not target.exists():
        raise BundlerError(f"No bundle.yml found at '{target}'.")
    return target


def _download_manifest(resolved, *, offline: bool):
    """Resolve a bundle's manifest from its catalog ``download_url``.

    Local/``file://`` URLs always work offline and may point at a ``.zip``
    artifact, a bundle directory, or a ``bundle.yml`` (handled by
    :func:`_local_manifest_source`). Remote ``https://`` URLs are fetched with
    the shared authenticated, redirect-validated HTTP client, and only when not
    ``--offline``.
    """
    from urllib.parse import urlparse

    url = resolved.entry.download_url
    if not url:
        raise BundlerError(
            f"Catalog entry '{resolved.entry.id}' has no download_url; cannot resolve "
            "its manifest."
        )
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    # On Windows an absolute path like ``C:\bundle.yml`` parses with a
    # single-letter ``scheme``; treat it as a local file, not a URL scheme.
    if scheme in ("", "file") or re.match(r"^[A-Za-z]:[\\/]", url):
        local = Path(parsed.path if scheme == "file" else url)
        manifest = _local_manifest_source(str(local))
        if manifest is None:
            raise BundlerError(f"Bundle manifest not found: {local}")
        return manifest

    if scheme in ("http", "https"):
        if offline:
            raise BundlerError(
                f"Network access disabled; cannot download bundle '{resolved.entry.id}' "
                f"from {url}."
            )
        return _download_remote_manifest(resolved.entry.id, url)

    raise BundlerError(
        f"Unsupported download_url scheme for bundle '{resolved.entry.id}': {url}"
    )


def _require_https(label: str, url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
        raise BundlerError(
            f"Refusing to download {label} over non-HTTPS URL: {url}"
        )
    if not parsed.hostname:
        raise BundlerError(f"Refusing to download {label} from URL with no host: {url}")


def _download_remote_manifest(entry_id: str, url: str):
    """Fetch a remote bundle artifact over HTTPS and extract its manifest."""
    import io
    import tempfile

    from ...authentication.http import open_url

    def _validate_redirect(old_url: str, new_url: str) -> None:
        _require_https(f"bundle '{entry_id}'", new_url)

    _require_https(f"bundle '{entry_id}'", url)
    try:
        with open_url(url, timeout=30, redirect_validator=_validate_redirect) as resp:
            _require_https(f"bundle '{entry_id}'", resp.geturl())
            raw = resp.read()
    except BundlerError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise BundlerError(f"Failed to download bundle '{entry_id}' from {url}: {exc}") from exc

    # A .zip artifact is written to a temp file and parsed via the local-source
    # path (which extracts bundle.yml); any other payload is treated as YAML.
    if url.lower().endswith(".zip"):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "bundle.zip"
            artifact.write_bytes(raw)
            manifest = _local_manifest_source(str(artifact))
            if manifest is None:
                raise BundlerError(
                    f"Downloaded artifact for bundle '{entry_id}' is not a valid bundle."
                )
            return manifest

    import yaml as _yaml

    from ...bundler.models.manifest import BundleManifest

    data = _yaml.safe_load(io.BytesIO(raw))
    return BundleManifest.from_dict(data)


def register(app: typer.Typer) -> None:
    """Attach the bundle command group to the root Typer app."""
    app.add_typer(bundle_app, name="bundle")
