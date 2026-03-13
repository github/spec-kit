"""
Agent Command Registrar for Spec Kit

Shared infrastructure for registering commands with AI agents.
Used by both the extension system and the preset system to write
command files into agent-specific directories in the correct format.
"""

from pathlib import Path
from typing import Dict, List, Any

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
            "dir": ".codex/prompts",
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md"
        },
        "windsurf": {
            "dir": ".windsurf/workflows",
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
            "extension": "/SKILL.md"
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

        yaml_str = yaml.dump(fm, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n"

    def _adjust_script_paths(self, frontmatter: dict) -> dict:
        """Adjust script paths from extension-relative to repo-relative.

        Args:
            frontmatter: Frontmatter dictionary

        Returns:
            Modified frontmatter with adjusted paths
        """
        if "scripts" in frontmatter:
            for key in frontmatter["scripts"]:
                script_path = frontmatter["scripts"][key]
                if script_path.startswith("../../scripts/"):
                    frontmatter["scripts"][key] = f".specify/scripts/{script_path[14:]}"
        return frontmatter

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

        toml_lines.append('prompt = """')
        toml_lines.append(body)
        toml_lines.append('"""')

        return "\n".join(toml_lines)

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

            if agent_config["format"] == "markdown":
                output = self.render_markdown_command(frontmatter, body, source_id, context_note)
            elif agent_config["format"] == "toml":
                output = self.render_toml_command(frontmatter, body, source_id)
            else:
                raise ValueError(f"Unsupported format: {agent_config['format']}")

            dest_file = commands_dir / f"{cmd_name}{agent_config['extension']}"
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(output, encoding="utf-8")

            if agent_name == "copilot":
                self.write_copilot_prompt(project_root, cmd_name)

            registered.append(cmd_name)

            for alias in cmd_info.get("aliases", []):
                alias_file = commands_dir / f"{alias}{agent_config['extension']}"
                alias_file.parent.mkdir(parents=True, exist_ok=True)
                alias_file.write_text(output, encoding="utf-8")
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
            agent_dir = project_root / agent_config["dir"].split("/")[0]

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
                cmd_file = commands_dir / f"{cmd_name}{agent_config['extension']}"
                if cmd_file.exists():
                    cmd_file.unlink()

                if agent_name == "copilot":
                    prompt_file = project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                    if prompt_file.exists():
                        prompt_file.unlink()
