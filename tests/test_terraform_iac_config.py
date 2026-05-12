"""
Unit tests for Terraform IaC tool support in iac_config.py.

Tests cover:
- Terraform entry present and correctly structured in IAC_CONFIG
- Terraform-specific field values (output_format, resource_term, requires_tools)
- Terraform IaC commands (create_terraform_code, update_terraform_code)
- get_iac_choices() includes terraform
- get_iac_commands() returns correct commands for terraform
- Terraform and Crossplane can coexist without interference
"""

import pytest
from infrakit_cli.iac_config import IAC_CONFIG, get_iac_choices, get_iac_commands


class TestTerraformIacConfig:
    """Tests for the Terraform entry in IAC_CONFIG."""

    def test_terraform_present_in_iac_config(self):
        """Terraform must be a key in IAC_CONFIG."""
        assert "terraform" in IAC_CONFIG, "terraform key missing from IAC_CONFIG"

    def test_terraform_has_all_required_fields(self):
        """Terraform config must contain every required field."""
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
        terraform = IAC_CONFIG["terraform"]
        for field in required_fields:
            assert field in terraform, (
                f"terraform config missing required field '{field}'"
            )

    def test_terraform_name(self):
        """Terraform display name should be 'Terraform'."""
        assert IAC_CONFIG["terraform"]["name"] == "Terraform"

    def test_terraform_description_non_empty(self):
        """Terraform description must be a non-empty string."""
        desc = IAC_CONFIG["terraform"]["description"]
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_terraform_requires_tools(self):
        """Terraform requires the terraform CLI."""
        assert IAC_CONFIG["terraform"]["requires_tools"] == ["terraform"]

    def test_terraform_optional_tools_is_list(self):
        """optional_tools must be a list (can be empty)."""
        optional = IAC_CONFIG["terraform"]["optional_tools"]
        assert isinstance(optional, list)

    def test_terraform_output_format_is_hcl(self):
        """Terraform output format must be 'hcl'."""
        assert IAC_CONFIG["terraform"]["output_format"] == "hcl"

    def test_terraform_resource_term_is_module(self):
        """Terraform resource term must be 'module'."""
        assert IAC_CONFIG["terraform"]["resource_term"] == "module"

    def test_terraform_generic_commands_present(self):
        """Terraform generic commands list must be non-empty."""
        generic = IAC_CONFIG["terraform"]["generic_commands"]
        assert isinstance(generic, list)
        assert len(generic) > 0

    def test_terraform_generic_commands_include_core_workflow(self):
        """Terraform must include the core spec-driven workflow generic commands."""
        expected = [
            "setup",
            "status",
            "analyze",
            "architect-review",
            "security-review",
        ]
        generic = IAC_CONFIG["terraform"]["generic_commands"]
        for cmd in expected:
            assert cmd in generic, f"terraform generic_commands missing '{cmd}'"
        # implement is IaC-specific, not generic
        assert "implement" not in generic, "implement must be in iac_commands, not generic_commands"
        assert "implement" in IAC_CONFIG["terraform"]["iac_commands"]

    def test_terraform_iac_commands_present(self):
        """Terraform IaC-native commands list must be non-empty."""
        iac = IAC_CONFIG["terraform"]["iac_commands"]
        assert isinstance(iac, list)
        assert len(iac) > 0

    def test_terraform_has_create_terraform_code_command(self):
        """create_terraform_code must be in terraform iac_commands."""
        assert "create_terraform_code" in IAC_CONFIG["terraform"]["iac_commands"]

    def test_terraform_has_update_terraform_code_command(self):
        """update_terraform_code must be in terraform iac_commands."""
        assert "update_terraform_code" in IAC_CONFIG["terraform"]["iac_commands"]

    def test_terraform_has_review_command(self):
        """review must be in terraform iac_commands."""
        assert "review" in IAC_CONFIG["terraform"]["iac_commands"]

    def test_terraform_has_plan_command(self):
        """plan must be in terraform iac_commands."""
        assert "plan" in IAC_CONFIG["terraform"]["iac_commands"]

    def test_terraform_iac_commands_no_duplicates(self):
        """terraform iac_commands must have no duplicate entries."""
        iac = IAC_CONFIG["terraform"]["iac_commands"]
        assert len(iac) == len(set(iac)), "terraform iac_commands contains duplicates"

    def test_terraform_generic_commands_no_duplicates(self):
        """terraform generic_commands must have no duplicate entries."""
        generic = IAC_CONFIG["terraform"]["generic_commands"]
        assert len(generic) == len(set(generic)), (
            "terraform generic_commands contains duplicates"
        )

    def test_terraform_no_overlap_between_generic_and_iac_commands(self):
        """terraform generic_commands and iac_commands must not overlap."""
        generic = set(IAC_CONFIG["terraform"]["generic_commands"])
        iac = set(IAC_CONFIG["terraform"]["iac_commands"])
        overlap = generic & iac
        assert len(overlap) == 0, f"terraform command overlap: {overlap}"

    def test_terraform_uses_crossplane_generic_commands(self):
        """Terraform generic commands should match Crossplane's (same workflow)."""
        terraform_generic = set(IAC_CONFIG["terraform"]["generic_commands"])
        crossplane_generic = set(IAC_CONFIG["crossplane"]["generic_commands"])
        assert terraform_generic == crossplane_generic, (
            "Terraform and Crossplane should share the same generic workflow commands"
        )

    def test_terraform_iac_commands_differ_from_crossplane(self):
        """Terraform IaC-native commands must differ from Crossplane's."""
        terraform_iac = set(IAC_CONFIG["terraform"]["iac_commands"])
        crossplane_iac = set(IAC_CONFIG["crossplane"]["iac_commands"])
        assert terraform_iac != crossplane_iac, (
            "Terraform and Crossplane should have different IaC-native commands"
        )

    def test_terraform_does_not_use_composition_commands(self):
        """Terraform must not reference Crossplane-specific composition commands."""
        terraform_iac = IAC_CONFIG["terraform"]["iac_commands"]
        assert "new_composition" not in terraform_iac
        assert "update_composition" not in terraform_iac

    def test_crossplane_does_not_use_terraform_commands(self):
        """Crossplane must not reference Terraform-specific commands."""
        crossplane_iac = IAC_CONFIG["crossplane"]["iac_commands"]
        assert "create_terraform_code" not in crossplane_iac
        assert "update_terraform_code" not in crossplane_iac


