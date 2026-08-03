"""Tests for CLI version reporting."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


class TestVersionFlag:
    """Test --version / -V flag on the root command."""

    def test_version_long_flag(self):
        """specify --version prints version and exits 0."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "specify 1.2.3" in result.output

    def test_version_short_flag(self):
        """specify -V prints version and exits 0."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "specify 1.2.3" in result.output

    def test_version_flag_takes_precedence_over_subcommand(self):
        """--version should work even when a subcommand follows."""
        with patch("specify_cli.get_speckit_version", return_value="0.7.2"):
            result = runner.invoke(app, ["--version", "init"])
        assert result.exit_code == 0
        assert "specify 0.7.2" in result.output


class TestVersionCommand:
    """Test the `specify version` subcommand."""

    def test_version_features_text(self):
        """specify version --features prints local capability flags."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--features"])

        assert result.exit_code == 0
        assert "Spec Kit CLI: 1.2.3" in result.output
        assert "Features:" in result.output
        assert "- controlled multi install integrations: yes" in result.output
        assert "- integration use command: yes" in result.output
        assert "- self check command: yes" in result.output

    def test_version_features_json(self):
        """specify version --features --json prints machine-readable capabilities."""
        with patch("specify_cli.get_speckit_version", return_value="1.2.3"):
            result = runner.invoke(app, ["version", "--features", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {
            "version": "1.2.3",
            "features": {
                "controlled_multi_install_integrations": True,
                "integration_use_command": True,
                "multi_install_safe_registry_metadata": True,
                "integration_upgrade_command": True,
                "self_check_command": True,
                "workflow_catalog": True,
                "bundled_templates": True,
            },
        }

    def test_version_json_requires_features(self):
        """specify version --json is rejected until a JSON surface exists."""
        result = runner.invoke(app, ["version", "--json"])

        assert result.exit_code != 0
        assert "--json requires --features" in result.output
