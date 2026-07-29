"""Contract tests for the model discovery and fallback command templates."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS_TEMPLATE = ROOT / "templates" / "commands" / "models.md"
IMPLEMENT_TEMPLATE = ROOT / "templates" / "commands" / "implement.md"


def test_models_command_separates_runtime_agent_from_installed_integration():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "Runtime agent" in content
    assert "Installed Spec Kit integration" in content
    assert "does **not** prove which agent is hosting this conversation" in content
    assert '"runtime"' in content
    assert '"integration"' in content


def test_models_command_requires_first_party_catalog_evidence():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "Do **not** derive a catalog from the agent name" in content
    assert "A help page showing only a `--model` option is not a model catalog" in content
    assert "Never create `models.json` from guesses" in content
    assert '"discovery"' in content
    assert '"mechanism"' in content
    assert '"tier": "<5 | 4 | 3 | 2 | 1>"' in content


def test_models_command_defines_ordered_fallback_candidates():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "primary first, then alternatives in fallback order" in content
    assert "independent provider/quota route" in content
    assert "preserve the task state and retry with the next candidate" in content
    assert "Do not hide code/test failures by switching models" in content
    assert "dispatch_strategy" not in content
    assert "round_robin" not in content


def test_models_command_requires_executor_for_every_assignment():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "Resolve an executor for every assigned model" in content
    assert '"executors"' in content
    assert "Every assigned ID has exactly one `executors` entry" in content
    # the concrete executor mechanics are CLI-specific and injected from each
    # integration's executor_block(); the raw template only carries the
    # placeholder so no single CLI's mechanism leaks into another's skill.
    assert "__SPECKIT_EXECUTOR_BLOCK__" in content
    assert '"mode": "cli"' not in content
    assert '"argv"' not in content


def test_models_command_supports_cli_subprocess_executor_for_hermes():
    """The Hermes executor block (injected into the models skill on install)
    dispatches via a same-CLI subprocess that pins the model with -m."""
    from specify_cli.integrations.dispatch_blocks import HERMES_EXECUTOR_BLOCK

    block = HERMES_EXECUTOR_BLOCK
    assert "cli_subprocess" in block
    assert "hermes chat -q -m" in block
    assert "no in-session per-task model selector" in block
    assert "same-CLI" in block
    assert '"command": "hermes chat -q -m' in block
    # dedicated to Hermes: no OpenCode agent mechanism leaks in
    assert "subagent_type" not in block


def test_models_hermes_render_is_hermes_only():
    """Rendering models.md for Hermes yields a skill that documents only the
    Hermes executor route — never subagent_type."""
    from specify_cli.integrations import INTEGRATION_REGISTRY

    raw = MODELS_TEMPLATE.read_text(encoding="utf-8")
    ig = INTEGRATION_REGISTRY["hermes"]
    out = ig.process_template(
        raw, "hermes", "py", "$ARGUMENTS",
        dispatch_block=ig.dispatch_block(),
        executor_block=ig.executor_block(),
    )
    assert "__SPECKIT_EXECUTOR_BLOCK__" not in out
    assert "hermes chat -q -m" in out
    assert "subagent_type" not in out


def test_models_command_requires_pinned_agent_on_dispatch():
    """OpenCode's executor block pins the model via a named subagent."""
    from specify_cli.integrations.dispatch_blocks import OPENCODE_EXECUTOR_BLOCK

    block = OPENCODE_EXECUTOR_BLOCK
    assert "subagent_type" in block
    assert "named subagent" in block
    # dedicated to OpenCode: no Hermes subprocess mechanism leaks in
    assert "hermes chat" not in block


def test_models_command_dispatches_without_a_verification_gate():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    # the raw template must not carry stale verification-state schema fields
    assert '"verified"' not in content
    assert "pending_restart" not in content
    # dispatch is optimistic — the CLI executor blocks say so explicitly
    from specify_cli.integrations.dispatch_blocks import (
        HERMES_EXECUTOR_BLOCK,
        OPENCODE_EXECUTOR_BLOCK,
    )

    assert "optimistic" in OPENCODE_EXECUTOR_BLOCK
    assert "No agent config is created and no restart is needed" in HERMES_EXECUTOR_BLOCK


