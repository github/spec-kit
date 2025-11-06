"""
Unit tests for AI agent detection and validation.
"""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from specify_cli import (
    AGENT_CONFIG,
    check_tool,
)


@pytest.mark.unit
class TestAgentDetection:
    """Tests for AI agent detection."""

    def test_detect_claude_cli(self):
        """Test detection of Claude CLI tool."""
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            assert check_tool("claude") is True

    def test_detect_gemini_cli(self):
        """Test detection of Gemini CLI tool."""
        with patch("shutil.which", return_value="/usr/local/bin/gemini"):
            assert check_tool("gemini") is True

    def test_detect_qwen_cli(self):
        """Test detection of Qwen CLI tool."""
        with patch("shutil.which", return_value="/usr/local/bin/qwen"):
            assert check_tool("qwen") is True

    def test_claude_local_path_priority(self, temp_dir: Path):
        """Test Claude local path is checked before PATH."""
        claude_local = temp_dir / ".claude" / "local" / "claude"
        claude_local.parent.mkdir(parents=True, exist_ok=True)
        claude_local.touch()

        with patch("specify_cli.CLAUDE_LOCAL_PATH", claude_local), \
             patch("shutil.which", return_value=None):
            # Even though which() returns None, local path should be found
            assert check_tool("claude") is True

    def test_claude_local_path_not_file(self, temp_dir: Path):
        """Test Claude local path must be a file."""
        claude_local = temp_dir / ".claude" / "local" / "claude"
        claude_local.parent.mkdir(parents=True, exist_ok=True)
        # Don't create the file

        with patch("specify_cli.CLAUDE_LOCAL_PATH", claude_local), \
             patch("shutil.which", return_value=None):
            assert check_tool("claude") is False

    def test_agent_not_found(self):
        """Test agent not found returns False."""
        with patch("shutil.which", return_value=None):
            assert check_tool("nonexistent-agent") is False


@pytest.mark.unit
class TestAgentConfiguration:
    """Tests for agent configuration structure."""

    def test_all_agents_have_required_fields(self):
        """Test all agents have required configuration fields."""
        required_fields = ["name", "folder", "requires_cli"]

        for agent_key, config in AGENT_CONFIG.items():
            for field in required_fields:
                assert field in config, f"Agent '{agent_key}' missing '{field}' field"

    def test_cli_agents_configuration(self):
        """Test CLI-based agents have correct configuration."""
        cli_agents = [
            "claude", "gemini", "qwen", "opencode", "codex",
            "auggie", "codebuddy", "q", "amp"
        ]

        for agent_key in cli_agents:
            if agent_key in AGENT_CONFIG:
                config = AGENT_CONFIG[agent_key]
                assert config["requires_cli"] is True, f"{agent_key} should require CLI"

    def test_ide_agents_configuration(self):
        """Test IDE-based agents have correct configuration."""
        ide_agents = ["copilot", "cursor-agent", "windsurf", "kilocode", "roo"]

        for agent_key in ide_agents:
            if agent_key in AGENT_CONFIG:
                config = AGENT_CONFIG[agent_key]
                assert config["requires_cli"] is False, f"{agent_key} should not require CLI"

    def test_agent_folders_unique(self):
        """Test each agent has a unique folder."""
        folders = [config["folder"] for config in AGENT_CONFIG.values()]
        assert len(folders) == len(set(folders)), "Agent folders should be unique"

    def test_agent_names_unique(self):
        """Test each agent has a unique display name."""
        names = [config["name"] for config in AGENT_CONFIG.values()]
        assert len(names) == len(set(names)), "Agent names should be unique"

    def test_agent_folder_format(self):
        """Test agent folders follow expected format."""
        for agent_key, config in AGENT_CONFIG.items():
            folder = config["folder"]
            assert folder.startswith("."), f"Agent '{agent_key}' folder should start with '.'"
            assert folder.endswith("/"), f"Agent '{agent_key}' folder should end with '/'"


@pytest.mark.unit
class TestAgentValidation:
    """Tests for agent validation logic."""

    def test_valid_agent_key(self):
        """Test validation of valid agent keys."""
        valid_agents = ["claude", "copilot", "gemini"]

        for agent in valid_agents:
            assert agent in AGENT_CONFIG, f"{agent} should be in AGENT_CONFIG"

    def test_invalid_agent_key(self):
        """Test validation of invalid agent keys."""
        invalid_agents = ["invalid", "unknown", "fake-agent"]

        for agent in invalid_agents:
            assert agent not in AGENT_CONFIG, f"{agent} should not be in AGENT_CONFIG"

    def test_agent_key_case_sensitive(self):
        """Test agent keys are case-sensitive."""
        # AGENT_CONFIG uses lowercase keys
        assert "claude" in AGENT_CONFIG
        assert "Claude" not in AGENT_CONFIG
        assert "CLAUDE" not in AGENT_CONFIG


