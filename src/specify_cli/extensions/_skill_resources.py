"""Resolve and track extension resources for generated skills."""

from __future__ import annotations

import os
import stat
from collections.abc import Callable, Iterable, Iterator
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


#: Every skill an extension generates is named ``speckit-...``. Path-based
#: resource cleanup relies on it, because it has no ``SKILL.md`` marker to read.
GENERATED_SKILL_PREFIX = "speckit-"


def skill_name_parts(name: object, *, generated_only: bool = False) -> tuple[str, ...] | None:
    """Return the path segments of a skill name, or ``None`` if it cannot be one.

    A free-form alias may produce a nested skill (``speckit-ext/group-alias``),
    so a name has one or more segments. Empty, ``.`` and ``..`` segments,
    backslashes and drive prefixes never name a skill. ``generated_only`` also
    requires the ``speckit-`` prefix every generated skill carries.
    """
    if (
        not isinstance(name, str) or not name or "\\" in name
        or PureWindowsPath(name).drive
    ):
        return None
    parts = tuple(name.split("/"))
    if any(part in ("", ".", "..") for part in parts):
        return None
    if generated_only and not parts[0].startswith(GENERATED_SKILL_PREFIX):
        return None
    return parts


def _boundaries(project_root: Path) -> tuple[Path, Path]:
    return Path(os.path.abspath(project_root)), Path(os.path.abspath(Path.home()))


def locate_skills_dir(project_root: Path, skills_dir: Path) -> tuple[Path, Path] | None:
    """Return *skills_dir* below its project or home root, and that root.

    Paths are compared lexically, so a symlinked skills directory is judged by
    where it is, not by where it points. A path that was already resolved (the
    generic output root is) is expressed below the lexical root first, so a
    project reached through a symlink, such as ``/var`` versus ``/private/var``,
    is still recognised.
    """
    candidate = Path(os.path.abspath(skills_dir))
    roots = _boundaries(project_root)
    for root in roots:
        if candidate.is_relative_to(root):
            return candidate, root
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if candidate.is_relative_to(resolved):
            return root / candidate.relative_to(resolved), root
    return None


def skills_resource_root(project_root: Path, skills_dir: Path) -> tuple[str, Path] | None:
    """Choose the existing project-first, then home skills validation boundary."""
    located = locate_skills_dir(project_root, skills_dir)
    if located is None:
        return None
    project, _ = _boundaries(project_root)
    return ("project" if located[1] == project else "home"), located[1]


def configured_skill_roots(project_root: Path) -> dict[Path, Path]:
    """Return every skills directory an integration is configured to write, with its root."""
    from .. import DEFAULT_SKILLS_DIR
    from ..agents import CommandRegistrar
    from ..integrations import get_integration
    from ..integrations.installer import project_integrations

    with project_integrations(project_root):
        registrar = CommandRegistrar(project_root, include_generic=False)
        folders = []
        for key in registrar.AGENT_CONFIGS:
            integration = get_integration(key)
            if integration is not None:
                folder = (integration.config or {}).get("folder")
                if folder:
                    folders.append(folder)

    candidates: dict[Path, Path] = {}

    def add_candidate(candidate: Path) -> None:
        located = locate_skills_dir(project_root, candidate)
        if located is not None:
            candidates[located[0]] = located[1]

    for folder in folders:
        add_candidate(project_root / folder.rstrip("/") / "skills")
    add_candidate(project_root / DEFAULT_SKILLS_DIR)

    from ..integration_state import integration_setting, try_read_integration_json

    state, error = try_read_integration_json(project_root)
    if error is None and integration_setting(state or {}, "generic"):
        from ..integrations.generic import registration_directory

        try:
            add_candidate(registration_directory(project_root))
        except (OSError, ValueError):
            # Recorded paths and static roots still allow safe cleanup.
            pass

    for agent_name, agent_config in registrar.AGENT_CONFIGS.items():
        if agent_config.get("extension") != "/SKILL.md":
            continue
        add_candidate(registrar._resolve_agent_dir(agent_name, agent_config, project_root))
    return candidates


def skill_roots(
    project_root: Path,
    *,
    skills_dir: Path | None = None,
    extra_roots: Iterable[Path] = (),
) -> dict[Path, Path]:
    """Return the skills directories extension cleanup may touch, with each root.

    This is the one answer to "which directories may hold an extension's
    skills": skill removal, resource retirement and the update backup all ask
    it. Without ``skills_dir`` that is every configured skills directory; with
    it, only that one. ``extra_roots`` adds earlier locations the caller proved
    from its own records, such as a generic output directory that moved.
    """
    roots: dict[Path, Path] = {}
    if skills_dir is None:
        roots.update(configured_skill_roots(project_root))
    else:
        located = locate_skills_dir(project_root, skills_dir)
        if located is not None:
            roots[located[0]] = located[1]
    for extra in extra_roots:
        located = locate_skills_dir(project_root, extra)
        if located is not None:
            roots[located[0]] = located[1]
    return roots


