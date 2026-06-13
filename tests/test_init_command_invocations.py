"""Regression tests for integration-aware init command hints."""

from typer.testing import CliRunner

from tests.conftest import strip_ansi


def _clean_output(output: str) -> str:
    return strip_ansi(output)


def test_init_codex_next_steps_use_dollar_skills(tmp_path):
    from specify_cli import app

    project = tmp_path / "codex-init"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            "codex",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    output = _clean_output(result.output)
    assert result.exit_code == 0, result.output
    assert "$speckit-plan" in output
    assert "$speckit-analyze" in output
    assert "/speckit-plan" not in output
    assert "/speckit.plan" not in output


def test_init_copilot_next_steps_keep_slash_dot(tmp_path):
    from specify_cli import app

    project = tmp_path / "copilot-init"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            "copilot",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    output = _clean_output(result.output)
    assert result.exit_code == 0, result.output
    assert "/speckit.plan" in output
    assert "/speckit.tasks" in output
    assert "$speckit-plan" not in output


def test_init_copilot_skills_next_steps_keep_slash_hyphen(tmp_path):
    from specify_cli import app

    project = tmp_path / "copilot-skills-init"
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            "copilot",
            "--integration-options",
            "--skills",
            "--script",
            "sh",
            "--ignore-agent-tools",
        ],
        catch_exceptions=False,
    )

    output = _clean_output(result.output)
    assert result.exit_code == 0, result.output
    assert "/speckit-plan" in output
    assert "/speckit-tasks" in output
    assert "/speckit.plan" not in output
    assert "$speckit-plan" not in output
