"""Tests for the ``specify preset update`` command."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest
import typer

from specify_cli.presets._commands import (
    _render_powershell_argv,
    preset_update,
)
from tests.conftest import strip_ansi


class TestPresetUpdateCommand:
    """Test the destructive remove-then-add update contract."""

    @staticmethod
    def _manager(monkeypatch, project_dir, installed=True):
        from specify_cli.presets import _commands as commands

        registry = SimpleNamespace(is_installed=lambda _preset_id: installed)
        manager = SimpleNamespace(registry=registry)
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.presets.PresetManager", lambda _root: manager)
        return commands

    def test_unknown_preset_fails_without_remove_or_add(self, project_dir, monkeypatch):
        commands = self._manager(monkeypatch, project_dir, installed=False)
        calls = []
        monkeypatch.setattr(
            commands, "preset_remove", lambda *_args: calls.append("remove")
        )
        monkeypatch.setattr(
            commands, "preset_add", lambda **_kwargs: calls.append("add")
        )

        with pytest.raises(typer.Exit) as exc_info:
            preset_update("missing", from_url=None, dev=None, priority=10)

        assert exc_info.value.exit_code == 1
        assert calls == []

    @pytest.mark.parametrize(
        ("from_url", "dev"),
        [
            ("https://example.com/preset.zip", "./preset"),
            ("", "./preset"),
            ("https://example.com/preset.zip", ""),
        ],
    )
    def test_mutually_exclusive_sources_are_rejected(
        self, project_dir, monkeypatch, from_url, dev
    ):
        commands = self._manager(monkeypatch, project_dir)
        calls = []
        monkeypatch.setattr(
            commands, "preset_remove", lambda *_args: calls.append("remove")
        )
        monkeypatch.setattr(
            commands, "preset_add", lambda **_kwargs: calls.append("add")
        )

        with pytest.raises(typer.Exit) as exc_info:
            preset_update(
                "test-pack",
                from_url=from_url,
                dev=dev,
                priority=10,
            )

        assert exc_info.value.exit_code == 1
        assert calls == []

    @pytest.mark.parametrize(
        ("from_url", "dev", "option"),
        [("", None, "--from"), (None, "", "--dev")],
    )
    def test_empty_source_is_rejected_before_removal(
        self, project_dir, monkeypatch, capsys, from_url, dev, option
    ):
        commands = self._manager(monkeypatch, project_dir)
        calls = []
        monkeypatch.setattr(
            commands, "preset_remove", lambda *_args: calls.append("remove")
        )
        monkeypatch.setattr(
            commands, "preset_add", lambda **_kwargs: calls.append("add")
        )

        with pytest.raises(typer.Exit) as exc_info:
            preset_update(
                "test-pack",
                from_url=from_url,
                dev=dev,
                priority=10,
            )

        assert exc_info.value.exit_code == 1
        assert calls == []
        assert f"{option} must not be empty" in strip_ansi(capsys.readouterr().out)

    def test_remove_failure_prevents_add(self, project_dir, monkeypatch):
        commands = self._manager(monkeypatch, project_dir)
        calls = []

        def fail_remove(_preset_id):
            calls.append("remove")
            raise typer.Exit(1)

        monkeypatch.setattr(commands, "preset_remove", fail_remove)
        monkeypatch.setattr(
            commands, "preset_add", lambda **_kwargs: calls.append("add")
        )

        with pytest.raises(typer.Exit) as exc_info:
            preset_update("test-pack", from_url=None, dev=None, priority=10)

        assert exc_info.value.exit_code == 1
        assert calls == ["remove"]

    def test_update_forwards_id_sources_and_priority_to_add(
        self, project_dir, monkeypatch
    ):
        commands = self._manager(monkeypatch, project_dir)
        calls = []
        monkeypatch.setattr(
            commands,
            "preset_remove",
            lambda preset_id: calls.append(("remove", preset_id)),
        )
        monkeypatch.setattr(
            commands,
            "preset_add",
            lambda **kwargs: calls.append(("add", kwargs)),
        )

        preset_update(
            "test-pack",
            from_url="https://example.com/replacement.zip",
            dev=None,
            priority=4,
        )

        assert calls == [
            ("remove", "test-pack"),
            (
                "add",
                {
                    "preset_id": "test-pack",
                    "from_url": "https://example.com/replacement.zip",
                    "dev": None,
                    "priority": 4,
                },
            ),
        ]

    def test_add_failure_states_removed_and_prints_retry_command(
        self, project_dir, monkeypatch, capsys
    ):
        commands = self._manager(monkeypatch, project_dir)
        monkeypatch.setattr(commands, "preset_remove", lambda _preset_id: None)

        def fail_add(**_kwargs):
            raise typer.Exit(1)

        monkeypatch.setattr(commands, "preset_add", fail_add)

        with pytest.raises(typer.Exit) as exc_info:
            preset_update(
                "test-pack",
                from_url=None,
                dev="/tmp/replacement preset",
                priority=6,
            )

        assert exc_info.value.exit_code == 1
        output = strip_ansi(capsys.readouterr().out)
        assert "previous preset was removed" in output
        retry_args = [
            "specify",
            "preset",
            "add",
            "test-pack",
            "--dev",
            "/tmp/replacement preset",
            "--priority",
            "6",
        ]
        expected = (
            _render_powershell_argv(retry_args)
            if os.name == "nt"
            else shlex.join(retry_args)
        )
        assert expected in output

    def test_retry_command_quotes_powershell_metacharacters(
        self, project_dir, monkeypatch, capsys
    ):
        """Windows retry commands keep PowerShell metacharacters literal."""
        commands = self._manager(monkeypatch, project_dir)
        monkeypatch.setattr(commands, "preset_remove", lambda _preset_id: None)

        def fail_add(**_kwargs):
            raise typer.Exit(1)

        monkeypatch.setattr(commands, "preset_add", fail_add)
        monkeypatch.setattr(os, "name", "nt")

        with pytest.raises(typer.Exit) as exc_info:
            preset_update(
                "test-pack",
                from_url=None,
                dev=r"C:\replacement&$backup's presets",
                priority=6,
            )

        assert exc_info.value.exit_code == 1
        output = strip_ansi(capsys.readouterr().out)
        expected = (
            "& 'specify' 'preset' 'add' 'test-pack' '--dev' "
            "'C:\\replacement&$backup''s presets' '--priority' '6'"
        )
        assert "Retry in PowerShell: " in output
        assert expected in output

    def test_powershell_retry_renderer_preserves_literal_arguments(self):
        """The rendered command survives parsing by a real PowerShell."""
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell is None:
            pytest.skip("PowerShell is not available")

        arguments = [
            "https://example.com/archive.zip?one=1&two=$value",
            r"C:\owner's presets",
        ]
        rendered = _render_powershell_argv(
            [
                sys.executable,
                "-c",
                "import json,sys; print(json.dumps(sys.argv[1:]))",
                *arguments,
            ]
        )
        result = subprocess.run(
            [powershell, "-NoProfile", "-Command", rendered],
            check=True,
            capture_output=True,
            text=True,
        )

        assert json.loads(result.stdout) == arguments

    def test_invalid_priority_rejected_before_removal(
        self, project_dir, monkeypatch, capsys
    ):
        """--priority 0 must fail without removing the installed preset."""
        commands = self._manager(monkeypatch, project_dir)
        calls = []
        monkeypatch.setattr(
            commands, "preset_remove", lambda preset_id: calls.append("remove")
        )
        monkeypatch.setattr(
            commands, "preset_add", lambda **_kwargs: calls.append("add")
        )

        with pytest.raises(typer.Exit) as exc_info:
            preset_update("test-pack", from_url=None, dev=None, priority=0)

        assert exc_info.value.exit_code == 1
        assert calls == []
        output = strip_ansi(capsys.readouterr().out)
        assert "Priority must be a positive integer" in output
        assert "previous preset was removed" not in output
