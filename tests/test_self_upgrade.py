"""Tests for `specify self upgrade`.

These cases patch subprocess, PATH lookup, and release-tag resolution so the
suite stays isolated from the real environment.
"""

import errno
import json
import os
import subprocess
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

import specify_cli
from specify_cli import app
from specify_cli._version import (
    _InstallMethod,
    _INSTALLER_TIMEOUT_SENTINEL,
    _UpgradePlan,
    _assemble_installer_argv,
    _detect_install_method,
    _verify_upgrade,
)

from tests.conftest import strip_ansi

runner = CliRunner()

SENTINEL_GH_TOKEN = "SENTINEL-GH-TOKEN-VALUE"
SENTINEL_GITHUB_TOKEN = "SENTINEL-GITHUB-TOKEN-VALUE"


def _mock_urlopen_response(payload: dict) -> MagicMock:
    """Build a urlopen() context-manager mock whose .read() returns the JSON payload."""
    body = json.dumps(payload).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


def _completed_process(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess:
    """Build a subprocess.CompletedProcess for installer / verification calls."""
    return subprocess.CompletedProcess(
        args=["mocked"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


@pytest.fixture
def clean_environ(monkeypatch):
    """Strip any real GH_TOKEN / GITHUB_TOKEN from the test environment."""
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


@pytest.fixture(autouse=True)
def route_open_url_through_urlopen(monkeypatch):
    """Keep release-tag tests hermetic even when ~/.specify/auth.json exists."""

    def _open_url(url, timeout=10, extra_headers=None):
        req = specify_cli._version.urllib.request.Request(url)
        for key, value in (extra_headers or {}).items():
            req.add_header(key, value)
        return specify_cli._version.urllib.request.urlopen(req, timeout=timeout)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", _open_url)


@pytest.fixture
def uv_tool_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated `uv tool` install path under tmp HOME.

    Sets the platform-specific home/tool root env so _expand_prefix() resolves
    to a path that actually contains the fake binary. This avoids needing a
    `_UV_TOOL_ROOT_OVERRIDE` knob in production code.
    """
    if os.name == "nt":
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        fake_dir = tmp_path / "uv" / "tools" / "specify-cli" / "bin"
    else:
        monkeypatch.setenv("HOME", str(tmp_path))
        fake_dir = tmp_path / ".local" / "share" / "uv" / "tools" / "specify-cli" / "bin"
    fake_dir.mkdir(parents=True)
    fake_specify = fake_dir / "specify"
    fake_specify.write_text("#!/usr/bin/env python\n")
    fake_specify.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(fake_specify)])
    return fake_specify


@pytest.fixture
def pipx_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated pipx install path under tmp HOME."""
    if os.name == "nt":
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        fake_dir = tmp_path / "pipx" / "venvs" / "specify-cli" / "bin"
    else:
        monkeypatch.setenv("HOME", str(tmp_path))
        fake_dir = tmp_path / ".local" / "pipx" / "venvs" / "specify-cli" / "bin"
    fake_dir.mkdir(parents=True)
    fake_specify = fake_dir / "specify"
    fake_specify.write_text("#!/usr/bin/env python\n")
    fake_specify.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(fake_specify)])
    return fake_specify


@pytest.fixture
def uvx_ephemeral_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a simulated uvx ephemeral-cache path under tmp HOME."""
    if os.name == "nt":
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        fake_dir = tmp_path / "uv" / "cache" / "archive-v0" / "abc123" / "bin"
    else:
        monkeypatch.setenv("HOME", str(tmp_path))
        fake_dir = tmp_path / ".cache" / "uv" / "archive-v0" / "abc123" / "bin"
    fake_dir.mkdir(parents=True)
    fake_specify = fake_dir / "specify"
    fake_specify.write_text("#!/usr/bin/env python\n")
    fake_specify.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(fake_specify)])
    return fake_specify


@pytest.fixture
def unsupported_argv0(monkeypatch, tmp_path):
    """Point sys.argv[0] at a path that does not match any installer prefix."""
    monkeypatch.setenv("HOME", str(tmp_path))
    fake_dir = tmp_path / "random" / "location" / "bin"
    fake_dir.mkdir(parents=True)
    fake_specify = fake_dir / "specify"
    fake_specify.write_text("#!/usr/bin/env python\n")
    fake_specify.chmod(0o755)
    monkeypatch.setattr("sys.argv", [str(fake_specify)])
    return fake_specify


class TestDetectionUvTool:
    """Tier-1 path-prefix detection for uv-tool installs."""

    def test_posix_uv_tool_prefix_matches(self, uv_tool_argv0):
        method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.UV_TOOL
        assert signals.matched_tier == 1
        assert "uv/tools/specify-cli" in signals.matched_prefix.replace("\\", "/")

    def test_detection_is_deterministic(self, uv_tool_argv0):
        a = _detect_install_method()
        b = _detect_install_method()
        assert a == b == _InstallMethod.UV_TOOL

    def test_no_argv_match_falls_through_to_unsupported(self, unsupported_argv0):
        with patch("specify_cli._version.shutil.which", return_value=None), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ):
            method = _detect_install_method()
        assert method == _InstallMethod.UNSUPPORTED

    def test_include_signals_false_returns_bare_enum(self, uv_tool_argv0):
        result = _detect_install_method(include_signals=False)
        assert isinstance(result, _InstallMethod)

    def test_bare_argv0_is_resolved_via_path_lookup(self, monkeypatch, tmp_path):
        if os.name == "nt":
            monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
            fake_dir = tmp_path / "uv" / "tools" / "specify-cli" / "bin"
        else:
            monkeypatch.setenv("HOME", str(tmp_path))
            fake_dir = (
                tmp_path / ".local" / "share" / "uv" / "tools" / "specify-cli" / "bin"
            )
        fake_dir.mkdir(parents=True)
        fake_specify = fake_dir / "specify"
        fake_specify.write_text("#!/usr/bin/env python\n")
        monkeypatch.setattr("sys.argv", ["specify"])
        with patch(
            "specify_cli._version.shutil.which",
            side_effect=lambda name: str(fake_specify) if name == "specify" else None,
        ):
            method = _detect_install_method()
        assert method == _InstallMethod.UV_TOOL

    def test_prefix_match_does_not_accept_sibling_directory(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HOME", str(tmp_path))
        fake_dir = tmp_path / ".local" / "share" / "uv" / "tools" / "specify-cli2" / "bin"
        fake_dir.mkdir(parents=True)
        fake_specify = fake_dir / "specify"
        fake_specify.write_text("#!/usr/bin/env python\n")
        monkeypatch.setattr("sys.argv", [str(fake_specify)])
        with patch("specify_cli._version.shutil.which", return_value=None), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ):
            method = _detect_install_method()
        assert method == _InstallMethod.UNSUPPORTED

    def test_tier3_uv_tool_when_registry_lists_exact_name(
        self,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        def fake_which(name):
            return "/usr/bin/uv" if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/uv", "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="specify-cli v0.7.6\nother-tool v1.2.3\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.UV_TOOL
        assert signals.matched_tier == 3
        assert "uv tool list" in signals.installer_registries_consulted

    def test_unresolved_bare_argv0_skips_tier3_registry_detection(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["specify"])

        def fake_which(name):
            return "/usr/bin/uv" if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            return subprocess.CompletedProcess(
                args=argv,
                returncode=0,
                stdout="specify-cli v0.7.6\n",
                stderr="",
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.UNSUPPORTED
        assert signals.installer_registries_consulted == []

    def test_tier3_uv_tool_ignores_substring_false_positive(
        self,
        unsupported_argv0,
    ):
        def fake_which(name):
            return "/usr/bin/uv" if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/uv", "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="my-specify-cli-helper v0.1.0\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method = _detect_install_method()
        assert method == _InstallMethod.UNSUPPORTED

    def test_tier3_uv_tool_does_not_override_absolute_unsupported_entrypoint(
        self,
        unsupported_argv0,
    ):
        def fake_which(name):
            return "/usr/bin/uv" if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/uv", "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="specify-cli v0.7.6\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method = _detect_install_method()
        assert method == _InstallMethod.UNSUPPORTED

    def test_tier3_uv_tool_does_not_override_resolved_bare_unsupported_entrypoint(
        self,
        monkeypatch,
        tmp_path,
    ):
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        fake_specify = venv_bin / "specify"
        fake_specify.write_text("#!/usr/bin/env python\n")
        fake_specify.chmod(0o755)
        monkeypatch.setattr("sys.argv", ["specify"])

        def fake_which(name):
            if name == "specify":
                return str(fake_specify)
            if name == "uv":
                return "/usr/bin/uv"
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/uv", "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="specify-cli v0.7.6\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.UNSUPPORTED
        assert signals.matched_tier is None
        assert signals.installer_registries_consulted == []


class TestArgvAssemblyUvTool:
    """uv-tool installer argv shape."""

    def test_stable_tag_produces_expected_argv(self):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"):
            argv = _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.7.6")
        assert argv == [
            "/usr/bin/uv",
            "tool",
            "install",
            "specify-cli",
            "--force",
            "--from",
            "git+https://github.com/github/spec-kit.git@v0.7.6",
        ]

    def test_dev_suffix_tag_embedded_literally(self):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"):
            argv = _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.8.0.dev0")
        assert "git+https://github.com/github/spec-kit.git@v0.8.0.dev0" in argv
        assert (
            "upgrade" not in argv
        )  # never `uv tool upgrade` — does not accept --tag pinning


class TestBareUpgradeUvTool:
    """uv-tool happy path, bare invocation."""

    def test_happy_path_end_to_end(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),  # installer
                _completed_process(0, stdout="specify 0.7.6\n"),  # verify
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Upgrading specify-cli 0.7.5 → v0.7.6 via uv tool:" in out
        assert "Upgraded specify-cli: 0.7.5 → 0.7.6" in out
        assert mock_run.call_count == 2
        for call in mock_run.call_args_list:
            assert call.kwargs.get("shell", False) is False

    def test_one_user_action_no_prompt(self, uv_tool_argv0, clean_environ):
        # The single `invoke` represents the single user action — no prompt.
        # If a prompt existed, runner.invoke would hang waiting for input.
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 0


class TestAlreadyLatestUvTool:
    """already on latest, no installer launched."""

    def test_already_latest_exits_zero_no_subprocess(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.6"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release: v0.7.6" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_dev_build_ahead_of_release_reports_newer_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.7.dev0"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release or newer: 0.7.7.dev0" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_unparseable_current_version_does_not_false_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version._get_installed_version", return_value="release-main"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Already on latest release" not in out
        assert "Upgrading specify-cli release-main → v0.7.6 via uv tool:" in out
        assert mock_run.call_count == 2

    def test_literal_current_target_match_noops_when_version_is_unparseable(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version._get_installed_version", return_value="release-main"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "release-main"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release: release-main" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_pinned_older_tag_still_runs_installer(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.6"
        ):
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.5\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v0.7.5"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Already on latest release" not in out
        assert "Upgrading specify-cli 0.7.6 → v0.7.5 via uv tool:" in out
        assert mock_run.call_count == 2

    def test_pinned_rc_tag_uses_canonical_version_equality_for_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version._get_installed_version", return_value="1.0.0rc1"
        ):
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v1.0.0-rc1"])

        assert result.exit_code == 0
        assert "Already on requested release: v1.0.0-rc1" in strip_ansi(result.output)


class TestDryRunUvTool:
    """--dry-run preview path + --dry-run combined with --tag."""

    def test_dry_run_without_tag_resolves_network_but_no_subprocess(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Dry run — no changes will be made." in out
        assert "Detected install method: uv tool" in out
        assert "Current version: 0.7.5" in out
        assert "Target version: v0.7.6" in out
        assert "Command that would be executed:" in out
        assert mock_run.call_count == 0

    def test_dry_run_with_tag_skips_network(self, uv_tool_argv0, clean_environ):
        # --dry-run with --tag must NOT hit the network.
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ), patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0" in strip_ansi(result.output)
        mock_urlopen.assert_not_called()


# ===========================================================================
# Phase 4 — User Story 2: `pipx` immediate upgrade (P2)
# ===========================================================================


class TestDetectionPipx:
    """Pipx detection — tier 1 (path) and tier 3 (registry)."""

    def test_posix_pipx_prefix_matches(self, pipx_argv0):
        method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.PIPX
        assert signals.matched_tier == 1

    def test_tier3_pipx_when_no_prefix_match_but_registry_lists_it(
        self,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        def fake_which(name):
            return "/usr/bin/pipx" if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/pipx", "list", "--json"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout='{"venvs":{"specify-cli":{}}}',
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.PIPX
        assert signals.matched_tier == 3
        assert "pipx list --json" in signals.installer_registries_consulted

    def test_tier3_pipx_does_not_override_absolute_unsupported_entrypoint(
        self,
        unsupported_argv0,
    ):
        def fake_which(name):
            return "/usr/bin/pipx" if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/pipx", "list", "--json"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout='{"venvs":{"specify-cli":{}}}',
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method = _detect_install_method()
        assert method == _InstallMethod.UNSUPPORTED

    def test_tier3_pipx_ignores_malformed_json_output(
        self,
        unsupported_argv0,
    ):
        def fake_which(name):
            return "/usr/bin/pipx" if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/pipx", "list", "--json"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="not json but mentions specify-cli",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method = _detect_install_method()
        assert method == _InstallMethod.UNSUPPORTED

    def test_tier3_both_uv_tool_and_pipx_match_is_treated_as_unsupported(
        self,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        def fake_which(name):
            if name == "uv":
                return "/usr/bin/uv"
            if name == "pipx":
                return "/usr/bin/pipx"
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == ["/usr/bin/uv", "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="specify-cli v0.7.6\n",
                    stderr="",
                )
            if argv[:3] == ["/usr/bin/pipx", "list", "--json"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout='{"venvs":{"specify-cli":{}}}',
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=argv, returncode=1, stdout="", stderr=""
            )

        with patch("specify_cli._version.shutil.which", side_effect=fake_which), patch(
            "specify_cli._version.subprocess.run", side_effect=fake_run
        ), patch("specify_cli._version._editable_marker_seen", return_value=False):
            method, signals = _detect_install_method(include_signals=True)
        assert method == _InstallMethod.UNSUPPORTED
        assert signals.matched_tier is None
        assert "uv tool list" in signals.installer_registries_consulted
        assert "pipx list --json" in signals.installer_registries_consulted


class TestEditableInstallMetadata:
    def test_direct_url_editable_install_marks_source_checkout(self, tmp_path):
        project_root = tmp_path / "spec-kit"
        project_root.mkdir()
        (project_root / ".git").mkdir()

        class FakeDist:
            files = []

            def read_text(self, name):
                if name == "direct_url.json":
                    return json.dumps(
                        {
                            "dir_info": {"editable": True},
                            "url": project_root.as_uri(),
                        }
                    )
                return None

            def locate_file(self, file):
                return file

        with patch("importlib.metadata.distribution", return_value=FakeDist()):
            assert specify_cli._version._editable_marker_seen() is True
            assert specify_cli._version._source_checkout_path() == project_root.resolve()

    def test_editable_marker_false_without_explicit_editable_metadata(self, tmp_path):
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        venv_file = repo_root / ".venv" / "lib" / "python3.13" / "site-packages" / "specify_cli.py"
        venv_file.parent.mkdir(parents=True)
        venv_file.write_text("# installed module\n")

        class FakeDist:
            files = ["specify_cli.py"]

            def read_text(self, name):
                return None

            def locate_file(self, file):
                return venv_file

        with patch("importlib.metadata.distribution", return_value=FakeDist()):
            assert specify_cli._version._editable_marker_seen() is False


class TestTagValidationWhitespace:
    def test_tag_whitespace_is_trimmed_before_validation(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v9.9.9"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.8.0\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade", "--tag", " v0.8.0 "])

        assert result.exit_code == 0
        assert "v0.8.0" in strip_ansi(result.output)


class TestArgvAssemblyPipx:
    """pipx installer argv shape — pipx 1.5+ uses positional PACKAGE_SPEC, never `--spec` or `upgrade`."""

    def test_pipx_argv_uses_install_force_positional_not_upgrade(self):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/pipx"):
            argv = _assemble_installer_argv(_InstallMethod.PIPX, "v0.7.6")
        assert argv == [
            "/usr/bin/pipx",
            "install",
            "--force",
            "git+https://github.com/github/spec-kit.git@v0.7.6",
        ]
        assert "upgrade" not in argv  # pipx upgrade does not accept arbitrary refs
        assert "--spec" not in argv  # pipx 1.5+ dropped the --spec flag


class TestBareUpgradePipx:
    """pipx happy path."""

    def test_happy_path(self, pipx_argv0, clean_environ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/pipx"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 0.7.6\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "via pipx:" in out
        assert "Upgraded specify-cli: 0.7.5 → 0.7.6" in out


class TestDetectionShortCircuit:
    """Tier-1 path-prefix matches short-circuit before registry checks."""

    def test_pipx_argv0_prefix_short_circuits_before_registry_checks(
        self,
        pipx_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/X"), patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            method = _detect_install_method()
        assert method == _InstallMethod.PIPX
        mock_run.assert_not_called()


class TestDryRunPipx:
    def test_dry_run_preview_names_pipx(self, pipx_argv0, clean_environ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/pipx"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert result.exit_code == 0
        assert "Detected install method: pipx" in strip_ansi(result.output)
        assert mock_run.call_count == 0


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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
            "specify_cli._version.urllib.request.urlopen",
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
        ), patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert f"Running from a source checkout at {fake_tree}" in out
        assert "git pull" in out
        assert "pip install -e ." in out
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
        ), patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run:
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
            "specify_cli._version.urllib.request.urlopen",
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        ), patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert result.exit_code == 0
        assert "Could not identify your install method" in strip_ansi(result.output)


# ===========================================================================
# Phase 6 — User Story 4: failure recovery (P2)
# ===========================================================================


class TestInstallerMissing:
    """Installer disappeared between detection and run → exit 3."""

    def test_uv_missing_exits_3(self, uv_tool_argv0, clean_environ):
        which_results = {"specify": "/usr/local/bin/specify"}
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda n: which_results.get(n)
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        assert "Installer uv not found on PATH; reinstall it and retry." in strip_ansi(
            result.output
        )

    def test_pipx_missing_exits_3(self, pipx_argv0, clean_environ):
        which_results = {}
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", side_effect=lambda n: which_results.get(n)
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
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
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(0)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 0

    def test_absolute_installer_path_not_executable_gets_specific_message(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/bin/sh\n")
        fake_uv.chmod(0o644)
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
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
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        assert (
            f"Installer path {fake_uv} is not an executable file; fix the path or reinstall it and retry."
            in strip_ansi(result.output)
        )

    def test_real_installer_exit_126_is_not_treated_as_invalid_path(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
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
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        assert (
            f"Installer path {fake_uv} no longer exists; reinstall it and retry."
            in strip_ansi(result.output)
        )

    def test_exec_oserror_is_treated_as_invalid_installer(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        fake_uv.chmod(0o755)
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
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
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 3
        out = strip_ansi(result.output)
        assert f"Installer path {fake_uv} is not an executable file" in out
        assert "not found on PATH" not in out

    def test_exec_oserror_errno_is_treated_as_invalid_installer(
        self, uv_tool_argv0, clean_environ, tmp_path
    ):
        fake_uv = tmp_path / "installer-bin" / "uv"
        fake_uv.parent.mkdir()
        fake_uv.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        fake_uv.chmod(0o755)
        invalid_error = OSError(errno.ENOEXEC, "Exec format error")
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
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
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
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
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code != 3
        assert isinstance(result.exception, OSError)


class TestInstallerFailed:
    """Installer non-zero exit → propagate code, print rollback hint."""

    def test_installer_exit_2_propagates(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(127)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 127

    def test_installer_timeout_prints_timeout_specific_message(
        self, uv_tool_argv0, clean_environ, monkeypatch
    ):
        monkeypatch.setenv("SPECIFY_UPGRADE_TIMEOUT_SECS", "12")
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(_INSTALLER_TIMEOUT_SENTINEL)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 124
        out = strip_ansi(result.output)
        assert "Upgrade timed out while waiting for the installer subprocess." in out
        assert "SPECIFY_UPGRADE_TIMEOUT_SECS=12" in out

    def test_real_installer_exit_124_is_not_treated_as_timeout(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(124)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 124
        out = strip_ansi(result.output)
        assert "Upgrade failed. Installer exit code: 124." in out
        assert "Upgrade timed out while waiting for the installer subprocess." not in out

    def test_pipx_failure_prints_pipx_rollback_hint(self, pipx_argv0, clean_environ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/pipx"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
            mock_run.side_effect = [_completed_process(2)]
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert (
            "To pin back to the previous version: pipx install --force "
            "git+https://github.com/github/spec-kit.git@v0.7.5"
        ) in out

    def test_prerelease_failure_degrades_rollback_hint_to_releases_page(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="1.0.0rc1"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v1.0.0"})
            mock_run.side_effect = [_completed_process(2)]
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 2
        out = strip_ansi(result.output)
        assert "Previous version was not an exact stable release tag" in out
        assert "https://github.com/github/spec-kit/releases" in out
        assert "git+https://github.com/github/spec-kit.git@v1.0.0rc1" not in out


class TestVerificationMismatch:
    """Installer says 0 but the binary is still the old version → exit 2."""

    def test_installer_ok_but_verify_returns_old_version(
        self,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.9.0"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v9.9.9"})
            mock_run.side_effect = [
                _completed_process(0),
                _completed_process(0, stdout="specify 1.0.0rc1\n"),
            ]
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v1.0.0-rc1"])

        assert result.exit_code == 0
        assert "Upgraded specify-cli: 0.9.0 → 1.0.0rc1" in strip_ansi(result.output)

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
            "specify_cli._version.urllib.request.urlopen",
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
        with patch("specify_cli._version.urllib.request.urlopen", side_effect=err):
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
        with patch("specify_cli._version.urllib.request.urlopen", side_effect=err):
            result = runner.invoke(app, ["self", "upgrade"])
        assert result.exit_code == 1
        assert "Upgrade aborted: HTTP 500" in strip_ansi(result.output)

    def test_unparseable_resolved_release_tag_exits_1_without_traceback(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "release-main"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 1
        out = strip_ansi(result.output)
        assert "resolved release tag 'release-main' is not a comparable version" in out
        assert "Traceback" not in out
        assert mock_run.call_count == 0


class TestTagValidation:
    """--tag regex enforcement."""

    def test_valid_stable_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.7.6"],
            )
        assert result.exit_code == 0

    def test_valid_dev_suffix_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0.dev0"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0.dev0" in strip_ansi(result.output)

    def test_valid_rc_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v1.0.0-rc1"],
            )
        assert result.exit_code == 0

    def test_valid_build_metadata_tag(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli._version.shutil.which", return_value="/usr/bin/uv"), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0+build.42"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0+build.42" in strip_ansi(result.output)

    @pytest.mark.parametrize(
        "bad_tag",
        ["latest", "0.7.5", "main", "v7", "", "v1.2.3abc", "v1.2.3...", "v1.2.3++"],
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="unknown"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="unknown"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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

        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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

        with patch("specify_cli._version.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value="/usr/bin/uv"
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = _mock_urlopen_response({"tag_name": "v0.7.6"})
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
        monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "enterprise-gh")
        monkeypatch.setenv("GITHUB_ENTERPRISE_TOKEN", "enterprise-github")
        monkeypatch.setenv("GITHUB_API_TOKEN", "api-token")
        monkeypatch.setenv("HOMEBREW_GITHUB_API_TOKEN", "homebrew-token")
        monkeypatch.setenv("UNRELATED_TOKEN", "kept")

        env = specify_cli._version._scrubbed_env()

        assert "GH_ENTERPRISE_TOKEN" not in env
        assert "GITHUB_ENTERPRISE_TOKEN" not in env
        assert "GITHUB_API_TOKEN" not in env
        assert "HOMEBREW_GITHUB_API_TOKEN" not in env
        assert env["UNRELATED_TOKEN"] == "kept"
