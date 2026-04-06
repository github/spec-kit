"""
Unit tests for iac_config.py module.

Tests cover:
- IAC_CONFIG structure validation
- get_iac_choices() function
- get_iac_commands() function
"""

import pytest
from infrakit_cli.iac_config import IAC_CONFIG, get_iac_choices, get_iac_commands


class TestIacConfig:
    """Test the IAC_CONFIG dictionary and helper functions."""

    def test_iac_config_structure(self):
        """Every IaC tool entry must have all required fields."""
        required_fields = [
            "name",
            "description",
            "requires_tools",
            "optional_tools",
            "output_format",
            "resource_term",
            "generic_commands",
            "iac_commands",
        ]

        for tool_key, config in IAC_CONFIG.items():
            for field in required_fields:
                assert field in config, (
                    f"IaC tool '{tool_key}' missing required field '{field}'"
                )

    def test_crossplane_configuration(self):
        """Crossplane configuration should be complete and correct."""
        assert "crossplane" in IAC_CONFIG
        crossplane = IAC_CONFIG["crossplane"]

        assert crossplane["name"] == "Crossplane"
        assert crossplane["requires_tools"] == ["kubectl"]
        assert crossplane["optional_tools"] == ["crossplane", "docker"]
        assert crossplane["output_format"] == "yaml"
        assert crossplane["resource_term"] == "composition"

        # Verify command lists
        assert len(crossplane["generic_commands"]) > 0
        assert len(crossplane["iac_commands"]) > 0
        assert "setup" in crossplane["generic_commands"]
        assert "new_composition" in crossplane["iac_commands"]

    def test_get_iac_choices(self):
        """get_iac_choices returns correct dictionary format."""
        choices = get_iac_choices()

        assert isinstance(choices, dict)
        assert len(choices) == len(IAC_CONFIG)

        for key, name in choices.items():
            assert key in IAC_CONFIG
            assert name == IAC_CONFIG[key]["name"]

    def test_get_iac_commands_existing_tool(self):
        """get_iac_commands returns combined command list for existing tool."""
        commands = get_iac_commands("crossplane")

        assert isinstance(commands, list)
        expected_length = len(IAC_CONFIG["crossplane"]["generic_commands"]) + len(
            IAC_CONFIG["crossplane"]["iac_commands"]
        )
        assert len(commands) == expected_length

        # Verify all commands are present
        for cmd in IAC_CONFIG["crossplane"]["generic_commands"]:
            assert cmd in commands
        for cmd in IAC_CONFIG["crossplane"]["iac_commands"]:
            assert cmd in commands

    def test_get_iac_commands_unknown_tool(self):
        """get_iac_commands returns empty list for unknown tool."""
        commands = get_iac_commands("nonexistent-tool")
        assert commands == []

    def test_get_iac_commands_empty_string(self):
        """get_iac_commands handles empty string input gracefully."""
        commands = get_iac_commands("")
        assert commands == []

    def test_all_iac_tools_have_unique_names(self):
        """All IaC tools should have unique display names."""
        names = []
        for tool_key, config in IAC_CONFIG.items():
            name = config["name"]
            assert name not in names, f"Duplicate display name '{name}' for IaC tool"
            names.append(name)

    def test_command_lists_no_duplicates(self):
        """No duplicate commands in generic_commands or iac_commands."""
        for tool_key, config in IAC_CONFIG.items():
            generic = config["generic_commands"]
            iac = config["iac_commands"]

            assert len(generic) == len(set(generic)), (
                f"Duplicate commands in {tool_key} generic_commands"
            )
            assert len(iac) == len(set(iac)), (
                f"Duplicate commands in {tool_key} iac_commands"
            )

            # No overlap between generic and iac commands
            overlap = set(generic) & set(iac)
            assert len(overlap) == 0, f"Command overlap in {tool_key}: {overlap}"

    def test_output_format_valid(self):
        """Output format should be one of known valid formats."""
        valid_formats = ["yaml", "hcl", "json", "code"]

        for tool_key, config in IAC_CONFIG.items():
            fmt = config["output_format"]
            assert fmt in valid_formats, (
                f"IaC tool '{tool_key}' has invalid output_format '{fmt}'"
            )

    def test_tool_lists_are_lists(self):
        """requires_tools and optional_tools must be lists."""
        for tool_key, config in IAC_CONFIG.items():
            assert isinstance(config["requires_tools"], list), (
                f"{tool_key} requires_tools is not a list"
            )
            assert isinstance(config["optional_tools"], list), (
                f"{tool_key} optional_tools is not a list"
            )

    @pytest.mark.parametrize("tool_key", IAC_CONFIG.keys())
    def test_iac_tool_consistency(self, tool_key):
        """General consistency checks for every IaC tool."""
        config = IAC_CONFIG[tool_key]

        # Name should be non-empty
        assert isinstance(config["name"], str)
        assert len(config["name"]) > 0

        # Description should be non-empty
        assert isinstance(config["description"], str)
        assert len(config["description"]) > 0

        # Resource term should be non-empty
        assert isinstance(config["resource_term"], str)
        assert len(config["resource_term"]) > 0
