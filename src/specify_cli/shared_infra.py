"""Shared Spec Kit infrastructure installation helpers."""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import logging
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any

from ._file_policy import project_files
from .file_helper import FileHelper, FileHelperError
from .integrations.base import IntegrationBase
from .integrations._file_changes import observe_directory_change, observe_file_change
from .integrations.manifest import IntegrationManifest

logger = logging.getLogger(__name__)

# Managed ``.specify/.gitignore``. Keeps machine-local Spec Kit state out of
# version control while leaving shareable project files (specs, constitution,
# templates, scripts, extension config) tracked. Patterns are relative to the
# ``.specify/`` directory the file lives in.
SPECIFY_GITIGNORE_CONTENT = """\
# Machine-local Spec Kit state — not meant to be shared.
# Managed by the Specify CLI; safe to edit (your changes are preserved on refresh).

# Local pointer to the current feature directory. Rewritten every time you
# switch features, so it is per-checkout state rather than something to share.
feature.json

# Per-machine extension config overrides.
extensions/*/local-config.yml

# Executable adapter packages and their per-checkout provenance registry.
# Execution consent is stored separately in the user's local trust registry.
integrations/packages/
integrations/packages.json
"""

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


def _shared_file_id(files: FileHelper, path: Path | str) -> tuple[int, int] | None:
    entry = files.stat(path, missing_ok=True)
    if entry is not None and stat.S_ISREG(entry.st_mode):
        return entry.st_dev, entry.st_ino
    return None


def load_speckit_manifest(
    project_path: Path,
    *,
    version: str,
    console: Any | None = None,
    files: FileHelper | None = None,
) -> IntegrationManifest:
    """Load the shared infrastructure manifest, preserving existing entries."""
    project_path = Path(project_path).absolute()
    manifest_path = project_path / ".specify" / "integrations" / "speckit.manifest.json"
    files = files if files is not None else project_files(project_path)
    if files.stat(manifest_path, missing_ok=True) is not None:
        try:
            manifest = IntegrationManifest.load("speckit", project_path, files=files)
            manifest.version = version
            return manifest
        except (FileHelperError, FileNotFoundError):
            raise
        except (ValueError, OSError, UnicodeDecodeError) as exc:
            if console is not None:
                console.print(
                    f"[yellow]Warning:[/yellow] Could not read shared infrastructure "
                    f"manifest at {manifest_path}: {exc}"
                )
                console.print(
                    "A new shared manifest will be created; previously tracked "
                    "shared files may be treated as untracked."
                )
    return IntegrationManifest("speckit", project_path, version=version, files=files)


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


