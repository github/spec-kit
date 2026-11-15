"""Command handler for ``specify workflow step add``.

The registered handler stays a thin orchestrator: it parses options, validates
them, and dispatches to a per-source private helper (catalog, ``--dev`` local
directory, and ``--from`` archive URL). All three sources converge on
``step/installer.py``'s single validation + staged-commit path.
"""

from __future__ import annotations

import hashlib
import sys
from typing import Annotated

from .. import _commands as cli
from . import _helpers as step_helpers
from . import step_app

_MAX_STEP_CATALOG_RESPONSE_BYTES = 50 * 1024 * 1024


def _print_installed(step_id: str, entry: dict) -> None:
    step_name = entry.get("name") or step_id
    cli.console.print(
        "[green]✓[/green] Step type "
        f"'{cli._escape_markup(str(step_name))}' "
        f"({cli._escape_markup(str(step_id))}) installed"
    )
    cli.console.print(
        "  Use [cyan]specify workflow step list[/cyan] to verify the installation."
    )


def _install_from_dev(
    project_root: cli.Path, step_id: str, dev: str, *, force: bool
) -> None:
    """Install a complete step package from a local directory."""
    from . import installer

    dev_path = cli.Path(dev).expanduser()
    if dev_path.is_symlink():
        raise installer.StepInstallError(
            f"Refusing to install from a symlinked source directory: '{dev_path}'"
        )
    if not dev_path.is_dir():
        raise installer.StepInstallError(
            "--dev source must be a directory containing step.yml and "
            f"__init__.py: '{dev_path}'"
        )

    entry = installer.install_step_package(
        project_root, step_id, dev_path, source="local", force=force
    )
    _print_installed(step_id, entry)


def _install_from_url(
    project_root: cli.Path, step_id: str, from_url: str, *, force: bool
) -> None:
    """Install a step package archive from a direct URL."""
    from .. import _archive_install as archive
    from . import installer

    entry = archive.install_from_archive_url(
        archive.ArchiveRequest(project_root, step_id, from_url, force),
        installer._step_spec(),
        archive.ArchiveHooks(
            preflight=lambda root, sid, force: installer.check_installable(
                root, sid, force=force
            ),
            resolve_root=lambda extracted: installer.resolve_package_root(extracted),
            install=lambda root, sid, package, force: installer.install_step_package(
                root, sid, package, source="url", force=force
            ),
        ),
    )
    _print_installed(step_id, entry)


