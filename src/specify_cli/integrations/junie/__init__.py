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
_PATH_FILE_EXTENSIONS = frozenset(
    {
        "md",
        "sh",
        "ps1",
        "py",
        "js",
        "ts",
        "mjs",
        "cjs",
        "json",
        "yml",
        "yaml",
        "toml",
        "txt",
        "bat",
        "cmd",
        "exe",
        "rb",
        "pl",
        "cfg",
        "ini",
        "conf",
        "xml",
        "csv",
        "log",
    }
)


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


def _is_valid_env_var_end(text: str, seg_start: int, seg_end: int) -> bool:
    """Whether ``text[seg_start:seg_end]`` ends with a ``%VAR%`` directory token."""
    if seg_end - seg_start < 3 or text[seg_end - 1] != "%":
        return False
    pct_open = text.rfind("%", seg_start, seg_end - 1)
    if pct_open < 0 or seg_end - pct_open < 3:
        return False
    first = text[pct_open + 1]
    if not (first.isascii() and (first.isalpha() or first == "_")):
        return False
    return all(
        c.isascii() and (c.isalnum() or c in "_()")
        for c in text[pct_open + 2 : seg_end - 1]
    )


def _find_inline_bracket_end(line: str, open_idx: int) -> int:
    """Return the closing bracket index for a single-line non-path bracket group."""
    open_ch = line[open_idx]
    closer = ")" if open_ch == "(" else "]"
    n = len(line)
    idx = open_idx + 1
    while idx < n:
        ch = line[idx]
        if ch == closer:
            return idx if idx > open_idx + 1 else -1
        if ch in "/\\" or ch == open_ch:
            return -1
        idx += 1
    return -1


def _is_contraction_apostrophe(line: str, idx: int) -> bool:
    """Whether ``line[idx]`` is an in-word apostrophe (e.g. ``don't``)."""
    return 0 < idx < len(line) - 1 and line[idx - 1].isalnum() and line[idx + 1].isalpha()


def _is_valid_dir_component(comp: str, is_first: bool) -> bool:
    """Validate one directory component inside a standalone path string."""
    if not comp:
        return False
    if is_first and len(comp) == 2 and comp[0].isascii() and comp[0].isalpha() and comp[1] == ":":
        return True
    if comp.endswith(":"):
        return False
    if comp.endswith("%"):
        return _is_valid_env_var_end(comp, 0, len(comp))
    if is_first and comp[0] in "([":
        closer = ")" if comp[0] == "(" else "]"
        if comp.endswith(closer) and any(c.isspace() for c in comp[1:-1]):
            return False
    if " " in comp:
        for word in comp.split():
            stripped = word.lstrip("/")
            if _SPECKIT_DOTTED_REF.fullmatch(stripped) is not None:
                return False
    return _is_path_char(comp[-1]) or comp[-1] in ")]"


def _is_standalone_path(text: str, start: int, end: int) -> bool:
    """Whether ``text[start:end]`` is a standalone single-line directory path."""
    inner = text[start:end]
    if (
        not inner
        or inner[0].isspace()
        or inner[-1].isspace()
        or "\n" in inner
        or "\r" in inner
        or "\t" in inner
        or "," in inner
        or ";" in inner
        or " /" in inner
        or " \\" in inner
    ):
        return False

    last_sep = max(inner.rfind("/"), inner.rfind("\\"))
    if last_sep <= 0:
        return False

    dir_part = inner[:last_sep].replace("\\", "/")
    if dir_part.startswith("/"):
        dir_part = dir_part[1:]
    if not dir_part:
        return False
    dir_comps = dir_part.split("/")
    for idx, comp in enumerate(dir_comps):
        if not _is_valid_dir_component(comp, idx == 0):
            return False

    base = inner[last_sep + 1 :]
    if not base:
        return False
    if " " not in base:
        return True

    words = base.split()
    if any("." in w for w in words[:-1]):
        return False
    last_word = words[-1]
    if "." not in last_word:
        return False
    return last_word.rsplit(".", 1)[-1].lower() in _PATH_FILE_EXTENSIONS


