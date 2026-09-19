"""Tests for the ``specify integration scaffold`` command."""

from pathlib import Path  # noqa: F401

from typer.testing import CliRunner

from specify_cli import app
from tests.conftest import strip_ansi
from tests.integrations._integration_scaffold_helpers import integration_repo_root as _repo_root


runner = CliRunner()

def test_integration_scaffold_creates_markdown_files(tmp_path, monkeypatch):
    root = _repo_root(tmp_path)
    monkeypatch.chdir(root)

    result = runner.invoke(app, [
        "integration", "scaffold", "my-agent",
        "--type", "markdown",
    ], catch_exceptions=False)

    output = strip_ansi(result.output)
    integration_file = root / "src" / "specify_cli" / "integrations" / "my_agent" / "__init__.py"
    test_file = root / "tests" / "integrations" / "test_integration_my_agent.py"

    assert result.exit_code == 0
    assert integration_file.exists()
    assert test_file.exists()
    assert "Created integration scaffold: my-agent" in output
    assert "Register MyAgentIntegration" in output

    content = integration_file.read_text(encoding="utf-8")
    assert "class MyAgentIntegration(MarkdownIntegration):" in content
    assert 'key = "my-agent"' in content
    assert '"folder": ".my-agent/"' in content
    assert '"extension": ".md"' in content
    assert "multi_install_safe = False" in content

    test_content = test_file.read_text(encoding="utf-8")
    assert "from specify_cli.integrations.my_agent import MyAgentIntegration" in test_content
    assert 'assert integration.registrar_config["dir"] == ".my-agent/commands"' in test_content
    assert "assert integration.multi_install_safe is False" in test_content

def test_integration_scaffold_rejects_unknown_type_before_scaffolding(tmp_path, monkeypatch):
    root = _repo_root(tmp_path)
    monkeypatch.chdir(root)

    result = runner.invoke(app, [
        "integration", "scaffold", "my-agent",
        "--type", "xml",
    ])

    output = strip_ansi(result.output)
    assert result.exit_code == 2
    assert "Invalid value for '--type'" in output
    assert not (root / "src" / "specify_cli" / "integrations" / "my_agent").exists()

def test_integration_scaffold_reports_filesystem_errors_cleanly(tmp_path, monkeypatch):
    root = _repo_root(tmp_path)
    monkeypatch.chdir(root)

    import specify_cli.integration_scaffold as scaffold_module

    def boom(*args, **kwargs):
        raise PermissionError("Permission denied: read-only checkout")

    monkeypatch.setattr(scaffold_module, "scaffold_integration", boom)

    result = runner.invoke(app, [
        "integration", "scaffold", "my-agent",
        "--type", "markdown",
    ], catch_exceptions=False)

    output = strip_ansi(result.output)
    assert result.exit_code == 1
    assert "Error:" in output
    assert "Permission denied" in output

def test_integration_scaffold_accepts_uppercase_type(tmp_path, monkeypatch):
    root = _repo_root(tmp_path)
    monkeypatch.chdir(root)

    result = runner.invoke(app, [
        "integration", "scaffold", "my-agent",
        "--type", "YAML",
    ], catch_exceptions=False)

    assert result.exit_code == 0, strip_ansi(result.output)
    content = (
        root / "src" / "specify_cli" / "integrations" / "my_agent" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert "class MyAgentIntegration(YamlIntegration):" in content
