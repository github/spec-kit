"""Tests for approval gates functionality"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from specify_cli.approval_gates import ApprovalGatesConfig


def test_approval_gates_load_exists():
    """Test loading approval gates when config exists"""
    yaml_content = """
approval_gates:
  specify:
    enabled: true
    min_approvals: 1
  plan:
    enabled: true
    min_approvals: 2
"""
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        with patch("pathlib.Path.exists", return_value=True):
            config = ApprovalGatesConfig.load()
            assert config is not None
            assert "specify" in config.gates


def test_approval_gates_load_not_exists():
    """Test loading when no approval gates configured"""
    with patch("pathlib.Path.exists", return_value=False):
        config = ApprovalGatesConfig.load()
        assert config is None  # This is expected behavior


def test_is_phase_gated_enabled():
    """Test checking if phase is gated (enabled)"""
    config_data = {
        "approval_gates": {
            "specify": {"enabled": True, "min_approvals": 1},
            "plan": {"enabled": False},
        }
    }
    config = ApprovalGatesConfig(config_data)
    assert config.is_phase_gated("specify") == True
    assert config.is_phase_gated("plan") == False


def test_get_phase_gate():
    """Test retrieving gate configuration for phase"""
    config_data = {
        "approval_gates": {
            "specify": {"enabled": True, "min_approvals": 1},
        }
    }
    config = ApprovalGatesConfig(config_data)
    gate = config.get_phase_gate("specify")
    assert gate is not None
    assert gate.get("min_approvals") == 1


def test_get_phase_gate_disabled():
    """Test getting gate for disabled phase"""
    config_data = {
        "approval_gates": {
            "plan": {"enabled": False},
        }
    }
    config = ApprovalGatesConfig(config_data)
    gate = config.get_phase_gate("plan")
    assert gate is None  # Returns None if not enabled
