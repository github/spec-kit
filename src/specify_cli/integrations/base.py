"""Base classes for AI-assistant integrations.

Provides:
- ``IntegrationOption`` — declares a CLI option an integration accepts.
- ``IntegrationBase`` — abstract base every integration must implement.
- ``MarkdownIntegration`` — concrete base for standard Markdown-format
  integrations (the common case — subclass, set three class attrs, done).
- ``TomlIntegration`` — concrete base for TOML-format integrations
  (Gemini, Tabnine — subclass, set three class attrs, done).
- ``SkillsIntegration`` — concrete base for integrations that install
  commands as agent skills (``speckit-<name>/SKILL.md`` layout).
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from .._toml_string import escape_toml_basic as _escape_toml_basic
from .._toml_string import has_illegal_toml_control as _has_illegal_toml_control

if TYPE_CHECKING:
    from .manifest import IntegrationManifest

_HOOK_COMMAND_NOTE = (
    "- When constructing slash commands from hook command names, "
    "replace dots (`.`) with hyphens (`-`). "
    "For example, `speckit.git.commit` → `/speckit-git-commit`.\n"
)

_CORE_COMMAND_TEMPLATE_ORDER = (
    "analyze",
    "clarify",
    "constitution",
    "implement",
    "converge",
    "plan",
    "checklist",
    "specify",
    "tasks",
    "taskstoissues",
)
_CORE_COMMAND_TEMPLATE_RANK = {
    command: index for index, command in enumerate(_CORE_COMMAND_TEMPLATE_ORDER)
}


def yaml_quote(value: str) -> str:
    """Emit *value* as a double-quoted YAML scalar on a single line.

    A hand-rolled quote cannot carry raw newlines (YAML folds them to
    spaces) or control characters (the reader rejects them), so let the
    YAML emitter produce the escapes.
    """
    return yaml.safe_dump(
        str(value), default_style='"', allow_unicode=True, width=sys.maxsize
    ).strip()


# ---------------------------------------------------------------------------
# IntegrationOption
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegrationOption:
    """Declares an option that an integration accepts via ``--integration-options``.

    Attributes:
        name:      The flag name (e.g. ``"--commands-dir"``).
        is_flag:   ``True`` for boolean flags (``--skills``).
        required:  ``True`` if the option must be supplied.
        default:   Default value when not supplied (``None`` → no default).
        help:      One-line description shown in ``specify integrate info``.
    """

    name: str
    is_flag: bool = False
    required: bool = False
    default: Any = None
    help: str = ""


# ---------------------------------------------------------------------------
# IntegrationBase — abstract base class
# ---------------------------------------------------------------------------


class IntegrationBase(ABC):
    """Abstract base class every integration must implement.

    Subclasses must set the following class-level attributes:

    * ``key``              — unique identifier, matches actual CLI tool name
    * ``config``           — dict compatible with ``AGENT_CONFIG`` entries
    * ``registrar_config`` — dict compatible with ``CommandRegistrar.AGENT_CONFIGS``

    And may optionally set:

    * ``invoke_separator`` — slash-command separator (defaults to ``"."``)
    * ``multi_install_safe`` — declare the integration safe to install
      alongside others (defaults to ``False``)
    """

    # -- Must be set by every subclass ------------------------------------

    key: str = ""
    """Unique integration key — should match the actual CLI tool name."""

    config: dict[str, Any] | None = None
    """Metadata dict matching the ``AGENT_CONFIG`` shape."""

    registrar_config: dict[str, Any] | None = None
    """Registration dict matching ``CommandRegistrar.AGENT_CONFIGS`` shape."""

    # -- Optional ---------------------------------------------------------

    invoke_separator: str = "."
    """Separator used in slash-command invocations (``"."`` → ``/speckit.plan``)."""

    dev_no_symlink: bool = False
    """Whether dev-mode registration should write files instead of symlinks."""

    multi_install_safe: bool = False
    """Whether this integration is declared safe to install alongside others.

    Safe integrations must use a static, unique agent root and command
    directory. Registry tests enforce those invariants for every
    integration that sets this flag.
    """

    def post_process_command_content(self, content: str) -> str:
        """Transform command content after format rendering.

        Called by ``register_commands()`` for non-skills format types
        (Markdown, TOML, YAML) after the command has been rendered into
        its target format and before writing to disk.  Skills-format
        agents use ``post_process_skill_content()`` instead.

        Subclasses may override to inject agent-specific content.
        The default implementation returns *content* unchanged.
        """
        return content

    # -- Public API -------------------------------------------------------

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        """Return options this integration accepts. Default: none."""
        return []

    def effective_invoke_separator(
        self, parsed_options: dict[str, Any] | None = None
    ) -> str:
        """Return the invoke separator for the given options.

        Subclasses whose separator depends on runtime options (e.g.
        Copilot in ``--skills`` mode) should override this method.
        The default implementation ignores *parsed_options* and returns
        the class-level ``invoke_separator``.
        """
        return self.invoke_separator

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build CLI arguments for non-interactive execution.

        Returns a list of command-line tokens that will execute *prompt*
        non-interactively using this integration's CLI tool, or ``None``
        if the integration does not support CLI dispatch.

        Subclasses for CLI-based integrations should override this.
        """
        return None

    def _resolve_executable(self) -> str:
        """Return the executable for this integration's CLI tool.

        Checks ``SPECKIT_INTEGRATION_<KEY>_EXECUTABLE`` first, allowing
        operators to override the binary path without modifying the
        integration configuration — useful when the tool is installed in
        a non-standard location or a specific version must be pinned.
        Hyphens in the integration key are replaced with underscores and
        the key is uppercased so that, for example, ``kiro-cli`` maps to
        ``SPECKIT_INTEGRATION_KIRO_CLI_EXECUTABLE``.

        Falls back to ``self.key`` when the env var is unset or
        whitespace-only so existing behaviour is unchanged.

        See issue #2596.
        """
        env_name = (
            f"SPECKIT_INTEGRATION_{self.key.upper().replace('-', '_')}_EXECUTABLE"
        )
        override = os.environ.get(env_name, "").strip()
        return override if override else self.key

    def _apply_extra_args_env_var(self, args: list[str]) -> None:
        """Append `SPECKIT_INTEGRATION_<KEY>_EXTRA_ARGS` env-var value to *args*.

        Operators can inject extra CLI flags into the spawned agent
        subprocess by setting an env var named for the integration key,
        e.g. `SPECKIT_INTEGRATION_CLAUDE_EXTRA_ARGS="--dangerously-skip-permissions"`.
        The `INTEGRATION` segment scopes the variable to this subsystem
        so it does not collide with other Spec Kit env-var namespaces.
        Hyphens in the integration key are replaced with underscores
        and the key is uppercased
        (e.g. `kiro-cli` → `SPECKIT_INTEGRATION_KIRO_CLI_EXTRA_ARGS`).

        Useful in CI / non-interactive contexts where the spawned agent
        needs flags that change its prompt-handling behaviour.
        Default behaviour (env var unset or whitespace-only) is a no-op
        — *args* is unchanged. Multi-token values are parsed via
        `shlex.split`.

        See issue #2595.
        """
        env_name = (
            f"SPECKIT_INTEGRATION_{self.key.upper().replace('-', '_')}_EXTRA_ARGS"
        )
        extra = os.environ.get(env_name, "").strip()
        if not extra:
            return
        try:
            tokens = shlex.split(extra)
        except ValueError as exc:
            raise ValueError(
                f"{env_name} is not parseable as a POSIX-quoted command line "
                f"(value: {extra!r}). shlex reported: {exc}. "
                f"Use single or double quotes to group multi-word values, e.g. "
                f'{env_name}=\'--flag "value with spaces"\'.'
            ) from exc
        args.extend(tokens)

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Build the native slash-command invocation for a Spec Kit command.

        The CLI tools discover and execute commands from installed files
        on disk.  This method builds the invocation string the CLI
        expects — e.g. ``"/speckit.specify my-feature"`` for markdown
        agents or ``"/speckit-specify my-feature"`` for skills agents.

        *command_name* may be a full dotted name like
        ``"speckit.specify"``, an extension command like
        ``"speckit.git.commit"``, or a bare stem like ``"specify"``.
        """
        stem = command_name
        if stem.startswith("speckit."):
            stem = stem[len("speckit."):]

        invocation = f"/speckit.{stem}"
        if args:
            invocation = f"{invocation} {args}"
        return invocation

    def dispatch_command(
        self,
        command_name: str,
        args: str = "",
        *,
        project_root: Path | None = None,
        model: str | None = None,
        timeout: int = 600,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Dispatch a Spec Kit command through this integration's CLI.

        By default this builds a slash-command invocation with
        ``build_command_invocation()`` and passes that prompt to
        ``build_exec_args()`` to construct the CLI command line.
        Integrations with custom dispatch behavior can override
        ``build_command_invocation()``, ``build_exec_args()``, or
        ``dispatch_command()`` directly.

        When *stream* is ``True`` (the default), stdout and stderr are
        piped directly to the terminal so the user sees live output.
        When ``False``, output is captured and returned in the dict.

        Returns a dict with ``exit_code``, ``stdout``, and ``stderr``.
        Raises ``NotImplementedError`` if the integration does not
        support CLI dispatch.
        """
        import subprocess

        prompt = self.build_command_invocation(command_name, args)
        # When streaming to the terminal, request text output so the
        # user sees readable output instead of raw JSONL events.
        exec_args = self.build_exec_args(
            prompt, model=model, output_json=not stream
        )

        if exec_args is None:
            msg = (
                f"Integration {self.key!r} does not support CLI dispatch. "
                f"Override build_exec_args() to enable it."
            )
            raise NotImplementedError(msg)

        # Windows: ``subprocess.run`` calls ``CreateProcess`` which does not
        # consult ``PATHEXT``, so a bare command name like ``cursor-agent``
        # that resolves to ``cursor-agent.cmd`` fails with ``WinError 2``.
        # Resolve via ``shutil.which`` (which does honor ``PATHEXT``) so
        # ``.cmd``/``.bat`` shims work transparently.  On POSIX this is a
        # no-op for absolute paths and a harmless lookup otherwise.
        resolved = shutil.which(exec_args[0])
        if resolved:
            exec_args = [resolved, *exec_args[1:]]

        cwd = str(project_root) if project_root else None

        if stream:
            # No timeout when streaming — the user sees live output and
            # can Ctrl+C at any time.  The timeout parameter is only
            # applied in the captured (non-streaming) branch below.
            try:
                result = subprocess.run(
                    exec_args,
                    text=True,
                    cwd=cwd,
                )
            except KeyboardInterrupt:
                return {
                    "exit_code": 130,
                    "stdout": "",
                    "stderr": "Interrupted by user",
                }
            return {
                "exit_code": result.returncode,
                "stdout": "",
                "stderr": "",
            }

        result = subprocess.run(
            exec_args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    # -- Primitives — building blocks for setup() -------------------------

    def shared_commands_dir(self) -> Path | None:
        """Return path to the shared command templates directory.

        Checks ``core_pack/commands/`` (wheel install) first, then
        ``templates/commands/`` (source checkout).  Returns ``None``
        if neither exists.
        """
        import inspect

        pkg_dir = Path(inspect.getfile(IntegrationBase)).resolve().parent.parent
        for candidate in [
            pkg_dir / "core_pack" / "commands",
            pkg_dir.parent.parent / "templates" / "commands",
        ]:
            if candidate.is_dir():
                return candidate
        return None

    def shared_templates_dir(self) -> Path | None:
        """Return path to the shared page templates directory.

        Contains ``vscode-settings.json``, ``spec-template.md``, etc.
        Checks ``core_pack/templates/`` then ``templates/``.
        """
        import inspect

        pkg_dir = Path(inspect.getfile(IntegrationBase)).resolve().parent.parent
        for candidate in [
            pkg_dir / "core_pack" / "templates",
            pkg_dir.parent.parent / "templates",
        ]:
            if candidate.is_dir():
                return candidate
        return None

    def list_command_templates(self) -> list[Path]:
        """Return ordered list of command template files from the shared directory."""
        cmd_dir = self.shared_commands_dir()
        if not cmd_dir or not cmd_dir.is_dir():
            return []
        return sorted(
            (f for f in cmd_dir.iterdir() if f.is_file() and f.suffix == ".md"),
            key=lambda f: (
                _CORE_COMMAND_TEMPLATE_RANK.get(
                    f.stem, len(_CORE_COMMAND_TEMPLATE_ORDER)
                ),
                f.name,
            ),
        )

    def command_filename(self, template_name: str) -> str:
        """Return the destination filename for a command template.

        *template_name* is the stem of the source file (e.g. ``"plan"``).
        Default: ``speckit.{template_name}.md``.  Subclasses override
        to change the extension or naming convention.
        """
        return f"speckit.{template_name}.md"

    def stale_cleanup_exclusions(self) -> set[str]:
        """Return project-relative paths that upgrade must never stale-delete.

        During ``integration upgrade``, files recorded in a previous manifest
        but absent from the freshly written one are treated as stale and
        removed.  Conditionally-tracked files (e.g. a settings file that the
        integration merges into when it already exists, and therefore stops
        tracking) would otherwise be deleted even though they are still
        managed.  Subclasses list such paths here to protect them.
        """
        return set()

    def commands_dest(self, project_root: Path) -> Path:
        """Return the absolute path to the commands output directory.

        Derived from ``config["folder"]`` and ``config["commands_subdir"]``.
        Raises ``ValueError`` if ``config`` or ``folder`` is missing.
        """
        if not self.config:
            raise ValueError(
                f"{type(self).__name__}.config is not set; integration "
                "subclasses must define a non-empty 'config' mapping."
            )
        folder = self.config.get("folder")
        if not folder:
            raise ValueError(
                f"{type(self).__name__}.config is missing required 'folder' entry."
            )
        subdir = self.config.get("commands_subdir", "commands")
        return project_root / folder / subdir

    # -- File operations — granular primitives for setup() ----------------

    @staticmethod
    def copy_command_to_directory(
        src: Path,
        dest_dir: Path,
        filename: str,
    ) -> Path:
        """Copy a command template to *dest_dir* with the given *filename*.

        Creates *dest_dir* if needed.  Returns the absolute path of the
        written file.  The caller can post-process the file before
        recording it in the manifest.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        dst = dest_dir / filename
        shutil.copy2(src, dst)
        return dst

    @staticmethod
    def record_file_in_manifest(
        file_path: Path,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> None:
        """Hash *file_path* and record it in *manifest*.

        *file_path* must be inside *project_root*.
        """
        rel = file_path.resolve().relative_to(project_root.resolve())
        manifest.record_existing(rel)

    @staticmethod
    def write_file_and_record(
        content: str,
        dest: Path,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> Path:
        """Write *content* to *dest*, hash it, and record in *manifest*.

        Creates parent directories as needed.  Writes bytes directly to
        avoid platform newline translation (CRLF on Windows).  Any
        ``\r\n`` sequences in *content* are normalised to ``\n`` before
        writing.  Returns *dest*.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        normalized = content.replace("\r\n", "\n")
        dest.write_bytes(normalized.encode("utf-8"))
        rel = dest.resolve().relative_to(project_root.resolve())
        manifest.record_existing(rel)
        return dest

    def integration_scripts_dir(self) -> Path | None:
        """Return path to this integration's bundled ``scripts/`` directory.

        Looks for a ``scripts/`` sibling of the module that defines the
        concrete subclass (not ``IntegrationBase`` itself).
        Returns ``None`` if the directory doesn't exist.
        """
        import inspect

        cls_file = inspect.getfile(type(self))
        scripts = Path(cls_file).resolve().parent / "scripts"
        return scripts if scripts.is_dir() else None

    def install_scripts(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
    ) -> list[Path]:
        """Copy integration-specific scripts into the project.

        Copies files from this integration's ``scripts/`` directory to
        ``.specify/integrations/<key>/scripts/`` in the project.  Shell
        (``.sh``) and Python (``.py``) scripts are made executable.  All
        copied files are recorded in *manifest*.

        Returns the list of files created.
        """
        scripts_src = self.integration_scripts_dir()
        if not scripts_src:
            return []

        created: list[Path] = []
        scripts_dest = project_root / ".specify" / "integrations" / self.key / "scripts"
        scripts_dest.mkdir(parents=True, exist_ok=True)

        for src_script in sorted(scripts_src.iterdir()):
            if not src_script.is_file():
                continue
            dst_script = scripts_dest / src_script.name
            shutil.copy2(src_script, dst_script)
            if dst_script.suffix in (".sh", ".py"):
                dst_script.chmod(dst_script.stat().st_mode | 0o111)
            self.record_file_in_manifest(dst_script, project_root, manifest)
            created.append(dst_script)

        return created

    @staticmethod
    def resolve_command_refs(content: str, separator: str = ".") -> str:
        """Replace ``__SPECKIT_COMMAND_<NAME>__`` placeholders with invocations.

        Each placeholder encodes a command name in upper-case with
        underscores (e.g. ``__SPECKIT_COMMAND_PLAN__``,
        ``__SPECKIT_COMMAND_GIT_COMMIT__``).  The replacement uses
        *separator* to join the segments:

        * ``separator="."`` → ``/speckit.plan``, ``/speckit.git.commit``
        * ``separator="-"`` → ``/speckit-plan``, ``/speckit-git-commit``
        """
        return re.sub(
            r"__SPECKIT_COMMAND_([A-Z][A-Z0-9_]*)__",
            lambda m: "/speckit" + separator + m.group(1).lower().replace("_", separator),
            content,
        )

    @staticmethod
    def resolve_python_interpreter(project_root: Path | None = None) -> str:
        """Resolve a portable Python interpreter command for ``{SCRIPT}``.

        Used to build the invocation string for the ``py`` script type so
        that ``.py`` workflow scripts run consistently across platforms
        (notably Windows, where ``.py`` files are not directly executable).

        Resolution order:

        1. A project virtual environment (``.venv``) interpreter, if one
           exists under *project_root* (POSIX ``bin/python`` or Windows
           ``Scripts/python.exe``).  The returned path is **relative to the
           project root** (e.g. ``.venv/bin/python``) so generated
           ``{SCRIPT}`` invocations stay portable and runnable from the
           repo root regardless of where the project lives.
        2. ``python3`` on ``PATH``.
        3. ``python`` on ``PATH``.

        Falls back to the running interpreter (``sys.executable``) when
        ``PATH`` resolution fails so the generated command is guaranteed
        to work in the current environment, and finally to ``"python3"``
        if even that is unavailable.
        """
        if project_root is not None:
            # (existence check path, repo-root-relative invocation string)
            venv_candidates = (
                (project_root / ".venv" / "bin" / "python", ".venv/bin/python"),
                (
                    project_root / ".venv" / "Scripts" / "python.exe",
                    ".venv/Scripts/python.exe",
                ),
            )
            for candidate, relative in venv_candidates:
                if candidate.exists():
                    return relative
        for name in ("python3", "python"):
            found = shutil.which(name)
            if not found:
                continue
            # On Windows, python3/python on PATH may be the Microsoft
            # Store App Execution Alias stub: it exists but only prints
            # an installer hint and exits non-zero, so existence is not
            # enough (see #3304 for the same defect in the sh scripts).
            if sys.platform == "win32" and not IntegrationBase._interpreter_runs(
                found
            ):
                continue
            return name
        return sys.executable or "python3"

    @staticmethod
    def _interpreter_runs(path: str) -> bool:
        """Return True when *path* executes as a Python interpreter.

        Runs isolated (``-I``) without ``site`` (``-S``) and discards
        I/O so the probe is a fast liveness check that cannot trigger
        ``sitecustomize``/user startup hooks.
        """
        try:
            return (
                subprocess.run(
                    [path, "-I", "-S", "-c", ""],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                ).returncode
                == 0
            )
        except (OSError, subprocess.SubprocessError):
            return False

    @staticmethod
    def process_template(
        content: str,
        agent_name: str,
        script_type: str,
        arg_placeholder: str = "$ARGUMENTS",
        invoke_separator: str = ".",
        project_root: Path | None = None,
    ) -> str:
        """Process a raw command template into agent-ready content.

        Performs the same transformations as the release script:
        1. Extract ``scripts.<script_type>`` value from YAML frontmatter
        2. Replace ``{SCRIPT}`` with the extracted script command
        3. Strip ``scripts:`` section from frontmatter
        4. Replace ``{ARGS}`` and ``$ARGUMENTS`` with *arg_placeholder*
        5. Replace ``__AGENT__`` with *agent_name*
        6. Rewrite paths: ``scripts/`` → ``.specify/scripts/`` etc.
        7. Replace ``__SPECKIT_COMMAND_<NAME>__`` with invocation strings
        """
        # 1. Extract script command from frontmatter
        script_command = ""
        script_pattern = re.compile(
            rf"^\s*{re.escape(script_type)}:\s*(.+)$", re.MULTILINE
        )
        # Find the scripts: block
        in_scripts = False
        for line in content.splitlines():
            if line.strip() == "scripts:":
                in_scripts = True
                continue
            if in_scripts and line and not line[0].isspace():
                in_scripts = False
            if in_scripts:
                m = script_pattern.match(line)
                if m:
                    script_command = m.group(1).strip()
                    break

        # 2. Replace {SCRIPT}
        if script_command:
            # For the Python script type, prefix the resolved interpreter so
            # the command is portable (``.py`` files are not directly
            # executable on Windows).
            if script_type == "py":
                interpreter = IntegrationBase.resolve_python_interpreter(project_root)
                # Quote the interpreter if it contains whitespace (e.g. an
                # absolute ``sys.executable`` path under Windows
                # ``Program Files``) so it isn't split into multiple args.
                if any(ch.isspace() for ch in interpreter):
                    interpreter = f'"{interpreter}"'
                script_command = f"{interpreter} {script_command}"
            content = content.replace("{SCRIPT}", script_command)

        # 3. Strip scripts: section from frontmatter
        lines = content.splitlines(keepends=True)
        output_lines: list[str] = []
        in_frontmatter = False
        skip_section = False
        dash_count = 0
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 1:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                skip_section = False
                output_lines.append(line)
                continue
            if in_frontmatter:
                if stripped == "scripts:":
                    skip_section = True
                    continue
                if skip_section:
                    if line[0:1].isspace():
                        continue  # skip indented content under scripts
                    skip_section = False
            output_lines.append(line)
        content = "".join(output_lines)

        # 4. Replace {ARGS} and $ARGUMENTS
        content = content.replace("{ARGS}", arg_placeholder)
        content = content.replace("$ARGUMENTS", arg_placeholder)

        # 5. Replace __AGENT__
        content = content.replace("__AGENT__", agent_name)

        # 6. Rewrite paths — delegate to the shared implementation in
        #    CommandRegistrar so extension-local paths are preserved and
        #    boundary rules stay consistent across the codebase.
        from specify_cli.agents import CommandRegistrar

        content = CommandRegistrar.rewrite_project_relative_paths(content)

        # 8. Replace __SPECKIT_COMMAND_<NAME>__ with invocation strings
        content = IntegrationBase.resolve_command_refs(content, invoke_separator)

        return content

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install integration command files into *project_root*.

        Returns the list of files created.  Copies raw templates without
        processing.  Integrations that need placeholder replacement
        (e.g. ``{SCRIPT}``, ``__AGENT__``) should override ``setup()``
        and call ``process_template()`` in their own loop — see
        ``CopilotIntegration`` for an example.
        """
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc

        created: list[Path] = []

        for src_file in templates:
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.copy_command_to_directory(src_file, dest, dst_name)
            self.record_file_in_manifest(dst_file, project_root, manifest)
            created.append(dst_file)


        return created

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Uninstall integration files from *project_root*.

        Delegates to ``manifest.uninstall()`` which only removes files
        whose hash still matches the recorded value (unless *force*).

        Returns ``(removed, skipped)`` file lists.
        """
        return manifest.uninstall(project_root, force=force)

    # -- Convenience helpers for subclasses -------------------------------

    def install(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """High-level install — calls ``setup()`` and returns created files."""
        return self.setup(project_root, manifest, parsed_options=parsed_options, **opts)

    def uninstall(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """High-level uninstall — calls ``teardown()``."""
        return self.teardown(project_root, manifest, force=force)


# ---------------------------------------------------------------------------
# MarkdownIntegration — covers ~20 standard agents
# ---------------------------------------------------------------------------


class MarkdownIntegration(IntegrationBase):
    """Concrete base for integrations that use standard Markdown commands.

    Subclasses only need to set ``key``, ``config``, ``registrar_config``.
    Everything else is inherited.

    ``setup()`` processes command templates (replacing ``{SCRIPT}``,
    ``{ARGS}``, ``__AGENT__``, rewriting paths).
    """

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "$ARGUMENTS")
            if self.registrar_config
            else "$ARGUMENTS"
        )
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                project_root=project_root,
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                processed, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)


        return created


