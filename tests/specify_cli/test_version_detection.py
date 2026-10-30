"""Detection, argv assembly, and dry-run tests for `specify self upgrade`."""

import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import specify_cli
from specify_cli import app

from tests.specify_cli.self_upgrade_helpers import (
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
    _InstallMethod,
    _assemble_installer_argv,
    _completed_process,
    _detect_install_method,
    mock_urlopen_response,
    runner,
    strip_ansi,
)


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
            return sys.executable if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "tool", "list"]:
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
            return sys.executable if name == "uv" else None

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
        assert signals.installer_registries_consulted == ()

    def test_bare_argv0_missing_path_resolution_allows_tier3_registry_detection(
        self, monkeypatch, tmp_path
    ):
        missing_specify = tmp_path / "missing" / "specify"
        monkeypatch.setattr("sys.argv", ["specify"])

        def fake_which(name):
            if name == "specify":
                return str(missing_specify)
            if name == "uv":
                return sys.executable
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "tool", "list"]:
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

        assert method == _InstallMethod.UV_TOOL
        assert signals.matched_tier == 3
        assert "uv tool list" in signals.installer_registries_consulted

    def test_missing_relative_argv0_falls_back_to_entrypoint_name_lookup(
        self, monkeypatch, tmp_path
    ):
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
        monkeypatch.setattr("sys.argv", ["./bin/specify"])

        def fake_which(name):
            return str(fake_specify) if name == "specify" else None

        with patch("specify_cli._version.shutil.which", side_effect=fake_which):
            method = _detect_install_method()

        assert method == _InstallMethod.UV_TOOL

    def test_tier3_uv_tool_ignores_substring_false_positive(
        self,
        unsupported_argv0,
    ):
        def fake_which(name):
            return sys.executable if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "tool", "list"]:
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
            return sys.executable if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "tool", "list"]:
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
                return sys.executable
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "tool", "list"]:
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
        assert signals.installer_registries_consulted == ()


class TestPrefixExpansion:
    """Path-prefix expansion edge cases."""

    def test_literal_dollar_without_variable_name_is_preserved(self, tmp_path):
        prefix_path = tmp_path / "specify-$-cache" / "tools" / "specify-cli"
        prefix = str(prefix_path)

        expanded = specify_cli._version._expand_prefix(prefix)

        assert expanded == prefix_path.resolve()

    def test_unresolved_posix_variable_is_rejected(self):
        assert specify_cli._version._expand_prefix("$SPECIFY_MISSING/specify-cli/") is None

    def test_absolute_prefix_resolve_oserror_is_rejected(self, tmp_path):
        prefix = str(tmp_path / "specify-cli")

        with patch("pathlib.Path.resolve", side_effect=OSError("bad path")):
            assert specify_cli._version._expand_prefix(prefix) is None


class TestArgv0Resolution:
    """Entrypoint path resolution edge cases."""

    def test_absolute_argv0_resolve_oserror_returns_original_path(self, tmp_path):
        argv0 = tmp_path / "specify"

        with patch("pathlib.Path.resolve", side_effect=OSError("bad path")):
            assert specify_cli._version._resolved_argv0_path(str(argv0)) == argv0

    def test_path_lookup_resolve_oserror_returns_unresolved_lookup_path(self):
        with patch(
            "specify_cli._version.shutil.which", return_value="/broken/specify"
        ), patch("pathlib.Path.resolve", side_effect=OSError("bad path")):
            result = specify_cli._version._resolved_argv0_path("specify")

        # Compare as Path objects: on Windows the same logical path renders
        # with backslashes, so a raw string compare against the POSIX form
        # would spuriously fail.
        assert result == Path("/broken/specify")