def _install_from_catalog(
    project_root: cli.Path, step_id: str, *, force: bool, version: str | None = None,
    selected_info: dict | None = None,
) -> None:
    """Install a step package from the step catalog.

    The catalog fetch (URL/derivation/count preflight) stays a catalog concern;
    the materialized files are then handed to the shared installer.
    """
    import tempfile

    from . import installer
    from .catalog import StepCatalog, StepCatalogError
    from .catalog._versions import validate_checksums

    if selected_info is not None:
        info = selected_info
    else:
        catalog = StepCatalog(project_root)
        try:
            info = (
                catalog.get_step_info(step_id, version=version)
                if version is not None
                else catalog.get_step_info(step_id)
            )
        except StepCatalogError as exc:
            raise installer.StepInstallError(str(exc)) from exc

    if not info:
        raise installer.StepInstallError(
            f"Step type '{step_id}' version '{version}' not found in the winning catalog"
            if version is not None
            else f"Step type '{step_id}' not found in catalog"
        )

    if not info.get("_install_allowed", True):
        cli.console.print(
            "[yellow]Warning:[/yellow] Step type "
            f"'{cli._escape_markup(step_id)}' is from a "
            "discovery-only catalog"
        )
        cli.console.print("Direct installation is not enabled for this catalog source.")
        raise cli.typer.Exit(1)

    try:
        validate_checksums(info, step_id, required=version is not None)
    except StepCatalogError as exc:
        raise installer.StepInstallError(str(exc)) from exc
    checksums = info.get("sha256")

    # Reject built-in collisions and duplicates before any download.
    installer.check_installable(project_root, step_id, force=force)

    declared_step_yml_url = info.get("step_yml_url")
    if declared_step_yml_url is not None and not isinstance(declared_step_yml_url, str):
        raise installer.StepInstallError(
            f"Catalog entry for '{step_id}' has a malformed step.yml URL; "
            "expected a non-empty string"
        )
    step_yml_url = declared_step_yml_url or info.get("url")
    if step_yml_url is None or (
        isinstance(step_yml_url, str) and not step_yml_url.strip()
    ):
        raise installer.StepInstallError(
            f"Catalog entry for '{step_id}' has no URL"
        )
    if not isinstance(step_yml_url, str):
        raise installer.StepInstallError(
            f"Catalog entry for '{step_id}' has a malformed step.yml URL; "
            "expected a non-empty string"
        )

    # Derive __init__.py URL: replace trailing step.yml with __init__.py or use
    # explicit init_url if provided.
    init_url = info.get("init_url")
    if init_url is not None and (not isinstance(init_url, str) or not init_url.strip()):
        raise installer.StepInstallError(
            f"Catalog entry for '{step_id}' has a malformed __init__.py URL; "
            "expected a non-empty string"
        )
    if not init_url:
        if step_yml_url.endswith("step.yml"):
            init_url = step_yml_url[: -len("step.yml")] + "__init__.py"
        else:
            raise installer.StepInstallError(
                f"Cannot derive __init__.py URL from '{step_yml_url}'. "
                "Catalog entry should provide 'init_url' or a 'url' ending in "
                "'step.yml'."
            )

    # Preflight the declared file count before creating a staging directory or
    # issuing any request. The two required files are always part of the
    # package; duplicate declarations for them in extra_files are ignored below
    # and do not count twice.
    extra_files = info.get("extra_files")
    if extra_files is not None and not isinstance(extra_files, dict):
        cli.console.print(
            "[yellow]Warning:[/yellow] Catalog entry 'extra_files' is not a mapping; "
            "additional package files will not be downloaded."
        )
        extra_files = {}

    def _is_required_package_file(rel_path: object) -> bool:
        """Match portable path/case aliases of the two required package files."""
        if not isinstance(rel_path, str):
            return False
        parts = cli.PurePosixPath(rel_path.replace("\\", "/")).parts
        return len(parts) == 1 and parts[0].casefold() in {
            "step.yml",
            "__init__.py",
        }

    declared_extra_count = sum(
        1 for rel_path in (extra_files or {}) if not _is_required_package_file(rel_path)
    )
    package_file_count = 2 + declared_extra_count
    if package_file_count > installer._MAX_STEP_PACKAGE_FILES:
        raise installer.StepInstallError(
            f"Step package declares {package_file_count} files, exceeding the "
            f"{installer._MAX_STEP_PACKAGE_FILES}-entry limit (files and "
            "directories combined)"
        )

    from specify_cli.authentication.http import open_url as _open_url

    def _safe_fetch(url: str) -> bytes:
        if not cli.is_https_or_localhost_http(url):
            raise ValueError(f"Refusing to fetch from non-HTTPS URL: {url}")
        with _open_url(
            url, timeout=30, redirect_validator=cli._reject_insecure_download_redirect
        ) as resp:
            final_url = resp.geturl()
            if not cli.is_https_or_localhost_http(final_url):
                raise ValueError(f"Redirect to non-HTTPS URL: {final_url}")
            return cli.read_response_limited(
                resp,
                max_bytes=_MAX_STEP_CATALOG_RESPONSE_BYTES,
                error_type=ValueError,
                label="step package response",
            )

    def _fetch_checked(url: str, name: str) -> bytes:
        content = _safe_fetch(url)
        if checksums and (
            hashlib.sha256(content).hexdigest().lower() != checksums[name].lower()
        ):
            raise installer.StepInstallError(f"SHA-256 checksum mismatch for '{name}'")
        return content

    try:
        package_tmp = tempfile.TemporaryDirectory(prefix="speckit-step-package-")
    except OSError as exc:
        raise installer.StepInstallError(
            f"Failed to create temporary step package directory: {exc}"
        ) from exc
    package_dir = cli.Path(package_tmp.name)
    committed = False
    try:
        try:
            step_yml_content = _fetch_checked(step_yml_url, "step.yml")
            init_py_content = _fetch_checked(init_url, "__init__.py")
        except Exception as exc:
            raise installer.StepInstallError(
                f"Failed to download step files: {exc}"
            ) from exc

        package_bytes = len(step_yml_content) + len(init_py_content)
        if package_bytes > installer._MAX_STEP_PACKAGE_BYTES:
            raise installer.StepInstallError(
                f"Step package exceeds the "
                f"{installer._MAX_STEP_PACKAGE_BYTES}-byte total size limit"
            )

        try:
            (package_dir / "step.yml").write_bytes(step_yml_content)
            (package_dir / "__init__.py").write_bytes(init_py_content)
        except OSError as exc:
            raise installer.StepInstallError(
                f"Failed to write step files to staging directory: {exc}"
            ) from exc

        # Optionally download additional package files declared in the catalog
        # entry (e.g. helper modules). Each entry in ``extra_files`` is a mapping
        # of relative-path → URL. Paths are validated to stay within the step
        # package directory to prevent path-traversal attacks.
        for rel_path, file_url in (extra_files or {}).items():
            if not isinstance(rel_path, str) or not rel_path.strip():
                raise installer.StepInstallError(
                    "Catalog entry 'extra_files' contains an empty or non-string "
                    "path key"
                )
            if _is_required_package_file(rel_path):
                continue  # already written above
            path_parts = cli.Path(rel_path).parts
            if not path_parts or any(seg in ("", ".", "..") for seg in path_parts):
                raise installer.StepInstallError(
                    f"extra_files path '{rel_path}' is not a valid relative file path"
                )
            if not isinstance(file_url, str) or not file_url.strip():
                raise installer.StepInstallError(
                    f"extra_files entry '{rel_path}' has an empty or non-string URL"
                )
            resolved_base = package_dir.resolve()
            dest = (package_dir / rel_path).resolve()
            try:
                dest.relative_to(resolved_base)
            except ValueError:
                raise installer.StepInstallError(
                    f"extra_files path '{rel_path}' is outside the step package "
                    "directory"
                ) from None
            try:
                file_content = _fetch_checked(file_url, rel_path)
            except Exception as exc:
                raise installer.StepInstallError(
                    f"Failed to download extra file '{rel_path}': {exc}"
                ) from exc
            package_bytes += len(file_content)
            if package_bytes > installer._MAX_STEP_PACKAGE_BYTES:
                raise installer.StepInstallError(
                    f"Step package exceeds the "
                    f"{installer._MAX_STEP_PACKAGE_BYTES}-byte total size limit"
                )
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file_content)
            except OSError as exc:
                raise installer.StepInstallError(
                    f"Failed to write extra file '{rel_path}': {exc}"
                ) from exc

        if version is not None or "releases" in info:
            from packaging.version import InvalidVersion, Version

            step_meta = installer.validate_step_package(package_dir, step_id)
            declared_version = step_meta.get("version")
            try:
                matches = (
                    isinstance(declared_version, str)
                    and Version(declared_version) == Version(info["version"])
                )
            except (InvalidVersion, TypeError, KeyError):
                matches = False
            if not matches:
                raise installer.StepInstallError(
                    f"step.yml version ({declared_version!r}) does not match "
                    f"catalog version ({info.get('version')!r})"
                )

        entry = installer.install_step_package(
            project_root,
            step_id,
            package_dir,
            source="catalog",
            catalog_name=info.get("_catalog_name", ""),
            catalog_metadata=info,
            force=force,
        )
        committed = True
    finally:
        primary_error = sys.exc_info()[1]
        try:
            package_tmp.cleanup()
        except OSError as cleanup_exc:
            if package_tmp.name and cli.Path(package_tmp.name).exists():
                detail = (
                    f"{cli._escape_markup(str(cleanup_exc))} "
                    f"(path: {cli._escape_markup(package_tmp.name)})"
                )
                cli.console.print(
                    "[yellow]Warning:[/yellow] Could not remove temporary "
                    f"step package directory: {detail}"
                )
            if primary_error is None and not committed:
                raise installer.StepInstallError(
                    "Failed to remove temporary step package directory: "
                    f"{cleanup_exc}"
                ) from cleanup_exc
            # Do not raise from cleanup: preserve a primary download/install
            # error, or report a successful install with a warning only.

    _print_installed(step_id, entry)


