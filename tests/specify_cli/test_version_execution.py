"""Installer execution, verification, and error-path tests for `specify self upgrade`."""

import errno
import os
import subprocess
from unittest.mock import patch

from specify_cli import app
from specify_cli._version import _runs_from_uv_tool_env_on_windows

from tests.specify_cli.self_upgrade_helpers import (
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
    _completed_process,
    mock_urlopen_response,
    requires_posix,
    runner,
    strip_ansi,
)

# ===========================================================================
# Phase 6 — User Story 4: failure recovery (P2)
# ===========================================================================


class TestInstallerMissing:
    """Installer disappeared between detection and run → exit 3."""

    def test_uv_missing_exits_3(self, uv_tool_argv0, clean_environ):
        which_results = {"specify": "/usr/local/bin/specify"}
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda n: which_results.get(n)
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        out = strip_ansi(result.output)
        assert "Installer uv not found on PATH; reinstall it and retry." in out
        assert "Upgrading specify-cli" not in out

    def test_pipx_missing_exits_3(self, pipx_argv0, clean_environ):
        which_results = {}
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda n: which_results.get(n)
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        assert "Installer pipx not found on PATH" in strip_ansi(result.output)

    def test_absolute_installer_path_does_not_require_path_lookup(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/bin/sh\n")
        fake_uv.chmod(0o755)
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ), patch(
            "specify_cli._version._verify_upgrade", return_value="0.7.6"
        ), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                str(fake_uv),
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(0)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 0

    @requires_posix
    def test_relative_installer_path_does_not_require_path_lookup(
        self, monkeypatch, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "uv"
        fake_uv.write_text("#!/bin/sh\n")
        fake_uv.chmod(0o755)
        monkeypatch.chdir(tmp_path)
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ), patch(
            "specify_cli._version._verify_upgrade", return_value="0.7.6"
        ), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                "./uv",
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(0)]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert mock_run.call_args.args[0][0] == "./uv"

    @requires_posix
    def test_relative_installer_path_missing_gets_path_specific_message(
        self, monkeypatch, uv_tool_argv0, clean_environ, tmp_path
    ):
        monkeypatch.chdir(tmp_path)
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                "./uv",
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 3
        assert (
            "Installer path ./uv no longer exists; reinstall it and retry."
            in strip_ansi(result.output)
        )
        assert "not found on PATH" not in strip_ansi(result.output)

    def test_resolved_absolute_installer_removed_before_exec_gets_missing_path_message(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/bin/sh\n")
        fake_uv.chmod(0o755)

        def fake_run(argv, *args, **kwargs):
            fake_uv.unlink()
            raise FileNotFoundError(str(fake_uv))

        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which",
            side_effect=lambda name: str(fake_uv) if name == "uv" else None,
        ), patch("specify_cli._version.subprocess.run", side_effect=fake_run), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 3
        assert (
            f"Installer path {fake_uv} no longer exists; reinstall it and retry."
            in strip_ansi(result.output)
        )

    def test_absolute_installer_path_not_executable_gets_specific_message(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/bin/sh\n")
        fake_uv.chmod(0o644)
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version.os.access", return_value=False), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                str(fake_uv),
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        assert (
            f"Installer path {fake_uv} is not an executable file; fix the path or reinstall it and retry."
            in strip_ansi(result.output)
        )

    @requires_posix
    def test_relative_installer_path_not_executable_gets_path_specific_message(
        self, monkeypatch, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "uv"
        fake_uv.write_text("#!/bin/sh\n")
        fake_uv.chmod(0o644)
        monkeypatch.chdir(tmp_path)
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version.os.access", return_value=False), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                "./uv",
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        out = strip_ansi(result.output)
        assert result.exit_code == 3
        assert (
            "Installer path ./uv is not an executable file; fix the path or reinstall it and retry."
            in out
        )
        assert "Installer ./uv is not executable" not in out

    def test_real_installer_exit_126_is_not_treated_as_invalid_path(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(126)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 126
        out = strip_ansi(result.output)
        assert "Upgrade failed. Installer exit code: 126." in out
        assert "not an executable file" not in out

    def test_absolute_installer_path_missing_gets_path_specific_message(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "missing-installer" / "uv"
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                str(fake_uv),
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        assert (
            f"Installer path {fake_uv} no longer exists; reinstall it and retry."
            in strip_ansi(result.output)
        )
        mock_run.assert_not_called()

    def test_exec_oserror_is_treated_as_invalid_installer(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        fake_uv.chmod(0o755)
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                str(fake_uv),
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ), patch(
            "specify_cli._version.subprocess.run",
            side_effect=PermissionError("Permission denied"),
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        out = strip_ansi(result.output)
        assert f"Installer path {fake_uv} is not an executable file" in out
        assert "not found on PATH" not in out

    def test_bare_invalid_installer_message_does_not_call_it_a_path(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                "uv",
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ), patch(
            "specify_cli._version.subprocess.run",
            side_effect=PermissionError("Permission denied"),
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 3
        out = strip_ansi(result.output)
        assert "Installer uv is not executable" in out
        assert "Installer path uv" not in out

    def test_exec_oserror_errno_is_treated_as_invalid_installer(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        fake_uv.chmod(0o755)
        invalid_error = OSError(errno.ENOEXEC, "Exec format error")
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                str(fake_uv),
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ), patch("specify_cli._version.subprocess.run", side_effect=invalid_error):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        out = strip_ansi(result.output)
        assert f"Installer path {fake_uv} is not an executable file" in out
        assert "not found on PATH" not in out

    def test_transient_exec_oserror_is_not_treated_as_invalid_installer(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        fake_uv.chmod(0o755)
        transient_error = OSError(errno.EMFILE, "Too many open files")
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda name: None
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"), patch(
            "specify_cli._version._assemble_installer_argv",
            return_value=[
                str(fake_uv),
                "tool",
                "install",
                "specify-cli",
                "--force",
                "--from",
                "git+https://github.com/github/spec-kit.git@v0.7.6",
            ],
        ), patch("specify_cli._version.subprocess.run", side_effect=transient_error):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        # Transient/unknown OSErrors are re-raised rather than mapped to the
        # invalid-installer exit 3, so the CLI surfaces them as an uncaught
        # error: exit code 1 with the original OSError preserved.
        assert result.exit_code == 1
        assert isinstance(result.exception, OSError)


class TestInstallerFailed:
    """Installer non-zero exit → propagate code, print rollback hint."""

    def test_installer_exit_2_propagates(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(2)]  # installer fails
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Upgrade failed. Installer exit code: 2." in out
        assert "Try again or run the command manually:" in out
        assert "git+https://github.com/github/spec-kit.git@v0.7.6" in out
        assert (
            "To pin back to the previous version: "
            "uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@v0.7.5"
        ) in out
        # No verification attempted after a failed installer run.
        assert mock_run.call_count == 1

    def test_installer_exit_127_propagates(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(127)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 127

    def test_installer_timeout_prints_timeout_specific_message(
        self, uv_tool_argv0, clean_environ, monkeypatch
    ):
        monkeypatch.setenv("SPECIFY_UPGRADE_TIMEOUT_SECS", "12")
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                subprocess.TimeoutExpired(cmd=["uv"], timeout=12)
            ]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 124
        out = strip_ansi(result.output)
        assert "Upgrade timed out while waiting for the installer subprocess." in out
        assert "SPECIFY_UPGRADE_TIMEOUT_SECS=12" in out

    def test_non_finite_timeout_warns_and_runs_without_timeout(
        self, uv_tool_argv0, clean_environ, monkeypatch
    ):
        monkeypatch.setenv("SPECIFY_UPGRADE_TIMEOUT_SECS", "nan")
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Ignoring invalid SPECIFY_UPGRADE_TIMEOUT_SECS='nan'" in strip_ansi(
            result.output
        )
        assert mock_run.call_args_list[0].kwargs["timeout"] is None

    def test_real_installer_exit_124_is_not_treated_as_timeout(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(124)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 124
        out = strip_ansi(result.output)
        assert "Upgrade failed. Installer exit code: 124." in out
        assert "Upgrade timed out while waiting for the installer subprocess." not in out

    def test_pipx_failure_prints_pipx_rollback_hint(self, pipx_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="pipx"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(2)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert (
            "To pin back to the previous version: pipx install --force "
            "git+https://github.com/github/spec-kit.git@v0.7.5"
        ) in out

    def test_rollback_hint_accepts_normalizable_stable_snapshot(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="v0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(2)]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert (
            "To pin back to the previous version: uv tool install specify-cli --force "
            "--from git+https://github.com/github/spec-kit.git@v0.7.5"
        ) in out
        assert "Previous version was not an exact stable release tag" not in out

    def test_prerelease_failure_degrades_rollback_hint_to_releases_page(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.0.0rc1"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.0.0"})
            mock_run.side_effect = [_completed_process(2)]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Previous version was not an exact stable release tag" in out
        assert "https://github.com/github/spec-kit/releases" in out
        assert "git+https://github.com/github/spec-kit.git@v1.0.0rc1" not in out


class TestWindowsUvToolEnvironment:
    """Windows uv-tool installs cannot reinstall the environment they run from."""

    def test_windows_uv_tool_prints_command_without_running_installer(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.2.2"
        ), patch(
            "specify_cli._version._runs_from_uv_tool_env_on_windows", return_value=True
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.2.4"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Not upgrading specify-cli 1.2.2 → v1.2.4" in out
        assert (
            "  uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@v1.2.4"
        ) in out
        assert "Upgrade failed" not in out
        assert mock_run.call_count == 0

    def test_windows_pipx_still_runs_installer(self, pipx_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="pipx"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.2.2"
        ), patch(
            "specify_cli._version._runs_from_uv_tool_env_on_windows", return_value=True
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.2.4"})
            mock_run.side_effect = [
                _completed_process(0),  # installer
                _completed_process(0, stdout="specify 1.2.4\n"),  # verify
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Upgraded specify-cli: 1.2.2 → 1.2.4" in strip_ansi(result.output)
        assert mock_run.call_count == 2

    def test_windows_uv_tool_dry_run_previews_manual_command(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.2.2"
        ), patch(
            "specify_cli._version._runs_from_uv_tool_env_on_windows", return_value=True
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.2.4"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Dry run — no changes will be made." in out
        assert "Target version: v1.2.4" in out
        assert (
            "Command that would be executed: (none — on Windows, uv cannot "
            "replace the tool environment specify is running from)"
        ) in " ".join(out.split())
        assert (
            "Run it yourself once this command exits:\n"
            "  uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@v1.2.4\n"
        ) in out
        assert mock_run.call_count == 0

    def test_windows_uv_tool_dry_run_with_tag_previews_pinned_command(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.2.2"
        ), patch(
            "specify_cli._version._runs_from_uv_tool_env_on_windows", return_value=True
        ):
            result = runner.invoke(
                app, ["self", "upgrade", "--dry-run", "--tag", "v1.2.0"]
            )

        assert result.exit_code == 0
        assert (
            "\n  uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@v1.2.0\n"
        ) in strip_ansi(result.output)
        mock_urlopen.assert_not_called()
        assert mock_run.call_count == 0

    def test_windows_uv_tool_dry_run_matches_real_run_command(
        self, uv_tool_argv0, clean_environ
    ):
        outputs = {}
        for args in (["self", "upgrade", "--dry-run"], ["self", "upgrade"]):
            with patch(
                "specify_cli.authentication.http.urllib.request.urlopen"
            ) as mock_urlopen, patch(
                "specify_cli._version.shutil.which", return_value="uv"
            ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
                "specify_cli._version._get_installed_version", return_value="1.2.2"
            ), patch(
                "specify_cli._version._runs_from_uv_tool_env_on_windows",
                return_value=True,
            ):
                mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.2.4"})
                result = runner.invoke(app, args)
            assert result.exit_code == 0
            assert mock_run.call_count == 0
            outputs[len(args)] = strip_ansi(result.output)

        manual_steps = (
            "Run it yourself once this command exits:\n"
            "  uv tool install specify-cli --force --from "
            "git+https://github.com/github/spec-kit.git@v1.2.4\n"
        )
        assert manual_steps in outputs[3]
        assert manual_steps in outputs[2]

    def test_non_windows_uv_tool_dry_run_still_previews_installer(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="uv"
        ), patch("specify_cli._version.subprocess.run"), patch(
            "specify_cli._version._get_installed_version", return_value="1.2.2"
        ), patch(
            "specify_cli._version._runs_from_uv_tool_env_on_windows", return_value=False
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.2.4"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert (
            "Command that would be executed: uv tool install specify-cli --force "
            "--from git+https://github.com/github/spec-kit.git@v1.2.4"
        ) in " ".join(out.split())
        assert "Run it yourself" not in out

    def test_windows_uv_tool_dry_run_without_uv_reports_missing_installer(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=None
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.2.2"
        ), patch(
            "specify_cli._version._runs_from_uv_tool_env_on_windows", return_value=True
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.2.4"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Command that would be executed: (installer uv not found on PATH)" in out
        assert "Run it yourself" not in out
        assert mock_run.call_count == 0

    def test_help_mentions_windows_uv_tool_exception(self):
        result = runner.invoke(app, ["self", "upgrade", "--help"])
        assert result.exit_code == 0
        out = " ".join(strip_ansi(result.output).split())
        assert "On Windows, uv cannot replace the uv-tool environment" in out

    def test_detects_uv_tool_environment_on_windows(self, tmp_path, monkeypatch):
        (tmp_path / "uv-receipt.toml").write_text("[tool]\n")
        monkeypatch.setattr("sys.prefix", str(tmp_path))
        monkeypatch.setattr(os, "name", "nt")
        assert _runs_from_uv_tool_env_on_windows() is True

    def test_ignores_environment_without_uv_receipt(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sys.prefix", str(tmp_path))
        monkeypatch.setattr(os, "name", "nt")
        assert _runs_from_uv_tool_env_on_windows() is False

    def test_ignores_uv_tool_environment_off_windows(self, tmp_path, monkeypatch):
        (tmp_path / "uv-receipt.toml").write_text("[tool]\n")
        monkeypatch.setattr("sys.prefix", str(tmp_path))
        monkeypatch.setattr(os, "name", "posix")
        assert _runs_from_uv_tool_env_on_windows() is False
