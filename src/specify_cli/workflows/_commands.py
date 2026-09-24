"""Shared infrastructure and registration for ``specify workflow`` commands.

Decorated handlers live in command modules matching the CLI surface. Thin
forwarders preserve established direct-import and monkeypatch boundaries.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath as PurePosixPath
from typing import Any

import typer
import yaml
from rich.markup import escape as _escape_markup

from .._console import console, err_console
from .._download_security import (
    archive_format_from_content_type,
    archive_format_from_name,
    archive_suffix as archive_suffix,
    detect_archive_format,
    is_https_or_localhost_http,
    is_safe_download_redirect,
    read_response_limited,
    safe_extract_archive,
)
from .._project import _resolve_init_dir_override as _resolve_init_dir_override
from ..shared_infra import verify_archive_sha256

workflow_app = typer.Typer(
    name="workflow",
    help="Manage and run automation workflows",
    add_completion=False,
)


def _error_console(json_output: bool):
    """Console for error text: stderr under ``--json`` so the JSON stdout
    stream stays parseable, the normal console otherwise. Mirrors the
    stderr-only error routing already used by ``specify bundle``.
    """
    return err_console if json_output else console


def _open_workflow_registry(project_root: Path, out=None):
    """Construct a WorkflowRegistry, exiting cleanly on an unreadable file.

    WorkflowRegistry fails closed (raises OSError) at construction when its
    file can't be read, rather than falling back to an empty registry a
    caller could mistake for "nothing installed". Every CLI command that
    opens a registry needs this same clean-error boundary.
    """
    from .catalog import WorkflowRegistry

    try:
        return WorkflowRegistry(project_root)
    except OSError as exc:
        (out or console).print(
            f"[red]Error:[/red] Failed to read workflow registry: {_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)


def _require_enabled_workflow(
    registry_root: Path, workflow_id: str, out: Any
) -> bool:
    """Fail closed for corrupted or explicitly disabled registry entries."""
    metadata = _open_workflow_registry(registry_root, out).get(workflow_id)
    if metadata is not None and not isinstance(metadata, dict):
        out.print(
            f"[red]Error:[/red] Registry entry for "
            f"'{_escape_markup(workflow_id)}' is corrupted"
        )
        raise typer.Exit(1)
    if isinstance(metadata, dict) and not metadata.get("enabled", True):
        out.print(
            f"[red]Error:[/red] Workflow '{_escape_markup(workflow_id)}' is disabled. "
            f"Enable with: specify workflow enable {_escape_markup(workflow_id)}"
        )
        raise typer.Exit(1)
    return metadata is not None


def _resolve_run_owner_root(
    installed_registry_root: str | None, project_root: Path
) -> Path:
    """Forward to the resume-private owner-state resolver."""
    from ._command_resume_state import _resolve_run_owner_root as resolver

    return resolver(installed_registry_root, project_root)


def _parse_input_values(
    input_values: list[str] | None, *, json_output: bool = False
) -> dict[str, Any]:
    """Parse repeated ``key=value`` CLI inputs into a dict.

    Shared by ``workflow run`` and ``workflow resume``. Exits with an error
    on any entry missing ``=``.
    """
    inputs: dict[str, Any] = {}
    for kv in input_values or []:
        if "=" not in kv:
            _error_console(json_output).print(
                f"[red]Error:[/red] Invalid input format: {kv!r} (expected key=value)"
            )
            raise typer.Exit(1)
        key, _, value = kv.partition("=")
        inputs[key.strip()] = value.strip()
    return inputs


def _reject_unsafe_dir(path: Path, label: str) -> None:
    """Refuse to proceed when *path* is a symlink or an existing non-directory.

    A symlinked ``.specify`` (or ``.specify/workflows``) could redirect
    workflow writes outside the project root, so any command that creates or
    writes files beneath it must bail first. Absence is tolerated — the caller
    creates the directory — only an existing-but-wrong target is rejected.
    """
    if path.is_symlink():
        err_console.print(f"[red]Error:[/red] Refusing to use symlinked {label} path")
        raise typer.Exit(1)
    if path.exists() and not path.is_dir():
        err_console.print(f"[red]Error:[/red] {label} path exists but is not a directory")
        raise typer.Exit(1)


def _reject_unsafe_workflow_storage(project_root: Path) -> None:
    """Refuse symlinked workflow storage directories before workflow commands run."""
    _reject_unsafe_dir(project_root / ".specify", ".specify")
    _reject_unsafe_dir(project_root / ".specify" / "workflows", ".specify/workflows")
    _reject_unsafe_dir(
        project_root / ".specify" / "workflows" / "runs",
        ".specify/workflows/runs",
    )
    _reject_unsafe_dir(
        project_root / ".specify" / "workflows" / "overlays",
        ".specify/workflows/overlays",
    )


def _resolve_installed_workflow_ownership(
    source_path: Path, err
) -> tuple[Path | None, str | None]:
    """Forward to the run-private installed-workflow ownership resolver."""
    from ._command_run_ownership import (
        _resolve_installed_workflow_ownership as resolver,
    )
    return resolver(source_path, err)


_WORKFLOW_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_RESERVED_WORKFLOW_IDS: frozenset[str] = frozenset({"overlays", "runs", "steps"})


def _reject_insecure_download_redirect(old_url: str, new_url: str) -> None:
    """Reject insecure redirects before they are followed."""
    import urllib.error

    if is_safe_download_redirect(old_url, new_url):
        return
    raise urllib.error.URLError(
        "redirect target must use HTTPS without entering a local target; "
        "loopback HTTP may only redirect from another loopback URL"
    )


# Workflow YAML definitions are small step/metadata text, not binaries, so
# this is generous headroom against a malicious or misbehaving server -- not
# a ceiling any legitimate workflow definition should ever approach.
_MAX_WORKFLOW_YAML_BYTES = 5 * 1024 * 1024  # 5 MiB
_DOWNLOAD_CHUNK_SIZE = 65536


def _read_response_within_limit(response, max_bytes: int | None = None) -> bytes:
    """Read *response* fully, enforcing *max_bytes* via bounded streaming.

    A ``Content-Length`` header is checked up front to fail fast, but it is
    never trusted alone: the actual bytes read are also counted as they
    stream in, so a chunked or ``Content-Length``-less response that lies
    about (or omits) its size still cannot exceed the limit.

    ``max_bytes`` defaults to ``None`` (resolved to the module-level
    ``_MAX_WORKFLOW_YAML_BYTES`` at call time, not at function-definition
    time) so tests can override the effective limit via monkeypatching the
    module attribute.
    """
    if max_bytes is None:
        max_bytes = _MAX_WORKFLOW_YAML_BYTES
    content_length = None
    getheader = getattr(response, "getheader", None)
    if callable(getheader):
        try:
            raw_length = getheader("Content-Length")
        except Exception:
            raw_length = None
        if raw_length is not None:
            try:
                content_length = int(raw_length)
            except (TypeError, ValueError):
                content_length = None
    if content_length is not None and content_length > max_bytes:
        raise ValueError(
            f"response declared {content_length} bytes, exceeding the "
            f"{max_bytes}-byte workflow size limit"
        )

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(_DOWNLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"response exceeds the {max_bytes}-byte workflow size limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _workflow_yaml_is_declared(
    source_name: str, content_type: str | None
) -> bool:
    """Return whether response metadata explicitly identifies workflow YAML."""
    from urllib.parse import urlparse

    path = urlparse(source_name).path.casefold()
    media_type = (content_type or "").split(";", 1)[0].strip().casefold()
    return path.endswith((".yml", ".yaml")) or media_type in {
        "application/yaml",
        "application/x-yaml",
        "text/yaml",
        "text/x-yaml",
    }


def _sniff_workflow_archive_format(data: bytes):
    """Return a supported archive format when suffixless response bytes match."""
    from io import BytesIO

    try:
        return detect_archive_format(
            Path("workflow-download"),
            archive_file=BytesIO(data),
        )
    except ValueError:
        return None


def _enforce_workflow_yaml_size(data: bytes) -> None:
    if len(data) > _MAX_WORKFLOW_YAML_BYTES:
        raise ValueError(
            f"response exceeds the {_MAX_WORKFLOW_YAML_BYTES}-byte workflow size limit"
        )


def _validate_workflow_id_or_exit(workflow_id: str) -> None:
    """Validate that ``workflow_id`` is a safe installed-workflow directory name."""
    if (
        workflow_id in _RESERVED_WORKFLOW_IDS
        or not _WORKFLOW_ID_PATTERN.fullmatch(workflow_id)
    ):
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)


def _safe_workflow_id_dir(workflows_dir: Path, workflow_id: str) -> Path:
    """Validate the per-id install directory before any write and return it.

    Installs write to ``workflows_dir / <id> / workflow.yml``. The ``<id>``
    segment comes from a workflow YAML or catalog key, so it must be checked
    before ``mkdir``/copy/download follows a symlink outside the project root.
    Rejects, with a clean ``typer.Exit``:

    - an ``<id>`` that is a symlink or an existing non-directory
      (the latter would otherwise make ``mkdir`` raise);
    - an ``<id>`` that is not a single workflow-id path segment or collides
      with internal workflow storage directories;
    - an ``<id>`` that escapes ``workflows_dir`` (path traversal);
    - an ``<id>/workflow.yml`` leaf that is a symlink or an existing
      non-file (either would otherwise make the later write/copy raise).

    The symlink/non-directory check runs *before* ``resolve()`` so a symlinked
    ``<id>`` reports as a symlink rather than misleadingly as path traversal.
    ``workflow_id`` is markup-escaped in output to avoid Rich markup injection.
    """
    safe_id = _escape_markup(workflow_id)
    _validate_workflow_id_or_exit(workflow_id)

    dest_dir = workflows_dir / workflow_id
    _reject_unsafe_dir(dest_dir, f".specify/workflows/{safe_id}")
    try:
        dest_dir.resolve().relative_to(workflows_dir.resolve())
    except ValueError:
        # Escape the repr (not the raw id) so backslashes added by repr cannot
        # re-expose markup brackets to Rich.
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)
    workflow_yml = dest_dir / "workflow.yml"
    if workflow_yml.is_symlink():
        console.print(
            "[red]Error:[/red] Refusing to write through symlinked "
            f".specify/workflows/{safe_id}/workflow.yml"
        )
        raise typer.Exit(1)
    if workflow_yml.exists() and not workflow_yml.is_file():
        console.print(
            "[red]Error:[/red] "
            f".specify/workflows/{safe_id}/workflow.yml exists but is not a file"
        )
        raise typer.Exit(1)
    return dest_dir


class _StagedWorkflowFile:
    """Exclusive staging inode kept open until its atomic commit."""

    def __init__(self, path: Path, fd: int) -> None:
        self.path = path
        self.fd = fd

    def _write(self, chunks) -> None:
        os.lseek(self.fd, 0, os.SEEK_SET)
        os.ftruncate(self.fd, 0)
        for chunk in chunks:
            view = memoryview(chunk)
            while view:
                written = os.write(self.fd, view)
                if written <= 0:
                    raise OSError("Failed to write staged workflow file")
                view = view[written:]

    def write_bytes(self, data: bytes) -> None:
        self._write((data,))

    def verify_path(self) -> None:
        import stat

        try:
            path_stat = self.path.stat(follow_symlinks=False)
            open_stat = os.fstat(self.fd)
        except OSError as exc:
            raise OSError(
                "Staged workflow file changed before commit"
            ) from exc
        if (
            not stat.S_ISREG(path_stat.st_mode)
            or path_stat.st_dev != open_stat.st_dev
            or path_stat.st_ino != open_stat.st_ino
        ):
            raise OSError("Staged workflow file changed before commit")

    def set_mode(self, mode: int) -> None:
        if hasattr(os, "fchmod"):
            os.fchmod(self.fd, mode)

    def close(self) -> None:
        if self.fd < 0:
            return
        fd, self.fd = self.fd, -1
        try:
            os.close(fd)
        except OSError:
            pass


def _stage_workflow_file(
    dest_dir: Path, *, use_project_file_mode: bool = False
) -> _StagedWorkflowFile:
    """Reserve a same-directory staging file so new/updated workflow.yml
    content can be written and validated without ever touching (and risking
    truncating) an existing destination file before the final atomic swap.
    Shared by the local-install and catalog-install paths.

    If dest_dir did not already exist, this call creates it; if mkstemp then
    fails (disk full/EMFILE/quota), the freshly-created directory is removed
    again via a guarded rmdir (never a broad rmtree, so any concurrently
    written content is left untouched) before the original OSError is
    re-raised unchanged. A pre-existing dest_dir (reinstall) is never
    touched by this cleanup. For catalog-created files,
    ``use_project_file_mode`` recreates the reserved path exclusively with
    mode 0666 so the process umask supplies the normal project-file mode.
    The final descriptor remains open so callers write to and verify the
    reserved inode rather than reopening a replaceable pathname."""
    import tempfile

    created_dir = not dest_dir.exists()
    dest_dir.mkdir(parents=True, exist_ok=True)
    fd = -1
    staged_file: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=dest_dir, prefix=".workflow.yml.", suffix=".tmp")
        staged_file = Path(tmp_name)
        if use_project_file_mode:
            os.close(fd)
            fd = -1
            staged_file.unlink()
            flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(staged_file, flags, 0o666)
    except OSError:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        if staged_file is not None:
            try:
                staged_file.unlink(missing_ok=True)
            except OSError:
                pass
        if created_dir:
            try:
                dest_dir.rmdir()
            except OSError as cleanup_exc:
                console.print(
                    "[yellow]Warning:[/yellow] Failed to remove incomplete "
                    f"workflow directory: {_escape_markup(str(cleanup_exc))}"
                )
        raise
    assert staged_file is not None
    return _StagedWorkflowFile(staged_file, fd)


@contextlib.contextmanager
def _workflow_install_transaction(project_root: Path):
    """Serialize workflow file swaps with their registry updates."""
    from ..shared_infra import _ensure_safe_shared_directory

    lock_dir = project_root / ".specify"
    try:
        _ensure_safe_shared_directory(
            project_root, lock_dir, context="workflow install lock directory"
        )
    except ValueError as exc:
        raise OSError(str(exc)) from exc
    lock_file = lock_dir / ".workflow-install.lock"
    if lock_file.is_symlink():
        raise OSError(f"Refusing to use symlinked workflow install lock: {lock_file}")

    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(lock_file, flags, 0o600)
    try:
        if lock_file.is_symlink():
            raise OSError(
                f"Refusing to use symlinked workflow install lock: {lock_file}"
            )
        if os.name == "nt":
            import errno
            import msvcrt
            import time

            if os.fstat(fd).st_size == 0:
                os.write(fd, b"\0")
            while True:
                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EDEADLK):
                        raise
                    time.sleep(0.05)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _commit_workflow_file(
    staged_file: Path | _StagedWorkflowFile,
    dest_file: Path,
    existed_before: bool,
) -> Path | None:
    """Atomically swap ``staged_file`` onto ``dest_file``. If a prior file
    existed, it is first renamed to a unique sibling (path returned) so a
    later failure (e.g. registry.add()) can restore it via rename instead
    of a content rewrite -- the destination is never truncated/overwritten
    in place. If the second rename fails after the first succeeded, the
    prior file is put back immediately so dest_file is never left simply
    missing."""
    staged_path = (
        staged_file.path
        if isinstance(staged_file, _StagedWorkflowFile)
        else staged_file
    )
    if isinstance(staged_file, _StagedWorkflowFile):
        staged_file.verify_path()
    if existed_before and dest_file.exists():
        import tempfile

        dest_state = dest_file.stat(follow_symlinks=False)
        mode = dest_state.st_mode & 0o7777
        if isinstance(staged_file, _StagedWorkflowFile):
            staged_file.set_mode(mode)
        else:
            staged_path.chmod(mode)
        fd, backup_name = tempfile.mkstemp(
            dir=dest_file.parent,
            prefix=f".{dest_file.name}.",
            suffix=".bak",
        )
        try:
            placeholder_state = os.fstat(fd)
        finally:
            os.close(fd)
        backup_file = Path(backup_name)
        try:
            os.replace(dest_file, backup_file)
        except BaseException as move_exc:
            backup_state = None
            try:
                backup_state = backup_file.stat(follow_symlinks=False)
            except OSError:
                pass
            if (
                backup_state is not None
                and os.path.samestat(dest_state, backup_state)
            ):
                try:
                    os.replace(backup_file, dest_file)
                except OSError as restore_exc:
                    raise OSError(
                        f"Failed to stage prior workflow ({move_exc}); failed "
                        f"to restore it from {backup_file} ({restore_exc}). "
                        f"The prior workflow remains at {backup_file}."
                    ) from restore_exc
            elif (
                backup_state is not None
                and os.path.samestat(placeholder_state, backup_state)
            ):
                try:
                    backup_file.unlink(missing_ok=True)
                except OSError:
                    pass
            raise
        try:
            if isinstance(staged_file, _StagedWorkflowFile):
                staged_file.verify_path()
                # Windows cannot replace an open file. Verify through the
                # exclusive descriptor, then close immediately before rename.
                staged_file.close()
            os.replace(staged_path, dest_file)
        except BaseException as commit_exc:
            try:
                os.replace(backup_file, dest_file)
            except OSError as restore_exc:
                raise OSError(
                    f"Failed to commit workflow file ({commit_exc}); failed "
                    f"to restore the prior workflow from {backup_file} "
                    f"({restore_exc}). The prior workflow remains at "
                    f"{backup_file}."
                ) from restore_exc
            raise
        return backup_file
    if isinstance(staged_file, _StagedWorkflowFile):
        staged_file.verify_path()
        staged_file.close()
    os.replace(staged_path, dest_file)
    return None


def _discard_staged_workflow_file(
    staged_file: Path | _StagedWorkflowFile,
    dest_dir: Path,
    existed_before: bool,
) -> None:
    """Clean up after a pre-commit failure (staged_file was never swapped
    onto dest_file): remove the staged file, and for a fresh install (no
    prior directory) remove the now-orphaned dest_dir too. A genuine
    removal failure must propagate (not be swallowed) so the safe wrapper
    below can warn instead of silently leaving an orphan; a dest_dir
    already absent is not itself an error."""
    staged_path = (
        staged_file.path
        if isinstance(staged_file, _StagedWorkflowFile)
        else staged_file
    )
    if isinstance(staged_file, _StagedWorkflowFile):
        staged_file.close()
    staged_path.unlink(missing_ok=True)
    if not existed_before and dest_dir.exists():
        import errno

        try:
            dest_dir.rmdir()
        except OSError as exc:
            # Another concurrent install may already have committed content
            # into this once-fresh directory. Never recursively delete it.
            if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                raise


def _rollback_committed_workflow_file(
    dest_file: Path, dest_dir: Path, existed_before: bool, backup_file: Path | None
) -> None:
    """Undo a successful _commit_workflow_file swap after a later failure
    (registry.add()): restore the prior file via rename, remove the newly
    committed file for a reinstall over a pre-existing empty directory
    (no backup), or remove the new file and then its directory when empty
    for a fresh install. A genuine removal failure must propagate (not be
    swallowed) so the safe wrapper below can warn instead of silently
    leaving an orphan; a dest_dir already absent is not itself an error."""
    if backup_file is not None:
        os.replace(backup_file, dest_file)
    else:
        dest_file.unlink(missing_ok=True)
        if not existed_before and dest_dir.exists():
            import errno

            try:
                dest_dir.rmdir()
            except OSError as exc:
                # Another installer may have staged a sibling before taking
                # the transaction lock. Preserve it rather than recursively
                # deleting the shared directory during this rollback.
                if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                    raise


def _safe_discard_staged_workflow_file(
    staged_file: Path | _StagedWorkflowFile,
    dest_dir: Path,
    existed_before: bool,
) -> None:
    """Guarded wrapper: a cleanup failure must be reported, never crash or
    silently mask the original install error that triggered it."""
    try:
        _discard_staged_workflow_file(staged_file, dest_dir, existed_before)
    except OSError as exc:
        console.print(
            "[yellow]Warning:[/yellow] Failed to clean up incomplete workflow "
            f"install: {_escape_markup(str(exc))}"
        )


def _safe_rollback_committed_workflow_file(
    dest_file: Path, dest_dir: Path, existed_before: bool, backup_file: Path | None
) -> None:
    """Guarded wrapper: a rollback failure must be reported, never crash or
    silently claim the prior workflow file was restored when it wasn't."""
    try:
        _rollback_committed_workflow_file(dest_file, dest_dir, existed_before, backup_file)
    except OSError as exc:
        console.print(
            "[yellow]Warning:[/yellow] Failed to restore prior workflow file "
            f"after registry update failure: {_escape_markup(str(exc))}"
        )


