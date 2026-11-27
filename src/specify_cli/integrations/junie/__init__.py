"""Junie integration (JetBrains)."""

from ..base import MarkdownIntegration
from ..manifest import IntegrationManifest


import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# Note injected into hook sections so Junie maps dot-notation command
# names (from extensions.yml) to the hyphenated slash commands it uses.
_HOOK_COMMAND_NOTE = (
    "- When constructing slash commands from hook command names, "
    "replace dots (`.`) with hyphens (`-`). "
    "For example, `speckit.git.commit` → `/speckit-git-commit`.\n"
)


def format_junie_command_name(cmd_name: str) -> str:
    """Convert command name to Junie-compatible hyphenated format.

    Junie does not allow dots inside of slash-commands.
    This function converts dot-notation command names to hyphenated format.

    The function is idempotent: already-formatted names are returned unchanged.

    Examples:
        >>> format_junie_command_name("plan")
        'speckit-plan'
        >>> format_junie_command_name("speckit.plan")
        'speckit-plan'
        >>> format_junie_command_name("speckit.git.commit")
        'speckit-git-commit'

    Args:
        cmd_name: Command name in dot notation (speckit.foo.bar),
                  hyphenated format (speckit-foo-bar), or plain name (foo)

    Returns:
        Hyphenated command name with 'speckit-' prefix
    """
    cmd_name = cmd_name.replace(".", "-")

    if not cmd_name.startswith("speckit-"):
        cmd_name = f"speckit-{cmd_name}"

    return cmd_name


# Dotted ``speckit.*`` references in extension and preset command content.
_SPECKIT_DOTTED_REF = re.compile(r"\bspeckit\.[A-Za-z0-9-_]+(?:\.[A-Za-z0-9-_]+)*\b")


def _is_path_char(ch: str) -> bool:
    """Whether *ch* can end the directory part of a path before a separator."""
    return ch.isalnum() or ch in "._-~/\\}$+"


_SEGMENT_CHARS = frozenset("._-~+@$%")
_QUOTE_OPEN_BOUNDARY = frozenset(' \t\r\n"\'`([<{:=-')
_SEP_LEADING_BOUNDARY = frozenset(' \t\r\n"\'`([<{')


def _is_segment_char(ch: str) -> bool:
    """Whether *ch* can appear inside an unquoted filename or directory segment."""
    return ch.isalnum() or ch in _SEGMENT_CHARS


def _is_drive_prefix(text: str, sep: int) -> bool:
    """Whether a Windows drive (``C:``) ends right before the separator at *sep*.

    The drive letter must stand alone, so ``C:\\speckit.foo.md`` and
    ``C:/speckit.foo.md`` count as root-level paths while ``ab:/speckit.foo.md``
    does not.
    """
    return (
        sep >= 2
        and text[sep - 1] == ":"
        and text[sep - 2].isascii()
        and text[sep - 2].isalpha()
        and (sep == 2 or not _is_path_char(text[sep - 3]))
    )


