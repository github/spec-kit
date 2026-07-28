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
    assert "native_subagent" in content
    assert '"executors"' in content
    assert "Every model appearing in `by_complexity` must have an executor entry" in content
    assert "A `manual` executor is valid but cannot be used for autonomous fallback" in content
    assert "native_subagent`, `current_session`, or `manual`" in content
    assert '"mode": "cli"' not in content
    assert '"argv"' not in content


def test_models_command_dispatches_without_a_verification_gate():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "There is no verification gate" in content
    assert "No verification state is stored" in content
    assert '"verified"' not in content
    assert "pending_restart" not in content


def test_models_command_configures_opencode_agents_without_claiming_hot_reload():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "#### OpenCode" in content
    assert "select a configured agent name; do not claim direct model selection" in content
    assert ".opencode/agents/<name>.md" in content
    assert "Ask before creating or updating OpenCode agent files" in content
    assert "tell the user to restart" in content
    assert "the fallback chain simply moves to the next candidate" in content


def test_models_command_mandates_agent_creation_when_runtime_supports_pinned_models():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "MUST propose creating them for every assigned model that lacks a matching agent" in content
    assert "violates this contract" in content
    assert "you MUST propose a stable agent" in content
    assert "Do not skip this step and record `manual` instead" in content


def test_models_command_keeps_execution_inside_the_current_host():
    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    assert "These are verification branches, not claims" in content
    assert "All task execution must remain inside the agent or CLI hosting this conversation" in content
    assert "Never launch another agent CLI" in content
    assert "Do not use `codex exec`" in content
    assert "Never hand work to a companion CLI" in content
    assert "do not create guessed config files or commands" in content
    assert "Ask before creating agent configuration" in content


def test_models_command_covers_every_registered_integration():
    from specify_cli.integrations import INTEGRATION_REGISTRY

    content = MODELS_TEMPLATE.read_text(encoding="utf-8")

    for key in INTEGRATION_REGISTRY:
        assert f"`{key}`" in content


def test_implement_command_continues_with_ordered_fallback_state():
    content = IMPLEMENT_TEMPLATE.read_text(encoding="utf-8")

    assert "remaining models are ordered fallbacks, not load-balancing targets" in content
    assert "preserve verified progress and retry with the next candidate" in content
    assert "There is no verification gate" in content
    assert "changed files, test results, completed work, and remaining work" in content
    assert "Do not switch models merely to mask an ordinary code or test failure" in content
    assert "Resolve the candidate in `executors`" in content
    assert "Never launch an agent CLI or a second process of the current host" in content
    assert "pause and provide the recorded model-switch/continuation instructions" in content
