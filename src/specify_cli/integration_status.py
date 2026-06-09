"""Read-only status reporting for project integration state."""

from __future__ import annotations

import hashlib
import re
import stat
from pathlib import Path
from typing import Any

from .integration_state import (
    INTEGRATION_JSON,
    INTEGRATION_STATE_SCHEMA,
    IntegrationReadError,
    default_integration_key,
    installed_integration_keys,
    try_read_integration_json_with_raw,
)
from .integrations import INTEGRATION_REGISTRY
from .integrations.manifest import IntegrationManifest

_MANIFEST_READ_ERRORS = (ValueError, OSError)
_MANIFEST_KEY_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_WINDOWS_RESERVED_MANIFEST_BASENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_SHARED_MANIFEST_KEY = "speckit"


def _finding(
    severity: str,
    code: str,
    message: str,
    *,
    integration: str | None = None,
    path: str | None = None,
    suggestion: str | None = None,
) -> dict[str, str]:
    item = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if integration:
        item["integration"] = integration
    if path:
        item["path"] = path
    if suggestion:
        item["suggestion"] = suggestion
    return item


def _status(findings: list[dict[str, str]]) -> str:
    if any(item["severity"] == "error" for item in findings):
        return "error"
    if findings:
        return "warning"
    return "ok"


def _with_error_detail(message: str, error: IntegrationReadError) -> str:
    if error.detail:
        return f"{message} Detail: {error.detail}"
    return message


def _integration_state_error_message(error: IntegrationReadError) -> str:
    if error.kind == "decode":
        return _with_error_detail(
            f"{INTEGRATION_JSON} contains invalid JSON or is not valid UTF-8.",
            error,
        )
    if error.kind == "os":
        return _with_error_detail(f"Could not read {INTEGRATION_JSON}.", error)
    if error.kind == "not_object":
        return f"{INTEGRATION_JSON} must contain a JSON object, got {error.detail}."
    if error.kind == "schema_too_new":
        return (
            f"{INTEGRATION_JSON} uses integration state schema {error.schema}, "
            f"which is newer than this CLI supports; supported schema: {INTEGRATION_STATE_SCHEMA}."
        )
    return f"Could not inspect {INTEGRATION_JSON}."


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _strip_extended_length_prefix(path: Path) -> Path:
    """Drop the Windows ``\\\\?\\`` extended-length prefix for path comparison.

    ``os.readlink`` and ``Path.resolve`` can return extended-length paths on
    Windows (e.g. ``\\\\?\\C:\\proj``). Comparing such a path against a plain
    ``C:\\proj`` root via :meth:`Path.relative_to` would spuriously fail, so we
    normalise both sides through this helper before containment checks.
    """
    raw = str(path)
    if raw.startswith("\\\\?\\UNC\\"):
        return Path("\\\\" + raw[len("\\\\?\\UNC\\"):])
    if raw.startswith("\\\\?\\"):
        return Path(raw[len("\\\\?\\"):])
    return path


def _is_within_project(project_root_resolved: Path, candidate: Path) -> bool:
    """Return ``True`` when *candidate* stays within *project_root_resolved*.

    Both paths are stripped of any Windows extended-length prefix first so that
    a target produced by ``os.readlink`` (which may be ``\\\\?\\``-prefixed) is
    still recognised as living inside an unprefixed project root.
    """
    try:
        _strip_extended_length_prefix(candidate).relative_to(
            _strip_extended_length_prefix(project_root_resolved)
        )
    except ValueError:
        return False
    return True


def _safe_manifest_file(
    project_root: Path,
    project_root_resolved: Path,
    rel: str,
    *,
    project_root_is_resolved: bool = True,
) -> Path | None:
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None
    candidate = project_root / rel_path
    if not project_root_is_resolved:
        walk = project_root
        for part in rel_path.parts[:-1]:
            walk = walk / part
            try:
                if walk.is_symlink():
                    return None
            except OSError:
                return None
    try:
        candidate_parent = (
            candidate.parent.resolve(strict=False)
            if project_root_is_resolved
            else candidate.parent.absolute()
        )
    except (OSError, RuntimeError):
        return None
    if not _is_within_project(project_root_resolved, candidate_parent):
        return None
    return candidate


def _tracked_symlink_manifest_status(
    path: Path,
    project_root_resolved: Path,
    *,
    project_root_is_resolved: bool = True,
) -> str:
    """Classify a tracked symlink without following it outside the project.

    Manifests store content hashes for regular files, so an existing in-project
    symlink is still reported as modified. Escaping targets are invalid, and
    dangling in-project targets are missing.
    """
    try:
        target = path.readlink()
    except OSError:
        return "modified"

    target_path = target if target.is_absolute() else path.parent / target
    try:
        contained_parent = (
            target_path.parent.resolve(strict=False)
            if project_root_is_resolved
            else target_path.parent.absolute()
        )
    except (OSError, RuntimeError):
        return "invalid"
    if not _is_within_project(project_root_resolved, contained_parent):
        return "invalid"

    try:
        target_path.lstat()
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "modified"
    return "modified"