def _scan_path_structure(text: str) -> tuple[set[int], dict[int, int]]:
    """Precompute directory separators and inline bracket pairs in one linear pass."""
    dir_seps: set[int] = set()
    bracket_end: dict[int, int] = {}

    # Tracks open bracket candidates on the current line:
    # (open_idx, closer_char, has_prefix, space_count_at_open, slash_count_at_open).
    open_stack: list[tuple[int, str, bool, int, int]] = []
    # Latest same-line closing bracket immediately preceding index idx:
    # (close_idx, has_space, has_prefix).
    last_closed_bracket: tuple[int, bool, bool] | None = None

    # Linear %VAR% state machine.
    pct_start = -1
    pct_valid_body = False
    pct_valid_end = -1

    # Linear tracking of the latest separator on the current line.
    last_sep = -1
    last_sep_explicit = False
    since_sep_valid = True
    between_starts_speckit = False
    since_sep_len = 0

    space_count = 0
    slash_count = 0

    for idx, ch in enumerate(text):
        if ch in "\r\n":
            open_stack.clear()
            last_closed_bracket = None
            pct_start = -1
            pct_valid_body = False
            last_sep = -1
            last_sep_explicit = False
            since_sep_valid = True
            between_starts_speckit = False
            since_sep_len = 0
            slash_count += 1
            continue

        if ch in "/\\":
            is_dir = False
            if idx >= 1:
                prev = text[idx - 1]
                if _is_path_char(prev) or _is_drive_prefix(text, idx):
                    is_dir = True
                elif (
                    last_closed_bracket is not None
                    and last_closed_bracket[0] == idx - 1
                    and (not last_closed_bracket[1] or last_closed_bracket[2])
                ):
                    is_dir = True
                elif pct_valid_end == idx - 1:
                    is_dir = True

            if is_dir:
                dir_seps.add(idx)

            last_sep = idx
            last_sep_explicit = is_dir or (
                ch == "/" and (idx == 0 or text[idx - 1] in _SEP_LEADING_BOUNDARY)
            )
            since_sep_valid = True
            between_starts_speckit = False
            since_sep_len = 0
            slash_count += 1
            pct_start = -1
            pct_valid_body = False
            continue

        if ch in ("(", "["):
            closer = ")" if ch == "(" else "]"
            has_prefix = False
            if idx > 0 and _is_segment_char(text[idx - 1]):
                has_prefix = True
            elif (
                last_sep >= 0
                and since_sep_valid
                and since_sep_len > 0
                and last_sep_explicit
                and not (last_sep not in dir_seps and between_starts_speckit)
            ):
                has_prefix = True
            open_stack.append((idx, closer, has_prefix, space_count, slash_count))
        elif ch in (")", "]"):
            if open_stack and open_stack[-1][1] == ch:
                open_idx, _, has_prefix, open_spaces, open_slashes = open_stack.pop()
                if slash_count == open_slashes and idx > open_idx + 1:
                    bracket_end[open_idx] = idx
                    last_closed_bracket = (
                        idx,
                        space_count > open_spaces,
                        has_prefix,
                    )
            else:
                open_stack.clear()

        if ch == " ":
            space_count += 1
        elif ch.isspace():
            space_count += 1
            since_sep_valid = False
        elif not _is_segment_char(ch):
            since_sep_valid = False

        if last_sep >= 0:
            if since_sep_len == 0:
                between_starts_speckit = text.startswith("speckit.", last_sep + 1)
            since_sep_len += 1

        if ch == "%":
            if pct_start >= 0 and pct_valid_body and idx > pct_start + 1:
                pct_valid_end = idx
                pct_start = -1
                pct_valid_body = False
            else:
                pct_start = idx
                pct_valid_body = True
        elif pct_start >= 0:
            rel = idx - pct_start
            if rel == 1:
                if not (ch.isascii() and (ch.isalpha() or ch == "_")):
                    pct_start = -1
                    pct_valid_body = False
            elif not (ch.isascii() and (ch.isalnum() or ch in "_()")):
                pct_start = -1
                pct_valid_body = False

    return dir_seps, bracket_end


def _is_path_content(
    text: str, inner_start: int, inner_end: int, dir_seps: set[int]
) -> bool:
    """Whether ``text[inner_start:inner_end]`` is an explicit directory-qualified path."""
    inner = text[inner_start:inner_end]
    if (
        not inner
        or inner[0].isspace()
        or inner[-1].isspace()
        or "," in inner
        or ";" in inner
        or " /" in inner
        or " \\" in inner
    ):
        return False

    slash = inner.find("/")
    backslash = inner.find("\\")
    if slash < 0:
        rel_sep = backslash
    elif backslash < 0:
        rel_sep = slash
    else:
        rel_sep = min(slash, backslash)
    if rel_sep < 0:
        return False

    if rel_sep > 0:
        head = inner[:rel_sep]
        return not any(c.isspace() for c in head) and (
            (inner_start + rel_sep) in dir_seps
        )

    next_slash = inner.find("/", 1)
    next_backslash = inner.find("\\", 1)
    if next_slash < 0:
        rel_sep2 = next_backslash
    elif next_backslash < 0:
        rel_sep2 = next_slash
    else:
        rel_sep2 = min(next_slash, next_backslash)
    if rel_sep2 < 2:
        return False
    first_seg = inner[1:rel_sep2]
    return not any(c.isspace() for c in first_seg) and (
        (inner_start + rel_sep2) in dir_seps
    )


def _find_quoted_path_spans(
    text: str, dir_seps: set[int]
) -> list[tuple[int, int]]:
    """Find content spans of explicit same-line quoted paths in linear time."""
    spans: list[tuple[int, int]] = []
    n = len(text)
    for quote in ('"', "'", "`"):
        if quote not in text:
            continue
        open_idx = -1
        idx = text.find(quote)
        while idx >= 0:
            if open_idx >= 0 and ("\n" in text[open_idx:idx] or "\r" in text[open_idx:idx]):
                open_idx = -1
            if quote == "'" and 0 < idx < n - 1 and text[idx - 1].isalnum() and text[idx + 1].isalpha():
                idx = text.find(quote, idx + 1)
                continue
            if open_idx < 0:
                if idx == 0 or text[idx - 1] in _QUOTE_OPEN_BOUNDARY:
                    open_idx = idx
            else:
                if _is_path_content(text, open_idx + 1, idx, dir_seps):
                    spans.append((open_idx + 1, idx))
                open_idx = -1
            idx = text.find(quote, idx + 1)
    return spans