@pytest.mark.unit
class TestAgentToolRequirements:
    """Tests for agent tool requirement checking."""

    def test_check_tool_with_tracker_updates_status(self):
        """Test check_tool updates tracker with correct status."""
        mock_tracker = Mock()

        with patch("shutil.which", return_value="/usr/bin/tool"):
            check_tool("tool", tracker=mock_tracker)
            mock_tracker.complete.assert_called_once_with("tool", "available")

    def test_check_tool_with_tracker_on_error(self):
        """Test check_tool updates tracker on error."""
        mock_tracker = Mock()

        with patch("shutil.which", return_value=None):
            check_tool("missing-tool", tracker=mock_tracker)
            mock_tracker.error.assert_called_once_with("missing-tool", "not found")

    def test_cli_required_agents_list(self):
        """Test getting list of agents that require CLI."""
        cli_required = [
            agent_key for agent_key, config in AGENT_CONFIG.items()
            if config["requires_cli"]
        ]

        # Verify known CLI agents are in the list
        assert "claude" in cli_required
        assert "gemini" in cli_required
        assert "qwen" in cli_required

        # Verify IDE agents are not in the list
        assert "copilot" not in cli_required
        assert "cursor-agent" not in cli_required

    def test_ide_agents_list(self):
        """Test getting list of IDE-based agents."""
        ide_agents = [
            agent_key for agent_key, config in AGENT_CONFIG.items()
            if not config["requires_cli"]
        ]

        # Verify known IDE agents are in the list
        assert "copilot" in ide_agents
        assert "cursor-agent" in ide_agents
        assert "windsurf" in ide_agents


@pytest.mark.unit
class TestAgentInstallURLs:
    """Tests for agent installation URLs."""

    def test_cli_agents_have_install_urls(self):
        """Test CLI agents have installation URLs."""
        for agent_key, config in AGENT_CONFIG.items():
            if config["requires_cli"]:
                # Should have install_url defined (can be None but should exist)
                assert "install_url" in config, f"CLI agent '{agent_key}' missing install_url"

    def test_install_urls_are_valid_or_none(self):
        """Test install URLs are valid strings or None."""
        for agent_key, config in AGENT_CONFIG.items():
            install_url = config.get("install_url")
            assert install_url is None or isinstance(install_url, str), \
                f"Agent '{agent_key}' install_url should be string or None"

    def test_cli_agents_with_install_urls_format(self):
        """Test CLI agent install URLs are properly formatted."""
        for agent_key, config in AGENT_CONFIG.items():
            if config["requires_cli"] and config.get("install_url"):
                install_url = config["install_url"]
                # Should be HTTP(S) URL
                assert install_url.startswith(("http://", "https://")), \
                    f"Agent '{agent_key}' install_url should be HTTP(S) URL"


@pytest.mark.unit
class TestAgentSelection:
    """Tests for agent selection logic."""

    def test_agent_choices_dict_format(self):
        """Test creating agent choices dictionary."""
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}

        assert isinstance(ai_choices, dict)
        assert len(ai_choices) == len(AGENT_CONFIG)

        # Verify mapping
        assert ai_choices["claude"] == "Claude Code"
        assert ai_choices["copilot"] == "GitHub Copilot"

    def test_default_agent_exists(self):
        """Test default agent (copilot) exists in config."""
        assert "copilot" in AGENT_CONFIG
        assert AGENT_CONFIG["copilot"]["name"] == "GitHub Copilot"

    def test_all_agents_selectable(self):
        """Test all agents can be selected."""
        for agent_key in AGENT_CONFIG.keys():
            # Each agent key should be a valid string
            assert isinstance(agent_key, str)
            assert len(agent_key) > 0


@pytest.mark.unit
class TestAgentFolderStructure:
    """Tests for agent-specific folder structures."""

    def test_agent_folders_dont_overlap(self):
        """Test agent folders don't overlap in naming."""
        folders = [config["folder"] for config in AGENT_CONFIG.values()]

        # Check no folder is a prefix of another
        for i, folder1 in enumerate(folders):
            for j, folder2 in enumerate(folders):
                if i != j:
                    assert not folder2.startswith(folder1[:-1] + "/"), \
                        f"Folders may overlap: {folder1} and {folder2}"

    def test_claude_folder_structure(self):
        """Test Claude agent folder structure."""
        claude_config = AGENT_CONFIG["claude"]
        assert claude_config["folder"] == ".claude/"

    def test_copilot_folder_structure(self):
        """Test Copilot agent folder structure."""
        copilot_config = AGENT_CONFIG["copilot"]
        assert copilot_config["folder"] == ".github/"

    def test_gemini_folder_structure(self):
        """Test Gemini agent folder structure."""
        gemini_config = AGENT_CONFIG["gemini"]
        assert gemini_config["folder"] == ".gemini/"


@pytest.mark.unit
class TestSpecificAgents:
    """Tests for specific agent configurations."""

    def test_claude_configuration(self):
        """Test Claude Code configuration."""
        config = AGENT_CONFIG["claude"]
        assert config["name"] == "Claude Code"
        assert config["folder"] == ".claude/"
        assert config["requires_cli"] is True
        assert config["install_url"] is not None

    def test_copilot_configuration(self):
        """Test GitHub Copilot configuration."""
        config = AGENT_CONFIG["copilot"]
        assert config["name"] == "GitHub Copilot"
        assert config["folder"] == ".github/"
        assert config["requires_cli"] is False
        assert config["install_url"] is None

    def test_gemini_configuration(self):
        """Test Gemini CLI configuration."""
        config = AGENT_CONFIG["gemini"]
        assert config["name"] == "Gemini CLI"
        assert config["folder"] == ".gemini/"
        assert config["requires_cli"] is True
        assert config["install_url"] is not None

    def test_amazon_q_configuration(self):
        """Test Amazon Q configuration."""
        config = AGENT_CONFIG["q"]
        assert config["name"] == "Amazon Q Developer CLI"
        assert config["folder"] == ".amazonq/"
        assert config["requires_cli"] is True
