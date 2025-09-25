"""
Simple tests for Specify CLI
"""
import pytest
from typer.testing import CliRunner
from specify_cli import app


def test_check_command():
    """Test that check command works"""
    runner = CliRunner()
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Check Available Tools" in result.output


def test_init_command_help():
    """Test that init command shows help"""
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a new Specify project" in result.output


def test_init_command_validation():
    """Test init command validation"""
    runner = CliRunner()
    
    # Test conflicting arguments
    result = runner.invoke(app, ["init", "test-project", "--here"])
    assert result.exit_code == 1
    assert "Cannot specify both project name and --here flag" in result.output
    
    # Test missing arguments
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "Must specify either a project name or use --here flag" in result.output


def test_ai_choices():
    """Test that AI choices are properly defined"""
    from specify_cli import AI_CHOICES
    
    expected_agents = ["copilot", "claude", "gemini", "cursor", "qwen", "opencode"]
    
    for agent in expected_agents:
        assert agent in AI_CHOICES
        assert AI_CHOICES[agent] is not None


def test_script_type_choices():
    """Test that script type choices are properly defined"""
    from specify_cli import SCRIPT_TYPE_CHOICES
    
    assert "sh" in SCRIPT_TYPE_CHOICES
    assert "ps" in SCRIPT_TYPE_CHOICES
    assert SCRIPT_TYPE_CHOICES["sh"] == "POSIX Shell (bash/zsh)"
    assert SCRIPT_TYPE_CHOICES["ps"] == "PowerShell"
