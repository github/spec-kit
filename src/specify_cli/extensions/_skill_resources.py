"""Resolve and track extension resources for generated skills."""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Iterator
from contextlib import contextmanager
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


#: Root entries a wildcard never selects: the dev-mode render cache holds
#: generated outputs, and the manifest is not a packaged resource.
_WILDCARD_EXCLUDED_DIRS = frozenset({".specify-dev"})
_WILDCARD_EXCLUDED_FILES = frozenset({"extension.yml"})


@contextmanager
def track_skill_resource_writes() -> Iterator[set[Path]]:
    """Collect the paths written while active, via the file-change observer.

    Resource copies go through ``IntegrationManifest.record_file``, which
    reports every write it performs. Files that are skipped or preserved are
    never reported, so the result is the exact set an attempt wrote, whatever
    their digests. Any outer observer keeps receiving the events.
    """
    from ..integrations._file_changes import file_change_observer

    written: set[Path] = set()
    outer = file_change_observer.get()

    def observe(path: Path, before: bool, removal: bool) -> None:
        if outer is not None:
            outer(path, before, removal)
        if before and not removal:
            written.add(Path(path))

    token = file_change_observer.set(observe)
    try:
        yield written
    finally:
        file_change_observer.reset(token)


def written_resource_hashes(
    project_root: Path, hashes: dict, written: set[Path],
    *, previous: dict | None = None,
) -> dict[str, dict[str, str]]:
    """Select the recorded resources whose files were written, per bucket.

    With ``previous``, records that were already there before the attempt are
    left out, so only files the attempt created are selected.
    """
    roots = {"project": project_root.resolve(), "home": Path.home().resolve()}
    previous = previous or {}
    return {
        bucket: {
            key: digest for key, digest in records.items()
            if isinstance(key, str) and roots[bucket] / key in written
            and key not in (previous.get(bucket) or {})
        }
        for bucket, records in hashes.items()
        if bucket in roots and isinstance(records, dict)
    }


def resolve_skill_resources(
    ext_dir: Path,
    patterns: list[str],
    *,
    ignore: Callable[[str, list[str]], set[str]] | None = None,
) -> list[str]:
    """Resolve validated declarations against extension contents.

    ``ignore`` is a ``shutil.copytree`` ignore callback. When given, resources
    it would exclude from a copy are treated as absent, so a source directory
    can be validated in place with the result a later install will produce.
    """
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
                if Path(directory) == root:
                    dirs[:] = [name for name in dirs if name not in _WILDCARD_EXCLUDED_DIRS]
                    files = [name for name in files if name not in _WILDCARD_EXCLUDED_FILES]
                if ignore is not None:
                    shown = str(ext_dir / Path(directory).relative_to(root))
                    skipped = ignore(shown, dirs + files)
                    dirs[:] = [name for name in dirs if name not in skipped]
                    files = [name for name in files if name not in skipped]
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
            parts = PurePosixPath(pattern).parts
            if parts and parts[0] in _WILDCARD_EXCLUDED_DIRS:
                raise ValidationError(f"Resource is internal render output: {pattern}")
            for index, part in enumerate(parts):
                if ignore is not None and part in ignore(
                    str(ext_dir.joinpath(*parts[:index])), [part]
                ):
                    raise ValidationError(f"Resource is excluded from the install: {pattern}")

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
            written.append(manifest.record_file(
                rel, source.read_bytes(), mode=_resource_mode(source),
            ))
        except (ValueError, OSError) as exc:
            if expected is not None:
                updated[rel] = expected
            warnings.append(f"Skipped resource {rel}: {exc}")
    updated.update(manifest.files)
    return updated, written, warnings


def _resource_mode(source: Path) -> int:
    """Creation mode for a resource copy: the source's bits, owner read/write.

    The process umask still narrows it, so a copy never has group/other access
    the source lacks, and keeps the source's execute bits (not only for
    ``.sh`` scripts). Owner read/write is always kept so a later refresh can
    replace the copy.
    """
    return (stat.S_IMODE(source.stat().st_mode) & 0o777) | 0o600


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


def _home_skills_dirs(project_root: Path) -> list[Path]:
    """Resolve the skills dirs of agents that declare ``home_scoped`` output."""
    from ..agents import CommandRegistrar

    registrar = CommandRegistrar(project_root, include_generic=False)
    dirs: list[Path] = []
    for name, config in registrar.AGENT_CONFIGS.items():
        if config.get("extension") != "/SKILL.md" or config.get("home_scoped") is not True:
            continue
        resolved = registrar._resolve_agent_dir(name, config, project_root)
        scope = skills_resource_root(project_root, resolved)
        if scope is not None and scope[0] == "home":
            dirs.append(resolved)
    return dirs


def retire_skill_resources(
    project_root: Path, ext_id: str, hashes: dict, skill_names: set[str],
    *, skills_dir: Path | None = None,
) -> None:
    """Remove recorded resources for these skill names and forget their keys.

    Without ``skills_dir`` the project bucket follows recorded paths, even after
    a skills directory moved. The home bucket is a far larger boundary, so it is
    only cleaned under the skills directories of agents that declare
    ``registrar_config["home_scoped"]``, as their ``SKILL.md`` cleanup does;
    other records are left untouched.
    """
    import warnings

    # (bucket, trusted root, skills-dir prefix under that root or None for any)
    targets: list[tuple[str, Path, tuple[str, ...] | None]] = []
    if skills_dir is not None:
        scope = skills_resource_root(project_root, skills_dir)
        if scope is None:
            return
        targets.append((scope[0], scope[1], skills_dir.relative_to(scope[1]).parts))
    else:
        targets.append(("project", project_root, None))
        home = Path.home()
        targets.extend(
            ("home", home, directory.relative_to(home).parts)
            for directory in _home_skills_dirs(project_root)
        )
    for bucket, root, prefix in targets:
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
