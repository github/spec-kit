"""specify workflow * command handlers — app objects and register().

Moved out of __init__.py (PR-8/8). Handlers reference `_require_specify_project`
(kept in the package root) through the thin shim below, which re-fetches from
the parent package at call time so test monkeypatching of
`specify_cli._require_specify_project` keeps working.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.markup import escape as _escape_markup

from .._console import console, err_console
from .._project import _resolve_init_dir_override

workflow_app = typer.Typer(
    name="workflow",
    help="Manage and run automation workflows",
    add_completion=False,
)

workflow_catalog_app = typer.Typer(
    name="catalog",
    help="Manage workflow catalogs",
    add_completion=False,
)
workflow_app.add_typer(workflow_catalog_app, name="catalog")

workflow_step_app = typer.Typer(
    name="step",
    help="Manage workflow step types",
    add_completion=False,
)
workflow_app.add_typer(workflow_step_app, name="step")

workflow_step_catalog_app = typer.Typer(
    name="catalog",
    help="Manage step catalogs",
    add_completion=False,
)
workflow_step_app.add_typer(workflow_step_catalog_app, name="catalog")


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


def _path_has_symlink_component(path: Path) -> bool:
    """Return whether any component of an absolute path is a symlink."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _same_existing_path(left: Path, right: Path) -> bool:
    """Return whether two existing paths identify the same filesystem entry."""
    try:
        return os.path.samefile(left, right)
    except OSError:
        return left == right


def _resolve_run_owner_root(
    installed_registry_root: str | None, project_root: Path
) -> Path:
    """Determine which project's registry gates resuming a run.

    ``installed_registry_root`` is only ever persisted when the run's
    installed workflow genuinely belongs to a *different* project than the
    one whose ``runs/`` directory holds this run's own state (a direct
    external workflow-file invocation) -- see ``workflow_run``. The common
    case (an installed workflow run from its own project) stores ``None``,
    so a later project rename/move is transparently picked up here by
    falling back to the *current* ``project_root`` instead of a stale
    absolute path baked in at run start.

    A persisted cross-project root that no longer exists cannot be safely
    rediscovered and must fail closed instead of consulting the unrelated
    project that happens to store the run state.
    """
    if installed_registry_root:
        candidate = Path(installed_registry_root)
        if (
            candidate.is_absolute()
            and not _path_has_symlink_component(candidate)
            and candidate.is_dir()
        ):
            return candidate
        raise ValueError(
            "Installed workflow owner is unavailable; cannot safely resume"
        )
    return project_root


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


def _scan_for_workflow_owner(parts: tuple[str, ...]) -> int | None:
    """Find the *nearest* (innermost) ``.specify/workflows/<id>`` owner in
    *parts*, scanning from the end of the path.

    Scanning from the end (rather than stopping at the first match from the
    start) matters for a project nested beneath an unrelated outer path that
    happens to reuse the same ``.specify``/``workflows`` segment names: the
    first-from-start match would pick the outer directory and the wrong
    workflow ID, silently missing the real (inner) owner's disabled check.

    Returns the index of the owning ``.specify`` segment, or ``None`` if no
    owner segment is present.
    """
    for i in range(len(parts) - 3, -1, -1):
        if (
            parts[i].casefold() == ".specify"
            and parts[i + 1].casefold() == "workflows"
        ):
            return i
    return None


def _expand_first_symlink_target(path: Path) -> Path | None:
    """Expand one symlink component while preserving the remaining path."""
    parts = path.parts
    current = Path(path.anchor) if path.is_absolute() else Path()
    start = 1 if path.is_absolute() else 0
    for index in range(start, len(parts)):
        current = current / parts[index]
        if not current.is_symlink():
            continue
        try:
            target = Path(os.readlink(current))
        except OSError:
            return None
        if not target.is_absolute():
            target = current.parent / target
        expanded = target.joinpath(*parts[index + 1 :])
        return Path(os.path.normpath(str(expanded.absolute())))
    return None


def _resolve_installed_workflow_ownership(
    source_path: Path, err
) -> tuple[Path | None, str | None]:
    """Map a direct ``workflow.yml`` *source_path* back to the installed
    workflow (``registry_root``, ``registered_id``) it belongs to, if any.

    A registered path can point at installed storage three ways, all of
    which must receive the same registry disabled-check:

    1. Lexically: the path's own (symlink-preserving) segments identify
       ``.specify/workflows/<id>`` -- collapsing ``..``/``.`` but
       never resolving symlinks, so a symlinked ``workflow.yml`` leaf (or
       symlinked ``<id>`` directory) inside the owned tree is caught by the
       inward-symlink refusal below rather than silently followed.
    2. Via an intermediate alias target whose lexical path identifies
       ``.specify/workflows/<id>`` before a symlinked storage ancestor is
       resolved away.
    3. Via an outward-pointing alias whose fully resolved target lands
       inside legitimate installed storage, even though the raw invocation
       path has no ownership segments.

    Returns ``(None, None)`` when neither applies -- a genuinely standalone
    external workflow file, which is allowed to run unchecked.
    """
    def ownership_for(candidate: Path) -> tuple[Path, str] | None:
        parts = candidate.parts
        i = _scan_for_workflow_owner(parts)
        if i is None:
            return None
        registry_root = (
            Path(*parts[:i]) if i else Path(candidate.anchor or ".")
        )
        candidate_specify = Path(*parts[: i + 1])
        candidate_workflows = Path(*parts[: i + 2])
        candidate_id_dir = Path(*parts[: i + 3])
        canonical_specify = registry_root / ".specify"
        canonical_workflows = canonical_specify / "workflows"
        # The path-derived registry_root here may differ from the cwd's
        # project_root already checked by _reject_unsafe_workflow_storage
        # (e.g. this path points into another project entirely, or this
        # project's own .specify is itself a symlink to an
        # attacker-controlled tree) -- check it explicitly rather than
        # trusting that cwd-scoped guard, and don't rely on
        # WorkflowRegistry's own symlinked-parent handling as the safety
        # signal here: it fails closed by raising OSError at construction
        # time (see catalog.py's _load), but that surfaces as an opaque
        # exception rather than this guard's clean, specific CLI error for
        # the actual owning project root.
        _reject_unsafe_dir(canonical_specify, ".specify")
        _reject_unsafe_dir(canonical_workflows, ".specify/workflows")
        _reject_unsafe_dir(candidate_specify, ".specify")
        _reject_unsafe_dir(candidate_workflows, ".specify/workflows")
        try:
            if not os.path.samefile(candidate_specify, canonical_specify):
                return None
            if not os.path.samefile(
                candidate_workflows, canonical_workflows
            ):
                return None
        except OSError:
            return None
        registry = _open_workflow_registry(registry_root, err)
        registered_id = None
        for workflow_id in registry.list():
            if (
                not isinstance(workflow_id, str)
                or workflow_id in _RESERVED_WORKFLOW_IDS
                or not _WORKFLOW_ID_PATTERN.fullmatch(workflow_id)
            ):
                continue
            try:
                if os.path.samefile(
                    candidate_id_dir,
                    canonical_workflows / workflow_id,
                ):
                    registered_id = workflow_id
                    break
            except OSError:
                continue
        if registered_id is None:
            return None
        # A legitimately installed workflow's own directory tree never
        # contains a symlink (workflow add/remove both refuse one at
        # install time); one appearing here means the file actually loaded
        # below would not be the file this ownership match is based on, so
        # refuse rather than silently mismatch.
        for k in range(i + 2, len(parts) + 1):
            if Path(*parts[:k]).is_symlink():
                err.print(
                    "[red]Error:[/red] Refusing to run: "
                    f".specify/workflows/{_escape_markup(registered_id)} "
                    "contains a symlinked path component"
                )
                raise typer.Exit(1)
        return registry_root, registered_id

    lexical = Path(os.path.normpath(str(source_path.absolute())))
    ownership = ownership_for(lexical)
    if ownership is not None:
        return ownership

    # Inspect each intermediate symlink target before fully resolving it.
    # Full resolution can erase .specify/workflows ownership segments when
    # one of those storage directories is itself a symlink.
    candidate = lexical
    seen = {candidate}
    for _ in range(40):
        expanded = _expand_first_symlink_target(candidate)
        if expanded is None or expanded in seen:
            break
        ownership = ownership_for(expanded)
        if ownership is not None:
            return ownership
        seen.add(expanded)
        candidate = expanded

    # A fully resolved target may still land in legitimate installed
    # storage through an unrelated-looking alias.
    try:
        resolved = source_path.resolve(strict=False)
    except (OSError, RuntimeError):
        return None, None
    if resolved == lexical:
        # Nothing on this path is a symlink; already covered above.
        return None, None
    ownership = ownership_for(resolved)
    return ownership if ownership is not None else (None, None)


