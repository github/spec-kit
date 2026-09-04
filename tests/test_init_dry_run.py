"""CLI contract tests for ``specify init --dry-run``."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli._assets import _locate_bundled_extension, _locate_bundled_preset
from specify_cli.commands.init import (
    _is_within_root,
    _normalize_fs_path,
    _preview_child_failure_message,
    _preview_content_ownership,
    _preview_seed_paths,
    _seed_preview_home,
    _snapshot_files,
    _snapshot_tree_entries,
    _stage_project_copy,
    _strip_windows_extended_prefix,
    _windows_path_is_junction,
)

_PROVENANCE_CATEGORIES = {"core", "integration", "preset", "workflow", "extension"}


def _action_for(payload: dict, path: str) -> dict:
    return next(action for action in payload["actions"] if action["path"] == path)


def _assert_same_path(left: Path | str, right: Path | str) -> None:
    left_path = Path(left)
    right_path = Path(right)
    if left_path.exists() and right_path.exists():
        assert os.path.samefile(left_path, right_path)
        return
    assert _normalize_fs_path(left_path) == _normalize_fs_path(right_path)


def test_seed_preview_home_copies_auth_config(tmp_path: Path) -> None:
    real_home = tmp_path / "real-home"
    auth_config = real_home / ".specify" / "auth.json"
    auth_config.parent.mkdir(parents=True)
    auth_config.write_text('{"providers": []}\n', encoding="utf-8")
    auth_config.chmod(0o600)
    staged_home = tmp_path / "staged-home"
    staged_home.mkdir()

    _seed_preview_home(staged_home, real_home)

    staged_auth = staged_home / ".specify" / "auth.json"
    assert staged_auth.read_text(encoding="utf-8") == '{"providers": []}\n'
    assert staged_auth.stat().st_mode & 0o777 == auth_config.stat().st_mode & 0o777


def test_seed_preview_home_copies_symlinked_read_only_config(tmp_path: Path) -> None:
    real_home = tmp_path / "real-home"
    external_auth = tmp_path / "external-auth.json"
    external_auth.write_text('{"providers": []}\n', encoding="utf-8")
    auth_config = real_home / ".specify" / "auth.json"
    auth_config.parent.mkdir(parents=True)
    try:
        auth_config.symlink_to(external_auth)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")
    staged_home = tmp_path / "staged-home"
    staged_home.mkdir()

    _seed_preview_home(staged_home, real_home)

    staged_auth = staged_home / ".specify" / "auth.json"
    assert staged_auth.read_text(encoding="utf-8") == '{"providers": []}\n'
    assert not staged_auth.is_symlink()


def test_preview_seed_paths_include_cross_integration_event_targets() -> None:
    paths = _preview_seed_paths("copilot", None, "sh")

    assert Path("opencode.json") in paths
    assert Path(".opencode/plugin/speckit-events.ts") in paths


def test_preview_seed_paths_include_both_bob_layouts() -> None:
    paths = _preview_seed_paths("bob", None, "sh")

    assert Path(".bob/commands") in paths
    assert Path(".bob/skills") in paths


def test_dry_run_preserves_bob_skills_mode_when_both_layouts_exist(
    tmp_path: Path,
) -> None:
    target = tmp_path / "bob-layout-preview"
    legacy_command = target / ".bob" / "commands" / "speckit.plan.md"
    legacy_command.parent.mkdir(parents=True)
    legacy_command.write_text("# stale command\n", encoding="utf-8")
    managed_skill = target / ".bob" / "skills" / "speckit-plan" / "SKILL.md"
    managed_skill.parent.mkdir(parents=True)
    managed_skill.write_text("# managed skill\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--force",
            "--dry-run",
            "--json",
            "--integration",
            "bob",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    action_paths = {action["path"] for action in json.loads(result.output)["actions"]}
    assert ".bob/skills/speckit-specify/SKILL.md" in action_paths
    assert ".bob/commands/speckit.specify.md" not in action_paths


def test_public_staging_environment_cannot_bypass_directory_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "existing-project"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep\n", encoding="utf-8")
    monkeypatch.setenv("SPECIFY_INIT_PLAN_PATH", str(tmp_path / "forged-plan.jsonl"))
    monkeypatch.setenv("SPECIFY_INIT_STAGING_CONFIRMATION", "1")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--non-interactive",
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    assert "Directory already exists" in result.output
    assert sentinel.read_text(encoding="utf-8") == "keep\n"
    assert not (target / ".specify").exists()


def test_dry_run_child_ignores_pythonpath_sitecustomize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caller = tmp_path / "untrusted-caller"
    caller.mkdir()
    marker = tmp_path / "sitecustomize-executed"
    (caller / "sitecustomize.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(caller)
    monkeypatch.setenv("PYTHONPATH", str(caller))

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(tmp_path / "isolated-preview"),
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
    json.loads(result.output)
    assert not marker.exists()


def test_dry_run_child_does_not_import_shadow_package_from_caller_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caller = tmp_path / "untrusted-caller"
    shadow_package = caller / "specify_cli"
    shadow_package.mkdir(parents=True)
    marker = tmp_path / "shadow-package-executed"
    (shadow_package / "__init__.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(caller)

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(tmp_path / "isolated-shadow-preview"),
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
    json.loads(result.output)
    assert not marker.exists()


@pytest.mark.parametrize(
    "content",
    [
        "source: extension:anything\n",
        "<!-- preset:anything -->\n",
    ],
)
def test_preview_content_ownership_rejects_unregistered_typed_markers(
    content: str,
) -> None:
    assert _preview_content_ownership(content, {"git": {"extension"}}) is None


def test_preview_content_ownership_rejects_typed_marker_with_wrong_category() -> None:
    assert (
        _preview_content_ownership(
            "source: extension:self-test\n", {"self-test": {"preset"}}
        )
        is None
    )


def test_preview_child_failure_message_ignores_rich_panel_line_wrapping() -> None:
    result = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout=(
            "│ Initialization failed: Integration destination │\n"
            "│ /tmp/quarantine/.kilo/commands escapes project │\n"
            "│ root /tmp/project │\n"
        ),
        stderr="",
    )

    assert "escapes project root" in _preview_child_failure_message(result)


def test_snapshot_tree_entries_detects_empty_directory_creation(
    tmp_path: Path,
) -> None:
    before = _snapshot_tree_entries(tmp_path)
    (tmp_path / "created-empty-directory").mkdir()

    assert _snapshot_tree_entries(tmp_path) != before


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (r"\\?\C:\Users\runner\proj", r"C:\Users\runner\proj"),
        ("//?/C:/Users/runner/proj", "C:/Users/runner/proj"),
        (r"\\?\UNC\server\share\dir", r"\\server\share\dir"),
        ("//?/UNC/server/share/dir", "//server/share/dir"),
        ("/tmp/proj", "/tmp/proj"),
        (r"C:\Users\runner\proj", r"C:\Users\runner\proj"),
    ],
)
def test_strip_windows_extended_prefix(raw: str, expected: str) -> None:
    assert _strip_windows_extended_prefix(raw) == expected


def test_is_within_root_for_nested_real_paths(tmp_path: Path) -> None:
    nested = tmp_path / "store"
    nested.mkdir()
    assert _is_within_root(nested, tmp_path)
    assert _is_within_root(tmp_path, tmp_path)
    assert not _is_within_root(tmp_path.parent, tmp_path)


def test_is_within_root_does_not_match_prefix_sibling(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    sibling = tmp_path / "proj-evil"
    project.mkdir()
    sibling.mkdir()
    assert not _is_within_root(sibling, project)


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
    manifest_action = _action_for(
        payload, ".specify/integrations/copilot.manifest.json"
    )
    assert manifest_action["provenance"] == "integration"
    assert manifest_action["source_id"] == "copilot"
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
    shared_template = target / ".specify" / "templates" / "plan-template.md"
    shared_template.parent.mkdir(parents=True)
    shared_template.write_text("user-owned content\n", encoding="utf-8")

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
    assert {(action["action"], action["path"]) for action in payload["actions"]} >= {
        ("overwrite", ".specify/templates/plan-template.md")
    }
    assert shared_template.read_text(encoding="utf-8") == "user-owned content\n"


def test_non_forced_here_dry_run_matches_confirmed_preserve_behavior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "nonempty-project"
    shared_template = target / ".specify" / "templates" / "plan-template.md"
    shared_template.parent.mkdir(parents=True)
    shared_template.write_text("user-owned content\n", encoding="utf-8")
    existing = target / "keep.txt"
    existing.write_text("keep\n", encoding="utf-8")
    monkeypatch.chdir(target)

    result = CliRunner().invoke(
        app,
        [
            "init",
            "--here",
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
    assert ("preserve", ".specify/templates/plan-template.md") in actions
    assert ("create", ".github/skills/speckit-specify/SKILL.md") in actions
    assert all(action["action"] != "overwrite" for action in payload["actions"])
    assert all(action["path"] != "keep.txt" for action in payload["actions"])
    assert shared_template.read_text(encoding="utf-8") == "user-owned content\n"
    assert existing.read_text(encoding="utf-8") == "keep\n"

    actual = CliRunner().invoke(
        app,
        [
            "init",
            "--here",
            "--integration",
            "copilot",
            "--script",
            "sh",
        ],
        input="y\n",
        catch_exceptions=False,
    )

    assert actual.exit_code == 0, actual.output
    assert shared_template.read_text(encoding="utf-8") == "user-owned content\n"


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


def test_dry_run_preserves_preset_constitution_provenance_on_reinit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "preset-constitution-preview"
    arguments = [
        "init",
        str(target),
        "--force",
        "--integration",
        "copilot",
        "--script",
        "sh",
        "--ignore-agent-tools",
        "--preset",
        "self-test",
    ]
    created = CliRunner().invoke(app, arguments, catch_exceptions=False)
    assert created.exit_code == 0, created.output

    preview = CliRunner().invoke(
        app, [*arguments, "--dry-run", "--json"], catch_exceptions=False
    )

    assert preview.exit_code == 0, preview.output
    constitution_action = _action_for(
        json.loads(preview.output), ".specify/memory/constitution.md"
    )
    assert constitution_action["action"] == "skip"
    assert constitution_action["provenance"] == "preset"
    assert constitution_action["source_id"] == "self-test"


@pytest.mark.parametrize(
    ("arguments", "error_fragment"),
    [
        (["--integration", "copilot", "--script", "sh"], "Must specify"),
        (["project", "--integration", "unknown-agent"], "Unknown integration"),
        (
            ["project", "--integration", "copilot", "--script", "invalid"],
            "Invalid script type",
        ),
        (
            ["project", "--integration", "generic", "--script", "sh"],
            "requires --integration-options",
        ),
    ],
)
def test_dry_run_json_validation_errors_use_single_json_envelope(
    arguments: list[str], error_fragment: str
) -> None:
    result = CliRunner().invoke(
        app,
        ["init", *arguments, "--dry-run", "--json", "--ignore-agent-tools"],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert error_fragment in payload["error"]
    assert payload["actions"] == []


def test_dry_run_json_missing_agent_cli_uses_single_json_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("specify_cli.commands.init.check_tool", lambda _name: False)

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(tmp_path / "missing-cli-preview"),
            "--dry-run",
            "--json",
            "--integration",
            "kimi",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert "kimi not found" in payload["error"]
    assert payload["actions"] == []


def test_dry_run_json_file_target_uses_single_json_envelope(tmp_path: Path) -> None:
    target = tmp_path / "not-a-directory"
    target.write_text("file\n", encoding="utf-8")

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

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert "exists but is not a directory" in payload["error"]
    assert payload["actions"] == []


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
        "reason": "URL extensions are not fetched during dry-run",
    }
    assert not target.exists()


def test_dry_run_human_preview_escapes_untrusted_action_paths(tmp_path: Path) -> None:
    target = tmp_path / "markup-safe-preview"
    extension_url = "https://example.com/extensions/[/].zip"

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
            "--extension",
            extension_url,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert extension_url in result.output
    assert not target.exists()


def test_dry_run_reports_optional_extension_failure(tmp_path: Path) -> None:
    target = tmp_path / "failed-extension-preview"
    extension = "nonexistent-xyz-ext"

    json_result = CliRunner().invoke(
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
            extension,
        ],
        catch_exceptions=False,
    )

    assert json_result.exit_code == 0, json_result.output
    payload = json.loads(json_result.output)
    assert payload["failures"] == [
        {
            "component": "extension",
            "source_id": extension,
            "error": f"Extension '{extension}' not found in bundled extensions or catalog",
        }
    ]

    human_result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--dry-run",
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--extension",
            extension,
        ],
        catch_exceptions=False,
    )

    assert human_result.exit_code == 0, human_result.output
    normalized = " ".join(human_result.output.split())
    assert f"failed extension:{extension}" in normalized
    assert (
        f"Extension '{extension}' not found in bundled extensions or catalog"
        in normalized
    )
    assert not target.exists()


def test_dry_run_reports_optional_preset_failure(tmp_path: Path) -> None:
    target = tmp_path / "failed-preset-preview"
    preset = "nonexistent-xyz-preset"

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
            preset,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["failures"] == [
        {
            "component": "preset",
            "source_id": preset,
            "error": f"Preset '{preset}' not found in catalog",
        }
    ]
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


def test_dry_run_rejects_symlinked_hermes_home_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_home = tmp_path / "real-home"
    external_skill = tmp_path / "external-skill.md"
    external_skill.write_text("external content\n", encoding="utf-8")
    skill_file = real_home / ".hermes" / "skills" / "speckit-plan" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    try:
        skill_file.symlink_to(external_skill)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("USERPROFILE", str(real_home))
    target = tmp_path / "hermes-home-link-preview"

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

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert "symlinked path component" in payload["error"]
    assert external_skill.read_text(encoding="utf-8") == "external content\n"
    assert skill_file.is_symlink()
    assert not target.exists()


@pytest.mark.parametrize("linked_component", ["hermes", "skills"])
def test_dry_run_reports_json_for_symlinked_hermes_home_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    linked_component: str,
) -> None:
    real_home = tmp_path / "real-home"
    external = tmp_path / "external-home-target"
    external.mkdir()
    if linked_component == "hermes":
        real_home.mkdir()
        link = real_home / ".hermes"
    else:
        (real_home / ".hermes").mkdir(parents=True)
        link = real_home / ".hermes" / "skills"
    try:
        link.symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("USERPROFILE", str(real_home))

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(tmp_path / f"hermes-{linked_component}-link-preview"),
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

    assert result.exit_code == 1, result.output
    assert "symlinked path component" in json.loads(result.output)["error"]
    assert list(external.iterdir()) == []


def test_dry_run_reports_preserve_for_unchanged_hermes_home_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_home = tmp_path / "real-home"
    real_home.mkdir()
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("USERPROFILE", str(real_home))
    target = tmp_path / "hermes-reinit-preview"
    arguments = [
        "init",
        str(target),
        "--force",
        "--integration",
        "hermes",
        "--script",
        "sh",
        "--ignore-agent-tools",
    ]
    created = CliRunner().invoke(app, arguments, catch_exceptions=False)
    assert created.exit_code == 0, created.output

    preview = CliRunner().invoke(
        app, [*arguments, "--dry-run", "--json"], catch_exceptions=False
    )

    assert preview.exit_code == 0, preview.output
    action = _action_for(
        json.loads(preview.output), "~/.hermes/skills/speckit-plan/SKILL.md"
    )
    assert action["action"] == "preserve"
    assert action["provenance"] == "integration"
    assert action["source_id"] == "hermes"


def test_dry_run_omits_unmanaged_hermes_home_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_home = tmp_path / "real-home"
    unmanaged = (
        real_home / ".hermes" / "skills" / "speckit-obsolete" / "SKILL.md"
    )
    unmanaged.parent.mkdir(parents=True)
    unmanaged.write_text("user-owned\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("USERPROFILE", str(real_home))

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(tmp_path / "hermes-unmanaged-preview"),
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
    assert all(
        action["path"] != "~/.hermes/skills/speckit-obsolete/SKILL.md"
        for action in json.loads(result.output)["actions"]
    )
    assert unmanaged.read_text(encoding="utf-8") == "user-owned\n"


def test_dry_run_reports_kimi_legacy_removals(tmp_path: Path) -> None:
    target = tmp_path / "kimi-migration-preview"
    legacy_skill = target / ".kimi" / "skills" / "speckit-oldcmd" / "SKILL.md"
    legacy_skill.parent.mkdir(parents=True)
    legacy_skill.write_text("# Legacy\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "init",
            str(target),
            "--force",
            "--dry-run",
            "--json",
            "--integration",
            "kimi",
            "--integration-options=--migrate-legacy",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert (
        _action_for(payload, ".kimi/skills/speckit-oldcmd/SKILL.md")["action"]
        == "remove"
    )
    assert (
        _action_for(payload, ".kimi-code/skills/speckit-oldcmd/SKILL.md")["action"]
        == "create"
    )
    assert legacy_skill.read_text(encoding="utf-8") == "# Legacy\n"


def test_dry_run_does_not_write_through_external_hermes_symlink(
    tmp_path: Path,
) -> None:
    external = tmp_path / "external-hermes"
    external.mkdir()
    target = tmp_path / "hermes-external-link"
    target.mkdir()
    try:
        (target / ".hermes").symlink_to(external.resolve())
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
            "hermes",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    assert "symlinked path component" in json.loads(result.output)["error"]
    assert list(external.iterdir()) == []
    assert (target / ".hermes").is_symlink()
    assert (target / ".hermes").resolve() == external.resolve()


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


@pytest.mark.skipif(os.name == "nt", reason="chmod does not remove read access on Windows")
def test_dry_run_ignores_unreadable_unmanaged_file(tmp_path: Path) -> None:
    target = tmp_path / "unreadable-unmanaged"
    target.mkdir()
    unrelated = target / "unrelated.bin"
    unrelated.write_bytes(b"not used by init")
    unrelated.chmod(0)

    try:
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
                "--ignore-agent-tools",
            ],
            catch_exceptions=False,
        )
    finally:
        unrelated.chmod(0o600)

    assert result.exit_code == 0, result.output
    assert all(
        action["path"] != "unrelated.bin"
        for action in json.loads(result.output)["actions"]
    )


@pytest.mark.skipif(os.name == "nt", reason="chmod does not remove read access on Windows")
def test_dry_run_ignores_unreadable_unmanaged_file_in_selected_root(
    tmp_path: Path,
) -> None:
    target = tmp_path / "unreadable-selected-root"
    unrelated = target / ".github" / "skills" / "private" / "secret.txt"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("not managed by Spec Kit\n", encoding="utf-8")
    unrelated.chmod(0)

    try:
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
                "--ignore-agent-tools",
            ],
            catch_exceptions=False,
        )
    finally:
        unrelated.chmod(0o600)

    assert result.exit_code == 0, result.output
    assert all(
        action["path"] != ".github/skills/private/secret.txt"
        for action in json.loads(result.output)["actions"]
    )
    assert unrelated.read_text(encoding="utf-8") == "not managed by Spec Kit\n"


@pytest.mark.skipif(os.name == "nt", reason="chmod does not remove read access on Windows")
def test_dry_run_reports_unreadable_managed_file_in_selected_root(
    tmp_path: Path,
) -> None:
    target = tmp_path / "unreadable-managed-output"
    managed = target / ".github" / "skills" / "speckit-plan" / "SKILL.md"
    managed.parent.mkdir(parents=True)
    managed.write_text("managed but unreadable\n", encoding="utf-8")
    managed.chmod(0)

    try:
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
                "--ignore-agent-tools",
            ],
            catch_exceptions=False,
        )
    finally:
        managed.chmod(0o600)

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert "failed to stage preview inputs" in payload["error"]
    assert "Permission denied" in payload["error"]
    assert managed.read_text(encoding="utf-8") == "managed but unreadable\n"


def test_dry_run_rejects_selected_directory_junction_before_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "junction-preview"
    selected_root = target / ".github" / "skills"
    selected_root.mkdir(parents=True)
    (selected_root / "keep.txt").write_text("external-like\n", encoding="utf-8")
    real_is_junction = getattr(Path, "is_junction", None)

    def fake_is_junction(path: Path) -> bool:
        return path == selected_root or bool(
            real_is_junction and real_is_junction(path)
        )

    monkeypatch.setattr(Path, "is_junction", fake_is_junction, raising=False)

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
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert "junction" in payload["error"].lower()
    assert (selected_root / "keep.txt").read_text(encoding="utf-8") == "external-like\n"


def test_windows_junction_fallback_uses_reparse_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    monkeypatch.setattr(
        Path,
        "lstat",
        lambda _path: SimpleNamespace(st_reparse_tag=mount_point_tag),
    )

    assert _windows_path_is_junction(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction behavior")
def test_dry_run_rejects_real_windows_junction_before_copy(tmp_path: Path) -> None:
    target = tmp_path / "real-junction-preview"
    external = tmp_path / "external-skills"
    external.mkdir()
    selected_root = target / ".github" / "skills"
    selected_root.parent.mkdir(parents=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(selected_root), str(external)],
        check=True,
        capture_output=True,
        text=True,
    )

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
            "ps",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1, result.output
    assert "junction" in json.loads(result.output)["error"].lower()
    assert list(external.iterdir()) == []


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
    _assert_same_path(remapped, staged / "store")
    assert (staged / "link" / "file.txt").read_text(encoding="utf-8") == "ok\n"
    _assert_same_path(Path(os.readlink(link)), store)


def test_stage_project_copy_limits_copy_to_selected_paths(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    managed = project / ".specify" / "state.json"
    managed.parent.mkdir(parents=True)
    managed.write_text("{}\n", encoding="utf-8")
    unrelated = project / ".git" / "objects" / "large-object"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_bytes(b"unrelated")
    staged = tmp_path / "staged"

    _stage_project_copy(project, staged, {Path(".specify")})

    assert (staged / ".specify" / "state.json").read_text(encoding="utf-8") == "{}\n"
    assert not (staged / ".git").exists()


def test_stage_selected_path_quarantines_symlinked_parent(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside-agent"
    commands = outside / "commands"
    commands.mkdir(parents=True)
    (commands / "keep.md").write_text("external\n", encoding="utf-8")
    try:
        (project / ".agent").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")
    staged = tmp_path / "staged"

    _stage_project_copy(project, staged, {Path(".agent/commands")})

    staged_agent = staged / ".agent"
    assert staged_agent.is_symlink()
    assert not (staged_agent / "commands" / "keep.md").exists()
    assert (commands / "keep.md").read_text(encoding="utf-8") == "external\n"


def test_stage_copy_quarantines_external_absolute_symlinks(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep\n", encoding="utf-8")
    link = project / "escape"
    try:
        link.symlink_to(outside.resolve())
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")

    staged = tmp_path / "staged"
    _stage_project_copy(project, staged)

    staged_escape = staged / "escape"
    assert staged_escape.is_symlink()
    dummy = Path(os.readlink(staged_escape))
    if not dummy.is_absolute():
        dummy = staged_escape.parent / dummy
    assert not _is_within_root(dummy, staged)
    assert not _is_within_root(dummy, outside)
    (staged_escape / "skills").mkdir()
    assert not (outside / "skills").exists()
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "keep\n"
    _assert_same_path(Path(os.readlink(link)), outside)


def test_dry_run_does_not_write_through_external_command_symlink(
    tmp_path: Path,
) -> None:
    target = tmp_path / "escape-preview"
    outside = tmp_path / "outside-commands"
    outside.mkdir()
    kilo_dir = target / ".kilo"
    kilo_dir.mkdir(parents=True)
    try:
        (kilo_dir / "commands").symlink_to(outside.resolve())
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

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert "escapes project root" in payload["error"]
    assert not any(
        action["path"].startswith(".kilo/commands/") for action in payload["actions"]
    )
    assert list(outside.iterdir()) == []
    assert (kilo_dir / "commands").is_symlink()
    assert (kilo_dir / "commands").resolve() == outside.resolve()


def test_snapshot_fingerprint_includes_permission_bits(tmp_path: Path) -> None:
    script = tmp_path / "script.sh"
    script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    script.chmod(0o644)
    mode_before = script.stat().st_mode & 0o777
    before = _snapshot_files(tmp_path)
    script.chmod(0o755)
    mode_after = script.stat().st_mode & 0o777
    after = _snapshot_files(tmp_path)
    if mode_before == mode_after:
        pytest.skip("filesystem does not distinguish permission bits")
    assert before != after


@pytest.mark.skipif(os.name == "nt", reason="ensure_executable_scripts is a no-op on Windows")
def test_dry_run_reports_overwrite_when_shebang_script_lacks_execute_bit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "chmod-preview"
    arguments = [
        "init",
        str(target),
        "--force",
        "--integration",
        "copilot",
        "--script",
        "sh",
        "--ignore-agent-tools",
    ]
    created = CliRunner().invoke(app, arguments, catch_exceptions=False)
    assert created.exit_code == 0, created.output
    scripts = [
        path
        for path in (target / ".specify" / "scripts").rglob("*.sh")
        if path.is_file() and path.read_bytes().startswith(b"#!")
    ]
    assert scripts
    script = scripts[0]
    script.chmod(script.stat().st_mode & ~0o111)
    assert not (script.stat().st_mode & 0o111)

    preview = CliRunner().invoke(
        app, [*arguments, "--dry-run", "--json"], catch_exceptions=False
    )
    assert preview.exit_code == 0, preview.output
    relative = script.relative_to(target).as_posix()
    action = _action_for(json.loads(preview.output), relative)
    assert action["action"] == "overwrite"
    assert not (script.stat().st_mode & 0o111)


def test_dry_run_resolves_home_relative_local_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundled = _locate_bundled_extension("git")
    assert bundled is not None
    home = tmp_path / "home"
    extension = home / "exts" / "git"
    shutil.copytree(bundled, extension)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    target = tmp_path / "tilde-extension-preview"
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
            "~/exts/git",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    extension_action = _action_for(
        payload, ".specify/extensions/git/extension.yml"
    )
    assert extension_action["provenance"] == "extension"
    assert extension_action["source_id"] == "git"
    assert not target.exists()


def test_here_dry_run_resolves_bare_relative_local_preset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundled = _locate_bundled_preset("self-test")
    assert bundled is not None
    target = tmp_path / "bare-relative-preset-preview"
    target.mkdir()
    shutil.copytree(bundled, target / "local-preset")
    monkeypatch.chdir(target)

    result = CliRunner().invoke(
        app,
        [
            "init",
            "--here",
            "--dry-run",
            "--json",
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--preset",
            "local-preset",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["failures"] == []
    preset_action = _action_for(payload, ".github/skills/speckit-specify/SKILL.md")
    assert preset_action["provenance"] == "preset"
    assert not (target / ".specify").exists()
