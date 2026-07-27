"""Verification, resolution, and validation tests for `specify self upgrade`."""

import urllib.error
from unittest.mock import patch

import pytest
import specify_cli
from specify_cli import app

from tests.self_upgrade_helpers import (
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
    SENTINEL_GH_TOKEN,
    SENTINEL_GITHUB_TOKEN,
    _InstallMethod,
    _UpgradePlan,
    _completed_process,
    _verify_upgrade,
    mock_urlopen_response,
    runner,
    strip_ansi,
)

# ===========================================================================
# Phase 6 — User Story 4: failure recovery (P2)
# ===========================================================================


class TestVerificationMismatch:
    """Installer says 0 but the binary is still the old version → exit 2."""

    def test_installer_ok_but_verify_returns_old_version(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),  # installer OK
                _completed_process(0, stdout="specify 0.7.5\n"),  # verify: OLD!
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Verification failed" in out
        assert "resolves to 0.7.5 (expected v0.7.6)" in out
        assert "The new version may take effect on your next invocation." in out

    def test_verify_nonzero_exit_is_not_treated_as_success(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(1, stdout="specify 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Verification failed" in out
        assert "(unknown) (expected v0.7.6)" in out

    def test_verify_accepts_pep440_equivalent_rc_version(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.9.0"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v9.9.9"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 1.0.0rc1\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v1.0.0-rc1"])

        assert result.exit_code == 0
        assert "Upgraded specify-cli: 0.9.0 → 1.0.0rc1" in strip_ansi(result.output)

    def test_verify_accepts_specify_cli_binary_name_in_version_output(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify-cli version 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Upgraded specify-cli: 0.7.5 → 0.7.6" in strip_ansi(result.output)

    def test_verify_accepts_capitalized_binary_name_in_version_output(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="Specify, version 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Upgraded specify-cli: 0.7.5 → 0.7.6" in strip_ansi(result.output)

    def test_verify_rejects_output_without_parseable_version(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify version unknown\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Verification failed" in out
        assert "(unknown) (expected v0.7.6)" in out

    def test_verify_uses_current_entrypoint_when_not_on_path(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        assert uv_tool_argv0.exists()
        assert uv_tool_argv0.is_file()

        plan = _UpgradePlan(
            method=_InstallMethod.UV_TOOL,
            current_version="0.7.5",
            target_tag="v0.7.6",
            installer_argv=["/usr/bin/uv", "tool", "install", "specify-cli"],
            preview_summary="",
            pre_upgrade_snapshot="0.7.5",
        )

        with patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.os.access", return_value=True
        ):
            mock_run.return_value = _completed_process(0, stdout="specify 0.7.6\n")
            verified = _verify_upgrade(plan)

        assert verified == "0.7.6"
        assert mock_run.call_args.args[0][0] == str(uv_tool_argv0)
        assert mock_run.call_args.kwargs["timeout"] == specify_cli._version._VERIFY_TIMEOUT_SECS

    def test_verify_falls_back_to_path_when_current_entrypoint_is_not_executable(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        plan = _UpgradePlan(
            method=_InstallMethod.UV_TOOL,
            current_version="0.7.5",
            target_tag="v0.7.6",
            installer_argv=["/usr/bin/uv", "tool", "install", "specify-cli"],
            preview_summary="",
            pre_upgrade_snapshot="0.7.5",
        )

        with patch(
            "specify_cli._version.shutil.which",
            side_effect=lambda name: "/usr/local/bin/specify" if name == "specify" else None,
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version.os.access", return_value=False
        ):
            mock_run.return_value = _completed_process(0, stdout="specify 0.7.6\n")
            verified = _verify_upgrade(plan)

        assert verified == "0.7.6"
        assert mock_run.call_args.args[0][0] == "/usr/local/bin/specify"

    def test_verify_ignores_python_entrypoint_and_falls_back_to_specify(
        self,
        clean_environ,
        tmp_path,
    ):
        fake_python = tmp_path / "python3"
        fake_python.write_text("#!/bin/sh\n")
        fake_python.chmod(0o755)

        plan = _UpgradePlan(
            method=_InstallMethod.UV_TOOL,
            current_version="0.7.5",
            target_tag="v0.7.6",
            installer_argv=["/usr/bin/uv", "tool", "install", "specify-cli"],
            preview_summary="",
            pre_upgrade_snapshot="0.7.5",
        )

        with patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: "/usr/local/bin/specify" if name == "specify" else None
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version.sys.argv", [str(fake_python)]
        ), patch(
            "specify_cli._version.os.access", return_value=True
        ):
            mock_run.return_value = _completed_process(0, stdout="specify 0.7.6\n")
            verified = _verify_upgrade(plan)

        assert verified == "0.7.6"
        assert mock_run.call_args.args[0][0] == "/usr/local/bin/specify"

    def test_verify_accepts_specify_cli_named_current_entrypoint(
        self,
        clean_environ,
        tmp_path,
    ):
        fake_specify_cli = tmp_path / "specify-cli"
        fake_specify_cli.write_text("#!/bin/sh\n")
        fake_specify_cli.chmod(0o755)

        plan = _UpgradePlan(
            method=_InstallMethod.UV_TOOL,
            current_version="0.7.5",
            target_tag="v0.7.6",
            installer_argv=["/usr/bin/uv", "tool", "install", "specify-cli"],
            preview_summary="",
            pre_upgrade_snapshot="0.7.5",
        )

        with patch("specify_cli._version.shutil.which", return_value=None), patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch("specify_cli._version.sys.argv", [str(fake_specify_cli)]), patch(
            "specify_cli._version.os.access", return_value=True
        ):
            mock_run.return_value = _completed_process(0, stdout="specify 0.7.6\n")
            verified = _verify_upgrade(plan)

        assert verified == "0.7.6"
        assert mock_run.call_args.args[0][0] == str(fake_specify_cli)


class TestResolutionFailures:
    """Pre-installer resolution failure → exit 1, reusing the resolver category strings."""

    def test_offline_exits_1_with_phase1_string(self, uv_tool_argv0, clean_environ):
        with patch(
            "specify_cli.authentication.http.urllib.request.urlopen",
            side_effect=urllib.error.URLError("nope"),
        ):
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 1
        assert "Upgrade aborted: offline or timeout" in strip_ansi(result.output)

    def test_rate_limited_exits_1(self, uv_tool_argv0, clean_environ):
        err = urllib.error.HTTPError(
            url="https://api.github.com",
            code=403,
            msg="rate limited",
            hdrs={},  # type: ignore[arg-type]
            fp=None,
        )
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=err):
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 1
        assert (
            "Upgrade aborted: rate limited (configure ~/.specify/auth.json with a GitHub token)"
            in strip_ansi(result.output)
        )

    def test_http_500_exits_1(self, uv_tool_argv0, clean_environ):
        err = urllib.error.HTTPError(
            url="https://api.github.com",
            code=500,
            msg="srv err",
            hdrs={},  # type: ignore[arg-type]
            fp=None,
        )
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=err):
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 1
        assert "Upgrade aborted: HTTP 500" in strip_ansi(result.output)

    @pytest.mark.parametrize(
        "code, expected",
        [
            # 429 (Too Many Requests / secondary rate limit) gets the same
            # actionable token hint as 403; other statuses surface verbatim.
            (
                429,
                "Upgrade aborted: rate limited (configure ~/.specify/auth.json "
                "with a GitHub token)",
            ),
            (404, "Upgrade aborted: HTTP 404"),
            (502, "Upgrade aborted: HTTP 502"),
        ],
    )
    def test_http_error_categorization(
        self, code, expected, uv_tool_argv0, clean_environ
    ):
        err = urllib.error.HTTPError(
            url="https://api.github.com",
            code=code,
            msg="err",
            hdrs={},  # type: ignore[arg-type]
            fp=None,
        )
        with patch("specify_cli.authentication.http.urllib.request.urlopen", side_effect=err):
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 1
        assert expected in strip_ansi(result.output)

    def test_unparseable_resolved_release_tag_exits_1_without_traceback(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "release-main"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 1
        out = strip_ansi(result.output)
        assert "resolved release tag is not a comparable version" in out
        assert "release-main" not in out
        assert "Traceback" not in out
        assert mock_run.call_count == 0


class TestTagValidation:
    """--tag regex enforcement."""

    def test_valid_stable_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.7.6"],
            )
        assert result.exit_code == 0

    def test_valid_dev_suffix_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0.dev0"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0.dev0" in strip_ansi(result.output)

    def test_valid_rc_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v1.0.0-rc1"],
            )
        assert result.exit_code == 0

    def test_valid_beta_dot_tag_uses_pep440_equivalent_for_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="1.0.0b1"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--tag", "v1.0.0-beta.1"],
            )
        assert result.exit_code == 0
        assert "Already on requested release: v1.0.0-beta.1" in strip_ansi(
            result.output
        )

    def test_valid_build_metadata_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0+build.42"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0+build.42" in strip_ansi(result.output)

    def test_uppercase_v_prefix_is_folded_to_lowercase(
        self, uv_tool_argv0, clean_environ
    ):
        # A pasted uppercase `V` prefix is accepted and normalized to `v` so
        # the git ref matches the canonical lowercase release tag.
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "V0.7.6"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.7.6" in strip_ansi(result.output)

    def test_valid_prerelease_with_build_metadata_tag(
        self, uv_tool_argv0, clean_environ
    ):
        # Prerelease and build-metadata suffixes compose (PEP 440 / semver).
        with patch("specify_cli._version.shutil.which", return_value="uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v1.0.0-rc1+build.42"],
            )
        assert result.exit_code == 0
        assert "Target version: v1.0.0-rc1+build.42" in strip_ansi(result.output)

    @pytest.mark.parametrize(
        "bad_tag",
        [
            "latest",
            "0.7.5",
            "main",
            "v7",
            "",
            "v1.2.3abc",
            "v1.2.3...",
            "v1.2.3++",
            "v\uff11.2.3",
            "v1.\u0662.3",
        ],
    )
    def test_invalid_tags_rejected(self, bad_tag, uv_tool_argv0, clean_environ):
        result = runner.invoke(app, ["self", "upgrade", "--tag", bad_tag])
        assert result.exit_code == 1
        output = strip_ansi(result.output)
        assert "Invalid --tag" in output or "expected vMAJOR.MINOR.PATCH" in output


class TestUnknownCurrent:
    """'unknown' current version renders literally in notice and success message."""

    def test_unknown_current_renders_literal_in_notice(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="unknown"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Upgrading specify-cli unknown → v0.7.6 via uv tool:" in out
        assert "Upgraded specify-cli: unknown → 0.7.6" in out

    def test_unknown_current_rollback_hint_degrades(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="unknown"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(2)]  # installer fails
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Could not determine the previous version" in out
        assert "https://github.com/github/spec-kit/releases" in out


class TestTokenScrubbing:
    """GH_TOKEN / GITHUB_TOKEN are stripped from every child env."""

    def test_env_passed_to_subprocess_has_no_github_tokens(
        self,
        uv_tool_argv0,
        monkeypatch,
    ):
        monkeypatch.setenv("GH_TOKEN", SENTINEL_GH_TOKEN)
        monkeypatch.setenv("GITHUB_TOKEN", SENTINEL_GITHUB_TOKEN)
        response = mock_urlopen_response({"tag_name": "v0.7.6"})

        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli.authentication.http.urllib.request.build_opener"
        ) as mock_build_opener, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = response
            mock_build_opener.return_value.open.return_value = response
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            runner.invoke(app, ["self", "upgrade"])

        assert mock_run.call_count >= 1
        for call in mock_run.call_args_list:
            env_kwarg = call.kwargs.get("env") or {}
            assert "GH_TOKEN" not in env_kwarg, f"env leaked GH_TOKEN: {env_kwarg!r}"
            assert "GITHUB_TOKEN" not in env_kwarg
            for v in env_kwarg.values():
                assert SENTINEL_GH_TOKEN not in v
                assert SENTINEL_GITHUB_TOKEN not in v

    def test_env_scrubbing_is_case_insensitive(
        self,
        uv_tool_argv0,
        monkeypatch,
    ):
        monkeypatch.setenv("gh_token", SENTINEL_GH_TOKEN)
        monkeypatch.setenv("GitHub_Token", SENTINEL_GITHUB_TOKEN)
        response = mock_urlopen_response({"tag_name": "v0.7.6"})

        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli.authentication.http.urllib.request.build_opener"
        ) as mock_build_opener, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = response
            mock_build_opener.return_value.open.return_value = response
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            runner.invoke(app, ["self", "upgrade"])

        assert mock_run.call_count >= 1
        for call in mock_run.call_args_list:
            env_kwarg = call.kwargs.get("env") or {}
            assert "gh_token" not in env_kwarg
            assert "GitHub_Token" not in env_kwarg
            for v in env_kwarg.values():
                assert SENTINEL_GH_TOKEN not in v
                assert SENTINEL_GITHUB_TOKEN not in v

    def test_env_scrubbing_removes_github_token_variants(self, monkeypatch):
        monkeypatch.setenv("GH_PAT", "gh-pat")
        monkeypatch.setenv("GH_TOKEN_FILE", "gh-token-file")
        monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "enterprise-gh")
        monkeypatch.setenv("GH_ENTERPRISE_SECRET", "enterprise-secret")
        monkeypatch.setenv("GH_ENTERPRISE_PRIVATE_KEY", "enterprise-key")
        monkeypatch.setenv("GITHUB_PAT", "github-pat")
        monkeypatch.setenv("GITHUB_TOKEN_PATH", "github-token-path")
        monkeypatch.setenv("GITHUB_ENTERPRISE_TOKEN", "enterprise-github")
        monkeypatch.setenv("GITHUB_API_TOKEN", "api-token")
        monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "app-private-key")
        monkeypatch.setenv("GITHUB_OAUTH_CLIENT_SECRET", "oauth-secret")
        monkeypatch.setenv("HOMEBREW_GITHUB_API_TOKEN", "homebrew-token")
        monkeypatch.setenv("NOTGITHUB_TOKEN", "not-github-kept")
        monkeypatch.setenv("GHOST_API_TOKEN", "ghost-kept")
        monkeypatch.setenv("GHIDRA_API_KEY", "ghidra-kept")
        monkeypatch.setenv("UNRELATED_TOKEN", "kept")

        env = specify_cli._version._scrubbed_env()

        assert "GH_PAT" not in env
        assert "GH_TOKEN_FILE" not in env
        assert "GH_ENTERPRISE_TOKEN" not in env
        assert "GH_ENTERPRISE_SECRET" not in env
        assert "GH_ENTERPRISE_PRIVATE_KEY" not in env
        assert "GITHUB_PAT" not in env
        assert "GITHUB_TOKEN_PATH" not in env
        assert "GITHUB_ENTERPRISE_TOKEN" not in env
        assert "GITHUB_API_TOKEN" not in env
        assert "GITHUB_APP_PRIVATE_KEY" not in env
        assert "GITHUB_OAUTH_CLIENT_SECRET" not in env
        assert "HOMEBREW_GITHUB_API_TOKEN" not in env
        assert env["NOTGITHUB_TOKEN"] == "not-github-kept"
        assert env["GHOST_API_TOKEN"] == "ghost-kept"
        assert env["GHIDRA_API_KEY"] == "ghidra-kept"
        assert env["UNRELATED_TOKEN"] == "kept"

    def test_env_scrubbing_strips_noncredential_github_vars_by_design(
        self, monkeypatch
    ):
        # The scrub is intentionally broad: every GH_/GITHUB_-prefixed name is
        # removed from the installer subprocess env, including non-credential
        # context vars. This is a deliberate fail-safe so credential-adjacent
        # names that lack a recognized suffix (e.g. GH_TOKEN_FILE,
        # GITHUB_TOKEN_PATH, asserted above) can never leak. The installer
        # (`uv tool install` / `pipx install` of a public package) does not
        # consume routing/context vars like GITHUB_REPOSITORY, so nothing the
        # subprocess needs is lost by stripping them.
        monkeypatch.setenv("GH_HOST", "github.example.com")
        monkeypatch.setenv("GH_CONFIG_DIR", "/home/u/.config/gh")
        monkeypatch.setenv("GITHUB_REPOSITORY", "github/spec-kit")
        monkeypatch.setenv("GITHUB_WORKSPACE", "/home/runner/work")
        monkeypatch.setenv("GITHUB_USER", "octocat")

        env = specify_cli._version._scrubbed_env()

        assert "GH_HOST" not in env
        assert "GH_CONFIG_DIR" not in env
        assert "GITHUB_REPOSITORY" not in env
        assert "GITHUB_WORKSPACE" not in env
        assert "GITHUB_USER" not in env
