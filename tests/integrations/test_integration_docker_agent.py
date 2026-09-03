"""Tests for the Docker Agent integration."""

import pytest

from specify_cli.integrations.docker_agent import DockerAgentIntegration

from .test_integration_base_skills import SkillsIntegrationTests


class TestDockerAgentIntegration(SkillsIntegrationTests):
    KEY = "docker-agent"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"

    def test_multi_install_is_opt_in(self):
        assert DockerAgentIntegration().multi_install_safe is False


def test_extra_args_are_applied_to_build_exec_args(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS",
        "./agent.yaml --agent root --model openai/gpt-5",
    )
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/docker" if name == "docker" else None,
    )
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == [
        "docker",
        "agent",
        "run",
        "--exec",
        "./agent.yaml",
        "--agent",
        "root",
        "--model",
        "openai/gpt-5",
        "--",
        "prompt",
    ]


def test_per_step_runtime_config_builds_ordered_argv(monkeypatch):
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False)
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/docker-agent" if name == "docker-agent" else None,
    )

    args = DockerAgentIntegration().build_exec_args(
        "prompt",
        output_json=False,
        integration_args=["./agent.yaml"],
        integration_options={
            "agent": "root",
            "safety": "balanced",
            "model": "openai/gpt-5",
        },
    )

    assert args == [
        "docker-agent",
        "run",
        "--exec",
        "./agent.yaml",
        "--agent",
        "root",
        "--safety",
        "balanced",
        "--model",
        "openai/gpt-5",
        "--",
        "prompt",
    ]


def test_per_step_args_precede_legacy_extra_flags(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "--hide-tool-results"
    )
    monkeypatch.setattr("shutil.which", lambda name: None)

    args = DockerAgentIntegration().build_exec_args(
        "prompt",
        output_json=False,
        integration_args=["./agent.yaml"],
    )

    assert args == [
        "docker-agent",
        "run",
        "--exec",
        "./agent.yaml",
        "--hide-tool-results",
        "--",
        "prompt",
    ]


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"unknown": "value"}, "unknown integration option"),
        ({"agent": ""}, "must be a non-empty string"),
        ({"safety": "unsafe"}, "must be one of"),
    ],
)
def test_per_step_runtime_options_are_validated(options, message):
    with pytest.raises(ValueError, match=message):
        DockerAgentIntegration().build_exec_args(
            "prompt",
            integration_args=["./agent.yaml"],
            integration_options=options,
        )


def test_per_step_runtime_args_reject_multiple_agent_references():
    with pytest.raises(ValueError, match="at most one"):
        DockerAgentIntegration().build_exec_args(
            "prompt",
            integration_args=["./first.yaml", "./second.yaml"],
        )


@pytest.mark.parametrize("integration_args", [[""], [42]])
def test_per_step_runtime_args_reject_malformed_values(integration_args):
    with pytest.raises(ValueError, match="non-empty strings"):
        DockerAgentIntegration().build_exec_args(
            "prompt",
            integration_args=integration_args,
        )


def test_prompt_is_passed_after_agent_config(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml"
    )
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/docker" if name == "docker" else None,
    )
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())

    args = DockerAgentIntegration().build_exec_args(
        "/speckit-specify prompt", output_json=False
    )

    assert args == [
        "docker",
        "agent",
        "run",
        "--exec",
        "./agent.yaml",
        "--",
        "/speckit-specify prompt",
    ]


def test_prompt_starting_with_flag_is_delimited(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setattr("shutil.which", lambda name: None)

    args = DockerAgentIntegration().build_exec_args("--help", output_json=False)

    assert args == ["docker-agent", "run", "--exec", "./agent.yaml", "--", "--help"]


def test_requires_agent_config(monkeypatch):
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False)
    with pytest.raises(ValueError, match="requires an agent configuration reference"):
        DockerAgentIntegration().build_exec_args("prompt", output_json=False)


def test_uses_standalone_executable(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/docker-agent" if name == "docker-agent" else None,
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["docker-agent", "run", "--exec", "./agent.yaml", "--", "prompt"]


def test_standalone_executable_has_priority(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker-agent")

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["docker-agent", "run", "--exec", "./agent.yaml", "--", "prompt"]


def test_executable_override(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", "/opt/docker-agent"
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["/opt/docker-agent", "run", "--exec", "./agent.yaml", "--", "prompt"]


def test_docker_executable_override_uses_agent_subcommand(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", "/opt/docker"
    )

    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: type("Result", (), {"returncode": 0})(),
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["/opt/docker", "agent", "run", "--exec", "./agent.yaml", "--", "prompt"]