def _resolve_project_root_for_status(
    project_root: Path,
    findings: list[dict[str, str]],
) -> tuple[Path, bool]:
    try:
        return project_root.resolve(), True
    except (OSError, RuntimeError) as exc:
        findings.append(
            _finding(
                "warning",
                "project-root-unresolved",
                f"Could not fully resolve project root: {exc}",
                suggestion="Check project path permissions and symlinks before relying on manifest path checks.",
            )
        )
        return project_root.absolute(), False


def _is_safe_manifest_key(key: str) -> bool:
    if key in {"", ".", ".."}:
        return False
    if key.endswith("."):
        return False
    if _MANIFEST_KEY_RE.fullmatch(key) is None:
        return False
    if key.split(".", 1)[0].upper() in _WINDOWS_RESERVED_MANIFEST_BASENAMES:
        return False
    if "/" in key or "\\" in key:
        return False
    key_path = Path(key)
    return not key_path.is_absolute() and key_path.name == key


def _manifest_file_status(
    manifest: IntegrationManifest,
    project_root_resolved: Path,
    *,
    project_root_is_resolved: bool = True,
) -> tuple[list[str], list[str], list[str], list[str]]:
    missing: list[str] = []
    modified: list[str] = []
    invalid: list[str] = []
    valid: list[str] = []

    for rel, expected_hash in manifest.files.items():
        path = _safe_manifest_file(
            manifest.project_root,
            project_root_resolved,
            rel,
            project_root_is_resolved=project_root_is_resolved,
        )
        if path is None:
            invalid.append(rel)
            continue
        try:
            path_stat = path.lstat()
        except FileNotFoundError:
            valid.append(rel)
            missing.append(rel)
            continue
        except OSError:
            valid.append(rel)
            modified.append(rel)
            continue
        is_symlink = stat.S_ISLNK(path_stat.st_mode)
        if not is_symlink:
            try:
                is_symlink = path.is_symlink()
            except OSError:
                is_symlink = False
        if is_symlink:
            symlink_status = _tracked_symlink_manifest_status(
                path,
                project_root_resolved,
                project_root_is_resolved=project_root_is_resolved,
            )
            if symlink_status == "invalid":
                invalid.append(rel)
                continue
            valid.append(rel)
            if symlink_status == "missing":
                missing.append(rel)
                continue
            modified.append(rel)
            continue
        valid.append(rel)
        if not stat.S_ISREG(path_stat.st_mode):
            modified.append(rel)
            continue
        try:
            if _sha256_file(path) != expected_hash:
                modified.append(rel)
        except OSError:
            modified.append(rel)

    return missing, modified, invalid, valid


def _default_not_installed_from_raw_state(raw_state: dict[str, Any]) -> str | None:
    if not isinstance(raw_state.get("installed_integrations"), list):
        return None

    raw_default = default_integration_key(raw_state)
    raw_installed = installed_integration_keys(raw_state)
    if raw_default and raw_default not in raw_installed:
        return raw_default
    return None


def _manifest_summary(
    manifest_path: Path,
    project_root: Path,
    *,
    readable: bool,
    tracked_files: int = 0,
    missing_files: list[str] | None = None,
    modified_files: list[str] | None = None,
    invalid_files: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "manifest": manifest_path.relative_to(project_root).as_posix(),
        "readable": readable,
        "tracked_files": tracked_files,
        "missing_files": missing_files or [],
        "modified_files": modified_files or [],
        "invalid_files": invalid_files or [],
    }


def _manifest_owner(key: str) -> str:
    if key == _SHARED_MANIFEST_KEY:
        return "shared Spec Kit infrastructure"
    return f"integration '{key}'"


def _manifest_suggestion(key: str, default_key: str | None) -> str:
    if key == _SHARED_MANIFEST_KEY:
        if default_key and default_key in INTEGRATION_REGISTRY:
            return f"Run `specify integration upgrade {default_key}` to regenerate shared managed files."
        return (
            "Run `specify init --here --force --integration <key>` to regenerate "
            "shared managed files."
        )
    if key not in INTEGRATION_REGISTRY:
        return (
            "Upgrade Spec Kit, reinstall with a supported CLI version, "
            f"or remove the stale integration entry from {INTEGRATION_JSON}."
        )
    return f"Run `specify integration upgrade {key}` or reinstall the integration."