def historical_skill_roots(
    project_root: Path, recorded_paths: Iterable[object], skill_names: Iterable[str],
) -> list[Path]:
    """Derive the skills directories that recorded ``SKILL.md`` paths were written under."""
    names = [parts for parts in map(skill_name_parts, skill_names) if parts]
    roots: list[Path] = []
    for recorded in recorded_paths:
        if not isinstance(recorded, str) or "\\" in recorded:
            continue
        path = PurePosixPath(recorded)
        if path.is_absolute() or ".." in path.parts or path.name != "SKILL.md":
            continue
        directory = path.parts[:-1]
        for parts in names:
            if len(directory) > len(parts) and directory[-len(parts):] == parts:
                roots.append(Path(project_root).joinpath(*directory[:-len(parts)]))
    return roots


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
) -> tuple[list[Path], list[Path]]:
    """Remove recorded paths the caller already authorized; reject malformed keys.

    Authorization belongs to ``retire_skill_resources``. This only refuses keys
    that are not canonical relative paths, then deletes through the manifest
    safeguards (no symlink ancestors, files only).
    """
    manifest = IntegrationManifest(ext_id, trusted_root)
    dropped: list[Path] = []
    for key, digest in previous.items():
        path = PurePosixPath(key)
        if (
            not key or "\\" in key or path.is_absolute()
            or PureWindowsPath(key).drive or path.as_posix() != key
            or ".." in path.parts
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
    skills_dir = locate_skills_dir(project_root, skills_dir)[0]
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
        located = locate_skills_dir(
            project_root, registrar._resolve_agent_dir(name, config, project_root)
        )
        if located is not None and skills_resource_root(project_root, located[0])[0] == "home":
            dirs.append(located[0])
    return dirs


def _authorized_prefixes(
    roots: dict[Path, Path], trusted: Path, names: list[tuple[str, ...]],
) -> list[tuple[str, ...]]:
    """Root-relative directory prefixes ``<skills root>/<skill name>`` under *trusted*."""
    return [
        (*root.relative_to(trusted).parts, *name)
        for root, root_trusted in roots.items()
        if root_trusted == trusted
        for name in names
    ]


def retire_skill_resources(
    project_root: Path, ext_id: str, hashes: dict, skill_names: set[str],
    *, skills_dir: Path | None = None, extra_roots: Iterable[Path] = (),
) -> None:
    """Remove recorded resources for these skill names and forget their keys.

    A recorded path is removed only when it lies below
    ``<authorized skills directory>/<generated skill name>/``, anchored at that
    directory (see ``skill_roots``). The registry is project-controlled, so a
    record that merely names a directory, such as ``.git`` or ``src``, is
    never trusted. Without ``skills_dir`` the project bucket covers every
    configured skills directory plus ``extra_roots``. The home bucket is a far
    larger boundary and is only cleaned under the skills directories of agents
    that declare ``registrar_config["home_scoped"]``, as their ``SKILL.md``
    cleanup does; other records are left untouched.
    """
    import warnings

    names = [
        parts for parts in (skill_name_parts(n, generated_only=True) for n in skill_names)
        if parts
    ]
    if not names:
        return
    project, home = _boundaries(project_root)
    roots = skill_roots(project, skills_dir=skills_dir, extra_roots=extra_roots)
    if skills_dir is None:
        home_dirs = set(_home_skills_dirs(project))
        roots = {r: t for r, t in roots.items() if t == project or r in home_dirs}
    for bucket, trusted in (("project", project), ("home", home)):
        records = hashes.get(bucket)
        if not isinstance(records, dict):
            continue
        prefixes = _authorized_prefixes(roots, trusted, names)
        selected = {
            key: value for key, value in records.items()
            if isinstance(key, str) and any(
                (parts := PurePosixPath(key).parts)[:len(prefix)] == prefix
                and len(parts) > len(prefix)
                for prefix in prefixes
            )
        }
        if not selected:
            continue
        _, skipped = remove_skill_resources(ext_id, trusted, selected)
        for path in skipped:
            warnings.warn(f"Skipped unsafe skill resource {path}", stacklevel=2)
        for key in selected:
            records.pop(key, None)
        if not records:
            hashes.pop(bucket, None)
