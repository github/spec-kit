"""Codex CLI integration — skills-based agent.

Codex uses the ``.agents/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import stat
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .._file_changes import changing_file
from ..base import IntegrationOption, SkillsIntegration
# The manifest has no public validator; this is the check ``record_file`` and
# ``record_existing`` apply, so policies are planned, cleaned up and recorded by
# the same lexical path. Pinned by ``TestCodexManifestInternals``.
from ..manifest import IntegrationManifest, _validate_record_path

logger = logging.getLogger(__name__)

# Codex reads ``openai.yaml`` with serde_yaml, which follows the YAML 1.2 core
# schema. PyYAML's YAML 1.1 rules would turn ``display_name: On`` into ``True``
# and ``010`` into 8, changing user values on a round trip.
_YAML11_ONLY_TAGS = {
    f"tag:yaml.org,2002:{name}" for name in ("bool", "int", "float", "timestamp")
}
_YAML12_RESOLVERS = (
    ("tag:yaml.org,2002:bool", r"true|True|TRUE|false|False|FALSE", "tTfF"),
    ("tag:yaml.org,2002:int", r"[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+", "-+0123456789"),
    (
        "tag:yaml.org,2002:float",
        r"[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
        r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN)",
        "-+0123456789.",
    ),
)
_YAML12_INT = re.compile(_YAML12_RESOLVERS[1][1])


class _Yaml12Loader(yaml.SafeLoader):
    """Safe loader that resolves plain scalars by the YAML 1.2 core schema."""


_Yaml12Loader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag not in _YAML11_ONLY_TAGS]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class _Yaml12Dumper(yaml.SafeDumper):
    """Safe dumper that also quotes strings YAML 1.2 would read as non-strings."""


for _tag, _pattern, _first in _YAML12_RESOLVERS:
    for _cls in (_Yaml12Loader, _Yaml12Dumper):
        _cls.add_implicit_resolver(_tag, re.compile(f"^(?:{_pattern})$"), list(_first))


def _construct_yaml12_int(loader: _Yaml12Loader, node: yaml.ScalarNode) -> int:
    value = loader.construct_scalar(node)
    if not _YAML12_INT.fullmatch(value):  # an explicit ``!!int`` in another form
        return loader.construct_yaml_int(node)
    if value.startswith("0o"):
        return int(value[2:], 8)
    if value.startswith("0x"):
        return int(value[2:], 16)
    return int(value, 10)


_Yaml12Loader.add_constructor("tag:yaml.org,2002:int", _construct_yaml12_int)


def _dump_openai_yaml(data: dict[str, Any]) -> str:
    return yaml.dump(data, Dumper=_Yaml12Dumper, sort_keys=False, allow_unicode=True)


def _replace_file(path: Path, content: bytes) -> None:
    """Replace ``path`` through a sibling file, so a failed write leaves it intact."""
    with changing_file(path):
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
            try:
                temporary_path.chmod(stat.S_IMODE(path.stat().st_mode))
            except OSError:
                pass  # best effort: keeping the content matters more than the mode
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)


# Container shapes from Codex's ``SkillMetadataFile`` (codex-rs/skills/src/
# metadata.rs). A mismatch makes Codex ignore the whole file, policy included.
# Scalar leaves and ``products`` values are not checked, so a newer Codex value
# is never rejected here.
def _schema_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def expect(value: Any, kind: type, label: str) -> bool:
        if value is None or isinstance(value, kind):
            return value is not None
        name = "a mapping" if kind is dict else "a list"
        errors.append(f"'{label}' must be {name}, got {type(value).__name__}")
        return False

    expect(data.get("interface"), dict, "interface")
    dependencies = data.get("dependencies")
    if expect(dependencies, dict, "dependencies"):
        tools = dependencies.get("tools")
        if expect(tools, list, "dependencies.tools"):
            for index, tool in enumerate(tools):
                if expect(tool, dict, f"dependencies.tools[{index}]"):
                    expect(tool.get("oauth"), dict, f"dependencies.tools[{index}].oauth")
    policy = data.get("policy")
    if expect(policy, dict, "policy"):
        expect(policy.get("products"), list, "policy.products")
    return errors


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
            loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=_Yaml12Loader)
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
        try:
            # A symlinked ancestor makes the file unsafe to rehash or delete.
            _validate_record_path(Path(rel), root)
            if path.is_symlink() or not path.is_file():
                return False
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
            data = self._load_openai_yaml(path, rel)
            ownership = "whole" if self._is_generated(project_root, rel, prior) else "partial"
        policy = data.get("policy") or {}
        if ownership == "partial" and not tracked and policy.get("allow_implicit_invocation") is False:
            # The user already set it; claiming it would let cleanup remove their setting.
            return None
        policy["allow_implicit_invocation"] = False
        data["policy"] = policy
        errors = _schema_errors(data)
        if errors:
            raise ValueError(
                f"Cannot update {rel}: Codex would ignore this file, including the "
                f"policy: {'; '.join(errors)}"
            )
        return rel, _dump_openai_yaml(data), ownership

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
                _replace_file(path, _dump_openai_yaml(data).encode("utf-8"))
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
            for name in sorted(CORE_COMMAND_NAMES):
                rel = self._policy_rel(name)
                try:
                    # Policies are recorded and cleaned up by their lexical
                    # path, which a symlinked skills or skill directory would
                    # not match.
                    _validate_record_path(Path(rel), root)
                except ValueError as exc:
                    raise ValueError(f"Cannot use --no-model-invocation: {exc}") from exc
                self._plan_policy(root, rel, prior)
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        planned: list[tuple[str, str, str]] = []
        if enabled:
            for skill_file in [f for f in created if f.name == "SKILL.md"]:
                name = skill_file.parent.name
                if skill_file.parent.parent != root / skills_rel:
                    continue
                if self._is_core_command_skill_dir(name):
                    plan = self._plan_policy(root, self._policy_rel(name.removeprefix("speckit-")), prior)
                    if plan is not None:
                        planned.append(plan)
        for rel, content, ownership in planned:
            path = root / rel
            if path.exists():
                # ``record_file`` truncates in place; keep the user's file
                # intact if the write fails.
                _validate_record_path(Path(rel), root)
                _replace_file(path, content.encode("utf-8"))
                manifest.record_existing(rel, ownership=ownership)
                created.append(path)
            else:
                created.append(manifest.record_file(rel, content, ownership=ownership))
        if prior is not None:
            self._released_policy_rels = frozenset(
                self._release_prior_policies(root, manifest, prior, {rel for rel, _, _ in planned})
            )
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
        # report the ones cleaned as preserved modified files. Generated files
        # are left to ``uninstall``: content-equal ones are re-hashed so it
        # deletes them, and edited ones lose only the policy unless forced.
        root = project_root.resolve()
        cleaned: set[Path] = set()
        for rel, mode in manifest.ownership_modes.items():
            if not self._is_policy_rel(rel):
                continue
            if mode != "whole":
                if self._remove_policy(root, rel):
                    cleaned.add(root / rel)
            elif self._is_generated(root, rel, manifest):
                manifest.record_existing(rel)
            elif not force:
                self._remove_policy(root, rel)
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
