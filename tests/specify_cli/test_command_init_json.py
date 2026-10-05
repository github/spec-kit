"""Contract tests for ``specify init --json``."""

from __future__ import annotations

import json
import os
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


def test_json_init_new_directory_uses_safe_defaults(tmp_path: Path):
    project = tmp_path / "new-project"

    payload = _success(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["project"] == {
        "name": "new-project",
        "path": str(project.resolve()),
        "operation": "created",
    }
    assert payload["integration"]["key"] == "copilot"
    assert payload["integration"]["defaulted"] is True
    assert payload["script"]["type"] == ("ps" if os.name == "nt" else "sh")
    assert payload["script"]["defaulted"] is True
    assert payload["components"]["shared_infrastructure"]["status"] == "installed"
    assert payload["components"]["workflow"]["status"] in {
        "installed",
        "already_installed",
    }
    assert payload["components"]["constitution"]["status"] == "created"
    assert payload["components"]["preset"] is None
    assert payload["components"]["extensions"] == []
    assert payload["next_steps"][0] == {
        "action": "change_directory",
        "path": str(project.resolve()),
    }
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


def test_json_init_never_prompts_even_when_stdin_is_a_tty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli.command_init as init_command

    monkeypatch.setattr(init_command, "_stdin_is_interactive", lambda: True)

    def fail_prompt(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("JSON mode must not render or prompt")

    monkeypatch.setattr(init_command, "select_with_arrows", fail_prompt)
    monkeypatch.setattr(typer, "confirm", fail_prompt)
    monkeypatch.setattr(init_command, "show_banner", fail_prompt)
    monkeypatch.setattr(init_command, "Live", fail_prompt)

    payload = _success(
        _invoke(
            ["tty-project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["integration"]["defaulted"] is True
    assert payload["script"]["defaulted"] is True


def test_json_init_rejects_nonempty_here_without_force_and_preserves_files(
    tmp_path: Path,
):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    error = _failure(
        _invoke(
            ["--here", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "target_not_empty",
    )

    assert error["details"]["item_count"] == 1
    assert marker.read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / ".specify").exists()


def test_json_init_force_merges_nonempty_target(tmp_path: Path):
    project = tmp_path / "existing"
    project.mkdir()
    marker = project / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

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
    assert (project / ".specify").is_dir()


def test_json_init_reports_reinitialization(tmp_path: Path):
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


def test_json_force_reinitialization_persists_new_integration_before_reregistration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from specify_cli.extensions import ExtensionManager
    from specify_cli.presets import PresetManager

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

    observed: list[tuple[str, str, dict[str, Any]]] = []

    def record_extension_mode(
        manager: ExtensionManager,
        agent_name: str,
        *,
        force: bool = False,
    ) -> None:
        options = json.loads(
            (manager.project_root / ".specify" / "init-options.json").read_text(
                encoding="utf-8"
            )
        )
        observed.append(("extension", agent_name, options))

    def record_preset_mode(manager: PresetManager, agent_name: str) -> None:
        options = json.loads(
            (manager.project_root / ".specify" / "init-options.json").read_text(
                encoding="utf-8"
            )
        )
        observed.append(("preset", agent_name, options))

    monkeypatch.setattr(
        ExtensionManager,
        "register_enabled_extensions_for_agent",
        record_extension_mode,
    )
    monkeypatch.setattr(
        PresetManager,
        "register_enabled_presets_for_agent",
        record_preset_mode,
    )

    payload = _success(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--integration",
                "claude",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["project"]["operation"] == "reinitialized"
    assert [(kind, agent) for kind, agent, _options in observed] == [
        ("extension", "claude"),
        ("preset", "claude"),
    ]
    for _kind, _agent, options in observed:
        assert options["ai"] == "claude"
        assert options["ai_skills"] is True


def test_json_force_reinitialization_rejects_layout_change_before_mutation(
    tmp_path: Path,
):
    project = tmp_path / "project"
    _success(
        _invoke(
            [
                str(project),
                "--json",
                "--integration",
                "copilot",
                "--integration-options=--commands",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        )
    )

    manifest_path = (
        project / ".specify" / "integrations" / "copilot.manifest.json"
    )
    init_options_path = project / ".specify" / "init-options.json"
    old_manifest = manifest_path.read_bytes()
    old_init_options = init_options_path.read_bytes()
    old_command_files = sorted(
        path.relative_to(project)
        for root in (project / ".github" / "agents", project / ".github" / "prompts")
        for path in root.glob("speckit.*")
    )
    assert old_command_files

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--integration",
                "copilot",
                "--integration-options=--skills",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        ),
        "invalid_integration_options",
    )

    assert error["details"]["current_layout"] == "commands"
    assert error["details"]["requested_layout"] == "skills"
    assert error["details"]["recommended_action"] == {
        "command": "integration_upgrade",
        "integration": "copilot",
        "force": True,
        "integration_options": "--skills",
    }
    assert manifest_path.read_bytes() == old_manifest
    assert init_options_path.read_bytes() == old_init_options
    assert sorted(
        path.relative_to(project)
        for root in (project / ".github" / "agents", project / ".github" / "prompts")
        for path in root.glob("speckit.*")
    ) == old_command_files
    assert not (project / ".github" / "skills").exists()


def test_json_force_reinitialization_rejects_generic_destination_change(
    tmp_path: Path,
):
    project = tmp_path / "project"
    _success(
        _invoke(
            [
                str(project),
                "--json",
                "--integration",
                "generic",
                "--integration-options=--commands-dir .old/commands",
            ],
            cwd=tmp_path,
        )
    )

    manifest_path = (
        project / ".specify" / "integrations" / "generic.manifest.json"
    )
    init_options_path = project / ".specify" / "init-options.json"
    old_manifest = manifest_path.read_bytes()
    old_init_options = init_options_path.read_bytes()
    old_commands = {
        path.relative_to(project): path.read_bytes()
        for path in (project / ".old" / "commands").glob("speckit.*")
    }
    assert old_commands

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--force",
                "--integration",
                "generic",
                "--integration-options=--commands-dir .new/commands",
            ],
            cwd=tmp_path,
        ),
        "invalid_integration_options",
    )

    assert error["details"]["current_commands_dir"] == ".old/commands"
    assert error["details"]["requested_commands_dir"] == ".new/commands"
    assert error["details"]["recommended_action"] == {
        "command": "integration_upgrade",
        "integration": "generic",
        "force": True,
        "integration_options": "--commands-dir .new/commands",
    }
    assert manifest_path.read_bytes() == old_manifest
    assert init_options_path.read_bytes() == old_init_options
    assert {
        path.relative_to(project): path.read_bytes()
        for path in (project / ".old" / "commands").glob("speckit.*")
    } == old_commands
    assert not (project / ".new").exists()


def test_json_force_reinitialization_allows_same_generic_destination(
    tmp_path: Path,
):
    project = tmp_path / "project"
    args = [
        str(project),
        "--json",
        "--integration",
        "generic",
        "--integration-options=--commands-dir .agent/commands",
    ]
    _success(_invoke(args, cwd=tmp_path))

    payload = _success(
        _invoke([*args, "--force"], cwd=tmp_path)
    )

    assert payload["project"]["operation"] == "reinitialized"
    assert list((project / ".agent" / "commands").glob("speckit.*"))


@pytest.mark.parametrize(
    ("args", "code"),
    [
        (["--json"], "target_required"),
        (["project", "--here", "--json"], "conflicting_target_options"),
        (
            [
                "project",
                "--json",
                "--integration",
                "not-registered",
            ],
            "invalid_integration",
        ),
        (
            [
                "project",
                "--json",
                "--integration",
                "copilot",
                "--integration-options=--not-an-option",
            ],
            "invalid_integration_options",
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
                "bob",
                "--integration-options=--skills --legacy-commands",
            ],
            "invalid_integration_options",
        ),
        (
            [
                "project",
                "--json",
                "--script",
                "fish",
            ],
            "invalid_script_type",
        ),
    ],
)
def test_json_init_validation_failures_do_not_create_target(
    tmp_path: Path,
    args: list[str],
    code: str,
):
    _failure(_invoke(args, cwd=tmp_path), code)
    assert not (tmp_path / "project").exists()


def test_json_init_rejects_escaping_generic_directory_before_target_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    import specify_cli._command_init_json as init_json

    project = tmp_path / "project"

    def fail_claim(_plan: Any) -> None:
        raise AssertionError("invalid integration options must fail before mutation")

    monkeypatch.setattr(init_json, "_claim_new_target", fail_claim)

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--integration",
                "generic",
                "--integration-options=--commands-dir ../outside",
            ],
            cwd=tmp_path,
        ),
        "invalid_integration_options",
    )

    assert "escapes project root" in error["details"]["reason"]
    assert not project.exists()
    assert not (tmp_path / "outside").exists()


