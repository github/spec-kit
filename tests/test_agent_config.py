"""
Unit tests for agent_config.py module.

Tests cover:
- AGENT_CONFIG structure validation
- All required fields present for every agent
- Directory structure conventions
- Command format validation
- CLI tool validation logic
"""

import pytest
from infrakit_cli.agent_config import AGENT_CONFIG


class TestAgentConfig:
    """Test the AGENT_CONFIG dictionary structure and contents."""

    def test_all_agents_have_required_fields(self):
        """Every agent entry must have all required fields."""
        required_fields = [
            "name",
            "folder",
            "commands_subdir",
            "install_url",
            "requires_cli",
            "command_format",
            "command_args",
            "command_extension",
        ]

        for agent_key, config in AGENT_CONFIG.items():
            for field in required_fields:
                assert field in config, (
                    f"Agent '{agent_key}' missing required field '{field}'"
                )
                # install_url and folder can be None for IDE-based/generic agents
                if field not in ("install_url", "folder"):
                    assert config[field] is not None, (
                        f"Agent '{agent_key}' field '{field}' is None"
                    )

    def test_agent_folder_format(self):
        """Agent folder should start with '.' and end with '/' (if not None)."""
        for agent_key, config in AGENT_CONFIG.items():
            folder = config["folder"]
            if folder is not None:
                assert folder.startswith("."), (
                    f"Agent '{agent_key}' folder '{folder}' doesn't start with '.'"
                )
                assert folder.endswith("/"), (
                    f"Agent '{agent_key}' folder '{folder}' doesn't end with '/'"
                )

    def test_commands_subdir_valid_values(self):
        """Commands subdir should be one of the known valid values."""
        valid_subdirs = [
            "commands",
            "agents",
            "workflows",
            "prompts",
            "command",
            "rules",
        ]

        for agent_key, config in AGENT_CONFIG.items():
            subdir = config["commands_subdir"]
            assert subdir in valid_subdirs, (
                f"Agent '{agent_key}' has unknown commands_subdir '{subdir}'"
            )

    def test_command_format_valid(self):
        """Command format must be one of the recognised renderer formats."""
        valid_formats = ["markdown", "toml", "agent.md"]

        for agent_key, config in AGENT_CONFIG.items():
            fmt = config["command_format"]
            assert fmt in valid_formats, (
                f"Agent '{agent_key}' has invalid command_format '{fmt}'"
            )

    def test_command_extension_matches_format(self):
        """Command extension should match the declared format."""
        for agent_key, config in AGENT_CONFIG.items():
            fmt = config["command_format"]
            ext = config["command_extension"]

            if fmt == "markdown":
                assert ext == ".md", (
                    f"Agent '{agent_key}' is markdown but has extension '{ext}'"
                )
            elif fmt == "toml":
                assert ext == ".toml", (
                    f"Agent '{agent_key}' is toml but has extension '{ext}'"
                )
            elif fmt == "agent.md":
                assert ext == ".agent.md", (
                    f"Agent '{agent_key}' is agent.md but has extension '{ext}'"
                )

    def test_command_args_placeholder(self):
        """Command args should use correct placeholder pattern."""
        for agent_key, config in AGENT_CONFIG.items():
            fmt = config["command_format"]
            args = config["command_args"]

            if fmt == "markdown":
                assert args == "$ARGUMENTS", (
                    f"Agent '{agent_key}' (markdown) has wrong args placeholder"
                )
            elif fmt == "toml":
                assert args == "{{args}}", (
                    f"Agent '{agent_key}' (toml) has wrong args placeholder"
                )

    def test_requires_cli_boolean(self):
        """requires_cli must be a boolean."""
        for agent_key, config in AGENT_CONFIG.items():
            assert isinstance(config["requires_cli"], bool), (
                f"Agent '{agent_key}' requires_cli is not boolean"
            )

    def test_install_url_consistency(self):
        """IDE-based agents should have None install_url, CLI agents should have URL."""
        for agent_key, config in AGENT_CONFIG.items():
            requires_cli = config["requires_cli"]
            install_url = config["install_url"]

            if requires_cli:
                assert install_url is not None, (
                    f"Agent '{agent_key}' requires CLI but has no install URL"
                )
                assert install_url.startswith("http"), (
                    f"Agent '{agent_key}' install URL is not valid HTTP URL"
                )
            else:
                # IDE-based agents can have None or URL
                pass

    def test_folder_and_commands_subdir_combination(self):
        """Verify known agent directory patterns are correct."""
        expected_patterns = {
            "claude": (".claude/", "commands"),
            "gemini": (".gemini/", "commands"),
            "copilot": (".github/", "agents"),
            "cursor-agent": (".cursor/", "commands"),
            "qwen": (".qwen/", "commands"),
            "opencode": (".opencode/", "command"),
            "codex": (".codex/", "prompts"),
            "windsurf": (".windsurf/", "workflows"),
            "kilocode": (".kilocode/", "workflows"),
            "auggie": (".augment/", "commands"),
            "q": (".amazonq/", "prompts"),
        }

        for agent_key, (expected_folder, expected_subdir) in expected_patterns.items():
            if agent_key in AGENT_CONFIG:
                config = AGENT_CONFIG[agent_key]
                assert config["folder"] == expected_folder, (
                    f"Agent '{agent_key}' folder mismatch"
                )
                assert config["commands_subdir"] == expected_subdir, (
                    f"Agent '{agent_key}' commands_subdir mismatch"
                )

    def test_no_duplicate_folder_names(self):
        """No two agents should use the same folder."""
        folders = []
        for agent_key, config in AGENT_CONFIG.items():
            folder = config["folder"]
            assert folder not in folders, (
                f"Duplicate folder '{folder}' used by multiple agents"
            )
            folders.append(folder)

    def test_generic_agent_config(self):
        """Generic agent has special configuration."""
        assert "generic" in AGENT_CONFIG
        generic = AGENT_CONFIG["generic"]
        assert generic["requires_cli"] is False
        assert generic["command_format"] == "markdown"
        assert generic["command_extension"] == ".md"

    @pytest.mark.parametrize("agent_key", list(AGENT_CONFIG.keys()))
    def test_agent_configuration_is_consistent(self, agent_key):
        """Run general consistency checks for every agent."""
        config = AGENT_CONFIG[agent_key]

        # Name should be non-empty string
        assert isinstance(config["name"], str)
        assert len(config["name"]) > 0

        # Folder should be at least 2 chars (like .x/) if not None
        if config["folder"] is not None:
            assert len(config["folder"]) >= 3

        # Command args should be non-empty
        assert len(config["command_args"]) > 0

        # Command extension should start with .
        assert config["command_extension"].startswith(".")

    def test_agent_keys_are_cli_names(self):
        """Agent keys should match actual CLI tool names (no shorthand)."""
        # These are known CLI tool names - verify they're used as keys
        known_cli_tools = [
            "claude",
            "gemini",
            "qwen",
            "opencode",
            "codebuddy",
            "qodercli",
            "q",
            "amp",
            "shai",
        ]

        for tool in known_cli_tools:
            if tool in AGENT_CONFIG:
                assert AGENT_CONFIG[tool]["requires_cli"] is True, (
                    f"Tool '{tool}' should have requires_cli=True"
                )

        # Verify no shorthand keys exist (like "cursor" instead of "cursor-agent")
        assert "cursor" not in AGENT_CONFIG, (
            "Should use 'cursor-agent' as key, not shorthand 'cursor'"
        )
        assert "amazonq" not in AGENT_CONFIG, "Should use 'q' as key for Amazon Q"