_WORKFLOW_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_RESERVED_WORKFLOW_IDS: frozenset[str] = frozenset({"runs", "steps"})


def _reject_insecure_download_redirect(old_url: str, new_url: str) -> None:
    """Reject insecure redirects before they are followed."""
    import urllib.error
    from ipaddress import ip_address
    from urllib.parse import urlparse

    def _is_loopback_http(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme != "http":
            return False
        host = parsed.hostname or ""
        if host == "localhost":
            return True
        try:
            return ip_address(host).is_loopback
        except ValueError:
            return False

    if urlparse(new_url).scheme == "https":
        return
    if _is_loopback_http(old_url) and _is_loopback_http(new_url):
        return
    raise urllib.error.URLError(
        "redirect target must use HTTPS; loopback HTTP may only redirect from loopback HTTP"
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


# Root helper re-fetched at call time so test monkeypatching of
# `specify_cli._require_specify_project` keeps working after the move.
def _require_specify_project(*args, **kwargs):
    from .. import _require_specify_project as _f

    project_root = _f(*args, **kwargs)
    _reject_unsafe_workflow_storage(project_root)
    return project_root


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
    if not isinstance(step, dict) or not _is_gate_step(step):
        return None
    output = step.get("output") or {}
    # `message`, `options`, and `choice` may be non-string YAML literals in an
    # unvalidated workflow (GateStep coerces none of them for the payload), so
    # normalise all three for a stable JSON schema: message → str, options →
    # list[str] | None, choice → str | None (None means no decision yet).
    message = output.get("message")
    choice = output.get("choice")
    return {
        "step_id": state.current_step_id,
        "message": None if message is None else str(message),
        "options": _normalize_gate_options(output.get("options")),
        "choice": None if choice is None else str(choice),
    }


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


@workflow_app.command("run")
def workflow_run(
    source: str = typer.Argument(..., help="Workflow ID or YAML file path"),
    input_values: list[str] | None = typer.Option(
        None, "--input", "-i", help="Input values as key=value pairs"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the run outcome as a single JSON object instead of formatted text.",
    ),
):
    """Run a workflow from an installed ID or local YAML path."""
    from . import load_custom_steps
    from .engine import WorkflowEngine

    source_path = Path(source).expanduser()
    is_file_source = source_path.suffix.lower() in (".yml", ".yaml") and source_path.is_file()

    if is_file_source:
        # When running a YAML file directly, use cwd as project root without
        # requiring a .specify/ project directory — unless SPECIFY_INIT_DIR
        # explicitly names a project, in which case the strict override applies.
        override = _resolve_init_dir_override()
        project_root = override if override is not None else Path.cwd()
        _reject_unsafe_workflow_storage(project_root)
    else:
        project_root = _require_specify_project()

    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        engine.on_step_start = lambda sid, label: console.print(f"  \u25b8 [{sid}] {label} \u2026")

    err = _error_console(json_output)

    registered_id: str | None = None
    registry_root = project_root
    if not is_file_source:
        # Reject path-equivalent spellings ("align-wf/", "align-wf/.") that
        # would miss the registry lookup yet still load the installed file,
        # bypassing the disabled check below.
        if source in _RESERVED_WORKFLOW_IDS or not _WORKFLOW_ID_PATTERN.fullmatch(source):
            err.print(
                f"[red]Error:[/red] Invalid workflow ID: {_escape_markup(repr(source))}"
            )
            raise typer.Exit(1)
        registered_id = source
    else:
        # A direct YAML path may still point at an installed workflow's own
        # file (lexically, or via a symlinked alias pointing into installed
        # storage); map it back to its owning project and ID so the
        # disabled check below can't be silently bypassed.
        owner_root, owner_id = _resolve_installed_workflow_ownership(source_path, err)
        if owner_id is not None:
            registry_root = owner_root
            registered_id = owner_id

    if registered_id is not None:
        _require_enabled_workflow(registry_root, registered_id, err)

    try:
        definition = engine.load_workflow(source_path if is_file_source else source)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Workflow not found: {source}")
        raise typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] Invalid workflow: {exc}")
        raise typer.Exit(1)

    # Validate
    errors = engine.validate(definition)
    if errors:
        err.print("[red]Workflow validation failed:[/red]")
        for verr in errors:
            err.print(f"  • {_escape_markup(str(verr))}")
        raise typer.Exit(1)

    # Parse inputs
    inputs = _parse_input_values(input_values, json_output=json_output)

    if not json_output:
        console.print(f"\n[bold cyan]Running workflow:[/bold cyan] {definition.name} ({definition.id})")
        console.print(f"[dim]Version: {definition.version}[/dim]\n")

    try:
        with _stdout_to_stderr_when(json_output):
            state = engine.execute(
                definition,
                inputs,
                installed_workflow_id=registered_id,
                # Only persist an explicit root when the installed workflow
                # genuinely belongs to a *different* project than the one
                # whose runs/ directory holds this run's own state (a
                # direct external workflow-file invocation) -- the common
                # case (an installed workflow run from its own project)
                # leaves this None so resume re-derives the owning root
                # from wherever the project currently is, transparently
                # surviving a project rename/move instead of baking in a
                # stale absolute path at run start.
                installed_registry_root=(
                    registry_root.resolve(strict=True)
                    if registered_id
                    and not _same_existing_path(registry_root, project_root)
                    else None
                ),
            )
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Workflow failed:[/red] {exc}")
        raise typer.Exit(1)

    if json_output:
        _emit_workflow_json(_workflow_run_payload(state))
        raise typer.Exit(_run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")
    console.print(f"[dim]Run ID: {state.run_id}[/dim]")

    if state.status.value == "paused":
        console.print(f"\nResume with: [cyan]specify workflow resume {state.run_id}[/cyan]")

    raise typer.Exit(_run_outcome_exit_code(state.status.value))


@workflow_app.command("resume")
def workflow_resume(
    run_id: str = typer.Argument(..., help="Run ID to resume"),
    input_values: list[str] | None = typer.Option(
        None, "--input", "-i", help="Updated input values as key=value pairs"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit the resume outcome as a single JSON object instead of formatted text.",
    ),
):
    """Resume a paused or failed workflow run."""
    from . import load_custom_steps
    from .engine import RunState, WorkflowEngine

    project_root = _require_specify_project()
    load_custom_steps(project_root)
    engine = WorkflowEngine(project_root)
    if not json_output:
        engine.on_step_start = lambda sid, label: console.print(f"  \u25b8 [{sid}] {label} \u2026")

    inputs = _parse_input_values(input_values, json_output=json_output)
    err = _error_console(json_output)

    # Pre-load the persisted run state so a run started from an installed
    # workflow that has since been disabled cannot resume unchecked --
    # engine.resume() replays the run directly from disk with no registry
    # awareness at all, which would otherwise bypass the same disabled
    # guard `workflow run` enforces. Runs without installed_workflow_id
    # (a direct/non-installed source, or a run persisted before this field
    # existed) are unaffected and resume exactly as before.
    try:
        pre_state = RunState.load(run_id, project_root)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1)
    except OSError as exc:
        err.print(f"[red]Resume failed:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1)

    if pre_state.installed_workflow_id is not None:
        try:
            owner_root = _resolve_run_owner_root(
                pre_state.installed_registry_root, project_root
            )
        except ValueError as exc:
            err.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1)
        _require_enabled_workflow(
            owner_root, pre_state.installed_workflow_id, err
        )
    elif not pre_state.installed_origin_tracked:
        if _require_enabled_workflow(
            project_root, pre_state.workflow_id, err
        ):
            pre_state.installed_workflow_id = pre_state.workflow_id
        pre_state.installed_origin_tracked = True
        try:
            pre_state.save()
        except OSError as exc:
            err.print(f"[red]Resume failed:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1)

    try:
        with _stdout_to_stderr_when(json_output):
            state = engine.resume(run_id, inputs or None)
    except FileNotFoundError:
        err.print(f"[red]Error:[/red] Run not found: {run_id}")
        raise typer.Exit(1)
    except ValueError as exc:
        err.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1)
    except Exception as exc:
        err.print(f"[red]Resume failed:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1)

    if json_output:
        _emit_workflow_json(_workflow_run_payload(state))
        raise typer.Exit(_run_outcome_exit_code(state.status.value))

    status_colors = {
        "completed": "green",
        "paused": "yellow",
        "failed": "red",
        "aborted": "red",
    }
    color = status_colors.get(state.status.value, "white")
    console.print(f"\n[{color}]Status: {state.status.value}[/{color}]")

    raise typer.Exit(_run_outcome_exit_code(state.status.value))


@workflow_app.command("status")
def workflow_status(
    run_id: str | None = typer.Argument(None, help="Run ID to inspect (shows all if omitted)"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit run status as a single JSON object instead of formatted text.",
    ),
):
    """Show workflow run status."""
    from .engine import WorkflowEngine

    project_root = _require_specify_project()
    engine = WorkflowEngine(project_root)

    if run_id:
        try:
            from .engine import RunState
            state = RunState.load(run_id, project_root)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise typer.Exit(1)
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1)

        if json_output:
            # Build on the shared run/resume payload so the common fields
            # (including current_step_index) stay identical across commands.
            payload = {
                **_workflow_run_payload(state),
                "created_at": state.created_at,
                "updated_at": state.updated_at,
                "steps": {
                    sid: sd.get("status", "unknown")
                    for sid, sd in state.step_results.items()
                },
            }
            _emit_workflow_json(payload)
            return

        status_colors = {
            "completed": "green",
            "paused": "yellow",
            "failed": "red",
            "aborted": "red",
            "running": "blue",
            "created": "dim",
        }
        color = status_colors.get(state.status.value, "white")

        console.print(f"\n[bold cyan]Workflow Run: {state.run_id}[/bold cyan]")
        console.print(f"  Workflow: {state.workflow_id}")
        console.print(f"  Status:   [{color}]{state.status.value}[/{color}]")
        console.print(f"  Created:  {state.created_at}")
        console.print(f"  Updated:  {state.updated_at}")

        if state.current_step_id:
            console.print(f"  Current:  {state.current_step_id}")

        if state.step_results:
            console.print(f"\n  [bold]Steps ({len(state.step_results)}):[/bold]")
            for step_id, step_data in state.step_results.items():
                s = step_data.get("status", "unknown")
                sc = {"completed": "green", "failed": "red", "paused": "yellow"}.get(s, "white")
                console.print(f"    [{sc}]●[/{sc}] {step_id}: {s}")
    else:
        runs = engine.list_runs()

        if json_output:
            payload = {
                "runs": [
                    {
                        "run_id": r["run_id"],
                        "workflow_id": r.get("workflow_id"),
                        "status": r.get("status", "unknown"),
                        "updated_at": r.get("updated_at"),
                    }
                    for r in runs
                ]
            }
            _emit_workflow_json(payload)
            return

        if not runs:
            console.print("[yellow]No workflow runs found.[/yellow]")
            return

        console.print("\n[bold cyan]Workflow Runs:[/bold cyan]\n")
        for run_data in runs:
            s = run_data.get("status", "unknown")
            sc = {"completed": "green", "failed": "red", "paused": "yellow", "running": "blue"}.get(s, "white")
            console.print(
                f"  [{sc}]●[/{sc}] {run_data['run_id']}  "
                f"{run_data.get('workflow_id', '?')}  "
                f"[{sc}]{s}[/{sc}]  "
                f"[dim]{run_data.get('updated_at', '?')}[/dim]"
            )


@workflow_app.command("list")
def workflow_list():
    """List installed workflows."""
    project_root = _require_specify_project()
    registry = _open_workflow_registry(project_root)
    installed = registry.list()

    if not installed:
        console.print("[yellow]No workflows installed.[/yellow]")
        console.print("\nInstall a workflow with:")
        console.print("  [cyan]specify workflow add <workflow-id>[/cyan]")
        return

    console.print("\n[bold cyan]Installed Workflows:[/bold cyan]\n")
    for wf_id, wf_data in installed.items():
        safe_id = _escape_markup(wf_id)
        if not isinstance(wf_data, dict):
            console.print(f"  [yellow]Warning:[/yellow] Skipping corrupted registry entry '{safe_id}'.\n")
            continue
        marker = "" if wf_data.get("enabled", True) else " [red]\\[disabled][/red]"
        name = _escape_markup(str(wf_data.get("name", wf_id)))
        version = _escape_markup(str(wf_data.get("version", "?")))
        console.print(f"  [bold]{name}[/bold] ({safe_id}) v{version}{marker}")
        desc = wf_data.get("description", "")
        if desc:
            console.print(f"    {_escape_markup(str(desc))}")
        console.print()


@workflow_app.command("add")
def workflow_add(
    source: str = typer.Argument(..., help="Workflow ID, URL, or local path"),
    dev: bool = typer.Option(False, "--dev", help="Install from a local workflow YAML file or directory"),
    from_url: str | None = typer.Option(None, "--from", help="Install from a custom URL"),
):
    """Install a workflow from catalog, URL, or local path."""
    from .engine import WorkflowDefinition

    project_root = _require_specify_project()
    _open_workflow_registry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"
    # With --from, source names the expected workflow ID: validate it up
    # front so a URL/path/typo fails without a network fetch.
    if from_url is not None and not dev:
        _validate_workflow_id_or_exit(source)
    # Reject a symlinked .specify / .specify/workflows before any write so an
    # install can't escape the project root (covers the local, URL, and
    # catalog branches below — all write beneath workflows_dir).
    _reject_unsafe_dir(project_root / ".specify", ".specify")
    _reject_unsafe_dir(workflows_dir, ".specify/workflows")

    def _validate_and_install_local(
        yaml_path: Path, source_label: str, expected_id: str | None = None
    ) -> None:
        """Validate and install a workflow from a local YAML file."""
        try:
            with yaml_path.open("rb") as source_file:
                source_mode = os.fstat(source_file.fileno()).st_mode & 0o7777
                source_content = source_file.read()
            definition = WorkflowDefinition.from_string(
                source_content.decode("utf-8")
            )
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to read workflow YAML: "
                f"{_escape_markup(str(exc))}"
            )
            raise typer.Exit(1)
        except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
            console.print(f"[red]Error:[/red] Invalid workflow YAML: {_escape_markup(str(exc))}")
            raise typer.Exit(1)
        # Non-string ids (e.g. unquoted ``id: 123`` or ``id: 0``) fall through
        # to validate_workflow below, which reports a typed error instead of
        # crashing on ``.strip()`` here. Only None/empty/whitespace-only ids
        # are rejected as missing.
        if (
            definition.id is None
            or definition.id == ""
            or (isinstance(definition.id, str) and not definition.id.strip())
        ):
            console.print("[red]Error:[/red] Workflow definition has an empty or missing 'id'")
            raise typer.Exit(1)

        from .engine import validate_workflow
        errors = validate_workflow(definition)
        if errors:
            console.print("[red]Error:[/red] Workflow validation failed:")
            for err in errors:
                console.print(f"  \u2022 {_escape_markup(str(err))}")
            raise typer.Exit(1)

        if expected_id is not None and definition.id != expected_id:
            console.print(
                f"[red]Error:[/red] Workflow ID in YAML ({_escape_markup(repr(definition.id))}) "
                f"does not match the requested workflow ID ({_escape_markup(repr(expected_id))})."
            )
            raise typer.Exit(1)

        dest_dir = _safe_workflow_id_dir(workflows_dir, definition.id)
        dest_file = dest_dir / "workflow.yml"
        existed_before = dest_dir.is_dir()

        try:
            staged_file = _stage_workflow_file(dest_dir)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to install workflow "
                f"'{_escape_markup(definition.id)}': {_escape_markup(str(exc))}"
            )
            raise typer.Exit(1)

        try:
            # Write the exact bytes parsed above so a concurrent source edit
            # cannot desynchronize installed content from validated metadata.
            staged_file.write_bytes(source_content)
            staged_file.set_mode(source_mode)
        except OSError as exc:
            _safe_discard_staged_workflow_file(staged_file, dest_dir, existed_before)
            console.print(
                f"[red]Error:[/red] Failed to install workflow "
                f"'{_escape_markup(definition.id)}': {_escape_markup(str(exc))}"
            )
            raise typer.Exit(1)

        try:
            transaction = _workflow_install_transaction(project_root)
            with transaction:
                transaction_existed_before = existed_before or dest_file.exists()
                transaction_registry = _open_workflow_registry(project_root)
                # Commit the staged copy onto dest_file via an atomic swap. A
                # prior file is renamed aside so registry failure can restore it.
                try:
                    backup_file = _commit_workflow_file(
                        staged_file, dest_file, transaction_existed_before
                    )
                except OSError as exc:
                    _safe_discard_staged_workflow_file(
                        staged_file, dest_dir, existed_before
                    )
                    console.print(
                        f"[red]Error:[/red] Failed to install workflow "
                        f"'{_escape_markup(definition.id)}': "
                        f"{_escape_markup(str(exc))}"
                    )
                    raise typer.Exit(1)
                try:
                    entry = {
                        "name": definition.name,
                        "version": definition.version,
                        "description": definition.description,
                        "source": source_label,
                    }
                    existing = transaction_registry.get(definition.id)
                    if isinstance(existing, dict) and not existing.get(
                        "enabled", True
                    ):
                        entry["enabled"] = False
                    transaction_registry.add(definition.id, entry)
                except (OSError, TypeError, ValueError) as exc:
                    _safe_rollback_committed_workflow_file(
                        dest_file,
                        dest_dir,
                        transaction_existed_before,
                        backup_file,
                    )
                    console.print(
                        f"[red]Error:[/red] Failed to update workflow registry for "
                        f"'{_escape_markup(definition.id)}': "
                        f"{_escape_markup(str(exc))}"
                    )
                    raise typer.Exit(1)
                # Registry update succeeded while the transaction lock is held.
                _discard_committed_backup_file(backup_file)
        except typer.Exit:
            _safe_discard_staged_workflow_file(
                staged_file, dest_dir, existed_before
            )
            raise
        except OSError as exc:
            _safe_discard_staged_workflow_file(staged_file, dest_dir, existed_before)
            console.print(
                f"[red]Error:[/red] Failed to lock workflow install "
                f"'{_escape_markup(definition.id)}': {_escape_markup(str(exc))}"
            )
            raise typer.Exit(1)
        console.print(
            f"[green]✓[/green] Workflow '{_escape_markup(definition.name)}' "
            f"({_escape_markup(definition.id)}) installed"
        )

    # Explicit local install (mirrors `extension add --dev`). --dev takes
    # precedence over --from so a URL that would be ignored is never fetched.
    if dev:
        dev_path = Path(source).expanduser()
        if dev_path.is_file() and dev_path.suffix in (".yml", ".yaml"):
            _validate_and_install_local(dev_path, str(dev_path))
            return
        if dev_path.is_dir():
            dev_wf_file = dev_path / "workflow.yml"
            if not dev_wf_file.is_file():
                console.print(f"[red]Error:[/red] No workflow.yml found in {_escape_markup(source)}")
                raise typer.Exit(1)
            _validate_and_install_local(dev_wf_file, str(dev_path))
            return
        console.print(
            "[red]Error:[/red] --dev source must be a workflow YAML file or a "
            f"directory containing workflow.yml: {_escape_markup(source)}"
        )
        raise typer.Exit(1)

    # Try as URL (http/https) — either the positional source is a URL, or an
    # explicit --from URL names where to fetch it (mirrors `extension add --from`).
    download_url = (
        from_url
        if from_url is not None
        else (source if source.startswith(("http://", "https://")) else None)
    )
    if download_url is not None:
        from ipaddress import ip_address
        from urllib.parse import urlparse
        from specify_cli.authentication.http import open_url as _open_url

        try:
            parsed_src = urlparse(download_url)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid URL: {_escape_markup(download_url)}")
            raise typer.Exit(1)
        src_host = parsed_src.hostname or ""
        src_loopback = src_host == "localhost"
        if not src_loopback:
            try:
                src_loopback = ip_address(src_host).is_loopback
            except ValueError:
                # Host is not an IP literal (e.g., a DNS name); keep default non-loopback.
                pass
        if parsed_src.scheme != "https" and not (parsed_src.scheme == "http" and src_loopback):
            console.print("[red]Error:[/red] Only HTTPS URLs are allowed, except HTTP for localhost.")
            raise typer.Exit(1)

        if from_url is not None:
            from rich.panel import Panel

            safe_url = _escape_markup(from_url)
            console.print()
            console.print(
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
            console.print()
            if not typer.confirm("Continue with installation?", default=False):
                console.print("Cancelled")
                raise typer.Exit(0)

        from specify_cli._github_http import resolve_github_release_asset_api_url as _resolve_gh_asset
        from specify_cli.authentication.http import github_provider_hosts as _github_provider_hosts

        _wf_url_extra_headers = None
        _resolved_wf_url = _resolve_gh_asset(
            download_url,
            _open_url,
            timeout=30,
            github_hosts=_github_provider_hosts(),
            redirect_validator=_reject_insecure_download_redirect,
        )
        if _resolved_wf_url:
            download_url = _resolved_wf_url
            _wf_url_extra_headers = {"Accept": "application/octet-stream"}

        import tempfile
        tmp_path: Path | None = None
        try:
            with _open_url(
                download_url,
                timeout=30,
                extra_headers=_wf_url_extra_headers,
                redirect_validator=_reject_insecure_download_redirect,
            ) as resp:
                final_url = resp.geturl()
                final_parsed = urlparse(final_url)
                final_host = final_parsed.hostname or ""
                final_lb = final_host == "localhost"
                if not final_lb:
                    try:
                        final_lb = ip_address(final_host).is_loopback
                    except ValueError:
                        # Redirect host is not an IP literal; keep loopback as determined above.
                        pass
                if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_lb):
                    console.print(
                        f"[red]Error:[/red] URL redirected to non-HTTPS: {_escape_markup(final_url)}"
                    )
                    raise typer.Exit(1)
                with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp:
                    # Assign tmp_path immediately: NamedTemporaryFile(delete=False)
                    # creates the file on disk right away, before any bytes are
                    # written, so a failure in the size-limited read below must
                    # still be able to find and remove it.
                    tmp_path = Path(tmp.name)
                    tmp.write(_read_response_within_limit(resp))
        except typer.Exit:
            raise
        except Exception as exc:
            if tmp_path is not None:
                # A cleanup failure here must never replace/mask the
                # original download error below with a raw, unhandled
                # OSError -- warn about it and keep going, exactly like the
                # later post-install finally cleanup does.
                try:
                    tmp_path.unlink(missing_ok=True)
                except OSError as cleanup_exc:
                    console.print(
                        "[yellow]Warning:[/yellow] Could not remove temporary "
                        f"download file {_escape_markup(str(tmp_path))}: "
                        f"{_escape_markup(str(cleanup_exc))}"
                    )
            console.print(f"[red]Error:[/red] Failed to download workflow: {_escape_markup(str(exc))}")
            raise typer.Exit(1)
        try:
            # When installed via --from, the positional argument names the
            # workflow the user expects — enforce it like the catalog branch.
            _validate_and_install_local(
                tmp_path,
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
                console.print(
                    "[yellow]Warning:[/yellow] Could not remove temporary "
                    f"download file {_escape_markup(str(tmp_path))}: "
                    f"{_escape_markup(str(exc))}"
                )
        return

    # Try as a local file/directory
    source_path = Path(source)
    if source_path.exists():
        if source_path.is_file() and source_path.suffix in (".yml", ".yaml"):
            _validate_and_install_local(source_path, str(source_path))
            return
        elif source_path.is_dir():
            wf_file = source_path / "workflow.yml"
            if not wf_file.is_file():
                console.print(f"[red]Error:[/red] No workflow.yml found in {_escape_markup(source)}")
                raise typer.Exit(1)
            _validate_and_install_local(wf_file, str(source_path))
            return

    # Try from catalog
    _install_workflow_from_catalog(project_root, workflows_dir, source)


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
    from ipaddress import ip_address
    from urllib.parse import urlparse

    try:
        parsed_url = urlparse(workflow_url)
        url_host = parsed_url.hostname or ""
    except ValueError:
        console.print(
            f"[red]Error:[/red] Workflow '{safe_wf_id}' has a malformed install URL."
        )
        raise typer.Exit(1)
    is_loopback = False
    if url_host == "localhost":
        is_loopback = True
    else:
        try:
            is_loopback = ip_address(url_host).is_loopback
        except ValueError:
            # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
            pass
    if parsed_url.scheme != "https" and not (parsed_url.scheme == "http" and is_loopback):
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

    try:
        from specify_cli.authentication.http import open_url as _open_url
        from specify_cli.authentication.http import github_provider_hosts as _github_provider_hosts
        from specify_cli._github_http import resolve_github_release_asset_api_url as _resolve_gh_asset

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
            final_parsed = urlparse(final_url)
            final_host = final_parsed.hostname or ""
            final_loopback = final_host == "localhost"
            if not final_loopback:
                try:
                    final_loopback = ip_address(final_host).is_loopback
                except ValueError:
                    # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
                    pass
            if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_loopback):
                _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
                console.print(
                    f"[red]Error:[/red] Workflow '{safe_wf_id}' redirected to non-HTTPS URL: {_escape_markup(final_url)}"
                )
                raise typer.Exit(1)
            # Written to the staging file, never workflow_file directly, so a
            # reinstall's prior working copy is never touched until the
            # atomic commit below runs.
            downloaded_content = _read_response_within_limit(response)
            staged_file.write_bytes(downloaded_content)
    except typer.Exit:
        raise
    except Exception as exc:
        _safe_discard_staged_workflow_file(staged_file, workflow_dir, existed_before)
        console.print(f"[red]Error:[/red] Failed to install workflow '{safe_wf_id}' from catalog: {_escape_markup(str(exc))}")
        raise typer.Exit(1)

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


