"""opencode integration."""

import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pathspec

from ..base import IntegrationOption, MarkdownIntegration
from ..manifest import IntegrationManifest

# OpenCode 1.18.31 and 1.19.3 glob through ripgrep without ``--hidden``.
# Root ``.ignore`` rules ``!.specify/`` and ``!.specify/**`` make
# ``.specify/**/*`` return constitution, template, and script paths on
# that path (``opencode debug rg files --glob``, the same ``Ripgrep.glob``
# call the glob tool makes). ``!.specify/**`` alone does not. OpenCode 2.x
# was not part of that check.
_SPECIFY_IGNORE_RULES = ("!.specify/", "!.specify/**")


class OpencodeIntegration(MarkdownIntegration):
    key = "opencode"
    multi_install_safe = True
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "commands",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/commands",
        "legacy_dir": ".opencode/command",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    CANONICAL_TO_NATIVE = {
        "pre_tool_use": "tool.execute.before",
        "post_tool_use": "tool.execute.after",
        # session_start maps to the system-prompt transform hook (not the
        # session.created event) so the handler's stdout is injected into the
        # system prompt — session.created has no output channel. The hook
        # fires per LLM request, which keeps the context present across
        # compaction at the cost of running the handler per turn.
        "session_start": "experimental.chat.system.transform",
        # user_prompt_submit maps to chat.message so handler stdout is
        # injected as a synthetic text part on the user's message.
        "user_prompt_submit": "chat.message",
        "session_end": "session.deleted",
    }
    events_config_file = "opencode.json"
    events_format = "ts-plugin"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--configure-ignore-file",
                is_flag=True,
                default=False,
                help=(
                    "Append !.specify/ and !.specify/** to the project root "
                    ".ignore so OpenCode can glob hidden Spec Kit files. "
                    "Uninstall leaves .ignore in place."
                ),
            )
        )
        return opts

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Validate an explicit ``.ignore`` opt-in, then render commands.

        Command files stay on the Markdown layout from ``super().setup()``.
        ``--configure-ignore-file`` appends missing ``!.specify/`` and
        ``!.specify/**`` rules and records the root file as partial
        ownership. Without the flag the root ``.ignore`` is left alone.
        """
        configure = (parsed_options or {}).get("configure_ignore_file") is True
        if configure:
            _preflight_root_ignore(manifest)
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        if configure:
            created.append(_configure_root_ignore(manifest))
        return created

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
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "run"]
        # Apply operator-injected extra args before the prompt-derived
        # --command and the canonical --format/-m flags so Spec Kit's
        # later appends remain authoritative under repeated-flag CLI
        # semantics.
        self._apply_extra_args_env_var(args)

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args


def _ignore_newline(raw: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in raw else b"\n"


def _reject_hidden_specify_paths(path: Path, updated: bytes) -> None:
    """Fail when *updated* still hides Spec Kit paths, evaluated in file order."""
    from ..._assets import _locate_core_pack, _repo_root

    patterns = []
    for line in updated.decode("utf-8").splitlines():
        try:
            patterns.append(pathspec.GitIgnoreSpec.from_lines([line]).patterns[0])
        except (ValueError, IndexError):
            continue

    def ignored(candidate: str) -> bool:
        state = False
        for pattern in patterns:
            hit = pattern.include is not None and pattern.match_file(candidate) is not None
            state = bool(pattern.include) if hit else state
        return state

    def hides(probe: str) -> bool:
        parts = [part for part in probe.split("/") if part]
        built, ancestors = "", parts if probe.endswith("/") else parts[:-1]
        for part in ancestors:
            built = f"{built}/{part}" if built else part
            if ignored(built + "/"):
                return True
        return not probe.endswith("/") and ignored(probe)

    pack, repo = _locate_core_pack(), _repo_root()
    probes = {".specify/", ".specify/.gitignore", ".specify/memory/constitution.md"}
    for kind in ("templates", "scripts"):
        base = (pack if pack and (pack / kind).is_dir() else repo) / kind
        walk = () if not base.is_dir() else (base.iterdir() if kind == "templates" else base.rglob("*"))
        probes.update(
            f".specify/{kind}/{item.relative_to(base).as_posix()}"
            for item in walk
            if item.is_file() and "__pycache__" not in item.parts
            and not item.name.startswith(".") and item.name != "vscode-settings.json"
        )
    specify = path.parent / ".specify"
    if specify.is_dir() and not specify.is_symlink():
        probes.update(f.relative_to(path.parent).as_posix() for f in specify.rglob("*") if f.is_file())
    hidden = sorted(probe for probe in probes if hides(probe))
    if hidden:
        raise ValueError(
            f"A later exclusion in {path} hides {hidden[0]}. "
            "Move !.specify/ and !.specify/** below it, then rerun."
        )


def _with_specify_ignore_rules(raw: bytes) -> bytes:
    """Append missing Spec Kit rules, keeping *raw* as a byte prefix.

    New rules use the file's newline (``\\n`` when *raw* is empty) and a
    trailing newline. Exact ASCII lines are matched without decoding.
    Non-UTF-8 files are rejected before this runs and are not preserved.
    """
    if not raw:
        newline = b"\n"
        body = newline.join(rule.encode("ascii") for rule in _SPECIFY_IGNORE_RULES)
        return body + newline

    present = set(raw.splitlines())
    missing = [
        rule
        for rule in _SPECIFY_IGNORE_RULES
        if rule.encode("ascii") not in present
    ]
    if not missing:
        return raw

    newline = _ignore_newline(raw)
    addition = b"" if raw.endswith(b"\n") else newline
    addition += newline.join(rule.encode("ascii") for rule in missing) + newline
    return raw + addition


def _preflight_root_ignore(manifest: IntegrationManifest) -> tuple[Path, bytes, bytes]:
    path = manifest.project_root / ".ignore"
    if path.is_symlink():
        raise ValueError(f"Refusing to configure symlinked .ignore: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(
            f"Refusing to configure .ignore because it is not a regular file: {path}"
        )
    try:
        raw = path.read_bytes() if path.is_file() else b""
    except OSError as exc:
        raise OSError(f"Cannot read .ignore at {path}") from exc
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{path} is not UTF-8 ({exc.reason} at byte {exc.start}). "
            "Convert it to UTF-8 and rerun; ripgrep stops at the first invalid byte."
        ) from exc
    updated = _with_specify_ignore_rules(raw)
    _reject_hidden_specify_paths(path, updated)
    if updated != raw and path.exists() and not os.access(path, os.W_OK):
        raise PermissionError(f"Cannot update .ignore at {path}")
    if updated != raw and not os.access(path.parent, os.W_OK):
        if path.exists():
            raise PermissionError(f"Cannot update .ignore at {path}")
        raise PermissionError(f"Cannot create .ignore at {path}")
    return path, raw, updated


def _configure_root_ignore(manifest: IntegrationManifest) -> Path:
    """Recheck root ``.ignore``, write it atomically, and record partial ownership."""
    path, raw, updated = _preflight_root_ignore(manifest)
    if updated == raw and path.is_file():
        from .._file_changes import before_file_change

        before_file_change(path)
        manifest.record_existing(".ignore", ownership="partial")
        return path

    from ...shared_infra import _write_shared_bytes

    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    _write_shared_bytes(manifest.project_root, path, updated, mode=mode)
    manifest.record_existing(".ignore", ownership="partial")
    return path
