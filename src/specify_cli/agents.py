"""
Agent Command Registrar for Spec Kit

Shared infrastructure for registering commands with AI agents.
Used by both the extension system and the preset system to write
command files into agent-specific directories in the correct format.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional

import platform
import re
from copy import deepcopy
import yaml

from specify_cli.behavior import translate_behavior, strip_behavior_keys, get_deployment_type, get_copilot_tools


# Agent-specific frontmatter keys that extension/preset authors may declare in
# source command frontmatter and have passed through verbatim to the generated
# skill file.  Keys not in this set are ignored during skill rendering.
_SKILL_PASSTHROUGH_KEYS: dict[str, frozenset[str]] = {
    "claude": frozenset({
        "context",                    # fork execution model
        "agent",                      # subagent type when context: fork
        "model",                      # model override
        "effort",                     # effort level
        "allowed-tools",              # tool restriction list
        "color",                      # UI color in Claude Code task list
        "paths",                      # path-based activation glob
        "argument-hint",              # UI hint in slash-command menu
        "disable-model-invocation",   # override default True
        "user-invocable",             # override default True
    }),
    "codex": frozenset({
        "model",
        "effort",
    }),
}


def _build_agent_configs() -> dict[str, Any]:
    """Derive CommandRegistrar.AGENT_CONFIGS from INTEGRATION_REGISTRY."""
    from specify_cli.integrations import INTEGRATION_REGISTRY

    configs: dict[str, dict[str, Any]] = {}
    for key, integration in INTEGRATION_REGISTRY.items():
        if key == "generic":
            continue
        if integration.registrar_config:
            configs[key] = dict(integration.registrar_config)
    return configs


class CommandRegistrar:
    """Handles registration of commands with AI agents.

    Supports writing command files in Markdown or TOML format to the
    appropriate agent directory, with correct argument placeholders
    and companion files (e.g. Copilot .prompt.md).
    """

    # Derived from INTEGRATION_REGISTRY — single source of truth.
    # Populated lazily via _ensure_configs() on first use.
    AGENT_CONFIGS: dict[str, dict[str, Any]] = {}
    _configs_loaded: bool = False

    def __init__(self) -> None:
        self._ensure_configs()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._ensure_configs()

    @classmethod
    def _ensure_configs(cls) -> None:
        if not cls._configs_loaded:
            try:
                cls.AGENT_CONFIGS = _build_agent_configs()
                cls._configs_loaded = True
            except ImportError:
                pass  # Circular import during module init; retry on next access

    @staticmethod
    def parse_frontmatter(content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from Markdown content.

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        if not content.startswith("---"):
            return {}, content

        # Find second ---
        end_marker = content.find("---", 3)
        if end_marker == -1:
            return {}, content

        frontmatter_str = content[3:end_marker].strip()
        body = content[end_marker + 3 :].strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError:
            frontmatter = {}

        if not isinstance(frontmatter, dict):
            frontmatter = {}

        return frontmatter, body

    @staticmethod
    def render_frontmatter(fm: dict) -> str:
        """Render frontmatter dictionary as YAML.

        Args:
            fm: Frontmatter dictionary

        Returns:
            YAML-formatted frontmatter with delimiters
        """
        if not fm:
            return ""

        yaml_str = yaml.dump(
            fm, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
        return f"---\n{yaml_str}---\n"

    def _adjust_script_paths(self, frontmatter: dict) -> dict:
        """Normalize script paths in frontmatter to generated project locations.

        Rewrites known repo-relative and top-level script paths under the
        `scripts` and `agent_scripts` keys (for example `../../scripts/`,
        `../../templates/`, `../../memory/`, `scripts/`, `templates/`, and
        `memory/`) to the `.specify/...` paths used in generated projects.

        Args:
            frontmatter: Frontmatter dictionary

        Returns:
            Modified frontmatter with normalized project paths
        """
        frontmatter = deepcopy(frontmatter)

        for script_key in ("scripts", "agent_scripts"):
            scripts = frontmatter.get(script_key)
            if not isinstance(scripts, dict):
                continue

            for key, script_path in scripts.items():
                if isinstance(script_path, str):
                    scripts[key] = self.rewrite_project_relative_paths(script_path)
        return frontmatter

    @staticmethod
    def rewrite_project_relative_paths(text: str) -> str:
        """Rewrite repo-relative paths to their generated project locations."""
        if not isinstance(text, str) or not text:
            return text

        for old, new in (
            ("../../memory/", ".specify/memory/"),
            ("../../scripts/", ".specify/scripts/"),
            ("../../templates/", ".specify/templates/"),
        ):
            text = text.replace(old, new)

        # Only rewrite top-level style references so extension-local paths like
        # ".specify/extensions/<ext>/scripts/..." remain intact.
        text = re.sub(r'(^|[\s`"\'(])(?:\.?/)?memory/', r"\1.specify/memory/", text)
        text = re.sub(r'(^|[\s`"\'(])(?:\.?/)?scripts/', r"\1.specify/scripts/", text)
        text = re.sub(
            r'(^|[\s`"\'(])(?:\.?/)?templates/', r"\1.specify/templates/", text
        )

        return text.replace(".specify/.specify/", ".specify/").replace(
            ".specify.specify/", ".specify/"
        )

    @staticmethod
    def rewrite_extension_paths(text: str, extension_id: str, extension_dir: Path) -> str:
        """Rewrite extension-relative paths to their installed project locations.

        Extension command bodies reference files using paths relative to the
        extension root (e.g. ``agents/control/commander.md``).  After install,
        those files live at ``.specify/extensions/<id>/...``.  This method
        rewrites such references so that AI agents can locate them after install.

        Only directories that actually exist inside *extension_dir* are rewritten,
        keeping the behaviour conservative and avoiding false positives on prose.

        Args:
            text: Body text of the command file.
            extension_id: The extension identifier (e.g. ``"echelon"``).
            extension_dir: Path to the installed extension directory.

        Returns:
            Body text with extension-relative paths expanded.
        """
        if not isinstance(text, str) or not text:
            return text

        _SKIP = {"commands", ".git"}
        try:
            subdirs = [
                d.name
                for d in extension_dir.iterdir()
                if d.is_dir() and d.name not in _SKIP
            ]
        except OSError:
            return text

        base_prefix = f".specify/extensions/{extension_id}/"

        # Replace $EXTENSION_PATH shell variable with the actual installed path.
        text = text.replace("$EXTENSION_PATH", base_prefix.rstrip("/"))

        for subdir in subdirs:
            escaped = re.escape(subdir)
            text = re.sub(
                r"(^|[\s`\"'(])(?:\.?/)?" + escaped + r"/",
                r"\1" + base_prefix + subdir + "/",
                text,
            )

        return text

    def render_markdown_command(
        self, frontmatter: dict, body: str, source_id: str, context_note: str = None
    ) -> str:
        """Render command in Markdown format.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            source_id: Source identifier (extension or preset ID)
            context_note: Custom context comment (default: <!-- Source: {source_id} -->)

        Returns:
            Formatted Markdown command file content
        """
        if context_note is None:
            context_note = f"\n<!-- Source: {source_id} -->\n"
        return self.render_frontmatter(frontmatter) + "\n" + context_note + body

    def render_toml_command(self, frontmatter: dict, body: str, source_id: str) -> str:
        """Render command in TOML format.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            source_id: Source identifier (extension or preset ID)

        Returns:
            Formatted TOML command file content
        """
        toml_lines = []

        if "description" in frontmatter:
            toml_lines.append(
                f"description = {self._render_basic_toml_string(frontmatter['description'])}"
            )
            toml_lines.append("")

        toml_lines.append(f"# Source: {source_id}")
        toml_lines.append("")

        # Keep TOML output valid even when body contains triple-quote delimiters.
        # Prefer multiline forms, then fall back to escaped basic string.
        if '"""' not in body:
            toml_lines.append('prompt = """')
            toml_lines.append(body)
            toml_lines.append('"""')
        elif "'''" not in body:
            toml_lines.append("prompt = '''")
            toml_lines.append(body)
            toml_lines.append("'''")
        else:
            toml_lines.append(f"prompt = {self._render_basic_toml_string(body)}")

        return "\n".join(toml_lines)

    @staticmethod
    def _render_basic_toml_string(value: str) -> str:
        """Render *value* as a TOML basic string literal."""
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'

    def render_yaml_command(
        self,
        frontmatter: dict,
        body: str,
        source_id: str,
        cmd_name: str = "",
    ) -> str:
        """Render command in YAML recipe format for Goose.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            source_id: Source identifier (extension or preset ID)
            cmd_name: Command name used as title fallback

        Returns:
            Formatted YAML recipe file content
        """
        from specify_cli.integrations.base import YamlIntegration

        title = frontmatter.get("title", "") or frontmatter.get("name", "")
        if not isinstance(title, str):
            title = str(title) if title is not None else ""
        if not title and cmd_name:
            title = YamlIntegration._human_title(cmd_name)
        if not title and source_id:
            title = YamlIntegration._human_title(Path(str(source_id)).stem)
        if not title:
            title = "Command"

        description = frontmatter.get("description", "")
        if not isinstance(description, str):
            description = str(description) if description is not None else ""
        return YamlIntegration._render_yaml(title, description, body, source_id)

    def render_agent_definition(
        self,
        agent_name: str,
        skill_name: str,
        frontmatter: dict,
        body: str,
        source_id: str,
        source_file: str,
        project_root: Path,
        source_dir: Optional[Path] = None,
    ) -> str:
        """Render a command as a Claude agent definition file (.claude/agents/{name}.md).

        Agent definitions differ from skills:
        - Body is the system prompt, not a task prompt
        - Frontmatter is minimal: name, description, and behavior-derived fields
        - No user-invocable, disable-model-invocation, context, or metadata keys
        """
        if not isinstance(frontmatter, dict):
            frontmatter = {}

        if source_dir is not None and (source_dir / "extension.yml").exists():
            body = self.rewrite_extension_paths(body, source_id, source_dir)

        behavior = frontmatter.get("behavior") or {}
        agents_overrides = frontmatter.get("agents") or {}
        behavior_fields: dict = {}
        if isinstance(behavior, dict):
            behavior_fields = translate_behavior(
                agent_name, behavior,
                agents_overrides if isinstance(agents_overrides, dict) else {}
            )

        clean_frontmatter = strip_behavior_keys(frontmatter)
        description = clean_frontmatter.get("description", f"Spec-kit agent: {skill_name}")

        # Agent definition frontmatter: minimal set, no skill-specific keys
        agent_fm: dict = {
            "name": skill_name,
            "description": description,
        }

        # Merge behavior-translated fields; remap allowed-tools → tools for agent defs
        for k, v in behavior_fields.items():
            if k == "allowed-tools":
                agent_fm["tools"] = v
            elif k not in {"disable-model-invocation", "user-invocable", "context", "agent"}:
                agent_fm[k] = v

        # Explicit model/tools in source frontmatter win
        for key in ("model", "tools"):
            if key in clean_frontmatter:
                agent_fm[key] = clean_frontmatter[key]

        return self.render_frontmatter(agent_fm) + "\n" + body

    def render_skill_command(
        self,
        agent_name: str,
        skill_name: str,
        frontmatter: dict,
        body: str,
        source_id: str,
        source_file: str,
        project_root: Path,
        source_dir: Optional[Path] = None,
    ) -> str:
        """Render a command override as a SKILL.md file.

        SKILL-target agents should receive the same skills-oriented
        frontmatter shape used elsewhere in the project instead of the
        original command frontmatter.

        Technical debt note:
        Spec-kit currently has multiple SKILL.md generators (template packaging,
        init-time conversion, and extension/preset overrides). Keep the skill
        frontmatter keys aligned (name/description/compatibility/metadata, with
        metadata.author and metadata.source subkeys) to avoid drift across agents.
        """
        if not isinstance(frontmatter, dict):
            frontmatter = {}

        if source_dir is not None and (source_dir / "extension.yml").exists():
            body = self.rewrite_extension_paths(body, source_id, source_dir)

        if agent_name in {"codex", "kimi"}:
            body = self.resolve_skill_placeholders(
                agent_name, frontmatter, body, project_root
            )

        # Extract and translate behavior + agents escape hatch
        behavior = frontmatter.get("behavior") or {}
        agents_overrides = frontmatter.get("agents") or {}
        behavior_fields: dict = {}
        if isinstance(behavior, dict):
            behavior_fields = translate_behavior(
                agent_name, behavior,
                agents_overrides if isinstance(agents_overrides, dict) else {}
            )

        # Strip behavior/agents keys before building skill frontmatter
        clean_frontmatter = strip_behavior_keys(frontmatter)

        description = clean_frontmatter.get("description", f"Spec-kit workflow command: {skill_name}")
        skill_frontmatter = self.build_skill_frontmatter(
            agent_name,
            skill_name,
            description,
            f"{source_id}:{source_file}",
            source_frontmatter=clean_frontmatter,
        )
        # Merge behavior translation — passthrough (already in skill_frontmatter) wins
        # because we only set behavior fields if they are not already set via passthrough,
        # EXCEPT for the set of fields that behavior can legitimately override defaults for.
        _behavior_overridable = {"disable-model-invocation", "user-invocable", "model", "effort", "context", "agent", "allowed-tools"}
        for k, v in behavior_fields.items():
            if k not in skill_frontmatter or k in _behavior_overridable:
                skill_frontmatter[k] = v

        return self.render_frontmatter(skill_frontmatter) + "\n" + body

    @staticmethod
    def build_skill_frontmatter(
        agent_name: str,
        skill_name: str,
        description: str,
        source: str,
        source_frontmatter: dict | None = None,
    ) -> dict:
        """Build consistent SKILL.md frontmatter across all skill generators.

        Args:
            agent_name: Target agent key (e.g. "claude", "codex").
            skill_name: Generated skill name (e.g. "speckit-revenge-extract").
            description: Human-readable description.
            source: Source tracking string (e.g. "revenge:commands/extract.md").
            source_frontmatter: Original command frontmatter. Keys present in
                ``_SKILL_PASSTHROUGH_KEYS[agent_name]`` are merged after
                defaults, allowing source authors to override injected values.
        """
        source_frontmatter = source_frontmatter or {}

        skill_frontmatter: dict = {
            "name": skill_name,
            "description": description,
            "compatibility": "Requires spec-kit project structure with .specify/ directory",
            "metadata": {
                "author": "github-spec-kit",
                "source": source,
            },
        }
        if agent_name == "claude":
            skill_frontmatter["user-invocable"] = True
            skill_frontmatter["disable-model-invocation"] = True

        # Merge passthrough keys from source (wins over defaults above)
        for key in _SKILL_PASSTHROUGH_KEYS.get(agent_name, frozenset()):
            if key in source_frontmatter:
                skill_frontmatter[key] = source_frontmatter[key]

        return skill_frontmatter

    @staticmethod
    def resolve_skill_placeholders(
        agent_name: str, frontmatter: dict, body: str, project_root: Path
    ) -> str:
        """Resolve script placeholders for skills-backed agents."""
        try:
            from . import load_init_options
        except ImportError:
            return body

        if not isinstance(frontmatter, dict):
            frontmatter = {}

        scripts = frontmatter.get("scripts", {}) or {}
        agent_scripts = frontmatter.get("agent_scripts", {}) or {}
        if not isinstance(scripts, dict):
            scripts = {}
        if not isinstance(agent_scripts, dict):
            agent_scripts = {}

        init_opts = load_init_options(project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}

        script_variant = init_opts.get("script")
        if script_variant not in {"sh", "ps"}:
            fallback_order = []
            default_variant = (
                "ps" if platform.system().lower().startswith("win") else "sh"
            )
            secondary_variant = "sh" if default_variant == "ps" else "ps"

            if default_variant in scripts or default_variant in agent_scripts:
                fallback_order.append(default_variant)
            if secondary_variant in scripts or secondary_variant in agent_scripts:
                fallback_order.append(secondary_variant)

            for key in scripts:
                if key not in fallback_order:
                    fallback_order.append(key)
            for key in agent_scripts:
                if key not in fallback_order:
                    fallback_order.append(key)

            script_variant = fallback_order[0] if fallback_order else None

        script_command = scripts.get(script_variant) if script_variant else None
        if script_command:
            script_command = script_command.replace("{ARGS}", "$ARGUMENTS")
            body = body.replace("{SCRIPT}", script_command)

        agent_script_command = (
            agent_scripts.get(script_variant) if script_variant else None
        )
        if agent_script_command:
            agent_script_command = agent_script_command.replace("{ARGS}", "$ARGUMENTS")
            body = body.replace("{AGENT_SCRIPT}", agent_script_command)

        body = body.replace("{ARGS}", "$ARGUMENTS").replace("__AGENT__", agent_name)
        return CommandRegistrar.rewrite_project_relative_paths(body)

    def _convert_argument_placeholder(
        self, content: str, from_placeholder: str, to_placeholder: str
    ) -> str:
        """Convert argument placeholder format.

        Args:
            content: Command content
            from_placeholder: Source placeholder (e.g., "$ARGUMENTS")
            to_placeholder: Target placeholder (e.g., "{{args}}")

        Returns:
            Content with converted placeholders
        """
        return content.replace(from_placeholder, to_placeholder)

    @staticmethod
    def _compute_output_name(
        agent_name: str, cmd_name: str, agent_config: Dict[str, Any]
    ) -> str:
        """Compute the on-disk command or skill name for an agent."""
        if agent_config["extension"] != "/SKILL.md":
            return cmd_name

        short_name = cmd_name
        if short_name.startswith("speckit."):
            short_name = short_name[len("speckit.") :]
        short_name = short_name.replace(".", "-")

        return f"speckit-{short_name}"

    def register_commands(
        self,
        agent_name: str,
        commands: List[Dict[str, Any]],
        source_id: str,
        source_dir: Path,
        project_root: Path,
        context_note: str = None,
    ) -> List[str]:
        """Register commands for a specific agent.

        Args:
            agent_name: Agent name (claude, gemini, copilot, etc.)
            commands: List of command info dicts with 'name', 'file', and optional 'aliases'
            source_id: Identifier of the source (extension or preset ID)
            source_dir: Directory containing command source files
            project_root: Path to project root
            context_note: Custom context comment for markdown output

        Returns:
            List of registered command names

        Raises:
            ValueError: If agent is not supported
        """
        self._ensure_configs()
        if agent_name not in self.AGENT_CONFIGS:
            raise ValueError(f"Unsupported agent: {agent_name}")

        agent_config = self.AGENT_CONFIGS[agent_name]
        commands_dir = project_root / agent_config["dir"]
        commands_dir.mkdir(parents=True, exist_ok=True)

        registered = []

        for cmd_info in commands:
            cmd_name = cmd_info["name"]
            cmd_file = cmd_info["file"]

            source_file = source_dir / cmd_file
            if not source_file.exists():
                continue

            content = source_file.read_text(encoding="utf-8")
            frontmatter, body = self.parse_frontmatter(content)

            # Merge manifest-level fields into frontmatter — source file wins.
            # This lets extension.yml declare behavior/description for agent files
            # that carry no frontmatter of their own (e.g. pure persona prompts).
            for key in ("description", "behavior", "agents"):
                if key in cmd_info and key not in frontmatter:
                    frontmatter[key] = cmd_info[key]

            frontmatter = self._adjust_script_paths(frontmatter)

            for key in agent_config.get("strip_frontmatter_keys", []):
                frontmatter.pop(key, None)

            if agent_config.get("inject_name") and not frontmatter.get("name"):
                # Use custom name formatter if provided (e.g., Forge's hyphenated format)
                format_name = agent_config.get("format_name")
                frontmatter["name"] = format_name(cmd_name) if format_name else cmd_name

            body = self._convert_argument_placeholder(
                body, "$ARGUMENTS", agent_config["args"]
            )

            output_name = self._compute_output_name(agent_name, cmd_name, agent_config)

            # Deployment target is fully derived from behavior.execution
            cmd_type = get_deployment_type(frontmatter)

            if cmd_type == "agent" and agent_name == "claude":
                output = self.render_agent_definition(
                    agent_name, output_name, frontmatter, body,
                    source_id, cmd_file, project_root, source_dir=source_dir,
                )
                agents_dir = project_root / ".claude" / "agents"
                agents_dir.mkdir(parents=True, exist_ok=True)
                dest_file = agents_dir / f"{output_name}.md"
                dest_file.write_text(output, encoding="utf-8")
                registered.append(cmd_name)
                continue  # skip normal skill/command rendering

            if agent_config["extension"] == "/SKILL.md":
                output = self.render_skill_command(
                    agent_name,
                    output_name,
                    frontmatter,
                    body,
                    source_id,
                    cmd_file,
                    project_root,
                    source_dir=source_dir,
                )
            elif agent_config["format"] == "markdown":
                # For Copilot execution:agent, inject behavior-derived fields into frontmatter
                if agent_name == "copilot" and cmd_type == "agent":
                    behavior = frontmatter.get("behavior") or {}
                    agents_overrides = frontmatter.get("agents") or {}
                    extra_fields = translate_behavior(
                        agent_name, behavior,
                        agents_overrides if isinstance(agents_overrides, dict) else {}
                    )
                    copilot_tools = get_copilot_tools(behavior if isinstance(behavior, dict) else {})
                    if copilot_tools:
                        extra_fields["tools"] = copilot_tools
                    # Build modified frontmatter: strip internal keys, add extra
                    copilot_fm = strip_behavior_keys(frontmatter)
                    copilot_fm.update(extra_fields)
                    output = self.render_markdown_command(copilot_fm, body, source_id, context_note)
                else:
                    output = self.render_markdown_command(frontmatter, body, source_id, context_note)
            elif agent_config["format"] == "toml":
                output = self.render_toml_command(frontmatter, body, source_id)
            elif agent_config["format"] == "yaml":
                output = self.render_yaml_command(
                    frontmatter, body, source_id, cmd_name
                )
            else:
                raise ValueError(f"Unsupported format: {agent_config['format']}")

            dest_file = commands_dir / f"{output_name}{agent_config['extension']}"
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(output, encoding="utf-8")

            if agent_name == "copilot":
                self.write_copilot_prompt(project_root, cmd_name)

            registered.append(cmd_name)

            for alias in cmd_info.get("aliases", []):
                alias_output_name = self._compute_output_name(
                    agent_name, alias, agent_config
                )

                # For agents with inject_name, render with alias-specific frontmatter
                if agent_config.get("inject_name"):
                    alias_frontmatter = deepcopy(frontmatter)
                    # Use custom name formatter if provided (e.g., Forge's hyphenated format)
                    format_name = agent_config.get("format_name")
                    alias_frontmatter["name"] = (
                        format_name(alias) if format_name else alias
                    )

                    if agent_config["extension"] == "/SKILL.md":
                        alias_output = self.render_skill_command(
                            agent_name,
                            alias_output_name,
                            alias_frontmatter,
                            body,
                            source_id,
                            cmd_file,
                            project_root,
                            source_dir=source_dir,
                        )
                    elif agent_config["format"] == "markdown":
                        alias_output = self.render_markdown_command(alias_frontmatter, body, source_id, context_note)
                    elif agent_config["format"] == "toml":
                        alias_output = self.render_toml_command(
                            alias_frontmatter, body, source_id
                        )
                    elif agent_config["format"] == "yaml":
                        alias_output = self.render_yaml_command(
                            alias_frontmatter, body, source_id, alias
                        )
                    else:
                        raise ValueError(
                            f"Unsupported format: {agent_config['format']}"
                        )
                else:
                    # For other agents, reuse the primary output
                    alias_output = output
                    if agent_config["extension"] == "/SKILL.md":
                        alias_output = self.render_skill_command(
                            agent_name,
                            alias_output_name,
                            frontmatter,
                            body,
                            source_id,
                            cmd_file,
                            project_root,
                            source_dir=source_dir,
                        )

                alias_file = (
                    commands_dir / f"{alias_output_name}{agent_config['extension']}"
                )
                try:
                    alias_file.resolve().relative_to(commands_dir.resolve())
                except ValueError:
                    raise ValueError(
                        f"Alias output path escapes commands directory: {alias_file!r}"
                    )
                alias_file.parent.mkdir(parents=True, exist_ok=True)
                alias_file.write_text(alias_output, encoding="utf-8")
                if agent_name == "copilot":
                    self.write_copilot_prompt(project_root, alias)
                registered.append(alias)

        return registered

    @staticmethod
    def write_copilot_prompt(project_root: Path, cmd_name: str) -> None:
        """Generate a companion .prompt.md file for a Copilot agent command.

        Args:
            project_root: Path to project root
            cmd_name: Command name (e.g. 'speckit.my-ext.example')
        """
        prompts_dir = project_root / ".github" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = prompts_dir / f"{cmd_name}.prompt.md"
        prompt_file.write_text(f"---\nagent: {cmd_name}\n---\n", encoding="utf-8")

    def register_commands_for_all_agents(
        self,
        commands: List[Dict[str, Any]],
        source_id: str,
        source_dir: Path,
        project_root: Path,
        context_note: str = None,
    ) -> Dict[str, List[str]]:
        """Register commands for all detected agents in the project.

        Args:
            commands: List of command info dicts
            source_id: Identifier of the source (extension or preset ID)
            source_dir: Directory containing command source files
            project_root: Path to project root
            context_note: Custom context comment for markdown output

        Returns:
            Dictionary mapping agent names to list of registered commands
        """
        results = {}

        self._ensure_configs()
        for agent_name, agent_config in self.AGENT_CONFIGS.items():
            agent_dir = project_root / agent_config["dir"]

            if agent_dir.exists():
                try:
                    registered = self.register_commands(
                        agent_name,
                        commands,
                        source_id,
                        source_dir,
                        project_root,
                        context_note=context_note,
                    )
                    if registered:
                        results[agent_name] = registered
                except ValueError:
                    continue

        return results

    def unregister_commands(
        self, registered_commands: Dict[str, List[str]], project_root: Path
    ) -> None:
        """Remove previously registered command files from agent directories.

        Args:
            registered_commands: Dict mapping agent names to command name lists
            project_root: Path to project root
        """
        self._ensure_configs()
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in self.AGENT_CONFIGS:
                continue

            agent_config = self.AGENT_CONFIGS[agent_name]
            commands_dir = project_root / agent_config["dir"]

            for cmd_name in cmd_names:
                output_name = self._compute_output_name(
                    agent_name, cmd_name, agent_config
                )
                cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                if cmd_file.exists():
                    cmd_file.unlink()
                    # For SKILL.md agents each command lives in its own subdirectory
                    # (e.g. .agents/skills/speckit-ext-cmd/SKILL.md). Remove the
                    # parent dir when it becomes empty to avoid orphaned directories.
                    parent = cmd_file.parent
                    if parent != commands_dir and parent.exists():
                        try:
                            parent.rmdir()  # no-op if dir still has other files
                        except OSError:
                            pass

                if agent_name == "copilot":
                    prompt_file = (
                        project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                    )
                    if prompt_file.exists():
                        prompt_file.unlink()

                # Also try agent definition file (Claude-specific)
                if agent_name == "claude":
                    agent_def = project_root / ".claude" / "agents" / f"{output_name}.md"
                    if agent_def.exists():
                        agent_def.unlink()


# Populate AGENT_CONFIGS after class definition.
# Catches ImportError from circular imports during module loading;
# _configs_loaded stays False so the next explicit access retries.
try:
    CommandRegistrar._ensure_configs()
except ImportError:
    pass