def _find_protected_segments(
    text: str, dir_seps: set[int], bracket_end: dict[int, int]
) -> list[tuple[int, int]]:
    """Compute unquoted path-qualified segments in a single linear pass."""
    spans: list[tuple[int, int]] = []
    n = len(text)
    i = 0
    while i < n:
        if _is_segment_char(text[i]) or i in bracket_end:
            seg_start = i
            while i < n:
                if _is_segment_char(text[i]):
                    i += 1
                elif i in bracket_end:
                    i = bracket_end[i] + 1
                else:
                    break
            seg_end = i
            if (seg_start >= 2 and (seg_start - 1) in dir_seps) or (
                seg_end < n and seg_end in dir_seps
            ):
                spans.append((seg_start, seg_end))
        else:
            i += 1
    return spans


def hyphenate_command_refs(text: str) -> str:
    """Hyphenate dotted ``speckit.*`` command references in *text*.

    Uses linear-time passes to preserve directory-qualified file names,
    script paths, dotted ancestor directories, bracketed path components, and
    quoted paths containing spaces, while hyphenating bare, slash-prefixed,
    and punctuation-wrapped command references.
    """
    if "speckit." not in text:
        return text

    dir_seps, bracket_end = _scan_path_structure(text)
    raw_spans = _find_protected_segments(text, dir_seps, bracket_end)
    raw_spans.extend(_find_quoted_path_spans(text, dir_seps))

    merged: list[tuple[int, int]] = []
    if raw_spans:
        raw_spans.sort()
        cur_start, cur_end = raw_spans[0]
        for start, end in raw_spans[1:]:
            if start <= cur_end:
                if end > cur_end:
                    cur_end = end
            else:
                merged.append((cur_start, cur_end))
                cur_start, cur_end = start, end
        merged.append((cur_start, cur_end))

    parts: list[str] = []
    last = 0
    span_idx = 0
    span_count = len(merged)

    for match in _SPECKIT_DOTTED_REF.finditer(text):
        m_start = match.start()
        m_end = match.end()
        while span_idx < span_count and merged[span_idx][1] < m_end:
            span_idx += 1
        parts.append(text[last:m_start])
        if (
            span_idx < span_count
            and merged[span_idx][0] <= m_start
            and m_end <= merged[span_idx][1]
        ):
            parts.append(match.group(0))
        else:
            parts.append(match.group(0).replace(".", "-"))
        last = m_end

    if last == 0:
        return text
    parts.append(text[last:])
    return "".join(parts)


def _hyphenate_frontmatter_refs(
    val: Any, _memo: dict[int, Any] | None = None
) -> Any:
    """Recursively hyphenate dotted ``speckit.*`` references in frontmatter values."""
    if isinstance(val, dict):
        if _memo is None:
            _memo = {}
        obj_id = id(val)
        if obj_id in _memo:
            return _memo[obj_id]
        out_dict: dict[Any, Any] = {}
        _memo[obj_id] = out_dict
        for k, v in val.items():
            out_dict[k] = _hyphenate_frontmatter_refs(v, _memo)
        return out_dict
    if isinstance(val, list):
        if _memo is None:
            _memo = {}
        obj_id = id(val)
        if obj_id in _memo:
            return _memo[obj_id]
        out_list: list[Any] = []
        _memo[obj_id] = out_list
        for item in val:
            out_list.append(_hyphenate_frontmatter_refs(item, _memo))
        return out_list
    if isinstance(val, str):
        if "speckit." not in val:
            return val
        dir_seps, _ = _scan_path_structure(val)
        if _is_path_content(val, 0, len(val), dir_seps):
            return val
        return hyphenate_command_refs(val)
    return val


