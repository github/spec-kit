"""
Runtime template renderer for InfraKit.

This module replaces the release-time bash pipeline in
``.github/workflows/scripts/create-release-packages.sh``. ``infrakit init``
calls :func:`materialize_project` which copies the in-package templates into
the user's project, rendering per-agent variants (folder layout, frontmatter
substitution, file extension, TOML wrapping) at call time.

The renderer takes its inputs from two sources:

* The templates bundled inside the wheel at ``infrakit_cli/templates``
  (resolved by :func:`templates_root`).
* The per-agent layout map in :mod:`infrakit_cli.agent_config`.

Releases ship the CLI + templates as a single artifact; per-agent specificity
is materialised on the user's machine, not by CI.
"""

from __future__ import annotations

import re
import shutil
from importlib.resources import files
from pathlib import Path

from .agent_config import AGENT_CONFIG
from .iac_config import IAC_CONFIG

# ---------------------------------------------------------------------------
# Path resolution: locate the bundled templates dir.
# ---------------------------------------------------------------------------


def templates_root() -> Path:
    """Return the path to the bundled ``templates/`` directory.

    Prefers a repo-relative path when running from a source checkout (so local
    edits show up immediately during development). Falls back to the wheel's
    package-data location.
    """
    repo_relative = Path(__file__).resolve().parent.parent.parent / "templates"
    if repo_relative.is_dir():
        return repo_relative
    return Path(str(files("infrakit_cli").joinpath("templates")))


# ---------------------------------------------------------------------------
# Path-rewrite rules: mirror the ``rewrite_paths()`` sed pipeline in
# ``create-release-packages.sh``. Command bodies often reference ``memory/``,
# ``scripts/``, or ``templates/`` at the repo root; in a user project these
# live under ``.infrakit/``.
# ---------------------------------------------------------------------------

_PATH_REWRITES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<![\w./-])memory/"), ".infrakit/memory/"),
    (re.compile(r"(?<![\w./-])scripts/"), ".infrakit/scripts/"),
    (re.compile(r"(?<![\w./-])templates/"), ".infrakit/templates/"),
    # Idempotency: if a path is already correctly under .infrakit/, do not
    # double-prefix it. The pipeline runs the rewrites first then collapses
    # any accidental doubling here.
    (re.compile(r"\.infrakit\.infrakit/"), ".infrakit/"),
]


def _rewrite_paths(text: str) -> str:
    for pattern, replacement in _PATH_REWRITES:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Command parsing: extract description from frontmatter, return body.
# ---------------------------------------------------------------------------

_DESCRIPTION_RE = re.compile(
    r'^description:\s*"?(?P<desc>[^"\n]*)"?\s*$',
    re.MULTILINE,
)


def parse_description(template_text: str) -> str:
    """Extract the value of ``description:`` from YAML frontmatter.

    Returns an empty string if no description is found (e.g. a command without
    frontmatter). Used by the TOML wrapper for Gemini/Qwen output.
    """
    match = _DESCRIPTION_RE.search(template_text)
    return match.group("desc").strip() if match else ""


# ---------------------------------------------------------------------------
# Per-command rendering.
# ---------------------------------------------------------------------------


def render_command(template_text: str, *, args_token: str, agent: str) -> str:
    """Apply the runtime substitutions to a command body.

    ``{ARGS}``      → ``args_token`` (e.g. ``$ARGUMENTS`` or ``{{args}}``).
    ``__AGENT__``   → the agent key (e.g. ``claude``, ``gemini``).

    Path tokens like ``memory/``, ``scripts/``, ``templates/`` at non-anchored
    positions are rewritten under ``.infrakit/`` to match the on-disk layout
    the rest of the CLI produces.
    """
    text = template_text.replace("{ARGS}", args_token).replace("__AGENT__", agent)
    return _rewrite_paths(text)


