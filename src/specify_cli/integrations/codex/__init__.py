"""Codex CLI integration — skills-based agent.

Codex uses the ``.agents/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.
"""

from __future__ import annotations

import errno
import hashlib
import logging
import os
import re
import stat
import sys
from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from ...file_helper import (
    FileHelper, FileHelperError, SymlinkDeniedError, UnsupportedPathError,
)
from .._file_changes import before_file_change, changing_file
from ..base import (
    IntegrationOption,
    SkillsIntegration,
    check_dispatch_settings,
    requested_dispatch_settings,
)
# The manifest has no public validator; this is the check ``record_file`` and
# ``record_existing`` apply, so policies are planned, cleaned up and recorded by
# the same lexical path. Pinned by ``TestCodexManifestInternals``.
from ..manifest import IntegrationManifest, _validate_record_path
from . import _openai_yaml

logger = logging.getLogger(__name__)

# ``model_context_window`` is a TOML integer that Codex reads as an i64.
_CONTEXT_WINDOW = re.compile(r"[1-9][0-9]*")
_MAX_CONTEXT_WINDOW = 2**63 - 1


_BACKUP_SUFFIX = ".speckit-backup"


def _read_policy(root: Path, rel: str) -> bytes:
    """Read ``rel`` without following a symlinked ancestor out of ``root``."""
    with FileHelper(root) as helper:
        return helper.read_bytes(rel)


def _replace_file(
    root: Path,
    rel: str,
    content: bytes,
    on_written: Callable[[bytes], None] | None = None,
    *,
    expected: bytes | None = None,
) -> bytes:
    """Rewrite an existing file in place and return its previous bytes.

    Writing through the same file keeps its owner, group, access-control list
    and other attributes, which a sibling-and-rename swap would replace with
    the directory's defaults. Every step goes through ``FileHelper``, which
    opens each ancestor without following links, so a directory swapped for a
    symlink part-way cannot redirect the write outside the project, and the
    file written must be the one that was read.

    Until the new bytes are on disk and the backup is gone, a copy of the
    previous ones is kept beside the file as ``<name>.speckit-backup``. The
    backup is created exclusively and readable by the current user only (on
    Windows, through an access-control list set as it is created): one left
    by an interrupted run stops the rewrite instead of being overwritten. A failure up to and including
    removing the backup restores the previous bytes before it propagates.
    ``on_written`` receives the previous bytes once the rewrite is complete,
    so a caller can still undo it if closing the file fails afterwards.
    Read-only and hard-linked files are refused, as is a file whose bytes
    differ from ``expected``, the bytes ``content`` was derived from, or that
    changes between being read and being opened for writing.
    """
    backup_rel = f"{rel}{_BACKUP_SUFFIX}"
    with FileHelper(root) as helper:
        read = helper.stat(rel)
        original = helper.read_bytes(rel)
        if expected is not None and original != expected:
            raise PermissionError(
                errno.EPERM, "File changed since it was read; retry", str(root / rel),
            )
        with changing_file(root / backup_rel):
            try:
                helper.create_private_bytes(backup_rel, original)
            except FileExistsError as exc:
                raise FileExistsError(
                    errno.EEXIST,
                    f"{backup_rel} is left from an interrupted update; compare it "
                    f"with {rel}, keep the right copy and delete the backup",
                    str(root / backup_rel),
                ) from exc
            except PermissionError as exc:
                # On Windows, also a backup name still pending deletion.
                raise PermissionError(
                    exc.errno or errno.EACCES,
                    f"Could not create {backup_rel}: {exc.strerror or exc}; {rel} is "
                    "unchanged, so retry",
                    str(root / backup_rel),
                ) from exc
            # Cleanup deletes only this entry, never one that replaced it.
            backup_id = _entry_identity(helper, backup_rel)
        # The descriptor closes after the journal sees the rewrite finish, so a
        # failed close is rolled back like any other failure instead of being
        # left pending, which the journal would preserve as a conflict.
        with ExitStack() as stack, changing_file(root / rel):
            try:
                fd = stack.enter_context(helper.open_rewrite(rel))
                _require_rewritable_fd(fd, root / rel, read)
                # Catches an in-place edit the size and timestamp miss, such
                # as a same-length one on a coarse-timestamp filesystem.
                if helper.read_bytes(rel) != original:
                    raise PermissionError(
                        errno.EPERM, "File changed while being updated", str(root / rel),
                    )
            except BaseException:
                # Nothing was written, so the backup is only clutter, and one
                # left behind would block the next run.
                _discard_backup(helper, root, backup_rel, backup_id)
                raise
            try:
                _write_fd(fd, content)
                _remove_backup(helper, root, backup_rel, backup_id)
            except BaseException:
                try:
                    _write_fd(fd, original)
                except OSError as exc:
                    kept = (
                        backup_id is not None
                        and _entry_identity(helper, backup_rel) == backup_id
                    )
                    if kept:
                        _keep_through_rollback(root / backup_rel)
                    where = (
                        f"its previous content is in {backup_rel}"
                        if kept
                        else "its previous content could not be kept"
                    )
                    logger.warning(
                        "Could not restore %s after a failed write: %s; %s", rel, exc, where,
                    )
                else:
                    _discard_backup(helper, root, backup_rel, backup_id)
                raise
            if on_written is not None:
                on_written(original)
    return original


