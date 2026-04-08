"""Tests for behavior.execution:agent deployment to agent-specific directories."""
import json
import yaml
import pytest
import tempfile
import shutil
from pathlib import Path
from textwrap import dedent

from specify_cli.agents import CommandRegistrar


@pytest.fixture
def project_root(tmp_path):
    root = tmp_path / "proj"
    (root / ".claude" / "skills").mkdir(parents=True)
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".specify").mkdir()
    (root / ".specify" / "init-options.json").write_text(
        json.dumps({"ai": "claude", "ai_skills": True, "script": "sh"})
    )
    return root


@pytest.fixture
def source_dir(tmp_path):
    src = tmp_path / "ext" / "commands"
    src.mkdir(parents=True)
    return src


class TestClaudeAgentDeployment:
    def _write_command(self, source_dir, filename, content):
        f = source_dir / filename
        f.write_text(content)
        return f

    def test_no_execution_behavior_deploys_to_skills(self, project_root, source_dir):
        self._write_command(source_dir, "hello.md", dedent("""\
            ---
            description: Test command
            ---
            Hello world
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "claude",
            [{"name": "speckit.test-ext.hello", "file": "hello.md"}],
            "test-ext", source_dir, project_root,
        )
        skill_file = project_root / ".claude" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
        agent_file = project_root / ".claude" / "agents" / "speckit-test-ext-hello.md"
        assert skill_file.exists()
        assert not agent_file.exists()

    def test_execution_agent_deploys_to_agents_dir(self, project_root, source_dir):
        self._write_command(source_dir, "analyzer.md", dedent("""\
            ---
            description: Analyze the codebase
            behavior:
              execution: agent
              capability: strong
              tools: read-only
            ---
            You are a codebase analysis specialist. $ARGUMENTS
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "claude",
            [{"name": "speckit.test-ext.analyzer", "file": "analyzer.md"}],
            "test-ext", source_dir, project_root,
        )
        agent_file = project_root / ".claude" / "agents" / "speckit-test-ext-analyzer.md"
        skill_file = project_root / ".claude" / "skills" / "speckit-test-ext-analyzer" / "SKILL.md"
        assert agent_file.exists()
        assert not skill_file.exists()

    def test_agent_file_has_correct_frontmatter(self, project_root, source_dir):
        self._write_command(source_dir, "analyzer.md", dedent("""\
            ---
            description: Analyze the codebase
            behavior:
              execution: agent
              capability: strong
              tools: read-only
            ---
            You are a specialist. $ARGUMENTS
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "claude",
            [{"name": "speckit.test-ext.analyzer", "file": "analyzer.md"}],
            "test-ext", source_dir, project_root,
        )
        content = (project_root / ".claude" / "agents" / "speckit-test-ext-analyzer.md").read_text()
        parts = content.split("---")
        fm = yaml.safe_load(parts[1])
        assert fm["name"] == "speckit-test-ext-analyzer"
        assert fm["description"] == "Analyze the codebase"
        assert fm.get("model") == "claude-opus-4-6"        # from capability: strong
        assert fm.get("tools") == "Read Grep Glob"         # from tools: read-only
        # These must NOT appear in agent definition files
        assert "user-invocable" not in fm
        assert "disable-model-invocation" not in fm
        assert "context" not in fm
        assert "behavior" not in fm

    def test_agent_file_body_is_system_prompt(self, project_root, source_dir):
        self._write_command(source_dir, "analyzer.md", dedent("""\
            ---
            description: Analyze the codebase
            behavior:
              execution: agent
            ---
            You are a specialist. $ARGUMENTS
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "claude",
            [{"name": "speckit.test-ext.analyzer", "file": "analyzer.md"}],
            "test-ext", source_dir, project_root,
        )
        content = (project_root / ".claude" / "agents" / "speckit-test-ext-analyzer.md").read_text()
        body = "---".join(content.split("---")[2:]).strip()
        assert "You are a specialist" in body

    def test_execution_isolated_deploys_to_skills_not_agents(self, project_root, source_dir):
        self._write_command(source_dir, "hello.md", dedent("""\
            ---
            description: Test isolated
            behavior:
              execution: isolated
            ---
            Hello
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "claude",
            [{"name": "speckit.test-ext.hello", "file": "hello.md"}],
            "test-ext", source_dir, project_root,
        )
        skill_file = project_root / ".claude" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
        agent_file = project_root / ".claude" / "agents" / "speckit-test-ext-hello.md"
        assert skill_file.exists()
        assert not agent_file.exists()

    def test_unregister_removes_agent_file(self, project_root, source_dir):
        self._write_command(source_dir, "analyzer.md", dedent("""\
            ---
            description: Test
            behavior:
              execution: agent
            ---
            Body
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "claude",
            [{"name": "speckit.test-ext.analyzer", "file": "analyzer.md"}],
            "test-ext", source_dir, project_root,
        )
        agent_file = project_root / ".claude" / "agents" / "speckit-test-ext-analyzer.md"
        assert agent_file.exists()

        registrar.unregister_commands(
            {"claude": ["speckit.test-ext.analyzer"]},
            project_root,
        )
        assert not agent_file.exists()


class TestCopilotAgentDeployment:
    """behavior.execution:agent on Copilot injects mode: and tools: into .agent.md frontmatter."""

    def _setup_copilot_project(self, tmp_path):
        root = tmp_path / "proj"
        (root / ".github" / "agents").mkdir(parents=True)
        (root / ".github" / "prompts").mkdir(parents=True)
        (root / ".specify").mkdir()
        (root / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "copilot", "script": "sh"})
        )
        return root

    def test_copilot_type_agent_injects_mode(self, tmp_path):
        root = self._setup_copilot_project(tmp_path)
        src = tmp_path / "ext" / "commands"
        src.mkdir(parents=True)
        (src / "analyzer.md").write_text(dedent("""\
            ---
            description: Analyze codebase
            behavior:
              execution: agent
              tools: read-only
            ---
            Analyze $ARGUMENTS
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "copilot",
            [{"name": "speckit.test-ext.analyzer", "file": "analyzer.md"}],
            "test-ext", src, root,
        )
        agent_file = root / ".github" / "agents" / "speckit.test-ext.analyzer.agent.md"
        assert agent_file.exists()
        content = agent_file.read_text()
        parts = content.split("---")
        fm = yaml.safe_load(parts[1])
        assert fm.get("mode") == "agent"
        assert "read_file" in fm.get("tools", [])

    def test_copilot_type_command_no_tools_injected(self, tmp_path):
        root = self._setup_copilot_project(tmp_path)
        src = tmp_path / "ext" / "commands"
        src.mkdir(parents=True)
        (src / "hello.md").write_text("---\ndescription: Hello\n---\nHello")
        registrar = CommandRegistrar()
        registrar.register_commands(
            "copilot",
            [{"name": "speckit.test-ext.hello", "file": "hello.md"}],
            "test-ext", src, root,
        )
        agent_file = root / ".github" / "agents" / "speckit.test-ext.hello.agent.md"
        content = agent_file.read_text()
        parts = content.split("---")
        fm = yaml.safe_load(parts[1]) or {}
        assert "mode" not in fm
        assert "tools" not in fm
