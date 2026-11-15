"""Cline IDE integration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration
from ..manifest import IntegrationManifest


# Note injected into hook sections so Cline maps dot-notation command
# names (from extensions.yml) to the hyphenated slash commands it uses.
_HOOK_COMMAND_NOTE = (
    "- When constructing slash commands from hook command names, "
    "replace dots (`.`) with hyphens (`-`). "
    "For example, `speckit.git.commit` → `/speckit-git-commit`.\n"
)


def format_cline_command_name(cmd_name: str) -> str:
    """Convert command name to Cline-compatible hyphenated format.

    Cline handles slash-commands optimally when they use hyphens instead of dots.
    This function converts dot-notation command names to hyphenated format.

    The function is idempotent: already-formatted names are returned unchanged.

    Examples:
        >>> format_cline_command_name("plan")
        'speckit-plan'
        >>> format_cline_command_name("speckit.plan")
        'speckit-plan'
        >>> format_cline_command_name("speckit.git.commit")
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
    return ch.isalnum() or ch in "._-~/\\}$"


# A ``%VAR%`` environment variable reference ending a directory name
# (``%TEMP%``, ``%ProgramFiles(x86)%``).
_ENV_VAR_DIR = re.compile(r"%[A-Za-z_][A-Za-z0-9_()]*%\Z")

_BRACKET_OPENERS = {")": "(", "]": "["}


def _ends_directory(text: str, sep: int) -> bool:
    """Whether the text before the separator at *sep* ends a directory name.

    Besides plain path-name characters this accepts a closing bracket that
    closes a whitespace-free group (``Program Files (x86)``,
    ``commands[old]``) and a ``%VAR%`` environment variable reference
    (``%TEMP%``).  An opening bracket, or a closing one around prose such as
    ``(see docs)``, does not end a directory, so ``[/speckit.foo.md]`` and
    ``(/speckit.foo.md)`` stay command references.
    """
    ch = text[sep - 1]
    if _is_path_char(ch):
        return True
    if ch in _BRACKET_OPENERS:
        opener = text.rfind(_BRACKET_OPENERS[ch], 0, sep - 1)
        group = text[opener + 1 : sep - 1]
        return (
            opener >= 0
            and bool(group)
            and ch not in group
            and not any(c.isspace() for c in group)
        )
    if ch == "%":
        return _ENV_VAR_DIR.search(text, 0, sep) is not None
    return False


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


def _hyphenate_ref_match(match: re.Match[str]) -> str:
    """Hyphenate one dotted speckit reference, leaving ``.md`` file names alone.

    Command names may themselves end in an ``md`` segment: extension
    commands are ``speckit.<extension>.<command>`` and preset command names
    may contain further dots, so ``/speckit.foo.md`` and
    ``speckit.foo.bar.md`` can both be valid command references.  The
    ``.md`` suffix and the segment count therefore cannot tell a file name
    apart from a command.  A ``.md`` token is kept as a file name only when
    it sits inside a path (``commands/speckit.git.commit.md``), that is,
    when the separator before it ends a directory name (see
    ``_ends_directory``: ``commands/``, ``C:\\Program Files (x86)\\``,
    ``%TEMP%\\``, ``commands[old]/``) or follows a Windows drive
    (``C:\\speckit.foo.md``, ``C:/speckit.foo.md``).  A bare or
    slash-prefixed token is treated as a command reference, including after
    an opening bracket or other punctuation (``[/speckit.foo.md]``,
    ``(/speckit.foo.md)``).
    """
    ref = match.group(0)
    if ref.endswith(".md"):
        start = match.start()
        text = match.string
        if start >= 2 and text[start - 1] in "/\\" and (
            _ends_directory(text, start - 1) or _is_drive_prefix(text, start - 1)
        ):
            return ref
    return ref.replace(".", "-")


def hyphenate_command_refs(text: str) -> str:
    """Hyphenate dotted ``speckit.*`` command references in *text*."""
    return _SPECKIT_DOTTED_REF.sub(_hyphenate_ref_match, text)