def _remove_workflow_locked(
    project_root: Path, workflows_dir: Path, workflow_id: str
) -> Path | None:
    """Stage a workflow directory and persist removal while locked."""
    registry = _open_workflow_registry(project_root)
    safe_id = _escape_markup(workflow_id)
    if not registry.is_installed(workflow_id):
        console.print(
            f"[red]Error:[/red] Workflow '{safe_id}' is not installed"
        )
        raise typer.Exit(1)

    workflow_dir_unresolved = workflows_dir / workflow_id
    if workflow_dir_unresolved.is_symlink():
        console.print(
            f"[red]Error:[/red] Refusing to remove symlinked "
            f".specify/workflows/{safe_id}"
        )
        raise typer.Exit(1)

    workflow_dir = workflow_dir_unresolved.resolve()
    try:
        rel_parts = workflow_dir.relative_to(workflows_dir.resolve()).parts
    except ValueError:
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: "
            f"{_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)
    if rel_parts != (workflow_id,):
        console.print(
            f"[red]Error:[/red] Invalid workflow ID: "
            f"{_escape_markup(repr(workflow_id))}"
        )
        raise typer.Exit(1)

    if workflow_dir.exists() and not workflow_dir.is_dir():
        console.print(
            f"[red]Error:[/red] .specify/workflows/{safe_id} exists "
            "but is not a directory"
        )
        raise typer.Exit(1)

    import tempfile

    staged_dir: Path | None = None
    if workflow_dir.exists():
        try:
            reserved = Path(
                tempfile.mkdtemp(
                    prefix=f".{workflow_id}.removing-", dir=workflows_dir
                )
            )
            reserved.rmdir()
            os.rename(workflow_dir, reserved)
            staged_dir = reserved
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to stage workflow directory "
                f"{_escape_markup(str(workflow_dir))} for removal: "
                f"{_escape_markup(str(exc))}"
            )
            raise typer.Exit(1)

    try:
        registry.remove(workflow_id)
    except (OSError, TypeError, ValueError) as exc:
        if staged_dir is not None:
            try:
                os.rename(staged_dir, workflow_dir)
            except OSError as restore_exc:
                console.print(
                    f"[yellow]Warning:[/yellow] Failed to restore workflow "
                    "directory after registry update failure; it remains "
                    f"staged at {_escape_markup(str(staged_dir))}: "
                    f"{_escape_markup(str(restore_exc))}"
                )
        console.print(
            f"[red]Error:[/red] Failed to update workflow registry for "
            f"'{safe_id}': {_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)
    return staged_dir


@workflow_app.command("remove")
def workflow_remove(
    workflow_id: str = typer.Argument(..., help="Workflow ID to uninstall"),
):
    """Uninstall a workflow."""
    project_root = _require_specify_project()
    workflows_dir = project_root / ".specify" / "workflows"
    _validate_workflow_id_or_exit(workflow_id)
    safe_id = _escape_markup(workflow_id)
    import shutil
    try:
        with _workflow_install_transaction(project_root):
            staged_dir = _remove_workflow_locked(
                project_root, workflows_dir, workflow_id
            )
    except OSError as exc:
        console.print(
            f"[red]Error:[/red] Failed to lock workflow removal "
            f"'{safe_id}': {_escape_markup(str(exc))}"
        )
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Workflow '{workflow_id}' removed")

    # The registry has already durably committed the removal at this point,
    # so it must stand regardless of what happens below: deleting the staged
    # directory is now just cleanup, not a data-integrity concern, and a
    # failure here is reported as a warning (not an error) to avoid
    # contradicting the registry state that already succeeded.
    if staged_dir is not None:
        try:
            shutil.rmtree(staged_dir)
        except OSError as exc:
            console.print(
                f"[yellow]Warning:[/yellow] Workflow '{safe_id}' was removed, but its "
                f"staged directory could not be deleted: {_escape_markup(str(exc))}. "
                f"Remove it manually: {_escape_markup(str(staged_dir))}"
            )


@workflow_app.command("update")
def workflow_update(
    workflow_id: str | None = typer.Argument(None, help="Workflow ID to update (default: all)"),
):
    """Update installed workflow(s) to the latest catalog version."""
    from packaging import version as pkg_version

    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    registry = _open_workflow_registry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"
    _reject_unsafe_dir(project_root / ".specify", ".specify")
    _reject_unsafe_dir(workflows_dir, ".specify/workflows")

    installed = registry.list()
    if workflow_id:
        if not registry.is_installed(workflow_id):
            console.print(f"[red]Error:[/red] Workflow '{_escape_markup(workflow_id)}' is not installed")
            raise typer.Exit(1)
        targets = [workflow_id]
    else:
        targets = list(installed)

    if not targets:
        console.print("[yellow]No workflows installed[/yellow]")
        raise typer.Exit(0)

    catalog = WorkflowCatalog(project_root)
    console.print("🔄 Checking for updates...\n")

    updates_available: list[dict[str, str]] = []
    checked = 0
    for wf_id in targets:
        safe_id = _escape_markup(str(wf_id))
        metadata = installed.get(wf_id)
        if not isinstance(metadata, dict):
            console.print(f"⚠  {safe_id}: Registry entry is corrupted (skipping)")
            continue
        if metadata.get("source") != "catalog":
            console.print(f"⚠  {safe_id}: Not installed from a catalog — re-add to update (skipping)")
            continue
        try:
            installed_version = pkg_version.Version(str(metadata.get("version")))
        except pkg_version.InvalidVersion:
            console.print(
                f"⚠  {safe_id}: Invalid installed version '{_escape_markup(str(metadata.get('version')))}' in registry (skipping)"
            )
            continue
        try:
            info = catalog.get_workflow_info(wf_id)
        except WorkflowCatalogError as exc:
            console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1)
        if not info:
            console.print(f"⚠  {safe_id}: Not found in catalog (skipping)")
            continue
        if not info.get("_install_allowed", True):
            console.print(
                f"⚠  {safe_id}: Updates not allowed from '{_escape_markup(str(info.get('_catalog_name', 'catalog')))}' (skipping)"
            )
            continue
        try:
            catalog_version = pkg_version.Version(str(info.get("version")))
        except pkg_version.InvalidVersion:
            console.print(
                f"⚠  {safe_id}: Invalid catalog version '{_escape_markup(str(info.get('version')))}' (skipping)"
            )
            continue
        if catalog_version > installed_version:
            checked += 1
            updates_available.append(
                {"id": wf_id, "installed": str(installed_version), "available": str(catalog_version)}
            )
        else:
            checked += 1
            console.print(f"✓ {safe_id}: Up to date (v{installed_version})")

    if not updates_available:
        if not checked:
            console.print("\n[yellow]No workflows were eligible for update[/yellow]")
        elif checked == len(targets):
            console.print("\n[green]All workflows are up to date![/green]")
        else:
            console.print(
                f"\n[green]All checked workflows are up to date[/green] "
                f"[yellow]({len(targets) - checked} skipped)[/yellow]"
            )
        raise typer.Exit(0)

    console.print("\n[bold]Updates available:[/bold]\n")
    for update in updates_available:
        console.print(
            f"  • {_escape_markup(update['id'])}: {update['installed']} → {update['available']}"
        )
    console.print()
    if not typer.confirm("Update these workflows?"):
        console.print("Cancelled")
        raise typer.Exit(0)

    console.print()
    failed: list[str] = []
    for update in updates_available:
        # _install_workflow_from_catalog is fully transactional (staged
        # download, atomic commit, rename-based rollback on registry
        # failure): it never leaves a partially-written workflow.yml, so
        # this loop only needs to record success/failure, not perform its
        # own backup/restore.
        try:
            _install_workflow_from_catalog(
                project_root, workflows_dir, update["id"],
                expected_version=update["available"],
                expected_installed_version=update["installed"],
            )
        except (typer.Exit, OSError) as exc:
            if isinstance(exc, OSError):
                console.print(
                    f"[red]Error:[/red] Filesystem error updating "
                    f"'{_escape_markup(update['id'])}': {_escape_markup(str(exc))}"
                )
            failed.append(update["id"])

    if failed:
        console.print(
            f"\n[red]Failed to update:[/red] {', '.join(_escape_markup(f) for f in failed)}"
        )
        raise typer.Exit(1)


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


