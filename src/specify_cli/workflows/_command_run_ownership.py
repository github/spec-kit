"""Run-private installed-workflow ownership resolution."""

from __future__ import annotations

import os
from pathlib import Path

from . import _commands as cli


def _same_existing_path(left: Path, right: Path) -> bool:
    """Return whether two existing paths identify the same filesystem entry."""
    try:
        return os.path.samefile(left, right)
    except OSError:
        return left == right


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
        cli._reject_unsafe_dir(canonical_specify, ".specify")
        cli._reject_unsafe_dir(canonical_workflows, ".specify/workflows")
        cli._reject_unsafe_dir(candidate_specify, ".specify")
        cli._reject_unsafe_dir(candidate_workflows, ".specify/workflows")
        try:
            if not os.path.samefile(candidate_specify, canonical_specify):
                return None
            if not os.path.samefile(
                candidate_workflows, canonical_workflows
            ):
                return None
        except OSError:
            return None
        registry = cli._open_workflow_registry(registry_root, err)
        registered_id = None
        for workflow_id in registry.list():
            if (
                not isinstance(workflow_id, str)
                or workflow_id in cli._RESERVED_WORKFLOW_IDS
                or not cli._WORKFLOW_ID_PATTERN.fullmatch(workflow_id)
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
                    f".specify/workflows/{cli._escape_markup(registered_id)} "
                    "contains a symlinked path component"
                )
                raise cli.typer.Exit(1)
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
