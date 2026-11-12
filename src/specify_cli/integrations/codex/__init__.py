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
from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from ...file_helper import FileHelper
from .._file_changes import changing_file
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
from ._private_file import create_private

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
        # FileHelper has no public in-place byte rewrite; this is the anchored,
        # non-truncating open behind ``overwrite_text``, which would translate
        # newlines on Windows. Pinned by ``TestCodexFileHelperInternals``.
        destination = helper._path(rel)
        read = os.stat(destination, follow_symlinks=False)
        original = helper.read_bytes(rel)
        if expected is not None and original != expected:
            raise PermissionError(
                errno.EPERM, "File changed since it was read; retry", str(root / rel),
            )
        with changing_file(root / backup_rel):
            try:
                create_private(helper, backup_rel, original)
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
        with changing_file(root / rel), ExitStack() as stack:
            try:
                fd = stack.enter_context(helper._overwrite_descriptor(destination))
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
                _discard_backup(helper, root, backup_rel)
                raise
            try:
                _write_fd(fd, content)
                _remove_backup(helper, root, backup_rel)
            except BaseException:
                try:
                    _write_fd(fd, original)
                except OSError as exc:
                    where = (
                        f"its previous content is in {backup_rel}"
                        if (root / backup_rel).is_file()
                        else "its previous content could not be kept"
                    )
                    logger.warning(
                        "Could not restore %s after a failed write: %s; %s", rel, exc, where,
                    )
                else:
                    _discard_backup(helper, root, backup_rel)
                raise
            if on_written is not None:
                on_written(original)
    return original


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


def _discard_backup(helper: FileHelper, root: Path, backup_rel: str) -> None:
    """Remove a backup whose original is intact; a failure only leaves it behind."""
    try:
        _remove_backup(helper, root, backup_rel)
    except (OSError, ValueError) as exc:  # ValueError covers FileHelperError
        logger.warning(
            "Could not remove %s: %s; %s is intact, so delete the backup before "
            "retrying", backup_rel, exc, backup_rel.removesuffix(_BACKUP_SUFFIX),
        )


def _remove_backup(helper: FileHelper, root: Path, backup_rel: str) -> None:
    with changing_file(root / backup_rel, removal=True):
        try:
            helper.delete(backup_rel)
        except FileNotFoundError:
            pass


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


def _require_rewritable(path: Path) -> None:
    # The mode bits catch a read-only file even when running as root.
    if not os.access(path, os.W_OK) or not path.stat().st_mode & 0o222:
        raise PermissionError(errno.EACCES, "File is read-only", str(path))
    # An in-place write would also change every other link, possibly outside
    # the project.
    if path.stat().st_nlink > 1:
        raise PermissionError(errno.EPERM, "File has other hard links", str(path))


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
        path = root / rel
        if prior is None or prior.ownership_modes.get(rel) != "whole":
            return False
        try:
            # A symlinked ancestor makes the file unsafe to rehash or delete.
            _validate_record_path(Path(rel), root)
            if path.is_symlink() or not path.is_file():
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
        for parent in reversed(Path(rel).parents[:-1]):
            if (project_root / parent).exists() and not (project_root / parent).is_dir():
                raise ValueError(f"Cannot update {rel}: {parent.as_posix()} is not a directory")
        tracked = prior is not None and rel in prior.files
        raw: bytes | None = None
        if not path.exists():
            data: dict[str, Any] = {}
            ownership = "whole"
        elif not path.is_file():
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
                    _require_rewritable(path)
                except OSError as exc:
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
        if backup.exists() or backup.is_symlink():
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
        if already_set and path.exists():
            return rel, None, ownership, raw
        return rel, _openai_yaml.dump(data), ownership, raw

    def _remove_policy(self, project_root: Path, rel: str, *, final: bool = False) -> bool:
        """Drop the managed policy from a user-owned file; return whether it is now policy-free."""
        path = project_root / rel
        try:
            _validate_record_path(Path(rel), project_root)
            if not path.is_file():
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
        modes = prior.ownership_modes
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
        backup = root / f"{rel}{_BACKUP_SUFFIX}"
        if not (backup.exists() or backup.is_symlink()):
            return False
        logger.warning(
            "Leaving %s in place: %s is left from an interrupted update; compare "
            "them, keep the right copy and delete the backup",
            rel, backup.name,
        )
        return True

    @staticmethod
    def _may_still_exist(root: Path, rel: str) -> bool:
        """Whether ``rel`` may still hold a policy, so its entry must be kept.

        An unsafe ancestor (such as a dangling ``agents`` symlink) hides the
        file rather than proving it gone, so it counts as present.
        """
        path = root / rel
        try:
            _validate_record_path(Path(rel), root)
            return path.is_file() or path.is_symlink()
        except (OSError, ValueError):
            return True

    def _retained_mode(self, root: Path, rel: str, prior: IntegrationManifest) -> str:
        """Ownership for a file kept tracked because its cleanup did not finish.

        A readable ``whole`` file that is no longer policy-only holds a user
        edit, so it becomes ``partial``: upgrade re-hashes tracked files
        afterwards, and a ``whole`` entry would then count as generated and be
        deleted, edit included. Policy-only content stays ``whole``, so it is
        still deleted once cleanup can finish. When the file cannot be read,
        the prior mode is kept so a generated file is still recognised, and
        deleted, once it can be read again.
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
            root = project_root.resolve()
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
        root = project_root.resolve()
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
        # directory was new, whether the write completed)``
        written: list[tuple[str, bytes | None, bytes, bool, bool]] = []
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
                                (rel, original, new, False, True)
                            ),
                        )
                    manifest.record_existing(rel, ownership=ownership)
                    if manifest.files[rel] != hashlib.sha256(expected).hexdigest():
                        raise ValueError(f"Cannot update {rel}: it changed while updating")
                    created.append(path)
                else:
                    new = content.encode("utf-8")
                    if path.exists() or path.is_symlink():
                        raise ValueError(f"Cannot update {rel}: it was created while updating")
                    new_dir = not (path.parent.exists() or path.parent.is_symlink())
                    # Created exclusively through the helper, so a directory
                    # swapped for a symlink since planning cannot redirect it.
                    try:
                        with changing_file(path), FileHelper(root) as helper:
                            helper.mkdir(PurePosixPath(rel).parent.as_posix(), parents=True, exist_ok=True)
                            helper.create_bytes(rel, new)
                    except FileExistsError as exc:
                        # Someone else's file: not ours to roll back.
                        raise ValueError(f"Cannot update {rel}: it was created while updating") from exc
                    except BaseException:
                        written.append((rel, None, new, new_dir, False))
                        raise
                    written.append((rel, None, new, new_dir, True))
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
    def _roll_back_policies(root: Path, written: list[tuple[str, bytes | None, bytes, bool, bool]]) -> None:
        """Undo the policy writes of a setup that failed part-way.

        A file that no longer holds what setup wrote is left alone. Only runs
        outside a lifecycle transaction, so nothing journals it.
        """
        for rel, original, new, new_dir, complete in reversed(written):
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
                    except FileNotFoundError:  # the write itself failed
                        current = None
                    if current is not None:
                        # A write that failed part-way leaves a prefix.
                        if current != new and (complete or not new.startswith(current)):
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
        root = project_root.resolve()
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
            elif self._is_generated(root, rel, manifest):
                manifest.record_existing(rel)
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
