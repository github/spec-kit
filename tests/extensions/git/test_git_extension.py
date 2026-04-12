"""
Tests for the bundled git extension (extensions/git/).

Validates:
- extension.yml manifest
- Bash scripts (create-new-feature.sh, initialize-repo.sh, auto-commit.sh, git-common.sh)
- PowerShell scripts (where pwsh is available)
- Config reading from git-config.yml
- Extension install via ExtensionManager
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "git"
EXT_BASH = EXT_DIR / "scripts" / "bash"
EXT_PS = EXT_DIR / "scripts" / "powershell"
CORE_COMMON_SH = PROJECT_ROOT / "scripts" / "bash" / "common.sh"
CORE_COMMON_PS = PROJECT_ROOT / "scripts" / "powershell" / "common.ps1"

HAS_PWSH = shutil.which("pwsh") is not None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _init_git(path: Path) -> None:
    """Initialize a git repo with a dummy commit."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "seed", "-q"],
        cwd=path,
        check=True,
    )


def _setup_project(tmp_path: Path, *, git: bool = True) -> Path:
    """Create a project directory with core scripts and .specify."""
    # Core scripts (needed by extension scripts that source common.sh)
    bash_dir = tmp_path / "scripts" / "bash"
    bash_dir.mkdir(parents=True)
    shutil.copy(CORE_COMMON_SH, bash_dir / "common.sh")

    ps_dir = tmp_path / "scripts" / "powershell"
    ps_dir.mkdir(parents=True)
    shutil.copy(CORE_COMMON_PS, ps_dir / "common.ps1")

    # .specify structure
    (tmp_path / ".specify" / "templates").mkdir(parents=True)

    # Extension scripts (as if installed)
    ext_bash = tmp_path / ".specify" / "extensions" / "git" / "scripts" / "bash"
    ext_bash.mkdir(parents=True)
    for f in EXT_BASH.iterdir():
        dest = ext_bash / f.name
        shutil.copy(f, dest)
        dest.chmod(0o755)

    ext_ps = tmp_path / ".specify" / "extensions" / "git" / "scripts" / "powershell"
    ext_ps.mkdir(parents=True)
    for f in EXT_PS.iterdir():
        shutil.copy(f, ext_ps / f.name)

    # Copy extension.yml
    shutil.copy(EXT_DIR / "extension.yml", tmp_path / ".specify" / "extensions" / "git" / "extension.yml")

    if git:
        _init_git(tmp_path)

    return tmp_path


def _write_config(project: Path, content: str) -> Path:
    """Write git-config.yml into the extension config directory."""
    config_path = project / ".specify" / "extensions" / "git" / "git-config.yml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


