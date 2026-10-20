"""opencode integration."""

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

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
        """Render commands, then honor an explicit ``.ignore`` opt-in.

        Command files stay on the Markdown layout from ``super().setup()``.
        ``--configure-ignore-file`` appends missing ``!.specify/`` and
        ``!.specify/**`` rules and records the root file as partial
        ownership. Without the flag the root ``.ignore`` is left alone.
        """
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        if (parsed_options or {}).get("configure_ignore_file") is True:
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


def _present_ignore_rules(text: str) -> set[str]:
    present: set[str] = set()
    for line in text.splitlines():
        if line in _SPECIFY_IGNORE_RULES:
            present.add(line)
    return present


def _with_specify_ignore_rules(raw: bytes) -> bytes:
    """Append missing Spec Kit rules, keeping *raw* as a byte prefix.

    New rules use the file's newline (``\\n`` when *raw* is empty) and a
    trailing newline. Rules already present as exact lines are not repeated.
    """
    if not raw:
        newline = b"\n"
        body = newline.join(rule.encode("ascii") for rule in _SPECIFY_IGNORE_RULES)
        return body + newline

    missing = [
        rule
        for rule in _SPECIFY_IGNORE_RULES
        if rule not in _present_ignore_rules(raw.decode("utf-8"))
    ]
    if not missing:
        return raw

    newline = _ignore_newline(raw)
    addition = b"" if raw.endswith(b"\n") else newline
    addition += newline.join(rule.encode("ascii") for rule in missing) + newline
    return raw + addition


def _configure_root_ignore(manifest: IntegrationManifest) -> Path:
    """Record root ``.ignore`` with partial ownership.

    Symlinks are rejected before they are followed. Directories and
    unreadable files raise without a write. ``record_file`` journals a
    real change; an already-complete file is re-recorded in place.
    """
    path = manifest.project_root / ".ignore"
    if path.is_symlink():
        raise ValueError(f"Refusing to configure symlinked .ignore: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(
            f"Refusing to configure .ignore because it is not a regular file: {path}"
        )

    raw = path.read_bytes() if path.exists() else b""
    updated = _with_specify_ignore_rules(raw)
    if updated == raw and path.is_file():
        from .._file_changes import before_file_change

        before_file_change(path)
        manifest.record_existing(".ignore", ownership="partial")
        return path

    if path.exists() and not os.access(path, os.W_OK):
        raise PermissionError(f"Cannot update .ignore at {path}")
    if not path.exists() and not os.access(path.parent, os.W_OK):
        raise PermissionError(f"Cannot create .ignore at {path}")
    return manifest.record_file(".ignore", updated, ownership="partial")