def build_integration_status_report(project_root: Path) -> dict[str, Any]:
    """Return a machine-readable integration status report for *project_root*."""
    findings: list[dict[str, str]] = []
    project_root_resolved, project_root_is_resolved = _resolve_project_root_for_status(
        project_root,
        findings,
    )
    state, raw_state, error = try_read_integration_json_with_raw(project_root)
    if error is not None:
        findings.append(
            _finding(
                "error",
                "integration-state-unreadable",
                _integration_state_error_message(error),
                path=INTEGRATION_JSON,
                suggestion=f"Fix or delete {INTEGRATION_JSON}, then retry.",
            )
        )
        return _build_report(None, [], findings, {}, None)

    if state is None:
        findings.append(
            _finding(
                "error",
                "integration-state-missing",
                f"{INTEGRATION_JSON} is missing.",
                path=INTEGRATION_JSON,
                suggestion="Run `specify integration install <key>` to install an integration.",
            )
        )
        return _build_report(None, [], findings, {}, None)

    assert raw_state is not None
    raw_default_key = default_integration_key(raw_state)
    raw_installed_value = raw_state.get("installed_integrations")
    raw_installed_is_list = isinstance(raw_installed_value, list)
    raw_installed_keys = (
        installed_integration_keys(raw_state)
        if raw_installed_is_list
        else []
    )
    default_key = raw_default_key or default_integration_key(state)
    installed_keys = installed_integration_keys(state)
    raw_default_not_installed = _default_not_installed_from_raw_state(raw_state)
    if raw_installed_is_list and raw_default_not_installed and raw_installed_keys:
        check_installed_keys = raw_installed_keys
    else:
        check_installed_keys = installed_keys
    recorded_installed_keys = raw_installed_keys
    if "installed_integrations" in raw_state and not raw_installed_is_list:
        findings.append(
            _finding(
                "warning",
                "installed-integrations-invalid",
                (
                    "installed_integrations must be a list, "
                    f"got {type(raw_installed_value).__name__}."
                ),
                path=INTEGRATION_JSON,
                suggestion=f"Fix {INTEGRATION_JSON}, then retry.",
            )
        )
    if not installed_keys:
        findings.append(
            _finding(
                "warning",
                "no-installed-integrations",
                "No installed integrations are recorded.",
                suggestion="Run `specify integration install <key>` to install one.",
            )
        )

    if raw_installed_keys and raw_default_key is None:
        default_key = None
        findings.append(
            _finding(
                "error",
                "default-integration-missing",
                "No default integration is recorded.",
                suggestion="Run `specify integration use <key>` after choosing an installed integration.",
            )
        )

    if raw_default_not_installed:
        findings.append(
            _finding(
                "error",
                "default-integration-not-installed",
                (
                    f"Default integration '{raw_default_not_installed}' is not listed "
                    "in installed_integrations."
                ),
                integration=raw_default_not_installed,
                suggestion="Run `specify integration use <key>` for an installed integration, or reinstall the default integration.",
            )
        )

    known_installed = [key for key in check_installed_keys if key in INTEGRATION_REGISTRY]
    unknown_installed: list[str] = []
    for key in check_installed_keys:
        if key not in INTEGRATION_REGISTRY:
            unknown_installed.append(key)
            findings.append(
                _finding(
                    "error",
                    "unknown-integration",
                    f"Integration '{key}' is installed but is not known to this CLI.",
                    integration=key,
                    suggestion=(
                        "Upgrade Spec Kit, reinstall with a supported CLI version, "
                        f"or remove the stale integration entry from {INTEGRATION_JSON}."
                    ),
                )
            )

    unsafe = [
        key for key in known_installed
        if not getattr(INTEGRATION_REGISTRY[key], "multi_install_safe", False)
    ]
    if len(check_installed_keys) > 1:
        unsafe.extend(unknown_installed)

    if len(check_installed_keys) > 1 and unsafe:
        findings.append(
            _finding(
                "error",
                "unsafe-multi-install",
                (
                    "Installed integrations are not all declared multi-install safe: "
                    + ", ".join(sorted(unsafe))
                ),
                suggestion=(
                    "Use `specify integration use <key>` to change defaults, "
                    "or `specify integration switch <key>` only when replacing integrations."
                ),
            )
        )

    manifest_files_by_path: dict[str, list[str]] = {}
    manifest_summaries: dict[str, dict[str, Any]] = {}
    attempted_manifest_keys: list[str] = []
    manifest_keys = list(check_installed_keys)
    if _SHARED_MANIFEST_KEY not in manifest_keys:
        manifest_keys.append(_SHARED_MANIFEST_KEY)

    for key in manifest_keys:
        owner = _manifest_owner(key)
        if not _is_safe_manifest_key(key):
            findings.append(
                _finding(
                    "error",
                    "integration-key-invalid",
                    f"Integration key {key!r} cannot be used as a manifest filename.",
                    integration=key,
                    path=INTEGRATION_JSON,
                    suggestion=f"Fix {INTEGRATION_JSON}, then reinstall the integration.",
                )
            )
            continue

        attempted_manifest_keys.append(key)
        manifest_path = project_root / ".specify" / "integrations" / f"{key}.manifest.json"
        try:
            manifest = IntegrationManifest.load(
                key,
                project_root_resolved,
                resolve_project_root=False,
            )
        except FileNotFoundError:
            findings.append(
                _finding(
                    "error",
                    "manifest-missing",
                    f"Manifest for {owner} is missing.",
                    integration=key,
                    path=manifest_path.relative_to(project_root).as_posix(),
                    suggestion=_manifest_suggestion(key, default_key),
                )
            )
            manifest_summaries[key] = _manifest_summary(
                manifest_path,
                project_root,
                readable=False,
            )
            continue
        except _MANIFEST_READ_ERRORS as exc:
            manifest_summaries[key] = _manifest_summary(
                manifest_path,
                project_root,
                readable=False,
            )
            findings.append(
                _finding(
                    "error",
                    "manifest-unreadable",
                    f"Manifest for {owner} is unreadable: {exc}",
                    integration=key,
                    path=manifest_path.relative_to(project_root).as_posix(),
                    suggestion=_manifest_suggestion(key, default_key),
                )
            )
            continue

        missing, modified, invalid, valid_files = _manifest_file_status(
            manifest,
            project_root_resolved,
            project_root_is_resolved=project_root_is_resolved,
        )
        manifest_summaries[key] = _manifest_summary(
            manifest_path,
            project_root,
            readable=True,
            tracked_files=len(manifest.files),
            missing_files=missing,
            modified_files=modified,
            invalid_files=invalid,
        )

        for rel in valid_files:
            manifest_files_by_path.setdefault(rel, []).append(key)
        if invalid:
            findings.append(
                _finding(
                    "error",
                    "manifest-paths-invalid",
                    f"{len(invalid)} unsafe manifest path(s) are recorded for {owner}.",
                    integration=key,
                    path=manifest_path.relative_to(project_root).as_posix(),
                    suggestion=_manifest_suggestion(key, default_key),
                )
            )
        if missing:
            findings.append(
                _finding(
                    "error",
                    "managed-files-missing",
                    f"{len(missing)} managed file(s) are missing for {owner}.",
                    integration=key,
                    suggestion=_manifest_suggestion(key, default_key),
                )
            )
        if modified:
            findings.append(
                _finding(
                    "warning",
                    "managed-files-modified",
                    f"{len(modified)} managed file(s) were modified for {owner}.",
                    integration=key,
                    suggestion="Review the changes before running `specify integration upgrade --force`.",
                )
            )

    for rel, keys in sorted(manifest_files_by_path.items()):
        if len(keys) > 1:
            findings.append(
                _finding(
                    "warning",
                    "managed-file-collision",
                    f"Managed file '{rel}' is tracked by multiple integrations: {', '.join(sorted(keys))}.",
                    path=rel,
                    suggestion="Review the manifests before uninstalling or upgrading these integrations.",
                )
            )

    if not raw_installed_is_list or not raw_installed_keys:
        multi_install_safe = None
    else:
        multi_install_safe = not (len(check_installed_keys) > 1 and unsafe)
    return _build_report(
        default_key,
        installed_keys,
        findings,
        manifest_summaries,
        multi_install_safe,
        manifest_checked_keys=attempted_manifest_keys,
        recorded_installed_keys=recorded_installed_keys,
    )