class JunieIntegration(MarkdownIntegration):
    key = "junie"
    config = {
        "name": "Junie",
        "folder": ".junie/",
        "commands_subdir": "commands",
        "install_url": "https://junie.jetbrains.com/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".junie/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
        "inject_name": True,
        "format_name": format_junie_command_name,
        "invoke_separator": "-",
    }
    multi_install_safe = True
    invoke_separator = "-"

    def command_filename(self, template_name: str) -> str:
        return format_junie_command_name(template_name) + ".md"

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Junie installs hyphenated slash-commands (``/speckit-<name>``), so the
        dispatch invocation must match. The inherited MarkdownIntegration default
        builds the dotted ``/speckit.<name>``, which references a command Junie
        never registered. Reuse the same hyphenation as command_filename /
        the injected frontmatter name (see ``format_junie_command_name``),
        mirroring the forge integration.
        """
        invocation = "/" + format_junie_command_name(command_name)
        if args:
            invocation = f"{invocation} {args}"
        return invocation

    def process_template(self, *args, **kwargs):
        """Ensure shared templates render Junie command references with hyphens."""
        kwargs.setdefault("invoke_separator", self.invoke_separator)
        return super().process_template(*args, **kwargs)

    @staticmethod
    def _inject_hook_command_note(content: str) -> str:
        """Insert a dot-to-hyphen note before each hook output instruction.

        Targets the line ``- For each executable hook, output the following``
        and inserts the note on the line before it, matching its indentation.
        Skips if the note is already present.
        """
        if "replace dots" in content:
            return content

        def repl(m: re.Match[str]) -> str:
            indent = m.group(1)
            instruction = m.group(2)
            # ``eol`` is empty when the regex matched via ``$`` because the
            # instruction was the final line of a file with no trailing
            # newline. Default to ``\n`` so the note never collapses onto
            # the same line as the instruction.
            eol = m.group(3) or "\n"
            return (
                indent
                + _HOOK_COMMAND_NOTE.rstrip("\n")
                + eol
                + indent
                + instruction
                + eol
            )

        return re.sub(
            r"(?m)^(\s*)(- For each executable hook, output the following[^\r\n]*)(\r\n|\n|$)",
            repl,
            content,
        )

    @staticmethod
    def _rewrite_handoff_references(content: str) -> str:
        """Replace dot-notation agent references in handoffs with hyphens."""
        return re.sub(
            r"(?m)^(\s*agent:\s*)(speckit\.[A-Za-z0-9-_]+(?:\.[A-Za-z0-9-_]+)*)",
            lambda m: f"{m.group(1)}{format_junie_command_name(m.group(2))}",
            content,
        )

    def process_registered_command(
        self, frontmatter: dict[str, Any], body: str, *, source_id: str
    ) -> tuple[dict[str, Any], str]:
        """Hyphenate dotted command references in extension and preset commands.

        Junie only registers hyphenated slash commands, so references such as
        ``/speckit.git.commit`` in extension and preset command content are
        rewritten to ``/speckit-git-commit``.  Path components (``speckit.*.md``
        file names, script paths, and dotted ancestor directories) keep their
        dots.  Core commands (``source_id ==
        "core"``) are left unchanged; their references are rendered through
        ``invoke_separator`` instead.
        """
        if source_id == "core":
            return frontmatter, body
        return _hyphenate_frontmatter_refs(frontmatter), hyphenate_command_refs(body)

    def post_process_command_content(self, content: str) -> str:
        """Apply Junie-specific transformations to command content.

        Overrides the ``IntegrationBase`` hook of the same name so that
        ``CommandRegistrar.register_commands()`` (which dispatches to
        ``post_process_command_content``) applies these transforms to
        extension/preset command files too, not just core commands.
        """
        updated = self._inject_hook_command_note(content)
        updated = self._rewrite_handoff_references(updated)
        return updated

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Junie commands and apply post-processing transformations."""
        created = super().setup(project_root, manifest, parsed_options, **opts)

        # Post-process generated command files
        dest_dir = self.commands_dest(project_root).resolve()

        for path in created:
            # Only touch .md files under the commands directory
            try:
                path.resolve().relative_to(dest_dir)
            except ValueError:
                continue
            if path.suffix != ".md":
                continue

            content_bytes = path.read_bytes()
            content = content_bytes.decode("utf-8")

            updated = self.post_process_command_content(content)

            if updated != content:
                from .._file_changes import write_bytes

                write_bytes(path, updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

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
        """Build CLI arguments for non-interactive ``junie`` execution.

        ``MarkdownIntegration``'s default passes the prompt as ``-p <prompt>``,
        but Junie's ``-p`` is ``--project <path>``, so the prompt would be
        taken as the project directory and no task would be given. Junie
        takes a non-interactive task as a positional argument or ``--task``.
        """
        self.validate_runtime_config(integration_args, integration_options)
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self._resolve_executable(), "--task", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args
