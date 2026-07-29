"""Tests for CLI-specific orchestrator dispatch-block injection.

Every workflow command template carries a ``__SPECKIT_DISPATCH_BLOCK__``
placeholder. At install time each integration substitutes it with the block
dedicated to its CLI's model-dispatch mechanism, so the skills written to disk
speak only their own CLI's route (OpenCode → named subagents; Hermes → spawn
the Hermes CLI with ``-m``).
"""

from pathlib import Path

import pytest

from specify_cli.integrations import INTEGRATION_REGISTRY
from specify_cli.integrations.base import IntegrationBase
from specify_cli.integrations.dispatch_blocks import (
    DISPATCH_PLACEHOLDER,
    GENERIC_DISPATCH_BLOCK,
    HERMES_DISPATCH_BLOCK,
    OPENCODE_DISPATCH_BLOCK,
)

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_DIR = ROOT / "templates" / "commands"
# Templates that carry the orchestrator dispatch placeholder (everything that
# consumes models.json — constitution and models are exempt).
EXEMPT = {"constitution.md", "models.md"}


def _workflow_templates():
    return [
        t for t in sorted(COMMANDS_DIR.glob("*.md")) if t.name not in EXEMPT
    ]


def test_every_workflow_template_carries_the_placeholder():
    for t in _workflow_templates():
        content = t.read_text(encoding="utf-8")
        assert DISPATCH_PLACEHOLDER in content, t.name


def test_templates_never_hardcode_a_single_cli_mechanism():
    """The raw template must not bake in one CLI's route; that leaks it into
    every other CLI's skills. The mechanism is injected per-CLI instead."""
    for t in _workflow_templates():
        content = t.read_text(encoding="utf-8")
        assert "subagent_type" not in content, t.name


def test_hermes_dispatch_block_is_hermes_only():
    block = INTEGRATION_REGISTRY["hermes"].dispatch_block()
    assert block is HERMES_DISPATCH_BLOCK
    assert "hermes chat -q -m" in block
    # no OpenCode/agent mechanism words
    assert "subagent_type" not in block
    assert "native_subagent" not in block
    # the fallback contract is present
    assert "next model in that level's list" in block
    assert "DISPATCH n<level> -> <model>" in block


def test_opencode_dispatch_block_is_opencode_only():
    block = INTEGRATION_REGISTRY["opencode"].dispatch_block()
    assert block is OPENCODE_DISPATCH_BLOCK
    assert "subagent_type" in block
    # no Hermes subprocess mechanism
    assert "hermes chat" not in block
    # the fallback contract is present
    assert "next model in that level's list" in block
    assert "DISPATCH n<level> -> <model>" in block


def test_default_dispatch_block_is_generic_multimode():
    """Integrations that don't override dispatch_block() get the generic block
    that reads every executor mode from models.json."""
    block = INTEGRATION_REGISTRY["claude"].dispatch_block()
    assert block == GENERIC_DISPATCH_BLOCK
    assert "native_subagent" in block
    assert "cli_subprocess" in block


def test_hermes_render_substitutes_placeholder_with_hermes_block():
    raw = (COMMANDS_DIR / "implement.md").read_text(encoding="utf-8")
    integ = INTEGRATION_REGISTRY["hermes"]
    out = integ.process_template(
        raw, "hermes", "py", "$ARGUMENTS",
        dispatch_block=integ.dispatch_block(),
    )
    assert DISPATCH_PLACEHOLDER not in out
    assert "hermes chat -q -m" in out
    # the dispatch procedure injected for Hermes must not tell it to use a
    # subagent_type call (that mechanism does not exist in Hermes)
    assert "subagent_type" not in out


def test_opencode_render_substitutes_placeholder_with_opencode_block():
    raw = (COMMANDS_DIR / "implement.md").read_text(encoding="utf-8")
    integ = INTEGRATION_REGISTRY["opencode"]
    out = integ.process_template(
        raw, "opencode", "sh", "$ARGUMENTS",
        dispatch_block=integ.dispatch_block(),
    )
    assert DISPATCH_PLACEHOLDER not in out
    assert "subagent_type" in out


def test_empty_dispatch_block_drops_placeholder_cleanly():
    """A template still renders on an integration with no dispatch logic."""
    raw = "before __SPECKIT_DISPATCH_BLOCK__ after"
    out = IntegrationBase.process_template(raw, "x", "sh", "$ARGUMENTS")
    assert out == "before  after"


@pytest.mark.parametrize("key", ["hermes", "opencode"])
def test_installed_skills_are_dedicated_to_the_chosen_cli(key, tmp_path, monkeypatch):
    """End-to-end: installing for a CLI writes skills that carry only that
    CLI's dispatch mechanism — the init choice determines the dispatch."""
    from specify_cli.integrations.manifest import IntegrationManifest

    project = tmp_path / "proj"
    project.mkdir()
    # Hermes installs to ~/.hermes/skills (global) — redirect HOME so the test
    # never touches the real user directory.
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))

    integ = INTEGRATION_REGISTRY[key]
    manifest = IntegrationManifest(integ.key, project.resolve())
    created = integ.setup(project, manifest, script_type="sh")

    # The dispatch block is injected into the *workflow* commands (implement,
    # plan, tasks, ...). The `models` command is the config/discovery command
    # and legitimately documents every CLI's executor, so it is excluded from
    # the "dedicated to one CLI" check.
    workflow = [p for p in created if "models" not in Path(p).stem.lower()
                and "models" not in Path(p).parent.name.lower()]
    blob = "\n".join(Path(p).read_text(encoding="utf-8") for p in workflow)
    assert "DISPATCH n<level>" in blob
    if key == "hermes":
        assert "hermes chat -q -m" in blob
        assert "subagent_type" not in blob
    else:  # opencode
        assert "subagent_type" in blob
        assert "hermes chat" not in blob