@pytest.mark.parametrize(
    "args",
    [
        ["project", "--json", "--unknown-option"],
        ["project", "--json", "--script"],
    ],
)
def test_json_init_parser_failures_use_structured_error(
    tmp_path: Path,
    args: list[str],
):
    _failure(_invoke(args, cwd=tmp_path), "invalid_arguments")
    assert not (tmp_path / "project").exists()


def test_json_init_rejects_existing_named_target_without_force(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()

    _failure(
        _invoke([str(project), "--json"], cwd=tmp_path),
        "target_exists",
    )

    assert project.is_dir()
    assert not (project / ".specify").exists()


def test_json_init_reports_missing_required_agent_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    monkeypatch.setattr(init_json, "check_tool", lambda _tool: False)

    error = _failure(
        _invoke(
            [
                "project",
                "--json",
                "--integration",
                "claude",
            ],
            cwd=tmp_path,
        ),
        "missing_agent_tool",
    )

    assert error["details"]["integration"] == "claude"
    assert error["details"]["override_flag"] == "--ignore-agent-tools"
    assert not (tmp_path / "project").exists()


def test_json_init_rejects_untrusted_url_extension_before_mutation(tmp_path: Path):
    project = tmp_path / "project"

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--extension",
                "https://example.com/extension.zip",
            ],
            cwd=tmp_path,
        ),
        "extension_url_trust_required",
    )

    assert error["details"]["required_flag"] == "--trust-extension-urls"
    assert not project.exists()