def _rewrite_segment(segment: str) -> str:
    """Hyphenate ``speckit.*`` matches inside one unprotected segment."""
    if "speckit." not in segment:
        return segment
    return _SPECKIT_DOTTED_REF.sub(lambda m: m.group(0).replace(".", "-"), segment)


def _hyphenate_line(line: str) -> str:
    """Stream-normalize dotted ``speckit.*`` refs on one line with O(1) extra memory."""
    if "speckit." not in line:
        return line

    n = len(line)
    i = 0
    out: list[str] | None = None
    last_emitted = 0

    last_sep = -1
    last_sep_is_dir = False
    last_sep_explicit = False
    since_sep_valid = True
    since_sep_len = 0
    between_starts_speckit = False
    last_closed_bracket_end = -1
    last_closed_bracket_has_space = False
    last_closed_bracket_has_prefix = False
    last_env_var_end = -1
    no_more_quote = {"'": False, '"': False, "`": False}

    def emit_replacement(start: int, end: int, replacement: str) -> None:
        nonlocal out, last_emitted
        if out is None:
            out = []
        if start > last_emitted:
            out.append(line[last_emitted:start])
        out.append(replacement)
        last_emitted = end

    while i < n:
        ch = line[i]

        if ch in ('"', "'", "`"):
            if (
                not no_more_quote[ch]
                and not (ch == "'" and _is_contraction_apostrophe(line, i))
                and (i == 0 or line[i - 1] in _QUOTE_OPEN_BOUNDARY)
            ):
                close_idx = line.find(ch, i + 1)
                while (
                    close_idx >= 0
                    and ch == "'"
                    and _is_contraction_apostrophe(line, close_idx)
                ):
                    close_idx = line.find(ch, close_idx + 1)
                if close_idx < 0:
                    no_more_quote[ch] = True
                elif _is_standalone_path(line, i + 1, close_idx):
                    since_sep_valid = False
                    last_closed_bracket_end = -1
                    last_env_var_end = -1
                    i = close_idx + 1
                    continue
            since_sep_valid = False
            last_closed_bracket_end = -1
            last_env_var_end = -1
            if last_sep >= 0:
                if since_sep_len == 0:
                    between_starts_speckit = line.startswith("speckit.", last_sep + 1)
                since_sep_len += 1
            i += 1
            continue

        if ch in "/\\":
            is_dir = False
            if i >= 1:
                prev = line[i - 1]
                if _is_path_char(prev) or _is_drive_prefix(line, i):
                    is_dir = True
                elif (
                    last_closed_bracket_end == i - 1
                    and (not last_closed_bracket_has_space or last_closed_bracket_has_prefix)
                ):
                    is_dir = True
                elif last_env_var_end == i - 1:
                    is_dir = True
            last_sep = i
            last_sep_is_dir = is_dir
            last_sep_explicit = is_dir or (
                ch == "/" and (i == 0 or line[i - 1] in _SEP_LEADING_BOUNDARY)
            )
            since_sep_valid = True
            since_sep_len = 0
            between_starts_speckit = False
            last_closed_bracket_end = -1
            last_env_var_end = -1
            i += 1
            continue

        if _is_segment_char(ch) or (
            ch in ("(", "[") and _find_inline_bracket_end(line, i) >= 0
        ):
            seg_start = i
            seg_bracket_end = -1
            seg_bracket_has_space = False
            seg_bracket_has_prefix = False
            while i < n:
                cur = line[i]
                if _is_segment_char(cur):
                    if last_sep >= 0:
                        if since_sep_len == 0:
                            between_starts_speckit = line.startswith("speckit.", last_sep + 1)
                        since_sep_len += 1
                    i += 1
                elif cur in ("(", "["):
                    b_end = _find_inline_bracket_end(line, i)
                    if b_end < 0:
                        break
                    b_prefix = (i > 0 and _is_segment_char(line[i - 1])) or (
                        last_sep >= 0
                        and since_sep_valid
                        and since_sep_len > 0
                        and last_sep_explicit
                        and not (not last_sep_is_dir and between_starts_speckit)
                    )
                    b_space = any(c.isspace() for c in line[i + 1 : b_end])
                    b_has_non_space_ws = any(
                        c.isspace() and c != " " for c in line[i + 1 : b_end]
                    )
                    if b_has_non_space_ws:
                        since_sep_valid = False
                    if last_sep >= 0:
                        if since_sep_len == 0:
                            between_starts_speckit = line.startswith("speckit.", last_sep + 1)
                        since_sep_len += b_end - i + 1
                    seg_bracket_end = b_end
                    seg_bracket_has_space = b_space
                    seg_bracket_has_prefix = b_prefix
                    i = b_end + 1
                else:
                    break

            seg_end = i
            if seg_bracket_end == seg_end - 1:
                last_closed_bracket_end = seg_bracket_end
                last_closed_bracket_has_space = seg_bracket_has_space
                last_closed_bracket_has_prefix = seg_bracket_has_prefix
            else:
                last_closed_bracket_end = -1
            last_env_var_end = (
                seg_end - 1
                if line[seg_end - 1] == "%"
                and _is_valid_env_var_end(line, seg_start, seg_end)
                else -1
            )

            preceded_by_dir = seg_start >= 2 and line[seg_start - 1] in "/\\" and last_sep_is_dir
            followed_by_dir = False
            if seg_end < n and line[seg_end] in "/\\":
                end_ch = line[seg_end - 1]
                if end_ch == "%":
                    followed_by_dir = last_env_var_end == seg_end - 1
                elif _is_path_char(end_ch):
                    followed_by_dir = True
                elif seg_bracket_end == seg_end - 1 and (
                    not seg_bracket_has_space or seg_bracket_has_prefix
                ):
                    followed_by_dir = True
            if not (preceded_by_dir or followed_by_dir):
                seg = line[seg_start:seg_end]
                if "speckit." in seg:
                    rewritten = _rewrite_segment(seg)
                    if rewritten != seg:
                        emit_replacement(seg_start, seg_end, rewritten)
            continue

        if ch == " ":
            if last_sep >= 0:
                if since_sep_len == 0:
                    between_starts_speckit = line.startswith("speckit.", last_sep + 1)
                since_sep_len += 1
        else:
            since_sep_valid = False
        last_closed_bracket_end = -1
        last_env_var_end = -1
        i += 1

    if out is None:
        return line
    if last_emitted < n:
        out.append(line[last_emitted:])
    return "".join(out)


def hyphenate_command_refs(text: str) -> str:
    """Hyphenate dotted ``speckit.*`` command references in *text*.

    Streams line-by-line with O(1) extra state per line to preserve
    directory-qualified file names, script paths, dotted ancestor directories,
    bracketed path components, and same-line quoted paths containing spaces,
    while hyphenating bare, slash-prefixed, and punctuation-wrapped command
    references.
    """
    if "speckit." not in text:
        return text

    n = len(text)
    pos = 0
    out: list[str] | None = None
    last_emitted = 0

    while pos < n:
        nl = text.find("\n", pos)
        line_end = n if nl < 0 else nl + 1
        line = text[pos:line_end]
        if "speckit." in line:
            normalized = _hyphenate_line(line)
            if normalized != line:
                if out is None:
                    out = []
                if pos > last_emitted:
                    out.append(text[last_emitted:pos])
                out.append(normalized)
                last_emitted = line_end
        pos = line_end

    if out is None:
        return text
    if last_emitted < n:
        out.append(text[last_emitted:])
    return "".join(out)


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
        if _is_standalone_path(val, 0, len(val)):
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
