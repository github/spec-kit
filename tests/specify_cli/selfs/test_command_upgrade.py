"""Command tests for ``specify self upgrade``."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from specify_cli import app
from tests.specify_cli.self_upgrade_helpers import runner, strip_ansi


@pytest.mark.parametrize(("method", "name"), [("uv-tool", "uv"), ("pipx", "pipx")])
@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("dry_run", [False, True])
def test_unsafe_installer_lookup_aborts_without_execution(
    monkeypatch, tmp_path, request, method, name, absolute, dry_run
):
    request.getfixturevalue("uv_tool_argv0" if method == "uv-tool" else "pipx_argv0")
    # Exercise the Windows fixture directory collision on every platform.
    (tmp_path / name).mkdir(exist_ok=True)
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    decoy = project / name
    decoy.write_text("decoy; must never be executed\n", encoding="utf-8")
    decoy.chmod(0o755)
    unsafe_path = str(decoy) if absolute else f"./{name}"

    with patch(
        "specify_cli._version.shutil.which", return_value=unsafe_path
    ), patch(
        "specify_cli._version._get_installed_version", return_value="0.7.5"
    ), patch("specify_cli._version.subprocess.run") as mock_run:
        args = ["self", "upgrade", "--tag", "v0.7.6"]
        if dry_run:
            args.append("--dry-run")
        result = runner.invoke(app, args)

    assert result.exit_code == (0 if dry_run else 3)
    output = strip_ansi(result.output)
    assert f"Installer {name} rejected" in output
    assert "PATH" in output
    assert ("Run from another directory" if absolute else "absolute PATH") in output
    if not absolute:
        assert "Run from a directory without a matching installer executable" in output
    assert "reinstall" not in output
    assert "not found on PATH" not in output
    mock_run.assert_not_called()


@pytest.mark.parametrize("name", ["uv", "pipx"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_registry_probe_rejection_guidance_is_preserved(
    monkeypatch, tmp_path, name, dry_run
):
    monkeypatch.setattr("sys.argv", [str(tmp_path / "missing" / "specify")])
    with patch(
        "specify_cli._version.shutil.which",
        side_effect=lambda command: f"./{name}" if Path(command).stem == name else None,
    ), patch(
        "specify_cli._version._editable_marker_seen", return_value=False
    ), patch("specify_cli._version.subprocess.run") as mock_run:
        args = ["self", "upgrade", "--tag", "v0.7.6"]
        if dry_run:
            args.append("--dry-run")
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert f"Installer {name} rejected" in output
    assert "absolute PATH" in output
    assert "Run from a directory without a matching installer executable" in output
    mock_run.assert_not_called()


@pytest.mark.parametrize(("method", "name"), [("uv-tool", "uv"), ("pipx", "pipx")])
@pytest.mark.parametrize("dry_run", [False, True])
def test_deleted_working_directory_gets_rejection_guidance(
    request, method, name, dry_run
):
    request.getfixturevalue("uv_tool_argv0" if method == "uv-tool" else "pipx_argv0")
    with patch(
        "specify_cli._version.shutil.which", return_value=sys.executable
    ), patch(
        "specify_cli._version.Path.cwd",
        side_effect=FileNotFoundError("working directory was deleted"),
    ), patch(
        "specify_cli._version._get_installed_version", return_value="0.7.5"
    ), patch("specify_cli._version.subprocess.run") as mock_run:
        args = ["self", "upgrade", "--tag", "v0.7.6"]
        if dry_run:
            args.append("--dry-run")
        result = runner.invoke(app, args)

    assert result.exit_code == (0 if dry_run else 3)
    output = strip_ansi(result.output)
    assert f"Installer {name} rejected: could not validate its path" in output
    assert "working directory was deleted" in output
    assert "existing, accessible working directory" in output
    mock_run.assert_not_called()


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("rejected_name", ["uv", "pipx"])
def test_rejected_probe_prevents_selecting_a_different_installer(
    monkeypatch, tmp_path, dry_run, rejected_name, installer_paths
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
    ), patch(
        "specify_cli._version._get_installed_version", return_value="0.7.5"
    ), patch("specify_cli._version.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[installer_paths[other_name], *probe_args],
            returncode=0,
            stdout=probe_output,
            stderr="",
        )
        args = ["self", "upgrade", "--tag", "v0.7.6"]
        if dry_run:
            args.append("--dry-run")
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    output = strip_ansi(result.output)
    assert f"Installer {rejected_name} rejected" in output
    assert "Could not identify your install method automatically" in output
    assert "Upgrading specify-cli" not in output
    assert "not found on PATH" not in output
    assert mock_run.call_count == 1
    assert mock_run.call_args.args[0] == [installer_paths[other_name], *probe_args]


class TestTagValidation:
    """--tag option parsing and command help."""

    def test_valid_stable_tag(self, installer_paths, uv_tool_argv0, clean_environ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.7.6"],
            )
        assert result.exit_code == 0

    def test_valid_dev_suffix_tag(self, installer_paths, uv_tool_argv0, clean_environ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0.dev0"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0.dev0" in strip_ansi(result.output)

    def test_valid_rc_tag(self, installer_paths, uv_tool_argv0, clean_environ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v1.0.0-rc1"],
            )
        assert result.exit_code == 0

    def test_valid_beta_dot_tag_uses_pep440_equivalent_for_noop(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch(
                "specify_cli._version._get_installed_version", return_value="1.0.0b1"
            ),
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--tag", "v1.0.0-beta.1"],
            )
        assert result.exit_code == 0
        assert "Already on requested release: v1.0.0-beta.1" in strip_ansi(
            result.output
        )

    def test_valid_build_metadata_tag(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "v0.8.0+build.42"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.8.0+build.42" in strip_ansi(result.output)

    def test_uppercase_v_prefix_is_folded_to_lowercase(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
        ):
            result = runner.invoke(
                app,
                ["self", "upgrade", "--dry-run", "--tag", "V0.7.6"],
            )
        assert result.exit_code == 0
        assert "Target version: v0.7.6" in strip_ansi(result.output)

    def test_valid_prerelease_with_build_metadata_tag(
        self, installer_paths, uv_tool_argv0, clean_environ
    ):
        with (
            patch(
                "specify_cli._version.shutil.which", return_value=installer_paths["uv"]
            ),
            patch("specify_cli._version._get_installed_version", return_value="0.7.5"),
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

    def test_rejection_message_keeps_the_suffix_token(
        self, uv_tool_argv0, clean_environ
    ):
        result = runner.invoke(app, ["self", "upgrade", "--tag", "latest"])
        assert result.exit_code == 1
        assert "expected vMAJOR.MINOR.PATCH[suffix]" in strip_ansi(result.output)

    def test_tag_option_help_keeps_the_suffix_token(self):
        result = runner.invoke(app, ["self", "upgrade", "--help"])
        assert result.exit_code == 0
        assert "[suffix]" in strip_ansi(result.output)
