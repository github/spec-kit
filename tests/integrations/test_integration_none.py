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
    assert integration.registrar_config is None
    before = list(tmp_path.iterdir())
    manifest = IntegrationManifest("none", tmp_path)
    assert integration.setup(tmp_path, manifest) == []
    assert manifest.files == {}
    assert list(tmp_path.iterdir()) == before


@pytest.mark.parametrize("script_type", ["sh", "ps", "py"])
def test_none_init_uses_standard_project_metadata(tmp_path, script_type):
    project = tmp_path / "project"
    result = CliRunner().invoke(app, [
        "init", str(project), "--integration", "none", "--script", script_type,
        "--non-interactive",
    ])
    assert result.exit_code == 0, result.output
    state = json.loads((project / ".specify/integration.json").read_text())
    assert state["integration"] == "none"
    assert state["installed_integrations"] == ["none"]
    options = json.loads((project / ".specify/init-options.json").read_text())
    assert options["ai"] == options["integration"] == "none"
    assert options["script"] == script_type
    assert IntegrationManifest.load("none", project).files == {}
    assert (project / ".specify/templates/spec-template.md").is_file()
    assert not (project / ".github").exists()


def test_none_can_be_the_configured_init_default(tmp_path, monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DEFAULT", "none")
    project = tmp_path / "project"
    result = CliRunner().invoke(app, ["init", str(project), "--non-interactive"])
    assert result.exit_code == 0, result.output
    state = json.loads((project / ".specify/integration.json").read_text())
    assert state["integration"] == "none"
    assert IntegrationManifest.load("none", project).files == {}
    assert not (project / ".github").exists()


def test_none_uses_normal_install_selection_and_uninstall_lifecycle(tmp_path, monkeypatch):
    runner = CliRunner()
    project = tmp_path / "project"
    result = runner.invoke(app, [
        "init", str(project), "--integration", "none", "--non-interactive",
        "--extension", "git",
    ])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(project)

    def run(*arguments):
        result = runner.invoke(app, list(arguments))
        assert result.exit_code == 0, result.output
        return result

    def state():
        return json.loads((project / ".specify/integration.json").read_text())

    assert state()["integration"] == "none"
    assert state()["installed_integrations"] == ["none"]
    assert IntegrationManifest.load("none", project).files == {}
    assert not (project / ".github").exists()
    run("integration", "upgrade", "none")
    run("integration", "install", "copilot", "--force")
    assert state()["integration"] == "none"
    assert state()["installed_integrations"] == ["none", "copilot"]
    assert not (project / ".github/skills/speckit-git-feature/SKILL.md").exists()
    result = runner.invoke(app, ["integration", "install", "claude"])
    assert result.exit_code == 1, result.output
    assert "multi-install safe" in result.output
    assert state()["installed_integrations"] == ["none", "copilot"]
    assert not (project / ".claude").exists()
    run("integration", "use", "copilot")
    assert state()["integration"] == "copilot"
    assert (project / ".github/skills/speckit-git-feature/SKILL.md").is_file()
    run("integration", "use", "none")
    assert state()["integration"] == "none"
    assert IntegrationManifest.load("none", project).files == {}
    run("integration", "uninstall", "copilot")
    assert state()["installed_integrations"] == ["none"]
    assert json.loads(run("integration", "status", "--json").output)["status"] == "ok"
    run("integration", "uninstall", "none")
    assert not (project / ".specify/integration.json").exists()
    assert not (project / ".specify/integrations/none.manifest.json").exists()
    assert (project / ".specify/templates/spec-template.md").is_file()
    run("integration", "install", "none")
    assert state()["integration"] == "none"
    assert IntegrationManifest.load("none", project).files == {}
    run("integration", "switch", "copilot")
    assert state()["installed_integrations"] == ["copilot"]
    assert not (project / ".specify/integrations/none.manifest.json").exists()
    run("integration", "switch", "none")
    assert state()["installed_integrations"] == ["none"]
    assert not (project / ".github/skills/speckit-plan/SKILL.md").exists()
    assert IntegrationManifest.load("none", project).files == {}


def test_uninstalling_default_agent_reselects_installed_none(tmp_path, monkeypatch):
    runner = CliRunner()
    project = tmp_path / "project"
    result = runner.invoke(app, ["init", str(project), "--integration", "none", "--non-interactive"])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(project)
    for arguments in [
        ["integration", "install", "copilot", "--force"],
        ["integration", "use", "copilot"],
        ["integration", "uninstall", "copilot"],
    ]:
        result = runner.invoke(app, arguments)
        assert result.exit_code == 0, result.output
    options = json.loads((project / ".specify/init-options.json").read_text())
    assert options["ai"] == options["integration"] == "none"


def test_none_operations_do_not_adopt_or_modify_agent_files(tmp_path, monkeypatch):
    runner = CliRunner()
    project = tmp_path / "project"
    result = runner.invoke(app, [
        "init", str(project), "--integration", "copilot", "--non-interactive",
        "--extension", "git",
    ])
    assert result.exit_code == 0, result.output
    user_file = project / "AGENTS.md"
    user_file.write_text("User-owned instructions\n")
    before = {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and ".specify" not in path.relative_to(project).parts
    }
    monkeypatch.chdir(project)
    for arguments in [
        ["integration", "install", "none", "--force"],
        ["integration", "upgrade", "none"],
        ["integration", "use", "none"],
        ["integration", "upgrade", "none"],
    ]:
        result = runner.invoke(app, arguments)
        assert result.exit_code == 0, result.output
        assert IntegrationManifest.load("none", project).files == {}
    result = runner.invoke(app, ["integration", "uninstall", "none"])
    assert result.exit_code == 0, result.output
    options = json.loads((project / ".specify/init-options.json").read_text())
    assert options["ai"] == options["integration"] == "copilot"
    assert {
        path.relative_to(project): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and ".specify" not in path.relative_to(project).parts
    } == before
    result = runner.invoke(app, [
        "integration", "install", "none", "--force", "--integration-options=--skills",
    ])
    assert result.exit_code == 1, result.output
    assert "Unknown integration option" in result.output
    assert not (project / ".specify/integrations/none.manifest.json").exists()
