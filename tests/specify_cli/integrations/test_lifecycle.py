"""Tests for mirrored integration CLI behavior in test_lifecycle.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

class TestIntegrationLifecycle:
    def test_install_modify_uninstall_preserves_modified(self, tmp_path):
        """Full lifecycle: install → modify file → uninstall → verify modified file kept."""
        project = tmp_path / "lifecycle"
        project.mkdir()
        (project / ".specify").mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)

            # Install
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert result.exit_code == 0
            assert "installed successfully" in result.output

            # Claude uses skills directory
            plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
            assert plan_file.exists()

            # Modify one file
            plan_file.write_text("# user customization\n", encoding="utf-8")

            # Uninstall
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "preserved" in result.output

            # Modified file kept
            assert plan_file.exists()
            assert plan_file.read_text(encoding="utf-8") == "# user customization\n"
        finally:
            os.chdir(old_cwd)


@pytest.mark.parametrize("change", ["none", "changed-file", "new-file", "deleted-directory", "nonempty-sibling"])
def test_directory_identity_ignores_only_new_empty_destination_parents(tmp_path, change):
    from specify_cli.integrations._lifecycle import _file_identity, _matches_directory_before_write

    package = tmp_path / "package"
    package.mkdir()
    (package / "original.txt").write_text("original")
    (package / "original-empty").mkdir()
    expected = _file_identity(package)
    (package / ".cache/nested").mkdir(parents=True)
    if change == "changed-file":
        (package / "original.txt").write_text("concurrent edit")
    elif change == "new-file":
        (package / "user.txt").write_text("concurrent user file")
    elif change == "deleted-directory":
        (package / "original-empty").rmdir()
    elif change == "nonempty-sibling":
        (package / ".cache/user.txt").write_text("concurrent user cache file")
    assert _matches_directory_before_write(
        _file_identity(package), expected, (".cache", "nested"),
    ) == (change == "none")