def write_command(
    rendered_body: str,
    dest_dir: Path,
    *,
    name: str,
    command_format: str,
    extension: str,
    description: str = "",
) -> Path:
    """Write a rendered command to disk.

    ``command_format`` controls the output wrapper:

    * ``markdown``   — raw body, written as-is.
    * ``agent.md``   — raw body (same as markdown; the distinction is only the
      file extension and Copilot's companion-prompt extras).
    * ``toml``       — wrapped in a TOML document with ``description`` and
      ``prompt`` keys, suitable for Gemini / Qwen.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"infrakit:{name}{extension}"

    if command_format == "toml":
        escaped = rendered_body.replace("\\", "\\\\")
        body = (
            f'description = "{description}"\n'
            "\n"
            'prompt = """\n'
            f"{escaped}\n"
            '"""\n'
        )
        dest.write_text(body, encoding="utf-8")
    else:
        dest.write_text(rendered_body, encoding="utf-8")

    return dest


# ---------------------------------------------------------------------------
# Per-agent extras.
# ---------------------------------------------------------------------------


def _emit_copilot_prompts(agents_dir: Path, prompts_dir: Path) -> int:
    """Copilot uses an agent + companion-prompt pair. For each ``infrakit:*.agent.md``
    file written by ``write_command``, emit a sibling ``infrakit:*.prompt.md``
    whose frontmatter points at the agent. Returns the number of prompt files
    written.
    """
    if not agents_dir.is_dir():
        return 0
    prompts_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for agent_file in sorted(agents_dir.glob("infrakit:*.agent.md")):
        basename = agent_file.name[: -len(".agent.md")]  # "infrakit:setup"
        prompt_file = prompts_dir / f"{basename}.prompt.md"
        prompt_file.write_text(
            f"---\nagent: {basename}\n---\n",
            encoding="utf-8",
        )
        count += 1
    return count


def _copy_vscode_settings(project_path: Path) -> bool:
    """Materialise ``.vscode/settings.json`` from the bundled template.

    If the user already has a ``.vscode/settings.json`` (e.g. they ran with
    ``--here`` on an existing project), the two JSON documents are deep-merged
    rather than overwritten. Returns True if the file was written; False if
    the source template was missing.
    """
    import json

    source = templates_root() / "vscode-settings.json"
    if not source.is_file():
        return False
    dest_dir = project_path / ".vscode"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "settings.json"

    template_data = json.loads(source.read_text(encoding="utf-8"))
    if dest.exists():
        try:
            existing = json.loads(dest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        merged = _deep_merge_dicts(existing, template_data)
    else:
        merged = template_data
    dest.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return True


def _deep_merge_dicts(base: dict, update: dict) -> dict:
    """Recursively merge ``update`` into ``base``. New keys win; for keys
    present in both, dicts are merged recursively and other values are
    overwritten by ``update``.
    """
    result = dict(base)
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Static-tree copies: memory/, scripts/<variant>/, IaC assets, personas.
# ---------------------------------------------------------------------------


def _copy_tree_into(src: Path, dest: Path, *, overwrite: bool = False) -> int:
    """Copy every file under ``src`` into ``dest``, preserving relative paths.

    Existing files at the destination are left untouched unless ``overwrite``
    is True. Returns the number of files copied.
    """
    if not src.is_dir():
        return 0
    count = 0
    for source_file in src.rglob("*"):
        if not source_file.is_file():
            continue
        rel = source_file.relative_to(src)
        dest_file = dest / rel
        if dest_file.exists() and not overwrite:
            continue
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest_file)
        count += 1
    return count


# ---------------------------------------------------------------------------
# Orchestrator.
# ---------------------------------------------------------------------------


