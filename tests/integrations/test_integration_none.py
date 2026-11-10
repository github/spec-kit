"""Artifact-free integration and its normal management lifecycle."""

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


def test_none_setup_produces_no_files(tmp_path):
    integration = get_integration("none")
    assert integration is not None
    assert integration.multi_install_safe
    assert integration.registrar_config is None
    assert integration.list_command_templates() == []
    manifest = IntegrationManifest("none", tmp_path)
    before = list(tmp_path.iterdir())
    assert integration.setup(tmp_path, manifest) == []
    assert manifest.files == {}
    assert list(tmp_path.iterdir()) == before


@pytest.mark.parametrize("integration_args", [[], ["--integration", "none"]])
def test_none_lifecycle(tmp_path, monkeypatch, integration_args):
    runner = CliRunner()
    monkeypatch.setenv("SPECKIT_INTEGRATION_DEFAULT", "none")
    project = tmp_path / "project"

    def run(*arguments):
        result = runner.invoke(app, list(arguments))
        assert result.exit_code == 0, result.output

    def state():
        return json.loads((project / ".specify/integration.json").read_text())

    run("init", str(project), "--non-interactive", *integration_args)
    monkeypatch.chdir(project)
    assert state()["integration"] == "none"
    assert state()["installed_integrations"] == ["none"]
    options = json.loads((project / ".specify/init-options.json").read_text())
    assert options["ai"] == options["integration"] == "none"
    assert IntegrationManifest.load("none", project).files == {}
    assert not (project / ".github").exists()
    user_file = project / "AGENTS.md"
    user_file.write_text("User-owned instructions\n")
    run("integration", "install", "copilot", "--force")
    assert state()["integration"] == "none"
    run("integration", "use", "copilot")
    run("integration", "uninstall", "copilot")
    assert state()["integration"] == "none"
    run("integration", "upgrade", "none")
    run("integration", "uninstall", "none")
    assert not (project / ".specify/integration.json").exists()
    assert not (project / ".specify/integrations/none.manifest.json").exists()
    assert (project / ".specify/templates/spec-template.md").is_file()
    run("integration", "install", "none")
    run("integration", "switch", "copilot")
    assert state()["installed_integrations"] == ["copilot"]
    run("integration", "switch", "none")
    assert state()["installed_integrations"] == ["none"]
    assert IntegrationManifest.load("none", project).files == {}
    assert not (project / ".github").exists()
    assert user_file.read_text() == "User-owned instructions\n"
    result = runner.invoke(app, [
        "integration", "upgrade", "none", "--integration-options=--skills",
    ])
    assert result.exit_code == 1, result.output
    assert "Unknown integration option" in result.output
    assert IntegrationManifest.load("none", project).files == {}


@pytest.mark.parametrize("force", [False, True])
def test_none_teardown_preserves_unowned_dispatcher(tmp_path, force):
    integration = get_integration("none")
    manifest = IntegrationManifest("none", tmp_path)
    manifest.save()
    dispatcher = tmp_path / ".specify/events.py"
    dispatcher.write_text("# User-owned dispatcher\n")

    assert integration.teardown(tmp_path, manifest, force=force) == ([], [])
    assert dispatcher.read_text() == "# User-owned dispatcher\n"
    assert not (tmp_path / ".specify/integrations/none.manifest.json").exists()


def test_none_coexists_with_a_safe_agent_without_force(tmp_path, monkeypatch):
    runner = CliRunner()
    project = tmp_path / "project"
    result = runner.invoke(app, [
        "init", str(project), "--integration", "none", "--non-interactive",
    ])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(project)
    result = runner.invoke(app, ["integration", "install", "kiro-cli"])
    assert result.exit_code == 0, result.output
    state = json.loads((project / ".specify/integration.json").read_text())
    assert state["integration"] == "none"
    assert state["installed_integrations"] == ["none", "kiro-cli"]
    result = runner.invoke(app, ["integration", "status", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "ok"
    result = runner.invoke(app, ["integration", "install", "copilot"])
    assert result.exit_code == 1, result.output
    assert "multi-install safe" in result.output
