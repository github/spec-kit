"""Tests for the integration scaffolding domain API."""

from pathlib import Path

import pytest

from specify_cli.integration_scaffold import scaffold_integration
from tests.integrations._integration_scaffold_helpers import integration_repo_root as _repo_root

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