def _hyphenate_frontmatter_refs(val: Any) -> Any:
    """Recursively hyphenate dotted ``speckit.*`` references in frontmatter values."""
    if isinstance(val, dict):
        return {k: _hyphenate_frontmatter_refs(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_hyphenate_frontmatter_refs(x) for x in val]
    if isinstance(val, str):
        return hyphenate_command_refs(val)
    return val


class ClineIntegration(MarkdownIntegration):
    """Integration for Cline IDE."""

    key = "cline"
    config = {
        "name": "Cline",
        "folder": ".clinerules/",
        "commands_subdir": "workflows",
        "install_url": "https://github.com/cline/cline",
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".clinerules/workflows",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
        "inject_name": True,
        "format_name": format_cline_command_name,
        "invoke_separator": "-",
    }
    invoke_separator = "-"
    multi_install_safe = True

    def command_filename(self, template_name: str) -> str:
        """Cline uses hyphenated filenames (e.g. speckit-git-commit.md)."""
        return format_cline_command_name(template_name) + ".md"

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Cline installs hyphenated slash-commands (``/speckit-<name>``), so the
        dispatch invocation must match. The inherited MarkdownIntegration default
        builds the dotted ``/speckit.<name>``, which references a command Cline
        never registered. Reuse the same hyphenation as command_filename /
        the injected frontmatter name (see ``format_cline_command_name``),
        mirroring the forge integration.
        """
        invocation = "/" + format_cline_command_name(command_name)
        if args:
            invocation = f"{invocation} {args}"
        return invocation

    def process_template(self, *args, **kwargs):
        """Ensure shared templates render Cline command references with hyphens."""
        kwargs.setdefault("invoke_separator", self.invoke_separator)
        return super().process_template(*args, **kwargs)

    @staticmethod
    def _inject_hook_command_note(content: str) -> str:
        """Insert a dot-to-hyphen note before each hook output instruction.

        Targets the line ``- For each executable hook, output the following``
        and inserts the note on the line before it, matching its indentation.
        Skips individual instructions that already have the note immediately
        above them.
        """
        note = _HOOK_COMMAND_NOTE.rstrip("\n")

        def repl(m: re.Match[str]) -> str:
            indent = m.group(1)
            instruction = m.group(2)
            # Check the line immediately above this instruction, mirroring the
            # shared ``SkillsIntegration`` helper. The previous whole-document
            # ``if "replace dots" in content`` scan meant any command or
            # extension markdown whose prose merely contained that phrase lost
            # the note entirely -- leaving the agent told to emit a dotted
            # ``/speckit.git.commit``, which Cline never registers -- and a
            # document with one already-noted section never got a note on a
            # second, un-noted one.
            previous_lines = content[:m.start()].splitlines()
            if previous_lines and previous_lines[-1] == indent + note:
                return m.group(0)
            # ``eol`` is empty when the regex matched via ``$`` because the
            # instruction was the final line of a file with no trailing
            # newline. Default to ``\n`` so the note never collapses onto
            # the same line as the instruction.
            eol = m.group(3) or "\n"
            return (
                indent
                + note
                + eol
                + indent
                + instruction
                + eol
            )

        # ``[ \t]*`` rather than ``\s*``: ``\s`` matches newlines, so the
        # captured "indent" could swallow a preceding blank line and the note
        # was then emitted with a spurious blank line between it and the
        # instruction. This also matches the shared base helper, without which
        # the per-instruction check above cannot line up.
        return re.sub(
            r"(?m)^([ \t]*)(- For each executable hook, output the following[^\r\n]*)(\r\n|\n|$)",
            repl,
            content,
        )

    @staticmethod
    def _rewrite_handoff_references(content: str) -> str:
        """Replace dot-notation agent references in handoffs with hyphens."""
        return re.sub(
            r"(?m)^(\s*agent:\s*)(speckit\.[A-Za-z0-9-_]+(?:\.[A-Za-z0-9-_]+)*)",
            lambda m: f"{m.group(1)}{format_cline_command_name(m.group(2))}",
            content,
        )

    def process_registered_command(
        self, frontmatter: dict[str, Any], body: str, *, source_id: str
    ) -> tuple[dict[str, Any], str]:
        """Hyphenate dotted command references in extension and preset commands.

        Cline only registers hyphenated slash commands, so references such as
        ``/speckit.git.commit`` in extension and preset command content are
        rewritten to ``/speckit-git-commit``.  ``speckit.*.md`` file names
        inside a path keep their extension.  Core commands (``source_id ==
        "core"``) are left unchanged; their references are rendered through
        ``invoke_separator`` instead.
        """
        if source_id == "core":
            return frontmatter, body
        return _hyphenate_frontmatter_refs(frontmatter), hyphenate_command_refs(body)

    def post_process_command_content(self, content: str) -> str:
        """Apply Cline-specific transformations to command content.

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
        """Install Cline commands and apply post-processing transformations."""
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
