from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app


def _parse_skill_frontmatter(skill_file: Path) -> dict:
    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    lines = content.splitlines(keepends=True)
    end = next(i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---")
    parsed = yaml.safe_load("".join(lines[1:end]))
    assert isinstance(parsed, dict)
    return parsed


def _write_hint_extension(ext_dir: Path, *, description: str, arg_hint: str) -> Path:
    (ext_dir / "commands").mkdir(parents=True)
    (ext_dir / "extension.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "extension": {
                    "id": "hint-ext",
                    "name": "Hint Extension",
                    "version": "1.0.0",
                    "description": "Extension with argument-hint",
                    "author": "ext-author",
                    "repository": "https://example.com",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": "speckit.hint-ext.run",
                            "file": "commands/run.md",
                            "description": description,
                            "aliases": ["speckit.hint-ext.go"],
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (ext_dir / "commands" / "run.md").write_text(
        f'---\ndescription: "{description}"\nargument-hint: "{arg_hint}"\n---\n\nRun $ARGUMENTS\n',
        encoding="utf-8",
    )
    return ext_dir


def test_extension_add_preserves_argument_hint_and_skill_flags_for_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    project = tmp_path / "proj"
    init_res = runner.invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            "claude",
            "--ignore-agent-tools",
            "--non-interactive",
        ],
    )
    assert init_res.exit_code == 0, init_res.output

    long_description = (
        "Build and maintain a lean static context folder so coding agents "
        "load only relevant files and preserve token budget across runs"
    )
    arg_hint = "<target> [--dry-run] [--notes]"
    ext_dir = _write_hint_extension(
        tmp_path / "hint-ext",
        description=long_description,
        arg_hint=arg_hint,
    )

    monkeypatch.chdir(project)
    add_res = runner.invoke(app, ["extension", "add", str(ext_dir), "--dev"])
    assert add_res.exit_code == 0, add_res.output

    for skill_name in ("speckit-hint-ext-run", "speckit-hint-ext-go"):
        skill_file = project / ".claude" / "skills" / skill_name / "SKILL.md"
        assert skill_file.is_file()
        parsed = _parse_skill_frontmatter(skill_file)
        assert parsed["name"] == skill_name
        assert parsed["description"] == long_description
        assert parsed["argument-hint"] == arg_hint
        assert parsed["user-invocable"] is True
        assert parsed["disable-model-invocation"] is False


def test_extension_add_gates_argument_hint_and_applies_agent_skill_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    ext_dir = _write_hint_extension(
        tmp_path / "hint-ext",
        description="Run command",
        arg_hint="<target>",
    )

    codex_project = tmp_path / "codex-proj"
    assert (
        runner.invoke(
            app,
            [
                "init",
                str(codex_project),
                "--integration",
                "codex",
                "--ignore-agent-tools",
                "--non-interactive",
            ],
        ).exit_code
        == 0
    )
    monkeypatch.chdir(codex_project)
    assert (
        runner.invoke(app, ["extension", "add", str(ext_dir), "--dev"]).exit_code == 0
    )
    codex_fm = _parse_skill_frontmatter(
        codex_project / ".agents" / "skills" / "speckit-hint-ext-run" / "SKILL.md"
    )
    assert "argument-hint" not in codex_fm
    assert "user-invocable" not in codex_fm

    droid_project = tmp_path / "droid-proj"
    assert (
        runner.invoke(
            app,
            [
                "init",
                str(droid_project),
                "--integration",
                "droid",
                "--ignore-agent-tools",
                "--non-interactive",
            ],
        ).exit_code
        == 0
    )
    monkeypatch.chdir(droid_project)
    assert (
        runner.invoke(app, ["extension", "add", str(ext_dir), "--dev"]).exit_code == 0
    )
    droid_fm = _parse_skill_frontmatter(
        droid_project / ".factory" / "skills" / "speckit-hint-ext-run" / "SKILL.md"
    )
    assert "argument-hint" not in droid_fm
    assert droid_fm["user-invocable"] is True
    assert droid_fm["disable-model-invocation"] is False


@pytest.mark.parametrize(
    ("integration", "skills_rel", "expected_hook_example"),
    [
        ("claude", ".claude/skills", "`/speckit-git-commit`"),
        ("codex", ".agents/skills", "`$speckit-git-commit`"),
    ],
)
def test_bundled_github_extension_skill_receives_hook_command_note(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    integration: str,
    skills_rel: str,
    expected_hook_example: str,
) -> None:
    runner = CliRunner()
    project = tmp_path / f"{integration}-proj"
    init_res = runner.invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            integration,
            "--extension",
            "github",
            "--ignore-agent-tools",
            "--non-interactive",
        ],
    )
    assert init_res.exit_code == 0, init_res.output

    skill_file = (
        project / skills_rel / "speckit-github-taskstoissues" / "SKILL.md"
    )
    assert skill_file.is_file()
    content = skill_file.read_text(encoding="utf-8")
    assert expected_hook_example in content


def test_preset_command_alias_skill_preserves_argument_hint_and_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    project = tmp_path / "proj"
    init_res = runner.invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            "claude",
            "--ignore-agent-tools",
            "--non-interactive",
        ],
    )
    assert init_res.exit_code == 0, init_res.output

    preset_dir = tmp_path / "deploy-preset"
    (preset_dir / "commands").mkdir(parents=True)
    (preset_dir / "preset.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "deploy-preset",
                    "name": "Deploy Preset",
                    "version": "1.0.0",
                    "description": "Preset with aliased command",
                    "author": "preset-author",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "command",
                            "name": "speckit.custom.deploy",
                            "file": "commands/deploy.md",
                            "description": "Deploy command",
                            "aliases": ["speckit.custom.ship"],
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (preset_dir / "commands" / "deploy.md").write_text(
        '---\ndescription: "Deploy command"\nargument-hint: "<env> [--force]"\n---\n\nDeploy $ARGUMENTS\n',
        encoding="utf-8",
    )

    monkeypatch.chdir(project)
    add_res = runner.invoke(app, ["preset", "add", "--dev", str(preset_dir)])
    assert add_res.exit_code == 0, add_res.output

    for skill_name in ("speckit-custom-deploy", "speckit-custom-ship"):
        skill_file = project / ".claude" / "skills" / skill_name / "SKILL.md"
        assert skill_file.is_file()
        parsed = _parse_skill_frontmatter(skill_file)
        assert parsed["argument-hint"] == "<env> [--force]"
        assert parsed["user-invocable"] is True
        assert parsed["disable-model-invocation"] is False
