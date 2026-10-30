"""Tests for the ``IntegrationBase.preflight_setup()`` hook and its CLI wiring."""

from __future__ import annotations

import hashlib
import os

import pytest

from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.claude import ClaudeIntegration
from specify_cli.integrations.codex import CodexIntegration
from specify_cli.shared_infra import script_variant_dirs
from tests.conftest import strip_ansi
from tests.specify_cli.integrations._helpers import _init_project, _run_in_project


def _snapshot(project):
    """Map every file under *project* to its SHA-256, plus the directory set."""
    files = {}
    dirs = set()
    for root, dirnames, filenames in os.walk(project):
        for name in dirnames:
            dirs.add(os.path.relpath(os.path.join(root, name), project))
        for name in filenames:
            path = os.path.join(root, name)
            with open(path, "rb") as fh:
                files[os.path.relpath(path, project)] = hashlib.sha256(fh.read()).hexdigest()
    return files, dirs


def _refuse(exc):
    def preflight_setup(self, project_root, parsed_options=None, *, script_type=None):
        raise exc

    return preflight_setup


# (command args, integration class whose hook runs, project's initial integration)
_COMMANDS = {
    "install": (["integration", "install", "codex", "--script", "sh", "--force"], CodexIntegration, "claude"),
    "switch": (["integration", "switch", "codex", "--script", "sh"], CodexIntegration, "claude"),
    "upgrade": (["integration", "upgrade", "claude", "--script", "sh", "--force"], ClaudeIntegration, "claude"),
}


def test_default_preflight_accepts(tmp_path):
    assert CodexIntegration().preflight_setup(tmp_path, {}, script_type="sh") is None
    assert IntegrationBase.preflight_setup is CodexIntegration.preflight_setup


@pytest.mark.parametrize("command", sorted(_COMMANDS))
@pytest.mark.parametrize("exc", [ValueError("bad config"), PermissionError("locked")])
def test_refusal_exits_before_any_write(tmp_path, monkeypatch, command, exc):
    args, cls, initial = _COMMANDS[command]
    project = _init_project(tmp_path, initial)
    # Make the shared infrastructure stale so a run past the hook would rewrite it.
    template = next((project / ".specify" / "templates").glob("*.md"))
    template.write_text("stale\n", encoding="utf-8")
    before = _snapshot(project)

    monkeypatch.setattr(cls, "preflight_setup", _refuse(exc))
    result = _run_in_project(project, args)

    assert result.exit_code == 1, result.output
    output = " ".join(strip_ansi(result.output).split())
    assert str(exc) in output
    assert "No files were changed." in output
    assert _snapshot(project) == before


@pytest.mark.parametrize("command", sorted(_COMMANDS))
def test_hook_receives_options_and_script_type(tmp_path, monkeypatch, command):
    args, cls, initial = _COMMANDS[command]
    project = _init_project(tmp_path, initial)
    calls = []

    def preflight_setup(self, project_root, parsed_options=None, *, script_type=None):
        calls.append((self.key, project_root, parsed_options, script_type))

    monkeypatch.setattr(cls, "preflight_setup", preflight_setup)
    result = _run_in_project(project, args)

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    key, root, parsed, script_type = calls[0]
    assert key == cls.key
    assert root.resolve() == project.resolve()
    assert parsed is None or isinstance(parsed, dict)
    assert script_type == "sh"


@pytest.mark.parametrize(
    ("script_type", "expected"),
    [
        ("sh", ("bash",)),
        ("ps", ("powershell",)),
        ("py", ("python", "powershell" if os.name == "nt" else "bash")),
    ],
)
def test_script_variant_dirs(script_type, expected):
    assert script_variant_dirs(script_type) == expected