_Written = tuple[str, bytes | None, bytes, bool, tuple[int, int, int] | None]


def _entry_identity(helper: FileHelper, rel: str) -> tuple[int, int, int] | None:
    """The device, inode and change time of ``rel`` itself, or ``None`` if unreadable.

    The change time tells a file recreated under a reused inode number from
    the one first seen.
    """
    try:
        info = helper.stat(rel)
    except (OSError, ValueError):  # ValueError covers FileHelperError
        return None
    return info.st_dev, info.st_ino, info.st_ctime_ns


def _publish_new(helper: FileHelper, rel: str, content: bytes) -> tuple[int, int, int] | None:
    """Create ``rel`` holding ``content``, never leaving a partial file there.

    The bytes are written in a private staging directory beside ``rel`` and
    moved into place without replacing anything, so a failed write leaves
    nothing at ``rel`` for a retry or the lifecycle journal to mistake for a
    user file. Every step goes through the helper, so a directory swapped
    for a symlink since planning cannot redirect it. Returns the identity of
    the published file, or ``None`` if the entry at ``rel`` is not provably
    the one moved there; rollback deletes only a file whose identity matches.
    """
    parent = PurePosixPath(rel).parent.as_posix()
    helper.mkdir(parent, parents=True, exist_ok=True)
    identity = None
    moved = False
    try:
        with helper.temporary_directory(parent, prefix=".speckit-") as staging:
            staged = staging / PurePosixPath(rel).name
            helper.create_bytes(staged, content)
            made = helper.stat(staged)
            helper.move_noreplace(staged, rel)
            moved = True
            identity = _entry_identity(helper, rel)
            if identity is not None and identity[:2] != (made.st_dev, made.st_ino):
                identity = None
    except OSError as exc:
        if not moved:
            raise
        # Only the empty staging directory is left; the policy is in place.
        logger.warning("Could not remove a staging directory in %s: %s", parent, exc)
    return identity


def _keep_through_rollback(backup: Path) -> None:
    """Stop a lifecycle rollback from deleting a backup that is now the only copy.

    The journal recorded the backup as created by this run, so a rollback
    would remove it. Reporting it as about to change again leaves it pending,
    which the rollback preserves and reports instead of deleting.
    """
    try:
        before_file_change(backup)
    except Exception as exc:  # the observer refuses paths it cannot restore
        logger.warning("Could not protect %s from rollback: %s", backup, exc)


def _write_fd(fd: int, content: bytes) -> None:
    # Truncating after writing, not before, means the old bytes' space is
    # reused rather than freed first.
    os.lseek(fd, 0, os.SEEK_SET)
    view = memoryview(content)
    while view:
        count = os.write(fd, view)
        if count == 0:
            raise OSError(errno.EIO, "Write made no progress")
        view = view[count:]
    os.ftruncate(fd, len(content))
    os.fsync(fd)
    if sys.platform == "darwin":
        # macOS ``fsync`` can leave the bytes in the drive cache, and the
        # caller deletes the backup next.
        import fcntl

        try:
            fcntl.fcntl(fd, fcntl.F_FULLFSYNC)
        except OSError as exc:
            # Not every filesystem supports it, and fsync has already run.
            if exc.errno not in (errno.ENOTSUP, errno.EOPNOTSUPP, errno.EINVAL, errno.ENOTTY):
                raise


def _discard_backup(
    helper: FileHelper, root: Path, backup_rel: str, identity: tuple[int, int, int] | None,
) -> None:
    """Remove a backup whose original is intact; a failure only leaves it behind."""
    try:
        _remove_backup(helper, root, backup_rel, identity)
    except (OSError, ValueError) as exc:  # ValueError covers FileHelperError
        logger.warning(
            "Could not remove %s: %s; %s is intact, so delete the backup before "
            "retrying", backup_rel, exc, backup_rel.removesuffix(_BACKUP_SUFFIX),
        )


def _remove_backup(
    helper: FileHelper, root: Path, backup_rel: str, identity: tuple[int, int, int] | None,
) -> None:
    """Delete the backup ``_replace_file`` created, identified by ``identity``.

    An entry that replaced it is someone else's and is left in place.
    """
    with changing_file(root / backup_rel, removal=True):
        try:
            info = helper.stat(backup_rel)
        except FileNotFoundError:
            return
        if identity is None or (info.st_dev, info.st_ino, info.st_ctime_ns) != identity:
            raise PermissionError(
                errno.EPERM,
                f"{backup_rel} was replaced during the update, so it was left in place",
                str(root / backup_rel),
            )
        helper.delete(backup_rel)


