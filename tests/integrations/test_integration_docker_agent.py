"""Tests for the Docker Agent integration."""

import os
import subprocess
from unittest.mock import Mock

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

    def test_is_slash_skills_agent(self):
        """Docker Agent only installs `speckit-<name>/SKILL.md` skills, so the
        helper must agree with its own renderer with or without `ai_skills`
        (always slash, like Zed and Muse Code, which share that layout)."""
        from specify_cli._invocation_style import is_slash_skills_agent

        assert DockerAgentIntegration().build_command_invocation("plan") == "/speckit-plan"
        assert is_slash_skills_agent("docker-agent", True) is True
        assert is_slash_skills_agent("docker-agent", False) is True

    def test_hook_invocation_renders_the_hyphenated_form(self, tmp_path, monkeypatch):
        import specify_cli
        from specify_cli.extensions import HookExecutor

        monkeypatch.setattr(
            specify_cli,
            "load_init_options",
            lambda _root: {"ai": "docker-agent", "ai_skills": True},
        )

        rendered = HookExecutor(tmp_path)._render_hook_invocation("speckit.git.commit")

        assert rendered == "/speckit-git-commit"


def test_extra_args_are_applied_to_build_exec_args(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS",
        "./agent.yaml --agent root --model openai/gpt-5",
    )
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker" if name == "docker" else None,
    )
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == [
        "/usr/bin/docker",
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
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent" if name == "docker-agent" else None,
    )

    args = DockerAgentIntegration().build_exec_args(
        "prompt",
        output_json=False,
        integration_args=["./agent.yaml"],
        integration_options={
            "agent": "root",
            "safety": "balanced",
        },
        model="openai/gpt-5",
    )

    assert args == [
        "/usr/bin/docker-agent",
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


def test_per_step_args_ignore_legacy_extra_flags(monkeypatch):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "--hide-tool-results"
    )
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent",
    )

    args = DockerAgentIntegration().build_exec_args(
        "prompt",
        output_json=False,
        integration_args=["./agent.yaml"],
    )

    assert args == [
        "/usr/bin/docker-agent",
        "run",
        "--exec",
        "./agent.yaml",
        "--",
        "prompt",
    ]


@pytest.mark.parametrize("legacy_value", ["./global.yaml --hide-tool-results", '"broken'])
def test_per_step_args_override_legacy_extra_args(monkeypatch, legacy_value):
    monkeypatch.setenv(
        "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS",
        legacy_value,
    )
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent",
    )

    args = DockerAgentIntegration().build_exec_args(
        "prompt",
        output_json=False,
        integration_args=["./step.yaml"],
    )

    assert args == [
        "/usr/bin/docker-agent",
        "run",
        "--exec",
        "./step.yaml",
        "--",
        "prompt",
    ]


def test_command_step_model_is_the_only_model_source(monkeypatch):
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False)
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent",
    )

    args = DockerAgentIntegration().build_exec_args(
        "prompt",
        output_json=False,
        model="openai/gpt-5",
        integration_args=["./agent.yaml"],
    )

    assert args.count("--model") == 1
    assert args[args.index("--model") + 1] == "openai/gpt-5"


def test_integration_options_model_is_rejected():
    with pytest.raises(ValueError, match="command-step 'model' field"):
        DockerAgentIntegration().build_exec_args(
            "prompt",
            integration_args=["./agent.yaml"],
            integration_options={"model": "openai/gpt-5"},
        )


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
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker" if name == "docker" else None,
    )
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())

    args = DockerAgentIntegration().build_exec_args(
        "/speckit-specify prompt", output_json=False
    )

    assert args == [
        "/usr/bin/docker",
        "agent",
        "run",
        "--exec",
        "./agent.yaml",
        "--",
        "/speckit-specify prompt",
    ]


def test_prompt_starting_with_flag_is_delimited(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent",
    )

    args = DockerAgentIntegration().build_exec_args("--help", output_json=False)

    assert args == ["/usr/bin/docker-agent", "run", "--exec", "./agent.yaml", "--", "--help"]


def test_requires_agent_config(monkeypatch):
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", raising=False)
    with pytest.raises(ValueError, match="requires an agent configuration reference"):
        DockerAgentIntegration().build_exec_args("prompt", output_json=False)


