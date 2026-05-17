"""Version checking and self-update commands for specify_cli.

Pure helpers for comparing PEP 440 versions and fetching the latest GitHub
release tag.  The ``self_app`` Typer sub-command group is co-located here so
all version-related logic lives in one place.

Dependencies: stdlib + packaging + ._console only (no other internal imports
at module level, keeping this layer thin and circular-import-safe).
"""
from __future__ import annotations

import errno
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from packaging.version import InvalidVersion, Version

from ._console import console

GITHUB_API_LATEST = "https://api.github.com/repos/github/spec-kit/releases/latest"


def _get_installed_version() -> str:
    """Return the installed specify-cli distribution version or 'unknown'.

    Uses importlib.metadata so the value reflects what was actually installed
    by pip/uv/pipx — not a value read from pyproject.toml. This is
    intentional for `specify self check`, which should reason about the
    installed distribution rather than a source-tree fallback. Callers must
    treat the sentinel string 'unknown' as an indeterminate value (see FR-020).
    """
    import importlib.metadata

    metadata_errors = [importlib.metadata.PackageNotFoundError]
    invalid_metadata_error = getattr(importlib.metadata, "InvalidMetadataError", None)
    if invalid_metadata_error is not None:
        metadata_errors.append(invalid_metadata_error)

    try:
        return importlib.metadata.version("specify-cli")
    except tuple(metadata_errors):
        return "unknown"


def _normalize_tag(tag: str) -> str:
    """Strip exactly one leading 'v' from a release tag.

    Returns the rest of the string unchanged. This handles the common
    'vX.Y.Z' tag convention in this repo; it MUST NOT strip more
    aggressively (e.g., two leading 'v's keeps one).
    """
    return tag[1:] if tag.startswith("v") else tag


def _is_newer(latest: str, current: str) -> bool:
    """Return True iff `latest` is strictly greater than `current` under PEP 440.

    Returns False whenever either side is 'unknown' or fails to parse; this
    keeps the comparison indeterminate (rather than crashing or falsely
    recommending a downgrade) on edge inputs.
    """
    if latest == "unknown" or current == "unknown":
        return False
    try:
        return Version(latest) > Version(current)
    except InvalidVersion:
        return False


def _fetch_latest_release_tag() -> tuple[str | None, str | None]:
    """Return (tag, failure_category). Exactly one outbound call, 5 s timeout.

    On success: (tag_name, None).
    On a documented network/HTTP failure (added in T029/T030): (None, category).
    On anything else — including a malformed response body — the exception
    propagates; there is no catch-all (research D-006).
    """
    from .authentication.http import open_url

    try:
        with open_url(
            GITHUB_API_LATEST,
            timeout=5,
            extra_headers={"Accept": "application/vnd.github+json"},
        ) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            tag = payload.get("tag_name")
            if not isinstance(tag, str) or not tag:
                raise ValueError("GitHub API response missing valid tag_name")
            return tag, None
    except urllib.error.HTTPError as e:
        # Order matters: HTTPError is a subclass of URLError.
        if e.code == 403:
            return None, (
                "rate limited (configure ~/.specify/auth.json with a GitHub token)"
            )
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, OSError):
        return None, "offline or timeout"


def _canonicalize_version_text(value: str) -> str:
    """Normalize version-like text for equality checks when parseable."""
    normalized = _normalize_tag(value)
    try:
        return str(Version(normalized))
    except InvalidVersion:
        return normalized


def _stable_release_tag_for_version(version_text: str) -> str | None:
    """Return `vX.Y.Z` only for exact stable release versions."""
    try:
        parsed = Version(version_text)
    except InvalidVersion:
        return None
    if parsed.pre or parsed.post or parsed.dev or parsed.local:
        return None
    release = parsed.release
    if len(release) != 3:
        return None
    return f"v{release[0]}.{release[1]}.{release[2]}"


def _is_comparable_version_text(value: str) -> bool:
    """Return whether version-like text parses under PEP 440 after tag normalization."""
    try:
        Version(_normalize_tag(value))
        return True
    except InvalidVersion:
        return False


def _render_argv(argv: list[str]) -> str:
    """Render argv for copy/paste on the current platform."""
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


_INSTALLER_PATH_PREFIXES: dict[str, list[str]] = {
    "uv-tool": [
        "~/.local/share/uv/tools/specify-cli/",
        "%LOCALAPPDATA%\\uv\\tools\\specify-cli\\",
    ],
    "pipx": [
        "~/.local/pipx/venvs/specify-cli/",
        "%LOCALAPPDATA%\\pipx\\venvs\\specify-cli\\",
    ],
    "uvx-ephemeral": [
        "~/.cache/uv/archive-v0/",
        "%LOCALAPPDATA%\\uv\\cache\\archive-v0\\",
    ],
}