def _require_rewritable_fd(fd: int, path: Path, read: os.stat_result) -> None:
    # Checked on the open file, which is what is written, not its path.
    info = os.fstat(fd)
    if (info.st_dev, info.st_ino) != (read.st_dev, read.st_ino):
        raise PermissionError(errno.EPERM, "File was replaced while being updated", str(path))
    if (info.st_size, info.st_mtime_ns) != (read.st_size, read.st_mtime_ns):
        raise PermissionError(errno.EPERM, "File changed while being updated", str(path))
    if not stat.S_ISREG(info.st_mode):
        raise PermissionError(errno.EPERM, "Not a regular file", str(path))
    if not info.st_mode & 0o222:
        raise PermissionError(errno.EACCES, "File is read-only", str(path))
    if info.st_nlink > 1:
        raise PermissionError(errno.EPERM, "File has other hard links", str(path))


def _entry_kind(root: Path, rel: str) -> str:
    """What ``rel`` itself is: ``missing``, ``file``, ``dir``, ``symlink`` or ``other``.

    Checked through ``FileHelper``, so no link at or above ``rel`` is followed.
    ``other`` is any entry the helper refuses to use, such as a FIFO or a
    Windows junction. A missing ancestor, or one that is not a directory,
    reads as ``missing``, so callers that care check each parent's kind. Any
    other ancestor that cannot be used raises: a symlink ``SymlinkDeniedError``,
    a junction or special file ``UnsupportedPathError`` (both
    ``FileHelperError``), and a failed check its ``OSError``.
    """
    parent = PurePosixPath(rel).parent
    try:
        with FileHelper(root) as helper:
            if parent.parts:
                # Denied here, the link is above ``rel``; denied below, it is ``rel``.
                helper.stat(parent.as_posix())
            try:
                mode = helper.stat(rel).st_mode
            except SymlinkDeniedError:
                return "symlink"
            except UnsupportedPathError:
                return "other"
    except (FileNotFoundError, NotADirectoryError):
        return "missing"
    if stat.S_ISREG(mode):
        return "file"
    return "dir" if stat.S_ISDIR(mode) else "other"


def _canonical_root(project_root: Path) -> Path:
    with FileHelper(project_root) as helper:
        return helper.canonical_root


# Windows ``os.access`` reads only the read-only attribute, not the
# access-control list. A module flag so tests can take the Windows path.
_PROBE_WRITE_ACCESS = os.name == "nt"
_ERROR_SHARING_VIOLATION = 32


def _require_rewritable(root: Path, rel: str) -> None:
    path = root / rel
    with FileHelper(root) as helper:
        info = helper.stat(rel)
        if not stat.S_ISREG(info.st_mode):
            raise PermissionError(errno.EPERM, "Not a regular file", str(path))
        # The mode bits catch a read-only file even when running as root.
        if not helper.access(rel, os.W_OK) or not info.st_mode & 0o222:
            raise PermissionError(errno.EACCES, "File is read-only", str(path))
        if _PROBE_WRITE_ACCESS:
            # Opening for writing, without writing, is what the access-control
            # list is checked against.
            try:
                with helper.open_rewrite(rel):
                    pass
            except PermissionError as exc:
                # Another program holding the file open is not a denial; the
                # write itself reports it if it still holds it then.
                if getattr(exc, "winerror", None) != _ERROR_SHARING_VIOLATION:
                    raise PermissionError(
                        exc.errno or errno.EACCES, "File cannot be opened for writing", str(path),
                    ) from exc
    # An in-place write would also change every other link, possibly outside
    # the project.
    if info.st_nlink > 1:
        raise PermissionError(errno.EPERM, "File has other hard links", str(path))


def _require_creatable_beside(root: Path, rel: str) -> None:
    """Refuse unless an entry can be created beside ``rel``.

    The nearest existing ancestor is checked, since setup creates any missing
    directory below it. Windows ``os.access`` ignores a directory's
    access-control list, so there this catches only a read-only mount.
    """
    parent = PurePosixPath(rel).parent
    while parent.parts and _entry_kind(root, parent.as_posix()) == "missing":
        parent = parent.parent
    with FileHelper(root) as helper:
        target = parent.as_posix() if parent.parts else "."
        if not helper.access(target, os.W_OK | os.X_OK):
            raise PermissionError(
                errno.EACCES, "Directory is not writable", str(root / parent),
            )


def _reparse_point_on(root: Path, rel: str) -> str | None:
    """The first existing entry of ``rel`` that ``FileHelper`` will not use.

    That is a Windows junction or other non-symlink reparse point, or a
    special file such as a FIFO. ``FileHelper`` rejects the same entries, but
    only when a file is written through them.
    """
    current = PurePosixPath()
    with FileHelper(root) as helper:
        for part in PurePosixPath(rel).parts:
            current = current / part
            try:
                helper.stat(current.as_posix())
            except (FileNotFoundError, NotADirectoryError):
                return None
            except UnsupportedPathError:
                return current.as_posix()
            except SymlinkDeniedError:
                # Symlinks are reported by ``_validate_record_path``.
                return None
            except OSError as exc:
                raise ValueError(
                    f"Cannot use --no-model-invocation: could not check "
                    f"{current.as_posix()} for a junction: {exc}"
                ) from exc
    return None


