"""Tests for the runtime template renderer that replaces release-time
``create-release-packages.sh``.
"""

from pathlib import Path

import pytest

from infrakit_cli.template_renderer import (
    _PATH_REWRITES,
    materialize_project,
    parse_description,
    render_command,
    templates_root,
    write_command,
)


# ---------------------------------------------------------------------------
# Unit tests for the pure functions.
# ---------------------------------------------------------------------------


class TestParseDescription:
    def test_extracts_quoted_description(self):
        text = '---\ndescription: "Hello world."\nfoo: bar\n---\nbody\n'
        assert parse_description(text) == "Hello world."

    def test_extracts_unquoted_description(self):
        text = "---\ndescription: Hello world.\n---\n"
        assert parse_description(text) == "Hello world."

    def test_returns_empty_when_missing(self):
        assert parse_description("body without frontmatter") == ""


class TestRenderCommand:
    def test_substitutes_args_token(self):
        out = render_command("Use {ARGS} here.", args_token="$ARGUMENTS", agent="claude")
        assert "Use $ARGUMENTS here." in out

    def test_substitutes_toml_args(self):
        out = render_command("Use {ARGS} here.", args_token="{{args}}", agent="gemini")
        assert "Use {{args}} here." in out

    def test_substitutes_agent_token(self):
        out = render_command("Hi from __AGENT__.", args_token="$ARGUMENTS", agent="claude")
        assert out == "Hi from claude."

    def test_rewrites_repo_root_paths(self):
        body = (
            "Run scripts/foo.sh and look at memory/notes.md and templates/x.md."
        )
        out = render_command(body, args_token="$ARGUMENTS", agent="claude")
        assert ".infrakit/scripts/foo.sh" in out
        assert ".infrakit/memory/notes.md" in out
        assert ".infrakit/templates/x.md" in out

    def test_does_not_rewrite_already_prefixed_paths(self):
        body = "Already prefixed: .infrakit/scripts/foo.sh."
        out = render_command(body, args_token="$ARGUMENTS", agent="claude")
        # The rewrite must be idempotent — no doubling.
        assert ".infrakit.infrakit" not in out
        assert ".infrakit/scripts/foo.sh" in out

    def test_does_not_rewrite_mid_word_matches(self):
        # "schemescripts/" should not become "scheme.infrakit/scripts/".
        body = "schemescripts/foo and unrelatedmemory/bar"
        out = render_command(body, args_token="$ARGUMENTS", agent="claude")
        assert "schemescripts/foo" in out
        assert "unrelatedmemory/bar" in out


class TestWriteCommand:
    def test_markdown_writes_raw_body(self, tmp_path: Path):
        dest = write_command(
            "BODY",
            tmp_path,
            name="setup",
            command_format="markdown",
            extension=".md",
        )
        assert dest.name == "infrakit:setup.md"
        assert dest.read_text(encoding="utf-8") == "BODY"

    def test_agent_md_writes_raw_body_with_agent_extension(self, tmp_path: Path):
        dest = write_command(
            "BODY",
            tmp_path,
            name="setup",
            command_format="agent.md",
            extension=".agent.md",
        )
        assert dest.name == "infrakit:setup.agent.md"
        assert dest.read_text(encoding="utf-8") == "BODY"

    def test_toml_wraps_body_with_description(self, tmp_path: Path):
        dest = write_command(
            "Hello {{args}}.",
            tmp_path,
            name="setup",
            command_format="toml",
            extension=".toml",
            description="Initialise project.",
        )
        assert dest.name == "infrakit:setup.toml"
        content = dest.read_text(encoding="utf-8")
        assert 'description = "Initialise project."' in content
        assert 'prompt = """' in content
        assert "Hello {{args}}." in content

    def test_toml_escapes_backslashes(self, tmp_path: Path):
        dest = write_command(
            r"path with \backslash",
            tmp_path,
            name="x",
            command_format="toml",
            extension=".toml",
            description="d",
        )
        content = dest.read_text(encoding="utf-8")
        # Backslashes in TOML body must be escaped to survive triple-quoted parsing.
        assert "\\\\backslash" in content


# ---------------------------------------------------------------------------
# Integration: materialize_project produces the expected directory layouts
# for representative (agent, iac) combinations.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "agent,iac,expected_commands_dir,expected_extension",
    [
        ("claude", "terraform", ".claude/commands", ".md"),
        ("claude", "crossplane", ".claude/commands", ".md"),
        ("gemini", "terraform", ".gemini/commands", ".toml"),
        ("qwen", "crossplane", ".qwen/commands", ".toml"),
        ("copilot", "terraform", ".github/agents", ".agent.md"),
        ("cursor-agent", "crossplane", ".cursor/commands", ".md"),
        ("opencode", "terraform", ".opencode/command", ".md"),
        ("codex", "crossplane", ".codex/prompts", ".md"),
        ("q", "terraform", ".amazonq/prompts", ".md"),
        ("amp", "crossplane", ".agents/commands", ".md"),
        ("generic", "terraform", ".infrakit/commands", ".md"),
    ],
)
def test_materialize_project_layouts(
    tmp_path: Path,
    agent: str,
    iac: str,
    expected_commands_dir: str,
    expected_extension: str,
):
    project = tmp_path / "proj"
    counts = materialize_project(
        project, ai_assistant=agent, iac_tool=iac, script_variant="sh"
    )

    cmds_dir = project / expected_commands_dir
    assert cmds_dir.is_dir(), f"missing commands dir: {cmds_dir}"

    rendered = sorted(p.name for p in cmds_dir.iterdir() if p.is_file())
    assert rendered, "no commands rendered"
    for name in rendered:
        assert name.startswith("infrakit:")
        assert name.endswith(expected_extension)

    # Both generic and IaC-native commands should be present.
    assert counts["generic_commands"] > 0
    assert counts["iac_commands"] > 0

    # Personas (generic + IaC) land in .infrakit/agent_personas/.
    personas_dir = project / ".infrakit" / "agent_personas"
    assert personas_dir.is_dir()
    personas = list(personas_dir.glob("*.md"))
    assert len(personas) >= 3  # 3 generic personas at minimum