# ---------------------------------------------------------------------------
# TomlIntegration — TOML-format agents (Gemini, Tabnine)
# ---------------------------------------------------------------------------


class TomlIntegration(IntegrationBase):
    """Concrete base for integrations that use TOML command format.

    Mirrors ``MarkdownIntegration`` closely: subclasses only need to set
    ``key``, ``config``, ``registrar_config``.  Everything else is inherited.

    ``setup()`` processes command templates through the same placeholder
    pipeline as ``MarkdownIntegration``, then converts the result to
    TOML format (``description`` key + ``prompt`` multiline string).
    """

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args

    def command_filename(self, template_name: str) -> str:
        """TOML commands use ``.toml`` extension."""
        return f"speckit.{template_name}.toml"

    @staticmethod
    def _extract_description(content: str) -> str:
        """Extract the ``description`` value from YAML frontmatter.

        Parses the YAML frontmatter so block scalar descriptions (``|``
        and ``>``) keep their YAML semantics instead of being treated as
        raw text.
        """

        frontmatter_text, _ = TomlIntegration._split_frontmatter(content)
        if not frontmatter_text:
            return ""
        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return ""

        if not isinstance(frontmatter, dict):
            return ""

        description = frontmatter.get("description", "")
        if isinstance(description, str):
            return description
        return ""

    @staticmethod
    def _split_frontmatter(content: str) -> tuple[str, str]:
        """Split YAML frontmatter from the remaining content.

        Returns ``("", content)`` when no complete frontmatter block is
        present. The body is preserved exactly as written so prompt text
        keeps its intended formatting.
        """
        if not content.startswith("---"):
            return "", content

        lines = content.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            return "", content

        frontmatter_end = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.rstrip("\r\n") == "---":
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return "", content

        frontmatter = "".join(lines[1:frontmatter_end])
        body = "".join(lines[frontmatter_end + 1 :])
        return frontmatter, body

    # Control-char detection and basic-string escaping are shared with the
    # extension/preset renderer in ``specify_cli.agents`` via
    # ``specify_cli._toml_string`` so the two never drift apart.
    _has_illegal_toml_control = staticmethod(_has_illegal_toml_control)
    _escape_toml_basic = staticmethod(_escape_toml_basic)

    @staticmethod
    def _render_toml_string(value: str) -> str:
        """Render *value* as a TOML string literal.

        Uses a basic string for single-line values, multiline basic
        strings for values containing newlines, and falls back to a
        literal string or escaped basic string when delimiters appear in
        the content.
        """
        # Control characters other than tab/newline (and a bare CR) cannot
        # appear literally in any TOML string; route them to a fully-escaped
        # basic string so the generated file stays parseable.
        if TomlIntegration._has_illegal_toml_control(value):
            return TomlIntegration._escape_toml_basic(value)

        if "\n" not in value and "\r" not in value:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'

        escaped = value.replace("\\", "\\\\")
        if '"""' not in escaped:
            if escaped.endswith('"'):
                return '"""\n' + escaped + '\\\n"""'
            return '"""\n' + escaped + '"""'
        if "'''" not in value and not value.endswith("'"):
            return "'''\n" + value + "'''"

        return TomlIntegration._escape_toml_basic(value)

    @staticmethod
    def _render_toml(description: str, body: str) -> str:
        """Render a TOML command file from description and body.

        Uses multiline basic strings (``\"\"\"``) with backslashes
        escaped, matching the output of the release script.  Falls back
        to multiline literal strings (``'''``) if the body contains
        ``\"\"\"``, then to an escaped basic string as a last resort.

        The body is ``rstrip("\\n")``'d before rendering, so the TOML
        value preserves content without forcing a trailing newline. As a
        result, multiline delimiters appear on their own line only when
        the rendered value itself ends with a newline.
        """
        toml_lines: list[str] = []

        if description:
            toml_lines.append(
                f"description = {TomlIntegration._render_toml_string(description)}"
            )
            toml_lines.append("")

        body = body.rstrip("\n")
        toml_lines.append(f"prompt = {TomlIntegration._render_toml_string(body)}")

        return "\n".join(toml_lines) + "\n"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "{{args}}")
            if self.registrar_config
            else "{{args}}"
        )
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            description = self._extract_description(raw)
            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                project_root=project_root,
            )
            _, body = self._split_frontmatter(processed)
            toml_content = self._render_toml(description, body)
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                toml_content, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)


        return created


