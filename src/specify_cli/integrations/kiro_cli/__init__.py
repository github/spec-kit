"""Kiro CLI integration."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import _HOOK_COMMAND_NOTE, MarkdownIntegration
from ..manifest import IntegrationManifest


# Kiro CLI file-based prompts do NOT support any argument-substitution syntax,
# so a raw "$ARGUMENTS" token would reach the model verbatim and break the
# prompt (issue #1926, kirodotdev/Kiro#4141). Use a prose fallback so the
# rendered prompt instructs the model to take its argument from the user's
# next message.
_KIRO_ARG_FALLBACK = "(the user will provide the argument in this conversation)"


def format_kiro_command_name(cmd_name: str) -> str:
    """Convert a command name to the hyphenated form Kiro CLI can invoke.

    Kiro CLI runs ``/name`` from ``.kiro/prompts/name.md`` only when the name
    has no dots: ``/speckit.plan`` is rejected as an unrecognized slash
    command, while ``/speckit-plan`` runs the prompt (issue #4797).

    The function is idempotent: already-formatted names are returned unchanged.

    Examples:
        >>> format_kiro_command_name("plan")
        'speckit-plan'
        >>> format_kiro_command_name("speckit.plan")
        'speckit-plan'
        >>> format_kiro_command_name("speckit.git.commit")
        'speckit-git-commit'
    """
    cmd_name = cmd_name.replace(".", "-")

    if not cmd_name.startswith("speckit-"):
        cmd_name = f"speckit-{cmd_name}"

    return cmd_name


class KiroCliIntegration(MarkdownIntegration):
    key = "kiro-cli"
    # Kiro CLI keeps everything under a static, isolated agent root
    # (``.kiro/`` with commands in ``.kiro/prompts``) that no other
    # integration writes to, so it is safe to install alongside others
    # (issue #3471). IntegrationBase defaults this to False; declaring it
    # True here is the actual behavior change this integration opts into.
    # The registry's multi-install-safe contract tests enforce that
    # isolation for every integration setting this flag.
    multi_install_safe = True
    config = {
        "name": "Kiro CLI",
        "folder": ".kiro/",
        "commands_subdir": "prompts",
        "install_url": "https://kiro.dev/docs/cli/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".kiro/prompts",
        "format": "markdown",
        "args": _KIRO_ARG_FALLBACK,
        "extension": ".md",
        "format_name": format_kiro_command_name,
        "invoke_separator": "-",
    }
    invoke_separator = "-"
    # Prompts used to be named after the dotted command
    # (``.kiro/prompts/speckit.<cmd>.md``), which Kiro CLI cannot invoke.
    # ``integration upgrade`` stale-removes the core ones through the
    # manifest; ExtensionManager retires an extension's dotted prompt once
    # registration writes its hyphenated replacement (#4797).
    legacy_flat_command_dir = ".kiro/prompts"
    legacy_flat_command_extension = ".md"

    def command_filename(self, template_name: str) -> str:
        return format_kiro_command_name(template_name) + ".md"

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Kiro CLI installs hyphenated prompts (``/speckit-<name>``), so the
        dispatch invocation must match; the inherited dotted ``/speckit.<name>``
        is not a slash command Kiro recognizes.
        """
        invocation = "/" + format_kiro_command_name(command_name)
        if args:
            invocation = f"{invocation} {args}"
        return invocation

    def process_template(self, *args, **kwargs):
        """Ensure shared templates render Kiro command references with hyphens."""
        kwargs.setdefault("invoke_separator", self.invoke_separator)
        return super().process_template(*args, **kwargs)

    @staticmethod
    def _inject_hook_command_note(content: str) -> str:
        """Insert a dot-to-hyphen note before each hook output instruction.

        Hook command names come from ``extensions.yml`` in dot notation, so
        the model needs the mapping to the hyphenated prompt names. Skips
        instructions that already have the note immediately above them (the
        per-instruction check from the Cline fix in #4150).
        """
        note = _HOOK_COMMAND_NOTE.rstrip("\n")

        def repl(m: re.Match[str]) -> str:
            indent = m.group(1)
            instruction = m.group(2)
            previous_lines = content[:m.start()].splitlines()
            if previous_lines and previous_lines[-1] == indent + note:
                return m.group(0)
            # ``eol`` is empty when the instruction is the final line of a
            # file with no trailing newline.
            eol = m.group(3) or "\n"
            return indent + note + eol + indent + instruction + eol

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
            lambda m: f"{m.group(1)}{format_kiro_command_name(m.group(2))}",
            content,
        )

    def post_process_command_content(self, content: str) -> str:
        """Apply the hook note and handoff rewrite to Kiro prompt content.

        ``CommandRegistrar.register_commands()`` calls this hook too, so
        extension and preset prompts get the same transforms as core ones.
        """
        return self._rewrite_handoff_references(self._inject_hook_command_note(content))

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install Kiro prompts and apply post-processing transformations."""
        created = super().setup(project_root, manifest, parsed_options, **opts)

        dest_dir = self.commands_dest(project_root).resolve()
        for path in created:
            try:
                path.resolve().relative_to(dest_dir)
            except ValueError:
                continue
            if path.suffix != ".md":
                continue

            content = path.read_bytes().decode("utf-8")
            updated = self.post_process_command_content(content)
            if updated != content:
                path.write_bytes(updated.encode("utf-8"))
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
        """Build CLI arguments for headless ``kiro-cli chat`` execution.

        The inherited ``kiro-cli -p <prompt>`` exits 2 at argument parsing
        (``unexpected argument '-p'``). Kiro CLI runs one prompt headless
        through ``chat --no-interactive`` with the prompt as its positional
        input, and a ``/speckit-*`` input there runs the matching
        ``.kiro/prompts`` file. Headless mode cannot ask for tool approval, so
        without ``--trust-all-tools`` every file write is denied while the run
        still exits 0 (same role as Copilot's ``--yolo`` / Cursor's
        ``--force``). Kiro has no ``json`` output format; its structured output
        is ``--output-format stream-json`` (JSON Lines).
        """
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "chat", "--no-interactive", "--trust-all-tools"]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "stream-json"])
        args.append(prompt)
        return args