_RESOLUTION_FAILURE_CATEGORIES: frozenset[str] = frozenset(
    {
        "offline or timeout",
        "rate limited (configure ~/.specify/auth.json with a GitHub token)",
    }
)

# Internal subprocess sentinels deliberately sit outside real POSIX exit-code
# space; callers must map them to documented user-facing exit codes.
_INSTALLER_INVALID_SENTINEL = 900126
_INSTALLER_TIMEOUT_SENTINEL = 900124


class _InstallMethod(str, Enum):
    """Install-method classification for `specify self upgrade`."""

    UV_TOOL = "uv-tool"
    PIPX = "pipx"
    UVX_EPHEMERAL = "uvx-ephemeral"
    SOURCE_CHECKOUT = "source-checkout"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class _UpgradePlan:
    """Resolved upgrade decision shared by preview and apply paths."""

    method: _InstallMethod
    current_version: str
    target_tag: str | None
    installer_argv: list[str] | None
    preview_summary: str
    pre_upgrade_snapshot: str


@dataclass(frozen=True)
class _DetectionSignals:
    """Test-only record of which detection tier fired."""

    sys_argv0: str
    matched_tier: int | None
    matched_prefix: str | None
    editable_marker_seen: bool
    installer_registries_consulted: list[str]
    resolved_method: _InstallMethod


_SCRUBBED_ENV_KEYS: frozenset[str] = frozenset(
    {
        "GH_TOKEN",
        "GH_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
        "GITHUB_ENTERPRISE_TOKEN",
        "GITHUB_API_TOKEN",
    }
)


def _scrubbed_env() -> dict[str, str]:
    """Return a copy of `os.environ` without known GitHub credential keys."""

    return {
        k: v
        for k, v in os.environ.items()
        if k.upper() not in _SCRUBBED_ENV_KEYS
        and not re.match(r"^(GH_.*TOKEN|.*GITHUB.*TOKEN)$", k.upper())
    }


_TAG_REGEX = re.compile(
    r"^v\d+\.\d+\.\d+"
    r"(?:(?:\.?dev\d+)|(?:[-.]?(?:a|b|rc|alpha|beta)\d+)|"
    r"(?:\+[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*))?$"
)


def _validate_tag(tag: str) -> str:
    """Validate a user-supplied --tag value.

    Accepts vX.Y.Z plus optional PEP-440-ish suffix (dev0, rc1, beta.1,
    +build.42). Rejects everything else (including bare 'latest', hash refs,
    branch names, or a numeric version without the 'v' prefix).
    """
    tag = tag.strip()
    if not tag:
        raise typer.BadParameter("Invalid --tag: expected vMAJOR.MINOR.PATCH[suffix]")
    if not _TAG_REGEX.match(tag):
        raise typer.BadParameter("Invalid --tag: expected vMAJOR.MINOR.PATCH[suffix]")
    try:
        Version(_normalize_tag(tag))
    except InvalidVersion as exc:
        raise typer.BadParameter(
            "Invalid --tag: expected vMAJOR.MINOR.PATCH[suffix]"
        ) from exc

    return tag


def _expand_prefix(prefix: str) -> Path | None:
    """Expand `~` or `%LOCALAPPDATA%`-style tokens in a path prefix."""

    expanded = os.path.expanduser(prefix)
    if "%LOCALAPPDATA%" in expanded:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            return None
        expanded = expanded.replace("%LOCALAPPDATA%", local_app_data)
    expanded = os.path.expandvars(expanded)
    if "%" in expanded or "$" in expanded:
        return None
    return Path(expanded).resolve() if Path(expanded).is_absolute() else Path(expanded)


def _path_is_within_prefix(path: Path, prefix: Path) -> bool:
    """Return whether absolute `path` is under absolute `prefix`."""
    if not path.is_absolute() or not prefix.is_absolute():
        return False
    try:
        common = os.path.commonpath(
            [os.path.normcase(str(path)), os.path.normcase(str(prefix))]
        )
    except ValueError:
        return False
    return common == os.path.normcase(str(prefix))


def _resolved_argv0_path(argv0: str | None = None) -> Path:
    """Resolve the running entrypoint path, consulting PATH for bare commands."""
    raw = argv0 or sys.argv[0]
    candidate = Path(raw)
    if not candidate.is_absolute() and len(candidate.parts) == 1:
        resolved = shutil.which(raw) or shutil.which("specify")
        if resolved:
            return Path(resolved).resolve()
        return candidate
    return candidate.resolve()


def _looks_like_specify_entrypoint(path: Path) -> bool:
    """Return whether a path looks like the `specify` CLI entrypoint."""
    return path.name.lower() in {"specify", "specify.exe", "specify-cli", "specify-cli.exe"}


def _tier3_registry_lookup_allowed(argv0_path: Path) -> bool:
    """Return whether tier-3 registry reconciliation is safe for this entrypoint."""
    return argv0_path.is_absolute() and not argv0_path.exists()


