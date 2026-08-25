"""Tests for the Docker Agent integration."""

from specify_cli.integrations.docker_agent import DockerAgentIntegration

from .test_integration_base_skills import SkillsIntegrationTests


class TestDockerAgentIntegration(SkillsIntegrationTests):
    KEY = "docker-agent"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"

    def test_multi_install_is_opt_in(self):
        assert DockerAgentIntegration().multi_install_safe is False


def test_zero_config_dispatch_uses_stdin(monkeypatch, tmp_path):
    monkeypatch.setattr("shutil.which", lambda name: None)
    completed = type("CompletedProcess", (), {"returncode": 0})()
    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return completed

    monkeypatch.setattr(
        "specify_cli.integrations.docker_agent.subprocess.run", fake_run
    )

    result = DockerAgentIntegration().dispatch_command(
        "speckit.specify", "prompt", project_root=tmp_path
    )

    assert result["exit_code"] == 0
    assert captured["args"] == [
        "docker",
        "agent",
        "run",
        "--exec",
    ]
    assert captured["kwargs"]["input"] == "/speckit-specify prompt"

def test_uses_standalone_executable(monkeypatch):
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/bin/docker-agent" if name == "docker-agent" else None,
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["docker-agent", "run", "--exec"]

def test_standalone_executable_has_priority(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/docker-agent")

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["docker-agent", "run", "--exec"]

def test_executable_override(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", "/opt/docker-agent"
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["/opt/docker-agent", "run", "--exec"]


def test_docker_executable_override_uses_agent_subcommand(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", "/opt/docker"
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["/opt/docker", "agent", "run", "--exec"]
