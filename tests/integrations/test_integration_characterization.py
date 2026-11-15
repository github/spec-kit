"""Cross-integration characterization tests for stable delivery contracts."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest


@pytest.mark.parametrize(
    (
        "integration_key",
        "options",
        "installed_command",
        "expected_invocation",
        "expected_reference",
        "companion",
    ),
    [
        (
            "amp",
            {},
            ".agents/commands/speckit.specify.md",
            "/speckit.specify",
            "/speckit.plan",
            None,
        ),
        (
            "forge",
            {},
            ".forge/commands/speckit.specify.md",
            "/speckit-specify",
            "/speckit-plan",
            None,
        ),
        (
            "codex",
            {},
            ".agents/skills/speckit-specify/SKILL.md",
            "$speckit-specify",
            "$speckit-plan",
            None,
        ),
        (
            "kimi",
            {},
            ".kimi-code/skills/speckit-specify/SKILL.md",
            "/skill:speckit-specify",
            "/skill:speckit-plan",
            None,
        ),
        (
            "bob",
            {},
            ".bob/skills/speckit-specify/SKILL.md",
            "/speckit-specify",
            "/speckit-plan",
            None,
        ),
        (
            "bob",
            {"legacy_commands": True},
            ".bob/commands/speckit.specify.md",
            "/speckit.specify",
            "/speckit.plan",
            None,
        ),
        (
            "copilot",
            {},
            ".github/skills/speckit-specify/SKILL.md",
            "/speckit-specify",
            "/speckit-plan",
            None,
        ),
        (
            "copilot",
            {"commands": True},
            ".github/agents/speckit.specify.agent.md",
            "",
            "/speckit.plan",
            ".github/prompts/speckit.specify.prompt.md",
        ),
    ],
)
def test_installed_names_invocations_and_rendered_references_stay_aligned(
    tmp_path: Path,
    integration_key: str,
    options: dict[str, bool],
    installed_command: str,
    expected_invocation: str,
    expected_reference: str,
    companion: str | None,
) -> None:
    """Installed names, native invocation syntax, and rendered refs agree."""
    integration = type(get_integration(integration_key))()
    manifest = IntegrationManifest(integration_key, tmp_path)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        integration.setup(tmp_path, manifest, parsed_options=options)

    command_path = tmp_path / installed_command
    assert command_path.is_file()
    content = command_path.read_text(encoding="utf-8")
    assert "__SPECKIT_COMMAND_" not in content
    assert expected_reference in content
    invocation = (
        integration.build_command_invocation(
            "speckit.specify", project_root=tmp_path
        )
        if integration_key == "bob"
        else integration.build_command_invocation("speckit.specify")
    )
    assert invocation == expected_invocation
    if companion is not None:
        prompt_path = tmp_path / companion
        assert prompt_path.read_text(encoding="utf-8") == (
            "---\nagent: speckit.specify\n---\n"
        )


@pytest.mark.parametrize(
    ("integration_key", "expected", "excluded", "guidance"),
    [
        (
            "command-code",
            "$speckit-constitution",
            "/speckit.constitution",
            (),
        ),
        ("forge", "/speckit-plan", "/speckit.plan", ()),
        (
            "kimi",
            "/skill:speckit-constitution",
            "/speckit.constitution",
            ("Optional skills that you can use for your specs",),
        ),
        ("copilot", "/speckit-plan", "/speckit.plan", ()),
        (
            "dsh",
            "/speckit-plan",
            "/speckit.plan",
            ("Start DSH", "dsh web", ".dsh/skills"),
        ),
    ],
)
def test_init_completion_guidance_matches_installed_integration(
    tmp_path: Path,
    integration_key: str,
    expected: str,
    excluded: str,
    guidance: tuple[str, ...],
) -> None:
    project = tmp_path / integration_key
    result = CliRunner().invoke(
        app,
        [
            "init",
            str(project),
            "--integration",
            integration_key,
            "--ignore-agent-tools",
            "--script",
            "sh",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
    assert expected in result.output
    assert excluded not in result.output
    for snippet in guidance:
        assert snippet in result.output
