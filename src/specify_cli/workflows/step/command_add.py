"""Command handler for ``specify workflow step add``.

The registered handler stays a thin orchestrator: it parses options, validates
them, and dispatches to a per-source private helper (catalog, ``--dev`` local
directory, and ``--from`` archive URL). All three sources converge on
``step/installer.py``'s single validation + staged-commit path.
"""

from __future__ import annotations

from typing import Annotated

from .. import _commands as cli
from . import _helpers as step_helpers
from . import step_app

_MAX_STEP_CATALOG_RESPONSE_BYTES = 50 * 1024 * 1024


def _cleanup_download_tmp_path(tmp_path: cli.Path | None) -> None:
    """Best-effort unlink of a partially-downloaded step archive temp file.

    A cleanup ``OSError`` must never replace/mask whatever error or interrupt is
    already propagating -- warn about it and keep going.
    """
    if tmp_path is None:
        return
    try:
        tmp_path.unlink(missing_ok=True)
    except OSError as cleanup_exc:
        cli.console.print(
            "[yellow]Warning:[/yellow] Could not remove temporary "
            f"step download file: {cli._escape_markup(str(cleanup_exc))} "
            f"(path: {cli._escape_markup(str(tmp_path))})"
        )


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
    import tempfile
    from urllib.parse import urlparse

    from rich.panel import Panel

    from specify_cli.authentication.github_http import (
        resolve_github_release_asset_api_url as _resolve_gh_asset,
    )
    from specify_cli.authentication.http import (
        github_provider_hosts as _github_provider_hosts,
    )
    from specify_cli.authentication.http import open_url as _open_url

    from . import installer

    try:
        parsed = urlparse(from_url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        raise installer.StepInstallError(
            f"Invalid URL: {cli._escape_markup(from_url)}"
        ) from None
    if not hostname:
        raise installer.StepInstallError(
            f"Invalid URL: {cli._escape_markup(from_url)}"
        )
    if not cli.is_https_or_localhost_http(from_url):
        raise installer.StepInstallError(
            "URL must use HTTPS for security. HTTP is only allowed for "
            "loopback URLs."
        )

    # Reject before the trust prompt and before any network request.
    installer.check_installable(project_root, step_id, force=force)

    # Prompt BEFORE any request (and before any spinner) so the user can see
    # and answer it; a declined prompt issues no request and exits 0.
    cli.console.print()
    cli.console.print(
        Panel(
            "[bold]You are installing a workflow step type directly from an "
            "external URL.\nA step package contains executable Python.[/bold]\n\n"
            f"URL: {cli._escape_markup(from_url)}\n\n"
            "Only install step packages from sources you trust.",
            title="[bold yellow]⚠ Untrusted Source[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    cli.console.print()
    if not cli.typer.confirm("Continue with installation?", default=False):
        cli.console.print("Cancelled")
        raise cli.typer.Exit(0)

    download_url = from_url
    extra_headers = None
    tmp_path: cli.Path | None = None
    extract_tmp: tempfile.TemporaryDirectory[str] | None = None
    committed = False
    try:
        resolved_url = _resolve_gh_asset(
            from_url,
            _open_url,
            timeout=30,
            github_hosts=_github_provider_hosts(),
            redirect_validator=cli._reject_insecure_download_redirect,
        )
        if resolved_url:
            download_url = resolved_url
            extra_headers = {"Accept": "application/octet-stream"}

        with _open_url(
            download_url,
            timeout=30,
            extra_headers=extra_headers,
            redirect_validator=cli._reject_insecure_download_redirect,
        ) as resp:
            final_url = resp.geturl()
            if not cli.is_https_or_localhost_http(final_url):
                raise installer.StepInstallError(
                    f"URL redirected to non-HTTPS: {cli._escape_markup(final_url)}"
                )
            content_type = (
                resp.getheader("Content-Type")
                if hasattr(resp, "getheader")
                else None
            )
            declarations = [
                ("requested URL", from_url, cli.archive_format_from_name(from_url)),
                ("final URL", final_url, cli.archive_format_from_name(final_url)),
                (
                    "Content-Type",
                    content_type or "",
                    cli.archive_format_from_content_type(content_type),
                ),
            ]
            recognized = [item for item in declarations if item[2] is not None]
            archive_format = recognized[0][2] if recognized else None
            if archive_format is None:
                raise installer.StepInstallError(
                    "URL does not reference a supported archive "
                    "(.zip, .tar.gz, or .tgz)"
                )
            if any(item[2] != archive_format for item in recognized):
                details = ", ".join(
                    f"{label} declares {declared}"
                    for label, _value, declared in recognized
                )
                raise installer.StepInstallError(
                    f"Archive format mismatch: {cli._escape_markup(details)}"
                )
            downloaded = cli.read_response_limited(
                resp,
                error_type=ValueError,
                label="step archive download",
            )

        with tempfile.NamedTemporaryFile(
            suffix=cli.archive_suffix(archive_format), delete=False
        ) as tmp:
            tmp_path = cli.Path(tmp.name)
            tmp.write(downloaded)

        extract_tmp = tempfile.TemporaryDirectory(prefix="speckit-step-archive-")
        extracted_root = cli.Path(extract_tmp.name)
        try:
            # safe_extract_archive re-detects and confirms the archive bytes.
            cli.safe_extract_archive(
                tmp_path,
                extracted_root,
                source_name=next(
                    value for _label, value, declared in recognized if declared is not None
                ),
                content_type=content_type,
            )
            package_root = installer.resolve_package_root(extracted_root)
            entry = installer.install_step_package(
                project_root,
                step_id,
                package_root,
                source="url",
                force=force,
            )
            committed = True
        finally:
            try:
                extract_tmp.cleanup()
            except OSError as cleanup_exc:
                if committed:
                    cli.console.print(
                        "[yellow]Warning:[/yellow] Could not remove temporary step "
                        f"archive directory: {cli._escape_markup(str(cleanup_exc))} "
                        f"(path: {cli._escape_markup(extract_tmp.name)})"
                    )
                elif __import__("sys").exc_info()[0] is None:
                    raise installer.StepInstallError(
                        "Failed to remove temporary step archive directory: "
                        f"{cleanup_exc}"
                    ) from cleanup_exc
    except cli.typer.Exit:
        raise
    except installer.StepInstallError:
        raise
    except Exception as exc:
        raise installer.StepInstallError(
            f"Failed to install step from URL: {cli._escape_markup(str(exc))}"
        ) from exc
    finally:
        _cleanup_download_tmp_path(tmp_path)

    _print_installed(step_id, entry)


def _install_from_catalog(project_root: cli.Path, step_id: str, *, force: bool) -> None:
    """Install a step package from the step catalog.

    The catalog fetch (URL/derivation/count preflight) stays a catalog concern;
    the materialized files are then handed to the shared installer.
    """
    import tempfile

    from . import installer
    from .catalog import StepCatalog, StepCatalogError

    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError as exc:
        raise installer.StepInstallError(str(exc)) from exc

    if not info:
        raise installer.StepInstallError(
            f"Step type '{step_id}' not found in catalog"
        )

    if not info.get("_install_allowed", True):
        cli.console.print(
            f"[yellow]Warning:[/yellow] Step type '{step_id}' is from a "
            "discovery-only catalog"
        )
        cli.console.print("Direct installation is not enabled for this catalog source.")
        raise cli.typer.Exit(1)

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
            f"{installer._MAX_STEP_PACKAGE_FILES}-file limit"
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

    package_tmp = tempfile.TemporaryDirectory(prefix="speckit-step-package-")
    package_dir = cli.Path(package_tmp.name)
    committed = False
    try:
        try:
            step_yml_content = _safe_fetch(step_yml_url)
            init_py_content = _safe_fetch(init_url)
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
                file_content = _safe_fetch(file_url)
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
        try:
            package_tmp.cleanup()
        except OSError as cleanup_exc:
            if committed:
                cli.console.print(
                    "[yellow]Warning:[/yellow] Could not remove temporary step "
                    f"package directory: {cli._escape_markup(str(cleanup_exc))} "
                    f"(path: {cli._escape_markup(package_tmp.name)})"
                )
            elif __import__("sys").exc_info()[0] is None:
                raise installer.StepInstallError(
                    "Failed to remove temporary step package directory: "
                    f"{cleanup_exc}"
                ) from cleanup_exc

    _print_installed(step_id, entry)


@step_app.command("add")
def workflow_step_add(
    step_id: str = cli.typer.Argument(..., help="Step type ID"),
    dev: Annotated[str | None, cli.typer.Option("--dev", help="Install from a local step package directory")] = None,
    from_url: Annotated[str | None, cli.typer.Option("--from", help="Install from a .zip/.tar.gz/.tgz archive URL")] = None,
    force: Annotated[bool, cli.typer.Option("--force", help="Replace an existing installation")] = False,
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

    step_helpers._validate_step_id_or_exit(step_id)

    try:
        if dev is not None:
            _install_from_dev(project_root, step_id, dev, force=force)
        elif from_url is not None:
            _install_from_url(project_root, step_id, from_url, force=force)
        else:
            _install_from_catalog(project_root, step_id, force=force)
    except installer.StepInstallError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1) from exc
