"""Shared Spec Kit infrastructure installation helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from .integrations.base import IntegrationBase
from .integrations.manifest import IntegrationManifest


class SymlinkedSharedPathError(ValueError):
    """Raised when a shared infrastructure path or ancestor is a symlink.

    Distinct from other unsafe-path errors so callers can preserve symlinked
    destinations as customizations while still letting genuine safety errors
    (e.g. path escape, not-a-directory) propagate and abort the operation.
    """


def load_speckit_manifest(
    project_path: Path,
    *,
    version: str,
    console: Any | None = None,
) -> IntegrationManifest:
    """Load the shared infrastructure manifest, preserving existing entries."""
    manifest_path = project_path / ".specify" / "integrations" / "speckit.manifest.json"
    if manifest_path.exists():
        try:
            manifest = IntegrationManifest.load("speckit", project_path)
            manifest.version = version
            return manifest
        except (ValueError, FileNotFoundError, OSError, UnicodeDecodeError) as exc:
            if console is not None:
                console.print(
                    f"[yellow]Warning:[/yellow] Could not read shared infrastructure "
                    f"manifest at {manifest_path}: {exc}"
                )
                console.print(
                    "A new shared manifest will be created; previously tracked "
                    "shared files may be treated as untracked."
                )
    return IntegrationManifest("speckit", project_path, version=version)


def shared_templates_source(
    *,
    core_pack: Path | None,
    repo_root: Path,
) -> Path:
    """Return the bundled/source shared templates directory."""
    if core_pack and (core_pack / "templates").is_dir():
        return core_pack / "templates"
    return repo_root / "templates"


def shared_scripts_source(
    *,
    core_pack: Path | None,
    repo_root: Path,
) -> Path:
    """Return the bundled/source shared scripts directory."""
    if core_pack and (core_pack / "scripts").is_dir():
        return core_pack / "scripts"
    return repo_root / "scripts"


def _shared_destination_label(project_path: Path, dest: Path) -> str:
    try:
        return dest.relative_to(project_path).as_posix()
    except ValueError:
        return str(dest)


def _shared_relative_path(project_path: Path, dest: Path) -> Path:
    try:
        rel = dest.relative_to(project_path)
    except ValueError:
        label = _shared_destination_label(project_path, dest)
        raise ValueError(f"Shared infrastructure path escapes project root: {label}") from None

    if rel.is_absolute() or ".." in rel.parts:
        label = _shared_destination_label(project_path, dest)
        raise ValueError(f"Shared infrastructure path escapes project root: {label}")
    return rel


def _ensure_safe_shared_directory(project_path: Path, directory: Path, *, create: bool = True) -> None:
    """Create a shared infra directory without following symlinked parents."""
    root = project_path.resolve()
    rel = _shared_relative_path(project_path, directory)
    current = project_path

    for part in rel.parts:
        current = current / part
        label = _shared_destination_label(project_path, current)
        if current.is_symlink():
            raise SymlinkedSharedPathError(f"Refusing to use symlinked shared infrastructure directory: {label}")
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"Shared infrastructure directory path is not a directory: {label}")
            try:
                current.resolve().relative_to(root)
            except (OSError, ValueError):
                raise ValueError(f"Shared infrastructure directory escapes project root: {label}") from None
            continue
        if not create:
            raise ValueError(f"Shared infrastructure directory does not exist: {label}")
        current.mkdir()
        if current.is_symlink():
            raise SymlinkedSharedPathError(f"Refusing to use symlinked shared infrastructure directory: {label}")
        try:
            current.resolve().relative_to(root)
        except (OSError, ValueError):
            raise ValueError(f"Shared infrastructure directory escapes project root: {label}") from None


def _validate_safe_shared_directory(project_path: Path, directory: Path) -> None:
    """Validate existing directory parents while allowing missing directories."""
    root = project_path.resolve()
    rel = _shared_relative_path(project_path, directory)
    current = project_path

    for part in rel.parts:
        current = current / part
        label = _shared_destination_label(project_path, current)
        if current.is_symlink():
            raise SymlinkedSharedPathError(f"Refusing to use symlinked shared infrastructure directory: {label}")
        if not current.exists():
            continue
        if not current.is_dir():
            raise ValueError(f"Shared infrastructure directory path is not a directory: {label}")
        try:
            current.resolve().relative_to(root)
        except (OSError, ValueError):
            raise ValueError(f"Shared infrastructure directory escapes project root: {label}") from None


def _ensure_safe_shared_destination(
    project_path: Path,
    dest: Path,
    *,
    parent_must_exist: bool = True,
) -> None:
    """Refuse shared infra writes that would escape or follow symlinks."""
    root = project_path.resolve()
    _shared_relative_path(project_path, dest)
    if parent_must_exist:
        _ensure_safe_shared_directory(project_path, dest.parent, create=False)
    else:
        _validate_safe_shared_directory(project_path, dest.parent)
    label = _shared_destination_label(project_path, dest)
    if dest.is_symlink():
        raise SymlinkedSharedPathError(f"Refusing to overwrite symlinked shared infrastructure path: {label}")

    if dest.exists():
        try:
            dest.resolve().relative_to(root)
        except (OSError, ValueError):
            raise ValueError(f"Shared infrastructure destination escapes project root: {label}") from None


def _write_shared_text(project_path: Path, dest: Path, content: str) -> None:
    _write_shared_bytes(project_path, dest, content.encode("utf-8"))


def _write_shared_bytes(
    project_path: Path,
    dest: Path,
    content: bytes,
    *,
    mode: int = 0o644,
) -> None:
    _ensure_safe_shared_destination(project_path, dest)
    fd, temp_name = tempfile.mkstemp(prefix=f".{dest.name}.", dir=dest.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        temp_path.chmod(mode)
        _ensure_safe_shared_destination(project_path, dest)
        os.replace(temp_path, dest)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def refresh_shared_templates(
    project_path: Path,
    *,
    version: str,
    core_pack: Path | None,
    repo_root: Path,
    console: Any,
    invoke_separator: str,
    force: bool = False,
) -> None:
    """Refresh default-sensitive shared templates without touching scripts."""
    templates_src = shared_templates_source(core_pack=core_pack, repo_root=repo_root)
    if not templates_src.is_dir():
        return

    manifest = load_speckit_manifest(project_path, version=version, console=console)
    tracked_files = manifest.files
    modified = set(manifest.check_modified())
    skipped_files: list[str] = []
    planned_updates: list[tuple[Path, str, str]] = []

    dest_templates = project_path / ".specify" / "templates"
    _ensure_safe_shared_directory(project_path, dest_templates)
    for src in templates_src.iterdir():
        if not src.is_file() or src.name == "vscode-settings.json" or src.name.startswith("."):
            continue

        dst = dest_templates / src.name
        _ensure_safe_shared_destination(project_path, dst)
        rel = dst.relative_to(project_path).as_posix()
        if dst.exists() and not force:
            if rel not in tracked_files or rel in modified:
                skipped_files.append(rel)
                continue

        content = src.read_text(encoding="utf-8")
        content = IntegrationBase.resolve_command_refs(content, invoke_separator)
        planned_updates.append((dst, rel, content))

    for dst, rel, content in planned_updates:
        _write_shared_text(project_path, dst, content)
        manifest.record_existing(rel)

    manifest.save()

    if skipped_files:
        console.print(
            f"[yellow]⚠[/yellow]  {len(skipped_files)} modified or untracked shared template file(s) were not updated:"
        )
        for rel in skipped_files:
            console.print(f"    {rel}")


def install_shared_infra(
    project_path: Path,
    script_type: str,
    *,
    version: str,
    core_pack: Path | None,
    repo_root: Path,
    console: Any,
    force: bool = False,
    invoke_separator: str = ".",
    refresh_managed: bool = False,
    refresh_hint: str | None = None,
) -> bool:
    """Install shared scripts and templates into *project_path*.

    When ``refresh_managed`` is True, files whose on-disk hash still matches
    the previously recorded manifest hash are overwritten with the bundled
    version. Files whose hash diverges are treated as user customizations and
    preserved with a warning. ``force=True`` overwrites every regular file
    (symlinks and symlinked-parent destinations are always preserved with a
    warning — the safe-destination check refuses to follow them so writes
    cannot escape the project root). ``refresh_hint`` is shown after the
    customization warning to tell the user which flag would overwrite their
    customizations.
    """
    from .integrations.manifest import _sha256

    manifest = load_speckit_manifest(project_path, version=version, console=console)
    prior_hashes = dict(manifest.files)

    def _is_managed(rel: str, dst: Path) -> bool:
        expected = prior_hashes.get(rel)
        if not expected or not dst.is_file() or dst.is_symlink():
            return False
        try:
            return _sha256(dst) == expected
        except OSError:
            return False

    skipped_files: list[str] = []
    preserved_user_files: list[str] = []
    symlinked_files: list[str] = []
    planned_copies: list[tuple[Path, str, bytes, int]] = []
    planned_templates: list[tuple[Path, str, str]] = []

    def _decide_overwrite(rel: str, dst: Path) -> tuple[bool, str | None]:
        """Return (write, bucket) where bucket is 'skip', 'preserved', or None."""
        if not dst.exists():
            return True, None
        if force:
            return True, None
        if refresh_managed:
            if _is_managed(rel, dst):
                return True, None
            if rel in prior_hashes:
                return False, "preserved"
            return False, "skip"
        return False, "skip"

    def _safe_dest_or_bucket(dst: Path, rel: str, *, parent_must_exist: bool = True) -> bool:
        """Run the safe-destination check and bucket symlinked paths.

        Returns True when the destination is safe to consider (write or skip).
        Returns False (and records *rel* under ``symlinked_files``) when the
        destination or any of its ancestors is a symlink — those paths can't
        be written to safely, but they shouldn't abort the whole switch
        either. They're surfaced as a separate "symlinked" warning bucket.

        Other unsafe-path errors (e.g. path escape, parent-not-a-directory)
        are NOT caught here: they re-raise so the operation aborts, since
        treating them as "symlinked" would mask security-relevant failures.
        """
        try:
            _ensure_safe_shared_destination(project_path, dst, parent_must_exist=parent_must_exist)
        except SymlinkedSharedPathError:
            symlinked_files.append(rel)
            return False
        return True

    def _ensure_or_bucket_dir(directory: Path) -> bool:
        """Create *directory* unless an ancestor is symlinked.

        Returns True when the directory is safe to use. Returns False (and
        records the path under ``symlinked_files``) when a symlink ancestor
        forces us to skip the whole subtree. Other unsafe-path errors
        (escape, not-a-directory) re-raise so the operation aborts.
        """
        try:
            _ensure_safe_shared_directory(project_path, directory)
        except SymlinkedSharedPathError:
            symlinked_files.append(directory.relative_to(project_path).as_posix())
            return False
        return True

    scripts_src = shared_scripts_source(core_pack=core_pack, repo_root=repo_root)
    if scripts_src.is_dir():
        dest_scripts = project_path / ".specify" / "scripts"
        if _ensure_or_bucket_dir(dest_scripts):
            variant_dir = "bash" if script_type == "sh" else "powershell"
            variant_src = scripts_src / variant_dir
            if variant_src.is_dir():
                dest_variant = dest_scripts / variant_dir
                if _ensure_or_bucket_dir(dest_variant):
                    for src_path in variant_src.rglob("*"):
                        if not src_path.is_file():
                            continue

                        rel_path = src_path.relative_to(variant_src)
                        dst_path = dest_variant / rel_path
                        rel = dst_path.relative_to(project_path).as_posix()
                        if not _safe_dest_or_bucket(dst_path, rel, parent_must_exist=False):
                            continue
                        write, bucket = _decide_overwrite(rel, dst_path)
                        if not write:
                            if bucket == "preserved":
                                preserved_user_files.append(rel)
                            else:
                                skipped_files.append(rel)
                                # Record the existing-on-disk file in the manifest so a
                                # fresh manifest run against an already-populated
                                # ``.specify/`` tree does not silently drop it (#2107).
                                # ``prior_hashes`` is the function-scope snapshot taken
                                # at entry, so this membership check is O(1) and avoids
                                # the repeated ``dict(self._files)`` copy that
                                # ``manifest.files`` performs on every access.
                                if dst_path.is_file() and rel not in prior_hashes:
                                    try:
                                        manifest.record_existing(rel)
                                    except (OSError, ValueError) as exc:
                                        # Tolerate races / permission issues / non-file
                                        # collisions so one weird path does not abort
                                        # the whole install.
                                        console.print(
                                            f"[yellow]⚠[/yellow]  could not record {rel} in manifest: {exc}"
                                        )
                            continue

                        if not _ensure_or_bucket_dir(dst_path.parent):
                            continue
                        planned_copies.append((dst_path, rel, src_path.read_bytes(), src_path.stat().st_mode & 0o777))

    templates_src = shared_templates_source(core_pack=core_pack, repo_root=repo_root)
    if templates_src.is_dir():
        dest_templates = project_path / ".specify" / "templates"
        if _ensure_or_bucket_dir(dest_templates):
            for src in templates_src.iterdir():
                if not src.is_file() or src.name == "vscode-settings.json" or src.name.startswith("."):
                    continue

                dst = dest_templates / src.name
                rel = dst.relative_to(project_path).as_posix()
                if not _safe_dest_or_bucket(dst, rel):
                    continue
                write, bucket = _decide_overwrite(rel, dst)
                if not write:
                    if bucket == "preserved":
                        preserved_user_files.append(rel)
                    else:
                        skipped_files.append(rel)
                        # Record the existing-on-disk template in the manifest so a
                        # fresh manifest run against an already-populated
                        # ``.specify/`` tree does not silently drop it (#2107).
                        # ``prior_hashes`` is the function-scope snapshot taken at
                        # entry, so this membership check is O(1) and avoids the
                        # repeated ``dict(self._files)`` copy that ``manifest.files``
                        # performs on every access.
                        if dst.is_file() and rel not in prior_hashes:
                            try:
                                manifest.record_existing(rel)
                            except (OSError, ValueError) as exc:
                                # Tolerate races / permission issues / non-file
                                # collisions so one weird path does not abort
                                # the whole install.
                                console.print(
                                    f"[yellow]⚠[/yellow]  could not record {rel} in manifest: {exc}"
                                )
                    continue

                content = src.read_text(encoding="utf-8")
                content = IntegrationBase.resolve_command_refs(content, invoke_separator)
                planned_templates.append((dst, rel, content))

    for dst_path, rel, content, mode in planned_copies:
        if not _ensure_or_bucket_dir(dst_path.parent):
            continue
        _write_shared_bytes(project_path, dst_path, content, mode=mode)
        manifest.record_existing(rel)

    for dst, rel, content in planned_templates:
        _write_shared_text(project_path, dst, content)
        manifest.record_existing(rel)

    if skipped_files:
        console.print(
            f"[yellow]⚠[/yellow]  {len(skipped_files)} shared infrastructure file(s) already exist and were not updated:"
        )
        for path in skipped_files:
            console.print(f"    {path}")
        if refresh_managed and refresh_hint:
            console.print(refresh_hint)
        else:
            console.print(
                "To refresh shared infrastructure, run "
                "[cyan]specify init --here --force[/cyan] or "
                "[cyan]specify integration upgrade --force[/cyan]."
            )

    if symlinked_files:
        console.print(
            f"[yellow]⚠[/yellow]  Skipped {len(symlinked_files)} symlinked shared "
            "infrastructure path(s) — symlinks are never overwritten because they "
            "may resolve outside the project root:"
        )
        for path in symlinked_files:
            console.print(f"    {path}")
        console.print(
            "To restore the bundled version, remove or replace the symlink manually, "
            "then re-run the command."
        )

    if preserved_user_files:
        console.print(
            f"[yellow]⚠[/yellow]  Preserved {len(preserved_user_files)} customized shared "
            "infrastructure file(s) (hash differs from previous install):"
        )
        for path in preserved_user_files:
            console.print(f"    {path}")
        if refresh_hint:
            console.print(refresh_hint)

    manifest.save()
    return True