def _install_preselected_step(
    step_id: str, *, version: str | None, selected_info: dict,
) -> None:
    """Install a bundle-selected release with the normal step ID preflight."""
    project_root = cli._require_specify_project()
    step_helpers._validate_step_id_or_exit(step_id)
    _install_from_catalog(
        project_root, step_id, force=False, version=version,
        selected_info=selected_info,
    )


@step_app.command("add")
def workflow_step_add(
    step_id: str = cli.typer.Argument(..., help="Step type ID"),
    dev: Annotated[str | None, cli.typer.Option("--dev", help="Install from a local step package directory")] = None,
    from_url: Annotated[str | None, cli.typer.Option("--from", help="Install from a .zip/.tar.gz/.tgz archive URL")] = None,
    force: Annotated[bool, cli.typer.Option("--force", help="Replace an existing installation")] = False,
    version: Annotated[
        str | None,
        cli.typer.Option("--version", help="Install an exact catalog release"),
    ] = None,
):
    """Install a custom step type from the catalog, a local directory, or a URL."""
    from . import installer

    project_root = cli._require_specify_project()

    if dev is not None and from_url is not None:
        cli.console.print(
            "[red]Error:[/red] --dev and --from are mutually exclusive"
        )
        raise cli.typer.Exit(1)
    if dev is not None and not dev.strip():
        cli.console.print("[red]Error:[/red] --dev value must not be empty")
        raise cli.typer.Exit(1)
    if from_url is not None and not from_url.strip():
        cli.console.print("[red]Error:[/red] --from value must not be empty")
        raise cli.typer.Exit(1)
    if version is not None and (dev is not None or from_url is not None):
        cli.console.print("[red]Error:[/red] --version requires a catalog step ID")
        raise cli.typer.Exit(1)
    if version is not None and not version.strip():
        cli.console.print("[red]Error:[/red] --version value must not be empty")
        raise cli.typer.Exit(1)

    step_helpers._validate_step_id_or_exit(step_id)

    try:
        if dev is not None:
            _install_from_dev(project_root, step_id, dev, force=force)
        elif from_url is not None:
            _install_from_url(project_root, step_id, from_url, force=force)
        else:
            _install_from_catalog(project_root, step_id, force=force, version=version)
    except installer.StepInstallError as exc:
        cli._print_package_error(exc)
        raise cli.typer.Exit(1) from exc
