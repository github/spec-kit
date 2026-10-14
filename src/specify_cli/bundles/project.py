"""Spec Kit project detection and active-integration resolution."""
from __future__ import annotations

from pathlib import Path

from .._project import (
    ProjectResolutionError,
    _resolve_init_dir_override_unrendered,
    render_project_error,
)
from .._file_policy import ProjectPolicyError, project_files
from ..integration_state import clean_integration_key, dedupe_integration_keys
from . import BundlerError
from .yamlio import ensure_within, load_json

DEFAULT_INTEGRATION = "copilot"


def find_project_root(start: Path | None = None) -> Path | None:
    """Return the nearest ancestor (incl. *start*) containing a ``.specify/`` dir, or None.

    A present ``.specify`` entry establishes the candidate boundary. Forbidden
    links/reparse entries, non-directory markers and corrupt policy fail there
    instead of silently selecting an ancestor. Only absent markers continue
    ancestor discovery.

    When *start* is ``None`` the ``SPECIFY_INIT_DIR`` override is honored first
    (see :func:`specify_cli._project._resolve_init_dir_override`). With an
    explicit override this may **raise** rather than return: a set-but-invalid
    value raises ``typer.Exit`` and a symlinked ``.specify`` raises
    ``BundlerError``. That is deliberate — returning ``None`` would let
    ``bundle init``/``install`` silently fall back to the current directory.
    """
    if start is None:
        try:
            override = _resolve_init_dir_override_unrendered()
        except ProjectResolutionError as exc:
            if isinstance(exc.__cause__, ProjectPolicyError):
                raise BundlerError(str(exc)) from exc.__cause__
            render_project_error(exc)
        if override is not None:
            # An explicit override is strict: do not return None here, because
            # bundle install treats None as "init the current directory".
            return override

    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        marker = candidate / ".specify"
        try:
            marker.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            error = ProjectPolicyError(f"Cannot inspect project marker {marker}: {exc}")
            raise BundlerError(str(error)) from error
        _preflight_policy(candidate)
        return candidate
    return None


def _preflight_policy(root: Path) -> None:
    try:
        project_files(root)
    except ProjectPolicyError as exc:
        raise BundlerError(str(exc)) from exc


def require_project_root(start: Path | None = None) -> Path:
    """Return the Spec Kit project root or raise an actionable error.

    Inherits :func:`find_project_root`'s override behavior: when *start* is
    ``None``, a set-but-invalid ``SPECIFY_INIT_DIR`` raises ``typer.Exit`` and a
    symlinked ``.specify`` raises ``BundlerError`` before this returns. A missing
    project (no override) raises ``BundlerError``.
    """
    root = find_project_root(start)
    if root is None:
        raise BundlerError(
            "Not a Spec Kit project (no .specify/ directory). "
            "Run 'specify bundle init' or 'specify init' first."
        )
    return root


def active_integration(project_root: Path) -> str | None:
    """Return the project's active integration id, if recorded.

    Spec Kit records the chosen integration in ``.specify/integration.json``
    during init. Returns None when it cannot be determined (e.g. agnostic).
    """
    marker = Path(project_root) / ".specify" / "integration.json"
    # Confine the read (mirrors records/catalog IO): refuse to follow a
    # symlinked or traversal-escaping .specify that resolves outside
    # project_root. An escape is treated as "not determinable".
    try:
        marker = ensure_within(project_root, marker)
    except BundlerError:
        return None
    if not marker.exists():
        return None
    try:
        data = load_json(marker)
    except BundlerError:
        return None
    if isinstance(data, dict):
        # Resolve the way the canonical path does: normalize first
        # (``normalize_integration_state``), then read the default
        # (``default_integration_key``). ``default_integration_key`` alone is
        # not that reader -- it expects *normalized* state, and on a raw marker
        # its ``state.get("default_integration") or state.get("integration")``
        # picks a whitespace-only default (truthy) over a valid legacy key
        # behind it.
        #
        # ``default_integration`` is authoritative; ``integration`` (the legacy
        # alias ``write_integration_json`` also writes), then ``id``/``active``,
        # are fallbacks. Clean EACH candidate before selecting it, as
        # ``normalize_integration_state`` does with
        # ``clean_integration_key(data.get("default_integration")) or
        # legacy_key``, rather than picking the first truthy raw value and
        # normalizing only that one:
        #     {"default_integration": "   ", "integration": "copilot"}
        #         raw-then-clean -> None      canonical -> 'copilot'
        #
        # Normalizing through the shared helper also fixes the original
        # divergence: ``isinstance(value, str) and value`` accepted a
        # whitespace-only key as real -- truthy, so it suppressed the "not
        # determinable" fallback -- and returned a padded key verbatim, which
        # matches no registered integration.
        for field in ("default_integration", "integration", "id", "active"):
            cleaned = clean_integration_key(data.get(field))
            if cleaned:
                return cleaned
        # Installed-only state -- ``installed_integrations`` populated but no
        # default recorded -- still has an active integration: the canonical
        # ``normalize_integration_state`` promotes ``installed_integrations[0]``
        # to the default. Returning None here instead told callers the
        # integration "cannot be determined", which lets an explicit
        # ``--integration`` bypass the FR-019 integration-clash guard in
        # ``bundle install`` / ``bundle update``. Checked last, so a marker
        # that already resolved through the fields above is unaffected.
        installed = data.get("installed_integrations")
        if isinstance(installed, list):
            installed_keys = dedupe_integration_keys(installed)
            if installed_keys:
                return installed_keys[0]
    return None
