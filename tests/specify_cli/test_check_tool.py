"""Tests for check_tool() — Claude Code CLI detection across install methods.

Covers issue https://github.com/github/spec-kit/issues/550:
  `specify check` reports "Claude Code CLI (not found)" even when claude is
  installed via npm-local (the default `claude` installer path).
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

from specify_cli import check_tool
from specify_cli.integrations.claude import ClaudeIntegration


class TestCheckToolClaude:
    """Claude CLI detection must work for all install methods."""

    def test_detected_via_migrate_installer_path(self, tmp_path):
        """claude migrate-installer puts binary at ~/.claude/local/claude."""
        fake_claude = tmp_path / "claude"
        fake_claude.touch()
        # Availability checks the execute bit, so model a real (executable) install.
        fake_claude.chmod(0o755)

        # Ensure npm-local path is missing so we only exercise migrate-installer path
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli.CLAUDE_LOCAL_PATH", fake_claude), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_claude), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("shutil.which", return_value=None):
            assert check_tool("claude") is True

    def test_detected_via_npm_local_path(self, tmp_path):
        """npm-local install puts binary at ~/.claude/local/node_modules/.bin/claude."""
        fake_npm_claude = tmp_path / "node_modules" / ".bin" / "claude"
        fake_npm_claude.parent.mkdir(parents=True)
        fake_npm_claude.touch()
        # Availability checks the execute bit, so model a real (executable) install.
        fake_npm_claude.chmod(0o755)

        # Neither the migrate-installer path nor PATH has claude
        fake_migrate = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli.CLAUDE_LOCAL_PATH", fake_migrate), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_migrate), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", fake_npm_claude), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_npm_claude), \
             patch("shutil.which", return_value=None):
            assert check_tool("claude") is True

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows has no POSIX execute bit; os.access(X_OK) is always true",
    )
    def test_non_executable_local_path_does_not_mask_npm_local(self, tmp_path):
        """A stale, non-executable migrate-installer file must not hide an npm-local install.

        Both candidates exist, so picking on existence alone returns the first
        one; availability then rejects it on the execute bit and Claude is
        reported missing even though the second candidate is launchable.
        """
        stale_local = tmp_path / "local" / "claude"
        stale_local.parent.mkdir(parents=True)
        stale_local.write_text("#!/bin/sh\n")
        stale_local.chmod(0o644)

        npm_local = tmp_path / "node_modules" / ".bin" / "claude"
        npm_local.parent.mkdir(parents=True)
        npm_local.write_text("#!/bin/sh\n")
        npm_local.chmod(0o755)

        with patch("specify_cli.CLAUDE_LOCAL_PATH", stale_local), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", stale_local), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", npm_local), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", npm_local), \
             patch("shutil.which", return_value=None):
            integration = ClaudeIntegration()
            # Dispatch runs this value, so it has to be the launchable candidate.
            assert integration._resolve_executable() == str(npm_local)
            assert integration.is_cli_available() is True
            assert check_tool("claude") is True

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows has no POSIX execute bit; os.access(X_OK) is always true",
    )
    def test_not_found_when_candidates_exist_but_none_are_executable(self, tmp_path):
        """Skipping a non-executable candidate must not invent an install."""
        stale_local = tmp_path / "local" / "claude"
        stale_local.parent.mkdir(parents=True)
        stale_local.write_text("#!/bin/sh\n")
        stale_local.chmod(0o644)

        stale_npm = tmp_path / "node_modules" / ".bin" / "claude"
        stale_npm.parent.mkdir(parents=True)
        stale_npm.write_text("#!/bin/sh\n")
        stale_npm.chmod(0o644)

        with patch("specify_cli.CLAUDE_LOCAL_PATH", stale_local), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", stale_local), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", stale_npm), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", stale_npm), \
             patch("shutil.which", return_value=None):
            assert check_tool("claude") is False

    def test_detected_via_path(self, tmp_path):
        """claude on PATH (global npm install) should still work."""
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("shutil.which", return_value="/usr/local/bin/claude"):
            assert check_tool("claude") is True

    def test_not_found_when_nowhere(self, tmp_path):
        """Should return False when claude is genuinely not installed."""
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("shutil.which", return_value=None):
            assert check_tool("claude") is False

    def test_tracker_updated_on_npm_local_detection(self, tmp_path):
        """StepTracker should be marked 'available' for npm-local installs."""
        fake_npm_claude = tmp_path / "node_modules" / ".bin" / "claude"
        fake_npm_claude.parent.mkdir(parents=True)
        fake_npm_claude.touch()
        # Availability checks the execute bit, so model a real (executable) install.
        fake_npm_claude.chmod(0o755)

        fake_missing = tmp_path / "nonexistent" / "claude"
        tracker = MagicMock()

        with patch("specify_cli.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", fake_npm_claude), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_npm_claude), \
             patch("shutil.which", return_value=None):
            result = check_tool("claude", tracker=tracker)

        assert result is True
        tracker.complete.assert_called_once_with("claude", "available")


class TestCheckToolOther:
    """Non-Claude tools should be unaffected by the fix."""

    def test_git_detected_via_path(self):
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert check_tool("git") is True

    def test_missing_tool(self):
        with patch("shutil.which", return_value=None):
            assert check_tool("nonexistent-tool") is False

    def test_kiro_fallback(self):
        """kiro-cli detection should try both kiro-cli and kiro."""
        def fake_which(name):
            return "/usr/bin/kiro" if name == "kiro" else None

        with patch("shutil.which", side_effect=fake_which):
            assert check_tool("kiro-cli") is True

    def test_rovodev_uses_acli_executable(self):
        """rovodev should resolve through the shared acli executable."""

        def fake_which(name):
            return "/usr/bin/acli" if name == "acli" else None

        with patch("shutil.which", side_effect=fake_which):
            assert check_tool("rovodev") is True

    def test_docker_agent_plugin_fallback(self):
        """docker-agent should detect a working Docker CLI plugin form."""

        def fake_which(name):
            return "/usr/bin/docker" if name == "docker" else None

        with (
            patch("shutil.which", side_effect=fake_which),
            patch("subprocess.run") as run,
        ):
            run.return_value.returncode = 0
            assert check_tool("docker-agent") is True
            run.assert_called_once_with(
                ["/usr/bin/docker", "agent", "version"],
                capture_output=True,
                check=False,
                timeout=5,
            )

    def test_docker_agent_missing(self):
        """docker-agent should be missing when neither form is installed."""
        with patch("shutil.which", return_value=None):
            assert check_tool("docker-agent") is False

    def test_docker_agent_plugin_missing(self):
        """Plain Docker CLI should not count as Docker Agent."""
        def fake_which(name):
            return "/usr/bin/docker" if name == "docker" else None

        with (
            patch("shutil.which", side_effect=fake_which),
            patch("subprocess.run") as run,
        ):
            run.return_value.returncode = 1
            assert check_tool("docker-agent") is False
