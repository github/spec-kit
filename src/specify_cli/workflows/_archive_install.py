"""CLI flow shared by ``workflow step add --from`` and ``workflow function add --from``.

Downloading an archive from a URL, confirming trust, extracting it safely and
handing the package root to the kind's installer is identical for every package
kind that contains executable Python. The kind-specific parts are supplied as
:class:`ArchiveHooks`; naming and the error type come from the shared
:class:`~specify_cli.workflows._package_install.PackageSpec`.

This module is a CLI layer (it prompts and prints); the domain installers it
calls stay CLI-independent.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _commands as cli
from ._package_install import PackageSpec


@dataclass(frozen=True)
class ArchiveRequest:
    """What to install from which URL."""

    project_root: Path
    package_id: str
    url: str
    force: bool = False


@dataclass(frozen=True)
class ArchiveHooks:
    """Package-kind steps of the URL flow."""

    preflight: Callable[[Path, str, bool], Any]  # (root, id, force) -> None; rejects early
    resolve_root: Callable[[Path], Path]  # extracted dir -> package dir
    install: Callable[[Path, str, Path, bool], dict[str, Any]]  # (root, id, pkg, force)


def _cleanup_download_tmp_path(tmp_path: Path | None, spec: PackageSpec) -> None:
    """Best-effort unlink of a partially-downloaded archive temp file.

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
            f"{spec.lower} download file: {cli._escape_markup(str(cleanup_exc))} "
            f"(path: {cli._escape_markup(str(tmp_path))})"
        )


def install_from_archive_url(
    request: ArchiveRequest, spec: PackageSpec, hooks: ArchiveHooks
) -> dict[str, Any]:
    """Install a package archive from a direct URL and return its registry entry."""
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

    project_root, package_id, from_url, force = (
        request.project_root, request.package_id, request.url, request.force,
    )
    error = spec.error

    try:
        parsed = urlparse(from_url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        raise error(f"Invalid URL: {from_url}") from None
    if not hostname:
        raise error(f"Invalid URL: {from_url}")
    if not cli.is_https_or_localhost_http(from_url):
        raise error(
            "URL must use HTTPS for security. HTTP is only allowed for "
            "loopback URLs."
        )

    # Reject before the trust prompt and before any network request.
    hooks.preflight(project_root, package_id, force)

    # Prompt BEFORE any request (and before any spinner) so the user can see
    # and answer it; a declined prompt issues no request and exits 0.
    kind = spec.kind_label.lower()
    cli.console.print()
    cli.console.print(
        Panel(
            f"[bold]You are installing a workflow {kind} directly from an "
            f"external URL.\nA {spec.lower} package contains executable Python.[/bold]\n\n"
            f"URL: {cli._escape_markup(from_url)}\n\n"
            f"Only install {spec.lower} packages from sources you trust.",
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
    tmp_path: Path | None = None
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
                raise error(f"URL redirected to non-HTTPS: {final_url}")
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
            if any(item[2] != archive_format for item in recognized):
                details = ", ".join(
                    f"{label} declares {declared}"
                    for label, _value, declared in recognized
                )
                raise error(f"Archive format mismatch: {details}")
            downloaded = cli.read_response_limited(
                resp,
                error_type=ValueError,
                label=f"{spec.lower} archive download",
            )

        with tempfile.NamedTemporaryFile(
            suffix=cli.archive_suffix(archive_format) if archive_format else ".archive",
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(downloaded)

        try:
            extract_tmp = tempfile.TemporaryDirectory(
                prefix=f"speckit-{spec.lower}-archive-"
            )
        except OSError as exc:
            raise error(
                f"Failed to create temporary {spec.lower} archive directory: {exc}"
            ) from exc
        extracted_root = Path(extract_tmp.name)
        try:
            # safe_extract_archive re-detects and confirms the archive bytes.
            cli.safe_extract_archive(
                tmp_path,
                extracted_root,
                source_name=recognized[0][1] if recognized else None,
                content_type=content_type,
            )
            package_root = hooks.resolve_root(extracted_root)
            entry = hooks.install(project_root, package_id, package_root, force)
            committed = True
        finally:
            primary_error = sys.exc_info()[1]
            try:
                extract_tmp.cleanup()
            except OSError as cleanup_exc:
                if extract_tmp.name and Path(extract_tmp.name).exists():
                    detail = (
                        f"{cli._escape_markup(str(cleanup_exc))} "
                        f"(path: {cli._escape_markup(extract_tmp.name)})"
                    )
                    cli.console.print(
                        "[yellow]Warning:[/yellow] Could not remove temporary "
                        f"{spec.lower} archive directory: {detail}"
                    )
                if primary_error is None and not committed:
                    raise error(
                        f"Failed to remove temporary {spec.lower} archive directory: "
                        f"{cleanup_exc}"
                    ) from cleanup_exc
                # Do not raise from cleanup: the primary installation error
                # (if any) is already propagating, and after commit the install
                # has succeeded. The warning above reports the residual path.
    except cli.typer.Exit:
        raise
    except error:
        raise
    except Exception as exc:
        raise error(f"Failed to install {spec.lower} from URL: {exc}") from exc
    finally:
        _cleanup_download_tmp_path(tmp_path, spec)

    return entry