def _uv_tool_list_contains_specify_cli(stdout: str) -> bool:
    """Return whether `uv tool list` output includes an exact `specify-cli` entry."""
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        first_token = line.split(None, 1)[0]
        if first_token == "specify-cli":
            return True
    return False


def _git_ancestor(path: Path) -> Path | None:
    """Return the closest ancestor that looks like a git worktree root."""
    for ancestor in [path, *path.parents]:
        if (ancestor / ".git").exists():
            return ancestor
    return None


def _editable_direct_url_path() -> Path | None:
    """Return the editable checkout root recorded in direct_url.json, if any."""
    import importlib.metadata as _md

    try:
        dist = _md.distribution("specify-cli")
    except _md.PackageNotFoundError:
        return None

    payload = dist.read_text("direct_url.json")
    if not payload:
        return None

    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return None

    if not data.get("dir_info", {}).get("editable"):
        return None

    url = data.get("url")
    if not isinstance(url, str):
        return None

    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "file":
        return None

    url_path = urllib.request.url2pathname(urllib.parse.unquote(parsed.path))
    if parsed.netloc and parsed.netloc not in {"", "localhost"}:
        url_path = f"//{parsed.netloc}{url_path}"

    try:
        return Path(url_path).resolve()
    except OSError:
        return None


def _editable_marker_seen() -> bool:
    """Return whether the installed distribution is explicitly marked editable."""
    editable_root = _editable_direct_url_path()
    return editable_root is not None and _git_ancestor(editable_root) is not None


