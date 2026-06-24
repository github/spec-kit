"""Tests for integration scaffolding commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integration_scaffold import scaffold_integration
from tests.conftest import strip_ansi


runner = CliRunner()


def _repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "spec-kit"
    (root / "src" / "specify_cli" / "integrations").mkdir(parents=True)
    (root / "tests" / "integrations").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = \"specify-cli\"\n", encoding="utf-8")
    (root / "src" / "specify_cli" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "specify_cli" / "integrations" / "__init__.py").write_text(
        "",
        encoding="utf-8",
    )
    return root


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


@pytest.mark.parametrize(
    ("integration_type", "base_class", "commands_subdir", "args", "extension"),
    [
        ("markdown", "MarkdownIntegration", "commands", "$ARGUMENTS", ".md"),
        ("toml", "TomlIntegration", "commands", "{{args}}", ".toml"),
        ("yaml", "YamlIntegration", "recipes", "{{args}}", ".yaml"),
        ("skills", "SkillsIntegration", "skills", "$ARGUMENTS", "/SKILL.md"),
    ],
)
def test_scaffold_type_templates(
    tmp_path,
    integration_type,
    base_class,
    commands_subdir,
    args,
    extension,
):
    root = _repo_root(tmp_path)

    result = scaffold_integration(root, f"{integration_type}-agent", integration_type)

    content = result.integration_file.read_text(encoding="utf-8")
    assert f"class {result.class_name}({base_class}):" in content
    assert f'"commands_subdir": "{commands_subdir}"' in content
    assert f'"args": "{args}"' in content
    assert f'"extension": "{extension}"' in content
    assert "multi_install_safe = False" in content


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


def test_scaffold_refuses_invalid_key(tmp_path):
    root = _repo_root(tmp_path)

    with pytest.raises(ValueError, match="lowercase kebab-case"):
        scaffold_integration(root, "Bad_Key", "markdown")


def test_scaffold_refuses_unknown_type(tmp_path):
    root = _repo_root(tmp_path)

    with pytest.raises(ValueError, match="Unsupported integration type 'xml'"):
        scaffold_integration(root, "my-agent", " XML ")


def test_scaffold_refuses_overwrite(tmp_path):
    root = _repo_root(tmp_path)
    scaffold_integration(root, "my-agent", "markdown")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        scaffold_integration(root, "my-agent", "markdown")


def test_scaffold_rolls_back_partial_files_on_write_failure(tmp_path, monkeypatch):
    root = _repo_root(tmp_path)
    integration_dir = root / "src" / "specify_cli" / "integrations" / "my_agent"
    integration_file = integration_dir / "__init__.py"
    test_file = root / "tests" / "integrations" / "test_integration_my_agent.py"
    original_write_text = Path.write_text

    def fail_test_write(path, *args, **kwargs):
        if path == test_file:
            raise PermissionError("simulated test file write failure")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_test_write)

    with pytest.raises(PermissionError, match="simulated test file write failure"):
        scaffold_integration(root, "my-agent", "markdown")

    assert not integration_file.exists()
    assert not integration_dir.exists()
    assert not test_file.exists()


def test_scaffold_creates_only_leaf_integration_directory(tmp_path, monkeypatch):
    root = _repo_root(tmp_path)
    original_mkdir = Path.mkdir
    mkdir_calls = []

    def record_mkdir(path, *args, **kwargs):
        mkdir_calls.append((path, args, kwargs))
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", record_mkdir)

    scaffold_integration(root, "my-agent", "markdown")

    assert any(
        path == root / "src" / "specify_cli" / "integrations" / "my_agent"
        for path, _args, _kwargs in mkdir_calls
    )
    assert all(not kwargs.get("parents", False) for _path, _args, kwargs in mkdir_calls)


def test_scaffold_requires_repo_root(tmp_path):
    with pytest.raises(ValueError, match="Spec Kit repository root"):
        scaffold_integration(tmp_path, "my-agent", "markdown")


def test_scaffold_requires_integration_registry_file(tmp_path):
    root = _repo_root(tmp_path)
    (root / "src" / "specify_cli" / "integrations" / "__init__.py").unlink()

    with pytest.raises(ValueError, match="Spec Kit repository root"):
        scaffold_integration(root, "my-agent", "markdown")


def test_scaffold_refuses_symlinked_target_directory(tmp_path):
    root = _repo_root(tmp_path)
    # `outside` carries its own __init__.py so the repo-root heuristic still
    # passes through the symlink, isolating the symlink guard under test.
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "__init__.py").write_text("", encoding="utf-8")
    integrations = root / "src" / "specify_cli" / "integrations"
    (integrations / "__init__.py").unlink()
    integrations.rmdir()
    try:
        integrations.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    with pytest.raises(ValueError, match="symlinked path"):
        scaffold_integration(root, "my-agent", "markdown")

    assert not (outside / "my_agent").exists()


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
