"""Non-upgradable path guidance tests for `specify self upgrade`."""

from unittest.mock import patch

from specify_cli import app

from tests.self_upgrade_helpers import (
    mock_urlopen_response,
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
    runner,
    strip_ansi,
)

# ===========================================================================
# Phase 5 — User Story 3: non-upgradable path guidance (P3)
# ===========================================================================


class TestUvxEphemeral:
    """uvx ephemeral path emits exact one-liner, no installer call."""

    def test_uvx_argv0_prints_exact_one_liner_and_exits_zero(
        self,
        uvx_ephemeral_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 0
        expected = (
            "Running via uvx (ephemeral); the next uvx invocation already "
            "resolves to latest — no upgrade action needed."
        )
        assert expected in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_offline_still_exits_zero_without_tag_resolution(
        self,
        uvx_ephemeral_argv0,
        clean_environ,
    ):
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=AssertionError("non-upgradable uvx path must not hit network"),
        ):
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 0
        assert "uvx (ephemeral)" in strip_ansi(result.output)


class TestSourceCheckout:
    """Editable install path emits git pull guidance."""

    def test_source_checkout_prints_git_pull_guidance(
        self,
        unsupported_argv0,
        tmp_path,
        clean_environ,
    ):
        fake_tree = tmp_path / "worktree"
        fake_tree.mkdir()
        (fake_tree / ".git").mkdir()

        with patch("specify_cli._version._editable_marker_seen", return_value=True), patch(
            "specify_cli._version._source_checkout_path", return_value=fake_tree
        ), patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert f"Running from a source checkout at {fake_tree}" in out
        assert "git pull" in out
        assert "pip install -e ." in out
        assert mock_run.call_count == 0

    def test_source_checkout_without_path_mentions_checkout_directory(
        self,
        unsupported_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version._editable_marker_seen", return_value=True), patch(
            "specify_cli._version._source_checkout_path", return_value=None
        ), patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        out = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "checkout path could not be detected" in out
        assert "from your checkout directory" in out
        assert "(path unavailable)" not in out
        assert mock_run.call_count == 0


class TestUnsupported:
    """Unsupported path enumerates manual reinstall commands."""

    def test_unsupported_prints_both_reinstall_commands(
        self,
        unsupported_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version._editable_marker_seen", return_value=False), patch(
            "specify_cli._version.shutil.which", return_value=None
        ), patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Could not identify your install method automatically" in out
        assert (
            "uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@vX.Y.Z"
        ) in out
        assert (
            "pipx install --force git+https://github.com/github/spec-kit.git@vX.Y.Z"
            in out
        )
        assert mock_run.call_count == 0

    def test_unsupported_offline_degrades_to_placeholder_manual_commands(
        self,
        unsupported_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version._editable_marker_seen", return_value=False), patch(
            "specify_cli._version.shutil.which", return_value=None
        ), patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=AssertionError("unsupported guidance should not require network"),
        ):
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Could not identify your install method automatically" in out
        assert (
            "uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@vX.Y.Z"
        ) in out
        assert (
            "pipx install --force git+https://github.com/github/spec-kit.git@vX.Y.Z"
            in out
        )


class TestDryRunNonUpgradablePaths:
    """--dry-run on non-upgradable paths emits guidance, not preview."""

    def test_dry_run_on_uvx_ephemeral_emits_guidance_not_preview(
        self,
        uvx_ephemeral_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Dry run — no changes will be made." not in out
        assert "uvx (ephemeral)" in out

    def test_dry_run_on_unsupported_emits_manual_commands(
        self,
        unsupported_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version._editable_marker_seen", return_value=False), patch(
            "specify_cli._version.shutil.which", return_value=None
        ), patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert result.exit_code == 0
        assert "Could not identify your install method" in strip_ansi(result.output)