def _detect_install_method(
    argv0: str | None = None,
    include_signals: bool = False,
) -> "_InstallMethod | tuple[_InstallMethod, _DetectionSignals]":
    """Classify the current runtime into exactly one _InstallMethod.

    Detection order:
      1. `sys.argv[0]` path prefix match against `_INSTALLER_PATH_PREFIXES`
      2. editable-install marker
      3. installer registry reconciliation (`uv tool list` / `pipx list`)

    When `include_signals=True`, also return `_DetectionSignals`.
    """
    argv0_path = _resolved_argv0_path(argv0)
    argv0_resolved = str(argv0_path)

    # --- Tier 1: path prefix match ---
    for method_str, prefixes in _INSTALLER_PATH_PREFIXES.items():
        for prefix in prefixes:
            expanded = _expand_prefix(prefix)
            if expanded is None:
                continue
            if _path_is_within_prefix(argv0_path, expanded):
                method = _InstallMethod(method_str)
                if include_signals:
                    return method, _DetectionSignals(
                        sys_argv0=argv0_resolved,
                        matched_tier=1,
                        matched_prefix=prefix,
                        editable_marker_seen=False,
                        installer_registries_consulted=[],
                        resolved_method=method,
                    )
                return method

    # --- Tier 2: editable install marker ---
    if _editable_marker_seen():
        method = _InstallMethod.SOURCE_CHECKOUT
        if include_signals:
            return method, _DetectionSignals(
                sys_argv0=argv0_resolved,
                matched_tier=2,
                matched_prefix=None,
                editable_marker_seen=True,
                installer_registries_consulted=[],
                resolved_method=method,
            )
        return method

    # --- Tier 3: PATH + registry reconciliation ---
    consulted: list[str] = []
    if _tier3_registry_lookup_allowed(argv0_path):
        uv_tool_match = False
        uv_bin = shutil.which("uv")
        if uv_bin is not None:
            consulted.append("uv tool list")
            try:
                result = subprocess.run(
                    [uv_bin, "tool", "list"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env=_scrubbed_env(),
                    check=False,
                )
                if result.returncode == 0 and _uv_tool_list_contains_specify_cli(
                    result.stdout or ""
                ):
                    uv_tool_match = True
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass

        pipx_match = False
        pipx_bin = shutil.which("pipx")
        if pipx_bin is not None:
            consulted.append("pipx list --json")
            try:
                result = subprocess.run(
                    [pipx_bin, "list", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env=_scrubbed_env(),
                    check=False,
                )
                if result.returncode == 0:
                    payload = json.loads(result.stdout or "")
                    venvs = payload.get("venvs") if isinstance(payload, dict) else None
                    if isinstance(venvs, dict) and "specify-cli" in venvs:
                        pipx_match = True
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass

        # If both registries claim ownership, the active entrypoint is ambiguous.
        # Treat it as unsupported rather than guessing and upgrading the wrong install.
        exactly_one_match = uv_tool_match != pipx_match
        if exactly_one_match:
            method = _InstallMethod.UV_TOOL if uv_tool_match else _InstallMethod.PIPX
            if include_signals:
                return method, _DetectionSignals(
                    sys_argv0=argv0_resolved,
                    matched_tier=3,
                    matched_prefix=None,
                    editable_marker_seen=False,
                    installer_registries_consulted=consulted,
                    resolved_method=method,
                )
            return method

    # Fallthrough
    method = _InstallMethod.UNSUPPORTED
    if include_signals:
        return method, _DetectionSignals(
            sys_argv0=argv0_resolved,
            matched_tier=None,
            matched_prefix=None,
            editable_marker_seen=False,
            installer_registries_consulted=consulted,
            resolved_method=method,
        )
    return method


_GITHUB_SOURCE_URL = "git+https://github.com/github/spec-kit.git"
_MANUAL_TAG_PLACEHOLDER = "vX.Y.Z"


def _source_spec(target_tag: str | None) -> str:
    """Build a git source spec, optionally pinned to a release tag."""
    return f"{_GITHUB_SOURCE_URL}@{target_tag}" if target_tag else _GITHUB_SOURCE_URL


def _manual_source_spec(target_tag: str | None) -> str:
    """Build a stable-release-oriented source spec for manual guidance."""
    return f"{_GITHUB_SOURCE_URL}@{target_tag or _MANUAL_TAG_PLACEHOLDER}"


def _assemble_installer_argv(
    method: _InstallMethod, target_tag: str | None
) -> list[str] | None:
    """Build the installer argv for an upgradable install method."""
    source_spec = _source_spec(target_tag)

    if method == _InstallMethod.UV_TOOL:
        uv_bin = shutil.which("uv") or "uv"  # resolve at invocation time too
        return [
            uv_bin,
            "tool",
            "install",
            "specify-cli",
            "--force",
            "--from",
            source_spec,
        ]

    if method == _InstallMethod.PIPX:
        # pipx 1.5+ removed `--spec`; PACKAGE_SPEC is now positional and the
        # package name is auto-detected from the source's pyproject.toml.
        pipx_bin = shutil.which("pipx") or "pipx"
        return [
            pipx_bin,
            "install",
            "--force",
            source_spec,
        ]

    return None


def _method_label(method: _InstallMethod) -> str:
    """Render the user-facing label for an install method."""
    return {
        _InstallMethod.UV_TOOL: "uv tool",
        _InstallMethod.PIPX: "pipx",
        _InstallMethod.UVX_EPHEMERAL: "uvx (ephemeral)",
        _InstallMethod.SOURCE_CHECKOUT: "source checkout",
        _InstallMethod.UNSUPPORTED: "unsupported",
    }[method]


def _build_upgrade_plan(
    target_tag_override: str | None,
) -> tuple[_UpgradePlan | None, str | None]:
    """Return a resolved upgrade plan or `(None, failure_reason)`.

    A valid `target_tag_override` skips network resolution entirely.
    """
    method = _detect_install_method()

    if target_tag_override is not None:
        target_tag = target_tag_override
    elif method in (_InstallMethod.UV_TOOL, _InstallMethod.PIPX):
        tag, failure_reason = _fetch_latest_release_tag()
        if tag is None:
            return None, failure_reason  # surfaces as exit 1 in the orchestrator
        target_tag = tag
    else:
        target_tag = None

    current = _get_installed_version()
    argv = _assemble_installer_argv(method, target_tag)

    preview = (
        f"Detected install method: {_method_label(method)}\n"
        f"Current version: {current}\n"
        f"Target version: {target_tag or '(not resolved for this install method)'}\n"
        f"Command that would be executed: "
        f"{_render_argv(argv) if argv is not None else '(none — non-upgradable path)'}"
    )

    plan = _UpgradePlan(
        method=method,
        current_version=current,
        target_tag=target_tag,
        installer_argv=argv,
        preview_summary=preview,
        pre_upgrade_snapshot=current,
    )
    return plan, None


def _warn_invalid_upgrade_timeout(timeout_raw: str) -> None:
    """Warn that SPECIFY_UPGRADE_TIMEOUT_SECS could not be applied."""
    console.print(
        f"Ignoring invalid SPECIFY_UPGRADE_TIMEOUT_SECS={timeout_raw!r}; "
        "running without a timeout.",
        soft_wrap=True,
    )


def _installer_invalid_result(plan: _UpgradePlan) -> subprocess.CompletedProcess:
    """Return the internal marker for an installer path that cannot execute."""
    return subprocess.CompletedProcess(
        args=plan.installer_argv,
        returncode=_INSTALLER_INVALID_SENTINEL,
        stdout=None,
        stderr=None,
    )


def _run_installer(plan: _UpgradePlan) -> subprocess.CompletedProcess | None:
    """Invoke the installer subprocess.

    Returns None if the installer binary is not found on PATH. Returns a
    synthetic CompletedProcess with returncode=`_INSTALLER_INVALID_SENTINEL`
    when an absolute installer path exists but is not executable or not a
    regular file. Returns a CompletedProcess for every other case including
    non-zero exit — caller inspects returncode.

    stdout/stderr are inherited (not captured) so the user sees installer
    progress in real time. The child environment has GH_TOKEN /
    GITHUB_TOKEN removed.

    Timeout: by default the subprocess runs with no timeout — installer
    operations (dependency resolution, large wheel downloads) can legitimately
    take many minutes. Set the env var SPECIFY_UPGRADE_TIMEOUT_SECS to an
    integer/float to enforce a hard cap; on timeout we return a synthetic
    CompletedProcess with returncode=`_INSTALLER_TIMEOUT_SENTINEL`, which the
    orchestrator maps to user-facing exit code `124`. An unparseable or
    non-positive value emits a warning and runs without a timeout.
    """
    if plan.installer_argv is None:
        # Internal routing error: the orchestrator must route non-upgradable
        # methods to _emit_guidance and never reach this function. Use a real
        # raise (not assert) so the guard survives `python -O`.
        raise RuntimeError(
            "internal routing error: _run_installer received a plan without an "
            "installer_argv (non-upgradable methods must route to _emit_guidance)"
        )

    # Use the argv assembled at plan-build time verbatim. The pre-execution
    # notice and the actual subprocess argv must be byte-for-byte identical;
    # any re-resolution here would risk diverging from what the user just
    # saw printed. A lightweight pre-flight via `shutil.which` short-circuits
    # the obvious "binary disappeared" case before spawning, and the
    # try/except below catches the residual race window.
    installer_cmd = Path(plan.installer_argv[0])
    if installer_cmd.is_absolute():
        if installer_cmd.exists() and (
            not installer_cmd.is_file() or not os.access(installer_cmd, os.X_OK)
        ):
            return _installer_invalid_result(plan)
    elif shutil.which(plan.installer_argv[0]) is None:
        return None  # signals installer-missing to caller

    timeout_raw = os.environ.get("SPECIFY_UPGRADE_TIMEOUT_SECS")
    timeout: float | None = None
    if timeout_raw is not None:
        try:
            timeout = float(timeout_raw)
            if timeout <= 0:
                _warn_invalid_upgrade_timeout(timeout_raw)
                timeout = None
        except ValueError:
            _warn_invalid_upgrade_timeout(timeout_raw)
            timeout = None

    try:
        return subprocess.run(
            plan.installer_argv,
            shell=False,
            check=False,
            env=_scrubbed_env(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        # Surface as installer-failed via a synthetic CompletedProcess with a
        # non-zero exit code so the orchestrator's installer-failed path emits
        # the manual-retry argv + rollback hint.
        return subprocess.CompletedProcess(
            args=plan.installer_argv,
            returncode=_INSTALLER_TIMEOUT_SENTINEL,
            stdout=None,
            stderr=None,
        )
    except FileNotFoundError:
        return None  # disappeared between pre-flight and exec
    except (PermissionError, IsADirectoryError):
        return _installer_invalid_result(plan)
    except OSError as exc:
        if exc.errno in {errno.EACCES, errno.ENOEXEC, errno.EISDIR}:
            return _installer_invalid_result(plan)
        raise


_VERIFY_VERSION_REGEX = re.compile(r"specify (\S+)")


def _verify_upgrade(plan: _UpgradePlan) -> str | None:
    """Spawn a child `specify --version` and parse its output.

    Returns the version string on success, None on parse failure, timeout,
    or missing binary. Caller compares the returned version to plan.target_tag
    and raises verification-mismatch if they differ.

    Uses a child process (not in-process importlib.metadata) because Python
    cannot hot-swap the running module after the installer has replaced it —
    only a fresh process picks up the new binary.
    """
    argv0 = _resolved_argv0_path()
    specify_bin = (
        str(argv0)
        if (
            argv0.exists()
            and argv0.is_file()
            and os.access(argv0, os.X_OK)
            and _looks_like_specify_entrypoint(argv0)
        )
        else shutil.which("specify")
    )
    if specify_bin is None:
        return None
    try:
        result = subprocess.run(
            [specify_bin, "--version"],
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env=_scrubbed_env(),
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    match = _VERIFY_VERSION_REGEX.search(result.stdout or "")
    return match.group(1) if match else None


def _source_checkout_path() -> Path | None:
    """Return the working-tree root for an editable install when discoverable."""
    import importlib.metadata as _md

    editable_root = _editable_direct_url_path()
    if editable_root is not None:
        git_root = _git_ancestor(editable_root)
        if git_root is not None:
            return git_root

    try:
        dist = _md.distribution("specify-cli")
    except _md.PackageNotFoundError:
        return None
    files = dist.files or []
    for f in files:
        try:
            abs_path = Path(dist.locate_file(f)).resolve()
        except Exception:
            continue
        git_root = _git_ancestor(abs_path)
        if git_root is not None:
            return git_root
    return None


def _emit_guidance(method: _InstallMethod, target_tag: str | None) -> None:
    """Print path-specific guidance for non-upgradable install methods."""
    if method == _InstallMethod.UVX_EPHEMERAL:
        console.print(
            "Running via uvx (ephemeral); the next uvx invocation already "
            "resolves to latest — no upgrade action needed.",
            soft_wrap=True,
        )
        return

    if method == _InstallMethod.SOURCE_CHECKOUT:
        tree = _source_checkout_path()
        tree_str = str(tree) if tree else "(path unavailable)"
        console.print(
            f"Running from a source checkout at {tree_str}; "
            "upgrade by running the following commands from that directory:",
            soft_wrap=True,
        )
        console.print("  git pull")
        console.print("  pip install -e .")
        return

    if method == _InstallMethod.UNSUPPORTED:
        console.print(
            "Could not identify your install method automatically; "
            "run one of the following manually:",
            soft_wrap=True,
        )
        console.print(
            f"  uv tool install specify-cli --force --from "
            f"{_manual_source_spec(target_tag)}",
            soft_wrap=True,
        )
        console.print(
            f"  pipx install --force {_manual_source_spec(target_tag)}",
            soft_wrap=True,
        )
        return

    raise RuntimeError(
        f"internal routing error: _emit_guidance called on upgradable method: {method}"
    )


def _rollback_hint(plan: _UpgradePlan) -> str:
    """Build a manual rollback suggestion from the pre-upgrade version."""
    if plan.pre_upgrade_snapshot == "unknown":
        return (
            "Could not determine the previous version; "
            "reinstall manually from: https://github.com/github/spec-kit/releases"
        )
    rollback_tag = _stable_release_tag_for_version(plan.pre_upgrade_snapshot)
    if rollback_tag is None:
        return (
            "Previous version was not an exact stable release tag; "
            "reinstall manually from: https://github.com/github/spec-kit/releases"
        )
    if plan.method == _InstallMethod.PIPX:
        return (
            f"To pin back to the previous version: pipx install --force "
            f"git+https://github.com/github/spec-kit.git@{rollback_tag}"
        )
    return (
        f"To pin back to the previous version: uv tool install specify-cli --force "
        f"--from git+https://github.com/github/spec-kit.git@{rollback_tag}"
    )


def _emit_failure(
    category: str,
    plan: _UpgradePlan | None = None,
    installer_exit: int | None = None,
    installer_name: str | None = None,
    verified_version: str | None = None,
) -> None:
    """Render user-facing output for resolver, installer, or verification failures."""
    if (
        category in _RESOLUTION_FAILURE_CATEGORIES
        or category.startswith("HTTP ")
    ):
        console.print(f"Upgrade aborted: {category}", soft_wrap=True)
        return

    if category == "installer-missing":
        if installer_name and os.path.isabs(installer_name):
            console.print(
                f"Installer path {installer_name} no longer exists; reinstall it and retry.",
                soft_wrap=True,
            )
        else:
            name = installer_name or "(unknown)"
            console.print(
                f"Installer {name} not found on PATH; reinstall it and retry.",
                soft_wrap=True,
            )
        return

    if category == "installer-invalid":
        if installer_name and os.path.isabs(installer_name):
            console.print(
                f"Installer path {installer_name} is not an executable file; fix the path or reinstall it and retry.",
                soft_wrap=True,
            )
        else:
            name = installer_name or "(unknown)"
            console.print(
                f"Installer {name} is not an executable file; fix the path or reinstall it and retry.",
                soft_wrap=True,
            )
        return

    if category == "target-tag-unparseable":
        if plan is None:
            raise RuntimeError(
                "internal routing error: target-tag-unparseable requires plan to be set"
            )
        console.print(
            f"Upgrade aborted: resolved release tag {plan.target_tag!r} is not a comparable version.",
            soft_wrap=True,
        )
        console.print(
            "Try again later or pin a stable release with --tag vX.Y.Z.",
            soft_wrap=True,
        )
        return

    if category == "installer-failed":
        if plan is None or installer_exit is None:
            raise RuntimeError(
                "internal routing error: installer-failed requires both "
                "plan and installer_exit to be set"
            )
        argv_str = _render_argv(plan.installer_argv) if plan.installer_argv else ""
        if installer_exit == _INSTALLER_TIMEOUT_SENTINEL:
            timeout_value = os.environ.get("SPECIFY_UPGRADE_TIMEOUT_SECS", "(unknown)")
            console.print(
                "Upgrade timed out while waiting for the installer subprocess.",
                soft_wrap=True,
            )
            console.print(
                f"Configured timeout: SPECIFY_UPGRADE_TIMEOUT_SECS={timeout_value}",
                soft_wrap=True,
            )
            console.print(
                f"Try again or run the command manually: {argv_str}",
                soft_wrap=True,
            )
            console.print(_rollback_hint(plan), soft_wrap=True)
            return
        console.print(
            f"Upgrade failed. Installer exit code: {installer_exit}.",
            soft_wrap=True,
        )
        console.print(
            f"Try again or run the command manually: {argv_str}",
            soft_wrap=True,
        )
        console.print(_rollback_hint(plan), soft_wrap=True)
        return

    if category == "verification-mismatch":
        if plan is None:
            raise RuntimeError(
                "internal routing error: verification-mismatch requires plan to be set"
            )
        verified_str = verified_version or "(unknown)"
        console.print(
            f"Verification failed: installer reported success but "
            f"'specify --version' resolves to {verified_str} "
            f"(expected {plan.target_tag}).",
            soft_wrap=True,
        )
        console.print(
            "The new version may take effect on your next invocation.",
            soft_wrap=True,
        )
        return

    raise RuntimeError(f"Unknown failure category: {category!r}")


# ===== Self Commands =====
self_app = typer.Typer(
    name="self",
    help=(
        "Manage the specify CLI itself: check for newer releases, "
        "preview upgrades with --dry-run, and upgrade in place."
    ),
    add_completion=False,
)


@self_app.command("check")
def self_check() -> None:
    """Check whether a newer specify-cli release is available. Read-only.

    This command only checks for updates; it does not modify your installation.
    Use `specify self upgrade` to actually perform the upgrade once you've seen
    the result here, or `specify self upgrade --dry-run` to preview the
    installer command without running it.
    """

    installed = _get_installed_version()
    tag, failure_reason = _fetch_latest_release_tag()

    if tag is None:
        # Graceful-failure path (FR-008). `failure_reason` is one of the
        # enumerated strings produced by _fetch_latest_release_tag() — it
        # never contains a URL, headers, response body, or traceback.
        assert failure_reason is not None
        console.print(f"Installed: {installed}")
        console.print(f"[yellow]Could not check latest release:[/yellow] {failure_reason}")
        return

    latest_normalized = _normalize_tag(tag)

    if installed == "unknown":
        # FR-020: surface the latest release and the recovery action even
        # when the local distribution metadata is unavailable.
        console.print("Current version could not be determined.")
        console.print(f"Latest release: {latest_normalized}")
        console.print("\nManual fallback:")
        console.print(f"  uv tool install specify-cli --force --from {_manual_source_spec(tag)}")
        console.print(f"  pipx install --force {_manual_source_spec(tag)}")
        console.print("\nIf this install can still be detected:")
        console.print("  specify self upgrade")
        return

    if _is_newer(latest_normalized, installed):
        console.print(f"[green]Update available:[/green] {installed} → {latest_normalized}")
        console.print("\nTo upgrade:")
        console.print("  specify self upgrade")
        console.print("\nManual fallback:")
        console.print(f"  uv tool install specify-cli --force --from {_manual_source_spec(tag)}")
        console.print(f"  pipx install --force {_manual_source_spec(tag)}")
        return

    # Installed is parseable AND is >= latest → "up to date" (FR-006).
    # Also reached when the tag is unparseable (InvalidVersion) → _is_newer
    # returns False, and the up-to-date branch is the safer default per
    # FR-004 / test T016.
    console.print(f"[green]Up to date:[/green] {installed}")


@self_app.command("upgrade")
def self_upgrade(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the preview (method, current, target, installer argv) and "
        "exit 0 without launching the installer subprocess.",
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        help="Pin the target version (vX.Y.Z[suffix]). Without --tag, the "
        "latest stable release is resolved via GitHub Releases.",
    ),
) -> None:
    """Upgrade specify-cli to the latest release (or a pinned --tag).

    Bare invocation executes immediately with no confirmation prompt, matching
    pip install -U / uv tool upgrade / npm update conventions. Use --dry-run
    to preview without mutating anything. See `specify self check` for the
    non-destructive read-only counterpart.

    Detection classifies the runtime into uv-tool / pipx / uvx (ephemeral) /
    source-checkout / unsupported. Only uv-tool and pipx are upgraded
    automatically; the other three paths print path-specific guidance and
    exit 0.

    Exit codes:
      0      success or no-op-success (already on latest, --dry-run, or
             non-upgradable path with guidance shown)
      1      target-tag resolution failure or --tag regex validation failure
      2      verification mismatch (installer exited 0 but `specify --version`
             does not resolve to the target tag)
      3      installer binary not found on PATH, or resolved installer path is
             missing / non-executable
      124    internal installer timeout when SPECIFY_UPGRADE_TIMEOUT_SECS is set,
             or a real installer exit code 124 propagated verbatim
      other  installer exit code propagated verbatim

    Environment variables:
      SPECIFY_UPGRADE_TIMEOUT_SECS  Optional integer/float seconds. Caps how
        long the installer subprocess may run. Unset (default) means no
        timeout — interrupt with Ctrl+C if the installer hangs.
    """
    if tag is not None:
        try:
            tag = _validate_tag(tag)
        except typer.BadParameter as exc:
            console.print(str(exc), soft_wrap=True)
            raise typer.Exit(1) from exc

    plan, failure_reason = _build_upgrade_plan(target_tag_override=tag)

    # Resolver could not produce a tag → surface the categorized failure
    # and exit non-zero so scripts notice (action-oriented unlike `self check`).
    if plan is None:
        if failure_reason is None:
            # _build_upgrade_plan's contract: if plan is None, failure_reason
            # is set. Defend explicitly so the guard survives `python -O`.
            raise RuntimeError(
                "internal contract violation: _build_upgrade_plan returned (None, None)"
            )
        _emit_failure(failure_reason)
        raise typer.Exit(1)

    # --dry-run preview path. Non-upgradable methods still emit guidance
    # rather than a fake preview block — there is nothing to preview when
    # there is nothing the CLI would launch.
    if dry_run:
        if plan.method in (
            _InstallMethod.UVX_EPHEMERAL,
            _InstallMethod.SOURCE_CHECKOUT,
            _InstallMethod.UNSUPPORTED,
        ):
            _emit_guidance(plan.method, plan.target_tag)
            raise typer.Exit(0)
        console.print("Dry run — no changes will be made.")
        for line in plan.preview_summary.splitlines():
            console.print(line)
        raise typer.Exit(0)

    # Non-upgradable runtime: never launch an installer regardless of flags.
    if plan.method in (
        _InstallMethod.UVX_EPHEMERAL,
        _InstallMethod.SOURCE_CHECKOUT,
        _InstallMethod.UNSUPPORTED,
    ):
        _emit_guidance(plan.method, plan.target_tag)
        raise typer.Exit(0)

    if plan.target_tag is None:
        raise RuntimeError("Upgrade target tag is required for upgradable install methods")
    target_tag = plan.target_tag

    # No-op success when the user is already on the latest tag.
    if plan.current_version != "unknown":
        if plan.current_version == target_tag:
            if tag is None:
                console.print(f"Already on latest release: {target_tag}")
            else:
                console.print(f"Already on requested release: {target_tag}")
            raise typer.Exit(0)
    target_canonical = _canonicalize_version_text(target_tag)
    if not _is_comparable_version_text(target_canonical):
        _emit_failure("target-tag-unparseable", plan=plan)
        raise typer.Exit(1)
    if plan.current_version != "unknown":
        current_canonical = _canonicalize_version_text(plan.current_version)
        versions_comparable = _is_comparable_version_text(current_canonical)
        # Both arguments are pre-canonicalized so the ordering check matches
        # the exact-equality check used for pinned targets below.
        if tag is None and versions_comparable and not _is_newer(
            target_canonical, current_canonical
        ):
            if current_canonical == target_canonical:
                console.print(f"Already on latest release: {target_tag}")
            else:
                console.print(f"Already on latest release or newer: {plan.current_version}")
            raise typer.Exit(0)
        if tag is not None and current_canonical == target_canonical:
            console.print(f"Already on requested release: {target_tag}")
            raise typer.Exit(0)

    # One-line pre-execution notice so the user sees exactly what will run
    # before the installer's own output starts streaming.
    argv_str = _render_argv(plan.installer_argv) if plan.installer_argv else ""
    console.print(
        f"Upgrading specify-cli {plan.current_version} → {plan.target_tag} "
        f"via {_method_label(plan.method)}: {argv_str}",
        soft_wrap=True,
    )

    # Launch the installer. Stdout/stderr stream through (no capture) so the
    # user sees real-time progress. We never pass shell=True.
    completed = _run_installer(plan)

    if completed is None:
        installer_name = plan.installer_argv[0] if plan.installer_argv else None
        _emit_failure("installer-missing", plan=plan, installer_name=installer_name)
        raise typer.Exit(3)

    if completed.returncode == _INSTALLER_INVALID_SENTINEL:
        installer_name = plan.installer_argv[0] if plan.installer_argv else None
        _emit_failure("installer-invalid", plan=plan, installer_name=installer_name)
        raise typer.Exit(3)

    if completed.returncode != 0:
        _emit_failure(
            "installer-failed",
            plan=plan,
            installer_exit=completed.returncode,
        )
        if completed.returncode == _INSTALLER_TIMEOUT_SENTINEL:
            raise typer.Exit(124)
        raise typer.Exit(completed.returncode)

    # Verify in a child process: this Python process is still running the
    # pre-upgrade module, so importlib.metadata would lie. A fresh `specify
    # --version` is the only signal that the new binary is actually live.
    verified = _verify_upgrade(plan)
    if (
        verified is None
        or _canonicalize_version_text(plan.target_tag)
        != _canonicalize_version_text(verified)
    ):
        _emit_failure(
            "verification-mismatch",
            plan=plan,
            verified_version=verified,
        )
        raise typer.Exit(2)

    console.print(
        f"Upgraded specify-cli: {plan.pre_upgrade_snapshot} → {verified}",
        soft_wrap=True,
    )