# ---------------------------------------------------------------------------
# YamlIntegration — YAML-format agents (Goose)
# ---------------------------------------------------------------------------

class YamlIntegration(IntegrationBase):
    """Concrete base for integrations that use YAML recipe format.

    Mirrors ``TomlIntegration`` closely: subclasses only need to set
    ``key``, ``config``, ``registrar_config``.  Everything else is inherited.

    ``setup()`` processes command templates through the same placeholder
    pipeline as ``MarkdownIntegration``, then converts the result to
    YAML recipe format (version, title, description, prompt block scalar).
    """

    def command_filename(self, template_name: str) -> str:
        """YAML commands use ``.yaml`` extension."""
        return f"speckit.{template_name}.yaml"

    @staticmethod
    def _extract_frontmatter(content: str) -> dict[str, Any]:
        """Extract frontmatter as a dict from YAML frontmatter block."""

        if not content.startswith("---"):
            return {}

        lines = content.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            return {}

        frontmatter_end = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.rstrip("\r\n") == "---":
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return {}

        frontmatter_text = "".join(lines[1:frontmatter_end])
        try:
            fm = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return {}

        return fm if isinstance(fm, dict) else {}

    @staticmethod
    def _split_frontmatter(content: str) -> tuple[str, str]:
        """Split YAML frontmatter from the remaining body content."""
        if not content.startswith("---"):
            return "", content

        lines = content.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            return "", content

        frontmatter_end = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.rstrip("\r\n") == "---":
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return "", content

        frontmatter = "".join(lines[1:frontmatter_end])
        body = "".join(lines[frontmatter_end + 1 :])
        return frontmatter, body

    @staticmethod
    def _human_title(identifier: str) -> str:
        """Convert an identifier to a human-readable title.

        Strips a leading ``speckit.`` prefix and replaces ``.``, ``-``,
        and ``_`` with spaces before title-casing.
        """
        text = identifier
        if text.startswith("speckit."):
            text = text[len("speckit.") :]
        return text.replace(".", " ").replace("-", " ").replace("_", " ").title()


    @classmethod
    def _build_yaml_header(cls, title: str, description: str) -> dict[str, Any]:
        """Build the base YAML header."""
        header = {
            "version": "1.0.0",
            "title": title,
            "description": description,
            "author": {"contact": "spec-kit"},
            "parameters": [
                {
                    "key": "args",
                    "input_type": "string",
                    "requirement": "optional",
                    "default": "",
                    "description": "User input passed to the command.",
                }
            ],
            "extensions": [{"type": "builtin", "name": "developer"}],
            "activities": ["Spec-Driven Development"],
        }
        return header

    @classmethod
    def _render_yaml(cls, title: str, description: str, body: str, source_id: str) -> str:
        """Render a YAML recipe file from title, description, and body.

        Produces a Goose-compatible recipe with a literal block scalar
        for the prompt content.  Uses ``yaml.safe_dump()`` for the
        header fields to ensure proper escaping.
        """
        header = cls._build_yaml_header(title, description)

        header_yaml = yaml.safe_dump(
            header,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).strip()

        # Indent the body for YAML block scalar. Use an explicit indentation
        # indicator ("|2") rather than a bare "|": YAML infers a plain block
        # scalar's indentation from its first non-empty line, so a body whose
        # first line is itself indented (e.g. a markdown code block or a nested
        # list item) would make the parser expect that deeper indent for the
        # whole block and reject the later, less-indented lines. Pinning the
        # indent to 2 keeps the recipe parseable whatever the body looks like.
        indented = "\n".join(f"  {line}" for line in body.split("\n"))

        lines = [
            header_yaml,
            "prompt: |2",
            indented,
            "",
            f"# Source: {source_id}",
        ]

        return "\n".join(lines) + "\n"


    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        dest = self.commands_dest(project_root).resolve()
        try:
            dest.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Integration destination {dest} escapes "
                f"project root {project_root_resolved}"
            ) from exc
        dest.mkdir(parents=True, exist_ok=True)

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "{{args}}")
            if self.registrar_config
            else "{{args}}"
        )
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")
            fm = self._extract_frontmatter(raw)
            description = fm.get("description", "")
            if not isinstance(description, str):
                description = str(description) if description is not None else ""
            title = fm.get("title", "") or fm.get("name", "")
            if not isinstance(title, str):
                title = str(title) if title is not None else ""
            if not title:
                title = self._human_title(src_file.stem)

            processed = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                project_root=project_root,
            )
            _, body = self._split_frontmatter(processed)
            yaml_content = self._render_yaml(
                title, description, body, f"templates/commands/{src_file.name}"
            )
            dst_name = self.command_filename(src_file.stem)
            dst_file = self.write_file_and_record(
                yaml_content, dest / dst_name, project_root, manifest
            )
            created.append(dst_file)


        return created


