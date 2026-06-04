"""Tests for check_tool() — Claude Code CLI detection across install methods.

Covers issue https://github.com/github/spec-kit/issues/550:
  `specify check` reports "Claude Code CLI (not found)" even when claude is
  installed via npm-local (the default `claude` installer path).
"""

from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from specify_cli import app, check_tool
from specify_cli.integrations import get_integration
from tests.conftest import strip_ansi


runner = CliRunner()


class TestCheckToolClaude:
    """Claude CLI detection must work for all install methods."""

    def test_detected_via_migrate_installer_path(self, tmp_path):
        """claude migrate-installer puts binary at ~/.claude/local/claude."""
        fake_claude = tmp_path / "claude"
        fake_claude.touch()

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

        # Neither the migrate-installer path nor PATH has claude
        fake_migrate = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli.CLAUDE_LOCAL_PATH", fake_migrate), \
             patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_migrate), \
             patch("specify_cli.CLAUDE_NPM_LOCAL_PATH", fake_npm_claude), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_npm_claude), \
             patch("shutil.which", return_value=None):
            assert check_tool("claude") is True

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


class TestIsCliAvailable:
    """Integration.is_cli_available() must encode correct detection logic."""

    def test_rovodev_cli_executable_is_acli(self):
        """RovodevIntegration.cli_executable should return 'acli'."""
        impl = get_integration("rovodev")
        assert impl.cli_executable == "acli"

    def test_rovodev_is_cli_available_uses_acli(self):
        """RovodevIntegration.is_cli_available() checks for 'acli', not 'rovodev'."""
        impl = get_integration("rovodev")

        with patch("shutil.which", side_effect=lambda name: "/usr/bin/acli" if name == "acli" else None):
            assert impl.is_cli_available() is True

        with patch("shutil.which", return_value=None):
            assert impl.is_cli_available() is False

    def test_kiro_is_cli_available_accepts_kiro_cli(self):
        """KiroCliIntegration.is_cli_available() returns True for 'kiro-cli' binary."""
        impl = get_integration("kiro-cli")

        with patch("shutil.which", side_effect=lambda name: "/usr/bin/kiro-cli" if name == "kiro-cli" else None):
            assert impl.is_cli_available() is True

    def test_kiro_is_cli_available_accepts_legacy_kiro(self):
        """KiroCliIntegration.is_cli_available() accepts the legacy 'kiro' binary."""
        impl = get_integration("kiro-cli")

        with patch("shutil.which", side_effect=lambda name: "/usr/bin/kiro" if name == "kiro" else None):
            assert impl.is_cli_available() is True

    def test_kiro_is_cli_available_false_when_neither(self):
        """KiroCliIntegration.is_cli_available() returns False when neither binary exists."""
        impl = get_integration("kiro-cli")

        with patch("shutil.which", return_value=None):
            assert impl.is_cli_available() is False

    def test_claude_is_cli_available_local_path(self, tmp_path):
        """ClaudeIntegration.is_cli_available() finds claude via local path."""
        impl = get_integration("claude")
        fake_claude = tmp_path / "claude"
        fake_claude.touch()
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_claude), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("shutil.which", return_value=None):
            assert impl.is_cli_available() is True

    def test_claude_is_cli_available_npm_local_path(self, tmp_path):
        """ClaudeIntegration.is_cli_available() finds claude via npm-local path."""
        impl = get_integration("claude")
        fake_npm = tmp_path / "node_modules" / ".bin" / "claude"
        fake_npm.parent.mkdir(parents=True)
        fake_npm.touch()
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_npm), \
             patch("shutil.which", return_value=None):
            assert impl.is_cli_available() is True

    def test_claude_is_cli_available_path(self, tmp_path):
        """ClaudeIntegration.is_cli_available() finds claude via PATH."""
        impl = get_integration("claude")
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("shutil.which", return_value="/usr/local/bin/claude"):
            assert impl.is_cli_available() is True

    def test_claude_is_cli_available_not_found(self, tmp_path):
        """ClaudeIntegration.is_cli_available() returns False when not installed."""
        impl = get_integration("claude")
        fake_missing = tmp_path / "nonexistent" / "claude"

        with patch("specify_cli._utils.CLAUDE_LOCAL_PATH", fake_missing), \
             patch("specify_cli._utils.CLAUDE_NPM_LOCAL_PATH", fake_missing), \
             patch("shutil.which", return_value=None):
            assert impl.is_cli_available() is False

    def test_default_integration_uses_key(self):
        """Integrations without an override use key as cli_executable."""
        # Use a non-CLI integration to test the default; any MarkdownIntegration
        # without a cli_executable override works.
        impl = get_integration("gemini")
        assert impl.cli_executable == impl.key


class TestCheckTip:
    """`specify check` should point users to the existing version check."""

    def test_check_shows_self_check_tip(self):
        with patch("specify_cli.check_tool", return_value=True):
            result = runner.invoke(app, ["check"])

        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert (
            "Tip: Run 'specify self check' to verify you have the latest CLI version"
            in output
        )

    def test_check_tip_does_not_fetch_latest_release(self):
        with (
            patch("specify_cli.check_tool", return_value=True),
            patch(
                "specify_cli._version._fetch_latest_release_tag",
                side_effect=AssertionError("latest release lookup should not run"),
            ) as fetch_latest,
        ):
            result = runner.invoke(app, ["check"])

        assert result.exit_code == 0
        fetch_latest.assert_not_called()
