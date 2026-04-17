"""Tests for the --version CLI flag."""

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
