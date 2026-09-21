"""OpenHands installation, invocation and headless dispatch contracts."""

import subprocess
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestOpenhandsIntegration(SkillsIntegrationTests):
    KEY = "openhands"
    FOLDER = ".openhands/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".openhands/skills"

    def test_multi_install_safe(self):
        assert get_integration(self.KEY).multi_install_safe is True

    @pytest.mark.parametrize("output_json", [True, False])
    def test_headless_dispatch(self, output_json):
        integration = get_integration(self.KEY)
        prompt = integration.build_command_invocation("speckit.git.commit", "a 'quoted' task")
        assert prompt == "/speckit-git-commit a 'quoted' task"
        assert integration.build_exec_args(prompt, output_json=output_json) == [
            "openhands", "--headless", "-t", prompt,
        ] + (["--json"] if output_json else [])

    def test_executable_and_extra_args(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_INTEGRATION_OPENHANDS_EXECUTABLE", "/path with spaces/openhands")
        monkeypatch.setenv("SPECKIT_INTEGRATION_OPENHANDS_EXTRA_ARGS", "--override-with-envs")
        assert get_integration(self.KEY).build_exec_args("task") == [
            "/path with spaces/openhands", "--headless", "-t", "task",
            "--override-with-envs", "--json",
        ]

    def test_unsupported_model_has_actionable_error(self):
        with pytest.raises(ValueError, match="LLM_MODEL"):
            get_integration(self.KEY).build_exec_args("task", model="some-model")

    @pytest.mark.parametrize("config", [
        {"integration_args": ["--unknown"]},
        {"integration_options": {"unknown": True}},
    ])
    def test_rejects_unsupported_runtime_config(self, config):
        with pytest.raises(ValueError, match="does not support per-step"):
            get_integration(self.KEY).build_exec_args("task", **config)

    def test_generated_skills_have_slash_triggers(self, tmp_path):
        integration = get_integration(self.KEY)
        integration.setup(tmp_path, IntegrationManifest(self.KEY, tmp_path))
        for path in (tmp_path / self.REGISTRAR_DIR).glob("*/SKILL.md"):
            metadata = yaml.safe_load(path.read_text().split("---", 2)[1])
            assert metadata["triggers"] == [f"/{metadata['name']}"]

    def test_post_processing_preserves_existing_triggers_and_body(self):
        integration = get_integration(self.KEY)
        content = "---\nname: speckit-example\ndescription: Example\ntriggers: [existing]\n---\n\nBody\n"
        result = integration.post_process_skill_content(content)
        metadata = yaml.safe_load(result.split("---", 2)[1])
        assert metadata["triggers"] == ["existing", "/speckit-example"]
        assert result.endswith("\n\nBody\n")
        assert integration.post_process_skill_content(result) == result

    @pytest.mark.parametrize("script_type", ["sh", "ps", "py"])
    def test_init_and_cli_uninstall(self, tmp_path, monkeypatch, script_type):
        project = tmp_path / "project"
        result = CliRunner().invoke(app, [
            "init", str(project), "--integration", self.KEY,
            "--ignore-agent-tools", "--script", script_type, "--non-interactive",
        ])
        assert result.exit_code == 0, result.output
        assert "/speckit-specify" in result.output
        assert "Start using skills" in result.output
        skill = project / self.REGISTRAR_DIR / "speckit-plan/SKILL.md"
        assert skill.exists()
        assert not (project / "AGENTS.md").exists()
        monkeypatch.chdir(project)
        result = CliRunner().invoke(app, ["integration", "uninstall", self.KEY])
        assert result.exit_code == 0, result.output
        assert not skill.exists()

    def test_dispatch_passes_workspace_and_returns_jsonl(self, tmp_path):
        integration = get_integration(self.KEY)
        output = '{"type":"action"}\n{"type":"observation"}\n'
        with patch("subprocess.run", return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout=output, stderr="",
        )) as run, patch("shutil.which", return_value=None):
            result = integration.dispatch_command(
                "speckit.specify", "Build a task tracker",
                project_root=tmp_path, stream=False,
            )
        argv = run.call_args.args[0]
        assert argv[:3] == ["openhands", "--headless", "-t"]
        assert "/speckit-specify Build a task tracker" in argv[3]
        assert argv[-1] == "--json"
        assert run.call_args.kwargs["cwd"] == str(tmp_path)
        assert result == {"exit_code": 0, "stdout": output, "stderr": ""}