@contextlib.contextmanager
def _exclusive_project_lock(project_root: Path, lock_name: str, *, context: str):
    """Hold an exclusive inter-process lock on ``.specify/<lock_name>``.

    Callers use one lock file per mutable project resource so that its
    directory and registry changes are serialized across processes. Every
    failure to acquire the lock is raised as ``OSError``.
    """
    project_root = Path(project_root)
    lock_dir = project_root / ".specify"
    try:
        _ensure_safe_shared_directory(
            project_root, lock_dir, context=f"{context} lock directory"
        )
    except ValueError as exc:
        raise OSError(str(exc)) from exc
    lock_file = lock_dir / lock_name
    if lock_file.is_symlink():
        raise OSError(f"Refusing to use symlinked {context} lock: {lock_file}")

    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    fd = os.open(lock_file, flags, 0o600)
    try:
        if lock_file.is_symlink():
            raise OSError(f"Refusing to use symlinked {context} lock: {lock_file}")
        # Call the lock primitives through their modules so tests can observe
        # contention by patching ``msvcrt.locking`` / ``fcntl.flock``.
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
    from .integrations._file_changes import after_file_change, before_file_change

    before_file_change(dest)
    fd, temp_name = tempfile.mkstemp(prefix=f".{dest.name}.", dir=dest.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        temp_path.chmod(mode)
        _ensure_safe_shared_destination(project_path, dest)
        os.replace(temp_path, dest)
        after_file_change(dest)
    finally:
        temp_path.unlink(missing_ok=True)


_BASH_FORMAT_COMMAND_RE = re.compile(
    r"\$\(\s*format_speckit_command\s+(['\"]?)([A-Za-z0-9_.-]+)\1(?:\s+[^)]*)?\)"
)
_POWERSHELL_FORMAT_COMMAND_RE = re.compile(
    r"Format-SpecKitCommand\s+-CommandName\s+(['\"])([A-Za-z0-9_.-]+)\1(?:\s+-RepoRoot\s+[^\r\n]+)?"
)
_PYTHON_FORMAT_COMMAND_RETURN_RE = re.compile(
    r'return f"/speckit\{separator\}\{name\}"'
)
_BASH_FORMATTER_RETURN_RE = re.compile(
    r'''printf '/speckit%s%s\\n' "\$separator" "\$command_name"'''
)
_POWERSHELL_FORMATTER_RETURN_RE = re.compile(
    r'return "/speckit\$separator\$name"'
)


def _format_speckit_command(
    command_name: str, separator: str, prefix: str = "/"
) -> str:
    name = command_name.strip().lstrip("/")
    if name.startswith("speckit."):
        name = name[len("speckit.") :]
    elif name.startswith("speckit-"):
        name = name[len("speckit-") :]
    name = name.replace(".", separator)
    return f"{prefix}speckit{separator}{name}"


def _resolve_dynamic_command_refs(
    content: str, separator: str, prefix: str = "/"
) -> str:
    """Render script runtime command helpers for managed shared infra copies."""

    bash_prefix = r"\$" if prefix == "$" else prefix
    content = _BASH_FORMAT_COMMAND_RE.sub(
        lambda match: _format_speckit_command(
            match.group(2), separator, bash_prefix
        ),
        content,
    )
    content = _POWERSHELL_FORMAT_COMMAND_RE.sub(
        lambda match: f"'{_format_speckit_command(match.group(2), separator, prefix)}'",
        content,
    )
    content = _BASH_FORMATTER_RETURN_RE.sub(
        f'''printf '{prefix}speckit%s%s\\\\n' "$separator" "$command_name"''',
        content,
    )
    powershell_prefix = "`$" if prefix == "$" else prefix
    content = _POWERSHELL_FORMATTER_RETURN_RE.sub(
        f'return "{powershell_prefix}speckit$separator$name"',
        content,
    )
    return _PYTHON_FORMAT_COMMAND_RETURN_RE.sub(
        f'return f"{prefix}speckit{{separator}}{{name}}"',
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
    invoke_prefix: str = "/",
    force: bool = False,
    files: FileHelper | None = None,
) -> None:
    """Refresh selected bundled templates without inspecting other tracked files.

    Modification checks cover only the destinations this refresh produces;
    unrelated manifest entries retain their hashes and ownership records.
    """
    project_path = Path(project_path).absolute()
    templates_src = shared_templates_source(core_pack=core_pack, repo_root=repo_root)
    if not templates_src.is_dir():
        return

    files = files if files is not None else project_files(project_path)
    manifest = load_speckit_manifest(project_path, version=version, console=console, files=files)
    tracked_files = manifest.files
    templates = [
        src for src in templates_src.iterdir()
        if src.is_file() and src.name != "vscode-settings.json" and not src.name.startswith(".")
    ]
    modified = set(manifest.check_modified(
        paths={f".specify/templates/{src.name}" for src in templates},
    ))
    skipped_files: list[str] = []
    planned_updates: list[tuple[Path, str, str]] = []
    preserved_targets: set[tuple[int, int]] = set()

    dest_templates = project_path / ".specify" / "templates"
    files.mkdir(dest_templates, parents=True, exist_ok=True, observer=observe_directory_change)
    for src in templates:
        dst = dest_templates / src.name
        entry = files.stat(dst, missing_ok=True)
        rel = dst.relative_to(project_path).as_posix()
        if entry is not None and not force:
            if rel not in tracked_files or rel in modified or manifest.is_recovered(rel):
                # Never overwrite a recovered (pre-existing user) file without
                # --force, matching install_shared_infra's is_recovered gate
                # (#2918). Without this, refresh clobbers user content.
                skipped_files.append(rel)
                if stat.S_ISREG(entry.st_mode):
                    preserved_targets.add((entry.st_dev, entry.st_ino))
                continue

        content = src.read_text(encoding="utf-8")
        content = IntegrationBase.resolve_command_refs(
            content, invoke_separator, invoke_prefix
        )
        planned_updates.append((dst, rel, content))

    written_rels: list[str] = []
    for dst, rel, content in planned_updates:
        if preserved_targets and _shared_file_id(files, dst) in preserved_targets:
            skipped_files.append(rel)
            continue
        files.write_text(dst, content, observer=observe_file_change)
        written_rels.append(rel)

    # Allowed aliases can share targets; record their final bytes after all writes.
    for rel in written_rels:
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
    invoke_prefix: str = "/",
    refresh_managed: bool = False,
    refresh_hint: str | None = None,
    files: FileHelper | None = None,
) -> bool:
    """Install shared scripts and templates into *project_path*.

    When ``refresh_managed`` is True, files whose on-disk hash still matches
    the previously recorded manifest hash are overwritten with the bundled
    version. Files whose hash diverges are treated as user customizations and
    preserved with a warning. ``force=True`` overwrites every regular file
    permitted by the operation's FileHelper policy, preserving allowed links.
    Denied or invalid accessed links fail explicitly. Stale cleanup paths are
    policy-checked before planned file writes. ``refresh_hint`` is shown after the
    customization warning to tell the user which flag would overwrite their
    customizations.
    """
    project_path = Path(project_path).absolute()
    files = files if files is not None else project_files(project_path)
    manifest = load_speckit_manifest(project_path, version=version, console=console, files=files)
    prior_hashes = dict(manifest.files)

    def _is_file(dst: Path) -> bool:
        entry = files.stat(dst, missing_ok=True)
        return entry is not None and stat.S_ISREG(entry.st_mode)

    def _is_managed(rel: str, dst: Path) -> bool:
        expected = prior_hashes.get(rel)
        if not expected or not _is_file(dst):
            return False
        if manifest.is_recovered(rel):
            return False
        try:
            return hashlib.sha256(files.read_bytes(dst)).hexdigest() == expected
        except FileNotFoundError:
            raise
        except OSError:
            return False

    skipped_files: list[str] = []
    preserved_user_files: list[str] = []
    planned_copies: list[tuple[Path, str, bytes, int]] = []
    planned_templates: list[tuple[Path, str, str]] = []
    planned_stale: list[tuple[str, Path]] = []
    preserved_targets: set[tuple[int, int]] = set()
    # Track every shared path the current bundle produces so we can detect
    # manifest entries the core no longer ships (stale-script cleanup, #3076).
    seen_rels: set[str] = set()
    scanned_variant_dirs: set[str] = set()
    shell_variant = "powershell" if os.name == "nt" else "bash"
    variant_dirs = (
        ("python", shell_variant)
        if script_type == "py"
        else ("bash" if script_type == "sh" else "powershell",)
    )

    def _decide_overwrite(rel: str, dst: Path) -> tuple[bool, str | None]:
        """Return (write, bucket) where bucket is 'skip', 'preserved', or None."""
        if files.stat(dst, missing_ok=True) is None:
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

    def _ensure_dir(directory: Path) -> None:
        files.mkdir(directory, parents=True, exist_ok=True, observer=observe_directory_change)

    def _consider_destination(dst: Path, rel: str) -> bool:
        write, bucket = _decide_overwrite(rel, dst)
        if write:
            return True
        identity = _shared_file_id(files, dst)
        if identity is not None:
            preserved_targets.add(identity)
        if bucket == "preserved":
            preserved_user_files.append(rel)
        else:
            skipped_files.append(rel)
            # Observed files are recovered, not a managed baseline (#2107).
            if rel not in prior_hashes and _is_file(dst):
                try:
                    manifest.record_existing(rel, recovered=True)
                except (FileHelperError, FileNotFoundError):
                    raise
                except (OSError, ValueError) as exc:
                    console.print(
                        f"[yellow]⚠[/yellow]  could not record {rel} in manifest: {exc}"
                    )
        return False

    scripts_src = shared_scripts_source(core_pack=core_pack, repo_root=repo_root)
    if scripts_src.is_dir():
        dest_scripts = project_path / ".specify" / "scripts"
        _ensure_dir(dest_scripts)
        for variant_dir in variant_dirs:
            variant_src = scripts_src / variant_dir
            if not variant_src.is_dir():
                continue
            dest_variant = dest_scripts / variant_dir
            _ensure_dir(dest_variant)
            for src_path in variant_src.rglob("*"):
                if not src_path.is_file():
                    continue
                if "__pycache__" in src_path.parts:
                    continue
                # Empty/missing sources never trigger stale cleanup.
                scanned_variant_dirs.add(variant_dir)
                dst_path = dest_variant / src_path.relative_to(variant_src)
                rel = dst_path.relative_to(project_path).as_posix()
                seen_rels.add(rel)
                if not _consider_destination(dst_path, rel):
                    continue
                _ensure_dir(dst_path.parent)
                content = src_path.read_text(encoding="utf-8")
                content = IntegrationBase.resolve_command_refs(
                    content, invoke_separator, invoke_prefix
                )
                content = _resolve_dynamic_command_refs(
                    content, invoke_separator, invoke_prefix
                )
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
        _ensure_dir(dest_templates)
        for src in templates_src.iterdir():
            if not src.is_file() or src.name == "vscode-settings.json" or src.name.startswith("."):
                continue

            dst = dest_templates / src.name
            rel = dst.relative_to(project_path).as_posix()
            seen_rels.add(rel)
            if not _consider_destination(dst, rel):
                continue

            content = src.read_text(encoding="utf-8")
            content = IntegrationBase.resolve_command_refs(
                content, invoke_separator, invoke_prefix
            )
            planned_templates.append((dst, rel, content))

    # Managed ``.specify/.gitignore`` — keeps machine-local state (the
    # ``feature.json`` pointer and per-machine ``local-config.yml`` overrides)
    # out of git while leaving everything else shareable. Routed through the
    # same overwrite/skip/preserve policy as templates so ``--force`` refreshes
    # it and user edits are preserved. Like every other shared-infra file it is
    # tracked in ``speckit.manifest.json`` (not the per-integration manifest) and
    # is therefore intentionally left in place by ``integration uninstall``.
    specify_dir = project_path / ".specify"
    _ensure_dir(specify_dir)
    gitignore_dst = specify_dir / ".gitignore"
    gitignore_rel = gitignore_dst.relative_to(project_path).as_posix()
    seen_rels.add(gitignore_rel)
    if _consider_destination(gitignore_dst, gitignore_rel):
        planned_templates.append(
            (gitignore_dst, gitignore_rel, SPECIFY_GITIGNORE_CONTENT)
        )

    # Validate stale paths before overwriting shared files. Ownership is checked
    # again during cleanup because writes through aliases can change the bytes.
    if scanned_variant_dirs:
        script_prefixes = tuple(
            f".specify/scripts/{variant_dir}/" for variant_dir in scanned_variant_dirs
        )
        for rel in prior_hashes:
            if rel in seen_rels or not rel.startswith(script_prefixes):
                continue
            rel_path = Path(rel)
            if rel_path.anchor or any(
                part == ".." or Path(part).anchor for part in rel_path.parts
            ):
                continue
            dst = project_path / rel_path
            files.stat(dst, follow_symlinks=False, missing_ok=True)
            planned_stale.append((rel, dst))

    written_rels: list[str] = []
    for dst_path, rel, content, mode in planned_copies:
        if preserved_targets and _shared_file_id(files, dst_path) in preserved_targets:
            skipped_files.append(rel)
            continue
        _ensure_dir(dst_path.parent)
        files.write_bytes(dst_path, content, mode=mode, observer=observe_file_change)
        written_rels.append(rel)

    for dst, rel, content in planned_templates:
        if preserved_targets and _shared_file_id(files, dst) in preserved_targets:
            skipped_files.append(rel)
            continue
        files.write_text(dst, content, observer=observe_file_change)
        written_rels.append(rel)

    # Templates may overwrite a script target through an allowed alias.
    for rel in written_rels:
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
    # deletion), scoped to the selected variants, and only for *managed* copies —
    # a user-customized file (hash diverges), a symlink, or a recovered entry is
    # preserved by the leaf-identity and managed-hash checks.
    if planned_stale:
        live_file_ids: set[tuple[int, int]] = set()
        for rel in seen_rels:
            entry = files.stat(rel, missing_ok=True)
            if entry is not None and stat.S_ISREG(entry.st_mode):
                live_file_ids.add((entry.st_dev, entry.st_ino))
        stale_removed: list[str] = []
        for rel, dst in planned_stale:
            entry = files.stat(dst, follow_symlinks=False, missing_ok=True)
            # Already gone from disk but still tracked: drop the orphaned manifest
            # entry so the manifest stays consistent (nothing to unlink).
            if entry is None:
                manifest.remove(rel)
                continue
            if stat.S_ISLNK(entry.st_mode):
                continue
            if (entry.st_dev, entry.st_ino) in live_file_ids:
                continue
            if not _is_managed(rel, dst):
                continue  # user-modified / symlink / recovered → preserve
            try:
                files.delete(dst, observer=observe_file_change)
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
