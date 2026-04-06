"""Tests for BannerGroup class."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from infrakit_cli import app, BannerGroup


runner = CliRunner()


class TestBannerGroup:
    """Test suite for BannerGroup class."""

    def test_banner_group_initialization(self):
        """Test BannerGroup initializes correctly."""
        group = BannerGroup()
        assert group is not None

    def test_banner_group_invoke(self):
        """Test BannerGroup invoke method."""
        group = BannerGroup()
        # Should be callable
        assert callable(group)


class TestCallback:
    """Test suite for callback function."""

    def test_callback_runs(self):
        """Test callback function runs without error."""
        # The callback is called when the app starts
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_callback_shows_banner(self):
        """Test callback shows banner."""
        result = runner.invoke(app, ["check"])
        # Banner should be shown
        assert "infrakit" in result.output.lower()