class CodexIntegration(SkillsIntegration):
    """Integration for OpenAI Codex CLI."""

    key = "codex"
    config = {
        "name": "Codex CLI",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    dev_no_symlink = True
    multi_install_safe = True
    supported_dispatch_settings = frozenset({"reasoning_effort", "context_size"})

    CANONICAL_TO_NATIVE = {
        "session_start": "SessionStart",
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "stop": "Stop",
    }
    events_config_file = ".codex/config.toml"
    events_format = "toml"

    _GENERATED_POLICY: dict[str, Any] = {"policy": {"allow_implicit_invocation": False}}

    @staticmethod
    def _load_openai_yaml(raw: bytes, rel: str) -> dict[str, Any]:
        """Parse an existing ``openai.yaml``; raise rather than guess at unusable content."""
        try:
            loaded = yaml.load(raw.decode("utf-8"), Loader=_openai_yaml.Yaml12Loader)
        except (yaml.YAMLError, ValueError) as exc:  # ValueError covers decoding and bad numbers
            raise ValueError(f"Cannot update {rel}: {exc}") from exc
        if loaded is None:  # an empty file holds nothing to preserve
            return {}
        if not isinstance(loaded, dict):
            raise ValueError(
                f"Cannot update {rel}: expected a YAML mapping, got {type(loaded).__name__}"
            )
        policy = loaded.get("policy")
        if policy is not None and not isinstance(policy, dict):
            raise ValueError(
                f"Cannot update {rel}: 'policy' must be a mapping, got {type(policy).__name__}"
            )
        if policy is not None:
            # A YAML alias can make ``policy`` the same dict as another key;
            # a copy keeps policy edits from reaching that key.
            loaded["policy"] = dict(policy)
        return loaded

    def _is_policy_rel(self, rel: str) -> bool:
        parts = PurePosixPath(rel).parts
        skills = PurePosixPath(self.registrar_config["dir"]).parts
        return (
            len(parts) == len(skills) + 3
            and parts[: len(skills)] == skills
            and parts[-2:] == ("agents", "openai.yaml")
        )

    def _prior_manifest(self, project_root: Path) -> IntegrationManifest | None:
        """Return the on-disk manifest, which setup's callers save only afterwards."""
        try:
            return IntegrationManifest.load(self.key, project_root)
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            logger.warning(
                "Could not read prior manifest for '%s'; leaving earlier "
                "agents/openai.yaml policies in place: %s",
                self.key, exc,
            )
            return None

    def _is_generated(
        self, root: Path, rel: str, prior: IntegrationManifest | None, raw: bytes | None = None,
    ) -> bool:
        """Whether ``rel`` is a policy-only file an earlier install generated.

        Content equality also counts, so a CRLF checkout or an added comment
        does not turn Spec Kit's own file into a user file.
        """
        if prior is None or prior.ownership_modes.get(rel) != "whole":
            return False
        try:
            # A symlinked ancestor makes the file unsafe to rehash or delete.
            _validate_record_path(Path(rel), root)
            if _entry_kind(root, rel) != "file":
                return False
            if raw is None:
                raw = _read_policy(root, rel)
            if hashlib.sha256(raw).hexdigest() == prior.files[rel]:
                return True
            loaded = self._load_openai_yaml(raw, rel)
            # ``0 == False`` in Python, so check the value's type as well.
            return loaded == self._GENERATED_POLICY and (
                loaded["policy"]["allow_implicit_invocation"] is False
            )
        except (OSError, ValueError):
            return False

    def _plan_policy(
        self, project_root: Path, rel: str, prior: IntegrationManifest | None
    ) -> tuple[str, str | None, str, bytes | None] | None:
        """Return ``(rel, content, ownership, read)`` to record, or ``None`` to leave a user file alone.

        ``content`` is ``None`` when the existing file already holds the policy,
        so it is recorded without being rewritten. ``read`` is the existing
        file's bytes, from which ``content`` was built, or ``None`` if it is new.
        Nothing is written, so ``preflight_setup`` runs this too.
        """
        path = project_root / rel
        # Checks every ancestor for symlinks before anything is read or written.
        _validate_record_path(Path(rel), project_root)

        def kind(entry: str) -> str:
            try:
                return _entry_kind(project_root, entry)
            except (OSError, FileHelperError) as exc:
                raise ValueError(f"Cannot update {rel}: {exc}") from exc

        for parent in reversed(Path(rel).parents[:-1]):
            if kind(parent.as_posix()) not in ("missing", "dir"):
                raise ValueError(f"Cannot update {rel}: {parent.as_posix()} is not a directory")
        tracked = prior is not None and rel in prior.files
        raw: bytes | None = None
        existing = kind(rel)
        if existing == "missing":
            data: dict[str, Any] = {}
            ownership = "whole"
        elif existing != "file":
            raise ValueError(f"Cannot update {rel}: not a regular file")
        else:
            try:
                raw = _read_policy(project_root, rel)
            except (OSError, ValueError) as exc:  # ValueError covers FileHelperError
                raise ValueError(f"Cannot update {rel}: {exc}") from exc
            data = self._load_openai_yaml(raw, rel)
            ownership = "whole" if self._is_generated(project_root, rel, prior, raw) else "partial"
            if (data.get("policy") or {}).get("allow_implicit_invocation") is not False:
                try:
                    _require_rewritable(project_root, rel)
                except (OSError, FileHelperError) as exc:
                    raise ValueError(f"Cannot update {rel}: {exc}") from exc
        policy = data.get("policy") or {}
        already_set = policy.get("allow_implicit_invocation") is False
        policy["allow_implicit_invocation"] = False
        data["policy"] = policy
        # Checked even for a file left alone, since Codex would ignore its policy.
        errors = _openai_yaml.schema_errors(data)
        if errors:
            raise ValueError(
                f"Cannot update {rel}: Codex would ignore this file, including the "
                f"policy: {'; '.join(errors)}"
            )
        backup = project_root / f"{rel}{_BACKUP_SUFFIX}"
        if kind(f"{rel}{_BACKUP_SUFFIX}") != "missing":
            # ``rel`` may be a half-written rewrite, one finished but not yet
            # recorded, or was deleted to start over; either way the backup
            # may be the only intact copy, and ``rel`` cannot be taken for the
            # user's own.
            raise ValueError(
                f"Cannot update {rel}: {backup.name} is left from an interrupted "
                f"update; compare it with {path.name}, keep the right copy and "
                "delete the backup"
            )
        if ownership == "partial" and not tracked and already_set:
            # The user already set it; claiming it would let cleanup remove their setting.
            return None
        if already_set and raw is not None:
            return rel, None, ownership, raw
        try:
            # A new policy is created here, and a rewrite keeps its backup here.
            _require_creatable_beside(project_root, rel)
        except (OSError, FileHelperError) as exc:
            raise ValueError(f"Cannot update {rel}: {exc}") from exc
        return rel, _openai_yaml.dump(data), ownership, raw

    def _remove_policy(self, project_root: Path, rel: str, *, final: bool = False) -> bool:
        """Drop the managed policy from a user-owned file; return whether it is now policy-free."""
        try:
            _validate_record_path(Path(rel), project_root)
            if _entry_kind(project_root, rel) != "file":
                return False
            raw = _read_policy(project_root, rel)
            data = self._load_openai_yaml(raw, rel)
            policy = data.get("policy")
            if isinstance(policy, dict) and policy.get("allow_implicit_invocation") is False:
                del policy["allow_implicit_invocation"]
                if not policy:
                    del data["policy"]
                _replace_file(
                    project_root, rel, _openai_yaml.dump(data).encode("utf-8"), expected=raw,
                )
        except (OSError, ValueError) as exc:
            # ``final``: nothing will retry, as uninstall drops the manifest.
            hint = (
                "; it may still set policy.allow_implicit_invocation: false, "
                "so remove it by hand to allow implicit invocation"
                if final else ""
            )
            logger.warning("Leaving %s unchanged: %s%s", rel, exc, hint)
            return False
        return True

    def _release_prior_policies(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        prior: IntegrationManifest,
        keep: set[str],
    ) -> set[str]:
        """Undo policies an earlier install wrote that this setup no longer writes.

        Unmodified generated files are deleted; in user files only the policy is
        removed, after which the file is no longer tracked. A file is tracked
        only while it holds the managed policy, so a policy the user sets later
        is never claimed. Files whose cleanup fails stay tracked under their
        prior hash so a later run retries. Every prior policy path is handed to
        upgrade's stale-file pass as an exclusion, so it never deletes a file
        this method released.
        """
        generated = IntegrationManifest(self.key, project_root, version="policy-cleanup")
        released: set[str] = set()
        for rel, recorded_hash in prior.files.items():
            if rel in keep or not self._is_policy_rel(rel):
                continue
            released.add(rel)
            if self._has_backup(project_root, rel):
                # Deleting the file would leave only the backup, which the
                # recovery steps compare it with; retry once that is resolved.
                mode = self._retained_mode(project_root, rel, prior)
                self._retain(manifest, rel, recorded_hash, mode)
                continue
            verified = self._generated_bytes(project_root, rel, prior)
            if verified is not None:
                # The hash of the bytes just checked, so the delete below
                # skips a file edited since.
                self._retain(generated, rel, hashlib.sha256(verified).hexdigest(), "whole")
                continue
            if self._remove_policy(project_root, rel):
                continue
            if self._may_still_exist(project_root, rel):
                # Unreadable, unparseable or unsafe: retry on a later run.
                mode = self._retained_mode(project_root, rel, prior)
                self._retain(manifest, rel, recorded_hash, mode)
        _, skipped = generated.uninstall(project_root, remove_manifest=False)
        for path in skipped:
            rel = path.relative_to(project_root).as_posix()
            if self._may_still_exist(project_root, rel):
                logger.warning(
                    "Could not remove %s, so it may still set "
                    "policy.allow_implicit_invocation: false and Codex will not "
                    "invoke that skill implicitly; run `specify integration upgrade "
                    "codex` again to retry, or delete the file by hand",
                    rel,
                )
                mode = self._retained_mode(project_root, rel, prior)
                self._retain(manifest, rel, prior.files[rel], mode)
        return released

    def _generated_bytes(
        self, root: Path, rel: str, prior: IntegrationManifest,
    ) -> bytes | None:
        """The bytes of ``rel`` if they are a generated policy-only file, else ``None``."""
        try:
            _validate_record_path(Path(rel), root)
            raw = _read_policy(root, rel)
        except (OSError, ValueError):
            return None
        return raw if self._is_generated(root, rel, prior, raw) else None

    @staticmethod
    def _has_backup(root: Path, rel: str) -> bool:
        """Whether an interrupted update left a backup beside ``rel``; warn if so."""
        backup_rel = f"{rel}{_BACKUP_SUFFIX}"
        try:
            if _entry_kind(root, backup_rel) == "missing":
                return False
        except (OSError, ValueError) as exc:  # ValueError covers FileHelperError
            # Unreadable or behind a symlinked ancestor: it may still be the
            # only intact copy, so keep both.
            logger.warning(
                "Leaving %s in place: could not check for %s: %s",
                rel, PurePosixPath(backup_rel).name, exc,
            )
            return True
        logger.warning(
            "Leaving %s in place: %s is left from an interrupted update; compare "
            "them, keep the right copy and delete the backup",
            rel, PurePosixPath(backup_rel).name,
        )
        return True

    @staticmethod
    def _may_still_exist(root: Path, rel: str) -> bool:
        """Whether ``rel`` may still hold a policy, so its entry must be kept.

        An unsafe ancestor (such as a dangling ``agents`` symlink) hides the
        file rather than proving it gone, so it counts as present.
        """
        try:
            _validate_record_path(Path(rel), root)
            return _entry_kind(root, rel) in ("file", "symlink")
        except (OSError, ValueError):
            return True

    def _retained_mode(self, root: Path, rel: str, prior: IntegrationManifest) -> str:
        """Ownership for a file kept tracked because its cleanup did not finish.

        A readable ``whole`` file that is no longer policy-only holds a user
        edit, unparseable ones included, so it becomes ``partial``: upgrade
        re-hashes tracked files afterwards, and a ``whole`` entry would then
        count as generated and be deleted, edit included. Policy-only content
        stays ``whole``, so it is still deleted once cleanup can finish. When
        the file cannot be read, the prior mode is kept so a generated file is
        still recognised, and deleted, once it can be read again.
        """
        mode = prior.ownership_modes[rel]
        if mode != "whole":
            return mode
        try:
            _validate_record_path(Path(rel), root)
            raw = _read_policy(root, rel)
        except (OSError, ValueError):
            return mode
        return mode if self._is_generated(root, rel, prior, raw) else "partial"

    @staticmethod
    def _retain(manifest: IntegrationManifest, rel: str, recorded_hash: str, ownership: str) -> None:
        """Keep tracking ``rel`` without reading it, which may be what failed.

        ``record_existing`` re-reads and re-hashes the file, and ``record_file``
        rewrites it, so neither can carry the prior hash forward. This is the
        only write to manifest internals; ``TestCodexManifestInternals`` pins it.
        """
        rel = Path(rel).as_posix()
        manifest._files[rel] = recorded_hash
        manifest.set_ownership(rel, ownership)

    # Policy paths the latest ``setup`` released; upgrade calls
    # ``stale_cleanup_exclusions`` on the same instance right after it.
    _released_policy_rels: frozenset[str] = frozenset()

    def stale_cleanup_exclusions(self) -> set[str]:
        # ``setup`` releases policy files itself and drops a file from the
        # manifest once its policy is removed; upgrade must not then delete it.
        from specify_cli.extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

        exclusions = super().stale_cleanup_exclusions()
        exclusions.update(self._policy_rel(name) for name in CORE_COMMAND_NAMES)
        exclusions.update(self._released_policy_rels)
        return exclusions

    def _policy_rel(self, command_name: str) -> str:
        skills = PurePosixPath(self.registrar_config["dir"])
        return (skills / f"speckit-{command_name}" / "agents" / "openai.yaml").as_posix()

    @staticmethod
    def _is_core_command_skill_dir(name: str) -> bool:
        from specify_cli.extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

        return name.startswith("speckit-") and (
            name.removeprefix("speckit-") in CORE_COMMAND_NAMES
        )

    def _plan_policies(
        self, root: Path, prior: IntegrationManifest | None,
    ) -> dict[str, tuple[str, str | None, str, bytes | None] | None]:
        """Plan every core command's policy, rejecting unusable layouts and files."""
        from specify_cli.extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

        plans: dict[str, tuple[str, str | None, str, bytes | None] | None] = {}
        for name in sorted(CORE_COMMAND_NAMES):
            rel = self._policy_rel(name)
            try:
                # Policies are recorded and cleaned up by their lexical path,
                # which a symlinked skills or skill directory would not match.
                _validate_record_path(Path(rel), root)
            except ValueError as exc:
                raise ValueError(f"Cannot use --no-model-invocation: {exc}") from exc
            # ``is_symlink`` misses a Windows junction, which resolving the
            # skills directory would follow just the same.
            reparse = _reparse_point_on(root, rel)
            if reparse is not None:
                raise ValueError(
                    f"Cannot use --no-model-invocation: {rel} goes through a special "
                    f"file, Windows junction or other reparse point at {reparse}"
                )
            plans[name] = self._plan_policy(root, rel, prior)
        return plans

    def preflight_setup(
        self,
        project_root: Path,
        parsed_options: dict[str, Any] | None = None,
        *,
        script_type: str | None = None,
    ) -> None:
        # Install, switch and upgrade call this before changing anything, so a
        # file setup would refuse stops a switch before the outgoing
        # integration is removed. Setup repeats the checks, since files can
        # change in between.
        super().preflight_setup(project_root, parsed_options, script_type=script_type)
        if (parsed_options or {}).get("no_model_invocation") is True:
            root = _canonical_root(project_root)
            self._plan_policies(root, self._prior_manifest(root))

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        # Codex has no SKILL.md frontmatter flag; the policy lives in a sibling
        # ``agents/openai.yaml``. It is written for core command skills only,
        # since mandatory extension hooks rely on the model invoking them.
        root = _canonical_root(project_root)
        enabled = (parsed_options or {}).get("no_model_invocation") is True
        prior = self._prior_manifest(root)
        self._released_policy_rels = frozenset()
        skills_rel = self.registrar_config["dir"]
        if enabled:
            # Reject unusable layouts and existing policy files before anything
            # is written. ``super().setup`` writes only SKILL.md, so these plans
            # stay valid.
            plans = self._plan_policies(root, prior)
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        planned: list[tuple[str, str | None, str, bytes | None]] = []
        if enabled:
            for skill_file in [f for f in created if f.name == "SKILL.md"]:
                name = skill_file.parent.name
                if skill_file.parent.parent != root / skills_rel:
                    continue
                if self._is_core_command_skill_dir(name):
                    plan = plans[name.removeprefix("speckit-")]
                    if plan is not None:
                        planned.append(plan)
        # ``(rel, prior bytes or None if new, bytes written, whether its
        # directory was new, the identity of a file it created, or None when
        # it is not provably the one setup created)``
        written: list[_Written] = []
        try:
            for rel, content, ownership, read in planned:
                path = root / rel
                if read is not None:
                    # ``record_file`` truncates in place; keep the user's file
                    # intact if the write fails.
                    _validate_record_path(Path(rel), root)
                    expected = read
                    if content is not None:
                        expected = new = content.encode("utf-8")
                        _replace_file(
                            root, rel, new, expected=read,
                            on_written=lambda original, rel=rel, new=new: written.append(
                                (rel, original, new, False, None)
                            ),
                        )
                    manifest.record_existing(rel, ownership=ownership)
                    if manifest.files[rel] != hashlib.sha256(expected).hexdigest():
                        raise ValueError(f"Cannot update {rel}: it changed while updating")
                    created.append(path)
                else:
                    new = content.encode("utf-8")
                    try:
                        present = _entry_kind(root, rel) != "missing"
                        new_dir = _entry_kind(root, PurePosixPath(rel).parent.as_posix()) == "missing"
                    except (OSError, FileHelperError) as exc:
                        raise ValueError(f"Cannot update {rel}: {exc}") from exc
                    if present:
                        raise ValueError(f"Cannot update {rel}: it was created while updating")
                    identity = None
                    try:
                        with changing_file(path), FileHelper(root) as helper:
                            identity = _publish_new(helper, rel, new)
                    except FileExistsError as exc:
                        # Someone else's file: not ours to roll back.
                        raise ValueError(f"Cannot update {rel}: it was created while updating") from exc
                    except BaseException:
                        written.append((rel, None, new, new_dir, identity))
                        raise
                    written.append((rel, None, new, new_dir, identity))
                    manifest.record_existing(rel, ownership=ownership)
                    if manifest.files[rel] != hashlib.sha256(new).hexdigest():
                        raise ValueError(f"Cannot update {rel}: it changed while updating")
                    created.append(path)
            if prior is not None:
                self._released_policy_rels = frozenset(
                    self._release_prior_policies(root, manifest, prior, {plan[0] for plan in planned})
                )
        except BaseException:
            # A retry would see these policies untracked and take them for the
            # user's own, so they could never be removed. A lifecycle
            # transaction restores its journal itself.
            from .._lifecycle import lifecycle_owns_rollback  # lazy: avoids circular import

            if not lifecycle_owns_rollback():
                self._roll_back_policies(root, written)
            raise
        return created

    @staticmethod
    def _roll_back_policies(root: Path, written: list[_Written]) -> None:
        """Undo the policy writes of a setup that failed part-way.

        A file that no longer holds what setup wrote is left alone, as is a
        created file that is no longer the entry setup created. Only runs
        outside a lifecycle transaction, so nothing journals it.
        """
        for rel, original, new, new_dir, identity in reversed(written):
            try:
                if original is not None:
                    try:
                        _replace_file(root, rel, original, expected=new)
                    except (OSError, ValueError) as exc:
                        logger.warning(
                            "Could not undo the policy written to %s: %s; restore "
                            "its earlier policy.allow_implicit_invocation setting by hand",
                            rel, exc,
                        )
                    continue
                parent = PurePosixPath(rel).parent.as_posix()
                with FileHelper(root) as helper:
                    # Deleting through the helper never follows a symlinked
                    # ancestor out of the project.
                    try:
                        current = helper.read_bytes(rel)
                    except FileNotFoundError:  # never published
                        current = None
                    if current is not None:
                        if identity is None or _entry_identity(helper, rel) != identity:
                            logger.warning(
                                "Leaving %s in place: it is not the file setup created", rel,
                            )
                            continue
                        if current != new:
                            logger.warning("Leaving %s in place: it changed after it was written", rel)
                            continue
                        helper.delete(rel)
                    if new_dir:
                        try:
                            helper.delete(parent)
                        except OSError:
                            pass  # gone already, or holds something else
            except (OSError, ValueError) as exc:  # ValueError covers FileHelperError
                logger.warning("Could not undo the policy written to %s: %s", rel, exc)

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        # ``manifest.uninstall`` never touches partial files, so remove the
        # managed policy from user-owned ``openai.yaml`` files here, and do not
        # report the ones cleaned as preserved modified files. Generated files
        # are left to ``uninstall``: content-equal ones are re-hashed so it
        # deletes them, and edited ones lose only the policy unless forced.
        root = _canonical_root(project_root)
        cleaned: set[Path] = set()
        for rel, mode in list(manifest.ownership_modes.items()):
            if not self._is_policy_rel(rel):
                continue
            if self._has_backup(root, rel):
                # ``uninstall`` never deletes a partial file, so both copies
                # stay for the recovery steps.
                manifest.set_ownership(rel, "partial")
                continue
            if mode != "whole":
                if self._remove_policy(root, rel, final=True):
                    cleaned.add(root / rel)
                continue
            verified = self._generated_bytes(root, rel, manifest)
            if verified is not None:
                # The hash of the bytes just checked, so ``uninstall`` keeps a
                # file edited since.
                self._retain(manifest, rel, hashlib.sha256(verified).hexdigest(), "whole")
            elif not force:
                self._remove_policy(root, rel, final=True)
        removed, skipped = super().teardown(project_root, manifest, force=force)
        return removed, [path for path in skipped if path not in cleaned]

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
        reasoning_effort: str | None = None,
        context_size: str | None = None,
    ) -> list[str] | None:
        # Codex uses ``codex exec "prompt"`` for non-interactive mode.
        # Resolve argv[0] via the shared executable resolver so operators can
        # override the binary with SPECKIT_INTEGRATION_CODEX_EXECUTABLE.
        self.validate_runtime_config(integration_args, integration_options)
        settings = requested_dispatch_settings(
            reasoning_effort=reasoning_effort, context_size=context_size
        )
        if settings:
            check_dispatch_settings(self, settings, via="build_exec_args")
        args: list[str] = [self._resolve_executable(), "exec", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        # ``-c`` values are parsed as TOML. The checked value cannot contain
        # quotes, backslashes, or control characters, so it forms a valid
        # basic string as-is.
        if reasoning_effort is not None:
            args.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])
        if context_size is not None:
            args.extend(["-c", f"model_context_window={context_size}"])
        if output_json:
            args.append("--json")
        return args

    def validate_dispatch_setting(self, name: str, value: str) -> None:
        """Require ``context_size`` to be a token count Codex can parse.

        The value can be captured agent output, so the error does not repeat it.
        """
        if name == "context_size" and (
            _CONTEXT_WINDOW.fullmatch(value) is None
            or int(value) > _MAX_CONTEXT_WINDOW
        ):
            raise ValueError(
                "Codex 'context_size' must be a positive integer token count "
                "(model_context_window) without leading zeros, at most "
                f"{_MAX_CONTEXT_WINDOW}."
            )

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Codex)",
            )
        )
        opts.append(
            IntegrationOption(
                "--no-model-invocation",
                is_flag=True,
                default=False,
                help=(
                    "Install core command skills as user-invocable only "
                    "(agents/openai.yaml: allow_implicit_invocation: false)"
                ),
            )
        )
        return opts
