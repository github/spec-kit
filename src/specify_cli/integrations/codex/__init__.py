"""Codex CLI integration — skills-based agent.

Codex uses the ``.agents/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .._file_changes import write_bytes
from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest, _validate_record_path

logger = logging.getLogger(__name__)


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
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError, UnicodeDecodeError) as exc:
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
        if path.is_symlink() or not path.is_file():
            return False
        try:
            if hashlib.sha256(path.read_bytes()).hexdigest() == prior.files[rel]:
                return True
            return self._load_openai_yaml(path, rel) == self._GENERATED_POLICY
        except (OSError, ValueError):
            return False

    def _plan_policy(
        self, project_root: Path, rel: str, prior: IntegrationManifest | None
    ) -> tuple[str, str, str] | None:
        """Return ``(rel, content, ownership)`` to write, or ``None`` to leave a user file alone."""
        path = project_root / rel
        # Checks every ancestor for symlinks before anything is read or written.
        _validate_record_path(Path(rel), project_root)
        tracked = prior is not None and rel in prior.files
        if not path.exists():
            data: dict[str, Any] = {}
            ownership = "whole"
        elif not path.is_file():
            raise ValueError(f"Cannot update {rel}: not a regular file")
        else:
            data = self._load_openai_yaml(path, rel)
            ownership = "whole" if self._is_generated(project_root, rel, prior) else "partial"
        policy = data.get("policy") or {}
        if ownership == "partial" and not tracked and policy.get("allow_implicit_invocation") is False:
            # The user already set it; claiming it would let cleanup remove their setting.
            return None
        policy["allow_implicit_invocation"] = False
        data["policy"] = policy
        return rel, yaml.safe_dump(data, sort_keys=False), ownership

    def _remove_policy(self, project_root: Path, rel: str) -> bool:
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
                write_bytes(path, yaml.safe_dump(data, sort_keys=False).encode("utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("Leaving %s unchanged: %s", rel, exc)
            return False
        return True

    def _release_prior_policies(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        prior: IntegrationManifest,
        keep: set[str],
    ) -> None:
        """Undo policies an earlier install wrote that this setup no longer writes.

        Unmodified generated files are deleted; in user files only the policy is removed.
        """
        generated = IntegrationManifest(self.key, project_root, version="policy-cleanup")
        modes = prior.ownership_modes
        for rel, recorded_hash in prior.files.items():
            if rel in keep or not self._is_policy_rel(rel):
                continue
            if self._is_generated(project_root, rel, prior):
                generated._files[rel] = recorded_hash
                continue
            self._remove_policy(project_root, rel)
            path = project_root / rel
            if modes[rel] == "whole" and path.is_file() and not path.is_symlink():
                # A generated file the user edited is theirs now, even if it no
                # longer parses. Track it as partial so upgrade's stale-file
                # pass, which deletes whole files with force, leaves it alone.
                try:
                    manifest.record_existing(rel, ownership="partial")
                except (OSError, ValueError) as exc:
                    logger.warning("Could not keep tracking %s: %s", rel, exc)
        # Each entry was checked above, content-equal ones included.
        generated.uninstall(project_root, force=True, remove_manifest=False)

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
        if enabled:
            # Reject unusable existing policy files before anything is written.
            from specify_cli.extensions import CORE_COMMAND_NAMES  # lazy: avoids circular import

            skills = PurePosixPath(self.registrar_config["dir"])
            for name in sorted(CORE_COMMAND_NAMES):
                rel = (skills / f"speckit-{name}" / "agents" / "openai.yaml").as_posix()
                agents_dir = (root / rel).parent
                if agents_dir.exists() or agents_dir.is_symlink():
                    self._plan_policy(root, rel, prior)
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        planned: list[tuple[str, str, str]] = []
        if enabled:
            for skill_file in [f for f in created if f.name == "SKILL.md"]:
                if self._is_core_command_skill_dir(skill_file.parent.name):
                    dest = skill_file.parent / "agents" / "openai.yaml"
                    plan = self._plan_policy(root, dest.relative_to(root).as_posix(), prior)
                    if plan is not None:
                        planned.append(plan)
        if prior is not None:
            self._release_prior_policies(root, manifest, prior, {rel for rel, _, _ in planned})
        for rel, content, ownership in planned:
            created.append(manifest.record_file(rel, content, ownership=ownership))
        return created

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        # ``manifest.uninstall`` never touches partial files, so remove the
        # managed policy from user-owned ``openai.yaml`` files here, and do not
        # report the ones cleaned as preserved modified files.
        root = project_root.resolve()
        cleaned = {
            root / rel
            for rel, mode in manifest.ownership_modes.items()
            if mode != "whole" and self._is_policy_rel(rel) and self._remove_policy(root, rel)
        }
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
    ) -> list[str] | None:
        # Codex uses ``codex exec "prompt"`` for non-interactive mode.
        # Resolve argv[0] via the shared executable resolver so operators can
        # override the binary with SPECKIT_INTEGRATION_CODEX_EXECUTABLE.
        self.validate_runtime_config(integration_args, integration_options)
        args: list[str] = [self._resolve_executable(), "exec", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.append("--json")
        return args

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
