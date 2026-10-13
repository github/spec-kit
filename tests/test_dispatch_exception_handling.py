"""Tests for dispatch_command exception handling (PR #3921).

Covers OSError and TimeoutExpired handling in both streaming and captured modes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specify_cli.integrations.base import IntegrationBase


class MockIntegration(IntegrationBase):
    """Minimal concrete integration for testing dispatch_command."""

    key = "mock-dispatch"
    config = {
        "name": "Mock Dispatch",
        "folder": ".mock/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".mock/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    def build_exec_args(self, prompt, *, model=None, output_json=False,
                        integration_args=None, integration_options=None):
        return ["mock-cli", prompt]


class TestDispatchCommandExceptionHandling:
    """OSError and TimeoutExpired handling in dispatch_command (PR #3921)."""

    def test_streaming_oserror_returns_error(self, tmp_path: Path) -> None:
        """OSError in streaming mode must return exit_code 1 with error."""
        integration = MockIntegration()

        with patch("specify_cli.integrations.base.shutil.which", return_value="mock-cli"):
            with patch("specify_cli.integrations.base.subprocess.run", side_effect=OSError("No such file")):
                result = integration.dispatch_command(
                    "speckit.plan", stream=True, project_root=tmp_path
                )

        assert result["exit_code"] == 1
        assert "Failed to execute command" in result["stderr"]
        assert result["stdout"] == ""

    def test_captured_oserror_returns_error(self, tmp_path: Path) -> None:
        """OSError in captured mode must return exit_code 1 with error."""
        integration = MockIntegration()

        with patch("specify_cli.integrations.base.shutil.which", return_value="mock-cli"):
            with patch("specify_cli.integrations.base.subprocess.run", side_effect=OSError("Permission denied")):
                result = integration.dispatch_command(
                    "speckit.plan", stream=False, project_root=tmp_path
                )

        assert result["exit_code"] == 1
        assert "Failed to execute command" in result["stderr"]

    def test_captured_timeout_returns_124(self, tmp_path: Path) -> None:
        """TimeoutExpired in captured mode must return exit_code 124."""
        integration = MockIntegration()

        with patch("specify_cli.integrations.base.shutil.which", return_value="mock-cli"):
            with patch(
                "specify_cli.integrations.base.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="mock-cli", timeout=5),
            ):
                result = integration.dispatch_command(
                    "speckit.plan", stream=False, timeout=5, project_root=tmp_path
                )

        assert result["exit_code"] == 124
        assert "timed out" in result["stderr"]
        assert "5s" in result["stderr"]

    def test_successful_captured_returns_output(self, tmp_path: Path) -> None:
        """Successful captured dispatch must return stdout and exit_code 0."""
        integration = MockIntegration()
        mock_result = MagicMock(returncode=0, stdout="hello", stderr="")

        with patch("specify_cli.integrations.base.shutil.which", return_value="mock-cli"):
            with patch("specify_cli.integrations.base.subprocess.run", return_value=mock_result):
                result = integration.dispatch_command(
                    "speckit.plan", stream=False, project_root=tmp_path
                )

        assert result["exit_code"] == 0
        assert result["stdout"] == "hello"
        assert result["stderr"] == ""

    def test_successful_streaming_returns_zero(self, tmp_path: Path) -> None:
        """Successful streaming dispatch must return exit_code 0."""
        integration = MockIntegration()
        mock_result = MagicMock(returncode=0)

        with patch("specify_cli.integrations.base.shutil.which", return_value="mock-cli"):
            with patch("specify_cli.integrations.base.subprocess.run", return_value=mock_result):
                result = integration.dispatch_command(
                    "speckit.plan", stream=True, project_root=tmp_path
                )

        assert result["exit_code"] == 0
        assert result["stdout"] == ""
        assert result["stderr"] == ""
