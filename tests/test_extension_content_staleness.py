"""Tests for the bundled-extension local update route (#4345).

Bundled extensions have no download URL, so `specify extension update`
installs them from the copy shipped with the running spec-kit release,
packaged by `_archive_extension_directory` into the same hardened
archive pipeline that downloaded updates use. These tests pin that
packaging step and its round trip through the archive installer.
"""

from __future__ import annotations

import os

import pytest
import yaml
from pathlib import Path

from specify_cli.extensions import ExtensionManager


def _create_extension_source(
    base_dir: Path, name: str = "test-ext", version: str = "1.0.0"
) -> Path:
    """Create a minimal installable extension source directory."""
    ext_dir = base_dir / name
    ext_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "1.0",
        "extension": {
            "id": "test-ext",
            "name": "Test Extension",
            "version": version,
            "description": "A test extension",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "commands": [
                {
                    "name": "speckit.test-ext.hello",
                    "file": "commands/hello.md",
                    "description": "Test command",
                }
            ]
        },
    }

    (ext_dir / "extension.yml").write_text(yaml.dump(manifest, sort_keys=False))
    commands_dir = ext_dir / "commands"
    commands_dir.mkdir(exist_ok=True)
    (commands_dir / "hello.md").write_text("---\ndescription: Test\n---\n\n$ARGUMENTS\n")
    scripts_dir = ext_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / "run.sh").write_text("#!/bin/sh\necho hello\n")
    (ext_dir / "test-ext-config.yml").write_text("setting: default\n")
    return ext_dir


def _make_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".specify").mkdir()
    (project_dir / ".claude" / "skills").mkdir(parents=True)
    return project_dir


class TestArchiveExtensionDirectory:
    def test_archive_contains_regular_files_only(self, tmp_path):
        import zipfile

        from specify_cli.extensions._commands import _archive_extension_directory

        ext_dir = _create_extension_source(tmp_path)
        archive_path = _archive_extension_directory(ext_dir)
        try:
            with zipfile.ZipFile(archive_path) as zf:
                names = set(zf.namelist())
            assert "extension.yml" in names
            assert "commands/hello.md" in names
        finally:
            archive_path.unlink()

    def test_archive_never_follows_symlinks(self, tmp_path):
        """A symlink in the source must not pull out-of-tree bytes into the
        archive before the hardened extractor sees it."""
        import zipfile

        from specify_cli.extensions._commands import _archive_extension_directory

        ext_dir = _create_extension_source(tmp_path)
        outside = tmp_path / "outside.txt"
        outside.write_text("external bytes\n")
        try:
            (ext_dir / "scripts" / "link.txt").symlink_to(outside)
        except OSError:
            pytest.skip("symlink creation requires privileges on this platform")

        archive_path = _archive_extension_directory(ext_dir)
        try:
            with zipfile.ZipFile(archive_path) as zf:
                names = set(zf.namelist())
            assert "scripts/link.txt" not in names
        finally:
            archive_path.unlink()

    @pytest.mark.skipif(
        os.name == "nt", reason="POSIX execute bits do not exist on Windows"
    )
    def test_archive_route_restores_script_execute_bits(self, tmp_path):
        """safe_extract_archive writes members without their recorded ZIP
        modes, so the archive install route depends on install_from_directory's
        trailing ensure_executable_scripts() call to keep documented
        `.specify/extensions/<id>/scripts/*.sh` invocations executable. Pin
        that round trip so removing the restoration would fail here instead
        of surfacing as `Permission denied` after a bundled update."""
        from specify_cli.extensions._commands import _archive_extension_directory

        project_dir = _make_project(tmp_path)
        source = _create_extension_source(tmp_path)
        (source / "scripts" / "run.sh").chmod(0o755)

        archive_path = _archive_extension_directory(source)
        try:
            ExtensionManager(project_dir).install_from_zip(archive_path, "0.1.0")
        finally:
            archive_path.unlink()

        installed_script = (
            project_dir / ".specify" / "extensions" / "test-ext" / "scripts" / "run.sh"
        )
        assert installed_script.is_file()
        assert installed_script.stat().st_mode & 0o100, (
            "execute bit lost through the archive install route"
        )
