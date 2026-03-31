"""
Agent Command Registrar for Spec Kit

Shared infrastructure for registering commands with AI agents.
Used by both the extension system and the preset system to write
command files into agent-specific directories in the correct format.
"""

from pathlib import Path
from typing import Dict, List, Any

import platform
import re
from copy import deepcopy
import yaml


class CommandRegistrar:
    """Handles registration of commands with AI agents.

    Supports writing command files in Markdown or TOML format to the
    appropriate agent directory, with correct argument placeholders
    and companion files (e.g. Copilot .prompt.md).
    """

    # Agent configurations with directory, format, and argument placeholder
    AGENT_CONFIGS = {
        "claude": {
            "dir": ".claude/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "gemini": {
            "dir": ".gemini/commands",
            "format": "toml",
            "args": "{{args}}",
            "extension": ".toml"
        },
        "copilot": {
            "dir": ".github/agents",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".agent.md"
        },
        "cursor": {
            "dir": ".cursor/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "qwen": {
            "dir": ".qwen/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "opencode": {
            "dir": ".opencode/command",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "codex": {
            "dir": ".agents/skills",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": "/SKILL.md",
        },
        "windsurf": {
            "dir": ".windsurf/workflows",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "junie": {
            "dir": ".junie/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "kilocode": {
            "dir": ".kilocode/workflows",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "auggie": {
            "dir": ".augment/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "roo": {
            "dir": ".roo/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "codebuddy": {
            "dir": ".codebuddy/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "qodercli": {
            "dir": ".qoder/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "kiro-cli": {
            "dir": ".kiro/prompts",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "pi": {
            "dir": ".pi/prompts",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "amp": {
            "dir": ".agents/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "shai": {
            "dir": ".shai/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "tabnine": {
            "dir": ".tabnine/agent/commands",
            "format": "toml",
            "args": "{{args}}",
            "extension": ".toml"
        },
        "bob": {
            "dir": ".bob/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "kimi": {
            "dir": ".kimi/skills",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": "/SKILL.md",
        },
        "trae": {
            "dir": ".trae/rules",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "iflow": {
            "dir": ".iflow/commands",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "goose": {
            "dir": ".goose/recipes",
            "format": "yaml",
            "args": "{{args}}",
            "extension": ".yaml"
        }
    }

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
        body = content[end_marker + 3:].strip()

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

        yaml_str = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
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
                    scripts[key] = self._rewrite_project_relative_paths(script_path)
        return frontmatter

    @staticmethod
    def _rewrite_project_relative_paths(text: str) -> str:
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
        text = re.sub(r'(^|[\s`"\'(])(?:\.?/)?templates/', r"\1.specify/templates/", text)

        return text.replace(".specify/.specify/", ".specify/").replace(".specify.specify/", ".specify/")

    def render_markdown_command(
        self,
        frontmatter: dict,
        body: str,
        source_id: str,
        context_note: str = None
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

    def render_toml_command(
        self,
        frontmatter: dict,
        body: str,
        source_id: str
    ) -> str:
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
            desc = frontmatter["description"].replace('"', '\\"')
            toml_lines.append(f'description = "{desc}"')
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
            escaped_body = (
                body.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            toml_lines.append(f'prompt = "{escaped_body}"')

        return "\n".join(toml_lines)

    def render_yaml_command(
        self,
        frontmatter: dict,
        body: str,
        source_id: str
    ) -> str:
        """Render command in YAML format for Goose recipes.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            source_id: Source identifier (extension or preset ID)

        Returns:
            Formatted YAML recipe file content
        """
        # Get title from frontmatter or generate from command name
        title = frontmatter.get("title", "")
        if not title and "name" in frontmatter:
            # Generate title from command name
            title = frontmatter["name"].replace("_", " ").replace("-", " ").title()

        description = frontmatter.get("description", "")

        # Build YAML structure following Goose recipe schema
        # Use yaml.safe_dump() for proper escaping of title and description
        header_dict = {
            "version": "1.0.0",
            "title": title,
            "description": description,
            "author": {"contact": "spec-kit"},
            "extensions": [{"type": "builtin", "name": "developer"}],
            "activities": ["Spec-Driven Development"],
        }

        # Dump header with proper escaping and consistent formatting
        header_yaml = yaml.safe_dump(
            header_dict,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).strip()

        # Build the final YAML with literal block scalar for prompt
        lines = [header_yaml, "prompt: |"]

        # Indent each line of body for proper YAML block scalar formatting
        for line in body.split("\n"):
            lines.append(f"  {line}")

        # Add source comment at the end
        lines.append("")
        lines.append(f"# Source: {source_id}")

        return "\n".join(lines)

    def render_skill_command(
        self,
        agent_name: str,
        skill_name: str,
        frontmatter: dict,
        body: str,
        source_id: str,
        source_file: str,
        project_root: Path,
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

        if agent_name in {"codex", "kimi"}:
            body = self.resolve_skill_placeholders(agent_name, frontmatter, body, project_root)

        description = frontmatter.get("description", f"Spec-kit workflow command: {skill_name}")
        skill_frontmatter = {
            "name": skill_name,
            "description": description,
            "compatibility": "Requires spec-kit project structure with .specify/ directory",
            "metadata": {
                "author": "github-spec-kit",
                "source": f"{source_id}:{source_file}",
            },
        }
        return self.render_frontmatter(skill_frontmatter) + "\n" + body

    @staticmethod
    def resolve_skill_placeholders(agent_name: str, frontmatter: dict, body: str, project_root: Path) -> str:
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
            default_variant = "ps" if platform.system().lower().startswith("win") else "sh"
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

        agent_script_command = agent_scripts.get(script_variant) if script_variant else None
        if agent_script_command:
            agent_script_command = agent_script_command.replace("{ARGS}", "$ARGUMENTS")
            body = body.replace("{AGENT_SCRIPT}", agent_script_command)

        body = body.replace("{ARGS}", "$ARGUMENTS").replace("__AGENT__", agent_name)
        return CommandRegistrar._rewrite_project_relative_paths(body)

    def _convert_argument_placeholder(self, content: str, from_placeholder: str, to_placeholder: str) -> str:
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
    def _compute_output_name(agent_name: str, cmd_name: str, agent_config: Dict[str, Any]) -> str:
        """Compute the on-disk command or skill name for an agent."""
        if agent_config["extension"] != "/SKILL.md":
            return cmd_name

        short_name = cmd_name
        if short_name.startswith("speckit."):
            short_name = short_name[len("speckit."):]
        short_name = short_name.replace(".", "-")

        return f"speckit-{short_name}"

    def register_commands(
        self,
        agent_name: str,
        commands: List[Dict[str, Any]],
        source_id: str,
        source_dir: Path,
        project_root: Path,
        context_note: str = None
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

            frontmatter = self._adjust_script_paths(frontmatter)

            body = self._convert_argument_placeholder(
                body, "$ARGUMENTS", agent_config["args"]
            )

            output_name = self._compute_output_name(agent_name, cmd_name, agent_config)

            if agent_config["extension"] == "/SKILL.md":
                output = self.render_skill_command(
                    agent_name, output_name, frontmatter, body, source_id, cmd_file, project_root
                )
            elif agent_config["format"] == "markdown":
                output = self.render_markdown_command(frontmatter, body, source_id, context_note)
            elif agent_config["format"] == "toml":
                output = self.render_toml_command(frontmatter, body, source_id)
            elif agent_config["format"] == "yaml":
                output = self.render_yaml_command(frontmatter, body, source_id)
            else:
                raise ValueError(f"Unsupported format: {agent_config['format']}")

            dest_file = commands_dir / f"{output_name}{agent_config['extension']}"
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(output, encoding="utf-8")

            if agent_name == "copilot":
                self.write_copilot_prompt(project_root, cmd_name)

            registered.append(cmd_name)

            for alias in cmd_info.get("aliases", []):
                alias_output_name = self._compute_output_name(agent_name, alias, agent_config)
                alias_output = output
                if agent_config["extension"] == "/SKILL.md":
                    alias_output = self.render_skill_command(
                        agent_name, alias_output_name, frontmatter, body, source_id, cmd_file, project_root
                    )
                alias_file = commands_dir / f"{alias_output_name}{agent_config['extension']}"
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
        context_note: str = None
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

        for agent_name, agent_config in self.AGENT_CONFIGS.items():
            agent_dir = project_root / agent_config["dir"]

            if agent_dir.exists():
                try:
                    registered = self.register_commands(
                        agent_name, commands, source_id, source_dir, project_root,
                        context_note=context_note
                    )
                    if registered:
                        results[agent_name] = registered
                except ValueError:
                    continue

        return results

    def unregister_commands(
        self,
        registered_commands: Dict[str, List[str]],
        project_root: Path
    ) -> None:
        """Remove previously registered command files from agent directories.

        Args:
            registered_commands: Dict mapping agent names to command name lists
            project_root: Path to project root
        """
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in self.AGENT_CONFIGS:
                continue

            agent_config = self.AGENT_CONFIGS[agent_name]
            commands_dir = project_root / agent_config["dir"]

            for cmd_name in cmd_names:
                output_name = self._compute_output_name(agent_name, cmd_name, agent_config)
                cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                if cmd_file.exists():
                    cmd_file.unlink()

                if agent_name == "copilot":
                    prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                    if prompt_file.exists():
                        prompt_file.unlink()
