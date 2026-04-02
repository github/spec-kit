"""
Unit tests for branch numbering options (sequential vs timestamp).

Tests cover:
- Persisting branch_numbering in init-options.json
- Default value when branch_numbering is None
- Validation of branch_numbering values
"""

import json
from pathlib import Path

from specify_cli import save_init_options


class TestSaveBranchNumbering:
    """Tests for save_init_options with branch_numbering."""

    def test_save_branch_numbering_timestamp(self, tmp_path: Path):
        opts = {"branch_numbering": "timestamp", "ai": "claude"}
        save_init_options(tmp_path, opts)

        saved = json.loads((tmp_path / ".specify/init-options.json").read_text())
        assert saved["branch_numbering"] == "timestamp"

    def test_save_branch_numbering_sequential(self, tmp_path: Path):
        opts = {"branch_numbering": "sequential", "ai": "claude"}
        save_init_options(tmp_path, opts)

        saved = json.loads((tmp_path / ".specify/init-options.json").read_text())
        assert saved["branch_numbering"] == "sequential"

    def test_branch_numbering_defaults_to_sequential(self, tmp_path: Path, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        def _fake_download(project_path, *args, **kwargs):
            Path(project_path).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("specify_cli.download_and_extract_template", _fake_download)

        project_dir = tmp_path / "proj"
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(project_dir), "--ai", "claude", "--ignore-agent-tools"])
        assert result.exit_code == 0

        saved = json.loads((project_dir / ".specify/init-options.json").read_text())
        assert saved["branch_numbering"] == "sequential"


class TestBranchNumberingValidation:
    """Tests for branch_numbering CLI validation via CliRunner."""

    def test_invalid_branch_numbering_rejected(self, tmp_path: Path):
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "proj"), "--ai", "claude", "--branch-numbering", "foobar"])
        assert result.exit_code == 1
        assert "Invalid --branch-numbering" in result.output

    def test_valid_branch_numbering_sequential(self, tmp_path: Path, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        def _fake_download(project_path, *args, **kwargs):
            Path(project_path).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("specify_cli.download_and_extract_template", _fake_download)

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "proj"), "--ai", "claude", "--branch-numbering", "sequential", "--ignore-agent-tools"])
        assert result.exit_code == 0
        assert "Invalid --branch-numbering" not in (result.output or "")

    def test_valid_branch_numbering_timestamp(self, tmp_path: Path, monkeypatch):
        from typer.testing import CliRunner
        from specify_cli import app

        def _fake_download(project_path, *args, **kwargs):
            Path(project_path).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("specify_cli.download_and_extract_template", _fake_download)

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "proj"), "--ai", "claude", "--branch-numbering", "timestamp", "--ignore-agent-tools"])
        assert result.exit_code == 0
        assert "Invalid --branch-numbering" not in (result.output or "")


class TestGitExtensionAutoInstall:
    """Tests for bundled git extension auto-install during specify init."""

    def test_git_extension_installed_during_init(self, tmp_path: Path, monkeypatch):
        """Verify that `specify init` auto-installs the bundled git extension."""
        from typer.testing import CliRunner
        from specify_cli import app

        def _fake_download(project_path, *args, **kwargs):
            Path(project_path).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("specify_cli.download_and_extract_template", _fake_download)

        project_dir = tmp_path / "proj"
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(project_dir), "--ai", "claude", "--ignore-agent-tools"])
        assert result.exit_code == 0

        # Extension files should exist
        ext_dir = project_dir / ".specify" / "extensions" / "git"
        assert ext_dir.is_dir(), "git extension directory not created"
        assert (ext_dir / "extension.yml").is_file(), "extension.yml not installed"

        # Registry should contain the git extension
        registry_file = project_dir / ".specify" / "extensions" / ".registry"
        assert registry_file.is_file(), "extension registry not created"
        registry = json.loads(registry_file.read_text())
        assert "git" in registry.get("extensions", {}), "git not in registry"
        assert registry["extensions"]["git"]["enabled"] is True

    def test_git_extension_noop_when_already_installed(self, tmp_path: Path):
        """_install_bundled_git_extension should no-op if git is already installed."""
        from specify_cli import _install_bundled_git_extension
        from specify_cli.extensions import ExtensionManager

        project_dir = tmp_path / "proj"
        (project_dir / ".specify").mkdir(parents=True)

        # First install
        result1 = _install_bundled_git_extension(project_dir)
        assert result1 is True

        # Second install should also succeed (no-op)
        result2 = _install_bundled_git_extension(project_dir)
        assert result2 is True

        # Only one entry in registry
        manager = ExtensionManager(project_dir)
        assert manager.registry.is_installed("git")

    def test_git_extension_reinstalls_when_directory_missing(self, tmp_path: Path):
        """_install_bundled_git_extension should reinstall if registry says installed but directory is gone."""
        import shutil
        from specify_cli import _install_bundled_git_extension
        from specify_cli.extensions import ExtensionManager

        project_dir = tmp_path / "proj"
        (project_dir / ".specify").mkdir(parents=True)

        # First install
        result1 = _install_bundled_git_extension(project_dir)
        assert result1 is True

        ext_dir = project_dir / ".specify" / "extensions" / "git"
        assert ext_dir.is_dir()

        # Simulate stale registry: delete extension directory but keep registry
        shutil.rmtree(ext_dir)
        assert not ext_dir.exists()

        # Registry still says installed
        manager = ExtensionManager(project_dir)
        assert manager.registry.is_installed("git")

        # Re-install should detect missing directory and reinstall
        result2 = _install_bundled_git_extension(project_dir)
        assert result2 is True
        assert ext_dir.is_dir(), "extension directory should be reinstalled"
        assert (ext_dir / "extension.yml").is_file(), "extension.yml should be reinstalled"
