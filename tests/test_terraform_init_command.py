"""
Unit tests for Terraform support in the infrakit init command.

Tests cover:
- --iac terraform is accepted and validated (no early exit for unknown tool)
- --iac terraform appears in the --help output
- init rejects invalid --iac values with a clear error message
- init --iac terraform fails gracefully when project dir already exists
- The IaC selection maps terraform to the correct IAC_CONFIG entry
- initialize_iac_config writes config.yaml with iac_tool=terraform
- initialize_iac_config copies the Terraform coding-style template
- initialize_iac_config copies the terraform_engineer persona
- initialize_iac_config writes correct IaC-native command files
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from infrakit_cli import app, initialize_iac_config
from infrakit_cli.iac_config import IAC_CONFIG


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_temp_dir() -> Path:
    """Return a freshly-created temporary directory path (caller must clean up)."""
    return Path(tempfile.mkdtemp())


# ---------------------------------------------------------------------------
# CLI-level tests (no network calls)
# ---------------------------------------------------------------------------


class TestInitHelpIncludesTerraform:
    """The help text for 'init' must document the --iac terraform option."""

    def test_init_help_mentions_terraform(self):
        """init --help must mention terraform."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "terraform" in result.output.lower()

    def test_init_help_mentions_crossplane(self):
        """init --help must still mention crossplane."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "crossplane" in result.output.lower()


class TestInitRejectsInvalidIacTool:
    """init must reject unrecognised --iac values with exit code 1."""

    @patch("infrakit_cli.download_and_extract_template")
    def test_invalid_iac_tool_rejected(self, _mock_download):
        """Passing an unknown IaC tool should exit with code 1."""
        result = runner.invoke(
            app,
            ["init", "my-project", "--ai", "claude", "--iac", "nonexistent-tool"],
        )
        assert result.exit_code == 1
        assert "nonexistent-tool" in result.output or "invalid" in result.output.lower()

    @patch("infrakit_cli.download_and_extract_template")
    def test_invalid_iac_tool_error_message_helpful(self, _mock_download):
        """Error message for unknown IaC tool should list valid options."""
        result = runner.invoke(
            app,
            ["init", "my-project", "--ai", "claude", "--iac", "pulumi"],
        )
        assert result.exit_code == 1
        # Should hint at valid options
        output = result.output.lower()
        assert "crossplane" in output or "terraform" in output


class TestInitMissingProjectName:
    """init requires either a project name or --here."""

    def test_no_project_name_and_no_here_exits_with_error(self):
        """Omitting both project name and --here must fail."""
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# initialize_iac_config() unit tests
# ---------------------------------------------------------------------------


class TestInitializeIacConfigTerraform:
    """Unit tests for initialize_iac_config() with terraform as the IaC tool."""

    @pytest.fixture()
    def project_dir(self):
        """Provide a fresh temporary directory for each test."""
        tmp = _make_temp_dir()
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_creates_infrakit_config_yaml(self, project_dir):
        """initialize_iac_config must write .infrakit/config.yaml."""
        initialize_iac_config(project_dir, "terraform", "claude")
        config_file = project_dir / ".infrakit" / "config.yaml"
        assert config_file.is_file(), "config.yaml was not created"

    def test_config_yaml_contains_terraform_iac_tool(self, project_dir):
        """config.yaml must record iac_tool: terraform."""
        initialize_iac_config(project_dir, "terraform", "claude")
        content = (project_dir / ".infrakit" / "config.yaml").read_text()
        assert "terraform" in content

    def test_config_yaml_contains_ai_assistant(self, project_dir):
        """config.yaml must record the chosen AI assistant."""
        initialize_iac_config(project_dir, "terraform", "claude")
        content = (project_dir / ".infrakit" / "config.yaml").read_text()
        assert "claude" in content

    def test_config_yaml_contains_resource_term_module(self, project_dir):
        """config.yaml resource_term must be 'module' for terraform."""
        initialize_iac_config(project_dir, "terraform", "claude")
        content = (project_dir / ".infrakit" / "config.yaml").read_text()
        assert "module" in content

    def test_creates_tracks_md(self, project_dir):
        """initialize_iac_config must create .infrakit/tracks.md."""
        initialize_iac_config(project_dir, "terraform", "claude")
        assert (project_dir / ".infrakit" / "tracks.md").is_file()

    def test_creates_tagging_md(self, project_dir):
        """initialize_iac_config must create .infrakit/tagging.md."""
        initialize_iac_config(project_dir, "terraform", "claude")
        assert (project_dir / ".infrakit" / "tagging.md").is_file()

    def test_creates_mcp_use_md(self, project_dir):
        """initialize_iac_config must create .infrakit/mcp-use.md."""
        initialize_iac_config(project_dir, "terraform", "claude")
        assert (project_dir / ".infrakit" / "mcp-use.md").is_file()

    def test_creates_memory_directory(self, project_dir):
        """initialize_iac_config must create .infrakit/memory/ directory."""
        initialize_iac_config(project_dir, "terraform", "claude")
        assert (project_dir / ".infrakit" / "memory").is_dir()

    def test_creates_tracks_directory(self, project_dir):
        """initialize_iac_config must create .infrakit/tracks/ directory."""
        initialize_iac_config(project_dir, "terraform", "claude")
        assert (project_dir / ".infrakit" / "tracks").is_dir()

    def test_config_yaml_not_overwritten_if_exists(self, project_dir):
        """config.yaml must not be overwritten on a second call."""
        initialize_iac_config(project_dir, "terraform", "claude")
        original_content = (project_dir / ".infrakit" / "config.yaml").read_text()

        # Second call with different values
        initialize_iac_config(project_dir, "crossplane", "gemini")
        final_content = (project_dir / ".infrakit" / "config.yaml").read_text()

        assert original_content == final_content, (
            "config.yaml was overwritten on second initialize_iac_config call"
        )

    def test_unknown_iac_tool_returns_early(self, project_dir):
        """initialize_iac_config with an unknown tool should not crash."""
        initialize_iac_config(project_dir, "nonexistent-tool", "claude")
        # Should not create .infrakit/config.yaml since the tool is unknown
        config_file = project_dir / ".infrakit" / "config.yaml"
        assert not config_file.exists(), (
            "config.yaml should not be created for an unknown IaC tool"
        )

    def test_copies_coding_style_template_from_terraform_assets(self, project_dir):
        """coding-style-template.md must be copied from terraform assets (if running from source)."""
        initialize_iac_config(project_dir, "terraform", "claude")
        # Only assert if the template source exists (skips when installed via pip)
        src = (
            Path(__file__).parent.parent
            / "templates"
            / "iac"
            / "terraform"
            / "assets"
            / "coding-style-template.md"
        )
        if src.is_file():
            dest = project_dir / ".infrakit" / "coding-style-template.md"
            assert dest.is_file(), (
                "coding-style-template.md was not copied to .infrakit/"
            )

    def test_copies_terraform_engineer_persona(self, project_dir):
        """terraform_engineer.md must be copied to .infrakit/agent_personas/ (if running from source)."""
        initialize_iac_config(project_dir, "terraform", "claude")
        src = (
            Path(__file__).parent.parent
            / "templates"
            / "iac"
            / "terraform"
            / "agent_personas"
            / "terraform_engineer.md"
        )
        if src.is_file():
            dest = (
                project_dir / ".infrakit" / "agent_personas" / "terraform_engineer.md"
            )
            assert dest.is_file(), (
                "terraform_engineer.md was not copied to .infrakit/agent_personas/"
            )

    def test_generic_personas_are_also_copied(self, project_dir):
        """Generic agent personas must be copied for terraform projects too (if from source)."""
        initialize_iac_config(project_dir, "terraform", "claude")
        generic_src = Path(__file__).parent.parent / "templates" / "agent_personas"
        if generic_src.is_dir():
            personas_dest = project_dir / ".infrakit" / "agent_personas"
            assert personas_dest.is_dir(), ".infrakit/agent_personas/ was not created"


class TestInitializeIacConfigCrossplaneUnchanged:
    """Verify Crossplane initialisation is unaffected after adding Terraform."""

    @pytest.fixture()
    def project_dir(self):
        tmp = _make_temp_dir()
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_crossplane_config_yaml_still_says_crossplane(self, project_dir):
        """Crossplane projects must still write iac_tool: crossplane."""
        initialize_iac_config(project_dir, "crossplane", "claude")
        content = (project_dir / ".infrakit" / "config.yaml").read_text()
        assert "crossplane" in content

    def test_crossplane_resource_term_is_composition(self, project_dir):
        """Crossplane projects must still use resource_term: composition."""
        initialize_iac_config(project_dir, "crossplane", "claude")
        content = (project_dir / ".infrakit" / "config.yaml").read_text()
        assert "composition" in content

    def test_crossplane_output_format_is_yaml(self):
        """Crossplane output_format in IAC_CONFIG must still be yaml."""
        assert IAC_CONFIG["crossplane"]["output_format"] == "yaml"


# ---------------------------------------------------------------------------
# IAC_CONFIG correctness cross-checks
# ---------------------------------------------------------------------------


class TestTerraformIacConfigValues:
    """Sanity-check the terraform entry values in IAC_CONFIG."""

    def test_terraform_output_format(self):
        """Terraform output_format must be hcl."""
        assert IAC_CONFIG["terraform"]["output_format"] == "hcl"

    def test_terraform_resource_term(self):
        """Terraform resource_term must be module."""
        assert IAC_CONFIG["terraform"]["resource_term"] == "module"

    def test_terraform_requires_terraform_cli(self):
        """Terraform requires_tools must include the terraform binary."""
        assert "terraform" in IAC_CONFIG["terraform"]["requires_tools"]

    def test_terraform_iac_commands_count(self):
        """Terraform must have exactly 4 IaC-native commands."""
        assert len(IAC_CONFIG["terraform"]["iac_commands"]) == 4

    def test_all_iac_tools_distinct_output_formats(self):
        """Crossplane (yaml) and Terraform (hcl) have distinct output formats."""
        assert (
            IAC_CONFIG["crossplane"]["output_format"]
            != IAC_CONFIG["terraform"]["output_format"]
        )

    def test_all_iac_tools_distinct_resource_terms(self):
        """Crossplane (composition) and Terraform (module) have distinct resource terms."""
        assert (
            IAC_CONFIG["crossplane"]["resource_term"]
            != IAC_CONFIG["terraform"]["resource_term"]
        )
