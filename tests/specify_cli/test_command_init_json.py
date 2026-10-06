"""JSON output and parity tests for ``specify init``."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest
import typer
from typer.testing import CliRunner, Result

from specify_cli import app


def _invoke(args: list[str], *, cwd: Path) -> Result:
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        return CliRunner().invoke(
            app,
            ["init", *args],
            catch_exceptions=False,
        )
    finally:
        os.chdir(previous)


def _success(result: Result) -> dict[str, Any]:
    assert result.exit_code == 0, result.stderr or result.stdout
    assert result.stderr == ""
    assert result.stdout.endswith("\n")
    assert result.stdout.count("\n") == 1
    assert "\x1b[" not in result.stdout
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    assert "error" not in payload
    return payload


def _failure(result: Result, code: str) -> dict[str, Any]:
    assert result.exit_code == 1, result.stdout or result.stderr
    assert result.stdout == ""
    assert result.stderr.endswith("\n")
    assert result.stderr.count("\n") == 1
    assert "\x1b[" not in result.stderr
    payload = json.loads(result.stderr)
    assert payload["error"]["code"] == code
    assert set(payload["error"]) == {"code", "message", "details"}
    return payload["error"]


def _normalize_value(value: Any, root: Path) -> Any:
    if isinstance(value, dict):
        return {
            key: _normalize_value(item, root)
            for key, item in value.items()
            if key not in {"installed_at", "updated_at", "created_at"}
        }
    if isinstance(value, list):
        return [_normalize_value(item, root) for item in value]
    if isinstance(value, str):
        return value.replace(str(root), "<PROJECT_ROOT>")
    return value


def _project_snapshot(root: Path) -> dict[str, tuple[Any, ...]]:
    snapshot: dict[str, tuple[Any, ...]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            snapshot[relative] = ("symlink", mode, os.readlink(path))
        elif path.is_dir():
            snapshot[relative] = ("directory", mode)
        else:
            content = path.read_bytes()
            try:
                normalized = _normalize_value(
                    json.loads(content.decode("utf-8")),
                    root,
                )
                content = json.dumps(
                    normalized,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            except (UnicodeDecodeError, json.JSONDecodeError):
                try:
                    content = content.decode("utf-8").replace(
                        str(root),
                        "<PROJECT_ROOT>",
                    ).encode("utf-8")
                except UnicodeDecodeError:
                    pass
            snapshot[relative] = ("file", mode, content)
    return snapshot


def test_json_init_new_directory_uses_safe_defaults(tmp_path: Path):
    project = tmp_path / "prøject"

    payload = _success(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["project"] == {
        "name": "prøject",
        "path": str(project.resolve()),
        "operation": "created",
    }
    assert payload["integration"] == {
        "key": "copilot",
        "defaulted": True,
        "status": "installed",
    }
    assert payload["script"] == {
        "type": "ps" if os.name == "nt" else "sh",
        "defaulted": True,
    }
    assert payload["components"]["shared_infrastructure"]["status"] == "installed"
    assert payload["components"]["workflow"]["status"] == "installed"
    assert payload["components"]["constitution"]["status"] == "created"
    assert payload["components"]["preset"] is None
    assert payload["components"]["extensions"] == []
    assert (project / ".specify" / "init-options.json").is_file()


def test_json_init_here_honors_explicit_integration_and_script(tmp_path: Path):
    payload = _success(
        _invoke(
            [
                "--here",
                "--json",
                "--integration",
                "copilot",
                "--script",
                "py",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["project"]["operation"] == "merged"
    assert payload["project"]["path"] == str(tmp_path.resolve())
    assert payload["integration"]["defaulted"] is False
    assert payload["script"] == {"type": "py", "defaulted": False}
    assert all(step["action"] != "change_directory" for step in payload["next_steps"])


def test_json_init_never_uses_prompt_or_rich_ui(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command

    monkeypatch.setattr(init_command, "_stdin_is_interactive", lambda: True)

    def fail_ui(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("JSON mode must not invoke interactive or Rich UI")

    monkeypatch.setattr(init_command, "select_with_arrows", fail_ui)
    monkeypatch.setattr(init_command, "show_banner", fail_ui)
    monkeypatch.setattr(init_command, "Live", fail_ui)
    monkeypatch.setattr(init_command, "Panel", fail_ui)
    monkeypatch.setattr(typer, "confirm", fail_ui)

    payload = _success(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["integration"]["defaulted"] is True
    assert payload["script"]["defaulted"] is True


def test_json_init_force_merges_nonempty_target(tmp_path: Path):
    project = tmp_path / "existing"
    project.mkdir()
    marker = project / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "target_exists",
    )
    payload = _success(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["project"]["operation"] == "merged"
    assert marker.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    ("args", "code"),
    [
        (["--json"], "target_required"),
        (["project", "--here", "--json"], "conflicting_target_options"),
        (
            ["project", "--json", "--integration", "missing"],
            "invalid_integration",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "generic",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "copilot",
                "--integration-options=--skills --commands",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "copilot",
                '--integration-options=--skills "',
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "copilot",
                "--integration-options=--missing",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "copilot",
                "--integration-options=--skills=true",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "generic",
                "--integration-options=--commands-dir",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "generic",
                "--integration-options=--commands-dir ../outside",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "bob",
                "--integration-options=--skills --legacy-commands",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--extension",
                "http://example.com/extension.zip",
                "--trust-extension-urls",
            ],
            "invalid_extension_url",
        ),
        (["project", "--json", "--script", "fish"], "invalid_script_type"),
    ],
)
def test_json_validation_failures_do_not_create_target(
    tmp_path: Path,
    args: list[str],
    code: str,
):
    _failure(_invoke(args, cwd=tmp_path), code)
    assert not (tmp_path / "project").exists()


@pytest.mark.parametrize(
    ("integration", "options", "diagnostic"),
    [
        (
            "copilot",
            '--skills "',
            "Could not parse integration options: No closing quotation.",
        ),
        (
            "copilot",
            "--missing",
            "Unknown integration option '--missing'.",
        ),
        (
            "copilot",
            "--skills=true",
            "Option '--skills' is a flag and does not accept a value.",
        ),
        (
            "generic",
            "--commands-dir",
            "Option '--commands-dir' requires a value.",
        ),
        (
            "copilot",
            "--skills stray",
            "Unexpected integration option value 'stray'.",
        ),
        (
            "copilot",
            "--skills --commands",
            "--skills and --commands are mutually exclusive; pass only one.",
        ),
        (
            "bob",
            "--skills --legacy-commands",
            "--skills and --legacy-commands are mutually exclusive; pass only one.",
        ),
    ],
)
def test_json_integration_option_failures_preserve_parser_diagnostic(
    tmp_path: Path,
    integration: str,
    options: str,
    diagnostic: str,
):
    error = _failure(
        _invoke(
            [
                "project",
                "--json",
                "--integration",
                integration,
                f"--integration-options={options}",
            ],
            cwd=tmp_path,
        ),
        "invalid_integration_options",
    )

    assert diagnostic in error["details"]["reason"]
    assert not (tmp_path / "project").exists()


def test_json_init_reports_missing_required_agent_tool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli._command_init_json as init_json

    monkeypatch.setattr(init_json, "check_tool", lambda _tool: False)

    error = _failure(
        _invoke(
            ["project", "--json", "--integration", "claude"],
            cwd=tmp_path,
        ),
        "missing_agent_tool",
    )

    assert error["details"]["override_flag"] == "--ignore-agent-tools"
    assert not (tmp_path / "project").exists()


def test_json_init_rejects_untrusted_url_before_mutation(tmp_path: Path):
    error = _failure(
        _invoke(
            [
                "project",
                "--json",
                "--extension",
                "https://example.com/extension.zip",
            ],
            cwd=tmp_path,
        ),
        "extension_url_trust_required",
    )

    assert error["details"]["required_flag"] == "--trust-extension-urls"
    assert not (tmp_path / "project").exists()


def test_json_init_exposes_optional_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command
    from specify_cli.presets import PresetManager

    monkeypatch.setattr(
        PresetManager,
        "install_from_directory",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("preset install failed")
        ),
    )
    monkeypatch.setattr(
        init_command,
        "_install_extension_during_init_result",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("extension install failed")
        ),
    )

    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--ignore-agent-tools",
                "--preset",
                "lean",
                "--extension",
                "git",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["preset"]["status"] == "failed"
    assert payload["components"]["extensions"][0]["status"] == "failed"
    assert {warning["code"] for warning in payload["warnings"]} >= {
        "preset_install_failed",
        "extension_install_failed",
    }


def test_json_init_rolls_back_new_target_after_fatal_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli

    monkeypatch.setattr(
        specify_cli,
        "_install_shared_infra_or_exit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            typer.Exit(1)
        ),
    )
    project = tmp_path / "project"

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "initialization_failed",
    )

    assert error["details"]["rollback"]["status"] == "completed"
    assert not project.exists()


def test_json_init_structures_system_exit_and_reports_actual_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli

    monkeypatch.setattr(
        specify_cli,
        "_install_shared_infra_or_exit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(SystemExit(7)),
    )
    project = tmp_path / "project"

    error = _failure(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "initialization_failed",
    )

    assert error["details"]["rollback"] == {
        "status": "completed",
        "path": str(project),
    }
    assert not project.exists()


def test_json_init_preserves_preexisting_target_after_fatal_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli

    project = tmp_path / "project"
    project.mkdir()
    marker = project / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(
        specify_cli,
        "_install_shared_infra_or_exit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            typer.Exit(1)
        ),
    )

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        ),
        "initialization_failed",
    )

    assert "rollback" not in error["details"]
    assert marker.read_text(encoding="utf-8") == "keep"


def test_json_init_sanitizes_unexpected_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from specify_cli.integrations import get_integration

    integration = get_integration("copilot")
    assert integration is not None
    monkeypatch.setattr(
        integration,
        "setup",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("sensitive detail")
        ),
    )

    error = _failure(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "internal_error",
    )

    assert error["details"] == {"exception_type": "RuntimeError"}
    assert "sensitive detail" not in json.dumps(error)
    assert not (tmp_path / "project").exists()


def test_json_init_reports_cleanup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli
    import specify_cli.command_init as init_command

    monkeypatch.setattr(
        specify_cli,
        "_install_shared_infra_or_exit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            typer.Exit(1)
        ),
    )
    monkeypatch.setattr(
        init_command.shutil,
        "rmtree",
        lambda _path: (_ for _ in ()).throw(OSError("cleanup failed")),
    )

    error = _failure(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "rollback_failed",
    )

    assert error["details"]["cleanup_error"]["code"] == "target_cleanup_failed"
    assert (tmp_path / "project").is_dir()


def test_json_init_preserves_target_created_during_claim_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    project = tmp_path / "project"
    marker = project / "keep.txt"
    original_mkdir = Path.mkdir

    def racing_mkdir(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == project and kwargs.get("exist_ok") is False:
            original_mkdir(path, parents=True)
            marker.write_text("keep", encoding="utf-8")
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", racing_mkdir)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "target_exists",
    )

    assert error["details"]["concurrent_creation"] is True
    assert marker.read_text(encoding="utf-8") == "keep"


def test_json_init_does_not_infer_rollback_from_stale_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli._command_init_json as init_json

    project = tmp_path / "project"
    marker = project / "keep.txt"
    original_preflight = init_json._preflight

    def racing_preflight(**kwargs: Any) -> dict[str, Any]:
        context = original_preflight(**kwargs)
        project.mkdir()
        marker.write_text("keep", encoding="utf-8")
        return context

    monkeypatch.setattr(init_json, "_preflight", racing_preflight)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "target_exists",
    )

    assert "rollback" not in error["details"]
    assert marker.read_text(encoding="utf-8") == "keep"


def test_json_init_reports_unverifiable_claim_without_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command

    project = tmp_path / "project"
    monkeypatch.setattr(
        init_command,
        "_directory_identity",
        lambda _path: (_ for _ in ()).throw(OSError("identity failed")),
    )
    monkeypatch.setattr(
        init_command.shutil,
        "rmtree",
        lambda _path: (_ for _ in ()).throw(
            AssertionError("unverified target must not be removed")
        ),
    )

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "rollback_failed",
    )

    assert error["details"]["cleanup_error"]["code"] == (
        "target_identity_unavailable"
    )
    assert project.is_dir()


def test_json_init_preserves_replacement_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from specify_cli.integrations import get_integration

    project = tmp_path / "project"
    claimed = tmp_path / "claimed"
    marker = project / "keep.txt"
    integration = get_integration("copilot")
    assert integration is not None

    def replace_target(*_args: Any, **_kwargs: Any) -> None:
        project.rename(claimed)
        project.mkdir()
        marker.write_text("keep", encoding="utf-8")
        raise RuntimeError("initialization failed")

    monkeypatch.setattr(integration, "setup", replace_target)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "rollback_failed",
    )

    assert error["details"]["cleanup_error"]["code"] == "target_identity_changed"
    assert marker.read_text(encoding="utf-8") == "keep"
    assert claimed.is_dir()


def test_json_rollback_does_not_delete_public_path_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command
    from specify_cli.integrations import get_integration

    project = tmp_path / "project"
    marker = project / "keep.txt"
    integration = get_integration("copilot")
    assert integration is not None
    original_directory_identity = init_command._directory_identity

    def replace_public_path_after_staging(path: Path) -> tuple[int, int]:
        identity = original_directory_identity(path)
        if path.name == "target" and ".specify-rollback-" in path.parent.name:
            project.mkdir()
            marker.write_text("replacement", encoding="utf-8")
        return identity

    monkeypatch.setattr(
        init_command,
        "_directory_identity",
        replace_public_path_after_staging,
    )
    monkeypatch.setattr(
        integration,
        "setup",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("initialization failed")
        ),
    )

    _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "internal_error",
    )

    assert marker.read_text(encoding="utf-8") == "replacement"


@pytest.mark.parametrize(
    "args",
    [
        ["project", "--json", "--unknown-option"],
        ["project", "--json", "--script"],
        ["project", "--json", "--integration"],
    ],
)
def test_json_parser_failures_are_structured(
    tmp_path: Path,
    args: list[str],
):
    _failure(_invoke(args, cwd=tmp_path), "invalid_arguments")
    assert not (tmp_path / "project").exists()


@pytest.mark.parametrize(
    "args",
    [
        ["--ignore-agent-tools"],
        [
            "--integration",
            "copilot",
            "--script",
            "py",
            "--ignore-agent-tools",
        ],
        [
            "--integration",
            "copilot",
            "--preset",
            "lean",
            "--extension",
            "git",
            "--ignore-agent-tools",
        ],
        [
            "--integration",
            "generic",
            "--integration-options=--commands-dir .agent/commands",
        ],
        [
            "--integration",
            "copilot",
            "--integration-options=--commands",
            "--ignore-agent-tools",
        ],
        [
            "--integration",
            "copilot",
            "--integration-options=--skills",
            "--ignore-agent-tools",
        ],
        [
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
    ],
)
def test_json_and_human_init_create_identical_projects(
    tmp_path: Path,
    args: list[str],
):
    human = tmp_path / "human"
    machine = tmp_path / "machine"

    human_result = _invoke(
        [str(human), "--non-interactive", *args],
        cwd=tmp_path,
    )
    assert human_result.exit_code == 0, human_result.output
    _success(
        _invoke(
            [str(machine), "--json", *args],
            cwd=tmp_path,
        )
    )

    assert _project_snapshot(human) == _project_snapshot(machine)


def test_json_and_human_reinitialization_create_identical_projects(
    tmp_path: Path,
):
    human = tmp_path / "human"
    machine = tmp_path / "machine"
    initial_args = [
        "--integration",
        "copilot",
        "--extension",
        "git",
        "--ignore-agent-tools",
    ]
    switch_args = [
        "--force",
        "--integration",
        "copilot",
        "--ignore-agent-tools",
    ]

    assert _invoke(
        [str(human), "--non-interactive", *initial_args],
        cwd=tmp_path,
    ).exit_code == 0
    _success(_invoke([str(machine), "--json", *initial_args], cwd=tmp_path))
    assert _invoke(
        [str(human), "--non-interactive", *switch_args],
        cwd=tmp_path,
    ).exit_code == 0
    _success(_invoke([str(machine), "--json", *switch_args], cwd=tmp_path))

    assert _project_snapshot(human) == _project_snapshot(machine)


@pytest.mark.parametrize(
    "switch_args",
    [
        [
            "--integration",
            "generic",
            "--integration-options=--commands-dir .agent/commands",
        ],
        [
            "--integration",
            "copilot",
            "--integration-options=--commands",
        ],
    ],
)
def test_json_rejects_incompatible_reinitialization_before_mutation(
    tmp_path: Path,
    switch_args: list[str],
):
    project = tmp_path / "project"
    _success(
        _invoke(
            [
                str(project),
                "--json",
                "--integration",
                "copilot",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )
    before = _project_snapshot(project)

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                *switch_args,
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        ),
        "invalid_integration_options",
    )

    assert "integration" in error["details"]
    assert _project_snapshot(project) == before


def test_json_rejects_generic_destination_change_before_mutation(tmp_path: Path):
    project = tmp_path / "project"
    _success(
        _invoke(
            [
                str(project),
                "--json",
                "--integration",
                "generic",
                "--integration-options=--commands-dir .agent/commands",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )
    before = _project_snapshot(project)

    _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--integration",
                "generic",
                "--integration-options=--commands-dir .other/commands",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        ),
        "invalid_integration_options",
    )

    assert _project_snapshot(project) == before


def test_human_rejects_incompatible_reinitialization_before_mutation(
    tmp_path: Path,
):
    project = tmp_path / "project"
    first = _invoke(
        [
            str(project),
            "--non-interactive",
            "--integration",
            "copilot",
            "--ignore-agent-tools",
        ],
        cwd=tmp_path,
    )
    assert first.exit_code == 0, first.output
    before = _project_snapshot(project)

    result = _invoke(
        [
            str(project),
            "--non-interactive",
            "--force",
            "--integration",
            "generic",
            "--integration-options=--commands-dir .agent/commands",
            "--ignore-agent-tools",
        ],
        cwd=tmp_path,
    )

    assert result.exit_code == 1
    assert "integration switch generic" in result.output
    assert _project_snapshot(project) == before


def test_force_reinitialization_persists_state_before_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli
    from specify_cli.integrations import _helpers

    project = tmp_path / "project"
    assert (
        _invoke(
            [
                str(project),
                "--non-interactive",
                "--integration",
                "copilot",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        ).exit_code
        == 0
    )
    stale_options = specify_cli.load_init_options(project)
    stale_options.update(
        {
            "ai": "generic",
            "integration": "generic",
        }
    )
    stale_options.pop("ai_skills", None)
    specify_cli.save_init_options(project, stale_options)

    observed: list[tuple[str, dict[str, Any]]] = []

    def capture_state(project_root: Path, agent_key: str, **_kwargs: Any) -> None:
        observed.append((agent_key, specify_cli.load_init_options(project_root)))

    monkeypatch.setattr(_helpers, "_register_extensions_for_agent", capture_state)
    monkeypatch.setattr(_helpers, "_register_presets_for_agent", capture_state)

    result = _invoke(
        [
            str(project),
            "--non-interactive",
            "--force",
            "--integration",
            "copilot",
            "--ignore-agent-tools",
        ],
        cwd=tmp_path,
    )

    assert result.exit_code == 0, result.output
    assert len(observed) == 2
    for agent_key, options in observed:
        assert agent_key == "copilot"
        assert options["ai"] == "copilot"
        assert options["integration"] == "copilot"
        assert options["ai_skills"] is True


def test_json_empty_selections_use_and_report_defaults(tmp_path: Path):
    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--integration",
                "",
                "--script",
                "",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["integration"]["defaulted"] is True
    assert payload["script"]["defaulted"] is True


def test_json_here_rejects_nonempty_target_without_force(tmp_path: Path):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    _failure(
        _invoke(
            ["--here", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "target_not_empty",
    )

    assert marker.read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / ".specify").exists()


def test_json_rejects_target_file(tmp_path: Path):
    target = tmp_path / "project"
    target.write_text("keep", encoding="utf-8")

    _failure(
        _invoke([str(target), "--json"], cwd=tmp_path),
        "target_not_directory",
    )

    assert target.read_text(encoding="utf-8") == "keep"


def test_json_rejects_empty_named_target_without_force(tmp_path: Path):
    target = tmp_path / "project"
    target.mkdir()

    _failure(
        _invoke([str(target), "--json"], cwd=tmp_path),
        "target_exists",
    )

    assert not (target / ".specify").exists()


def test_json_reports_reinitialization_operation(tmp_path: Path):
    project = tmp_path / "project"
    _success(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    payload = _success(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["project"]["operation"] == "reinitialized"


def test_json_invalid_default_integration_is_a_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DEFAULT", "missing")

    payload = _success(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["integration"]["key"] == "copilot"
    assert payload["warnings"][0]["code"] == "invalid_default_integration"


def test_json_reports_missing_bundled_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command

    monkeypatch.setattr(init_command, "_locate_bundled_workflow", lambda _id: None)

    payload = _success(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["workflow"]["status"] == "skipped"
    assert {
        warning["code"] for warning in payload["warnings"]
    } >= {"bundled_workflow_not_found"}


def test_json_reports_bundled_workflow_install_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from specify_cli.workflows.engine import WorkflowDefinition

    monkeypatch.setattr(
        WorkflowDefinition,
        "from_yaml",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("workflow parse failed")
        ),
    )

    payload = _success(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["workflow"] == {
        "id": "speckit",
        "status": "failed",
        "reason": "workflow parse failed",
    }
    warning = next(
        warning
        for warning in payload["warnings"]
        if warning["code"] == "workflow_install_failed"
    )
    assert warning["details"] == {
        "workflow": "speckit",
        "reason": "workflow parse failed",
    }


def test_json_reports_missing_optional_preset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from specify_cli.presets import PresetCatalog

    monkeypatch.setattr(
        PresetCatalog,
        "get_pack_info",
        lambda *_args, **_kwargs: None,
    )

    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--preset",
                "missing",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["preset"]["status"] == "skipped"
    assert {warning["code"] for warning in payload["warnings"]} >= {
        "preset_not_found"
    }


def test_json_reports_already_installed_extension(tmp_path: Path):
    project = tmp_path / "project"
    args = [
        str(project),
        "--json",
        "--extension",
        "git",
        "--ignore-agent-tools",
    ]
    _success(_invoke(args, cwd=tmp_path))

    payload = _success(_invoke([*args, "--force"], cwd=tmp_path))

    assert payload["components"]["extensions"][0]["status"] == "already_installed"


def test_json_extension_status_does_not_depend_on_display_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command
    import specify_cli.events as events

    monkeypatch.setattr(
        init_command,
        "_install_extension_during_init_result",
        lambda *_args, **_kwargs: init_command._InitExtensionInstallResult(
            status="already_installed",
            message="present from an earlier installation",
        ),
    )
    monkeypatch.setattr(
        events,
        "refresh_integration_events",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("already-installed extension must not refresh events")
        ),
    )

    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--extension",
                "git",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["extensions"][0] == {
        "requested": "git",
        "status": "already_installed",
        "message": "present from an earlier installation",
    }


def test_json_exposes_extension_event_refresh_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.events as events
    from specify_cli.events import EventRefreshError

    monkeypatch.setattr(
        events,
        "refresh_integration_events",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            EventRefreshError(
                [
                    ("copilot", "hook write failed"),
                    ("claude", "settings unavailable"),
                ]
            )
        ),
    )

    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--extension",
                "git",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["extensions"][0]["status"] == "installed"
    warning = next(
        warning
        for warning in payload["warnings"]
        if warning["code"] == "extension_event_refresh_failed"
    )
    assert warning["details"]["failures"] == [
        {
            "integration": "copilot",
            "reason": "hook write failed",
        },
        {
            "integration": "claude",
            "reason": "settings unavailable",
        },
    ]


def test_json_exposes_force_reregistration_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from specify_cli.integrations import _helpers

    project = tmp_path / "project"
    _success(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )
    monkeypatch.setattr(
        _helpers,
        "_register_extensions_for_agent",
        lambda *_args, **_kwargs: "extension registration failed",
    )
    monkeypatch.setattr(
        _helpers,
        "_register_presets_for_agent",
        lambda *_args, **_kwargs: "preset registration failed",
    )

    payload = _success(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    warnings = {warning["code"]: warning for warning in payload["warnings"]}
    assert warnings["extension_reregistration_failed"]["details"]["reason"] == (
        "extension registration failed"
    )
    assert warnings["preset_reregistration_failed"]["details"]["reason"] == (
        "preset registration failed"
    )


def test_json_preserves_existing_constitution(tmp_path: Path):
    project = tmp_path / "project"
    args = [str(project), "--json", "--ignore-agent-tools"]
    _success(_invoke(args, cwd=tmp_path))
    constitution = project / ".specify" / "memory" / "constitution.md"
    constitution.write_text("custom constitution", encoding="utf-8")

    payload = _success(_invoke([*args, "--force"], cwd=tmp_path))

    assert payload["components"]["constitution"]["status"] == "preserved"
    assert constitution.read_text(encoding="utf-8") == "custom constitution"


def test_json_explicit_url_trust_never_prompts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli.command_init as init_command

    monkeypatch.setattr(
        typer,
        "confirm",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("trusted JSON URL must not prompt")
        ),
    )
    monkeypatch.setattr(
        init_command,
        "_install_extension_during_init_result",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("download unavailable")
        ),
    )

    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--extension",
                "https://example.com/extension.zip",
                "--trust-extension-urls",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["extensions"][0]["status"] == "failed"


def test_json_and_human_here_mode_create_identical_projects(tmp_path: Path):
    human = tmp_path / "human"
    machine = tmp_path / "machine"
    human.mkdir()
    machine.mkdir()
    (human / "keep.txt").write_text("keep", encoding="utf-8")
    (machine / "keep.txt").write_text("keep", encoding="utf-8")

    assert _invoke(
        [
            "--here",
            "--force",
            "--non-interactive",
            "--ignore-agent-tools",
        ],
        cwd=human,
    ).exit_code == 0
    _success(
        _invoke(
            [
                "--here",
                "--force",
                "--json",
                "--ignore-agent-tools",
            ],
            cwd=machine,
        )
    )

    assert _project_snapshot(human) == _project_snapshot(machine)


def test_json_and_human_force_merge_create_identical_projects(tmp_path: Path):
    human = tmp_path / "human"
    machine = tmp_path / "machine"
    human.mkdir()
    machine.mkdir()
    (human / "keep.txt").write_text("keep", encoding="utf-8")
    (machine / "keep.txt").write_text("keep", encoding="utf-8")

    assert _invoke(
        [
            str(human),
            "--force",
            "--non-interactive",
            "--ignore-agent-tools",
        ],
        cwd=tmp_path,
    ).exit_code == 0
    _success(
        _invoke(
            [
                str(machine),
                "--force",
                "--json",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert _project_snapshot(human) == _project_snapshot(machine)


def test_noninteractive_human_output_remains_human_readable(tmp_path: Path):
    result = _invoke(
        [
            "human-project",
            "--non-interactive",
            "--ignore-agent-tools",
        ],
        cwd=tmp_path,
    )

    assert result.exit_code == 0, result.output
    assert "Project ready" in result.stdout
    with pytest.raises(json.JSONDecodeError):
        json.loads(result.stdout)