# ---------------------------------------------------------------------------
# SkillsIntegration — skills-format agents (Codex, Kimi, Agy)
# ---------------------------------------------------------------------------


class SkillsIntegration(IntegrationBase):
    """Concrete base for integrations that install commands as agent skills.

    Skills use the ``speckit-<name>/SKILL.md`` directory layout following
    the `agentskills.io <https://agentskills.io/specification>`_ spec.

    Subclasses set ``key``, ``config``, ``registrar_config`` like any
    integration.  They may also
    override ``options()`` to declare additional CLI flags (e.g.
    ``--skills``, ``--migrate-legacy``).

    ``setup()`` processes each shared command template into a
    ``speckit-<name>/SKILL.md`` file with skills-oriented frontmatter.
    """

    invoke_separator = "-"

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args

    def skills_dest(self, project_root: Path) -> Path:
        """Return the absolute path to the skills output directory.

        Derived from ``config["folder"]`` and the configured
        ``commands_subdir`` (defaults to ``"skills"``).

        Raises ``ValueError`` when ``config`` or ``folder`` is missing.
        """
        if not self.config:
            raise ValueError(f"{type(self).__name__}.config is not set.")
        folder = self.config.get("folder")
        if not folder:
            raise ValueError(
                f"{type(self).__name__}.config is missing required 'folder' entry."
            )
        subdir = self.config.get("commands_subdir", "skills")
        return project_root / folder / subdir

    def build_command_invocation(self, command_name: str, args: str = "") -> str:
        """Skills use ``/speckit-<stem>`` (hyphenated directory name)."""
        stem = command_name
        if stem.startswith("speckit."):
            stem = stem[len("speckit."):]

        invocation = "/speckit-" + stem.replace(".", "-")
        if args:
            invocation = f"{invocation} {args}"
        return invocation

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

        return re.sub(
            r"(?m)^([ \t]*)(- For each executable hook, output the following[^\r\n]*)(\r\n|\n|$)",
            repl,
            content,
        )

    def post_process_skill_content(self, content: str) -> str:
        """Post-process a SKILL.md file's content after generation.

        Called by external skill generators (presets, extensions) to let
        the integration inject agent-specific frontmatter or body
        transformations.  The base implementation injects shared skills
        guidance for converting dotted hook command names to hyphenated
        slash commands.  Subclasses may override — see ``ClaudeIntegration``.
        """
        return self._inject_hook_command_note(content)

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install command templates as agent skills.

        Creates ``speckit-<name>/SKILL.md`` for each shared command
        template.  Each SKILL.md has normalised frontmatter containing
        ``name``, ``description``, ``compatibility``, and ``metadata``.
        """

        templates = self.list_command_templates()
        if not templates:
            return []

        project_root_resolved = project_root.resolve()
        if manifest.project_root != project_root_resolved:
            raise ValueError(
                f"manifest.project_root ({manifest.project_root}) does not match "
                f"project_root ({project_root_resolved})"
            )

        skills_dir = self.skills_dest(project_root).resolve()
        try:
            skills_dir.relative_to(project_root_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Skills destination {skills_dir} escapes "
                f"project root {project_root_resolved}"
            ) from exc

        script_type = opts.get("script_type", "sh")
        arg_placeholder = (
            self.registrar_config.get("args", "$ARGUMENTS")
            if self.registrar_config
            else "$ARGUMENTS"
        )
        created: list[Path] = []

        for src_file in templates:
            raw = src_file.read_text(encoding="utf-8")

            # Derive the skill name from the template stem
            command_name = src_file.stem  # e.g. "plan"
            skill_name = f"speckit-{command_name.replace('.', '-')}"

            # Parse frontmatter for description
            frontmatter: dict[str, Any] = {}
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1])
                        if isinstance(fm, dict):
                            frontmatter = fm
                    except yaml.YAMLError:
                        pass

            # Process body through the standard template pipeline
            processed_body = self.process_template(
                raw, self.key, script_type, arg_placeholder,
                project_root=project_root,
                invoke_separator=self.invoke_separator,
            )
            # Strip the processed frontmatter — we rebuild it for skills.
            # Preserve leading whitespace in the body to match release ZIP
            # output byte-for-byte (the template body starts with \n after
            # the closing ---).
            if processed_body.startswith("---"):
                parts = processed_body.split("---", 2)
                if len(parts) >= 3:
                    processed_body = parts[2]

            # Select description — use the original template description
            # to stay byte-for-byte identical with release ZIP output.
            description = frontmatter.get("description", "")
            if not description:
                description = f"Spec Kit: {command_name} workflow"

            # Build SKILL.md with manually formatted frontmatter (stable
            # double-quoted values). yaml_quote escapes newlines and control
            # characters that a plain quoted f-string cannot carry.
            skill_content = (
                f"---\n"
                f"name: {yaml_quote(skill_name)}\n"
                f"description: {yaml_quote(description)}\n"
                f"compatibility: {yaml_quote('Requires spec-kit project structure with .specify/ directory')}\n"
                f"metadata:\n"
                f"  author: {yaml_quote('github-spec-kit')}\n"
                f"  source: {yaml_quote('templates/commands/' + src_file.name)}\n"
                f"---\n"
                f"{processed_body}"
            )

            skill_content = self.post_process_skill_content(skill_content)

            # Write speckit-<name>/SKILL.md
            skill_dir = skills_dir / skill_name
            skill_file = skill_dir / "SKILL.md"
            dst = self.write_file_and_record(
                skill_content, skill_file, project_root, manifest
            )
            created.append(dst)


        return created
