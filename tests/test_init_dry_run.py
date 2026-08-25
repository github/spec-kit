"""CLI contract tests for ``specify init --dry-run``."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.commands.init import _snapshot_files


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
    assert payload["actions"] == []
    assert existing.read_text(encoding="utf-8") == "keep\n"


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
    assert {
        (action["action"], action["path"])
        for action in payload["actions"]
    } >= {("unresolved", extension_url)}
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
    assert any(action["provenance"] == "extension" for action in payload["actions"])
    assert not target.exists()
