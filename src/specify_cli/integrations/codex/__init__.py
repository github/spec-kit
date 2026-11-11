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
from collections.abc import Mapping, Sequence
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

logger = logging.getLogger(__name__)

# ``model_context_window`` is a TOML integer that Codex reads as an i64.
_CONTEXT_WINDOW = re.compile(r"[1-9][0-9]*")
_MAX_CONTEXT_WINDOW = 2**63 - 1


_BACKUP_SUFFIX = ".speckit-backup"


def _replace_file(root: Path, rel: str, content: bytes) -> bytes:
    """Rewrite an existing file in place and return its previous bytes.

    Writing through the same file keeps its owner, group, access-control list
    and other attributes, which a sibling-and-rename swap would replace with
    the directory's defaults. Every step goes through ``FileHelper``, which
    opens each ancestor without following links, so a directory swapped for a
    symlink part-way cannot redirect the write outside the project.

    Until the new bytes are on disk and the backup is gone, a copy of the
    previous ones is kept beside the file as ``<name>.speckit-backup``. The
    backup is created exclusively: one left by an interrupted run stops the
    rewrite instead of being overwritten. Any failure, including removing the
    backup, restores the previous bytes before it propagates. Read-only and
    hard-linked files are refused.
    """
    backup_rel = f"{rel}{_BACKUP_SUFFIX}"
    with FileHelper(root) as helper:
        _require_rewritable(root / rel)
        original = helper.read_bytes(rel)
        with changing_file(root / backup_rel):
            try:
                helper.create_bytes(backup_rel, original, mode=0o600)
            except FileExistsError as exc:
                raise FileExistsError(
                    errno.EEXIST,
                    f"{backup_rel} is left from an interrupted update; compare it "
                    f"with {rel}, keep the right copy and delete the backup",
                    str(root / backup_rel),
                ) from exc
        # FileHelper has no public in-place byte rewrite; this is the anchored,
        # non-truncating open behind ``overwrite_text``, which would translate
        # newlines on Windows. Pinned by ``TestCodexFileHelperInternals``.
        destination = helper._path(rel)
        with changing_file(root / rel), ExitStack() as stack:
            try:
                fd = stack.enter_context(helper._overwrite_descriptor(destination))
                _require_rewritable_fd(fd, root / rel)
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
                    logger.warning(
                        "Could not restore %s after a failed write: %s; its previous "
                        "content is in %s", rel, exc, backup_rel,
                    )
                    raise
                _discard_backup(helper, root, backup_rel)
                raise
    return original


def _write_fd(fd: int, content: bytes) -> None:
    # Truncating after writing, not before, means the old bytes' space is
    # reused rather than freed first.
    os.lseek(fd, 0, os.SEEK_SET)
    view = memoryview(content)
    while view:
        view = view[os.write(fd, view):]
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
    if not (root / backup_rel).exists():
        return
    with changing_file(root / backup_rel, removal=True):
        helper.delete(backup_rel)


