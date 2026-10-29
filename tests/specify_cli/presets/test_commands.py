"""Shared error-boundary regressions for the preset CLI group."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.file_helper import FileHelperError, SymlinkDeniedError
from specify_cli.presets import PresetManager, PresetRegistry, PresetResolver
from tests.conftest import strip_ansi


def _registry_error(project: Path) -> str:
    registry = project / ".specify" / "presets" / ".registry"
    return (
        f"Cannot access preset registry {registry}: registry files and parent "
        "directories must not be symlinks. Replace linked entries with regular "
        "files or directories; allow_symlinks does not apply to preset registry metadata."
    )


@pytest.fixture(params=["directory", "file", "dangling-directory", "dangling-file"])
def linked_registry(tmp_path: Path, request: pytest.FixtureRequest) -> Iterator[Path]:
    project = tmp_path / "project"
    presets = project / ".specify" / "presets"
    presets.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / ".registry"
    sentinel.write_bytes(b"not registry JSON")
    is_directory = request.param.endswith("directory")
    link = presets if is_directory else presets / ".registry"
    target = outside if is_directory else sentinel
    if request.param.startswith("dangling"):
        target = outside / "missing"
    if is_directory:
        presets.rmdir()
    try:
        link.symlink_to(target, target_is_directory=is_directory)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    yield project

    assert link.is_symlink()
    assert sentinel.read_bytes() == b"not registry JSON"
    assert not (outside / "missing").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["list"],
        ["info", "example"],
        ["resolve", "spec-template"],
        ["add", "example"],
        ["remove", "example"],
        ["update", "example"],
        ["enable", "example"],
        ["disable", "example"],
        ["set-priority", "example", "5"],
    ],
)
@pytest.mark.parametrize("allow_symlinks", [False, True])
def test_text_commands_report_registry_specific_symlink_error(
    linked_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    allow_symlinks: bool,
):
    (linked_registry / ".specify" / "init-options.json").write_text(
        json.dumps({"allow_symlinks": allow_symlinks}), encoding="utf-8",
    )
    monkeypatch.chdir(linked_registry)

    result = CliRunner().invoke(
        app, ["preset", *arguments], catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert " ".join(strip_ansi(result.stdout).split()) == (
        f"Error: {_registry_error(linked_registry)}"
    )
    assert result.stderr == ""


@pytest.mark.parametrize("arguments", [["list"], ["info", "example"]])
@pytest.mark.parametrize("allow_symlinks", [False, True])
def test_json_commands_report_registry_specific_symlink_error(
    linked_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    allow_symlinks: bool,
):
    (linked_registry / ".specify" / "init-options.json").write_text(
        json.dumps({"allow_symlinks": allow_symlinks}), encoding="utf-8",
    )
    monkeypatch.chdir(linked_registry)

    result = CliRunner().invoke(
        app, ["preset", *arguments, "--json"], catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr) == {"error": _registry_error(linked_registry)}
    assert result.stderr.count("\n") == 1


@pytest.mark.parametrize(
    "command", ["add", "remove", "update", "enable", "disable", "set-priority"],
)
def test_mutating_commands_handle_registry_save_errors(
    project_dir: Path, pack_dir: Path, monkeypatch: pytest.MonkeyPatch, command: str,
):
    if command != "add":
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "99.0.0")
        if command == "enable":
            manager.registry.update("test-pack", {"enabled": False})

    def fail_save(self):
        raise SymlinkDeniedError(_registry_error(project_dir))

    monkeypatch.setattr(PresetRegistry, "_save", fail_save)
    monkeypatch.chdir(project_dir)
    arguments = ["preset", command, "test-pack"]
    if command == "add":
        arguments = ["preset", "add", "--dev", str(pack_dir)]
    elif command == "set-priority":
        arguments.append("5")

    result = CliRunner().invoke(app, arguments, catch_exceptions=False)

    assert result.exit_code == 1
    output = " ".join(strip_ansi(result.stdout).split())
    assert _registry_error(project_dir) in output
    assert "explicitly allow symlinks" not in output
    assert "Traceback" not in result.output


@pytest.mark.parametrize("phase", ["construction", "composition"])
def test_resolve_handles_filesystem_errors_at_each_phase(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch, phase: str,
):
    def fail(*args, **kwargs):
        raise SymlinkDeniedError(_registry_error(project_dir))

    if phase == "construction":
        monkeypatch.setattr("specify_cli.presets.PresetResolver", fail)
    else:
        monkeypatch.setattr(
            PresetResolver, "collect_all_layers",
            lambda *args: [
                {"path": Path("top.md"), "source": "preset:example", "strategy": "append"},
            ],
        )
        monkeypatch.setattr(PresetResolver, "resolve_content", fail)
    monkeypatch.chdir(project_dir)

    result = CliRunner().invoke(
        app, ["preset", "resolve", "spec-template"], catch_exceptions=False,
    )

    assert result.exit_code == 1
    assert _registry_error(project_dir) in " ".join(strip_ansi(result.stdout).split())
    assert "explicitly allow symlinks" not in result.output
    assert "composition error" not in result.output


def test_update_replacement_policy_error_preserves_removal_context(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch,
):
    PresetRegistry(project_dir / ".specify" / "presets").restore(
        "example", {"version": "1.0", "enabled": True},
    )

    def fail_add(**kwargs):
        raise SymlinkDeniedError(_registry_error(project_dir))

    monkeypatch.setattr(
        "specify_cli.presets._commands.preset_remove", lambda preset_id: None,
    )
    monkeypatch.setattr("specify_cli.presets._commands.preset_add", fail_add)
    monkeypatch.chdir(project_dir)

    result = CliRunner().invoke(
        app, ["preset", "update", "example"], catch_exceptions=False,
    )

    assert result.exit_code == 1
    output = " ".join(strip_ansi(result.stdout).split())
    assert "previous preset was removed" in output
    assert "specify preset add" in output
    assert _registry_error(project_dir) in output
    assert "explicitly allow symlinks" not in output


@pytest.mark.parametrize("json_output", [False, True])
def test_other_file_helper_errors_keep_their_diagnostics(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch, json_output: bool,
):
    def fail(*args, **kwargs):
        raise FileHelperError("unsupported registry path [red]")

    monkeypatch.setattr("specify_cli.presets.PresetManager", fail)
    monkeypatch.chdir(project_dir)
    arguments = ["preset", "list"]
    if json_output:
        arguments.append("--json")

    result = CliRunner().invoke(app, arguments, catch_exceptions=False)

    assert result.exit_code == 1
    message = "unsupported registry path [red]"
    if json_output:
        assert result.stdout == ""
        assert json.loads(result.stderr) == {"error": message}
    else:
        assert " ".join(strip_ansi(result.stdout).split()) == f"Error: {message}"
        assert result.stderr == ""


def test_preset_error_boundary_does_not_hide_unexpected_errors(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch,
):
    def fail(*args, **kwargs):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr("specify_cli.presets.PresetManager", fail)
    monkeypatch.chdir(project_dir)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        CliRunner().invoke(app, ["preset", "list"], catch_exceptions=False)
