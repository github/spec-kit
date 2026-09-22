"""Command handler for ``specify workflow add``."""

from __future__ import annotations

from . import _commands as cli


def _cleanup_download_tmp_path(tmp_path: cli.Path | None) -> None:
    """Best-effort unlink of a partially-downloaded workflow temp file.

    A cleanup ``OSError`` here must never replace/mask whatever error or
    interrupt is already propagating -- warn about it and keep going.
    """
    if tmp_path is None:
        return
    try:
        tmp_path.unlink(missing_ok=True)
    except OSError as cleanup_exc:
        cli.console.print(
            "[yellow]Warning:[/yellow] Could not remove temporary "
            f"workflow download file: {cli._escape_markup(str(cleanup_exc))} "
            f"(path: {cli._escape_markup(str(tmp_path))})"
        )


def _workflow_package_has_companions(package_dir: cli.Path) -> bool:
    """Return whether a directory contains anything beyond workflow.yml."""
    return any(path.name != "workflow.yml" for path in package_dir.iterdir())


@cli.workflow_app.command("add")
def workflow_add(
    source: str = cli.typer.Argument(..., help="Workflow ID, URL, or local path"),
    dev: bool = cli.typer.Option(
        False, "--dev", help="Install from a local workflow YAML file or directory"
    ),
    from_url: str | None = cli.typer.Option(
        None, "--from", help="Install from a custom URL"
    ),
):
    """Install a workflow from catalog, URL, or local path."""
    from . import load_custom_steps
    from .engine import WorkflowDefinition

    project_root = cli._require_specify_project()
    load_custom_steps(project_root)
    cli._open_workflow_registry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"
    # With --from, source names the expected workflow ID: validate it up
    # front so a URL/path/typo fails without a network fetch.
    if from_url is not None and not dev:
        cli._validate_workflow_id_or_exit(source)
    # Reject a symlinked .specify / .specify/workflows before any write so an
    # install can't escape the project root (covers the local, URL, and
    # catalog branches below — all write beneath workflows_dir).
    cli._reject_unsafe_dir(project_root / ".specify", ".specify")
    cli._reject_unsafe_dir(workflows_dir, ".specify/workflows")

    def _validate_and_install_local(
        yaml_path: cli.Path, source_label: str, expected_id: str | None = None
    ) -> None:
        """Validate and install a workflow from a local YAML file."""
        try:
            with yaml_path.open("rb") as source_file:
                source_mode = cli.os.fstat(source_file.fileno()).st_mode & 0o7777
                source_content = source_file.read()
            definition = WorkflowDefinition.from_string(source_content.decode("utf-8"))
        except OSError as exc:
            cli.console.print(
                f"[red]Error:[/red] Failed to read workflow YAML: "
                f"{cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)
        except (UnicodeDecodeError, ValueError, cli.yaml.YAMLError) as exc:
            cli.console.print(
                f"[red]Error:[/red] Invalid workflow YAML: {cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)
        # Non-string ids (e.g. unquoted ``id: 123`` or ``id: 0``) fall through
        # to validate_workflow below, which reports a typed error instead of
        # crashing on ``.strip()`` here. Only None/empty/whitespace-only ids
        # are rejected as missing.
        if (
            definition.id is None
            or definition.id == ""
            or (isinstance(definition.id, str) and not definition.id.strip())
        ):
            cli.console.print(
                "[red]Error:[/red] Workflow definition has an empty or missing 'id'"
            )
            raise cli.typer.Exit(1)

        from .engine import validate_workflow

        errors = validate_workflow(definition)
        if errors:
            cli.console.print("[red]Error:[/red] Workflow validation failed:")
            for err in errors:
                cli.console.print(f"  \u2022 {cli._escape_markup(str(err))}")
            raise cli.typer.Exit(1)

        if expected_id is not None and definition.id != expected_id:
            cli.console.print(
                f"[red]Error:[/red] Workflow ID in YAML ({cli._escape_markup(repr(definition.id))}) "
                f"does not match the requested workflow ID ({cli._escape_markup(repr(expected_id))})."
            )
            raise cli.typer.Exit(1)

        dest_dir = cli._safe_workflow_id_dir(workflows_dir, definition.id)
        dest_file = dest_dir / "workflow.yml"
        existed_before = dest_dir.is_dir()

        try:
            staged_file = cli._stage_workflow_file(dest_dir)
        except OSError as exc:
            cli.console.print(
                f"[red]Error:[/red] Failed to install workflow "
                f"'{cli._escape_markup(definition.id)}': {cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)

        try:
            # Write the exact bytes parsed above so a concurrent source edit
            # cannot desynchronize installed content from validated metadata.
            staged_file.write_bytes(source_content)
            staged_file.set_mode(source_mode)
        except OSError as exc:
            cli._safe_discard_staged_workflow_file(
                staged_file, dest_dir, existed_before
            )
            cli.console.print(
                f"[red]Error:[/red] Failed to install workflow "
                f"'{cli._escape_markup(definition.id)}': {cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)

        try:
            transaction = cli._workflow_install_transaction(project_root)
            with transaction:
                transaction_existed_before = existed_before or dest_file.exists()
                transaction_registry = cli._open_workflow_registry(project_root)
                # Commit the staged copy onto dest_file via an atomic swap. A
                # prior file is renamed aside so registry failure can restore it.
                try:
                    backup_file = cli._commit_workflow_file(
                        staged_file, dest_file, transaction_existed_before
                    )
                except OSError as exc:
                    cli._safe_discard_staged_workflow_file(
                        staged_file, dest_dir, existed_before
                    )
                    cli.console.print(
                        f"[red]Error:[/red] Failed to install workflow "
                        f"'{cli._escape_markup(definition.id)}': "
                        f"{cli._escape_markup(str(exc))}"
                    )
                    raise cli.typer.Exit(1)
                try:
                    entry = {
                        "name": definition.name,
                        "version": definition.version,
                        "description": definition.description,
                        "source": source_label,
                    }
                    existing = transaction_registry.get(definition.id)
                    if isinstance(existing, dict) and not existing.get("enabled", True):
                        entry["enabled"] = False
                    transaction_registry.add(definition.id, entry)
                except (OSError, TypeError, ValueError) as exc:
                    cli._safe_rollback_committed_workflow_file(
                        dest_file,
                        dest_dir,
                        transaction_existed_before,
                        backup_file,
                    )
                    cli.console.print(
                        f"[red]Error:[/red] Failed to update workflow registry for "
                        f"'{cli._escape_markup(definition.id)}': "
                        f"{cli._escape_markup(str(exc))}"
                    )
                    raise cli.typer.Exit(1)
                # Registry update succeeded while the transaction lock is held.
                cli._discard_committed_backup_file(backup_file)
        except cli.typer.Exit:
            cli._safe_discard_staged_workflow_file(
                staged_file, dest_dir, existed_before
            )
            raise
        except OSError as exc:
            cli._safe_discard_staged_workflow_file(
                staged_file, dest_dir, existed_before
            )
            cli.console.print(
                f"[red]Error:[/red] Failed to lock workflow install "
                f"'{cli._escape_markup(definition.id)}': {cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)
        cli.console.print(
            f"[green]✓[/green] Workflow '{cli._escape_markup(definition.name)}' "
            f"({cli._escape_markup(definition.id)}) installed"
        )

    # Explicit local install (mirrors `extension add --dev`). --dev takes
    # precedence over --from so a URL that would be ignored is never fetched.
    if dev:
        dev_path = cli.Path(source).expanduser()
        if dev_path.is_file() and dev_path.suffix.lower() in (".yml", ".yaml"):
            _validate_and_install_local(dev_path, str(dev_path))
            return
        if (
            dev_path.is_file()
            and cli.archive_format_from_name(str(dev_path)) is not None
        ):
            import tempfile

            with tempfile.TemporaryDirectory(
                prefix="speckit-workflow-archive-"
            ) as tmpdir:
                extracted_root = cli.Path(tmpdir)
                try:
                    cli.safe_extract_archive(dev_path, extracted_root)
                    package_root = cli._workflow_package_root(extracted_root)
                except ValueError as exc:
                    cli.console.print(
                        f"[red]Error:[/red] Invalid workflow archive: "
                        f"{cli._escape_markup(str(exc))}"
                    )
                    raise cli.typer.Exit(1)
                cli._install_workflow_package(
                    project_root,
                    workflows_dir,
                    package_root,
                    str(dev_path),
                )
            return
        if dev_path.is_dir():
            dev_wf_file = dev_path / "workflow.yml"
            if not dev_wf_file.is_file():
                cli.console.print(
                    f"[red]Error:[/red] No workflow.yml found in {cli._escape_markup(source)}"
                )
                raise cli.typer.Exit(1)
            if _workflow_package_has_companions(dev_path):
                cli._install_workflow_package(
                    project_root,
                    workflows_dir,
                    dev_path,
                    str(dev_path),
                )
            else:
                _validate_and_install_local(dev_wf_file, str(dev_path))
            return
        cli.console.print(
            "[red]Error:[/red] --dev source must be a workflow YAML file, "
            "supported archive, or directory containing workflow.yml: "
            f"{cli._escape_markup(source)}"
        )
        raise cli.typer.Exit(1)

    # Try as URL (http/https) — either the positional source is a URL, or an
    # explicit --from URL names where to fetch it (mirrors `extension add --from`).
    download_url = (
        from_url
        if from_url is not None
        else (source if source.startswith(("http://", "https://")) else None)
    )
    if download_url is not None:
        from urllib.parse import urlparse
        from specify_cli.authentication.http import open_url as _open_url

        try:
            urlparse(download_url).port
        except ValueError:
            cli.console.print(
                f"[red]Error:[/red] Invalid URL: {cli._escape_markup(download_url)}"
            )
            raise cli.typer.Exit(1)
        if not cli.is_https_or_localhost_http(download_url):
            cli.console.print(
                "[red]Error:[/red] Only HTTPS URLs are allowed, except HTTP for localhost."
            )
            raise cli.typer.Exit(1)

        if from_url is not None:
            from rich.panel import Panel

            safe_url = cli._escape_markup(from_url)
            cli.console.print()
            cli.console.print(
                Panel(
                    "[bold]You are installing a workflow from an external URL "
                    "that is not\nlisted in any of your configured workflow "
                    "catalogs.[/bold]\n\n"
                    f"URL: {safe_url}\n\n"
                    "Only install workflows from sources you trust.",
                    title="[bold yellow]⚠ Untrusted Source[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )
            cli.console.print()
            if not cli.typer.confirm("Continue with installation?", default=False):
                cli.console.print("Cancelled")
                raise cli.typer.Exit(0)

        from specify_cli.authentication.github_http import (
            resolve_github_release_asset_api_url as _resolve_gh_asset,
        )
        from specify_cli.authentication.http import (
            github_provider_hosts as _github_provider_hosts,
        )

        _wf_url_extra_headers = None
        _resolved_wf_url = _resolve_gh_asset(
            download_url,
            _open_url,
            timeout=30,
            github_hosts=_github_provider_hosts(),
            redirect_validator=cli._reject_insecure_download_redirect,
        )
        if _resolved_wf_url:
            download_url = _resolved_wf_url
            _wf_url_extra_headers = {"Accept": "application/octet-stream"}

        import tempfile

        tmp_path: cli.Path | None = None
        downloaded_archive_format = None
        try:
            with _open_url(
                download_url,
                timeout=30,
                extra_headers=_wf_url_extra_headers,
                redirect_validator=cli._reject_insecure_download_redirect,
            ) as resp:
                final_url = resp.geturl()
                if not cli.is_https_or_localhost_http(final_url):
                    cli.console.print(
                        f"[red]Error:[/red] URL redirected to non-HTTPS: {cli._escape_markup(final_url)}"
                    )
                    raise cli.typer.Exit(1)
                content_type = (
                    resp.getheader("Content-Type")
                    if hasattr(resp, "getheader")
                    else None
                )
                downloaded_archive_format = (
                    cli.archive_format_from_name(final_url)
                    or cli.archive_format_from_name(download_url)
                    or cli.archive_format_from_content_type(content_type)
                )
                declared_yaml = cli._workflow_yaml_is_declared(final_url, content_type)
                suffix = (
                    cli.archive_suffix(downloaded_archive_format)
                    if downloaded_archive_format is not None
                    else ".yml"
                    if declared_yaml
                    else ".download"
                )
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    # Assign tmp_path immediately: NamedTemporaryFile(delete=False)
                    # creates the file on disk right away, before any bytes are
                    # written, so a failure in the size-limited read below must
                    # still be able to find and remove it.
                    tmp_path = cli.Path(tmp.name)
                    if downloaded_archive_format is not None:
                        downloaded_content = cli.read_response_limited(
                            resp,
                            error_type=ValueError,
                            label="workflow archive download",
                        )
                    elif declared_yaml:
                        downloaded_content = cli._read_response_within_limit(resp)
                    else:
                        downloaded_content = cli.read_response_limited(
                            resp,
                            error_type=ValueError,
                            label="workflow download",
                        )
                        downloaded_archive_format = cli._sniff_workflow_archive_format(
                            downloaded_content
                        )
                        if downloaded_archive_format is None:
                            cli._enforce_workflow_yaml_size(downloaded_content)
                    tmp.write(downloaded_content)
        except cli.typer.Exit:
            _cleanup_download_tmp_path(tmp_path)
            raise
        except Exception as exc:
            # A cleanup failure here must never replace/mask the
            # original download error below with a raw, unhandled
            # OSError -- warn about it and keep going, exactly like the
            # later post-install finally cleanup does.
            _cleanup_download_tmp_path(tmp_path)
            cli.console.print(
                f"[red]Error:[/red] Failed to download workflow: {cli._escape_markup(str(exc))}"
            )
            raise cli.typer.Exit(1)
        except BaseException:
            # Covers KeyboardInterrupt and other non-Exception exits: the
            # temp file is already created on disk (delete=False) by this
            # point, so an interrupt during the size-limited read must still
            # unlink it rather than leaking it to the system temp directory.
            _cleanup_download_tmp_path(tmp_path)
            raise
        try:
            if downloaded_archive_format is None:
                _validate_and_install_local(
                    tmp_path,
                    download_url,
                    expected_id=source if from_url else None,
                )
            else:
                with tempfile.TemporaryDirectory(
                    prefix="speckit-workflow-archive-"
                ) as extract_dir:
                    extracted_root = cli.Path(extract_dir)
                    try:
                        cli.safe_extract_archive(
                            tmp_path,
                            extracted_root,
                            source_name=final_url,
                            content_type=content_type,
                        )
                        package_root = cli._workflow_package_root(extracted_root)
                    except ValueError as exc:
                        cli.console.print(
                            f"[red]Error:[/red] Invalid workflow archive: "
                            f"{cli._escape_markup(str(exc))}"
                        )
                        raise cli.typer.Exit(1)
                    cli._install_workflow_package(
                        project_root,
                        workflows_dir,
                        package_root,
                        download_url,
                        expected_id=source if from_url else None,
                    )
        finally:
            # Best-effort: _validate_and_install_local may already have
            # committed the file + registry entry (success) or already
            # raised its own clean typer.Exit (failure) by this point --
            # either way, a cleanup OSError here must never mask that
            # outcome or surface as its own unhandled failure. Warn instead,
            # same as the committed-backup cleanup above.
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError as exc:
                cli.console.print(
                    "[yellow]Warning:[/yellow] Could not remove temporary "
                    f"workflow download file: {cli._escape_markup(str(exc))} "
                    f"(path: {cli._escape_markup(str(tmp_path))})"
                )
        return

    # Try as a local file/directory
    source_path = cli.Path(source)
    if source_path.exists():
        if source_path.is_file() and source_path.suffix.lower() in (".yml", ".yaml"):
            _validate_and_install_local(source_path, str(source_path))
            return
        elif (
            source_path.is_file()
            and cli.archive_format_from_name(str(source_path)) is not None
        ):
            import tempfile

            with tempfile.TemporaryDirectory(
                prefix="speckit-workflow-archive-"
            ) as tmpdir:
                extracted_root = cli.Path(tmpdir)
                try:
                    cli.safe_extract_archive(source_path, extracted_root)
                    package_root = cli._workflow_package_root(extracted_root)
                except ValueError as exc:
                    cli.console.print(
                        f"[red]Error:[/red] Invalid workflow archive: "
                        f"{cli._escape_markup(str(exc))}"
                    )
                    raise cli.typer.Exit(1)
                cli._install_workflow_package(
                    project_root,
                    workflows_dir,
                    package_root,
                    str(source_path),
                )
            return
        elif source_path.is_dir():
            wf_file = source_path / "workflow.yml"
            if not wf_file.is_file():
                cli.console.print(
                    f"[red]Error:[/red] No workflow.yml found in {cli._escape_markup(source)}"
                )
                raise cli.typer.Exit(1)
            if _workflow_package_has_companions(source_path):
                cli._install_workflow_package(
                    project_root,
                    workflows_dir,
                    source_path,
                    str(source_path),
                )
            else:
                _validate_and_install_local(wf_file, str(source_path))
            return

    # Try from catalog
    cli._install_workflow_from_catalog(project_root, workflows_dir, source)
