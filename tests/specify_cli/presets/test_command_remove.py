"""Tests for the ``specify preset remove`` command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager
from tests.specify_cli.presets._skill_cleanup_helpers import (
    PRESET_REMOVE,
    check_cleanup_preserves_swapped_link_target,
    check_cleanup_preserves_user_files,
    check_cleanup_rollback_preserves_directory_mode,
)


def test_remove_installed_preset(project_dir, pack_dir):
    PresetManager(project_dir).install_from_directory(pack_dir, "0.1.5")

    with patch.object(Path, "cwd", return_value=project_dir):
        result = CliRunner().invoke(app, ["preset", "remove", "test-pack"])

    assert result.exit_code == 0, result.output
    assert not PresetManager(project_dir).registry.is_installed("test-pack")


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("ancestor", [False, True])
def test_preset_skill_cleanup_preserves_swapped_link_target(tmp_path, monkeypatch, fallback, ancestor):
    check_cleanup_preserves_swapped_link_target(tmp_path, monkeypatch, PRESET_REMOVE, fallback, ancestor)


@pytest.mark.parametrize(
    "user_reference,layout",
    [(False, "project"), (True, "project"), (False, "linked-parent")],
    ids=["empty", "user-files", "linked-parent"],
)
@pytest.mark.parametrize("fallback", [False, True])
def test_preset_skill_cleanup_preserves_user_files(tmp_path, monkeypatch, user_reference, layout, fallback):
    check_cleanup_preserves_user_files(tmp_path, monkeypatch, PRESET_REMOVE, user_reference, layout, fallback)


@pytest.mark.parametrize("user_reference", [False, True])
@pytest.mark.parametrize("fallback", [False, True])
def test_preset_skill_cleanup_rollback_preserves_directory_mode(
    tmp_path, monkeypatch, capsys, user_reference, fallback,
):
    check_cleanup_rollback_preserves_directory_mode(
        tmp_path, monkeypatch, capsys, PRESET_REMOVE, user_reference, fallback
    )