def test_materialize_copilot_emits_prompt_pairs(tmp_path: Path):
    project = tmp_path / "proj"
    counts = materialize_project(
        project, ai_assistant="copilot", iac_tool="terraform", script_variant="sh"
    )

    agents_dir = project / ".github" / "agents"
    prompts_dir = project / ".github" / "prompts"
    assert agents_dir.is_dir()
    assert prompts_dir.is_dir()

    agent_files = sorted(p.stem.removesuffix(".agent") for p in agents_dir.glob("infrakit:*.agent.md"))
    prompt_files = sorted(p.stem.removesuffix(".prompt") for p in prompts_dir.glob("infrakit:*.prompt.md"))
    assert agent_files == prompt_files
    assert counts["prompt_files"] == len(agent_files) > 0


def test_materialize_copilot_copies_vscode_settings(tmp_path: Path):
    project = tmp_path / "proj"
    materialize_project(
        project, ai_assistant="copilot", iac_tool="terraform", script_variant="sh"
    )
    assert (project / ".vscode" / "settings.json").is_file()


def test_materialize_gemini_wraps_commands_as_toml(tmp_path: Path):
    project = tmp_path / "proj"
    materialize_project(
        project, ai_assistant="gemini", iac_tool="crossplane", script_variant="sh"
    )
    setup = project / ".gemini" / "commands" / "infrakit:setup.toml"
    assert setup.is_file()
    content = setup.read_text(encoding="utf-8")
    assert 'description = "' in content
    assert 'prompt = """' in content
    # The {ARGS} marker (when present) gets substituted to the Gemini form.
    # Current templates use $ARGUMENTS literally, mirroring the previous
    # release-script behavior — substitution is opt-in via the {ARGS} marker.


def test_materialize_terraform_uses_terraform_commands(tmp_path: Path):
    project = tmp_path / "proj"
    materialize_project(
        project, ai_assistant="claude", iac_tool="terraform", script_variant="sh"
    )
    cmds = sorted(p.name for p in (project / ".claude" / "commands").iterdir())
    # Terraform IaC commands present, Crossplane ones absent.
    assert "infrakit:create_terraform_code.md" in cmds
    assert "infrakit:new_composition.md" not in cmds


def test_materialize_crossplane_uses_crossplane_commands(tmp_path: Path):
    project = tmp_path / "proj"
    materialize_project(
        project, ai_assistant="claude", iac_tool="crossplane", script_variant="sh"
    )
    cmds = sorted(p.name for p in (project / ".claude" / "commands").iterdir())
    assert "infrakit:new_composition.md" in cmds
    assert "infrakit:create_terraform_code.md" not in cmds


def test_unknown_agent_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="unknown AI assistant"):
        materialize_project(
            tmp_path / "x", ai_assistant="nope", iac_tool="terraform"
        )


def test_unknown_iac_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="unknown IaC tool"):
        materialize_project(
            tmp_path / "x", ai_assistant="claude", iac_tool="nope"
        )


def test_overwrite_is_idempotent_when_false(tmp_path: Path):
    project = tmp_path / "proj"
    materialize_project(
        project, ai_assistant="claude", iac_tool="terraform", script_variant="sh"
    )
    setup_path = project / ".claude" / "commands" / "infrakit:setup.md"
    first_mtime = setup_path.stat().st_mtime
    # Tamper with the file, then re-materialise without overwrite.
    setup_path.write_text("TAMPERED", encoding="utf-8")
    materialize_project(
        project, ai_assistant="claude", iac_tool="terraform", script_variant="sh"
    )
    assert setup_path.read_text(encoding="utf-8") == "TAMPERED"


def test_overwrite_true_replaces_existing(tmp_path: Path):
    project = tmp_path / "proj"
    materialize_project(
        project, ai_assistant="claude", iac_tool="terraform", script_variant="sh"
    )
    setup_path = project / ".claude" / "commands" / "infrakit:setup.md"
    setup_path.write_text("TAMPERED", encoding="utf-8")
    materialize_project(
        project,
        ai_assistant="claude",
        iac_tool="terraform",
        script_variant="sh",
        overwrite=True,
    )
    body = setup_path.read_text(encoding="utf-8")
    assert body != "TAMPERED"
    assert "description:" in body  # frontmatter restored


def test_templates_root_points_at_real_directory():
    root = templates_root()
    assert root.is_dir()
    assert (root / "commands" / "setup.md").is_file()
    assert (root / "iac" / "terraform" / "commands" / "create_terraform_code.md").is_file()
    assert (root / "iac" / "crossplane" / "commands" / "new_composition.md").is_file()


def test_path_rewrites_have_no_typos():
    # Smoke: every rewrite tuple is (compiled-regex, str-replacement).
    for pattern, replacement in _PATH_REWRITES:
        assert hasattr(pattern, "sub")
        assert isinstance(replacement, str)
