"""Tests for the Docker Agent integration."""


from specify_cli.integrations import get_integration
from specify_cli.integrations.base import SkillsIntegration
from specify_cli.integrations.docker_agent import DockerAgentIntegration


def test_registered_metadata():
    integration = get_integration("docker-agent")

    assert isinstance(integration, DockerAgentIntegration)
    assert isinstance(integration, SkillsIntegration)
    assert integration.config["name"] == "Docker Agent"
    assert integration.config["folder"] == ".docker-agent/"
    assert integration.config["commands_subdir"] == "skills"
    assert integration.config["requires_cli"] is True
    assert integration.registrar_config["dir"] == ".docker-agent/skills"
    assert integration.registrar_config["format"] == "markdown"
    assert integration.registrar_config["args"] == "$ARGUMENTS"
    assert integration.registrar_config["extension"] == "/SKILL.md"
    assert integration.multi_install_safe is True
    assert integration.CANONICAL_TO_NATIVE == {
        "session_start": "session_start",
        "pre_tool_use": "pre_tool_use",
        "post_tool_use": "post_tool_use",
        "session_end": "session_end",
        "user_prompt_submit": "user_prompt_submit",
        "stop": "stop",
    }


def test_build_exec_args_without_config(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)

    args = DockerAgentIntegration().build_exec_args("/speckit-specify build an API")

    assert args == [
        "docker",
        "agent",
        "run",
        "--exec",
        "--json",
        "/speckit-specify build an API",
    ]


def test_uses_standalone_executable(monkeypatch):
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/docker-agent" if name == "docker-agent" else None,
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args[:4] == ["docker-agent", "run", "--exec", "prompt"]


def test_standalone_executable_has_priority(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker-agent")

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args[:3] == ["docker-agent", "run", "--exec"]


def test_extra_args_can_supply_agent_config(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml"
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == [
        "docker",
        "agent",
        "run",
        "--exec",
        "./agent.yaml",
        "prompt",
    ]