def _discard_committed_backup_file(backup_file: Path | None) -> None:
    """Once registry.add()/registry.remove() has durably succeeded after a
    _commit_workflow_file() swap, the renamed-aside prior file is no longer
    needed for rollback -- it must be discarded, not left as a permanent
    orphan sibling that every future reinstall would silently accumulate or
    clobber. A cleanup failure here must not turn an already-successful
    install into a reported failure; it's reported as a warning, consistent
    with workflow_remove's post-commit cleanup semantics. A fresh install
    (backup_file is None) is a no-op."""
    if backup_file is None:
        return
    try:
        backup_file.unlink(missing_ok=True)
    except OSError as exc:
        console.print(
            "[yellow]Warning:[/yellow] Workflow installed, but its backup file "
            f"could not be cleaned up: {_escape_markup(str(exc))}. Remove it "
            f"manually: {_escape_markup(str(backup_file))}"
        )


def _workflow_package_root(extracted_root: Path) -> Path:
    """Resolve a root-level or single-nested workflow package."""
    if (extracted_root / "workflow.yml").is_file():
        return extracted_root
    entries = list(extracted_root.iterdir())
    if (
        len(entries) == 1
        and entries[0].is_dir()
        and not entries[0].is_symlink()
        and (entries[0] / "workflow.yml").is_file()
    ):
        return entries[0]
    raise ValueError(
        "Archive must contain workflow.yml at its root or in exactly one "
        "top-level directory"
    )


