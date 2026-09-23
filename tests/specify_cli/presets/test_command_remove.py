"""Tests for the ``specify preset remove`` command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager


def test_remove_installed_preset(project_dir, pack_dir):
    PresetManager(project_dir).install_from_directory(pack_dir, "0.1.5")

    with patch.object(Path, "cwd", return_value=project_dir):
        result = CliRunner().invoke(app, ["preset", "remove", "test-pack"])

    assert result.exit_code == 0, result.output
    assert not PresetManager(project_dir).registry.is_installed("test-pack")
