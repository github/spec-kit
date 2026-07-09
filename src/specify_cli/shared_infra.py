"""Shared Spec Kit infrastructure installation helpers."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from .integrations.base import IntegrationBase
from .integrations.manifest import IntegrationManifest

logger = logging.getLogger(__name__)

# Matches a SHA-256 digest in its normalized form: exactly 64 hexadecimal
# characters. Callers lowercase the declared value before matching (see
# ``expected_hex = raw.lower()`` below), so an uppercase digest is accepted and
# normalized rather than rejected.
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def verify_archive_sha256(
    data: bytes,
    expected: str | None,
    name: str,
    error_cls: type[Exception],
) -> None:
    """Verify downloaded archive bytes against a catalog-declared SHA-256.

    Catalog entries may pin the expected digest of their release archive in a
    ``sha256`` field (optionally prefixed with ``"sha256:"``). When present, the
    downloaded bytes must match before they are written to disk and installed,
    so a corrupted or tampered archive is rejected even though the transport was
    HTTPS. Entries without a declared digest are accepted unchanged, keeping the
    check backwards compatible.

    Args:
        data: The raw downloaded archive bytes.
        expected: The catalog-declared SHA-256 hex digest, or ``None``.
        name: The extension/preset id, used in the error message.
        error_cls: Exception type to raise on mismatch (e.g. ``ExtensionError``).

    Raises:
        error_cls: If ``expected`` is provided and is not a well-formed
            SHA-256 hex digest, or does not match ``data``.
    """
    # Skip only when no digest is declared at all (``None``). A declared but
    # empty/blank value (e.g. ``sha256: ""``) is an authoring error, not an
    # opt-out: let it fall through to the format check below so it is rejected
    # rather than silently disabling verification.
    if expected is None:
        logger.debug(
            "No sha256 declared for %r; archive integrity was not verified.",
            name,
        )
        return
    # Strip *only* a literal ``sha256:`` algorithm prefix (case-insensitive).
    # Any other prefix is part of the value and must not be silently dropped,
    # otherwise a malformed or wrong-algorithm digest (e.g. ``md5:...``) would
    # be quietly accepted as if it were a valid SHA-256.
    raw = str(expected).strip()
    if raw[:7].lower() == "sha256:":
        raw = raw[7:].strip()
    expected_hex = raw.lower()
    if not _SHA256_HEX_RE.match(expected_hex):
        raise error_cls(
            f"Invalid sha256 declared for {name!r}: expected 64 hexadecimal "
            f"characters (optionally prefixed with 'sha256:'), got "
            f"{expected!r}."
        )
    actual_hex = hashlib.sha256(data).hexdigest()
    # Constant-time comparison: both sides are fixed-length hex digests, so use
    # ``hmac.compare_digest`` to avoid leaking information through timing.
    if not hmac.compare_digest(actual_hex, expected_hex):
        raise error_cls(
            f"Integrity check failed for {name!r}: the catalog declares "
            f"sha256 {expected_hex}, but the downloaded archive is "
            f"{actual_hex}. The archive may be corrupted or tampered with."
        )


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


def _ensure_safe_shared_directory(
    project_path: Path,
    directory: Path,
    *,
    create: bool = True,
    context: str = "shared infrastructure directory",
) -> None:
    """Create a shared infra directory without following symlinked parents."""
    root = project_path.resolve()
    rel = _shared_relative_path(project_path, directory)
    current = project_path

    for part in rel.parts:
        current = current / part
        label = _shared_destination_label(project_path, current)
        if current.is_symlink():
            raise SymlinkedSharedPathError(f"Refusing to use symlinked {context}: {label}")
        if current.exists():
            if not current.is_dir():
                raise ValueError(f"{context.capitalize()} path is not a directory: {label}")
            try:
                current.resolve().relative_to(root)
            except (OSError, ValueError):
                raise ValueError(f"{context.capitalize()} escapes project root: {label}") from None
            continue
        if not create:
            raise ValueError(f"{context.capitalize()} does not exist: {label}")
        current.mkdir()
        if current.is_symlink():
            raise SymlinkedSharedPathError(f"Refusing to use symlinked {context}: {label}")
        try:
            current.resolve().relative_to(root)
        except (OSError, ValueError):
            raise ValueError(f"{context.capitalize()} escapes project root: {label}") from None


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


_BASH_FORMAT_COMMAND_RE = re.compile(
    r"\$\(\s*format_speckit_command\s+(['\"]?)([A-Za-z0-9_.-]+)\1(?:\s+[^)]*)?\)"
)
_POWERSHELL_FORMAT_COMMAND_RE = re.compile(
    r"Format-SpecKitCommand\s+-CommandName\s+(['\"])([A-Za-z0-9_.-]+)\1(?:\s+-RepoRoot\s+[^\r\n]+)?"
)


def _format_speckit_command(command_name: str, separator: str) -> str:
    name = command_name.strip().lstrip("/")
    if name.startswith("speckit."):
        name = name[len("speckit.") :]
    elif name.startswith("speckit-"):
        name = name[len("speckit-") :]
    name = name.replace(".", separator)
    return f"/speckit{separator}{name}"


def _resolve_dynamic_command_refs(content: str, separator: str) -> str:
    """Render script runtime command helpers for managed shared infra copies."""

    content = _BASH_FORMAT_COMMAND_RE.sub(
        lambda match: _format_speckit_command(match.group(2), separator),
        content,
    )
    return _POWERSHELL_FORMAT_COMMAND_RE.sub(
        lambda match: f"'{_format_speckit_command(match.group(2), separator)}'",
        content,
    )


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
            if rel not in tracked_files or rel in modified or manifest.is_recovered(rel):
                # Never overwrite a recovered (pre-existing user) file without
                # --force, matching install_shared_infra's is_recovered gate
                # (#2918). Without this, refresh clobbers user content.
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
            f"[yellow]⚠[/yellow]  {len(skipped_files)} modified, untracked, or preserved (recovered) shared template file(s) were not updated:"
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
    from .integrations.manifest import _sha256, _validate_rel_path

    manifest = load_speckit_manifest(project_path, version=version, console=console)
    prior_hashes = dict(manifest.files)

    def _is_managed(rel: str, dst: Path) -> bool:
        expected = prior_hashes.get(rel)
        if not expected or not dst.is_file() or dst.is_symlink():
            return False
        if manifest.is_recovered(rel):
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
    # Track every shared path the current bundle produces so we can detect
    # manifest entries the core no longer ships (stale-script cleanup, #3076).
    seen_rels: set[str] = set()
    scripts_scanned = False
    variant_dir = {"sh": "bash", "py": "python"}.get(script_type, "powershell")

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
            variant_src = scripts_src / variant_dir
            if variant_src.is_dir():
                dest_variant = dest_scripts / variant_dir
                if _ensure_or_bucket_dir(dest_variant):
                    for src_path in variant_src.rglob("*"):
                        if not src_path.is_file():
                            continue
                        # Python bytecode caches are local artifacts, not
                        # workflow scripts — never install them.
                        if "__pycache__" in src_path.parts:
                            continue
                        # Mark scanned only once a real source file is seen. An
                        # empty (or symlink-skipped) variant keeps this False, so
                        # stale-cleanup is skipped — otherwise it would treat every
                        # tracked script as obsolete and delete it. (The safety
                        # hinge is this flag, not ``seen_rels``, which also holds
                        # template paths populated later.)
                        scripts_scanned = True

                        rel_path = src_path.relative_to(variant_src)
                        dst_path = dest_variant / rel_path
                        rel = dst_path.relative_to(project_path).as_posix()
                        seen_rels.add(rel)
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
                                        manifest.record_existing(rel, recovered=True)
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
                        content = src_path.read_text(encoding="utf-8")
                        content = IntegrationBase.resolve_command_refs(content, invoke_separator)
                        content = _resolve_dynamic_command_refs(content, invoke_separator)
                        planned_copies.append(
                            (
                                dst_path,
                                rel,
                                content.encode("utf-8"),
                                src_path.stat().st_mode & 0o777,
                            )
                        )

    templates_src = shared_templates_source(core_pack=core_pack, repo_root=repo_root)
    if templates_src.is_dir():
        dest_templates = project_path / ".specify" / "templates"
        if _ensure_or_bucket_dir(dest_templates):
            for src in templates_src.iterdir():
                if not src.is_file() or src.name == "vscode-settings.json" or src.name.startswith("."):
                    continue

                dst = dest_templates / src.name
                rel = dst.relative_to(project_path).as_posix()
                seen_rels.add(rel)
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
                                manifest.record_existing(rel, recovered=True)
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
            f"[yellow]⚠[/yellow]  {len(skipped_files)} shared infrastructure path(s) already exist and were not updated:"
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

    # Remove stale managed scripts: paths a previous install recorded that the
    # current core no longer ships — e.g. the legacy
    # ``scripts/<variant>/update-agent-context.sh`` superseded by the bundled
    # agent-context extension. Left behind, such an orphan can crash when it
    # sources a refreshed ``common.sh`` (#3076). Only run when the script source
    # was actually scanned (so a missing/empty source never triggers mass
    # deletion), scoped to the active variant, and only for *managed* copies —
    # a user-customized file (hash diverges), a symlink, or a recovered entry is
    # preserved by ``_is_managed``.
    if scripts_scanned:
        stale_removed: list[str] = []
        script_prefix = f".specify/scripts/{variant_dir}/"
        for rel in list(prior_hashes):
            if rel in seen_rels or not rel.startswith(script_prefix):
                continue
            # Guard corrupted/hand-edited manifest keys BEFORE any filesystem
            # access: absolute, ``..``, or (on Windows) drive-relative keys such
            # as ``C:tmp`` are not ``is_absolute()`` yet discard the project root
            # when joined. The lexical check is a fast reject; ``_validate_rel_path``
            # resolves the join and confirms containment, catching the rest. A key
            # that still escapes is *skipped*, never turned into an install-time
            # hard failure. Mirrors IntegrationManifest.is_recovered / remove.
            rel_path = Path(rel)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                continue
            try:
                _validate_rel_path(rel_path, project_path)
            except ValueError:
                continue
            dst = project_path / rel_path
            # Already gone from disk but still tracked: drop the orphaned manifest
            # entry so the manifest stays consistent (nothing to unlink).
            if not dst.exists() and not dst.is_symlink():
                manifest.remove(rel)
                continue
            if not _is_managed(rel, dst):
                continue  # user-modified / symlink / recovered → preserve
            # Never unlink through a symlinked ancestor (writes/deletes could
            # escape the project root). The safe-destination check buckets such
            # paths under ``symlinked_files`` and we leave them in place.
            if not _safe_dest_or_bucket(dst, rel):
                continue
            try:
                dst.unlink()
            except OSError as exc:
                console.print(f"[yellow]⚠[/yellow]  could not remove stale {rel}: {exc}")
                continue
            manifest.remove(rel)
            stale_removed.append(rel)

        if stale_removed:
            console.print(
                f"[yellow]⚠[/yellow]  Removed {len(stale_removed)} obsolete shared "
                "script(s) left by a previous install:"
            )
            for path in stale_removed:
                console.print(f"    {path}")

    manifest.save()
    return True
