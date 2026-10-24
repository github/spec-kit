"""
Mistral Vibe CLI integration — skills-based agent.

Vibe uses ``.vibe/skills/speckit-<name>/SKILL.md`` layout (enforced since v2.0.0).
"""

from __future__ import annotations

import logging
import os
import re
import tomllib
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration
from .._file_changes import unlink as _unlink_file, write_bytes as _write_bytes
from ..manifest import IntegrationManifest
from ..._toml_string import escape_toml_basic
from ..._utils import dump_frontmatter

# Per-command frontmatter overrides for skills that should run in a forked
# subagent context.
#
# This is intentionally empty. ``analyze`` was previously forked (added in
# #2511) on the assumption that its heavy reads collapse to a short summary,
# but in practice ``/speckit-analyze`` returns a 300-500 line report that is
# injected back into the main conversation. In long sessions each subsequent
# fork inherits that growing context, compounding overhead until the chat
# freezes (#3185). Until a command genuinely returns a compact result, no
# command opts into ``context: fork``. The injection mechanism below stays in
# place so a future command can be added here when that holds true.
FORK_CONTEXT_COMMANDS: dict[str, dict[str, str]] = {}

# Keep the native Vibe timeout slightly longer than the dispatcher's inner
# timeout so Vibe does not terminate the dispatcher before it can reap its
# child process.
VIBE_EVENT_TIMEOUT_BUFFER = 5

logger = logging.getLogger(__name__)


def _toml_physical_lines(source: str) -> Iterator[str]:
    """Yield TOML physical lines, preserving their original terminators.

    TOML recognizes LF and CRLF only.  In particular, Python's ``splitlines``
    would incorrectly treat bare CR and Unicode line-separator characters as
    physical line boundaries.
    """
    start = 0
    while (newline := source.find("\n", start)) >= 0:
        yield source[start:newline + 1]
        start = newline + 1
    if start < len(source):
        yield source[start:]


