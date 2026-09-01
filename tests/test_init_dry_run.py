"""CLI contract tests for ``specify init --dry-run``."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.commands.init import (
    _remap_in_project_symlinks,
    _snapshot_files,
    _stage_project_copy,
)

_PROVENANCE_CATEGORIES = {"core", "integration", "preset", "workflow", "extension"}


def _action_for(payload: dict, path: str) -> dict:
    return next(action for action in payload["actions"] if action["path"] == path)


def test_dry_run_reports_new_project_files_without_creating_target(tmp_path: Path) -> None:
    target = tmp_path / "preview-project"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert "Initialization preview" in result.output
    assert ".github/skills/speckit-plan/SKILL.md" in result.output
    assert not target.exists()


def test_dry_run_json_is_machine_readable_and_has_no_target_writes(tmp_path: Path) -> None:
    target = tmp_path / "json-preview-project"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert {action["path"] for action in payload["actions"]} >= {
        ".github/skills/speckit-plan/SKILL.md"
    }
    plan_action = _action_for(payload, ".github/skills/speckit-plan/SKILL.md")
    assert plan_action["provenance"] == "integration"
    assert plan_action["source_id"] == "copilot"
    assert {
        action["provenance"] for action in payload["actions"]
    } <= _PROVENANCE_CATEGORIES
    assert not target.exists()


def test_dry_run_json_is_pure_json_without_explicit_integration(tmp_path: Path) -> None:
    target = tmp_path / "default-integration-json-preview"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--non-interactive",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert payload["actions"]
    assert "Non-interactive session detected" not in result.output
    assert not target.exists()


def test_forced_dry_run_reports_overwrite_without_changing_existing_file(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing-project"
    command = target / ".github" / "skills" / "speckit-plan" / "SKILL.md"
    command.parent.mkdir(parents=True)
    command.write_text("user-owned content\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--force",
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert {
        (action["action"], action["path"])
        for action in payload["actions"]
    } >= {("overwrite", ".github/skills/speckit-plan/SKILL.md")}
    assert command.read_text(encoding="utf-8") == "user-owned content\n"


def test_non_forced_dry_run_reports_existing_target_conflict(tmp_path: Path) -> None:
    target = tmp_path / "nonempty-project"
    command = target / ".github" / "skills" / "speckit-plan" / "SKILL.md"
    command.parent.mkdir(parents=True)
    command.write_text("user-owned content\n", encoding="utf-8")
    existing = target / "keep.txt"
    existing.write_text("keep\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["conflict"] is True
    actions = {(action["action"], action["path"]) for action in payload["actions"]}
    assert ("conflict", ".github/skills/speckit-plan/SKILL.md") in actions
    assert ("create", ".github/skills/speckit-specify/SKILL.md") in actions
    assert all(action["action"] != "overwrite" for action in payload["actions"])
    assert all(action["path"] != "keep.txt" for action in payload["actions"])
    assert command.read_text(encoding="utf-8") == "user-owned content\n"
    assert existing.read_text(encoding="utf-8") == "keep\n"


def test_non_forced_dry_run_reports_directory_conflict_without_overlapping_files(
    tmp_path: Path,
) -> None:
    target = tmp_path / "unrelated-nonempty-project"
    target.mkdir()
    existing = target / "keep.txt"
    existing.write_text("keep\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["conflict"] is True
    assert payload["actions"]
    assert all(action["action"] == "create" for action in payload["actions"])
    assert {action["path"] for action in payload["actions"]} >= {
        ".github/skills/speckit-plan/SKILL.md"
    }
    assert all(action["path"] != "keep.txt" for action in payload["actions"])
    assert existing.read_text(encoding="utf-8") == "keep\n"


def test_non_forced_dry_run_human_preview_lists_conflicting_artifacts(
    tmp_path: Path,
) -> None:
    target = tmp_path / "nonempty-human-preview"
    command = target / ".github" / "skills" / "speckit-plan" / "SKILL.md"
    command.parent.mkdir(parents=True)
    command.write_text("user-owned content\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert any(line.startswith("conflict") and line.endswith("target directory exists; applying this plan requires --force") for line in lines)
    assert any(
        line.startswith("conflict   .github/skills/speckit-plan/SKILL.md")
        for line in lines
    )
    assert any(
        line.startswith("create     .github/skills/speckit-specify/SKILL.md")
        for line in lines
    )
    assert command.read_text(encoding="utf-8") == "user-owned content\n"


def test_dry_run_reports_skip_for_already_installed_bundled_workflow(
    tmp_path: Path,
) -> None:
    target = tmp_path / "reinit-workflow-preview"
    arguments = [
        "init",
        str(target),
        "--force",
        "--integration",
        "copilot",
        "--script",
        "sh",
        "--ignore-agent-tools",
        "--extension",
        "git",
    ]
    created = CliRunner().invoke(app, arguments, catch_exceptions=False)
    assert created.exit_code == 0, created.output
    workflow = target / ".specify" / "workflows" / "speckit" / "workflow.yml"
    constitution = target / ".specify" / "memory" / "constitution.md"
    extension = target / ".specify" / "extensions" / "git" / "extension.yml"
    assert workflow.is_file()
    assert constitution.is_file()
    assert extension.is_file()
    workflow_before = workflow.read_text(encoding="utf-8")
    constitution_before = constitution.read_text(encoding="utf-8")
    extension_before = extension.read_text(encoding="utf-8")

    preview = CliRunner().invoke(
        app, [*arguments, "--dry-run", "--json"], catch_exceptions=False
    )
    assert preview.exit_code == 0, preview.output
    payload = json.loads(preview.output)
    workflow_action = _action_for(
        payload, ".specify/workflows/speckit/workflow.yml"
    )
    assert workflow_action["action"] == "skip"
    assert workflow_action["provenance"] == "workflow"
    assert workflow_action["source_id"] == "speckit"
    constitution_action = _action_for(
        payload, ".specify/memory/constitution.md"
    )
    assert constitution_action["action"] == "skip"
    assert constitution_action["provenance"] == "core"
    extension_action = _action_for(
        payload, ".specify/extensions/git/extension.yml"
    )
    assert extension_action["action"] == "skip"
    assert extension_action["provenance"] == "extension"
    assert extension_action["source_id"] == "git"
    assert workflow.read_text(encoding="utf-8") == workflow_before
    assert constitution.read_text(encoding="utf-8") == constitution_before
    assert extension.read_text(encoding="utf-8") == extension_before


def test_dry_run_leaves_url_extension_unresolved_without_creating_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "url-extension-preview"
    extension_url = "https://example.com/spec-kit-extension.zip"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--extension",
            extension_url,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    url_action = _action_for(payload, extension_url)
    assert url_action == {
        "action": "unresolved",
        "path": extension_url,
        "provenance": "extension",
        "source_id": extension_url,
    }
    assert not target.exists()


def test_dry_run_changed_paths_match_a_forced_real_initialization(tmp_path: Path) -> None:
    target = tmp_path / "parity-project"
    command = target / ".github" / "skills" / "speckit-plan" / "SKILL.md"
    command.parent.mkdir(parents=True)
    command.write_text("user-owned content\n", encoding="utf-8")
    before = _snapshot_files(target)
    arguments = [
        "init",
        str(target),
        "--force",
        "--integration",
        "copilot",
        "--script",
        "sh",
    ]

    preview = CliRunner().invoke(
        app, [*arguments, "--dry-run", "--json"], catch_exceptions=False
    )
    assert preview.exit_code == 0, preview.output
    predicted = {
        action["path"]
        for action in json.loads(preview.output)["actions"]
        if action["action"] in {"create", "overwrite"}
    }

    actual = CliRunner().invoke(app, arguments, catch_exceptions=False)
    assert actual.exit_code == 0, actual.output
    after = _snapshot_files(target)
    changed = {path for path, digest in after.items() if before.get(path) != digest}

    assert predicted == changed


def test_dry_run_includes_bundled_extension_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "extension-preview-project"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--extension",
            "git",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    extension_action = _action_for(
        payload, ".github/skills/speckit-git-feature/SKILL.md"
    )
    assert extension_action["provenance"] == "extension"
    assert extension_action["source_id"] == "git"
    assert not target.exists()


def test_dry_run_uses_preset_registry_and_skill_marker_for_provenance(
    tmp_path: Path,
) -> None:
    target = tmp_path / "preset-preview-project"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--preset",
            "self-test",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    preset_action = _action_for(payload, ".github/skills/speckit-specify/SKILL.md")
    assert preset_action["provenance"] == "preset"
    assert preset_action["source_id"] == "self-test"
    assert not target.exists()


def test_dry_run_uses_registries_for_command_integration_provenance(
    tmp_path: Path,
) -> None:
    target = tmp_path / "command-provenance-preview"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "gemini",
            "--script",
            "sh",
            "--ignore-agent-tools",
            "--preset",
            "self-test",
            "--extension",
            "git",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    preset_action = _action_for(payload, ".gemini/commands/speckit.specify.toml")
    extension_action = _action_for(payload, ".gemini/commands/speckit.git.feature.toml")
    assert (preset_action["provenance"], preset_action["source_id"]) == (
        "preset",
        "self-test",
    )
    assert (extension_action["provenance"], extension_action["source_id"]) == (
        "extension",
        "git",
    )
    assert not target.exists()


def test_dry_run_registry_owns_markerless_copilot_companion_prompt(
    tmp_path: Path,
) -> None:
    target = tmp_path / "copilot-command-preview"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--integration-options=--commands",
            "--script",
            "sh",
            "--extension",
            "git",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    prompt_action = _action_for(
        payload, ".github/prompts/speckit.git.feature.prompt.md"
    )
    assert (prompt_action["provenance"], prompt_action["source_id"]) == (
        "extension",
        "git",
    )
    assert not target.exists()


def test_dry_run_isolates_and_reports_hermes_home_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_home = tmp_path / "real-home"
    existing_skill = real_home / ".hermes" / "skills" / "speckit-plan" / "SKILL.md"
    existing_skill.parent.mkdir(parents=True)
    existing_skill.write_text("user-owned content\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("USERPROFILE", str(real_home))
    target = tmp_path / "hermes-preview-project"

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--json",
            "--integration",
            "hermes",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert existing_skill.read_text(encoding="utf-8") == "user-owned content\n"
    payload = json.loads(result.output)
    hermes_action = _action_for(payload, "~/.hermes/skills/speckit-plan/SKILL.md")
    assert hermes_action["action"] == "overwrite"
    assert hermes_action["provenance"] == "integration"
    assert hermes_action["source_id"] == "hermes"
    assert not target.exists()


def test_dry_run_remaps_in_project_absolute_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "symlink-preview"
    real_commands = target / "kilo-store" / "commands"
    real_commands.mkdir(parents=True)
    kilo_dir = target / ".kilo"
    kilo_dir.mkdir()
    try:
        (kilo_dir / "commands").symlink_to(real_commands.resolve())
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--force",
            "--dry-run",
            "--json",
            "--integration",
            "kilocode",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert {
        action["path"] for action in payload["actions"]
    } >= {"kilo-store/commands/speckit.plan.md"}
    assert list(real_commands.iterdir()) == []
    assert (kilo_dir / "commands").resolve() == real_commands.resolve()


def test_remap_in_project_absolute_symlinks_points_at_staged_copy(
    tmp_path: Path,
) -> None:
    project = tmp_path / "proj"
    store = project / "store"
    store.mkdir(parents=True)
    (store / "file.txt").write_text("ok\n", encoding="utf-8")
    link = project / "link"
    try:
        link.symlink_to(store.resolve())
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")

    staged = tmp_path / "staged"
    _stage_project_copy(project, staged)

    remapped = Path(os.readlink(staged / "link"))
    assert remapped == (staged / "store").resolve()
    assert (staged / "link" / "file.txt").read_text(encoding="utf-8") == "ok\n"
    assert Path(os.readlink(link)) == store.resolve()


def test_remap_leaves_external_absolute_symlinks(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = project / "escape"
    try:
        link.symlink_to(outside.resolve())
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")

    staged = tmp_path / "staged"
    shutil.copytree(project, staged, symlinks=True)
    _remap_in_project_symlinks(project.resolve(), staged.resolve())

    assert Path(os.readlink(staged / "escape")) == outside.resolve()


def test_dry_run_rejects_external_absolute_command_symlink(tmp_path: Path) -> None:
    target = tmp_path / "escape-preview"
    outside = tmp_path / "outside-commands"
    outside.mkdir()
    kilo_dir = target / ".kilo"
    kilo_dir.mkdir(parents=True)
    try:
        (kilo_dir / "commands").symlink_to(outside.resolve())
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")

    with pytest.raises(RuntimeError, match="staged initialization failed"):
        CliRunner().invoke(
            app,
            [
                "init",
                str(target),
                "--force",
                "--dry-run",
                "--json",
                "--integration",
                "kilocode",
                "--script",
                "sh",
            ],
            catch_exceptions=False,
        )