@workflow_app.command("enable")
def workflow_enable(
    workflow_id: str = typer.Argument(..., help="Workflow ID to enable"),
):
    """Enable a disabled workflow."""
    _set_workflow_enabled(workflow_id, True)


@workflow_app.command("disable")
def workflow_disable(
    workflow_id: str = typer.Argument(..., help="Workflow ID to disable"),
):
    """Disable a workflow without removing it."""
    _set_workflow_enabled(workflow_id, False)
    console.print(f"To re-enable: specify workflow enable {_escape_markup(workflow_id)}")


@workflow_app.command("search")
def workflow_search(
    query: str | None = typer.Argument(None, help="Search query"),
    tag: str | None = typer.Option(None, "--tag", help="Filter by tag"),
    author: str | None = typer.Option(None, "--author", help="Filter by author"),
):
    """Search workflow catalogs."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag, author=author)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1)

    if not results:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    console.print(f"\n[bold cyan]Workflows ({len(results)}):[/bold cyan]\n")
    for wf in results:
        name = _escape_markup(str(wf.get("name", wf.get("id", "?"))))
        wf_id = _escape_markup(str(wf.get("id", "?")))
        version = _escape_markup(str(wf.get("version", "?")))
        console.print(f"  [bold]{name}[/bold] ({wf_id}) v{version}")
        desc = wf.get("description", "")
        if desc:
            console.print(f"    {_escape_markup(str(desc))}")
        tags = wf.get("tags", [])
        if tags:
            safe_tags = _escape_markup(", ".join(str(t) for t in tags))
            console.print(f"    [dim]Tags: {safe_tags}[/dim]")
        console.print()


@workflow_app.command("info")
def workflow_info(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    """Show workflow details and step graph."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError
    from .engine import WorkflowEngine

    project_root = _require_specify_project()

    # Check installed first
    registry = _open_workflow_registry(project_root)
    installed = registry.get(workflow_id)

    engine = WorkflowEngine(project_root)

    definition = None
    try:
        definition = engine.load_workflow(workflow_id)
    except FileNotFoundError:
        # Local workflow definition not found on disk; fall back to
        # catalog/registry lookup below.
        pass

    if definition:
        console.print(f"\n[bold cyan]{definition.name}[/bold cyan] ({definition.id})")
        console.print(f"  Version:     {definition.version}")
        if definition.author:
            console.print(f"  Author:      {definition.author}")
        if definition.description:
            console.print(f"  Description: {definition.description}")
        if definition.default_integration:
            console.print(f"  Integration: {definition.default_integration}")
        if installed:
            console.print("  [green]Installed[/green]")

        if definition.inputs:
            console.print("\n  [bold]Inputs:[/bold]")
            for name, inp in definition.inputs.items():
                if isinstance(inp, dict):
                    req = "required" if inp.get("required") else "optional"
                    console.print(f"    {name} ({inp.get('type', 'string')}) — {req}")

        if definition.steps:
            console.print(f"\n  [bold]Steps ({len(definition.steps)}):[/bold]")
            for step in definition.steps:
                stype = step.get("type", "command")
                console.print(f"    → {step.get('id', '?')} [{stype}]")
        return

    # Try catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(workflow_id)
    except WorkflowCatalogError:
        info = None

    if info:
        console.print(f"\n[bold cyan]{info.get('name', workflow_id)}[/bold cyan] ({workflow_id})")
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        if info.get("tags"):
            console.print(f"  Tags:        {', '.join(info['tags'])}")
        console.print("  [yellow]Not installed[/yellow]")
    else:
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' not found")
        raise typer.Exit(1)