# Git identity env vars for CI runners without global git config
_GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test User",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test User",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def _run_bash(script_name: str, cwd: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run an extension bash script."""
    script = cwd / ".specify" / "extensions" / "git" / "scripts" / "bash" / script_name
    env = {**os.environ, **_GIT_ENV, **(env_extra or {})}
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def _run_pwsh(script_name: str, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run an extension PowerShell script."""
    script = cwd / ".specify" / "extensions" / "git" / "scripts" / "powershell" / script_name
    env = {**os.environ, **_GIT_ENV}
    return subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


# ── Manifest Tests ───────────────────────────────────────────────────────────


class TestGitExtensionManifest:
    def test_manifest_validates(self):
        """extension.yml passes manifest validation."""
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        assert m.id == "git"
        assert m.version == "1.0.0"

    def test_manifest_commands(self):
        """Manifest declares expected commands."""
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        names = [c["name"] for c in m.commands]
        assert "speckit.git.feature" in names
        assert "speckit.git.validate" in names
        assert "speckit.git.remote" in names
        assert "speckit.git.initialize" in names
        assert "speckit.git.commit" in names

    def test_manifest_hooks(self):
        """Manifest declares expected hooks."""
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        assert "before_constitution" in m.hooks
        assert "before_specify" in m.hooks
        assert "after_specify" in m.hooks
        assert "after_implement" in m.hooks
        assert m.hooks["before_constitution"]["command"] == "speckit.git.initialize"
        assert m.hooks["before_specify"]["command"] == "speckit.git.feature"

    def test_manifest_command_files_exist(self):
        """All command files referenced in the manifest exist."""
        from specify_cli.extensions import ExtensionManifest

        m = ExtensionManifest(EXT_DIR / "extension.yml")
        for cmd in m.commands:
            cmd_path = EXT_DIR / cmd["file"]
            assert cmd_path.is_file(), f"Missing command file: {cmd['file']}"


# ── Install Tests ────────────────────────────────────────────────────────────


class TestGitExtensionInstall:
    def test_install_from_directory(self, tmp_path: Path):
        """Extension installs via ExtensionManager.install_from_directory."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manifest = manager.install_from_directory(EXT_DIR, "0.5.0", register_commands=False)
        assert manifest.id == "git"
        assert manager.registry.is_installed("git")

    def test_install_copies_scripts(self, tmp_path: Path):
        """Extension install copies script files."""
        from specify_cli.extensions import ExtensionManager

        (tmp_path / ".specify").mkdir()
        manager = ExtensionManager(tmp_path)
        manager.install_from_directory(EXT_DIR, "0.5.0", register_commands=False)

        ext_installed = tmp_path / ".specify" / "extensions" / "git"
        assert (ext_installed / "scripts" / "bash" / "create-new-feature.sh").is_file()
        assert (ext_installed / "scripts" / "bash" / "initialize-repo.sh").is_file()
        assert (ext_installed / "scripts" / "bash" / "auto-commit.sh").is_file()
        assert (ext_installed / "scripts" / "bash" / "git-common.sh").is_file()
        assert (ext_installed / "scripts" / "powershell" / "create-new-feature.ps1").is_file()
        assert (ext_installed / "scripts" / "powershell" / "initialize-repo.ps1").is_file()
        assert (ext_installed / "scripts" / "powershell" / "auto-commit.ps1").is_file()
        assert (ext_installed / "scripts" / "powershell" / "git-common.ps1").is_file()

    def test_bundled_extension_locator(self):
        """_locate_bundled_extension finds the git extension."""
        from specify_cli import _locate_bundled_extension

        path = _locate_bundled_extension("git")
        assert path is not None
        assert (path / "extension.yml").is_file()


# ── initialize-repo.sh Tests ─────────────────────────────────────────────────


class TestInitializeRepoBash:
    def test_initializes_git_repo(self, tmp_path: Path):
        """initialize-repo.sh creates a git repo with initial commit."""
        project = _setup_project(tmp_path, git=False)
        result = _run_bash("initialize-repo.sh", project)
        assert result.returncode == 0, result.stderr

        # Verify git repo exists
        assert (project / ".git").exists()

        # Verify at least one commit exists
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project, capture_output=True, text=True,
        )
        assert log.returncode == 0

    def test_skips_if_already_git_repo(self, tmp_path: Path):
        """initialize-repo.sh skips if already a git repo."""
        project = _setup_project(tmp_path, git=True)
        result = _run_bash("initialize-repo.sh", project)
        assert result.returncode == 0
        assert "already initialized" in result.stderr.lower()

    def test_custom_commit_message(self, tmp_path: Path):
        """initialize-repo.sh reads custom commit message from config."""
        project = _setup_project(tmp_path, git=False)
        _write_config(project, 'init_commit_message: "Custom init message"\n')

        result = _run_bash("initialize-repo.sh", project)
        assert result.returncode == 0

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project, capture_output=True, text=True,
        )
        assert "Custom init message" in log.stdout


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
class TestInitializeRepoPowerShell:
    def test_initializes_git_repo(self, tmp_path: Path):
        """initialize-repo.ps1 creates a git repo with initial commit."""
        project = _setup_project(tmp_path, git=False)
        result = _run_pwsh("initialize-repo.ps1", project)
        assert result.returncode == 0, result.stderr
        assert (project / ".git").exists()

    def test_skips_if_already_git_repo(self, tmp_path: Path):
        """initialize-repo.ps1 skips if already a git repo."""
        project = _setup_project(tmp_path, git=True)
        result = _run_pwsh("initialize-repo.ps1", project)
        assert result.returncode == 0


# ── create-new-feature.sh Tests ──────────────────────────────────────────────


class TestCreateFeatureBash:
    def test_creates_branch_sequential(self, tmp_path: Path):
        """Extension create-new-feature.sh creates sequential branch."""
        project = _setup_project(tmp_path)
        result = _run_bash(
            "create-new-feature.sh", project,
            "--json", "--short-name", "user-auth", "Add user authentication",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "001-user-auth"
        assert data["FEATURE_NUM"] == "001"

    def test_creates_branch_timestamp(self, tmp_path: Path):
        """Extension create-new-feature.sh creates timestamp branch."""
        project = _setup_project(tmp_path)
        result = _run_bash(
            "create-new-feature.sh", project,
            "--json", "--timestamp", "--short-name", "feat", "Feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert re.match(r"^\d{8}-\d{6}-feat$", data["BRANCH_NAME"])

    def test_increments_from_existing_specs(self, tmp_path: Path):
        """Sequential numbering increments past existing spec directories."""
        project = _setup_project(tmp_path)
        (project / "specs" / "001-first").mkdir(parents=True)
        (project / "specs" / "002-second").mkdir(parents=True)

        result = _run_bash(
            "create-new-feature.sh", project,
            "--json", "--short-name", "third", "Third feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["FEATURE_NUM"] == "003"

    def test_no_git_graceful_degradation(self, tmp_path: Path):
        """create-new-feature.sh works without git (outputs branch name, skips branch creation)."""
        project = _setup_project(tmp_path, git=False)
        result = _run_bash(
            "create-new-feature.sh", project,
            "--json", "--short-name", "no-git", "No git feature",
        )
        assert result.returncode == 0, result.stderr
        assert "Warning" in result.stderr
        data = json.loads(result.stdout)
        assert "BRANCH_NAME" in data
        assert "FEATURE_NUM" in data

    def test_dry_run(self, tmp_path: Path):
        """--dry-run computes branch name without creating anything."""
        project = _setup_project(tmp_path)
        result = _run_bash(
            "create-new-feature.sh", project,
            "--json", "--dry-run", "--short-name", "dry", "Dry run test",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data.get("DRY_RUN") is True
        assert not (project / "specs" / data["BRANCH_NAME"]).exists()


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
class TestCreateFeaturePowerShell:
    def test_creates_branch_sequential(self, tmp_path: Path):
        """Extension create-new-feature.ps1 creates sequential branch."""
        project = _setup_project(tmp_path)
        result = _run_pwsh(
            "create-new-feature.ps1", project,
            "-Json", "-ShortName", "user-auth", "Add user authentication",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["BRANCH_NAME"] == "001-user-auth"

    def test_creates_branch_timestamp(self, tmp_path: Path):
        """Extension create-new-feature.ps1 creates timestamp branch."""
        project = _setup_project(tmp_path)
        result = _run_pwsh(
            "create-new-feature.ps1", project,
            "-Json", "-Timestamp", "-ShortName", "feat", "Feature",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert re.match(r"^\d{8}-\d{6}-feat$", data["BRANCH_NAME"])

    def test_no_git_graceful_degradation(self, tmp_path: Path):
        """create-new-feature.ps1 works without git."""
        project = _setup_project(tmp_path, git=False)
        result = _run_pwsh(
            "create-new-feature.ps1", project,
            "-Json", "-ShortName", "no-git", "No git feature",
        )
        assert result.returncode == 0, result.stderr
        # pwsh may prefix warnings to stdout; find the JSON line
        json_line = [l for l in result.stdout.splitlines() if l.strip().startswith("{")]
        assert json_line, f"No JSON in output: {result.stdout}"
        data = json.loads(json_line[-1])
        assert "BRANCH_NAME" in data
        assert "FEATURE_NUM" in data


# ── auto-commit.sh Tests ─────────────────────────────────────────────────────


class TestAutoCommitBash:
    def test_disabled_by_default(self, tmp_path: Path):
        """auto-commit.sh exits silently when config is all false."""
        project = _setup_project(tmp_path)
        _write_config(project, "auto_commit:\n  default: false\n")
        result = _run_bash("auto-commit.sh", project, "after_specify")
        assert result.returncode == 0
        # Should not have created any new commits
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=project, capture_output=True, text=True,
        )
        assert log.stdout.strip().count("\n") == 0  # only the seed commit

    def test_enabled_per_command(self, tmp_path: Path):
        """auto-commit.sh commits when per-command key is enabled."""
        project = _setup_project(tmp_path)
        _write_config(project, (
            "auto_commit:\n"
            "  default: false\n"
            "  after_specify:\n"
            "    enabled: true\n"
            '    message: "test commit after specify"\n'
        ))
        # Create a file to commit
        (project / "specs" / "001-test" / "spec.md").parent.mkdir(parents=True)
        (project / "specs" / "001-test" / "spec.md").write_text("test spec")

        result = _run_bash("auto-commit.sh", project, "after_specify")
        assert result.returncode == 0

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project, capture_output=True, text=True,
        )
        assert "test commit after specify" in log.stdout

    def test_custom_message(self, tmp_path: Path):
        """auto-commit.sh uses the per-command message."""
        project = _setup_project(tmp_path)
        _write_config(project, (
            "auto_commit:\n"
            "  default: false\n"
            "  after_plan:\n"
            "    enabled: true\n"
            '    message: "[Project] Plan complete"\n'
        ))
        (project / "new-file.txt").write_text("content")

        result = _run_bash("auto-commit.sh", project, "after_plan")
        assert result.returncode == 0

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project, capture_output=True, text=True,
        )
        assert "[Project] Plan complete" in log.stdout

    def test_default_true_with_no_event_key(self, tmp_path: Path):
        """auto-commit.sh uses default: true when event key is absent."""
        project = _setup_project(tmp_path)
        _write_config(project, "auto_commit:\n  default: true\n")
        (project / "new-file.txt").write_text("content")

        result = _run_bash("auto-commit.sh", project, "after_tasks")
        assert result.returncode == 0

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project, capture_output=True, text=True,
        )
        assert "Auto-commit after tasks" in log.stdout

    def test_no_changes_skips(self, tmp_path: Path):
        """auto-commit.sh skips when there are no changes."""
        project = _setup_project(tmp_path)
        _write_config(project, (
            "auto_commit:\n"
            "  default: false\n"
            "  after_specify:\n"
            "    enabled: true\n"
            '    message: "should not appear"\n'
        ))
        # Commit all existing files so nothing is dirty
        subprocess.run(["git", "add", "."], cwd=project, check=True)
        subprocess.run(["git", "commit", "-m", "setup", "-q"], cwd=project, check=True)

        result = _run_bash("auto-commit.sh", project, "after_specify")
        assert result.returncode == 0
        assert "No changes" in result.stderr

    def test_no_config_file_skips(self, tmp_path: Path):
        """auto-commit.sh exits silently when no config file exists."""
        project = _setup_project(tmp_path)
        # Remove config if it was copied
        config = project / ".specify" / "extensions" / "git" / "git-config.yml"
        config.unlink(missing_ok=True)

        result = _run_bash("auto-commit.sh", project, "after_specify")
        assert result.returncode == 0

    def test_no_git_repo_skips(self, tmp_path: Path):
        """auto-commit.sh skips when not in a git repo."""
        project = _setup_project(tmp_path, git=False)
        _write_config(project, "auto_commit:\n  default: true\n")
        result = _run_bash("auto-commit.sh", project, "after_specify")
        assert result.returncode == 0
        assert "not a Git repository" in result.stderr.lower() or "Warning" in result.stderr

    def test_requires_event_name_argument(self, tmp_path: Path):
        """auto-commit.sh fails without event name argument."""
        project = _setup_project(tmp_path)
        result = _run_bash("auto-commit.sh", project)
        assert result.returncode != 0


@pytest.mark.skipif(not HAS_PWSH, reason="pwsh not available")
class TestAutoCommitPowerShell:
    def test_disabled_by_default(self, tmp_path: Path):
        """auto-commit.ps1 exits silently when config is all false."""
        project = _setup_project(tmp_path)
        _write_config(project, "auto_commit:\n  default: false\n")
        result = _run_pwsh("auto-commit.ps1", project, "after_specify")
        assert result.returncode == 0

    def test_enabled_per_command(self, tmp_path: Path):
        """auto-commit.ps1 commits when per-command key is enabled."""
        project = _setup_project(tmp_path)
        _write_config(project, (
            "auto_commit:\n"
            "  default: false\n"
            "  after_specify:\n"
            "    enabled: true\n"
            '    message: "ps commit"\n'
        ))
        (project / "specs" / "001-test").mkdir(parents=True)
        (project / "specs" / "001-test" / "spec.md").write_text("test")

        result = _run_pwsh("auto-commit.ps1", project, "after_specify")
        assert result.returncode == 0

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project, capture_output=True, text=True,
        )
        assert "ps commit" in log.stdout


# ── git-common.sh Tests ──────────────────────────────────────────────────────


class TestGitCommonBash:
    def test_has_git_true(self, tmp_path: Path):
        """has_git returns 0 in a git repo."""
        project = _setup_project(tmp_path, git=True)
        script = project / ".specify" / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" && has_git "{project}"'],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_has_git_false(self, tmp_path: Path):
        """has_git returns non-zero outside a git repo."""
        project = _setup_project(tmp_path, git=False)
        script = project / ".specify" / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" && has_git "{project}"'],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_check_feature_branch_sequential(self, tmp_path: Path):
        """check_feature_branch accepts sequential branch names."""
        project = _setup_project(tmp_path)
        script = project / ".specify" / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" && check_feature_branch "001-my-feature" "true"'],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_check_feature_branch_timestamp(self, tmp_path: Path):
        """check_feature_branch accepts timestamp branch names."""
        project = _setup_project(tmp_path)
        script = project / ".specify" / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" && check_feature_branch "20260319-143022-feat" "true"'],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_check_feature_branch_rejects_main(self, tmp_path: Path):
        """check_feature_branch rejects non-feature branch names."""
        project = _setup_project(tmp_path)
        script = project / ".specify" / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" && check_feature_branch "main" "true"'],
            capture_output=True, text=True,
        )
        assert result.returncode != 0

    def test_check_feature_branch_rejects_malformed_timestamp(self, tmp_path: Path):
        """check_feature_branch rejects malformed timestamps (7-digit date)."""
        project = _setup_project(tmp_path)
        script = project / ".specify" / "extensions" / "git" / "scripts" / "bash" / "git-common.sh"
        result = subprocess.run(
            ["bash", "-c", f'source "{script}" && check_feature_branch "2026031-143022-feat" "true"'],
            capture_output=True, text=True,
        )
        assert result.returncode != 0


# ── Deprecation Notice Tests ──────────────────────────────────────────────────


class TestGitExtDeprecationNotice:
    """Tests for the v1.0.0 deprecation notice shown during specify init."""

    def test_deprecation_notice_shown_on_fresh_install(self, tmp_path: Path):
        """specify init shows the git extension deprecation notice on first install."""
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        runner = CliRunner()

        mock_registry = MagicMock()
        mock_registry.is_installed.return_value = False

        mock_manager = MagicMock()
        mock_manager.registry = mock_registry

        with patch("specify_cli.extensions.ExtensionManager", return_value=mock_manager):
            result = runner.invoke(
                app,
                ["init", str(project_dir), "--ai", "claude", "--ignore-agent-tools", "--script", "sh"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, result.output
        assert "Upcoming Change: git Extension" in result.output
        assert "v1.0.0" in result.output
        assert "specify init --extension git" in result.output

    def test_deprecation_notice_not_shown_when_already_installed(self, tmp_path: Path):
        """specify init does NOT show the deprecation notice when git extension is already installed."""
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        runner = CliRunner()

        mock_registry = MagicMock()
        mock_registry.is_installed.return_value = True

        mock_manager = MagicMock()
        mock_manager.registry = mock_registry

        with patch("specify_cli.extensions.ExtensionManager", return_value=mock_manager):
            result = runner.invoke(
                app,
                ["init", str(project_dir), "--ai", "claude", "--ignore-agent-tools", "--script", "sh"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, result.output
        assert "Upcoming Change: git Extension" not in result.output

    def test_deprecation_notice_not_shown_with_no_git_flag(self, tmp_path: Path):
        """specify init does NOT show the deprecation notice when --no-git is passed."""
        from typer.testing import CliRunner
        from specify_cli import app

        project_dir = tmp_path / "test-project"
        runner = CliRunner()

        result = runner.invoke(
            app,
            ["init", str(project_dir), "--ai", "claude", "--ignore-agent-tools", "--no-git", "--script", "sh"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.output
        assert "Upcoming Change: git Extension" not in result.output
