"""Public CLI contracts for project-local Spec Kit uninstall."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()

PRESERVATION_FLAGS = [
    [],
    ["--preserve-constitution"],
    ["--preserve-specs"],
    ["--preserve-constitution", "--preserve-specs"],
    ["--preserve-all"],
    ["--preserve-all", "--preserve-constitution"],
    ["--preserve-all", "--preserve-specs"],
    ["--preserve-all", "--preserve-constitution", "--preserve-specs"],
]


@pytest.mark.parametrize("flags", PRESERVATION_FLAGS)
@pytest.mark.parametrize("force", [False, True])
def test_preservation_flags_control_artifact_cleanup_and_preview(tmp_path, flags, force):
    constitution = tmp_path / ".specify/memory/constitution.md"
    constitution.parent.mkdir(parents=True)
    constitution.write_bytes(b"# Principles\r\n")
    config = tmp_path / ".specify/config"
    config.write_bytes(b"configuration")
    spec = tmp_path / "specs/001-feature/spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_bytes(b"# Specification\r\n")
    source = tmp_path / "app.py"
    source.write_bytes(b"source")
    original = {
        path: path.read_bytes() for path in (constitution, config, spec, source)
    }
    keep_constitution = "--preserve-all" in flags or "--preserve-constitution" in flags
    keep_specs = "--preserve-all" in flags or "--preserve-specs" in flags
    args = ["destroy", "--project", str(tmp_path), "--json", *flags, *(["--force"] if force else [])]
    preview = runner.invoke(app, [*args, "--dry-run"])
    assert preview.exit_code == 0, preview.output
    assert preview.stderr == ""
    plan = json.loads(preview.stdout)
    assert (".specify/memory/constitution.md" in plan["removed"]) is not keep_constitution
    assert ("specs/001-feature/spec.md" in plan["removed"]) is not keep_specs
    assert all(path.read_bytes() == content for path, content in original.items())
    result = runner.invoke(app, [*args, "--yes"])
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    expected = set()
    if keep_constitution:
        expected.add(".specify/memory/constitution.md")
        assert constitution.read_bytes() == original[constitution]
    else:
        assert not (tmp_path / ".specify").exists()
    if keep_specs:
        expected.add("specs")
        assert spec.read_bytes() == original[spec]
    else:
        assert not (tmp_path / "specs").exists()
    assert set(json.loads(result.stdout)["preserved"]) == expected
    assert source.read_bytes() == original[source]
    assert not config.exists()
    repeated = runner.invoke(app, [*args, "--yes"])
    assert repeated.exit_code == 0, repeated.output
    assert json.loads(repeated.stdout)["removed"] == []


@pytest.mark.parametrize("flags", PRESERVATION_FLAGS)
def test_preservation_flags_never_supply_destructive_consent(tmp_path, monkeypatch, flags):
    config = tmp_path / ".specify/config"
    config.parent.mkdir()
    config.write_bytes(b"configuration")
    specs = tmp_path / "specs/feature/spec.md"
    specs.parent.mkdir(parents=True)
    specs.write_bytes(b"specification")
    monkeypatch.setattr("specify_cli.command_destroy._stdin_is_interactive", lambda: False)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path), "--force", "--json", *flags])
    assert result.exit_code == 1, result.output
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "confirmation_required"
    assert config.read_bytes() == b"configuration"
    assert specs.read_bytes() == b"specification"


def test_interactive_default_warns_about_specs_and_cancellation_preserves_them(tmp_path, monkeypatch):
    (tmp_path / ".specify").mkdir()
    specs = tmp_path / "specs/empty"
    specs.mkdir(parents=True)
    prompts = []
    monkeypatch.setattr("specify_cli.command_destroy._stdin_is_interactive", lambda: True)

    def cancel(message, **kwargs):
        prompts.append(message)
        return False

    monkeypatch.setattr("typer.confirm", cancel)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert prompts and "specs/" in prompts[0]
    assert "specs/" in result.stdout
    assert specs.exists()
    assert (tmp_path / ".specify").exists()


def test_destroy_removes_configuration_and_preserves_constitution(tmp_path):
    memory = tmp_path / ".specify/memory"
    memory.mkdir(parents=True)
    constitution = memory / "constitution.md"
    constitution.write_bytes(b"# Project principles\r\n")
    config = tmp_path / ".specify/custom.txt"
    config.write_text("disposable", encoding="utf-8")

    result = runner.invoke(app, [
        "destroy", "--project", str(tmp_path), "--yes", "--json", "--preserve-constitution",
    ])

    assert result.exit_code == 0, result.output
    assert not config.exists()
    assert constitution.read_bytes() == b"# Project principles\r\n"
    assert json.loads(result.stdout)["preserved"] == [".specify/memory/constitution.md"]
    assert result.stderr == ""


@pytest.mark.parametrize("arguments", [[], ["--force"], ["--json"], ["--json", "--force"]])
def test_unattended_invocations_require_yes(tmp_path, monkeypatch, arguments):
    config = tmp_path / ".specify/config"
    config.parent.mkdir()
    config.write_bytes(b"configuration")
    monkeypatch.setattr("specify_cli.command_destroy._stdin_is_interactive", lambda: False)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path), *arguments])
    assert result.exit_code == 1
    assert config.read_bytes() == b"configuration"
    if "--json" in arguments:
        assert result.stdout == ""
        assert json.loads(result.stderr)["error"]["code"] == "confirmation_required"
    else:
        assert "--yes" in result.output


def test_json_preview_does_not_prompt_or_write(tmp_path, monkeypatch):
    config = tmp_path / ".specify/config"
    config.parent.mkdir()
    config.write_bytes(b"configuration")
    monkeypatch.setattr("typer.confirm", lambda *a, **kw: pytest.fail("prompted"))
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["removed"] == [".specify/config"]
    assert result.stderr == ""
    assert config.exists()


@pytest.mark.parametrize("answer", [True, False])
def test_interactive_confirmation(tmp_path, monkeypatch, answer):
    config = tmp_path / ".specify/config"
    config.parent.mkdir()
    config.write_bytes(b"configuration")
    monkeypatch.setattr("specify_cli.command_destroy._stdin_is_interactive", lambda: True)
    monkeypatch.setattr("typer.confirm", lambda *a, **kw: answer)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert config.exists() is not answer
    assert ("cancelled" in result.output) is not answer


def test_current_directory_and_project_override(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.mkdir()
    (target / ".specify").mkdir()
    (target / ".specify/config").write_text("config")
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(target))
    result = runner.invoke(app, ["destroy", "--yes", "--json"])
    assert result.exit_code == 0, result.output
    assert not (target / ".specify").exists()


def test_json_error_sanitizes_unexpected_failure(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("private detail")

    monkeypatch.setattr("specify_cli.command_destroy.destroy_project", fail)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path), "--yes", "--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "internal_error"
    assert "private detail" not in result.output


def test_mcp_has_explicit_unavailable_disposition():
    from specify_cli.mcp_destroy import DESTROY_TOOL

    assert DESTROY_TOOL.operation_id == "destroy"
    assert DESTROY_TOOL.disposition == "unavailable"
    assert "project-write" in DESTROY_TOOL.capabilities
    assert DESTROY_TOOL.disposition_reason


@pytest.mark.parametrize("arguments", [
    ["--unknown"], ["--project"], ["unexpected-positional"], ["--force=invalid"],
])
def test_json_argument_errors_use_single_envelope(arguments):
    result = runner.invoke(app, ["destroy", "--json", *arguments])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["error"]["code"] == "invalid_arguments"


def test_json_legacy_layout_cleanup_has_no_raw_warnings(tmp_path):
    registry = tmp_path / ".specify/extensions/.registry"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({
        "extensions": {"sample": {
            "registered_commands": {"opencode": ["speckit.sample.test"]},
        }},
    }))
    skill = tmp_path / ".opencode/command/speckit.sample.test.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("generated")
    result = runner.invoke(app, [
        "destroy", "--project", str(tmp_path), "--yes", "--force", "--json",
    ])
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    assert ".opencode/command/speckit.sample.test.md" in json.loads(result.stdout)["removed"]


@pytest.mark.parametrize("answer", [True, False])
def test_directory_only_cleanup_prompts(tmp_path, monkeypatch, answer):
    empty = tmp_path / ".specify/empty"
    empty.mkdir(parents=True)
    prompts = []
    monkeypatch.setattr("specify_cli.command_destroy._stdin_is_interactive", lambda: True)

    def confirm(*args, **kwargs):
        prompts.append(args)
        return answer

    monkeypatch.setattr("typer.confirm", confirm)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert len(prompts) == 1
    assert empty.exists() is not answer


def test_human_errors_show_recovery_paths_and_completed_integrations(tmp_path, monkeypatch):
    from specify_cli._operation_destroy import DestroyError

    def fail(*args, **kwargs):
        raise DestroyError(
            "cleanup_incomplete", "Cleanup needs attention",
            paths=[".custom/commands/retained.md"], removed=[".specify/cache"],
            uninstalled_integrations=["gemini"],
        )

    monkeypatch.setattr("specify_cli.command_destroy.destroy_project", fail)
    result = runner.invoke(app, ["destroy", "--project", str(tmp_path), "--yes"])
    assert result.exit_code == 1
    assert ".custom/commands/retained.md" in result.output
    assert ".specify/cache" in result.output
    assert "gemini" in result.output