@workflow_catalog_app.command("list")
def workflow_catalog_list():
    """List configured workflow catalog sources."""
    from .catalog import WorkflowCatalog, WorkflowCatalogError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Workflow Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = "[green]install allowed[/green]" if cfg["install_allowed"] else "[yellow]discovery only[/yellow]"
        console.print(f"  [{i}] [bold]{cfg['name']}[/bold] — {install_status}")
        console.print(f"      {cfg['url']}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@workflow_catalog_app.command("add")
def workflow_catalog_add(
    url: str = typer.Argument(..., help="Catalog URL to add"),
    name: str | None = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a workflow catalog source."""
    from .catalog import WorkflowCatalog, WorkflowValidationError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        catalog.add_catalog(url, name)
    except WorkflowValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source added: {url}")


@workflow_catalog_app.command("remove")
def workflow_catalog_remove(
    index: int = typer.Argument(..., help="Catalog index to remove (from 'catalog list')"),
):
    """Remove a workflow catalog source by index."""
    from .catalog import WorkflowCatalog, WorkflowValidationError

    project_root = _require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except WorkflowValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source '{removed_name}' removed")


# ===== Workflow Step Commands =====

@workflow_step_app.command("list")
def workflow_step_list():
    """List installed step types (built-in and custom)."""
    from . import STEP_REGISTRY
    from .catalog import StepRegistry

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Read installed custom steps from registry only — no dynamic imports
    installed: dict = {}
    if specify_dir.exists():
        registry = StepRegistry(project_root)
        installed = registry.list()

    console.print("\n[bold cyan]Installed Step Types:[/bold cyan]\n")

    built_in = sorted(k for k in STEP_REGISTRY if k not in installed)
    if built_in:
        console.print("  [bold]Built-in:[/bold]")
        for key in built_in:
            console.print(f"    • {key}")
        console.print()

    if installed:
        console.print("  [bold]Custom (installed):[/bold]")
        for key in sorted(installed):
            meta = installed[key] or {}
            name = meta.get("name", key)
            version = meta.get("version", "?")
            console.print(f"    • [bold]{name}[/bold] ({key}) v{version}")
        console.print()

    if not built_in and not installed:
        console.print("[yellow]No step types found.[/yellow]")

    if specify_dir.exists():
        console.print(
            "  Install a new step type with: [cyan]specify workflow step add <id>[/cyan]"
        )


# IDs that map to internal names used under .specify/workflows/steps/ and must
# not be used as custom step IDs (dotfile check is done separately at runtime).
_RESERVED_STEP_IDS: frozenset[str] = frozenset({".cache", "step-registry.json"})

# Windows reserved device names (case-insensitive, with or without extensions)
_WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset({
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
})

# Characters invalid in filenames on Windows
_WINDOWS_INVALID_CHARS: frozenset[str] = frozenset('<>:"|?*')


def _validate_step_id_or_exit(step_id: str) -> None:
    """Validate that ``step_id`` is a single safe path component.

    Rejects empty strings, whitespace-only strings, leading/trailing whitespace,
    path separators, ``.``/``..`` components, dotfile prefixes, reserved names,
    Windows-invalid filename characters, trailing dots/spaces, and Windows
    reserved device names. Exits with code 1 on failure.
    """
    # Strip the stem (before first dot) for Windows reserved-name check
    stem = step_id.split(".")[0].lower() if step_id else ""
    if (
        not step_id
        or not step_id.strip()
        or step_id != step_id.strip()
        or "/" in step_id
        or "\\" in step_id
        or step_id in (".", "..")
        or step_id.startswith(".")
        or step_id.endswith(".")
        or step_id.endswith(" ")
        or step_id.lower() in _RESERVED_STEP_IDS
        or stem in _WINDOWS_RESERVED_NAMES
        or any(c in _WINDOWS_INVALID_CHARS for c in step_id)
        or any(ord(c) < 32 for c in step_id)
    ):
        console.print(
            f"[red]Error:[/red] Invalid step id '{step_id}': must be a single safe "
            "path component (no separators, no leading dot, not a reserved name, "
            "no invalid filename characters)"
        )
        raise typer.Exit(1)


def _resolve_steps_base_dir_or_exit(project_root: Path) -> Path:
    """Resolve .specify/workflows/steps while refusing symlinked parent directories."""
    project_root_resolved = project_root.resolve()
    steps_base_dir_unresolved = project_root / ".specify" / "workflows" / "steps"

    current = project_root
    for part in (".specify", "workflows", "steps"):
        current = current / part
        if current.is_symlink():
            console.print(
                f"[red]Error:[/red] Refusing to use symlinked step directory '{current}'"
            )
            raise typer.Exit(1)
        if current.exists() and not current.is_dir():
            console.print(
                f"[red]Error:[/red] Step directory path is not a directory: '{current}'"
            )
            raise typer.Exit(1)

    steps_base_dir = steps_base_dir_unresolved.resolve()
    try:
        steps_base_dir.relative_to(project_root_resolved)
    except ValueError:
        console.print(
            f"[red]Error:[/red] Step directory escapes project root: '{steps_base_dir}'"
        )
        raise typer.Exit(1)

    return steps_base_dir


@workflow_step_app.command("add")
def workflow_step_add(
    step_id: str = typer.Argument(..., help="Step type ID from catalog"),
):
    """Install a custom step type from the step catalog."""
    from .catalog import StepCatalog, StepCatalogError, StepRegistry, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Step type '{step_id}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(
            f"[yellow]Warning:[/yellow] Step type '{step_id}' is from a discovery-only catalog"
        )
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    # Reject step IDs that collide with built-in step types
    from . import STEP_REGISTRY as _step_reg
    if step_id in _step_reg:
        console.print(
            f"[red]Error:[/red] Step type '{step_id}' conflicts with a built-in step type"
        )
        raise typer.Exit(1)

    # Reject if already installed
    registry = StepRegistry(project_root)
    if registry.is_installed(step_id):
        console.print(
            f"[red]Error:[/red] Step type '{step_id}' is already installed. "
            "Remove it first with: [cyan]specify workflow step remove "
            f"{step_id}[/cyan]"
        )
        raise typer.Exit(1)

    step_yml_url = info.get("step_yml_url") or info.get("url")
    if not step_yml_url:
        console.print(f"[red]Error:[/red] Catalog entry for '{step_id}' has no URL")
        raise typer.Exit(1)

    # Derive __init__.py URL: replace trailing step.yml with __init__.py
    # or use explicit init_url if provided.
    init_url = info.get("init_url")
    if not init_url:
        if step_yml_url.endswith("step.yml"):
            init_url = step_yml_url[: -len("step.yml")] + "__init__.py"
        else:
            console.print(
                f"[red]Error:[/red] Cannot derive __init__.py URL from '{step_yml_url}'. "
                "Catalog entry should provide 'init_url' or a 'url' ending in 'step.yml'."
            )
            raise typer.Exit(1)

    from urllib.parse import urlparse
    from specify_cli.authentication.http import open_url as _open_url

    def _safe_fetch(url: str) -> bytes:
        parsed = urlparse(url)
        is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
            raise ValueError(f"Refusing to fetch from non-HTTPS URL: {url}")
        if not parsed.hostname:
            raise ValueError(f"Refusing to fetch from URL with no hostname: {url}")
        with _open_url(
            url, timeout=30, redirect_validator=_reject_insecure_download_redirect
        ) as resp:
            final_url = resp.geturl()
            final_parsed = urlparse(final_url)
            final_is_localhost = final_parsed.hostname in ("localhost", "127.0.0.1", "::1")
            if final_parsed.scheme != "https" and not (
                final_parsed.scheme == "http" and final_is_localhost
            ):
                raise ValueError(f"Redirect to non-HTTPS URL: {final_url}")
            if not final_parsed.hostname:
                raise ValueError(f"Redirect to URL with no hostname: {final_url}")
            return _read_response_within_limit(resp)

    _validate_step_id_or_exit(step_id)

    steps_base_dir = _resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: ensure the resolved directory is a direct child of
    # steps_base_dir even after symlink resolution.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)
    if rel_parts != (step_id,):
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)

    import shutil
    import tempfile

    # Refuse if step_dir already exists (e.g. leftover from a previous failed/manual
    # install that wasn't registered). The user should remove it before retrying.
    if step_dir.exists():
        console.print(
            f"[red]Error:[/red] Step directory already exists at '{step_dir}'. "
            f"Remove it manually or use: [cyan]specify workflow step remove {step_id}[/cyan]"
        )
        raise typer.Exit(1)

    # Create steps_base_dir now so the staging temp dir is on the same filesystem,
    # enabling a truly atomic os.rename() below.
    try:
        steps_base_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(tempfile.mkdtemp(prefix="speckit_step_tmp_", dir=steps_base_dir))
    except OSError as exc:
        console.print(f"[red]Error:[/red] Failed to create staging directory: {exc}")
        raise typer.Exit(1)
    try:
        try:
            step_yml_content = _safe_fetch(step_yml_url)
            init_py_content = _safe_fetch(init_url)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to download step files: {exc}")
            raise typer.Exit(1)

        # Validate step.yml
        try:
            import yaml as _yaml

            meta = _yaml.safe_load(step_yml_content.decode("utf-8")) or {}
        except Exception as exc:
            console.print(f"[red]Error:[/red] Invalid step.yml: {exc}")
            raise typer.Exit(1)

        if not isinstance(meta, dict):
            console.print("[red]Error:[/red] step.yml must be a YAML mapping")
            raise typer.Exit(1)

        step_meta = meta.get("step", {})
        if not isinstance(step_meta, dict):
            console.print("[red]Error:[/red] step.yml 'step' field must be a mapping")
            raise typer.Exit(1)
        type_key = step_meta.get("type_key", "")
        if not type_key:
            console.print("[red]Error:[/red] step.yml missing 'step.type_key' field")
            raise typer.Exit(1)

        if type_key != step_id:
            console.print(
                f"[red]Error:[/red] step.yml type_key ({type_key!r}) does not match "
                f"catalog ID ({step_id!r})"
            )
            raise typer.Exit(1)

        # Write the two required files.
        try:
            (tmp_path / "step.yml").write_bytes(step_yml_content)
            (tmp_path / "__init__.py").write_bytes(init_py_content)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to write step files to staging directory: {exc}"
            )
            raise typer.Exit(1)

        # Optionally download additional package files declared in the catalog entry
        # (e.g. helper modules). Each entry in ``extra_files`` is a mapping of
        # relative-path → URL. step.yml and __init__.py are ignored here (already
        # written). Paths are validated to stay within the step package directory to
        # prevent path-traversal attacks.
        extra_files = info.get("extra_files")
        if extra_files is not None and not isinstance(extra_files, dict):
            console.print(
                "[yellow]Warning:[/yellow] Catalog entry 'extra_files' is not a mapping; "
                "additional package files will not be downloaded."
            )
            extra_files = {}
        for rel_path, file_url in (extra_files or {}).items():
            if not isinstance(rel_path, str) or not rel_path.strip():
                console.print(
                    "[red]Error:[/red] Catalog entry 'extra_files' contains an "
                    "empty or non-string path key"
                )
                raise typer.Exit(1)
            if rel_path in ("step.yml", "__init__.py"):
                continue  # already written above
            # Reject dot-path segments ('', '.', '..') that would refer to the
            # package directory itself (IsADirectoryError) or escape it.
            rel_parts = Path(rel_path).parts
            if not rel_parts or any(seg in ("", ".", "..") for seg in rel_parts):
                console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is not a "
                    "valid relative file path"
                )
                raise typer.Exit(1)
            if not isinstance(file_url, str) or not file_url.strip():
                console.print(
                    f"[red]Error:[/red] extra_files entry '{rel_path}' has an "
                    "empty or non-string URL"
                )
                raise typer.Exit(1)
            # Resolve both destination and base to handle any symlinks in tmp_path itself,
            # ensuring the traversal check is robust even on non-canonical paths.
            resolved_base = tmp_path.resolve()
            dest = (tmp_path / rel_path).resolve()
            try:
                dest.relative_to(resolved_base)
            except ValueError:
                console.print(
                    f"[red]Error:[/red] extra_files path '{rel_path}' is outside "
                    "the step package directory"
                )
                raise typer.Exit(1)
            try:
                file_content = _safe_fetch(file_url)
            except Exception as exc:
                console.print(
                    f"[red]Error:[/red] Failed to download extra file '{rel_path}': {exc}"
                )
                raise typer.Exit(1)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(file_content)
            except OSError as exc:
                console.print(
                    f"[red]Error:[/red] Failed to write extra file '{rel_path}': {exc}"
                )
                raise typer.Exit(1)

        # Atomically rename the staging directory to the final location.
        # Both paths are under steps_base_dir (same filesystem), so os.rename()
        # is atomic on POSIX and won't leave a partially-written directory at
        # step_dir on failure.
        try:
            os.rename(tmp_path, step_dir)
        except OSError as exc:
            console.print(f"[red]Error:[/red] Failed to install step '{step_id}': {exc}")
            raise typer.Exit(1)
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
                "description": info.get("description", step_meta.get("description", "")),
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
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(
        f"[green]✓[/green] Step type '{step_name}' ({step_id}) installed"
    )
    console.print(
        "  Use [cyan]specify workflow step list[/cyan] to verify the installation."
    )


@workflow_step_app.command("remove")
def workflow_step_remove(
    step_id: str = typer.Argument(..., help="Step type ID to uninstall"),
):
    """Uninstall a custom step type."""
    from .catalog import StepRegistry, StepValidationError

    project_root = _require_specify_project()

    _validate_step_id_or_exit(step_id)

    registry = StepRegistry(project_root)
    in_registry = registry.is_installed(step_id)

    steps_base_dir = _resolve_steps_base_dir_or_exit(project_root)
    step_dir = (steps_base_dir / step_id).resolve()
    # Defense-in-depth: even though _validate_step_id_or_exit rejects path
    # separators, ensure that the resolved directory is a single child of
    # steps_base_dir and is not steps_base_dir itself.
    try:
        rel_parts = step_dir.relative_to(steps_base_dir).parts
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)
    if rel_parts != (step_id,):
        console.print(f"[red]Error:[/red] Invalid step id '{step_id}'")
        raise typer.Exit(1)

    dir_exists = step_dir.exists()

    if not in_registry and not dir_exists:
        console.print(f"[red]Error:[/red] Step type '{step_id}' is not installed")
        raise typer.Exit(1)

    if not in_registry and dir_exists:
        # The registry was likely reset due to corruption.  Warn the user that the
        # directory is being removed even though there is no registry entry, so
        # the orphaned package can be cleaned up and a fresh install attempted.
        console.print(
            f"[yellow]Warning:[/yellow] '{step_id}' has no registry entry "
            "(registry may have been reset). Removing the orphaned directory."
        )

    if dir_exists and not in_registry:
        # No registry write needed; just delete the orphaned directory.
        import shutil
        try:
            shutil.rmtree(step_dir)
        except OSError as exc:
            console.print(
                f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
            )
            raise typer.Exit(1)
    elif in_registry:
        # Remove the registry entry, then the directory. If the directory
        # delete fails, restore the registry entry so state stays consistent
        # and a future `step add` isn't blocked by an orphaned directory
        # with no registry entry.
        registry_metadata = registry.get(step_id)
        try:
            registry.remove(step_id)
        except StepValidationError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)
        if dir_exists:
            import shutil
            try:
                shutil.rmtree(step_dir)
            except OSError as exc:
                # Restore the original registry entry verbatim (bypass add()
                # which would overwrite timestamps).
                try:
                    if registry_metadata is not None:
                        registry.data["steps"][step_id] = registry_metadata
                        registry.save()
                except Exception as restore_exc:  # noqa: BLE001
                    console.print(
                        f"[yellow]Warning:[/yellow] Failed to restore registry entry "
                        f"for '{step_id}' after directory removal failure: {restore_exc}"
                    )
                console.print(
                    f"[red]Error:[/red] Failed to remove step directory {step_dir}: {exc}"
                )
                raise typer.Exit(1)
    console.print(f"[green]✓[/green] Step type '{step_id}' uninstalled")


@workflow_step_app.command("search")
def workflow_step_search(
    query: str | None = typer.Argument(None, help="Search query"),
):
    """Search the step type catalog."""
    from .catalog import StepCatalog, StepCatalogError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)

    try:
        results = catalog.search(query=query)
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not results:
        if query:
            console.print(f"[yellow]No step types found matching '{query}'.[/yellow]")
        else:
            console.print("[yellow]No step types found in catalog.[/yellow]")
        return

    console.print(f"\n[bold cyan]Step Types ({len(results)}):[/bold cyan]\n")
    for step in results:
        install_note = (
            "" if step.get("_install_allowed", True) else " [dim](discovery only)[/dim]"
        )
        console.print(
            f"  [bold]{step.get('name', step.get('id', '?'))}[/bold]"
            f" ({step.get('id', '?')}) v{step.get('version', '?')}{install_note}"
        )
        desc = step.get("description", "")
        if desc:
            console.print(f"    {desc}")
        console.print()


@workflow_step_app.command("info")
def workflow_step_info(
    step_id: str = typer.Argument(..., help="Step type ID"),
):
    """Show details for a step type."""
    from . import STEP_REGISTRY
    from .catalog import StepCatalog, StepCatalogError, StepRegistry

    project_root = _require_specify_project()

    registry = StepRegistry(project_root)
    installed_meta = registry.get(step_id)

    # Check if it's a built-in
    builtin_step = STEP_REGISTRY.get(step_id)
    is_builtin = builtin_step is not None and not installed_meta

    if is_builtin:
        console.print(f"\n[bold cyan]{step_id}[/bold cyan] [dim](built-in)[/dim]")
        console.print(f"  Type key: {step_id}")
        console.print("  [green]Built-in step type[/green]")
        return

    if installed_meta:
        console.print(
            f"\n[bold cyan]{installed_meta.get('name', step_id)}[/bold cyan] ({step_id})"
        )
        console.print(f"  Version:     {installed_meta.get('version', '?')}")
        if installed_meta.get("author"):
            console.print(f"  Author:      {installed_meta['author']}")
        if installed_meta.get("description"):
            console.print(f"  Description: {installed_meta['description']}")
        console.print("  [green]Installed[/green]")
        return

    # Try catalog
    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError:
        info = None

    if info:
        console.print(
            f"\n[bold cyan]{info.get('name', step_id)}[/bold cyan] ({step_id})"
        )
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("author"):
            console.print(f"  Author:      {info['author']}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        console.print("  [yellow]Not installed[/yellow]")
        console.print(
            f"\n  Install with: [cyan]specify workflow step add {step_id}[/cyan]"
        )
    else:
        console.print(f"[red]Error:[/red] Step type '{step_id}' not found")
        raise typer.Exit(1)


@workflow_step_catalog_app.command("list")
def workflow_step_catalog_list():
    """List configured step catalog sources."""
    from .catalog import StepCatalog, StepCatalogError

    project_root = _require_specify_project()
    catalog = StepCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except StepCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Step Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = (
            "[green]install allowed[/green]"
            if cfg["install_allowed"]
            else "[yellow]discovery only[/yellow]"
        )
        console.print(f"  [{i}] [bold]{cfg['name']}[/bold] — {install_status}")
        console.print(f"      {cfg['url']}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@workflow_step_catalog_app.command("add")
def workflow_step_catalog_add(
    url: str = typer.Argument(..., help="Catalog URL to add"),
    name: str | None = typer.Option(None, "--name", help="Catalog name"),
):
    """Add a step catalog source."""
    from .catalog import StepCatalog, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        catalog.add_catalog(url, name)
    except StepValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Step catalog source added: {url}")


@workflow_step_catalog_app.command("remove")
def workflow_step_catalog_remove(
    index: int = typer.Argument(
        ..., help="Catalog index to remove (from 'step catalog list')"
    ),
):
    """Remove a step catalog source by index."""
    from .catalog import StepCatalog, StepValidationError

    project_root = _require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except StepValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Step catalog source '{removed_name}' removed")


def register(app: typer.Typer) -> None:
    """Attach the workflow command group to the root Typer app."""
    app.add_typer(workflow_app, name="workflow")
