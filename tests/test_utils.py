"""Tests for command execution and Docker executable discovery."""

from __future__ import annotations

import errno
import inspect
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from specify_cli import check_tool, run_command
from specify_cli._utils import docker_agent_command


def _symlink_or_skip(link, target, *, target_is_directory=False):
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")


def test_run_command_has_no_shell_parameter():
    """The shell-injection surface is removed at the API level.

    ``run_command`` must never accept a ``shell`` parameter: the argv-list
    contract makes shell interpolation impossible by construction, and there is
    no runtime mode to re-enable it. Passing ``shell=`` is a hard ``TypeError``.
    """
    assert "shell" not in inspect.signature(run_command).parameters
    with pytest.raises(TypeError):
        run_command(["echo", "blocked"], shell=True)  # type: ignore[call-arg]  # noqa: S604


@pytest.mark.parametrize("docker_installed", [False, True])
def test_docker_probe_ignores_implicit_windows_current_directory(
    tmp_path, monkeypatch, docker_installed
):
    """Model Python 3.11's implicit Windows CWD search, even with a clean PATH."""
    project = tmp_path / "project"
    project.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", str(installed))
    monkeypatch.setenv("PATHEXT", ".EXE;.CMD")
    monkeypatch.setattr("specify_cli._utils.sys.platform", "win32")

    def windows_which(command):
        if command == "docker":
            return str(project / "docker.exe")
        if command == str(installed / "docker.EXE") and docker_installed:
            return str(installed / "docker.exe")
        return None

    monkeypatch.setattr(shutil, "which", windows_which)
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    assert check_tool("docker-agent") is docker_installed
    if docker_installed:
        run.assert_called_once_with(
            [str(installed / "docker.exe"), "agent", "version"],
            capture_output=True,
            check=False,
            timeout=5,
        )
    else:
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize("entry", ["empty", "relative", "cwd", "child", "symlink"])
def test_docker_discovery_skips_checkout_executables(
    tmp_path, monkeypatch, name, entry
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    local_bin = project / "bin"
    local_bin.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    monkeypatch.setenv("PATHEXT", ".exe")
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (project, local_bin, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    link = tmp_path / "linked-bin"
    if entry == "symlink":
        _symlink_or_skip(link, local_bin, target_is_directory=True)
    entries = {
        "empty": "",
        "relative": "bin",
        "cwd": str(project),
        "child": str(local_bin),
        "symlink": str(link),
    }
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([entries[entry], str(installed)]))
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    command = docker_agent_command()

    expected = str(installed / filename)
    if name == "docker":
        assert command == [expected, "agent", "run"]
        run.assert_called_once_with(
            [expected, "agent", "version"],
            capture_output=True,
            check=False,
            timeout=5,
        )
    else:
        assert command == [expected, "run"]
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
def test_docker_discovery_rejects_executable_symlink_into_checkout(
    tmp_path, monkeypatch, name
):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("PATHEXT", ".exe")
    filename = f"{name}.exe" if os.name == "nt" else name
    executable = project / filename
    executable.touch()
    executable.chmod(0o755)
    installed = tmp_path / "installed"
    installed.mkdir()
    _symlink_or_skip(installed / filename, executable)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", str(installed))
    run = Mock()
    monkeypatch.setattr(subprocess, "run", run)

    assert docker_agent_command() is None
    run.assert_not_called()


@pytest.mark.parametrize(
    "failure", [1, OSError("unavailable"), subprocess.TimeoutExpired("docker", 5)]
)
def test_docker_plugin_probe_failures_are_unavailable(tmp_path, monkeypatch, failure):
    project = tmp_path / "project"
    project.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    monkeypatch.setenv("PATHEXT", ".exe")
    executable = installed / ("docker.exe" if os.name == "nt" else "docker")
    executable.touch()
    executable.chmod(0o755)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", str(installed))
    run = Mock()
    if isinstance(failure, Exception):
        run.side_effect = failure
    else:
        run.return_value = subprocess.CompletedProcess([], failure)
    monkeypatch.setattr(subprocess, "run", run)

    assert docker_agent_command() is None
    run.assert_called_once()


def test_docker_discovery_with_empty_path_never_probes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "")
    which = Mock()
    run = Mock()
    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(subprocess, "run", run)

    assert docker_agent_command() is None
    which.assert_not_called()
    run.assert_not_called()


