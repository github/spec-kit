"""Command handler for ``specify workflow step add``."""

from __future__ import annotations

from .. import _commands as cli
from . import step_app

from . import _helpers as step_helpers


@step_app.command("add")
def workflow_step_add(
    step_id: str = cli.typer.Argument(..., help="Step type ID from catalog"),
):
    """Install a custom step type from the step catalog."""
    from .catalog import (
        StepCatalog,
        StepCatalogError,
        StepRegistry,
        StepValidationError,
    )

    project_root = cli._require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    if not info:
        cli.console.print(
            f"[red]Error:[/red] Step type '{step_id}' not found in catalog"
        )
        raise cli.typer.Exit(1)

    if not info.get("_install_allowed", True):
        cli.console.print(
            f"[yellow]Warning:[/yellow] Step type '{step_id}' is from a discovery-only catalog"
        )
        cli.console.print("Direct installation is not enabled for this catalog source.")
        raise cli.typer.Exit(1)

    # Reject step IDs that collide with built-in step types
    from .. import STEP_REGISTRY as _step_reg

    if step_id in _step_reg:
        cli.console.print(
            f"[red]Error:[/red] Step type '{step_id}' conflicts with a built-in step type"
        )
        raise cli.typer.Exit(1)

    # Reject if already installed
    registry = StepRegistry(project_root)
    if registry.is_installed(step_id):
        cli.console.print(
            f"[red]Error:[/red] Step type '{step_id}' is already installed. "
            "Remove it first with: [cyan]specify workflow step remove "
            f"{step_id}[/cyan]"
        )
        raise cli.typer.Exit(1)

    declared_step_yml_url = info.get("step_yml_url")
    if declared_step_yml_url is not None and not isinstance(declared_step_yml_url, str):
        cli.console.print(
            f"[red]Error:[/red] Catalog entry for '{step_id}' has a malformed "
            "step.yml URL; expected a non-empty string"
        )
        raise cli.typer.Exit(1)
    step_yml_url = declared_step_yml_url or info.get("url")
    if step_yml_url is None or (
        isinstance(step_yml_url, str) and not step_yml_url.strip()
    ):
        cli.console.print(f"[red]Error:[/red] Catalog entry for '{step_id}' has no URL")
        raise cli.typer.Exit(1)
    if not isinstance(step_yml_url, str):
        cli.console.print(
            f"[red]Error:[/red] Catalog entry for '{step_id}' has a malformed "
            "step.yml URL; expected a non-empty string"
        )
        raise cli.typer.Exit(1)

    # Derive __init__.py URL: replace trailing step.yml with __init__.py
    # or use explicit init_url if provided.
    init_url = info.get("init_url")
    if init_url is not None and (not isinstance(init_url, str) or not init_url.strip()):
        cli.console.print(
            f"[red]Error:[/red] Catalog entry for '{step_id}' has a malformed "
            "__init__.py URL; expected a non-empty string"
        )
        raise cli.typer.Exit(1)
    if not init_url:
        if step_yml_url.endswith("step.yml"):
            init_url = step_yml_url[: -len("step.yml")] + "__init__.py"
        else:
            cli.console.print(
                f"[red]Error:[/red] Cannot derive __init__.py URL from '{step_yml_url}'. "
                "Catalog entry should provide 'init_url' or a 'url' ending in 'step.yml'."
            )
            raise cli.typer.Exit(1)

    # Preflight the declared file count before creating a staging directory or
    # issuing any request. The two required files are always part of the package;
    # duplicate declarations for them in extra_files are ignored below and do
    # not count twice.
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
    if package_file_count > step_helpers._MAX_STEP_PACKAGE_FILES:
        cli.console.print(
            f"[red]Error:[/red] Step package declares {package_file_count} files, "
            f"exceeding the {step_helpers._MAX_STEP_PACKAGE_FILES}-file limit"
        )
        raise cli.typer.Exit(1)

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
            return cli._read_response_within_limit(resp)

    step_helpers._validate_step_id_or_exit(step_id)

    steps_base_dir = step_helpers._resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: ensure the resolved directory is a direct child of
    # steps_base_dir even after symlink resolution.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        cli.console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise cli.typer.Exit(1)
    if rel_parts != (step_id,):
        cli.console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise cli.typer.Exit(1)

    import shutil
    import tempfile

    # Refuse if step_dir already exists (e.g. leftover from a previous failed/manual
    # install that wasn't registered). The user should remove it before retrying.
    if step_dir.exists():
        cli.console.print(
            f"[red]Error:[/red] Step directory already exists at '{step_dir}'. "
            f"Remove it manually or use: [cyan]specify workflow step remove {step_id}[/cyan]"
        )
        raise cli.typer.Exit(1)

    # Create steps_base_dir now so the staging temp dir is on the same filesystem,
    # enabling a truly atomic os.rename() below.
    try:
        steps_base_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = cli.Path(
            tempfile.mkdtemp(prefix="speckit_step_tmp_", dir=steps_base_dir)
        )
    except OSError as exc:
        cli.console.print(
            f"[red]Error:[/red] Failed to create staging directory: {exc}"
        )
        raise cli.typer.Exit(1)
    try:
        try:
            step_yml_content = _safe_fetch(step_yml_url)
            init_py_content = _safe_fetch(init_url)
        except Exception as exc:
            cli.console.print(f"[red]Error:[/red] Failed to download step files: {exc}")
            raise cli.typer.Exit(1)

        package_bytes = len(step_yml_content) + len(init_py_content)
        if package_bytes > step_helpers._MAX_STEP_PACKAGE_BYTES:
            cli.console.print(
                f"[red]Error:[/red] Step package exceeds the "
                f"{step_helpers._MAX_STEP_PACKAGE_BYTES}-byte total size limit"
            )
            raise cli.typer.Exit(1)

        # Validate step.yml
        try:
            import yaml as _yaml

            step_yml_text = step_yml_content.decode("utf-8")
            # ``safe_load`` returns None for BOTH an empty document and an
            # explicit null scalar (``null``, ``~``, ``NULL``), so it cannot
            # tell them apart on its own. ``compose`` yields no node only for
            # a genuinely empty document.
            node = _yaml.compose(step_yml_text)
            meta = _yaml.safe_load(step_yml_text)
            is_empty_document = node is None or (
                meta is None
                and isinstance(node, _yaml.nodes.ScalarNode)
                and node.value == ""
                and node.start_mark.index == node.end_mark.index
            )
        except Exception as exc:
            cli.console.print(f"[red]Error:[/red] Invalid step.yml: {exc}")
            raise cli.typer.Exit(1)

        # Do NOT coerce with ``or {}`` here: that also turns a FALSY non-mapping
        # (top-level ``[]``, ``false``, ``0``, ``''``, or an explicit ``null``)
        # into ``{}`` and silently bypasses this shape check, surfacing the
        # unrelated "missing 'step.type_key'" error below instead of the real
        # problem. Only a genuinely empty document defaults to ``{}``.
        if meta is None and is_empty_document:
            meta = {}
        elif not isinstance(meta, dict):
            cli.console.print("[red]Error:[/red] step.yml must be a YAML mapping")
            raise cli.typer.Exit(1)

        step_meta = meta.get("step", {})
        if not isinstance(step_meta, dict):
            cli.console.print(
                "[red]Error:[/red] step.yml 'step' field must be a mapping"
            )
            raise cli.typer.Exit(1)
        type_key = step_meta.get("type_key", "")
        if not type_key:
            cli.console.print(
                "[red]Error:[/red] step.yml missing 'step.type_key' field"
            )
            raise cli.typer.Exit(1)

        if type_key != step_id:
            cli.console.print(
                f"[red]Error:[/red] step.yml type_key ({type_key!r}) does not match "
                f"catalog ID ({step_id!r})"
            )
            raise cli.typer.Exit(1)

        # Write the two required files.
        try:
            (tmp_path / "step.yml").write_bytes(step_yml_content)
            (tmp_path / "__init__.py").write_bytes(init_py_content)
        except OSError as exc:
            cli.console.print(
                f"[red]Error:[/red] Failed to write step files to staging directory: {exc}"
            )
            raise cli.typer.Exit(1)

        # Optionally download additional package files declared in the catalog entry
        # (e.g. helper modules). Each entry in ``extra_files`` is a mapping of
        # relative-path → URL. step.yml and __init__.py are ignored here (already
        # written). Paths are validated to stay within the step package directory to
        # prevent path-traversal attacks.
        for rel_path, file_url in (extra_files or {}).items():
            if not isinstance(rel_path, str) or not rel_path.strip():
                cli.console.print(
                    "[red]Error:[/red] Catalog entry 'extra_files' contains an "
                    "empty or non-string path key"
                )
                raise cli.typer.Exit(1)
            if _is_required_package_file(rel_path):
                continue  # already written above
            # Reject dot-path segments ('', '.', '..') that would refer to the
            # package directory itself (IsADirectoryError) or escape it.
            rel_parts = cli.Path(rel_path).parts
            if not rel_parts or any(seg in ("", ".", "..") for seg in rel_parts):
                cli.console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is not a "
                    "valid relative file path"
                )
                raise cli.typer.Exit(1)
            if not isinstance(file_url, str) or not file_url.strip():
                cli.console.print(
                    f"[red]Error:[/red] extra_files entry '{rel_path}' has an "
                    "empty or non-string URL"
                )
                raise cli.typer.Exit(1)
            # Resolve both destination and base to handle any symlinks in tmp_path itself,
            # ensuring the traversal check is robust even on non-canonical paths.
            resolved_base = tmp_path.resolve()
            dest = (tmp_path / rel_path).resolve()
            try:
                dest.relative_to(resolved_base)
            except ValueError:
                cli.console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is outside "
                    "the step package directory"
                )
                raise cli.typer.Exit(1)
            try:
                file_content = _safe_fetch(file_url)
            except Exception as exc:
                cli.console.print(
                    f"[red]Error:[/red] Failed to download extra file '{rel_path}': {exc}"
                )
                raise cli.typer.Exit(1)
            package_bytes += len(file_content)
            if package_bytes > step_helpers._MAX_STEP_PACKAGE_BYTES:
                cli.console.print(
                    f"[red]Error:[/red] Step package exceeds the "
                    f"{step_helpers._MAX_STEP_PACKAGE_BYTES}-byte total size limit"
                )
                raise cli.typer.Exit(1)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file_content)
            except OSError as exc:
                cli.console.print(
                    f"[red]Error:[/red] Failed to write extra file '{rel_path}': {exc}"
                )
                raise cli.typer.Exit(1)

        # Atomically rename the staging directory to the final location.
        # Both paths are under steps_base_dir (same filesystem), so os.rename()
        # is atomic on POSIX and won't leave a partially-written directory at
        # step_dir on failure.
        try:
            cli.os.rename(tmp_path, step_dir)
        except OSError as exc:
            cli.console.print(
                f"[red]Error:[/red] Failed to install step '{step_id}': {exc}"
            )
            raise cli.typer.Exit(1)
    finally:
        # Clean up if the rename hasn't moved tmp_path yet (i.e. on any failure).
        shutil.rmtree(tmp_path, ignore_errors=True)

    step_name = info.get("name") or step_id
    step_version = info.get("version") or step_meta.get("version") or "0.0.0"

    # Register in step registry
    registry = StepRegistry(project_root)
    try:
        registry.add(
            step_id,
            {
                "name": step_name,
                "version": step_version,
                "description": info.get(
                    "description", step_meta.get("description", "")
                ),
                "author": info.get("author", step_meta.get("author", "")),
                "source": "catalog",
                "catalog_name": info.get("_catalog_name", ""),
                "type_key": type_key,
            },
        )
    except StepValidationError as exc:
        # Roll back the just-installed directory so the system isn't left with
        # an unregistered step package on disk after a registry write failure
        # (e.g. read-only filesystem, permission denied).
        shutil.rmtree(step_dir, ignore_errors=True)
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    cli.console.print(f"[green]✓[/green] Step type '{step_name}' ({step_id}) installed")
    cli.console.print(
        "  Use [cyan]specify workflow step list[/cyan] to verify the installation."
    )