def _require_rewritable_fd(fd: int, path: Path) -> None:
    # Re-checked on the open file, which is what is written, not its path.
    info = os.fstat(fd)
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
    def _load_openai_yaml(path: Path, rel: str) -> dict[str, Any]:
        """Parse an existing ``openai.yaml``; raise rather than guess at unusable content."""
        try:
            loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=_openai_yaml.Yaml12Loader)
        except (yaml.YAMLError, OSError, ValueError) as exc:  # ValueError covers decoding and bad numbers
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

    def _is_generated(self, root: Path, rel: str, prior: IntegrationManifest | None) -> bool:
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
            if hashlib.sha256(path.read_bytes()).hexdigest() == prior.files[rel]:
                return True
            loaded = self._load_openai_yaml(path, rel)
            # ``0 == False`` in Python, so check the value's type as well.
            return loaded == self._GENERATED_POLICY and (
                loaded["policy"]["allow_implicit_invocation"] is False
            )
        except (OSError, ValueError):
            return False

    def _plan_policy(
        self, project_root: Path, rel: str, prior: IntegrationManifest | None
    ) -> tuple[str, str | None, str] | None:
        """Return ``(rel, content, ownership)`` to record, or ``None`` to leave a user file alone.

        ``content`` is ``None`` when the existing file already holds the policy,
        so it is recorded without being rewritten.
        """
        path = project_root / rel
        # Checks every ancestor for symlinks before anything is read or written.
        _validate_record_path(Path(rel), project_root)
        for parent in reversed(Path(rel).parents[:-1]):
            if (project_root / parent).exists() and not (project_root / parent).is_dir():
                raise ValueError(f"Cannot update {rel}: {parent.as_posix()} is not a directory")
        tracked = prior is not None and rel in prior.files
        if not path.exists():
            data: dict[str, Any] = {}
            ownership = "whole"
        elif not path.is_file():
            raise ValueError(f"Cannot update {rel}: not a regular file")
        else:
            backup = project_root / f"{rel}{_BACKUP_SUFFIX}"
            if backup.exists() or backup.is_symlink():
                # ``rel`` may be a half-written rewrite; the backup is the
                # only intact copy, so nothing may replace or remove it.
                raise ValueError(
                    f"Cannot update {rel}: {backup.name} is left from an interrupted "
                    f"update; compare it with {path.name}, keep the right copy and "
                    "delete the backup"
                )
            data = self._load_openai_yaml(path, rel)
            ownership = "whole" if self._is_generated(project_root, rel, prior) else "partial"
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
        if ownership == "partial" and not tracked and already_set:
            # The user already set it; claiming it would let cleanup remove their setting.
            return None
        if already_set and path.exists():
            return rel, None, ownership
        return rel, _openai_yaml.dump(data), ownership

    def _remove_policy(self, project_root: Path, rel: str, *, final: bool = False) -> bool:
        """Drop the managed policy from a user-owned file; return whether it is now policy-free."""
        path = project_root / rel
        try:
            _validate_record_path(Path(rel), project_root)
            if not path.is_file():
                return False
            data = self._load_openai_yaml(path, rel)
            policy = data.get("policy")
            if isinstance(policy, dict) and policy.get("allow_implicit_invocation") is False:
                del policy["allow_implicit_invocation"]
                if not policy:
                    del data["policy"]
                _replace_file(project_root, rel, _openai_yaml.dump(data).encode("utf-8"))
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
            if self._is_generated(project_root, rel, prior):
                self._retain(generated, rel, recorded_hash, "whole")
                continue
            if self._remove_policy(project_root, rel):
                continue
            if self._may_still_exist(project_root, rel):
                # Unreadable, unparseable or unsafe: retry on a later run.
                mode = self._failed_cleanup_mode(project_root, rel, recorded_hash, modes[rel])
                self._retain(manifest, rel, recorded_hash, mode)
        # Each entry was checked above, content-equal ones included.
        _, skipped = generated.uninstall(project_root, force=True, remove_manifest=False)
        for path in skipped:
            rel = path.relative_to(project_root).as_posix()
            if self._may_still_exist(project_root, rel):
                self._retain(manifest, rel, prior.files[rel], "whole")
        return released

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

    @staticmethod
    def _failed_cleanup_mode(root: Path, rel: str, recorded_hash: str, mode: str) -> str:
        """Ownership for a file whose policy could not be removed.

        A ``whole`` file whose readable bytes differ from the recorded hash is
        a user edit, so it becomes ``partial``: upgrade re-hashes tracked files afterwards, and
        a ``whole`` entry would then count as generated and be deleted. When
        the file cannot be read, the prior mode is kept so a generated file is
        still recognised, and deleted, once it can be read again.
        """
        if mode != "whole":
            return mode
        try:
            _validate_record_path(Path(rel), root)
            if hashlib.sha256((root / rel).read_bytes()).hexdigest() != recorded_hash:
                return "partial"
        except (OSError, ValueError):
            pass
        return mode

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
        if enabled:
            # Reject unusable layouts and existing policy files before anything
            # is written.
            from specify_cli.extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

            skills_rel = self.registrar_config["dir"]
            plans: dict[str, tuple[str, str | None, str] | None] = {}
            for name in sorted(CORE_COMMAND_NAMES):
                rel = self._policy_rel(name)
                try:
                    # Policies are recorded and cleaned up by their lexical
                    # path, which a symlinked skills or skill directory would
                    # not match.
                    _validate_record_path(Path(rel), root)
                except ValueError as exc:
                    raise ValueError(f"Cannot use --no-model-invocation: {exc}") from exc
                # ``super().setup`` writes only SKILL.md, so these plans stay valid.
                plans[name] = self._plan_policy(root, rel, prior)
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        planned: list[tuple[str, str | None, str]] = []
        if enabled:
            for skill_file in [f for f in created if f.name == "SKILL.md"]:
                name = skill_file.parent.name
                if skill_file.parent.parent != root / skills_rel:
                    continue
                if self._is_core_command_skill_dir(name):
                    plan = plans[name.removeprefix("speckit-")]
                    if plan is not None:
                        planned.append(plan)
        # ``(rel, prior bytes or None if new, whether its directory was new)``
        written: list[tuple[str, bytes | None, bool]] = []
        try:
            for rel, content, ownership in planned:
                path = root / rel
                if path.exists():
                    # ``record_file`` truncates in place; keep the user's file
                    # intact if the write fails.
                    _validate_record_path(Path(rel), root)
                    if content is not None:
                        original = _replace_file(root, rel, content.encode("utf-8"))
                        written.append((rel, original, False))
                    manifest.record_existing(rel, ownership=ownership)
                    created.append(path)
                else:
                    written.append((rel, None, not path.parent.exists()))
                    created.append(manifest.record_file(rel, content, ownership=ownership))
            if prior is not None:
                self._released_policy_rels = frozenset(
                    self._release_prior_policies(root, manifest, prior, {rel for rel, _, _ in planned})
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
    def _roll_back_policies(root: Path, written: list[tuple[str, bytes | None, bool]]) -> None:
        """Undo the policy writes of a setup that failed part-way."""
        for rel, original, new_dir in reversed(written):
            path = root / rel
            try:
                if original is not None:
                    _replace_file(root, rel, original)
                    continue
                # Only runs outside a lifecycle transaction, so nothing journals it.
                if path.is_file() and not path.is_symlink():
                    path.unlink()
                if new_dir and path.parent.is_dir():
                    path.parent.rmdir()
            except OSError as exc:
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
        for rel, mode in manifest.ownership_modes.items():
            if not self._is_policy_rel(rel):
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
