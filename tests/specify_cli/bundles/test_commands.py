from __future__ import annotations

import io  # noqa: F401
import json  # noqa: F401
from pathlib import Path
from unittest.mock import patch  # noqa: F401

import pytest
import yaml  # noqa: F401
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.packager import build_bundle  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401

runner = CliRunner()


@pytest.mark.parametrize("command", ["install", "add", "init", "update"])
def test_install_adapters_render_structured_warnings_once(
    project: Path, monkeypatch, command: str,
):
    from types import SimpleNamespace

    from specify_cli.bundles import command_update, installer
    from specify_cli.bundles.manifest import BundleManifest, ComponentRef
    from specify_cli.bundles.primitives import _bundled_pin_warning
    from specify_cli.bundles.records import InstalledBundleRecord, save_records
    from tests.specify_cli.bundles.helpers import valid_manifest_dict, write_manifest

    data = valid_manifest_dict()
    manifest = BundleManifest.from_dict(data)
    component = ComponentRef(kind="extensions", id="x[/yellow]", version="1.0.0")
    warning = _bundled_pin_warning("Extension", component, "1.0.1")
    assert warning is not None
    outcome = installer.InstallResult(bundle_id=manifest.bundle.id, warnings=[warning])
    monkeypatch.setattr(installer, "install_bundle", lambda *a, **kw: outcome)

    if command == "update":
        save_records(project, [
            InstalledBundleRecord.create(manifest.bundle.id, manifest.bundle.version, []),
        ])
        stack = SimpleNamespace(resolve=lambda target: SimpleNamespace(install_allowed=True))
        monkeypatch.setattr(command_update, "_build_stack", lambda *a, **kw: stack)
        monkeypatch.setattr(command_update, "_download_manifest", lambda *a, **kw: manifest)
        target = manifest.bundle.id
    else:
        target = str(write_manifest(project / "bundle-source", data))

    result = runner.invoke(app, ["bundle", command, target, "--offline"])

    assert result.exit_code == 0, result.output
    assert result.stderr.count("Warning:") == 1
    assert "x[/yellow]" in strip_ansi(result.stderr)
    assert "newer packaged patch" in " ".join(result.stderr.split())
    assert "Warning:" not in result.stdout


def test_bundle_help_lists_all_commands():
    result = runner.invoke(app, ["bundle", "--help"])
    assert result.exit_code == 0
    for cmd in (
        "search",
        "info",
        "list",
        "install",
        "add",
        "update",
        "remove",
        "validate",
        "build",
        "init",
        "catalog",
    ):
        assert cmd in result.output


def test_fail_writes_error_to_stderr_not_stdout(capsys):
    """_fail must write to stderr, not stdout: every bundle command routes errors
    through it, and under --json the error would otherwise corrupt the JSON payload
    that consumers read from stdout."""
    import typer

    from specify_cli.bundles._commands import _fail

    with pytest.raises(typer.Exit):
        _fail("something broke")
    captured = capsys.readouterr()
    assert "something broke" in captured.err
    assert "something broke" not in captured.out


@pytest.mark.parametrize(
    "argv, expected",
    [
        (
            ["bundle", "catalog", "add", "ssh://ex[/red]ample.com/c.json"],
            "ssh://ex[/red]ample.com/c.json",
        ),
        (["bundle", "catalog", "remove", "no[/red]such"], "no[/red]such"),
        (["bundle", "update", "no[/red]such"], "no[/red]such"),
        (["bundle", "remove", "no[/red]such"], "no[/red]such"),
    ],
)
def test_error_paths_escape_rich_markup(project: Path, argv: list, expected: str):
    result = runner.invoke(app, argv)

    assert result.exit_code == 1
    # A MarkupError would surface here as an exception rather than a clean exit.
    assert isinstance(result.exception, SystemExit)
    assert expected in strip_ansi(result.output)


@pytest.mark.parametrize(
    ("argv", "target"),
    [
        (
            ["bundle", "install", "demo"],
            "specify_cli.bundles.project.find_project_root",
        ),
        (
            ["bundle", "update", "demo"],
            "specify_cli.bundles.command_update.require_project_root",
        ),
    ],
)
def test_refresh_cli_shows_restoration_notes(monkeypatch, argv, target):
    """``bundle install`` and ``bundle update`` show notes after the error."""
    from specify_cli.bundles import BundlerError

    def _boom(*_args, **_kwargs):
        exc = BundlerError("primary failure")
        exc.add_note("Could not restore step 'my-step' from backup '/tmp/bak'")
        raise exc

    monkeypatch.setattr(target, _boom)
    result = runner.invoke(app, argv)
    output = " ".join(strip_ansi(result.output).split())
    assert result.exit_code == 1, result.output
    assert "Error:" in output
    assert "primary failure" in output
    assert "Could not restore step 'my-step'" in output
    assert "/tmp/bak" in output
    assert output.index("primary failure") < output.index("Could not restore")


def test_update_cli_shows_notes_from_real_install_bundle_refresh(
    project: Path, monkeypatch
):
    """A refresh error's notes survive ``install_bundle`` and reach the CLI.

    ``install_bundle`` runs for real here: only the primitive installer is
    faked, and its step refresh fails the way a failed rollback does (the
    install error first, the restoration failure as a note).
    """
    from types import SimpleNamespace

    from specify_cli.bundles import BundlerError, adapters, command_update
    from specify_cli.bundles.manifest import BundleManifest, ComponentRef
    from specify_cli.bundles.records import InstalledBundleRecord, save_records
    from tests.specify_cli.bundles.helpers import FakeInstaller, valid_manifest_dict

    data = valid_manifest_dict(provides={"steps": [{"id": "my-step"}]})
    manifest = BundleManifest.from_dict(data)
    step = ComponentRef(kind="steps", id="my-step")
    save_records(project, [
        InstalledBundleRecord.create(manifest.bundle.id, manifest.bundle.version, [step]),
    ])

    class _RollbackFailingInstaller(FakeInstaller):
        def refresh(self, project_root, component):
            super().refresh(project_root, component)
            exc = BundlerError(f"Failed to install step '{component.id}'.")
            exc.add_note(
                f"Could not restore step '{component.id}' from backup "
                "'/tmp/speckit-step-refresh-x': restore copy failed"
            )
            raise exc

    fake = _RollbackFailingInstaller()
    fake.installed.add(("steps", "my-step"))
    stack = SimpleNamespace(resolve=lambda target: SimpleNamespace(install_allowed=True))
    monkeypatch.setattr(command_update, "_build_stack", lambda *a, **kw: stack)
    monkeypatch.setattr(command_update, "_download_manifest", lambda *a, **kw: manifest)
    monkeypatch.setattr(adapters, "DefaultPrimitiveInstaller", lambda **kw: fake)

    result = runner.invoke(app, ["bundle", "update", manifest.bundle.id])

    assert result.exit_code == 1, result.output
    assert fake.refresh_calls == [("steps", "my-step")]
    output = " ".join(strip_ansi(result.stderr).split())
    assert "Error: Failed to install step 'my-step'." in output
    assert "Could not restore step 'my-step'" in output
    assert "/tmp/speckit-step-refresh-x" in output
    assert "restore copy failed" in output
    assert output.index("Failed to install step") < output.index("Could not restore")