def test_json_init_explicit_url_trust_never_prompts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli.command_init as init_command

    def fail_prompt(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("trusted JSON URL install must not prompt")

    def fail_download(*_args: Any, **_kwargs: Any) -> str:
        raise ValueError("download unavailable")

    monkeypatch.setattr(typer, "confirm", fail_prompt)
    monkeypatch.setattr(
        init_command,
        "_install_extension_during_init",
        fail_download,
    )

    payload = _success(
        _invoke(
            [
                "project",
                "--json",
                "--ignore-agent-tools",
                "--extension",
                "https://example.com/extension.zip",
                "--trust-extension-urls",
            ],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["extensions"][0]["status"] == "failed"
    assert any(
        warning["code"] == "extension_install_failed"
        for warning in payload["warnings"]
    )


def test_json_init_invalid_default_integration_becomes_structured_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DEFAULT", "missing-default")

    payload = _success(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["integration"]["key"] == "copilot"
    assert payload["integration"]["defaulted"] is True
    assert payload["warnings"][0]["code"] == "invalid_default_integration"


def test_json_init_exposes_optional_preset_and_extension_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli.command_init as init_command
    from specify_cli.presets import PresetManager

    def fail_preset(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("preset install failed")

    def fail_extension(*_args: Any, **_kwargs: Any) -> str:
        raise ValueError("extension install failed")

    monkeypatch.setattr(PresetManager, "install_from_directory", fail_preset)
    monkeypatch.setattr(
        init_command,
        "_install_extension_during_init",
        fail_extension,
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
    assert payload["components"]["extensions"] == [
        {
            "requested": "git",
            "status": "failed",
            "reason": "extension install failed",
        }
    ]
    warning_codes = {warning["code"] for warning in payload["warnings"]}
    assert "preset_install_failed" in warning_codes
    assert "extension_install_failed" in warning_codes


def test_json_init_exposes_skipped_bundled_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    monkeypatch.setattr(init_json, "_locate_bundled_workflow", lambda _id: None)

    payload = _success(
        _invoke(
            ["project", "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        )
    )

    assert payload["components"]["workflow"] == {
        "id": "speckit",
        "status": "skipped",
        "reason": "bundled_workflow_not_found",
    }
    assert any(
        warning["code"] == "bundled_workflow_not_found"
        for warning in payload["warnings"]
    )


def test_json_init_rolls_back_new_target_after_fatal_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    def fail_shared(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise OSError("shared infrastructure failed")

    monkeypatch.setattr(init_json, "_install_shared_infrastructure", fail_shared)
    project = tmp_path / "project"

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "initialization_failed",
    )

    assert error["details"]["rollback"] == {
        "status": "completed",
        "path": str(project.resolve()),
    }
    assert not project.exists()


def test_json_init_never_deletes_preexisting_target_after_fatal_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    project = tmp_path / "project"
    project.mkdir()
    marker = project / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    def fail_shared(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise OSError("shared infrastructure failed")

    monkeypatch.setattr(init_json, "_install_shared_infrastructure", fail_shared)

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
    assert project.is_dir()


def test_json_init_never_deletes_target_created_during_claim_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    project = tmp_path / "project"
    marker = project / "keep.txt"
    original_mkdir = Path.mkdir

    def racing_mkdir(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == project and kwargs.get("exist_ok") is False:
            original_mkdir(path, parents=True)
            marker.write_text("keep", encoding="utf-8")
        original_mkdir(path, *args, **kwargs)

    def fail_initialize(_plan: Any) -> dict[str, Any]:
        raise AssertionError("initialization must not start without target ownership")

    monkeypatch.setattr(Path, "mkdir", racing_mkdir)
    monkeypatch.setattr(init_json, "_initialize_project", fail_initialize)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "target_exists",
    )

    assert error["details"]["concurrent_creation"] is True
    assert marker.read_text(encoding="utf-8") == "keep"
    assert project.is_dir()


def test_json_init_rolls_back_when_integration_setup_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from specify_cli.integrations import get_integration

    project = tmp_path / "project"
    integration = get_integration("copilot")
    assert integration is not None

    def fail_setup(*_args: Any, **_kwargs: Any) -> None:
        project.mkdir(exist_ok=True)
        raise OSError("integration setup failed")

    monkeypatch.setattr(integration, "setup", fail_setup)

    error = _failure(
        _invoke(
            [
                str(project),
                "--json",
                "--integration",
                "copilot",
                "--ignore-agent-tools",
            ],
            cwd=tmp_path,
        ),
        "initialization_failed",
    )

    assert error["details"]["component"] == "integration"
    assert error["details"]["rollback"]["status"] == "completed"
    assert not project.exists()


def test_json_init_rolls_back_when_manifest_construction_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli.integrations.manifest as manifest_module

    project = tmp_path / "project"

    class FailingManifest:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            project.mkdir(exist_ok=True)
            raise OSError("manifest construction failed")

    monkeypatch.setattr(manifest_module, "IntegrationManifest", FailingManifest)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "initialization_failed",
    )

    assert error["details"]["component"] == "integration"
    assert error["details"]["rollback"]["status"] == "completed"
    assert not project.exists()


def test_json_init_sanitizes_unexpected_exception_and_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    project = tmp_path / "project"

    def fail_unexpected(plan: Any) -> dict[str, Any]:
        raise RuntimeError("sensitive internal detail")

    monkeypatch.setattr(init_json, "_initialize_project", fail_unexpected)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "internal_error",
    )

    assert error["details"]["exception_type"] == "RuntimeError"
    assert "sensitive internal detail" not in json.dumps(error)
    assert error["details"]["rollback"]["status"] == "completed"
    assert not project.exists()


def test_json_init_reports_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli._command_init_json as init_json

    project = tmp_path / "project"

    def fail_unexpected(plan: Any) -> dict[str, Any]:
        raise RuntimeError("initial failure")

    def fail_cleanup(_path: Path) -> None:
        raise OSError("cleanup failed")

    monkeypatch.setattr(init_json, "_initialize_project", fail_unexpected)
    monkeypatch.setattr(init_json.shutil, "rmtree", fail_cleanup)

    error = _failure(
        _invoke(
            [str(project), "--json", "--ignore-agent-tools"],
            cwd=tmp_path,
        ),
        "rollback_failed",
    )

    assert error["details"]["original_error"]["code"] == "internal_error"
    assert error["details"]["cleanup_error"]["exception_type"] == "OSError"
    assert project.is_dir()


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