class TestGetIacChoicesWithTerraform:
    """Tests for get_iac_choices() after Terraform was added."""

    def test_get_iac_choices_includes_terraform(self):
        """get_iac_choices must include terraform."""
        choices = get_iac_choices()
        assert "terraform" in choices

    def test_get_iac_choices_terraform_display_name(self):
        """get_iac_choices terraform value must be 'Terraform'."""
        choices = get_iac_choices()
        assert choices["terraform"] == "Terraform"

    def test_get_iac_choices_includes_crossplane(self):
        """get_iac_choices must still include crossplane."""
        choices = get_iac_choices()
        assert "crossplane" in choices

    def test_get_iac_choices_returns_all_configured_tools(self):
        """get_iac_choices must return an entry for every key in IAC_CONFIG."""
        choices = get_iac_choices()
        assert len(choices) == len(IAC_CONFIG)
        for key in IAC_CONFIG:
            assert key in choices

    def test_get_iac_choices_values_match_names(self):
        """get_iac_choices values must match the name field in IAC_CONFIG."""
        choices = get_iac_choices()
        for key, display_name in choices.items():
            assert display_name == IAC_CONFIG[key]["name"]


class TestGetIacCommandsWithTerraform:
    """Tests for get_iac_commands() with terraform as input."""

    def test_get_iac_commands_terraform_returns_list(self):
        """get_iac_commands('terraform') must return a list."""
        result = get_iac_commands("terraform")
        assert isinstance(result, list)

    def test_get_iac_commands_terraform_non_empty(self):
        """get_iac_commands('terraform') must return a non-empty list."""
        result = get_iac_commands("terraform")
        assert len(result) > 0

    def test_get_iac_commands_terraform_includes_create_command(self):
        """get_iac_commands('terraform') must contain create_terraform_code."""
        assert "create_terraform_code" in get_iac_commands("terraform")

    def test_get_iac_commands_terraform_includes_update_command(self):
        """get_iac_commands('terraform') must contain update_terraform_code."""
        assert "update_terraform_code" in get_iac_commands("terraform")

    def test_get_iac_commands_terraform_includes_plan(self):
        """get_iac_commands('terraform') must contain plan."""
        assert "plan" in get_iac_commands("terraform")

    def test_get_iac_commands_terraform_includes_review(self):
        """get_iac_commands('terraform') must contain review."""
        assert "review" in get_iac_commands("terraform")

    def test_get_iac_commands_terraform_includes_setup(self):
        """get_iac_commands('terraform') must contain setup (generic)."""
        assert "setup" in get_iac_commands("terraform")

    def test_get_iac_commands_terraform_total_count(self):
        """get_iac_commands('terraform') count equals generic + iac commands."""
        expected = len(IAC_CONFIG["terraform"]["generic_commands"]) + len(
            IAC_CONFIG["terraform"]["iac_commands"]
        )
        assert len(get_iac_commands("terraform")) == expected

    def test_get_iac_commands_order_generic_before_iac(self):
        """generic commands must appear before IaC-native commands in the result."""
        commands = get_iac_commands("terraform")
        generic_cmds = IAC_CONFIG["terraform"]["generic_commands"]
        iac_cmds = IAC_CONFIG["terraform"]["iac_commands"]

        # The first N entries must be generic commands
        n = len(generic_cmds)
        assert commands[:n] == generic_cmds

        # The remaining entries must be IaC commands
        assert commands[n:] == iac_cmds

    def test_get_iac_commands_crossplane_unchanged(self):
        """Adding terraform must not alter get_iac_commands('crossplane') output."""
        crossplane_commands = get_iac_commands("crossplane")
        assert "new_composition" in crossplane_commands
        assert "update_composition" in crossplane_commands
        assert "create_terraform_code" not in crossplane_commands

    @pytest.mark.parametrize("tool_key", IAC_CONFIG.keys())
    def test_get_iac_commands_all_tools_return_lists(self, tool_key):
        """get_iac_commands must return a list for every configured tool."""
        result = get_iac_commands(tool_key)
        assert isinstance(result, list)
        assert len(result) > 0