def materialize_project(
    project_path: Path,
    *,
    ai_assistant: str,
    iac_tool: str,
    script_variant: str = "sh",
    overwrite: bool = False,
) -> dict[str, int]:
    """Materialise a fully-set-up InfraKit project at ``project_path``.

    This is the runtime counterpart to ``create-release-packages.sh``: instead
    of pre-building 76 zips at release time, the CLI ships the raw templates
    and applies the (agent, iac, script) transformations on demand.

    Returns a dict with counts: ``{"generic_commands": N, "iac_commands": N,
    "personas": N, "prompt_files": N}`` — useful for the tracker UI.
    """
    project_path.mkdir(parents=True, exist_ok=True)
    counts = {"generic_commands": 0, "iac_commands": 0, "personas": 0, "prompt_files": 0}

    agent_cfg = AGENT_CONFIG.get(ai_assistant)
    if not agent_cfg:
        raise ValueError(f"unknown AI assistant: {ai_assistant}")
    iac_cfg = IAC_CONFIG.get(iac_tool)
    if not iac_cfg:
        raise ValueError(f"unknown IaC tool: {iac_tool}")

    folder = (agent_cfg.get("folder") or "").rstrip("/")
    commands_subdir = agent_cfg.get("commands_subdir", "commands")
    command_format = agent_cfg.get("command_format", "markdown")
    command_args = agent_cfg.get("command_args", "$ARGUMENTS")
    command_extension = agent_cfg.get("command_extension", ".md")
    extras = agent_cfg.get("extras", []) or []

    tpl_root = templates_root()
    iac_root = tpl_root / "iac" / iac_tool

    # --- 1. Render commands into the agent folder -------------------------

    if folder:
        cmds_dest = project_path / folder / commands_subdir
    else:
        cmds_dest = project_path / commands_subdir

    allowed_generic = set(iac_cfg.get("generic_commands", []))
    counts["generic_commands"] = _render_command_set(
        src_dir=tpl_root / "commands",
        allowed=allowed_generic,
        dest_dir=cmds_dest,
        agent=ai_assistant,
        args_token=command_args,
        command_format=command_format,
        extension=command_extension,
        overwrite=overwrite,
    )

    allowed_iac = set(iac_cfg.get("iac_commands", []))
    counts["iac_commands"] = _render_command_set(
        src_dir=iac_root / "commands",
        allowed=allowed_iac,
        dest_dir=cmds_dest,
        agent=ai_assistant,
        args_token=command_args,
        command_format=command_format,
        extension=command_extension,
        overwrite=overwrite,
    )

    # --- 2. Personas: generic + IaC-specific into .infrakit/agent_personas/

    personas_dest = project_path / ".infrakit" / "agent_personas"
    counts["personas"] += _copy_tree_into(
        tpl_root / "agent_personas", personas_dest, overwrite=overwrite
    )
    counts["personas"] += _copy_tree_into(
        iac_root / "agent_personas", personas_dest, overwrite=overwrite
    )

    # --- 3. Per-agent extras (Copilot prompts, VS Code settings) ----------

    if "copilot_prompts" in extras and folder:
        counts["prompt_files"] = _emit_copilot_prompts(
            cmds_dest, project_path / folder / "prompts"
        )

    if "vscode_settings" in extras:
        _copy_vscode_settings(project_path)

    return counts


def _render_command_set(
    *,
    src_dir: Path,
    allowed: set[str],
    dest_dir: Path,
    agent: str,
    args_token: str,
    command_format: str,
    extension: str,
    overwrite: bool,
) -> int:
    """Render the subset of ``src_dir``'s ``.md`` templates whose stem is in
    ``allowed`` to ``dest_dir``. Returns the number of files written.
    """
    if not src_dir.is_dir():
        return 0
    written = 0
    for template in sorted(src_dir.glob("*.md")):
        if template.stem not in allowed:
            continue
        dest_path = dest_dir / f"infrakit:{template.stem}{extension}"
        if dest_path.exists() and not overwrite:
            continue
        text = template.read_text(encoding="utf-8")
        body = render_command(text, args_token=args_token, agent=agent)
        write_command(
            body,
            dest_dir,
            name=template.stem,
            command_format=command_format,
            extension=extension,
            description=parse_description(text),
        )
        written += 1
    return written