def _build_report(
    default_key: str | None,
    installed_keys: list[str],
    findings: list[dict[str, str]],
    manifests: dict[str, dict[str, Any]],
    multi_install_safe: bool | None,
    *,
    manifest_checked_keys: list[str] | None = None,
    recorded_installed_keys: list[str] | None = None,
) -> dict[str, Any]:
    missing_count = sum(len(item.get("missing_files", [])) for item in manifests.values())
    modified_count = sum(len(item.get("modified_files", [])) for item in manifests.values())
    invalid_count = sum(len(item.get("invalid_files", [])) for item in manifests.values())
    unchecked_count = sum(1 for item in manifests.values() if not item.get("readable", True))
    return {
        "status": _status(findings),
        "default_integration": default_key,
        "installed_integrations": installed_keys,
        "recorded_installed_integrations": (
            installed_keys if recorded_installed_keys is None else recorded_installed_keys
        ),
        "manifest_checked_integrations": (
            installed_keys if manifest_checked_keys is None else manifest_checked_keys
        ),
        "multi_install_safe": multi_install_safe,
        "shared_templates_target_alignment": default_key,
        "missing_managed_files": missing_count,
        "modified_managed_files": modified_count,
        "invalid_manifest_paths": invalid_count,
        "unchecked_manifests": unchecked_count,
        "manifests": manifests,
        "findings": findings,
    }