class TestInstallerResolution:
    @pytest.mark.skipif(os.name == "nt", reason="requires unprivileged symlinks")
    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    def test_working_directory_symlink_to_nested_target_is_rejected(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        target = project / "scripts" / name
        target.parent.mkdir(parents=True)
        target.write_text("decoy; must never be executed\n", encoding="utf-8")
        target.chmod(0o755)
        installer = project / name
        installer.symlink_to(target)
        monkeypatch.chdir(project)

        with patch(
            "specify_cli._version.shutil.which", return_value=str(installer)
        ), pytest.raises(ValueError, match=f"Installer {name} rejected"):
            _assemble_installer_argv(method, "v0.7.6")

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    def test_case_alias_of_working_directory_is_rejected(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "Project"
        project.mkdir()
        alias = tmp_path / "pROJECT"
        if not alias.exists():
            pytest.skip("requires a case-insensitive filesystem")
        installer = project / name
        installer.write_text("decoy; must never be executed\n", encoding="utf-8")
        installer.chmod(0o755)
        monkeypatch.chdir(project)

        with patch(
            "specify_cli._version.shutil.which", return_value=str(alias / name)
        ), pytest.raises(ValueError, match=f"Installer {name} rejected"):
            _assemble_installer_argv(method, "v0.7.6")

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    @pytest.mark.parametrize(
        ("operation", "error"),
        [
            ("cwd", FileNotFoundError("working directory was deleted")),
            ("samefile", PermissionError("cannot stat installer directory")),
            ("resolve", RuntimeError("symlink loop")),
        ],
    )
    def test_path_comparison_errors_are_rejected(
        self, tmp_path, method, name, operation, error
    ):
        with patch(
            "specify_cli._version.shutil.which",
            side_effect=lambda command: sys.executable if command == name else None,
        ), patch(
            "specify_cli._version._resolved_argv0_path",
            return_value=tmp_path / "missing" / "specify",
        ), patch(
            "specify_cli._version._expand_prefix", return_value=None
        ), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ), patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch.object(
            Path, operation, side_effect=error
        ):
            with pytest.raises(ValueError, match=f"Installer {name} rejected"):
                _assemble_installer_argv(method, "v0.7.6")
            detected, signals = _detect_install_method(include_signals=True)

        assert detected == _InstallMethod.UNSUPPORTED
        assert signals.installer_registries_consulted == ()
        assert len(signals.installer_rejections) == 1
        assert str(error) in signals.installer_rejections[0]
        mock_run.assert_not_called()

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    @pytest.mark.parametrize("target_missing", [False, True])
    def test_missing_installer_paths_are_rejected(
        self, monkeypatch, tmp_path, method, name, target_missing
    ):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        directory = tmp_path / "installer-bin"
        if target_missing:
            directory.mkdir()

        with patch(
            "specify_cli._version.shutil.which", return_value=str(directory / name)
        ), pytest.raises(ValueError, match=f"Installer {name} rejected"):
            _assemble_installer_argv(method, "v0.7.6")

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    @pytest.mark.parametrize(
        "location",
        ["bare", "current-relative", "relative-directory", "windows-relative", "current-absolute"],
    )
    def test_unsafe_lookup_result_is_not_used_for_upgrade_or_registry_probe(
        self, monkeypatch, tmp_path, method, name, location
    ):
        monkeypatch.chdir(tmp_path)
        paths = {
            "bare": name,
            "current-relative": f"./{name}",
            "relative-directory": f"bin/{name}",
            "windows-relative": f".\\{name}.exe",
            "current-absolute": str(tmp_path / name),
        }
        decoy = tmp_path / name
        decoy.write_text("#!/bin/sh\n", encoding="utf-8")
        decoy.chmod(0o755)
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        with patch(
            "specify_cli._version.shutil.which",
            side_effect=lambda command: paths[location] if command == name else None,
        ), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ), patch("specify_cli._version.subprocess.run") as mock_run:
            with pytest.raises(ValueError, match=f"Installer {name} rejected") as rejection:
                _assemble_installer_argv(method, "v0.7.6")
            detected, signals = _detect_install_method(include_signals=True)

        assert detected == _InstallMethod.UNSUPPORTED
        assert signals.installer_registries_consulted == ()
        assert len(signals.installer_rejections) == 1
        assert f"Installer {name} rejected" in signals.installer_rejections[0]
        if location == "windows-relative":
            guidance = "Run from a directory without a matching installer executable"
            assert guidance in str(rejection.value)
            assert guidance in signals.installer_rejections[0]
        mock_run.assert_not_called()

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    def test_absolute_installer_outside_working_directory_is_preserved(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        installer = tmp_path / "installed tools" / name
        installer.parent.mkdir()
        installer.write_text("#!/bin/sh\n", encoding="utf-8")
        installer.chmod(0o755)

        with patch(
            "specify_cli._version.shutil.which", return_value=str(installer)
        ):
            argv = _assemble_installer_argv(method, "v0.7.6")

        assert argv is not None
        assert argv[0] == str(installer)

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    @pytest.mark.parametrize("path_entry", ["empty", "dot", "relative", "current-absolute"])
    def test_real_lookup_rejects_working_directory_and_relative_path_entries(
        self, monkeypatch, tmp_path, method, name, path_entry
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)
        monkeypatch.setenv("PATHEXT", ".EXE")
        filename = f"{name}.exe" if os.name == "nt" else name
        (tmp_path / "bin").mkdir()
        for directory in (tmp_path, tmp_path / "bin"):
            executable = directory / filename
            executable.write_text("decoy; must never be executed\n", encoding="utf-8")
            executable.chmod(0o755)
        entries = {
            "empty": "",
            "dot": ".",
            "relative": "bin",
            "current-absolute": str(tmp_path),
        }
        monkeypatch.setenv("PATH", entries[path_entry])

        if path_entry == "empty":
            assert _assemble_installer_argv(method, "v0.7.6") is None
        else:
            with pytest.raises(ValueError, match=f"Installer {name} rejected"):
                _assemble_installer_argv(method, "v0.7.6")

    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    def test_real_lookup_preserves_installed_tool_on_absolute_path(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        directory = tmp_path / "installed tools"
        directory.mkdir()
        filename = f"{name}.exe" if os.name == "nt" else name
        installer = directory / filename
        installer.write_text("installer fixture; never executed\n", encoding="utf-8")
        installer.chmod(0o755)
        monkeypatch.setenv("PATH", str(directory))
        monkeypatch.setenv("PATHEXT", ".EXE")

        argv = _assemble_installer_argv(method, "v0.7.6")

        assert argv is not None
        assert Path(argv[0]) == installer

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows implicit cwd search")
    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    def test_windows_implicit_cwd_lookup_cannot_shadow_installed_tool(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        directory = tmp_path / "installed tools"
        directory.mkdir()
        for parent in (project, directory):
            executable = parent / f"{name}.exe"
            executable.write_text("fixture; must never be executed\n", encoding="utf-8")
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", str(directory))
        monkeypatch.setenv("PATHEXT", ".EXE")
        monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)

        try:
            argv = _assemble_installer_argv(method, "v0.7.6")
        except specify_cli._version._InstallerRejected:
            return
        assert argv is not None
        assert Path(argv[0]) == directory / f"{name}.exe"

    @pytest.mark.skipif(os.name == "nt", reason="requires unprivileged symlinks")
    @pytest.mark.parametrize(
        ("method", "name"),
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    def test_absolute_symlink_to_working_directory_installer_is_rejected(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        decoy = project / name
        decoy.write_text("#!/bin/sh\n", encoding="utf-8")
        decoy.chmod(0o755)
        installer = tmp_path / name
        installer.symlink_to(decoy)

        with patch(
            "specify_cli._version.shutil.which", return_value=str(installer)
        ), pytest.raises(ValueError, match=f"Installer {name} rejected"):
            _assemble_installer_argv(method, "v0.7.6")


class TestArgvAssemblyUvTool:
    """uv-tool installer argv shape."""

    def test_stable_tag_produces_expected_argv(self):
        with patch("specify_cli._version.shutil.which", return_value=sys.executable):
            argv = _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.7.6")
        assert argv == [
            sys.executable,
            "tool",
            "install",
            "specify-cli",
            "--force",
            "--from",
            "git+https://github.com/github/spec-kit.git@v0.7.6",
        ]

    def test_dev_suffix_tag_embedded_literally(self):
        with patch("specify_cli._version.shutil.which", return_value=sys.executable):
            argv = _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.8.0.dev0")
        assert "git+https://github.com/github/spec-kit.git@v0.8.0.dev0" in argv
        assert (
            "upgrade" not in argv
        )  # never `uv tool upgrade` — does not accept --tag pinning

    def test_missing_uv_returns_no_installer_argv(self):
        with patch("specify_cli._version.shutil.which", return_value=None):
            assert _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.7.6") is None


class TestBareUpgradeUvTool:
    """uv-tool happy path, bare invocation."""

    def test_happy_path_end_to_end(self, uv_tool_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
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


class TestAlreadyLatestUvTool:
    """already on latest, no installer launched."""

    def test_already_latest_exits_zero_no_subprocess(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.6"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release: v0.7.6" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_trailing_zero_equivalent_version_reports_latest_not_newer(
        self, uv_tool_argv0, clean_environ
    ):
        # Version("1.0") == Version("1.0.0") under packaging even though their
        # canonical strings differ. The no-op message must use Version equality
        # so this prints "Already on latest release", not "... or newer".
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="1.0"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.0.0"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Already on latest release: v1.0.0" in out
        assert "or newer" not in out
        assert mock_run.call_count == 0

    def test_dev_build_ahead_of_release_reports_newer_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.7.dev0"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release or newer: 0.7.7.dev0" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_unparseable_current_version_does_not_false_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="release-main"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
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

    def test_unparseable_resolved_target_fails_before_literal_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="release-main"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "release-main"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 1
        out = strip_ansi(result.output)
        assert "not a comparable version" in out
        assert "release-main" not in out
        assert "Already on latest release" not in out
        assert mock_run.call_count == 0

    def test_pinned_older_tag_still_runs_installer(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value=sys.executable), patch(
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
        # A pinned older tag is a downgrade and must be labelled as such.
        assert "Downgrading specify-cli 0.7.6 → v0.7.5 via uv tool:" in out
        assert "Upgrading specify-cli" not in out
        assert mock_run.call_count == 2

    def test_pinned_rc_tag_uses_canonical_version_equality_for_noop(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value=sys.executable), patch(
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
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
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
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ), patch("specify_cli._version.shutil.which", return_value=sys.executable), patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0" in strip_ansi(result.output)
        mock_urlopen.assert_not_called()

    def test_dry_run_rejects_unparseable_network_tag_before_preview(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = mock_urlopen_response(
                {"tag_name": "v0.9.0;echo unsafe"}
            )
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])

        out = strip_ansi(result.output)
        assert result.exit_code == 1
        assert "not a comparable version" in out
        assert "v0.9.0;echo unsafe" not in out
        assert "Command that would be executed:" not in out
        assert mock_run.call_count == 0

    def test_dry_run_with_missing_uv_flags_unresolved_installer(
        self, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=None
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.5"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Command that would be executed: (installer uv not found on PATH)" in out
        assert "uv tool install" not in out
        assert mock_run.call_count == 0


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
            return sys.executable if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "list", "--json"]:
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
            return sys.executable if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "list", "--json"]:
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
            return sys.executable if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "list", "--json"]:
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
                return sys.executable
            if name == "pipx":
                return sys.executable
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [sys.executable, "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="specify-cli v0.7.6\n",
                    stderr="",
                )
            if argv[:3] == [sys.executable, "list", "--json"]:
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


    @pytest.mark.parametrize("rejected_name", ["uv", "pipx"])
    def test_tier3_rejected_probe_leaves_ownership_ambiguous(
        self, monkeypatch, tmp_path, rejected_name
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])
        other_name = "pipx" if rejected_name == "uv" else "uv"
        probe_args = ["list", "--json"] if other_name == "pipx" else ["tool", "list"]
        probe_output = (
            '{"venvs":{"specify-cli":{}}}' if other_name == "pipx" else "specify-cli v0.7.6\n"
        )

        def fake_which(name):
            if name == rejected_name:
                return f"./{name}"
            if name == other_name:
                return sys.executable
            return None

        with patch(
            "specify_cli._version.shutil.which", side_effect=fake_which
        ), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ), patch("specify_cli._version.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[sys.executable, *probe_args],
                returncode=0,
                stdout=probe_output,
                stderr="",
            )
            method, signals = _detect_install_method(include_signals=True)

        assert method == _InstallMethod.UNSUPPORTED
        assert signals.matched_tier is None
        assert signals.installer_registries_consulted == (" ".join([other_name, *probe_args]),)
        assert len(signals.installer_rejections) == 1
        assert f"Installer {rejected_name} rejected" in signals.installer_rejections[0]
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == [sys.executable, *probe_args]


class TestEditableInstallMetadata:
    @pytest.mark.skipif(
        not hasattr(importlib.metadata, "InvalidMetadataError"),
        reason=(
            "importlib.metadata.InvalidMetadataError does not exist on this "
            "Python; _editable_direct_url_path only catches it when present, so "
            "fabricating it would exercise a path that cannot fire in production"
        ),
    )
    def test_editable_marker_false_when_metadata_is_invalid(self):
        invalid_metadata_error = importlib.metadata.InvalidMetadataError

        with patch(
            "importlib.metadata.distribution",
            side_effect=invalid_metadata_error("bad metadata"),
        ):
            assert specify_cli._version._editable_marker_seen() is False
            assert specify_cli._version._source_checkout_path() is None

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
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v9.9.9"})
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
        with patch("specify_cli._version.shutil.which", return_value=sys.executable):
            argv = _assemble_installer_argv(_InstallMethod.PIPX, "v0.7.6")
        assert argv == [
            sys.executable,
            "install",
            "--force",
            "git+https://github.com/github/spec-kit.git@v0.7.6",
        ]
        assert "upgrade" not in argv  # pipx upgrade does not accept arbitrary refs
        assert "--spec" not in argv  # pipx 1.5+ dropped the --spec flag

    def test_missing_pipx_returns_no_installer_argv(self):
        with patch("specify_cli._version.shutil.which", return_value=None):
            assert _assemble_installer_argv(_InstallMethod.PIPX, "v0.7.6") is None


class TestBareUpgradePipx:
    """pipx happy path."""

    def test_happy_path(self, pipx_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
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
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=sys.executable
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert result.exit_code == 0
        assert "Detected install method: pipx" in strip_ansi(result.output)
        assert mock_run.call_count == 0
