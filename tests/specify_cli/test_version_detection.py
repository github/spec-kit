"""Detection, argv assembly, and dry-run tests for `specify self upgrade`."""

import importlib.metadata
import json
import os
import stat
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
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
    _detection_result,
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
        installer_paths,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["uv"] if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["uv"], "tool", "list"]:
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

    def test_unresolved_bare_argv0_skips_tier3_registry_detection(self, installer_paths, monkeypatch):
        monkeypatch.setattr("sys.argv", ["specify"])

        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["uv"] if name == "uv" else None

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
        self, installer_paths, monkeypatch, tmp_path
    ):
        missing_specify = tmp_path / "missing" / "specify"
        monkeypatch.setattr("sys.argv", ["specify"])

        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            if name == "specify":
                return str(missing_specify)
            if name == "uv":
                return installer_paths["uv"]
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["uv"], "tool", "list"]:
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
        installer_paths,
        unsupported_argv0,
    ):
        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["uv"] if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["uv"], "tool", "list"]:
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
        installer_paths,
        unsupported_argv0,
    ):
        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["uv"] if name == "uv" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["uv"], "tool", "list"]:
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
        installer_paths,
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
            name = Path(name).stem if Path(name).is_absolute() else name
            if name == "specify":
                return str(fake_specify)
            if name == "uv":
                return installer_paths["uv"]
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["uv"], "tool", "list"]:
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
            ("stat", PermissionError("cannot stat installer directory")),
            ("resolve", RuntimeError("symlink loop")),
        ],
    )
    def test_path_comparison_errors_are_rejected(
        self, tmp_path, method, name, operation, error
    ):
        with patch(
            "specify_cli._version.shutil.which",
            side_effect=lambda command: sys.executable if Path(command).stem == name else None,
        ), patch(
            "specify_cli._version._resolved_argv0_path",
            return_value=tmp_path / "missing" / "specify",
        ), patch(
            "specify_cli._version._expand_prefix", return_value=None
        ), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ), patch(
            "specify_cli._version._tier3_registry_lookup_allowed", return_value=True
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
            side_effect=lambda command: paths[location] if Path(command).stem == name else None,
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

    def test_stable_tag_produces_expected_argv(self, installer_paths):
        with patch("specify_cli._version.shutil.which", return_value=installer_paths["uv"]):
            argv = _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.7.6")
        assert argv == [
            installer_paths["uv"],
            "tool",
            "install",
            "specify-cli",
            "--force",
            "--from",
            "git+https://github.com/github/spec-kit.git@v0.7.6",
        ]

    def test_dev_suffix_tag_embedded_literally(self, installer_paths):
        with patch("specify_cli._version.shutil.which", return_value=installer_paths["uv"]):
            argv = _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.8.0.dev0")
        assert "git+https://github.com/github/spec-kit.git@v0.8.0.dev0" in argv
        assert (
            "upgrade" not in argv
        )  # never `uv tool upgrade` — does not accept --tag pinning

    def test_missing_uv_returns_no_installer_argv(self):
        with patch("specify_cli._version.shutil.which", return_value=None):
            assert _assemble_installer_argv(_InstallMethod.UV_TOOL, "v0.7.6") is None


class TestWindowsPathContainment:
    @pytest.mark.parametrize("unc", [False, True])
    @pytest.mark.parametrize("root_extended", [False, True])
    @pytest.mark.parametrize("target_extended", [False, True])
    @pytest.mark.parametrize("location", ["root", "child", "sibling"])
    def test_namespace_spellings_share_containment(
        self, unc, root_extended, target_extended, location
    ):
        plain = r"\\server\share\project" if unc else r"C:\project"
        extended = r"\\?\UNC\server\share\project" if unc else r"\\?\C:\project"
        root = PureWindowsPath(extended if root_extended else plain)
        target = PureWindowsPath(extended if target_extended else plain)
        if location == "child":
            target /= "bin"
        elif location == "sibling":
            target = target.with_name("project-sibling") / "bin"

        assert specify_cli._version._path_is_within_prefix(target, root) is (
            location != "sibling"
        )


class TestInstallerLookupSecurity:
    @staticmethod
    def executable(directory, name):
        executable = directory / (f"{name}.exe" if os.name == "nt" else name)
        executable.write_bytes(b"installer lookup fixture; never executed\n")
        executable.chmod(0o755)
        return executable

    @staticmethod
    def junction(path, target):
        result = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(path), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            pytest.skip(
                f"Windows junction creation unavailable: {result.stderr or result.stdout}"
            )

    @pytest.mark.parametrize(
        "method,name",
        [(_InstallMethod.UV_TOOL, "uv"), (_InstallMethod.PIPX, "pipx")],
    )
    @pytest.mark.parametrize(
        "kind",
        [
            "aliased-directory",
            "directory-target",
            "file",
            "file-aliased-directory",
            "cwd-file-chain",
            "cwd-directory-chain",
        ],
    )
    @pytest.mark.parametrize("operation", ["lookup", "registry", "upgrade"])
    @pytest.mark.parametrize("fallback", [False, True])
    def test_symlink_bypasses_are_rejected(
        self, monkeypatch, tmp_path, method, name, kind, operation, fallback
    ):
        project = tmp_path / "project"
        project.mkdir()
        if kind not in {"cwd-file-chain", "cwd-directory-chain"}:
            (project / ".git").mkdir()
        external = tmp_path / "external"
        external.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = self.executable(trusted, name)
        try:
            if kind == "cwd-directory-chain":
                payload_dir = tmp_path / "payload"
                payload_dir.mkdir()
                self.executable(payload_dir, name)
                (project / "bin").symlink_to(payload_dir, target_is_directory=True)
                unsafe = external / "alias"
                unsafe.symlink_to(project / "bin", target_is_directory=True)
            elif kind == "cwd-file-chain":
                payload_dir = tmp_path / "payload"
                payload_dir.mkdir()
                payload = self.executable(payload_dir, name)
                malicious = project / payload.name
                malicious.symlink_to(payload)
                (external / payload.name).symlink_to(malicious)
                unsafe = external
            elif kind != "file":
                self.executable(external, name)
                (project / "bin").symlink_to(external, target_is_directory=True)
                alias = tmp_path / "alias"
                alias.symlink_to(project, target_is_directory=True)
                if kind == "aliased-directory":
                    unsafe = alias / "bin"
                elif kind == "directory-target":
                    unsafe = tmp_path / "directory-target"
                    unsafe.symlink_to(project / "bin", target_is_directory=True)
                else:
                    unsafe = tmp_path / "file-bin"
                    unsafe.mkdir()
                    executable_name = f"{name}.exe" if os.name == "nt" else name
                    (unsafe / executable_name).symlink_to(
                        alias / "bin" / executable_name
                    )
            else:
                malicious = self.executable(project, name)
                (external / malicious.name).symlink_to(malicious)
                unsafe = external
        except OSError:
            pytest.skip("symlinks are unavailable")
        monkeypatch.chdir(project)
        monkeypatch.setenv(
            "PATH",
            os.pathsep.join([str(unsafe), str(trusted)] if fallback else [str(unsafe)]),
        )
        monkeypatch.setattr("sys.argv", [str(project / "missing" / "specify")])
        stdout = (
            "specify-cli v0.7.6\n" if name == "uv" else '{"venvs":{"specify-cli":{}}}'
        )

        with (
            patch("specify_cli._version._editable_marker_seen", return_value=False),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
            patch("specify_cli._version._verify_upgrade", return_value="0.7.6"),
            patch(
                "specify_cli._version.subprocess.run",
                return_value=_completed_process(0, stdout=stdout),
            ) as run,
        ):
            if operation == "lookup":
                if fallback:
                    argv = _assemble_installer_argv(method, "v0.7.6")
                    assert argv is not None
                    assert Path(argv[0]) == expected
                else:
                    with pytest.raises(specify_cli._version._InstallerRejected):
                        _assemble_installer_argv(method, "v0.7.6")
                run.assert_not_called()
                return
            if operation == "registry":
                detected = _detect_install_method()
                assert detected == (method if fallback else _InstallMethod.UNSUPPORTED)
            else:
                with patch(
                    "specify_cli._version._detect_install_method", return_value=_detection_result(method)
                ):
                    result = runner.invoke(app, ["self", "upgrade", "--tag", "v0.7.6"])
                assert result.exit_code == (0 if fallback else 3)
                if not fallback:
                    assert f"Installer {name} rejected" in strip_ansi(
                        result.output
                    )

        if fallback:
            run.assert_called_once()
            assert Path(run.call_args.args[0][0]) == expected
        else:
            run.assert_not_called()

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("operation", ["lookup", "upgrade"])
    def test_external_file_symlink_preserves_dispatch_name(
        self, monkeypatch, tmp_path, name, operation
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        installed = tmp_path / "installed"
        installed.mkdir()
        dispatcher = self.executable(installed, "dispatcher")
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        selected = bin_dir / (f"{name}.exe" if os.name == "nt" else name)
        try:
            selected.symlink_to(dispatcher)
        except OSError:
            pytest.skip("file symlinks are unavailable")
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", str(bin_dir))

        if operation == "lookup":
            found = specify_cli._version._find_installer(name)
            assert found is not None
            assert Path(found) == selected
        else:
            method = _InstallMethod.UV_TOOL if name == "uv" else _InstallMethod.PIPX
            with (
                patch(
                    "specify_cli._version._detect_install_method", return_value=_detection_result(method)
                ),
                patch(
                    "specify_cli._version._get_installed_version", return_value="0.7.5"
                ),
                patch("specify_cli._version._verify_upgrade", return_value="0.7.6"),
                patch(
                    "specify_cli._version.subprocess.run",
                    return_value=_completed_process(0),
                ) as run,
            ):
                result = runner.invoke(app, ["self", "upgrade", "--tag", "v0.7.6"])
            assert result.exit_code == 0
            assert Path(run.call_args.args[0][0]) == selected

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("git_project", [False, True])
    @pytest.mark.parametrize("fallback", [False, True])
    def test_case_aliases_are_rejected_on_case_insensitive_volumes(
        self, monkeypatch, tmp_path, name, git_project, fallback
    ):
        project = tmp_path / "project"
        project.mkdir()
        alias = project.with_name("PROJECT")
        if not alias.exists() or not alias.samefile(project):
            pytest.skip("case-insensitive volume required")
        unsafe = project
        if git_project:
            (project / ".git").mkdir()
            unsafe = project / "bin"
            unsafe.mkdir()
        self.executable(unsafe, name)
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = self.executable(trusted, name)
        monkeypatch.chdir(project)
        entry = alias / "bin" if git_project else alias
        monkeypatch.setenv(
            "PATH",
            os.pathsep.join([str(entry), str(trusted)] if fallback else [str(entry)]),
        )

        if fallback:
            found = specify_cli._version._find_installer(name)
            assert found is not None
            assert Path(found) == expected
        else:
            with pytest.raises(specify_cli._version._InstallerRejected):
                specify_cli._version._find_installer(name)

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("stage", ["resolve", "lstat"])
    @pytest.mark.parametrize(
        "error", [PermissionError("denied"), RuntimeError("link loop")]
    )
    def test_inspection_failure_warns_and_checks_later_entries(
        self, monkeypatch, tmp_path, capsys, name, stage, error
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        bad = tmp_path / "bad"
        bad.mkdir()
        self.executable(bad, name)
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = self.executable(trusted, name)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", os.pathsep.join([str(bad), str(trusted)]))
        original = getattr(Path, stage)

        def inspect(path, *args, **kwargs):
            if path == bad:
                raise error
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, stage, inspect)

        found = specify_cli._version._find_installer(name)
        assert found is not None
        assert Path(found) == expected
        output = capsys.readouterr().out
        assert "Skipping installer PATH entry" in output
        assert str(bad) in output
        assert str(error) in output

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("tag", [0, 0x8000001B])
    def test_non_symlink_reparse_entries_are_rejected_portably(
        self, monkeypatch, tmp_path, name, tag
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        reparse = tmp_path / "reparse"
        reparse.mkdir()
        self.executable(reparse, name)
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = self.executable(trusted, name)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", os.pathsep.join([str(reparse), str(trusted)]))
        original = Path.lstat

        def lstat(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == reparse:
                return SimpleNamespace(
                    st_mode=result.st_mode,
                    st_file_attributes=0x400,
                    st_reparse_tag=tag,
                    st_ino=result.st_ino,
                    st_dev=result.st_dev,
                )
            return result

        monkeypatch.setattr(Path, "lstat", lstat)

        found = specify_cli._version._find_installer(name)
        assert found is not None
        assert Path(found) == expected

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("operation", ["lookup", "registry", "upgrade"])
    @pytest.mark.parametrize(
        "native",
        [
            False,
            pytest.param(
                True,
                marks=pytest.mark.skipif(
                    os.name != "nt", reason="Native Windows junctions required"
                ),
            ),
        ],
    )
    def test_external_junction_preserves_installer_paths(
        self, monkeypatch, tmp_path, name, operation, native
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        install = tmp_path / "install"
        install.mkdir()
        version = install / "version"
        version.mkdir()
        scripts = version / "Scripts"
        scripts.mkdir()
        executable = self.executable(scripts, name)
        current = install / "current"
        if native:
            self.junction(current, version)
            assert not current.is_symlink()
        else:
            try:
                current.symlink_to(version, target_is_directory=True)
            except OSError:
                pytest.skip("directory symlinks are unavailable")
            original = Path.lstat

            def lstat(path, *args, **kwargs):
                result = original(path, *args, **kwargs)
                if path == current:
                    return SimpleNamespace(
                        st_mode=stat.S_IFDIR | 0o755,
                        st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
                        st_reparse_tag=0xA0000003,
                        st_ino=result.st_ino,
                        st_dev=result.st_dev,
                    )
                return result

            monkeypatch.setattr(Path, "lstat", lstat)
        selected = current / "Scripts" / executable.name
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", str(selected.parent))
        monkeypatch.setattr("sys.argv", [str(project / "missing" / "specify")])
        method = _InstallMethod.UV_TOOL if name == "uv" else _InstallMethod.PIPX
        stdout = (
            "specify-cli v0.7.6\n" if name == "uv" else '{"venvs":{"specify-cli":{}}}'
        )

        with (
            patch("specify_cli._version._editable_marker_seen", return_value=False),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
            patch("specify_cli._version._verify_upgrade", return_value="0.7.6"),
            patch(
                "specify_cli._version.subprocess.run",
                return_value=_completed_process(0, stdout=stdout),
            ) as run,
        ):
            if operation == "lookup":
                argv = _assemble_installer_argv(method, "v0.7.6")
                assert argv is not None
                assert Path(argv[0]) == selected
                run.assert_not_called()
                return
            if operation == "registry":
                assert _detect_install_method() == method
            else:
                with patch(
                    "specify_cli._version._detect_install_method", return_value=_detection_result(method)
                ):
                    result = runner.invoke(app, ["self", "upgrade", "--tag", "v0.7.6"])
                assert result.exit_code == 0
        run.assert_called_once()
        assert Path(run.call_args.args[0][0]) == selected

    @pytest.mark.skipif(
        os.name != "nt", reason="Native Windows namespace paths required"
    )
    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("git_project", [False, True])
    @pytest.mark.parametrize("fallback", [False, True])
    def test_native_windows_extended_path_entries_are_rejected(
        self, monkeypatch, tmp_path, name, git_project, fallback
    ):
        project = tmp_path / "project"
        project.mkdir()
        unsafe = project
        if git_project:
            (project / ".git").mkdir()
            unsafe = project / "bin"
            unsafe.mkdir()
        self.executable(unsafe, name)
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = self.executable(trusted, name)
        raw = str(unsafe)
        extended = (
            "\\\\?\\UNC\\" + raw[2:] if raw.startswith("\\\\") else "\\\\?\\" + raw
        )
        monkeypatch.chdir(project)
        monkeypatch.setenv(
            "PATH",
            os.pathsep.join([extended, str(trusted)] if fallback else [extended]),
        )

        if fallback:
            found = specify_cli._version._find_installer(name)
            assert found is not None
            assert Path(found) == expected
        else:
            with pytest.raises(specify_cli._version._InstallerRejected):
                specify_cli._version._find_installer(name)

    @pytest.mark.skipif(os.name != "nt", reason="Native Windows junctions required")
    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("fallback", [False, True])
    @pytest.mark.parametrize("git_project", [False, True])
    def test_native_windows_junction_chain_is_rejected(
        self, monkeypatch, tmp_path, name, fallback, git_project
    ):
        project = tmp_path / "project"
        project.mkdir()
        if git_project:
            (project / ".git").mkdir()
        external = tmp_path / "external"
        external.mkdir()
        self.executable(external, name)
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = self.executable(trusted, name)
        alias = tmp_path / "alias"
        for path, target in ((project / "bin", external), (alias, project / "bin")):
            self.junction(path, target)
        assert not alias.is_symlink()
        monkeypatch.chdir(project)
        monkeypatch.setenv(
            "PATH",
            os.pathsep.join([str(alias), str(trusted)] if fallback else [str(alias)]),
        )

        if fallback:
            found = specify_cli._version._find_installer(name)
            assert found is not None
            assert Path(found) == expected
        else:
            with pytest.raises(specify_cli._version._InstallerRejected):
                specify_cli._version._find_installer(name)

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    def test_relative_lookup_result_is_rejected(self, monkeypatch, tmp_path, name):
        project = tmp_path / "project"
        project.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", str(trusted))
        with patch("specify_cli._version.shutil.which", return_value=name):
            with pytest.raises(specify_cli._version._InstallerRejected):
                specify_cli._version._find_installer(name)

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    def test_file_symlink_to_non_project_cwd_is_rejected(
        self, monkeypatch, tmp_path, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        malicious = self.executable(project, name)
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        try:
            (bin_dir / malicious.name).symlink_to(malicious)
        except OSError:
            pytest.skip("file symlinks are unavailable")
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", str(bin_dir))

        with pytest.raises(specify_cli._version._InstallerRejected):
            specify_cli._version._find_installer(name)

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    @pytest.mark.parametrize(
        "entry", ["", ".", "bin", "absolute", "symlink", "symlink-out"]
    )
    def test_project_path_entries_cannot_override_installer(
        self, monkeypatch, tmp_path, method, name, entry
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").mkdir()
        project_bin = project / "bin"
        project_bin.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        self.executable(project, name)
        self.executable(project_bin, name)
        expected = self.executable(trusted, name)
        if entry == "absolute":
            entry = str(project_bin)
        elif entry in {"symlink", "symlink-out"}:
            link = tmp_path / "project-bin-link"
            target = project_bin
            if entry == "symlink-out":
                link = project / "external-bin"
                target = tmp_path / "untrusted"
                target.mkdir()
                self.executable(target, name)
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                pytest.skip("directory symlinks are unavailable")
            entry = str(link)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", os.pathsep.join([entry, str(trusted)]))

        argv = _assemble_installer_argv(method, "v0.7.6")

        assert argv is not None
        assert Path(argv[0]) == expected

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    def test_implicit_windows_cwd_search_is_bypassed(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        malicious = self.executable(project, name)
        expected = self.executable(trusted, name)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", str(trusted))
        real_which = specify_cli._version.shutil.which

        def windows_style_which(command):
            if not Path(command).is_absolute():
                return str(malicious)
            return real_which(command)

        with patch(
            "specify_cli._version.shutil.which", side_effect=windows_style_which
        ):
            argv = _assemble_installer_argv(method, "v0.7.6")

        assert argv is not None
        assert Path(argv[0]) == expected

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    @pytest.mark.parametrize("path", ["", ".", "bin"])
    def test_only_project_local_installer_is_not_available(
        self, monkeypatch, tmp_path, method, name, path
    ):
        (tmp_path / "bin").mkdir()
        self.executable(tmp_path, name)
        self.executable(tmp_path / "bin", name)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PATH", path)

        if not path:
            assert _assemble_installer_argv(method, "v0.7.6") is None
        else:
            with pytest.raises(specify_cli._version._InstallerRejected):
                _assemble_installer_argv(method, "v0.7.6")

    def test_registry_probes_do_not_execute_project_local_installers(
        self, monkeypatch, tmp_path
    ):
        self.executable(tmp_path, "uv")
        self.executable(tmp_path, "pipx")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PATH", str(tmp_path))
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        with (
            patch("specify_cli._version._editable_marker_seen", return_value=False),
            patch("specify_cli._version.subprocess.run") as run,
        ):
            method, signals = _detect_install_method(include_signals=True)

        assert method == _InstallMethod.UNSUPPORTED
        assert signals.installer_registries_consulted == ()
        run.assert_not_called()

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    def test_missing_safe_installer_fails_without_execution(
        self, monkeypatch, tmp_path, method, name
    ):
        self.executable(tmp_path, name)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PATH", str(tmp_path))
        with (
            patch("specify_cli._version._detect_install_method", return_value=_detection_result(method)),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
            patch("specify_cli._version.subprocess.run") as run,
        ):
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v0.7.6"])

        assert result.exit_code == 3
        assert f"Installer {name} rejected" in strip_ansi(result.output)
        run.assert_not_called()

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    def test_absolute_path_order_is_preserved(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        first = tmp_path / "first"
        first.mkdir()
        second = tmp_path / "second"
        second.mkdir()
        expected = self.executable(first, name)
        self.executable(second, name)
        monkeypatch.chdir(project)
        monkeypatch.setenv(
            "PATH",
            os.pathsep.join([str(tmp_path / "missing"), str(first), str(second)]),
        )

        argv = _assemble_installer_argv(method, "v0.7.6")

        assert argv is not None
        assert Path(argv[0]) == expected

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    @pytest.mark.parametrize("pathext", [None, ".CMD;.EXE"])
    @pytest.mark.parametrize("quoted_path", [False, True])
    def test_windows_pathext_is_expanded_before_absolute_lookup(
        self, monkeypatch, tmp_path, name, pathext, quoted_path
    ):
        project = tmp_path / "project"
        project.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        expected = str(trusted / f"{name}.EXE")
        Path(expected).write_bytes(b"installer fixture; never executed\n")
        Path(expected).chmod(0o755)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", f'"{trusted}"' if quoted_path else str(trusted))
        if pathext is None:
            monkeypatch.delenv("PATHEXT", raising=False)
        else:
            monkeypatch.setenv("PATHEXT", pathext)

        with (
            patch("specify_cli._version.sys") as platform,
            patch(
                "specify_cli._version.shutil.which",
                side_effect=lambda command: expected if command == expected else None,
            ) as which,
        ):
            platform.platform = "win32"
            found = specify_cli._version._find_installer(name)

        assert found == expected
        assert [call.args[0] for call in which.call_args_list] == [
            str(trusted / f"{name}{suffix}")
            for suffix in ([".COM", ".EXE"] if pathext is None else [".CMD", ".EXE"])
        ]

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    def test_registry_probes_use_absolute_installer_path(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        self.executable(project, "uv")
        self.executable(project, "pipx")
        expected = self.executable(trusted, name)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", os.pathsep.join([".", str(trusted)]))
        monkeypatch.setattr("sys.argv", [str(project / "missing" / "specify")])
        stdout = (
            "specify-cli v0.7.6\n" if name == "uv" else '{"venvs":{"specify-cli":{}}}'
        )

        with (
            patch("specify_cli._version._editable_marker_seen", return_value=False),
            patch(
                "specify_cli._version.subprocess.run",
                return_value=_completed_process(0, stdout=stdout),
            ) as run,
        ):
            detected, signals = _detect_install_method(include_signals=True)

        assert detected == _InstallMethod.UNSUPPORTED
        assert signals.installer_rejections
        run.assert_called_once()
        assert Path(run.call_args.args[0][0]) == expected

    @pytest.mark.parametrize(
        "method,name",
        [
            (_InstallMethod.UV_TOOL, "uv"),
            (_InstallMethod.PIPX, "pipx"),
        ],
    )
    def test_upgrade_executes_selected_absolute_installer(
        self, monkeypatch, tmp_path, method, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        trusted = tmp_path / "trusted"
        trusted.mkdir()
        self.executable(project, name)
        expected = self.executable(trusted, name)
        monkeypatch.chdir(project)
        monkeypatch.setenv("PATH", os.pathsep.join([".", str(trusted)]))

        with (
            patch("specify_cli._version._detect_install_method", return_value=_detection_result(method)),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
            patch("specify_cli._version._verify_upgrade", return_value="0.7.6"),
            patch(
                "specify_cli._version.subprocess.run",
                return_value=_completed_process(0),
            ) as run,
        ):
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v0.7.6"])

        assert result.exit_code == 0
        run.assert_called_once()
        argv = run.call_args.args[0]
        assert Path(argv[0]) == expected
        assert run.call_args.kwargs["shell"] is False
        assert specify_cli._version._render_argv(argv) in strip_ansi(result.output)

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    def test_user_bin_below_non_project_working_directory_is_allowed(
        self, monkeypatch, tmp_path, name
    ):
        user_bin = tmp_path / ".local" / "bin"
        user_bin.mkdir(parents=True)
        expected = self.executable(user_bin, name)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PATH", str(user_bin))

        found = specify_cli._version._find_installer(name)

        assert found is not None
        assert Path(found) == expected

    @pytest.mark.parametrize("name", ["uv", "pipx"])
    def test_project_bin_is_rejected_from_nested_working_directory(
        self, monkeypatch, tmp_path, name
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".git").write_text("gitdir: unused\n")
        project_bin = project / "bin"
        project_bin.mkdir()
        nested = project / "nested"
        nested.mkdir()
        self.executable(project_bin, name)
        monkeypatch.chdir(nested)
        monkeypatch.setenv("PATH", str(project_bin))

        with pytest.raises(specify_cli._version._InstallerRejected):
            specify_cli._version._find_installer(name)


class TestBareUpgradeUvTool:
    """uv-tool happy path, bare invocation."""

    def test_happy_path_end_to_end(self, installer_paths, uv_tool_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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

    def test_one_user_action_no_prompt(self, installer_paths, uv_tool_argv0, clean_environ):
        # The single `invoke` represents the single user action — no prompt.
        # If a prompt existed, runner.invoke would hang waiting for input.
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.6"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release: v0.7.6" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_trailing_zero_equivalent_version_reports_latest_not_newer(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        # Version("1.0") == Version("1.0.0") under packaging even though their
        # canonical strings differ. The no-op message must use Version equality
        # so this prints "Already on latest release", not "... or newer".
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
        ), patch("specify_cli._version._get_installed_version", return_value="1.0"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v1.0.0"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        out = strip_ansi(result.output)
        assert "Already on latest release: v1.0.0" in out
        assert "or newer" not in out
        assert mock_run.call_count == 0

    def test_dev_build_ahead_of_release_reports_newer_noop(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
        ), patch("specify_cli._version._get_installed_version", return_value="0.7.7.dev0"):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade"])

        assert result.exit_code == 0
        assert "Already on latest release or newer: 0.7.7.dev0" in strip_ansi(result.output)
        assert mock_run.call_count == 0

    def test_unparseable_current_version_does_not_false_noop(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value=installer_paths["uv"]), patch(
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
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli._version.shutil.which", return_value=installer_paths["uv"]), patch(
            "specify_cli._version._get_installed_version", return_value="1.0.0rc1"
        ):
            result = runner.invoke(app, ["self", "upgrade", "--tag", "v1.0.0-rc1"])

        assert result.exit_code == 0
        assert "Already on requested release: v1.0.0-rc1" in strip_ansi(result.output)


class TestDryRunUvTool:
    """--dry-run preview path + --dry-run combined with --tag."""

    def test_dry_run_without_tag_resolves_network_but_no_subprocess(
        self,
        installer_paths,
        uv_tool_argv0,
        clean_environ,
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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

    def test_dry_run_with_tag_skips_network(self, installer_paths, uv_tool_argv0, clean_environ):
        # --dry-run with --tag must NOT hit the network.
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ), patch("specify_cli._version.shutil.which", return_value=installer_paths["uv"]), patch(
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
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.subprocess.run"
        ) as mock_run, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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
        installer_paths,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["pipx"] if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["pipx"], "list", "--json"]:
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
        installer_paths,
        unsupported_argv0,
    ):
        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["pipx"] if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["pipx"], "list", "--json"]:
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
        installer_paths,
        unsupported_argv0,
    ):
        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            return installer_paths["pipx"] if name == "pipx" else None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["pipx"], "list", "--json"]:
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
        installer_paths,
        monkeypatch,
        tmp_path,
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])

        def fake_which(name):
            name = Path(name).stem if Path(name).is_absolute() else name
            if name == "uv":
                return installer_paths["uv"]
            if name == "pipx":
                return installer_paths["pipx"]
            return None

        def fake_run(argv, *args, **kwargs):
            if argv[:3] == [installer_paths["uv"], "tool", "list"]:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="specify-cli v0.7.6\n",
                    stderr="",
                )
            if argv[:3] == [installer_paths["pipx"], "list", "--json"]:
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
        self, monkeypatch, tmp_path, rejected_name, installer_paths
    ):
        monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])
        other_name = "pipx" if rejected_name == "uv" else "uv"
        probe_args = ["list", "--json"] if other_name == "pipx" else ["tool", "list"]
        probe_output = (
            '{"venvs":{"specify-cli":{}}}' if other_name == "pipx" else "specify-cli v0.7.6\n"
        )

        def fake_which(name):
            name = Path(name).stem
            if name == rejected_name:
                return f"./{name}"
            if name == other_name:
                return installer_paths[other_name]
            return None

        with patch(
            "specify_cli._version.shutil.which", side_effect=fake_which
        ), patch(
            "specify_cli._version._editable_marker_seen", return_value=False
        ), patch("specify_cli._version.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[installer_paths[other_name], *probe_args],
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
        assert mock_run.call_args.args[0] == [installer_paths[other_name], *probe_args]


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
    def test_tag_whitespace_is_trimmed_before_validation(self, installer_paths, uv_tool_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
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

    def test_pipx_argv_uses_install_force_positional_not_upgrade(self, installer_paths):
        with patch("specify_cli._version.shutil.which", return_value=installer_paths["pipx"]):
            argv = _assemble_installer_argv(_InstallMethod.PIPX, "v0.7.6")
        assert argv == [
            installer_paths["pipx"],
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

    def test_happy_path(self, installer_paths, pipx_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["pipx"]
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
    def test_dry_run_preview_names_pipx(self, installer_paths, pipx_argv0, clean_environ):
        with patch("specify_cli.authentication.http.urllib.request.urlopen") as mock_urlopen, patch(
            "specify_cli._version.shutil.which", return_value=installer_paths["pipx"]
        ), patch("specify_cli._version.subprocess.run") as mock_run, patch(
            "specify_cli._version._get_installed_version", return_value="0.7.5"
        ):
            mock_urlopen.return_value = mock_urlopen_response({"tag_name": "v0.7.6"})
            result = runner.invoke(app, ["self", "upgrade", "--dry-run"])
        assert result.exit_code == 0
        assert "Detected install method: pipx" in strip_ansi(result.output)
        assert mock_run.call_count == 0
