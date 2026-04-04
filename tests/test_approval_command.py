"""Tests for approval CLI command"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from specify_cli.approval_command import approval_command
import typer


def test_approval_status_no_config():
    """Test approval status when no config exists"""
    with patch("specify_cli.approval_command.ApprovalGatesConfig.load", return_value=None):
        # Create a simple typer app to test the command
        app = typer.Typer()
        app.command()(approval_command)

        runner = CliRunner()
        result = runner.invoke(app, ["--action", "status"])
        assert result.exit_code == 0
        assert "No approval gates configured" in result.stdout


def test_approval_status_with_config():
    """Test approval status with gates configured"""
    # Mock configuration
    mock_config = MagicMock()
    mock_config.gates = {
        "specify": {"enabled": True, "min_approvals": 1},
        "plan": {"enabled": True, "min_approvals": 2},
    }

    with patch("specify_cli.approval_command.ApprovalGatesConfig.load", return_value=mock_config):
        app = typer.Typer()
        app.command()(approval_command)

        runner = CliRunner()
        result = runner.invoke(app, ["--action", "status"])
        assert result.exit_code == 0
        assert "Approval gates enabled" in result.stdout
        assert "specify" in result.stdout
        assert "plan" in result.stdout


def test_approval_default_action():
    """Test approval command with default action (status)"""
    mock_config = MagicMock()
    mock_config.gates = {
        "specify": {"enabled": True, "min_approvals": 1},
    }

    with patch("specify_cli.approval_command.ApprovalGatesConfig.load", return_value=mock_config):
        app = typer.Typer()
        app.command()(approval_command)

        runner = CliRunner()
        # Invoke without --action (should default to status)
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Approval gates enabled" in result.stdout
