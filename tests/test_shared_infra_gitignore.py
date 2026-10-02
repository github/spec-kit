"""Tests for the managed ``.specify/.gitignore`` written by shared-infra install.

The Specify CLI scaffolds a ``.specify/.gitignore`` so machine-local Spec Kit
state (the ``feature.json`` current-feature pointer and per-machine extension
``local-config.yml`` overrides) stays out of version control while everything
else under ``.specify/`` remains shareable. These tests pin that behaviour:
the file is created and manifest-tracked, its patterns actually make git ignore
the intended paths, user edits are preserved on a plain re-run, and ``--force``
restores the managed content.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from specify_cli import _install_shared_infra
from specify_cli.shared_infra import SPECIFY_GITIGNORE_CONTENT


def _install(project: Path, **kwargs) -> None:
    (project / ".specify").mkdir(parents=True, exist_ok=True)
    _install_shared_infra(project, "sh", **kwargs)


def test_gitignore_is_written_and_tracked(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _install(project)

    gitignore = project / ".specify" / ".gitignore"
    assert gitignore.is_file()

    content = gitignore.read_text(encoding="utf-8")
    assert "feature.json" in content
    assert "extensions/*/local-config.yml" in content

    manifest = json.loads(
        (project / ".specify" / "integrations" / "speckit.manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert ".specify/.gitignore" in manifest.get("files", {})


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_git_ignores_the_intended_paths(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)

    _install(project)

    (project / ".specify" / "feature.json").write_text("{}", encoding="utf-8")
    ext_local = project / ".specify" / "extensions" / "git" / "local-config.yml"
    ext_local.parent.mkdir(parents=True, exist_ok=True)
    ext_local.write_text("x\n", encoding="utf-8")

    for rel in (
        ".specify/feature.json",
        ".specify/extensions/git/local-config.yml",
    ):
        result = subprocess.run(
            ["git", "check-ignore", rel],
            cwd=project,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{rel} was not ignored"

    # A shareable file under .specify/ must NOT be ignored.
    tracked = subprocess.run(
        ["git", "check-ignore", ".specify/memory/constitution.md"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert tracked.returncode == 1


def test_user_edits_preserved_by_default(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _install(project)

    gitignore = project / ".specify" / ".gitignore"
    gitignore.write_text("# my customization\n", encoding="utf-8")

    _install(project)  # plain re-run must not clobber user edits
    assert gitignore.read_text(encoding="utf-8") == "# my customization\n"


def test_force_restores_managed_content(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    _install(project)

    gitignore = project / ".specify" / ".gitignore"
    gitignore.write_text("# my customization\n", encoding="utf-8")

    _install(project, force=True)
    assert gitignore.read_text(encoding="utf-8") == SPECIFY_GITIGNORE_CONTENT