def test_legacy_agent_config_cannot_resolve_to_empty_token_list(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", '""')

    with pytest.raises(ValueError, match="must start with an agent configuration"):
        DockerAgentIntegration().build_exec_args("prompt", output_json=False)


def test_uses_standalone_executable(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent" if name == "docker-agent" else None,
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["/usr/bin/docker-agent", "run", "--exec", "./agent.yaml", "--", "prompt"]


def test_standalone_executable_has_priority(monkeypatch):
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS", "./agent.yaml")
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: "/usr/bin/docker-agent",
    )

    args = DockerAgentIntegration().build_exec_args("prompt", output_json=False)

    assert args == ["/usr/bin/docker-agent", "run", "--exec", "./agent.yaml", "--", "prompt"]


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


@pytest.mark.parametrize("stream", [False, True])
def test_dispatch_rejects_checkout_local_executable(tmp_path, monkeypatch, stream):
    executable = tmp_path / ("docker-agent.exe" if os.name == "nt" else "docker-agent")
    executable.touch()
    executable.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("PATHEXT", ".exe")
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", raising=False)
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="", stderr=""))
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(NotImplementedError, match="does not support CLI dispatch"):
        DockerAgentIntegration().dispatch_command(
            "speckit.plan",
            project_root=tmp_path,
            stream=stream,
            integration_args=["./agent.yaml"],
        )

    run.assert_not_called()


def test_dispatch_preserves_explicit_checkout_local_override(tmp_path, monkeypatch):
    executable = tmp_path / ("docker-agent.exe" if os.name == "nt" else "docker-agent")
    executable.touch()
    executable.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", str(executable))
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="done", stderr=""))
    monkeypatch.setattr(subprocess, "run", run)

    result = DockerAgentIntegration().dispatch_command(
        "speckit.plan",
        project_root=tmp_path,
        stream=False,
        integration_args=["./agent.yaml"],
    )

    assert result == {"exit_code": 0, "stdout": "done", "stderr": ""}
    assert run.call_args.args[0][0] == str(executable)
    run.assert_called_once()


def test_dispatch_stops_after_failed_plugin_probe(tmp_path, monkeypatch):
    executable = tmp_path / ("docker.exe" if os.name == "nt" else "docker")
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", raising=False)
    monkeypatch.setattr(
        "specify_cli._utils._find_docker_executable",
        lambda name, **_kwargs: str(executable) if name == "docker" else None,
    )
    run = Mock(return_value=subprocess.CompletedProcess([], 1))
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(NotImplementedError, match="does not support CLI dispatch"):
        DockerAgentIntegration().dispatch_command(
            "speckit.plan",
            stream=False,
            integration_args=["./agent.yaml"],
        )

    run.assert_called_once_with(
        [str(executable), "agent", "version"],
        capture_output=True,
        check=False,
        timeout=5,
    )


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
@pytest.mark.parametrize("stream", [False, True])
def test_dispatch_excludes_runtime_project_from_another_cwd(
    tmp_path, monkeypatch, name, stream
):
    launch = tmp_path / "launch"
    launch.mkdir()
    project = tmp_path / "project"
    local_bin = project / "bin"
    local_bin.mkdir(parents=True)
    executable = local_bin / (f"{name}.exe" if os.name == "nt" else name)
    executable.touch()
    executable.chmod(0o755)
    monkeypatch.chdir(launch)
    monkeypatch.setenv("PATH", str(local_bin))
    monkeypatch.setenv("PATHEXT", ".exe")
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", raising=False)
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="", stderr=""))
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(NotImplementedError, match="does not support CLI dispatch"):
        DockerAgentIntegration().dispatch_command(
            "speckit.plan",
            project_root=project,
            stream=stream,
            integration_args=["./agent.yaml"],
        )

    run.assert_not_called()


@pytest.mark.parametrize("name", ["docker", "docker-agent"])
def test_dispatch_from_another_cwd_uses_external_install(tmp_path, monkeypatch, name):
    launch = tmp_path / "launch"
    launch.mkdir()
    project = tmp_path / "project"
    local_bin = project / "bin"
    local_bin.mkdir(parents=True)
    installed = tmp_path / "installed"
    installed.mkdir()
    filename = f"{name}.exe" if os.name == "nt" else name
    for directory in (local_bin, installed):
        executable = directory / filename
        executable.touch()
        executable.chmod(0o755)
    monkeypatch.chdir(launch)
    monkeypatch.setenv("PATH", os.pathsep.join([str(local_bin), str(installed)]))
    monkeypatch.setenv("PATHEXT", ".exe")
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", raising=False)
    run = Mock(return_value=subprocess.CompletedProcess([], 0, stdout="done", stderr=""))
    monkeypatch.setattr(subprocess, "run", run)

    result = DockerAgentIntegration().dispatch_command(
        "speckit.plan",
        project_root=project,
        stream=False,
        integration_args=["./agent.yaml"],
    )

    assert result == {"exit_code": 0, "stdout": "done", "stderr": ""}
    assert run.call_args.args[0][0] == str(installed / filename)
    assert run.call_args.kwargs["cwd"] == str(project)
    assert run.call_count == (2 if name == "docker" else 1)


def test_unavailable_executable_cannot_build_dispatch_args(monkeypatch):
    monkeypatch.delenv("SPECKIT_INTEGRATION_DOCKER_AGENT_EXECUTABLE", raising=False)
    monkeypatch.setenv("PATH", "")

    assert DockerAgentIntegration().build_exec_args(
        "prompt", integration_args=["./agent.yaml"]
    ) is None