def _validate_local_workflow_package(package_dir: Path) -> None:
    """Reject links and special files before copying a local package."""
    import stat

    for root, dirnames, filenames in os.walk(package_dir, followlinks=False):
        root_path = Path(root)
        for name in [*dirnames, *filenames]:
            path = root_path / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"Workflow package contains symlink: {path}")
            if not stat.S_ISDIR(mode) and not stat.S_ISREG(mode):
                raise ValueError(f"Workflow package contains unsupported file: {path}")


def _install_workflow_package(
    project_root: Path,
    workflows_dir: Path,
    package_dir: Path,
    source_label: str,
    *,
    expected_id: str | None = None,
    expected_version: str | None = None,
    expected_installed_version: str | None = None,
    catalog_info: dict[str, Any] | None = None,
) -> None:
    """Validate and atomically install a complete workflow package directory."""
    import shutil
    import tempfile

    from .engine import WorkflowDefinition, validate_workflow

    workflow_file = package_dir / "workflow.yml"
    try:
        _validate_local_workflow_package(package_dir)
        workflow_bytes = workflow_file.read_bytes()
        definition = WorkflowDefinition.from_string(workflow_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        console.print(
            f"[red]Error:[/red] Invalid workflow package: "
            f"{_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)

    errors = validate_workflow(definition)
    if errors:
        console.print("[red]Error:[/red] Workflow validation failed:")
        for error in errors:
            console.print(f"  • {_escape_markup(str(error))}")
        raise typer.Exit(1)
    if not isinstance(definition.id, str) or not definition.id.strip():
        console.print("[red]Error:[/red] Workflow definition has an empty or missing 'id'")
        raise typer.Exit(1)
    if expected_id is not None and definition.id != expected_id:
        console.print(
            f"[red]Error:[/red] Workflow ID in YAML "
            f"({_escape_markup(repr(definition.id))}) does not match the requested "
            f"workflow ID ({_escape_markup(repr(expected_id))})."
        )
        raise typer.Exit(1)
    if expected_version is not None and str(definition.version) != expected_version:
        console.print(
            f"[red]Error:[/red] Downloaded workflow version "
            f"({_escape_markup(str(definition.version))}) does not match the catalog "
            f"version ({_escape_markup(expected_version)})."
        )
        raise typer.Exit(1)

    dest_dir = _safe_workflow_id_dir(workflows_dir, definition.id)
    staged_dir = Path(
        tempfile.mkdtemp(prefix=f".{definition.id}.installing-", dir=workflows_dir)
    )
    try:
        package_root = package_dir.resolve()

        def ignore_reserved_package_entries(
            source: str, names: list[str]
        ) -> set[str]:
            if Path(source).resolve() == package_root and "overlays" in names:
                return {"overlays"}
            return set()

        shutil.copytree(
            package_dir,
            staged_dir,
            dirs_exist_ok=True,
            ignore=ignore_reserved_package_entries,
        )
    except OSError as exc:
        shutil.rmtree(staged_dir, ignore_errors=True)
        console.print(
            f"[red]Error:[/red] Failed to stage workflow package: "
            f"{_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)

    backup_dir: Path | None = None
    try:
        with _workflow_install_transaction(project_root):
            registry = _open_workflow_registry(project_root)
            existing = registry.get(definition.id)
            if expected_installed_version is not None and (
                not isinstance(existing, dict)
                or existing.get("source") != "catalog"
                or str(existing.get("version")) != expected_installed_version
            ):
                console.print(
                    f"[yellow]Warning:[/yellow] Workflow "
                    f"'{_escape_markup(definition.id)}' changed during update; "
                    "rerun the command."
                )
                raise typer.Exit(1)
            if dest_dir.exists():
                backup_dir = Path(
                    tempfile.mkdtemp(
                        prefix=f".{definition.id}.backup-",
                        dir=workflows_dir,
                    )
                )
                backup_dir.rmdir()
                os.replace(dest_dir, backup_dir)
            try:
                os.replace(staged_dir, dest_dir)
            except BaseException:
                if backup_dir is not None:
                    os.replace(backup_dir, dest_dir)
                    backup_dir = None
                raise

            entry = {
                "name": definition.name,
                "version": definition.version,
                "description": definition.description,
                "source": source_label,
            }
            if catalog_info is not None:
                entry.update(
                    {
                        "source": "catalog",
                        "catalog_name": catalog_info.get("_catalog_name", ""),
                        "url": catalog_info.get("url", ""),
                    }
                )
            if isinstance(existing, dict) and not existing.get("enabled", True):
                entry["enabled"] = False
            try:
                registry.add(definition.id, entry)
            except (OSError, TypeError, ValueError):
                failed_dir: Path | None = None
                try:
                    failed_dir = Path(
                        tempfile.mkdtemp(
                            prefix=f".{definition.id}.failed-",
                            dir=workflows_dir,
                        )
                    )
                    failed_dir.rmdir()
                    os.replace(dest_dir, failed_dir)
                    if backup_dir is not None:
                        os.replace(backup_dir, dest_dir)
                        backup_dir = None
                except OSError as rollback_exc:
                    console.print(
                        "[yellow]Warning:[/yellow] Failed to fully restore the prior "
                        f"workflow package: {_escape_markup(str(rollback_exc))}"
                    )
                finally:
                    if failed_dir is not None and failed_dir.exists():
                        try:
                            shutil.rmtree(failed_dir)
                        except OSError as cleanup_exc:
                            console.print(
                                "[yellow]Warning:[/yellow] Could not remove failed "
                                f"workflow package: {_escape_markup(str(cleanup_exc))}"
                            )
                raise
    except typer.Exit:
        raise
    except (OSError, TypeError, ValueError) as exc:
        console.print(
            f"[red]Error:[/red] Failed to install workflow package: "
            f"{_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)
    finally:
        if staged_dir.exists():
            shutil.rmtree(staged_dir, ignore_errors=True)

    if backup_dir is not None:
        try:
            shutil.rmtree(backup_dir)
        except OSError as exc:
            console.print(
                "[yellow]Warning:[/yellow] Workflow installed, but its backup "
                f"directory could not be removed: {_escape_markup(str(exc))}"
            )
    console.print(
        f"[green]✓[/green] Workflow '{_escape_markup(definition.name)}' "
        f"({_escape_markup(definition.id)}) installed"
    )


# Root helper re-fetched at call time so test monkeypatching of
# `specify_cli._require_specify_project` keeps working after the move.
def _require_specify_project(*args, **kwargs):
    from .. import _require_specify_project as _f

    project_root = _f(*args, **kwargs)
    _reject_unsafe_workflow_storage(project_root)
    return project_root


def _failed_step_error(state: Any) -> str | None:
    """Terminal error for a failed/aborted run, if any.

    Returns the run-level error persisted by the engine at the moment
    the run terminated. Returns ``None`` for non-terminal statuses so
    the caller can print unconditionally.
    """
    if getattr(state.status, "value", state.status) not in ("failed", "aborted"):
        return None
    return getattr(state, "error", None)


def _scope_current_step_id(record: dict[str, Any]) -> str | None:
    """Step id a serialized scope rests on.

    Prefers the persisted ``current_step_id``: it is the only accurate source
    when a scope paused inside a nested control-flow body (``if``/``switch``/
    loop), where the snapshot index still points at the enclosing step. Falls
    back to deriving the id from that index for states written before the field
    was persisted.
    """
    persisted = record.get("current_step_id")
    if isinstance(persisted, str) and persisted:
        return persisted
    index = record.get("current_step_index")
    definition = record.get("definition")
    steps = definition.get("steps") if isinstance(definition, dict) else None
    if (
        isinstance(index, int)
        and not isinstance(index, bool)
        and isinstance(steps, list)
        and 0 <= index < len(steps)
        and isinstance(steps[index], dict)
    ):
        step_id = steps[index].get("id")
        if isinstance(step_id, str):
            return step_id
    return None


def _scope_summary(scopes: Any) -> list[dict[str, Any]]:
    """Compact nested-scope summary for the machine-readable payload."""
    summary: list[dict[str, Any]] = []
    if not isinstance(scopes, dict):
        return summary
    for key, record in scopes.items():
        if not isinstance(record, dict):
            continue
        summary.append(
            {
                "invocation_id": key,
                "workflow_id": record.get("workflow_id"),
                "status": record.get("status"),
                "current_step_id": _scope_current_step_id(record),
                "scopes": _scope_summary(record.get("workflow_scopes")),
            }
        )
    return summary


def _workflow_run_payload(state: Any) -> dict[str, Any]:
    """Machine-readable summary of a run/resume outcome."""
    payload = {
        "run_id": state.run_id,
        "workflow_id": state.workflow_id,
        "status": state.status.value,
        "current_step_id": state.current_step_id,
        "current_step_index": state.current_step_index,
    }
    gate = _gate_outcome(state)
    if gate is not None:
        payload["gate"] = gate
    error = _failed_step_error(state)
    if error is not None:
        payload["error"] = error
    # Only present when composition is in play, so existing payloads stay
    # byte-for-byte stable for runs without nested scopes.
    scopes = _scope_summary(getattr(state, "workflow_scopes", None))
    if scopes:
        payload["scopes"] = scopes
    return payload


def _is_gate_step(step: dict[str, Any]) -> bool:
    """Whether a recorded step result is a gate.

    Prefers the persisted ``type`` field, but when it is absent — a run paused
    by an older version, whose step record predates ``type`` being stored —
    falls back to the gate's unique output signature: only ``GateStep`` writes
    an ``on_reject`` key. A record carrying a *different* known ``type`` is not
    a gate, so the fallback applies only when ``type`` is missing entirely.
    """
    step_type = step.get("type")
    if step_type == "gate":
        return True
    if step_type:
        return False
    output = step.get("output")
    return isinstance(output, dict) and "on_reject" in output


def _gate_details(step_id: str, output: Any) -> dict[str, Any]:
    """Normalise a gate step's output into the stable JSON gate schema.

    ``message``, ``options``, and ``choice`` may be non-string YAML literals in
    an unvalidated workflow (``GateStep`` coerces none of them for the payload),
    so all three are normalised: message → str, options → list[str] | None,
    choice → str | None (None means no decision yet).
    """
    output = output if isinstance(output, dict) else {}
    message = output.get("message")
    choice = output.get("choice")
    return {
        "step_id": step_id,
        "message": None if message is None else str(message),
        "options": _normalize_gate_options(output.get("options")),
        "choice": None if choice is None else str(choice),
    }


def _scope_gate(scopes: Any, path: list[str]) -> dict[str, Any] | None:
    """Find the active gate inside a serialized scope tree.

    A pause/abort inside a composed workflow leaves the *root* resting on the
    ``workflow`` call, so the gate itself lives in a nested scope. Return its
    detail augmented with the ``scope_path`` (invocation ids root → leaf) so an
    orchestrator can drive a nested gate exactly as a top-level one.
    """
    if not isinstance(scopes, dict):
        return None
    for key, record in scopes.items():
        if not isinstance(record, dict):
            continue
        child_path = [*path, key]
        if str(record.get("status")) not in ("paused", "aborted"):
            continue
        # A deeper paused scope is more specific; check descendants first.
        nested = _scope_gate(record.get("workflow_scopes"), child_path)
        if nested is not None:
            return nested
        step_id = _scope_current_step_id(record)
        step_results = record.get("step_results")
        if step_id is None or not isinstance(step_results, dict):
            continue
        step = step_results.get(step_id)
        if isinstance(step, dict) and _is_gate_step(step):
            return {
                **_gate_details(step_id, step.get("output")),
                "scope_path": child_path,
            }
    return None


def _gate_outcome(state: Any) -> dict[str, Any] | None:
    """Gate detail for the structured outcome, when the run rests at a gate.

    A paused or gate-aborted run is otherwise indistinguishable from any
    other pause/abort in the machine-readable payload; surfacing the gate's
    prompt, options, and (after an interactive choice) the decision lets
    orchestrators drive review gates without parsing the human-facing stream.
    """
    # Two run states rest *on* a gate: `paused` (awaiting a decision) and
    # `aborted` (a gate rejected with `on_reject: abort` — the only path that
    # sets ABORTED, leaving current_step_id on that gate). Any other status —
    # notably `completed`/`failed` — must be suppressed: current_step_id is
    # not cleared when a run whose last executed step was a gate moves on, so
    # without this guard it would surface stale detail (run/resume/status).
    if getattr(state.status, "value", state.status) not in ("paused", "aborted"):
        return None
    step = (getattr(state, "step_results", None) or {}).get(state.current_step_id)
    if isinstance(step, dict) and _is_gate_step(step):
        return _gate_details(state.current_step_id, step.get("output"))
    # Not a top-level gate: a composed workflow may be paused on a nested gate.
    return _scope_gate(getattr(state, "workflow_scopes", None), [])


def _normalize_gate_options(options: Any) -> list[str] | None:
    """Normalise a gate's ``options`` to a stable ``list[str]`` (or ``None``).

    A valid gate stores a list, but an unvalidated workflow could leave a
    scalar or tuple. ``None`` stays ``None`` (no options); a list/tuple maps
    each element through ``str``; any other scalar becomes a single-element
    list — so the emitted JSON schema is always ``list[str] | None``. A bare
    string is treated as one option, never iterated character-by-character.
    """
    if options is None:
        return None
    if isinstance(options, (list, tuple)):
        return [str(o) for o in options]
    return [str(options)]


def _run_outcome_exit_code(status_value: str) -> int:
    """Exit code for a finished run/resume: non-zero on terminal failure.

    ``failed`` and ``aborted`` map to 1 so scripts and orchestrators can
    rely on the process exit code; ``completed`` and ``paused`` map to 0
    (paused is a legitimate waiting state, not a failure).
    """
    return 1 if status_value in ("failed", "aborted") else 0


def _emit_workflow_json(payload: dict[str, Any]) -> None:
    """Write a workflow payload as machine-readable JSON to stdout.

    Uses the builtin ``print`` rather than ``console.print`` so Rich
    markup interpretation, syntax highlighting, and line-wrapping can
    never alter the emitted JSON.
    """
    print(json.dumps(payload, indent=2))


@contextlib.contextmanager
def _stdout_to_stderr_when(active: bool):
    """Redirect everything written to stdout onto stderr while *active*.

    Suppressing the banner and the step-start callback is not enough to
    keep a ``--json`` stream clean: individual steps may still write to
    stdout while the engine runs — the gate step prints its prompt,
    and the prompt step runs a subprocess that inherits the process's
    stdout file descriptor. Either would corrupt the single JSON object.

    Redirecting at the file-descriptor level (``dup2``) captures both
    Python-level writes and inherited-fd subprocess output, so step
    progress lands on stderr (still visible to a human) while stdout
    carries only the emitted JSON. A no-op when *active* is false.
    """
    if not active:
        yield
        return
    sys.stdout.flush()
    saved_stdout_fd = os.dup(1)
    try:
        os.dup2(2, 1)  # fd 1 (stdout) now points at fd 2 (stderr)
        with contextlib.redirect_stdout(sys.stderr):
            yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_stdout_fd, 1)  # restore the real stdout
        os.close(saved_stdout_fd)


def _install_workflow_from_catalog(
    project_root: Path,
    workflows_dir: Path,
    workflow_id: str,
    expected_version: str | None = None,
    expected_installed_version: str | None = None,
) -> None:
    """Download, validate, and register a catalog workflow.

    Shared by ``workflow add`` and ``workflow update``. Raises ``typer.Exit``
    on any failure; the registry entry is only written on full success.
    ``expected_version``, when given, rejects a downloaded workflow whose
    version does not match the catalog version that triggered the install.
    ``expected_installed_version``, when given by ``workflow update``, aborts
    if another process changes the installed source or version before commit.
    """
    from .catalog import WorkflowCatalog, WorkflowCatalogError
    from .engine import WorkflowDefinition

    def versions_match(actual: object, expected: str) -> bool:
        from packaging import version as pkg_version

        try:
            return pkg_version.Version(str(actual)) == pkg_version.Version(
                expected
            )
        except pkg_version.InvalidVersion:
            return str(actual) == expected

    safe_wf_id = _escape_markup(workflow_id)

    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(workflow_id)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Workflow '{safe_wf_id}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(f"[yellow]Warning:[/yellow] Workflow '{safe_wf_id}' is from a discovery-only catalog")
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    workflow_url = info.get("url")
    if not workflow_url:
        console.print(f"[red]Error:[/red] Workflow '{safe_wf_id}' does not have an install URL in the catalog")
        raise typer.Exit(1)
    if not isinstance(workflow_url, str):
        # Untrusted catalog payload; a non-string would crash urlparse below.
        console.print(
            f"[red]Error:[/red] Workflow '{safe_wf_id}' has a malformed install URL."
        )
        raise typer.Exit(1)

    # Validate URL scheme (HTTPS required, HTTP allowed for localhost only)
    from urllib.parse import urlparse

    try:
        parsed_url = urlparse(workflow_url)
        parsed_url.port
    except ValueError:
        console.print(
            f"[red]Error:[/red] Workflow '{safe_wf_id}' has a malformed install URL."
        )
        raise typer.Exit(1)
    if not is_https_or_localhost_http(workflow_url):
        console.print(
            f"[red]Error:[/red] Workflow '{safe_wf_id}' has an invalid install URL. "
            "Only HTTPS URLs are allowed, except HTTP for localhost/loopback."
        )
        raise typer.Exit(1)

    # Reject path traversal, symlinked <id>, and a symlinked workflow.yml leaf
    # before any mkdir/download writes beneath the install directory.
    workflow_dir = _safe_workflow_id_dir(workflows_dir, workflow_id)
    workflow_file = workflow_dir / "workflow.yml"

    # Captured before any mkdir/download writes so every failure branch below
    # can tell a fresh install from a reinstall-over-an-existing-one,
    # mirroring _validate_and_install_local's existed-before-aware cleanup.
    existed_before = workflow_dir.is_dir()

    try:
        staged_file = _stage_workflow_file(
            workflow_dir,
            use_project_file_mode=not workflow_file.exists(),
        )
    except OSError as exc:
        console.print(
            f"[red]Error:[/red] Failed to install workflow '{safe_wf_id}' from catalog: "
            f"{_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)

    original_workflow_url = workflow_url
    downloaded_archive_format = None
    archive_content_type = None
    try:
        from specify_cli.authentication.http import open_url as _open_url
        from specify_cli.authentication.http import github_provider_hosts as _github_provider_hosts
        from specify_cli.authentication.github_http import (
            resolve_github_release_asset_api_url as _resolve_gh_asset,
        )

        _wf_cat_extra_headers = None
        _resolved_workflow_url = _resolve_gh_asset(
            workflow_url,
            _open_url,
            timeout=30,
            github_hosts=_github_provider_hosts(),
            redirect_validator=_reject_insecure_download_redirect,
        )
        if _resolved_workflow_url:
            workflow_url = _resolved_workflow_url
            _wf_cat_extra_headers = {"Accept": "application/octet-stream"}

        with _open_url(
            workflow_url,
            timeout=30,
            extra_headers=_wf_cat_extra_headers,
            redirect_validator=_reject_insecure_download_redirect,
        ) as response:
            # Validate final URL after redirects
            final_url = response.geturl()
            if not is_https_or_localhost_http(final_url):
                _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
                console.print(
                    f"[red]Error:[/red] Workflow '{safe_wf_id}' redirected to non-HTTPS URL: {_escape_markup(final_url)}"
                )
                raise typer.Exit(1)
            archive_content_type = (
                response.getheader("Content-Type")
                if hasattr(response, "getheader")
                else None
            )
            downloaded_archive_format = (
                archive_format_from_name(final_url)
                or archive_format_from_name(original_workflow_url)
                or archive_format_from_content_type(archive_content_type)
            )
            # Written to the staging file, never workflow_file directly, so a
            # reinstall's prior working copy is never touched until the
            # atomic commit below runs.
            if downloaded_archive_format is not None:
                downloaded_content = read_response_limited(
                    response,
                    error_type=ValueError,
                    label=f"workflow '{workflow_id}' archive download",
                )
            elif _workflow_yaml_is_declared(final_url, archive_content_type):
                downloaded_content = _read_response_within_limit(response)
            else:
                downloaded_content = read_response_limited(
                    response,
                    error_type=ValueError,
                    label=f"workflow '{workflow_id}' download",
                )
                downloaded_archive_format = _sniff_workflow_archive_format(
                    downloaded_content
                )
                if downloaded_archive_format is None:
                    _enforce_workflow_yaml_size(downloaded_content)
            staged_file.write_bytes(downloaded_content)
    except typer.Exit:
        raise
    except Exception as exc:
        _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
        console.print(f"[red]Error:[/red] Failed to install workflow '{safe_wf_id}' from catalog: {_escape_markup(str(exc))}")
        raise typer.Exit(1)

    if downloaded_archive_format is not None:
        try:
            verify_archive_sha256(
                downloaded_content,
                info.get("sha256"),
                workflow_id,
                ValueError,
            )
            import tempfile
            from io import BytesIO

            with tempfile.TemporaryDirectory(
                prefix="speckit-workflow-archive-"
            ) as extract_dir:
                extracted_root = Path(extract_dir)
                safe_extract_archive(
                    staged_file.path,
                    extracted_root,
                    archive_file=BytesIO(downloaded_content),
                    source_name=original_workflow_url,
                    content_type=archive_content_type,
                )
                package_root = _workflow_package_root(extracted_root)
                _safe_discard_staged_workflow_file(
                    staged_file,
                    workflow_dir,
                    existed_before,
                )
                _install_workflow_package(
                    project_root,
                    workflows_dir,
                    package_root,
                    workflow_url,
                    expected_id=workflow_id,
                    expected_version=expected_version,
                    expected_installed_version=expected_installed_version,
                    catalog_info={**info, "url": workflow_url},
                )
        except typer.Exit:
            raise
        except (OSError, ValueError) as exc:
            _safe_discard_staged_workflow_file(
                staged_file,
                workflow_dir,
                existed_before,
            )
            console.print(
                f"[red]Error:[/red] Invalid workflow archive: "
                f"{_escape_markup(str(exc))}"
            )
            raise typer.Exit(1)
        return

    # Validate the downloaded workflow (still staged, not yet committed)
    # before registering.
    try:
        definition = WorkflowDefinition.from_string(
            downloaded_content.decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
        console.print(f"[red]Error:[/red] Downloaded workflow is invalid: {_escape_markup(str(exc))}")
        raise typer.Exit(1)

    from .engine import validate_workflow
    errors = validate_workflow(definition)
    if errors:
        _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
        console.print("[red]Error:[/red] Downloaded workflow validation failed:")
        for err in errors:
            console.print(f"  \u2022 {_escape_markup(str(err))}")
        raise typer.Exit(1)

    # Enforce that the workflow's internal ID matches the catalog key
    if definition.id and definition.id != workflow_id:
        _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
        console.print(
            f"[red]Error:[/red] Workflow ID in YAML ({_escape_markup(repr(definition.id))}) "
            f"does not match catalog key ({_escape_markup(repr(workflow_id))}). "
            f"The catalog entry may be misconfigured."
        )
        raise typer.Exit(1)

    # A stale or misconfigured URL can serve a different version than the
    # catalog advertised; without this check `update` would report success
    # while leaving the old version installed (or even downgrading).
    if expected_version is not None:
        if not versions_match(definition.version, expected_version):
            _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
            console.print(
                f"[red]Error:[/red] Downloaded workflow version ({_escape_markup(str(definition.version))}) "
                f"does not match the catalog version ({_escape_markup(expected_version)}). "
                f"The catalog entry may be stale or misconfigured."
            )
            raise typer.Exit(1)

    try:
        transaction = _workflow_install_transaction(project_root)
        with transaction:
            transaction_existed_before = (
                existed_before or workflow_file.exists()
            )
            transaction_registry = _open_workflow_registry(project_root)
            if expected_installed_version is not None:
                current = transaction_registry.get(workflow_id)
                if (
                    not isinstance(current, dict)
                    or current.get("source") != "catalog"
                    or not versions_match(
                        current.get("version"), expected_installed_version
                    )
                ):
                    console.print(
                        f"[yellow]Warning:[/yellow] Workflow '{safe_wf_id}' "
                        "changed during update; rerun the command to use its "
                        "current source and version."
                    )
                    raise typer.Exit(1)
            # Commit the staged download onto workflow_file via an atomic
            # swap. A prior file is renamed aside for registry rollback.
            try:
                backup_file = _commit_workflow_file(
                    staged_file, workflow_file, transaction_existed_before
                )
            except OSError as exc:
                _safe_discard_staged_workflow_file(
                    staged_file, workflow_dir, existed_before
                )
                console.print(
                    f"[red]Error:[/red] Failed to install workflow "
                    f"'{safe_wf_id}' from catalog: {_escape_markup(str(exc))}"
                )
                raise typer.Exit(1)

            entry = {
                "name": definition.name or info.get("name", workflow_id),
                "version": definition.version or info.get("version", "0.0.0"),
                "description": definition.description
                or info.get("description", ""),
                "source": "catalog",
                "catalog_name": info.get("_catalog_name", ""),
                "url": workflow_url,
            }
            # Preserve a prior disabled state across updates/reinstalls.
            existing = transaction_registry.get(workflow_id)
            if isinstance(existing, dict) and not existing.get(
                "enabled", True
            ):
                entry["enabled"] = False
            try:
                transaction_registry.add(workflow_id, entry)
            except (OSError, TypeError, ValueError) as exc:
                _safe_rollback_committed_workflow_file(
                    workflow_file,
                    workflow_dir,
                    transaction_existed_before,
                    backup_file,
                )
                console.print(
                    f"[red]Error:[/red] Failed to update workflow registry for "
                    f"'{_escape_markup(workflow_id)}': "
                    f"{_escape_markup(str(exc))}"
                )
                raise typer.Exit(1)
            # Registry update succeeded while the transaction lock is held.
            _discard_committed_backup_file(backup_file)
    except typer.Exit:
        _safe_discard_staged_workflow_file(
            staged_file, workflow_dir, existed_before
        )
        raise
    except OSError as exc:
        _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
        console.print(
            f"[red]Error:[/red] Failed to lock workflow install "
            f"'{safe_wf_id}': "
            f"{_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)
    console.print(
        f"[green]✓[/green] Workflow '{_escape_markup(str(info.get('name', workflow_id)))}' "
        "installed from catalog"
    )


def _set_workflow_enabled(workflow_id: str, enabled: bool) -> None:
    """Update enabled state from a fresh registry snapshot while locked."""
    project_root = _require_specify_project()
    safe_id = _escape_markup(workflow_id)
    try:
        with _workflow_install_transaction(project_root):
            registry = _open_workflow_registry(project_root)
            metadata = registry.get(workflow_id)
            if metadata is None:
                console.print(
                    f"[red]Error:[/red] Workflow '{safe_id}' is not installed"
                )
                raise typer.Exit(1)
            if not isinstance(metadata, dict):
                console.print(
                    f"[red]Error:[/red] Registry entry for '{safe_id}' "
                    "is corrupted"
                )
                raise typer.Exit(1)
            current = bool(metadata.get("enabled", True))
            state = "enabled" if enabled else "disabled"
            if current is enabled:
                console.print(
                    f"[yellow]Workflow '{safe_id}' is already {state}[/yellow]"
                )
                raise typer.Exit(0)
            try:
                registry.add(workflow_id, {**metadata, "enabled": enabled})
            except OSError as exc:
                console.print(
                    f"[red]Error:[/red] Failed to update workflow registry "
                    f"for '{safe_id}': {_escape_markup(str(exc))}"
                )
                raise typer.Exit(1)
    except OSError as exc:
        console.print(
            f"[red]Error:[/red] Failed to lock workflow registry for "
            f"'{safe_id}': {_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)
    state = "enabled" if enabled else "disabled"
    console.print(f"[green]✓[/green] Workflow '{safe_id}' {state}")


# Compatibility forwarders for established public and direct-call paths.
def workflow_add(*args, **kwargs):
    from .command_add import workflow_add as command

    return command(*args, **kwargs)


def workflow_remove(*args, **kwargs):
    from .command_remove import workflow_remove as command

    return command(*args, **kwargs)


def workflow_status(*args, **kwargs):
    from .command_status import workflow_status as command

    return command(*args, **kwargs)


def workflow_enable(*args, **kwargs):
    from .command_enable import workflow_enable as command

    return command(*args, **kwargs)


def workflow_disable(*args, **kwargs):
    from .command_disable import workflow_disable as command

    return command(*args, **kwargs)


def workflow_step_add(*args, **kwargs):
    from .step.command_add import workflow_step_add as command

    return command(*args, **kwargs)


def workflow_step_remove(*args, **kwargs):
    from .step.command_remove import workflow_step_remove as command

    return command(*args, **kwargs)


def register(app: typer.Typer) -> None:
    """Attach the workflow command group to the root Typer app."""
    from .catalog import register as register_catalog
    from .overlay import register as register_overlay
    from .step import register as register_step

    register_catalog(workflow_app)
    register_step(workflow_app)
    register_overlay(workflow_app)

    # isort: off
    from . import command_run  # noqa: F401 -- registers handler
    from . import command_resume  # noqa: F401 -- registers handler
    from . import command_status  # noqa: F401 -- registers handler
    from . import command_list  # noqa: F401 -- registers handler
    from . import command_add  # noqa: F401 -- registers handler
    from . import command_remove  # noqa: F401 -- registers handler
    from . import command_update  # noqa: F401 -- registers handler
    from . import command_enable  # noqa: F401 -- registers handler
    from . import command_disable  # noqa: F401 -- registers handler
    from . import command_search  # noqa: F401 -- registers handler
    from . import command_info  # noqa: F401 -- registers handler
    from . import command_resolve  # noqa: F401 -- registers handler
    # isort: on

    app.add_typer(workflow_app, name="workflow")
