"""Resolve and track extension resources for generated skills."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

import pathspec

from . import ValidationError
from ..integrations.manifest import IntegrationManifest, _sha256, _validate_record_path
from ..shared_infra import _validate_safe_shared_directory


def recorded_resource_hashes(metadata: dict | None) -> dict[str, dict[str, str]]:
    """Copy valid resource buckets from extension registry metadata."""
    previous = metadata.get("skill_resource_hashes", {}) if metadata else {}
    if not isinstance(previous, dict):
        return {}
    return {
        bucket: dict(previous[bucket])
        for bucket in ("project", "home")
        if isinstance(previous.get(bucket), dict)
    }


def skills_resource_root(project_root: Path, skills_dir: Path) -> tuple[str, Path] | None:
    """Choose the existing project-first, then home skills validation boundary."""
    for bucket, root in (("project", project_root), ("home", Path.home())):
        if skills_dir.is_relative_to(root):
            return bucket, root
    return None


def resolve_skill_resources(ext_dir: Path, patterns: list[str]) -> list[str]:
    """Resolve validated declarations against the installed extension contents."""
    if ext_dir.is_symlink():
        raise ValidationError(f"Resource extension directory is a symlink: {ext_dir}")
    root = ext_dir.resolve()
    matches: set[str] = set()
    for pattern in patterns:
        spec = pathspec.GitIgnoreSpec.from_lines([pattern])
        wildcard = any(char in pattern for char in "*?[")
        candidates: list[str] = []
        if wildcard:
            for directory, dirs, files in os.walk(root, followlinks=False):
                for name in dirs + files:
                    candidate = Path(directory) / name
                    relative = candidate.relative_to(root).as_posix()
                    if candidate.is_symlink():
                        if spec.match_file(relative) or spec.match_file(relative + "/"):
                            raise ValidationError(f"Resource match is a symlink: {relative}")
                    elif name in files and candidate.is_file() and spec.match_file(relative):
                        candidates.append(relative)
        else:
            candidates = [pattern]

        if not candidates:
            raise ValidationError(f"Resource pattern {pattern!r} matches no files")
        for relative in candidates:
            try:
                source = _validate_record_path(Path(relative), root)
            except (ValueError, OSError) as exc:
                raise ValidationError(f"Invalid resource {relative!r}: {exc}") from exc
            if not source.is_file():
                raise ValidationError(f"Resource is not an existing regular file: {relative}")
            normalized = source.relative_to(root).as_posix()
            if normalized.casefold() == "skill.md":
                raise ValidationError("Resource destination cannot be SKILL.md")
            matches.add(normalized)
    return sorted(matches)


def sync_skill_resources(
    ext_id: str,
    skills_dir: Path,
    trusted_root: Path,
    skill_name: str,
    ext_dir: Path,
    paths: list[str],
    previous: dict[str, str],
    *,
    overwrite_modified: bool = False,
) -> tuple[dict[str, str], list[Path], list[str]]:
    """Write resources through a throwaway manifest, preserving unowned edits."""
    skill_dir = skills_dir / skill_name
    _validate_safe_shared_directory(trusted_root, skill_dir)
    manifest = IntegrationManifest(ext_id, trusted_root)
    updated: dict[str, str] = {}
    written: list[Path] = []
    warnings: list[str] = []
    for resource in paths:
        rel = (skill_dir / resource).relative_to(trusted_root).as_posix()
        dest = trusted_root / rel
        expected = previous.get(rel)
        try:
            _validate_record_path(Path(rel), trusted_root)
        except (ValueError, OSError) as exc:
            if expected is not None:
                updated[rel] = expected
            warnings.append(f"Skipped unsafe resource {rel}: {exc}")
            continue
        if dest.exists() and not overwrite_modified:
            managed = False
            if expected is not None and dest.is_file():
                try:
                    managed = _sha256(dest) == expected
                except OSError:
                    pass
            if not managed:
                if expected is not None:
                    updated[rel] = expected
                    warnings.append(f"Preserved modified resource {rel}; use --force to overwrite")
                else:
                    warnings.append(f"Skipped unowned resource {rel}")
                continue
        try:
            source = _validate_record_path(Path(resource), ext_dir.resolve())
            written.append(manifest.record_file(rel, source.read_bytes()))
        except (ValueError, OSError) as exc:
            if expected is not None:
                updated[rel] = expected
            warnings.append(f"Skipped resource {rel}: {exc}")
    updated.update(manifest.files)
    return updated, written, warnings


def remove_skill_resources(
    ext_id: str,
    trusted_root: Path,
    previous: dict[str, str],
    allowed_skill_names: set[str],
) -> tuple[list[Path], list[Path]]:
    """Remove canonical recorded paths belonging to a registered skill name."""
    manifest = IntegrationManifest(ext_id, trusted_root)
    dropped: list[Path] = []
    for key, digest in previous.items():
        path = PurePosixPath(key)
        if (
            not key or "\\" in key or path.is_absolute()
            or PureWindowsPath(key).drive or path.as_posix() != key
            or ".." in path.parts or not set(path.parts[:-1]) & allowed_skill_names
        ):
            dropped.append(trusted_root / key)
            continue
        manifest._files[key] = digest
    removed, skipped = manifest.uninstall(force=True, remove_manifest=False)
    return removed, dropped + skipped


def deliver_skill_resources(
    project_root: Path,
    ext_id: str,
    skills_dir: Path,
    skill_name: str,
    ext_dir: Path,
    paths: list[str],
    previous: dict[str, dict[str, str]],
    collected: dict[str, dict[str, str]],
    *,
    overwrite_modified: bool = False,
) -> None:
    """Sync one written skill and collect manifest hashes without rescanning."""
    import warnings

    from .. import ensure_executable_scripts

    scope = skills_resource_root(project_root, skills_dir)
    if scope is None:
        warnings.warn(f"Skipped resources outside project and home: {skills_dir}", stacklevel=2)
        return
    bucket, root = scope
    try:
        hashes, written, messages = sync_skill_resources(
            ext_id, skills_dir, root, skill_name, ext_dir, paths,
            previous.get(bucket, {}), overwrite_modified=overwrite_modified,
        )
    except (ValueError, OSError) as exc:
        warnings.warn(f"Skipped unsafe skill resources in {skills_dir}: {exc}", stacklevel=2)
        return
    collected.setdefault(bucket, {}).update(hashes)
    for message in messages:
        warnings.warn(message, stacklevel=2)
    ensure_executable_scripts(project_root, files=written)


def retire_skill_resources(
    project_root: Path, ext_id: str, hashes: dict, skill_names: set[str],
    *, skills_dir: Path | None = None,
) -> None:
    """Remove recorded resources for these skill names and forget their keys."""
    import warnings

    scope = skills_resource_root(project_root, skills_dir) if skills_dir is not None else None
    if skills_dir is not None and scope is None:
        return
    for bucket, root in (("project", project_root), ("home", Path.home())):
        if skills_dir is not None and bucket != scope[0]:
            continue
        prefix = skills_dir.relative_to(root).parts if skills_dir is not None else None
        records = hashes.get(bucket)
        if not isinstance(records, dict):
            continue
        selected = {
            key: value for key, value in records.items()
            if isinstance(key, str) and (
                set(PurePosixPath(key).parts[:-1]) & skill_names if prefix is None else
                PurePosixPath(key).parts[:len(prefix)] == prefix
                and len(PurePosixPath(key).parts) > len(prefix) + 1
                and PurePosixPath(key).parts[len(prefix)] in skill_names
            )
        }
        if not selected:
            continue
        _, skipped = remove_skill_resources(ext_id, root, selected, skill_names)
        for path in skipped:
            warnings.warn(f"Skipped unsafe skill resource {path}", stacklevel=2)
        for key in selected:
            records.pop(key, None)
        if not records:
            hashes.pop(bucket, None)