def test_docker_discovery_uses_default_path_when_unset(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    monkeypatch.setenv("PATHEXT", ".exe")
    executable = installed / ("docker-agent.exe" if os.name == "nt" else "docker-agent")
    executable.touch()
    executable.chmod(0o755)
    monkeypatch.chdir(project)
    monkeypatch.delenv("PATH", raising=False)
    monkeypatch.setattr(os, "defpath", str(installed))

    assert docker_agent_command() == [str(executable), "run"]


@pytest.mark.parametrize("pathext", [None, ""])
@pytest.mark.parametrize("name", ["docker", "docker-agent"])
def test_docker_discovery_uses_default_windows_extensions(
    tmp_path, monkeypatch, name, pathext
):
    project = tmp_path / "project"
    project.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    executable = str(installed / f"{name}.EXE")
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", str(installed))
    if pathext is None:
        monkeypatch.delenv("PATHEXT", raising=False)
    else:
        monkeypatch.setenv("PATHEXT", pathext)
    monkeypatch.setattr("specify_cli._utils.sys.platform", "win32")
    monkeypatch.setattr(
        shutil, "which", lambda command: executable if command == executable else None
    )
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    expected = [executable, "agent", "run"] if name == "docker" else [executable, "run"]
    assert docker_agent_command() == expected
    if name == "docker":
        run.assert_called_once()
    else:
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize("entry", ["directory", "executable-symlink"])
def test_docker_discovery_rejects_case_aliases_of_checkout(
    tmp_path, monkeypatch, name, entry
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    alias = tmp_path / "PROJECT"
    if not alias.exists() or not alias.samefile(project):
        pytest.skip("requires a case-insensitive filesystem")
    local_bin = project / "bin"
    local_bin.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    executable = local_bin / filename
    executable.touch()
    executable.chmod(0o755)
    search_directory = alias / "bin"
    if entry == "executable-symlink":
        search_directory = tmp_path / "installed"
        search_directory.mkdir()
        _symlink_or_skip(search_directory / filename, alias / "bin" / filename)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", str(search_directory))
    monkeypatch.setenv("PATHEXT", ".exe")
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    assert docker_agent_command() is None
    run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize(
    "stage",
    ["directory-resolve", "directory-identity", "executable-resolve", "executable-identity", "which"],
)
@pytest.mark.parametrize(
    "error",
    [
        PermissionError("access denied"),
        OSError(errno.ELOOP, "too many symbolic links"),
        RuntimeError("Symlink loop from candidate"),
    ],
)
def test_docker_discovery_skips_failed_candidates(
    tmp_path, monkeypatch, name, stage, error
):
    project = tmp_path / "project"
    project.mkdir()
    inaccessible = tmp_path / "inaccessible"
    inaccessible.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (inaccessible, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    original_resolve = type(tmp_path).resolve
    original_samefile = type(tmp_path).samefile
    original_which = shutil.which

    def resolve(path, *args, **kwargs):
        if (
            (stage == "directory-resolve" and path == inaccessible)
            or (stage == "executable-resolve" and path == inaccessible / filename)
        ):
            raise error
        return original_resolve(path, *args, **kwargs)

    def samefile(path, other):
        if (
            (stage == "directory-identity" and path == inaccessible)
            or (stage == "executable-identity" and path == inaccessible / filename)
        ):
            raise error
        return original_samefile(path, other)

    def which(command):
        if stage == "which" and command == str(inaccessible / filename):
            raise error
        return original_which(command)

    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([str(inaccessible), str(installed)]))
    monkeypatch.setenv("PATHEXT", ".exe")
    monkeypatch.setattr(type(tmp_path), "resolve", resolve)
    monkeypatch.setattr(type(tmp_path), "samefile", samefile)
    monkeypatch.setattr(shutil, "which", which)
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.warns(UserWarning, match="Skipping Docker executable search candidate"):
        command = docker_agent_command()

    expected = str(installed / filename)
    assert command == ([expected, "agent", "run"] if name == "docker" else [expected, "run"])
    if name == "docker":
        assert run.call_args.args[0] == [expected, "agent", "version"]
        run.assert_called_once()
    else:
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
def test_docker_discovery_skips_cyclic_directory(tmp_path, monkeypatch, name):
    project = tmp_path / "project"
    project.mkdir()
    loop = tmp_path / "loop"
    _symlink_or_skip(loop, loop, target_is_directory=True)
    installed = tmp_path / "installed"
    installed.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    executable = installed / filename
    executable.touch()
    executable.chmod(0o755)
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", os.pathsep.join([str(loop), str(installed)]))
    monkeypatch.setenv("PATHEXT", ".exe")
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.warns(UserWarning, match="Skipping Docker executable search candidate"):
        command = docker_agent_command()

    expected = str(executable)
    assert command == ([expected, "agent", "run"] if name == "docker" else [expected, "run"])


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize(
    "launch_kind", ["home", "filesystem-root", "plain-directory", "project-subdirectory"]
)
@pytest.mark.parametrize("explicit_project", [False, True])
def test_docker_discovery_keeps_external_installations_available(
    tmp_path, monkeypatch, name, launch_kind, explicit_project
):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".specify").mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    launch = {
        "home": home,
        "filesystem-root": Path(tmp_path.anchor),
        "plain-directory": tmp_path / "launch",
        "project-subdirectory": home / "project" / "nested",
    }[launch_kind]
    if launch_kind in {"plain-directory", "project-subdirectory"}:
        launch.mkdir(parents=True)
    installed = (launch if launch_kind == "plain-directory" else home) / ".local" / "bin"
    installed.mkdir(parents=True)
    project = home / "project"
    local_bin = project / "bin"
    local_bin.mkdir(parents=True)
    (project / ".git").mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (local_bin, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    directories = [str(installed)]
    if explicit_project or launch_kind == "project-subdirectory":
        directories.insert(0, str(local_bin))
    monkeypatch.chdir(launch)
    monkeypatch.setenv("PATH", os.pathsep.join(directories))
    monkeypatch.setenv("PATHEXT", ".exe")
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    command = docker_agent_command(project_root=project if explicit_project else None)

    expected = str(installed / filename)
    assert command == ([expected, "agent", "run"] if name == "docker" else [expected, "run"])
    if name == "docker":
        run.assert_called_once_with(
            [expected, "agent", "version"],
            capture_output=True,
            check=False,
            timeout=5,
        )
    else:
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize("marker", ["git-directory", "git-file", "specify"])
@pytest.mark.parametrize("nested_launch", [False, True])
def test_docker_discovery_excludes_detected_project_subtree(
    tmp_path, monkeypatch, name, marker, nested_launch
):
    project = tmp_path / "project"
    project.mkdir()
    if marker == "git-file":
        (project / ".git").touch()
    else:
        (project / (".git" if marker == "git-directory" else ".specify")).mkdir()
    local_bin = project / "bin"
    local_bin.mkdir()
    launch = project
    if nested_launch:
        launch = project / "nested"
        launch.mkdir()
        (launch / ".git").mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (local_bin, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    monkeypatch.chdir(launch)
    monkeypatch.setenv("PATH", os.pathsep.join([str(local_bin), str(installed)]))
    monkeypatch.setenv("PATHEXT", ".exe")
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    command = docker_agent_command()

    expected = str(installed / filename)
    assert command == ([expected, "agent", "run"] if name == "docker" else [expected, "run"])
    if name == "docker":
        assert run.call_args.args[0] == [expected, "agent", "version"]
        run.assert_called_once()
    else:
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize("explicit_project", [False, True])
@pytest.mark.parametrize("indirect", [False, True])
def test_docker_discovery_rejects_project_symlinks_to_external_executables(
    tmp_path, monkeypatch, name, explicit_project, indirect
):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    untrusted = tmp_path / "untrusted"
    untrusted.mkdir()
    installed = tmp_path / "installed"
    installed.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (untrusted, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    link = project / "bin"
    _symlink_or_skip(link, untrusted, target_is_directory=True)
    search_entry = link
    if indirect:
        search_entry = tmp_path / "alias"
        _symlink_or_skip(search_entry, link, target_is_directory=True)
    launch = project
    if explicit_project:
        launch = tmp_path / "launch"
        launch.mkdir()
    monkeypatch.chdir(launch)
    monkeypatch.setenv("PATH", os.pathsep.join([str(search_entry), str(installed)]))
    monkeypatch.setenv("PATHEXT", ".exe")
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(subprocess, "run", run)

    command = docker_agent_command(project_root=project if explicit_project else None)

    expected = str(installed / filename)
    assert command == ([expected, "agent", "run"] if name == "docker" else [expected, "run"])
    if name == "docker":
        assert run.call_args.args[0] == [expected, "agent", "version"]
        run.assert_called_once()
    else:
        run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize("metadata", ["init-options.json", "integration.json"])
def test_docker_discovery_recognizes_an_initialized_home_project(
    tmp_path, monkeypatch, name, metadata
):
    home = tmp_path / "home"
    marker = home / ".specify"
    marker.mkdir(parents=True)
    (marker / metadata).write_text("{}")
    local_bin = home / ".local" / "bin"
    local_bin.mkdir(parents=True)
    installed = tmp_path / "installed"
    installed.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (local_bin, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    monkeypatch.chdir(home)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("PATH", os.pathsep.join([str(local_bin), str(installed)]))
    monkeypatch.setenv("PATHEXT", ".exe")
    monkeypatch.setattr(subprocess, "run", Mock(return_value=subprocess.CompletedProcess([], 0)))

    command = docker_agent_command()

    expected = str(installed / filename)
    assert command == ([expected, "agent", "run"] if name == "docker" else [expected, "run"])