class VibeIntegration(SkillsIntegration):
    """Integration for Mistral Vibe skills."""

    key = "vibe"
    config = {
        "name": "Mistral Vibe",
        "folder": ".vibe/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/mistralai/mistral-vibe",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".vibe/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    # Vibe's hooks schema supports exactly three hook types (HookConfig
    # rejects anything else): pre_tool, post_tool, post_agent. Unsupported
    # canonical events (session_start/session_end/user_prompt_submit) are
    # intentionally absent so install_integration_events skips them with a
    # warning instead of writing entries Vibe would refuse to load.
    CANONICAL_TO_NATIVE = {
        "pre_tool_use": "pre_tool",
        "post_tool_use": "post_tool",
        "stop": "post_agent",
    }
    events_config_file = ".vibe/hooks.toml"
    events_format = "toml-vibe"
    # Vibe parses any non-empty hook stdout as a JSON HookStructuredResponse;
    # plain text is reported as a hook failure and its output dropped. The
    # dispatcher therefore wraps handler stdout as {"decision": "allow",
    # "hook_specific_output": {"additional_context": ...}} for every event:
    # post_tool injects additional_context, pre_tool/post_agent ignore it but
    # still parse cleanly.
    events_context_envelope = {"*": "hook_specific_output"}

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills",
            ),
        )
        return opts

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
        """Build CLI arguments for non-interactive ``vibe`` execution.

        ``SkillsIntegration``'s default appends ``--model`` and
        ``--output-format``, neither of which exists in the Vibe CLI, so a
        dispatched step exits 2 at argument parsing whenever either flag ends
        up appended (a configured ``model``, or ``output_json=True``). Vibe's
        structured output is ``--output json``. ``model`` is deliberately
        dropped: Vibe has no per-invocation model flag and selects its model
        out of band via ``active_model`` in its config (or ``VIBE_ACTIVE_MODEL``).
        """
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if output_json:
            args.extend(["--output", "json"])
        return args

    def _render_skill(self, template_name: str, frontmatter: dict[str, Any], body: str) -> str:
        """Render a processed command template as a Vibe skill."""
        skill_name = f"speckit-{template_name.replace('.', '-')}"
        description = frontmatter.get(
            "description",
            f"Spec-kit workflow command: {template_name}",
        )
        skill_frontmatter = self._build_skill_fm(
            skill_name, description, f"templates/commands/{template_name}.md"
        )
        frontmatter_text = dump_frontmatter(skill_frontmatter)
        return f"---\n{frontmatter_text}\n---\n\n{body.strip()}\n"

    def _build_skill_fm(self, name: str, description: str, source: str) -> dict:
        from specify_cli.agents import CommandRegistrar
        return CommandRegistrar.build_skill_frontmatter(
            self.key, name, description, source
        )

    @staticmethod
    def _inject_frontmatter_flag(content: str, key: str, value: str = "true") -> str:
        """Insert ``key: value`` before the closing ``---`` if not already present."""
        lines = content.splitlines(keepends=True)

        # Pre-scan: bail out if already present in frontmatter
        dash_count = 0
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2:
                    break
                continue
            if dash_count == 1 and stripped.startswith(f"{key}:"):
                return content

        # Inject before the closing --- of frontmatter. Preserve the
        # existing EOL style, but default to "\n" (rather than "") when the
        # closing delimiter is the last line of the file with no trailing
        # newline -- otherwise the injected text glues onto the "---"
        # (e.g. "user-invocable: true---"), destroying the delimiter so a
        # later call's pre-scan/injection never finds a second "---" and
        # silently drops that key entirely.
        out: list[str] = []
        dash_count = 0
        injected = False
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2 and not injected:
                    if line.endswith("\r\n"):
                        eol = "\r\n"
                    elif line.endswith("\n"):
                        eol = "\n"
                    else:
                        eol = "\n"
                    out.append(f"{key}: {value}{eol}")
                    injected = True
            out.append(line)
        return "".join(out)

    @staticmethod
    def _skill_stem_from_content(content: str) -> str | None:
        """Derive the command stem (e.g. ``analyze``) from a skill's frontmatter.

        Reads the ``name:`` field of the first frontmatter block and strips
        the ``speckit-`` prefix. Returns ``None`` when no name is present.
        """
        dash_count = 0
        for line in content.splitlines():
            stripped = line.rstrip("\r\n")
            if stripped == "---":
                dash_count += 1
                if dash_count == 2:
                    break
                continue
            if dash_count == 1 and stripped.startswith("name:"):
                name = stripped[len("name:"):].strip().strip('"').strip("'")
                if name.startswith("speckit-"):
                    return name[len("speckit-"):]
                return name or None
        return None

    def post_process_skill_content(self, content: str) -> str:
        """Inject Vibe-specific frontmatter flags.

        Applied by every skill-generation path (setup, presets, extensions),
        so Vibe-specific frontmatter stays consistent however the SKILL.md
        was produced.
        """
        updated = super().post_process_skill_content(content)
        updated = self._inject_frontmatter_flag(updated, "user-invocable")
        updated = self._inject_frontmatter_flag(updated, "disable-model-invocation", "false")

        stem = self._skill_stem_from_content(updated)
        if stem:
            fork_config = FORK_CONTEXT_COMMANDS.get(stem)
            if fork_config:
                for key, value in fork_config.items():
                    updated = self._inject_frontmatter_flag(updated, key, value)
        return updated

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Vibe skills then inject Vibe-specific flags"""
        import click

        click.secho(
            "Warning: The .vibe/skills layout requires Mistral Vibe v2.0.0 or newer. "
            "Please ensure your installation is up to date.",
            fg="yellow",
            err=True,
        )

        return super().setup(project_root, manifest, parsed_options=parsed_options, **opts)

    @staticmethod
    def _hook_target_os() -> str:
        """Return the shell Vibe uses for hook commands on this host."""
        return "cmd" if os.name == "nt" else "host"

    @staticmethod
    def _toml_quote(value: str) -> str:
        """Render a TOML basic string without exposing Vibe syntax to events."""
        return escape_toml_basic(value)

    @staticmethod
    def _parse_toml_header(code: str) -> tuple[bool, tuple[str | None, ...] | None]:
        """Return a TOML header's kind and key path, or ``None`` if it is not one.

        This deliberately recognizes only header syntax, not full TOML.  Its
        caller has already excluded comments and unterminated strings.  A
        ``None`` key component represents a quoted basic key with an escape:
        it is still a real header, but cannot be the literal ``hooks`` key we
        manage without decoding TOML escapes.
        """
        text = code.strip(" \t")
        is_array = text.startswith("[[")
        if is_array:
            if not text.endswith("]]") or len(text) < 5:
                return False, None
            body = text[2:-2]
        else:
            if not text.startswith("[") or not text.endswith("]") or len(text) < 3:
                return False, None
            body = text[1:-1]

        parts: list[str | None] = []
        index = 0
        length = len(body)
        while True:
            while index < length and body[index] in " \t":
                index += 1
            if index == length:
                return False, None

            if body[index] in "\"'":
                quote = body[index]
                index += 1
                start = index
                escaped = False
                while index < length:
                    char = body[index]
                    if quote == "\"" and escaped:
                        escaped = False
                    elif quote == "\"" and char == "\\":
                        escaped = True
                    elif char == quote:
                        raw_part = body[start:index]
                        parts.append(raw_part if "\\\\" not in raw_part else None)
                        index += 1
                        break
                    index += 1
                else:
                    return False, None
            else:
                start = index
                while index < length and (body[index].isalnum() or body[index] in "_-"):
                    # TOML bare keys are ASCII-only; non-ASCII alphanumerics
                    # make this header ambiguous, so fail closed.
                    if not body[index].isascii():
                        return False, None
                    index += 1
                if start == index:
                    return False, None
                parts.append(body[start:index])

            while index < length and body[index] in " \t":
                index += 1
            if index == length:
                return is_array, tuple(parts)
            if body[index] != ".":
                return False, None
            index += 1

    @staticmethod
    def _managed_hook_spans(source: str) -> list[tuple[int, int]] | None:
        """Find Specify-owned hook blocks in valid TOML without interpreting values.

        The scanner only needs TOML's lexical boundaries: comments, ordinary
        strings, multiline strings, multiline arrays, and standalone table
        headers. A parser validity gate and the scanner both return ``None``
        for malformed or ambiguous input so callers can leave the source
        byte-for-byte untouched.

        A block ends after its last line of TOML and the blank lines right
        after it. A standalone comment that follows stays with the content
        after it, such as the user hook it introduces (#5079).
        """
        try:
            tomllib.loads(source)
        except tomllib.TOMLDecodeError:
            return None

        spans: list[tuple[int, int]] = []
        current_start: int | None = None
        current_end = 0
        current_after_comment = False
        current_is_hooks = False
        current_has_marker = False
        multiline: str | None = None
        array_depth = 0
        offset = 0

        for line in _toml_physical_lines(source):
            content = line.rstrip("\r\n")
            index = 0
            code_end = len(content)
            line_starts_in_multiline_string = multiline is not None
            line_has_multiline_string = line_starts_in_multiline_string
            line_starts_in_array = array_depth > 0
            structural = list(content)
            while index < len(content):
                char = content[index]
                if multiline is not None:
                    if multiline == '"""' and char == "\\":
                        # A basic multiline string may escape its next
                        # character (including a newline continuation).
                        structural[index:min(index + 2, len(content))] = " " * min(
                            2, len(content) - index
                        )
                        index += 2
                        continue
                    if content.startswith(multiline, index):
                        run_end = index
                        while run_end < len(content) and content[run_end] == multiline[0]:
                            run_end += 1
                        if run_end - index > 5:
                            return None
                        if run_end - index >= 3:
                            structural[index:run_end] = " " * (run_end - index)
                            multiline = None
                            index = run_end
                            continue
                    structural[index] = " "
                    index += 1
                    continue

                if char == "#":
                    code_end = index
                    break
                if content.startswith('"""', index) or content.startswith("'''", index):
                    multiline = content[index:index + 3]
                    line_has_multiline_string = True
                    structural[index:index + 3] = "   "
                    index += 3
                    continue
                if char in "\"'":
                    quote = char
                    start = index
                    index += 1
                    while index < len(content):
                        if quote == "\"" and content[index] == "\\":
                            if index + 1 == len(content):
                                return None
                            index += 2
                            continue
                        if content[index] == quote:
                            index += 1
                            structural[start:index] = " " * (index - start)
                            break
                        index += 1
                    else:
                        return None
                    continue
                index += 1

            if multiline is not None and not line.endswith(("\n", "\r")):
                return None

            # A multiline string can contain arbitrary text that resembles a
            # header or marker. A header/assignment cannot validly share its
            # physical line, so ignore that line for ownership purposes.
            code = "" if line_has_multiline_string else content[:code_end]
            is_array, header_path = (
                VibeIntegration._parse_toml_header(code)
                if not line_starts_in_array and not line_has_multiline_string
                else (False, None)
            )
            if header_path is not None:
                if current_start is not None and current_has_marker:
                    spans.append((current_start, current_end))
                current_start = offset
                current_is_hooks = is_array and header_path == ("hooks",)
                current_has_marker = False
            elif (
                not line_starts_in_array
                and not line_starts_in_multiline_string
                and content.lstrip(" \t").startswith("[")
            ):
                # A line that starts like a header but cannot be classified is
                # ambiguous (for example, a malformed header); never remove
                # content from such a file.  Inspect the original line here:
                # triple-quoted tokens are illegal in a header, but would
                # otherwise blank ``code`` before this guard sees it.
                return None
            elif current_is_hooks and re.fullmatch(
                r"[ \t]*speckit_marker[ \t]*=[ \t]*true[ \t]*", code
            ):
                current_has_marker = True

            if header_path is None:
                for char in structural[:code_end]:
                    if char == "[":
                        array_depth += 1
                    elif char == "]":
                        array_depth -= 1
                        if array_depth < 0:
                            return None

            # Lines inside a multiline string or array are part of the value,
            # even when they look like comments.
            if line_starts_in_array or line_has_multiline_string or code.strip(" \t"):
                current_end = offset + len(line)
                current_after_comment = False
            elif content.strip(" \t"):
                current_after_comment = True
            elif not current_after_comment:
                current_end = offset + len(line)

            offset += len(line)

        if multiline is not None or array_depth:
            return None
        if current_start is not None and current_has_marker:
            spans.append((current_start, current_end))
        return spans

    @classmethod
    def _without_managed_hooks(cls, source: str) -> str | None:
        """Remove managed spans, preserving every other source slice verbatim."""
        spans = cls._managed_hook_spans(source)
        if spans is None:
            return None
        if not spans:
            return source
        slices: list[str] = []
        previous_end = 0
        for start, end in spans:
            slices.append(source[previous_end:start])
            previous_end = end
        slices.append(source[previous_end:])
        return "".join(slices)

    def merge_vibe_event_hooks(
        self,
        project_root: Path,
        events: dict[str, list[dict[str, Any]]],
        *,
        build_dispatcher_command: Callable[[str, str, str, Any], str],
        native_timeout: Callable[[Any], int],
        ensure_safe_destination: Callable[[Path], None],
    ) -> bool:
        """Render and merge managed Vibe hooks without disturbing user content.

        This intentionally lives on Vibe rather than in shared events: Vibe's
        flat TOML schema, supported fields, unique-name rule, native shell
        quoting, and ownership-marker cleanup are all Vibe-specific.
        """
        lines: list[str] = []
        used_names: set[str] = set()
        for event, handlers in events.items():
            native = self.CANONICAL_TO_NATIVE[event]
            for config in handlers:
                command = config.get("command", "")
                dispatcher_command = build_dispatcher_command(
                    command,
                    event,
                    self._hook_target_os(),
                    config.get("timeout", 60),
                )
                command_stem = command.split(".")[-1] if command else "unknown"
                command_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", command_stem) or "unknown"
                base_name = f"speckit-{native}-{command_stem}"
                hook_name = base_name
                suffix = 2
                while hook_name in used_names:
                    hook_name = f"{base_name}-{suffix}"
                    suffix += 1
                used_names.add(hook_name)

                lines.extend(
                    [
                        "[[hooks]]",
                        f"name = {self._toml_quote(hook_name)}",
                        f"type = {self._toml_quote(native)}",
                    ]
                )
                matcher = config.get("matcher", "*")
                if matcher and matcher != "*" and native in ("pre_tool", "post_tool"):
                    lines.append(f"match = {self._toml_quote('re:' + matcher)}")
                lines.extend(
                    [
                        f"command = {self._toml_quote(dispatcher_command)}",
                        f"timeout = {native_timeout(config.get('timeout', 60) + VIBE_EVENT_TIMEOUT_BUFFER)}",
                        "speckit_marker = true",
                        "",
                    ]
                )
        return self._merge_managed_hooks(
            project_root / self.events_config_file,
            "\n".join(lines),
            ensure_safe_destination=ensure_safe_destination,
        )

    def remove_vibe_event_hooks(
        self,
        project_root: Path,
        *,
        ensure_safe_destination: Callable[[Path], None],
    ) -> bool:
        """Remove only Specify-owned Vibe hooks and delete an owned-only file."""
        path = project_root / self.events_config_file
        if not path.exists():
            return False
        ensure_safe_destination(path)
        try:
            with path.open(encoding="utf-8", newline="") as file:
                existing = file.read()
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning(
                "Could not read %s (it may be unreadable or not UTF-8); "
                "skipping event-config cleanup to preserve user content.",
                path,
            )
            logger.debug("Read error detail: %s", exc)
            return False

        cleaned = self._without_managed_hooks(existing)
        if cleaned is None:
            return False
        if cleaned == existing:
            return False
        non_comment_content = "\n".join(
            line
            for line in cleaned.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
        if not non_comment_content:
            _unlink_file(path, missing_ok=True)
            return True
        _write_bytes(path, cleaned.encode("utf-8"))
        return False

    def _merge_managed_hooks(
        self,
        path: Path,
        fragment: str,
        *,
        ensure_safe_destination: Callable[[Path], None],
    ) -> bool:
        """Replace managed entries while retaining unowned content.

        Active merges normalize trailing separators before appending generated
        hooks, so they do not promise byte-for-byte preservation.
        """
        ensure_safe_destination(path)
        existing = ""
        if path.exists():
            try:
                with path.open(encoding="utf-8", newline="") as file:
                    existing = file.read()
            except (OSError, UnicodeDecodeError) as exc:
                logger.warning(
                    "Could not read %s (it may be unreadable or not UTF-8); "
                    "skipping event-config merge to preserve user content.",
                    path,
                )
                logger.debug("Read error detail: %s", exc)
                return False
        cleaned = self._without_managed_hooks(existing)
        if cleaned is None:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_bytes(path, (cleaned.rstrip() + "\n\n" + fragment + "\n").encode("utf-8"))
        return True
