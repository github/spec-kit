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
    context_file = ".clinerules/specify-rules.md"
    invoke_separator = "-"
    multi_install_safe = True

    def command_filename(self, template_name: str) -> str:
        """Cline uses hyphenated filenames (e.g. speckit-git-commit.md)."""
        return format_cline_command_name(template_name) + ".md"

    def process_template(self, *args, **kwargs):
        """Ensure shared templates render Cline command references with hyphens."""
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
            eol = m.group(3)
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
            r"(?m)^(\s*agent:\s*)(speckit\.[a-z0-9.-]+)",
            lambda m: f"{m.group(1)}{format_cline_command_name(m.group(2))}",
            content,
        )

    def post_process_content(self, content: str) -> str:
        """Apply Cline-specific transformations to command content."""
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

            updated = self.post_process_content(content)

            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
                self.record_file_in_manifest(path, project_root, manifest)

        return created