def test_models_command_configures_opencode_agents_without_claiming_hot_reload():
    """OpenCode's executor block scaffolds pinned agents in the singular
    `agent/` dir and never claims hot reload."""
    from specify_cli.integrations.dispatch_blocks import OPENCODE_EXECUTOR_BLOCK

    block = OPENCODE_EXECUTOR_BLOCK
    # singular `agent/` — OpenCode silently ignores a plural `agents/` directory
    assert ".opencode/agent/<name>.md" in block
    assert ".opencode/agents/" not in block
    assert "opencode agent list" in block
    assert "tell the user to restart" in block
    assert "the fallback chain moves to the next candidate" in block


def test_models_command_mandates_agent_creation_when_runtime_supports_pinned_models():
    """When the host pins models via named agents (OpenCode), the executor
    block requires proposing one per assigned model."""
    from specify_cli.integrations.dispatch_blocks import OPENCODE_EXECUTOR_BLOCK

    block = OPENCODE_EXECUTOR_BLOCK
    assert "propose a stable agent" in block
    assert "without a matching agent" in block


def test_models_command_keeps_execution_inside_the_current_host():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    # The generic (default) executor block keeps execution inside the host and
    # forbids launching a different vendor's CLI.
    from specify_cli.integrations.dispatch_blocks import GENERIC_EXECUTOR_BLOCK

    assert "All task execution must remain inside the agent or CLI hosting this conversation" in GENERIC_EXECUTOR_BLOCK
    assert "Never launch a *different* vendor's CLI" in GENERIC_EXECUTOR_BLOCK
    # the raw template stays CLI-neutral (mechanism injected per-CLI)
    assert "__SPECKIT_EXECUTOR_BLOCK__" in content
    assert "subagent_type" not in content


def test_models_command_covers_every_registered_integration():
    """Every registered integration renders a models skill with a resolved
    executor block (no leftover placeholder), so none is left without a
    dispatch mechanism."""
    from specify_cli.integrations import INTEGRATION_REGISTRY

    raw = MODELS_TEMPLATE.read_text(encoding="utf-8")
    for key, ig in INTEGRATION_REGISTRY.items():
        out = ig.process_template(
            raw, key, "sh", "$ARGUMENTS",
            dispatch_block=ig.dispatch_block(),
            executor_block=ig.executor_block(),
        )
        assert "__SPECKIT_EXECUTOR_BLOCK__" not in out, key
        assert '"executors"' in out, key


def test_every_workflow_command_carries_orchestrator_dispatch():
    """Every command that consumes models.json must dispatch its own steps.

    `constitution` is exempt (it never reads models.json) and `models` is the
    command that writes the configuration in the first place.
    """
    commands_dir = ROOT / "templates" / "commands"
    exempt = {"constitution.md", "models.md"}

    for template in sorted(commands_dir.glob("*.md")):
        if template.name in exempt:
            continue
        content = template.read_text(encoding="utf-8")
        assert "Orchestrator dispatch (MANDATORY" in content, template.name
        assert "by_complexity" in content, template.name
        # The concrete dispatch procedure is CLI-specific and injected at
        # install time from each integration's dispatch_block(). The template
        # itself carries only the placeholder — never a hard-coded mechanism,
        # so no single CLI's route (e.g. subagent_type) leaks into every skill.
        assert "__SPECKIT_DISPATCH_BLOCK__" in content, template.name
        assert "subagent_type" not in content, template.name
        assert "Self-check before every" in content, template.name
        assert "no permission to create or edit project artifacts" in content, template.name
        # the project config wins and a denied global read must not abort
        assert "never abort the command because of it" in content, template.name


def test_implement_command_continues_with_ordered_fallback_state():
    content = IMPLEMENT_TEMPLATE.read_text(encoding="utf-8")

    assert "remaining models are ordered fallbacks, not load-balancing targets" in content
    assert "preserve verified progress and retry with the next candidate" in content
    assert "changed files, test results, completed work, and remaining work" in content
    assert "Do not switch models merely to mask an ordinary code or test failure" in content
    assert "Resolve the candidate in `executors`" in content
    assert "Never launch a *different* vendor's agent CLI to execute a task" in content
    # the executor detail defers to the injected, CLI-specific dispatch procedure
    assert "orchestrator dispatch procedure defined at the top of this command" in content
    assert "There is no verification gate" in content
    assert "pause and provide the recorded model-switch/continuation instructions" in content
