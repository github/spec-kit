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

    def test_copilot_agent_no_tools_key_omits_tools(self, tmp_path):
        root = self._setup_copilot_project(tmp_path)
        src = tmp_path / "ext" / "commands"
        src.mkdir(parents=True)
        (src / "worker.md").write_text(dedent("""\
            ---
            description: Worker agent
            behavior:
              execution: agent
            ---
            Do work
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "copilot",
            [{"name": "speckit.test-ext.worker", "file": "worker.md"}],
            "test-ext", src, root,
        )
        agent_file = root / ".github" / "agents" / "speckit.test-ext.worker.agent.md"
        content = agent_file.read_text()
        parts = content.split("---")
        fm = yaml.safe_load(parts[1]) or {}
        assert fm.get("mode") == "agent"
        assert "tools" not in fm

    def test_copilot_agents_override_survives(self, tmp_path):
        root = self._setup_copilot_project(tmp_path)
        src = tmp_path / "ext" / "commands"
        src.mkdir(parents=True)
        (src / "custom.md").write_text(dedent("""\
            ---
            description: Custom agent
            behavior:
              execution: agent
            agents:
              copilot:
                someCustomKey: someValue
            ---
            Do custom work
        """))
        registrar = CommandRegistrar()
        registrar.register_commands(
            "copilot",
            [{"name": "speckit.test-ext.custom", "file": "custom.md"}],
            "test-ext", src, root,
        )
        agent_file = root / ".github" / "agents" / "speckit.test-ext.custom.agent.md"
        content = agent_file.read_text()
        parts = content.split("---")
        fm = yaml.safe_load(parts[1]) or {}
        assert fm.get("someCustomKey") == "someValue"


class TestEndToEnd:
    """Full pipeline: extension with behavior.execution:agent → correct files deployed."""

    def test_extension_with_agent_command_deploys_correctly(self, tmp_path):
        """An extension declaring execution:agent deploys to .claude/agents/, not skills."""
        from specify_cli.extensions import ExtensionManager

        project_root = tmp_path / "proj"
        (project_root / ".claude" / "skills").mkdir(parents=True)
        (project_root / ".claude" / "agents").mkdir(parents=True)
        (project_root / ".specify").mkdir()
        (project_root / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "script": "sh"})
        )

        # Create extension directory with manifest + command
        ext_dir = tmp_path / "revenge"
        (ext_dir / "commands").mkdir(parents=True)
        (ext_dir / "extension.yml").write_text(yaml.dump({
            "schema_version": "1.0",
            "extension": {
                "id": "revenge",
                "name": "Revenge",
                "version": "1.0.0",
                "description": "Reverse engineering extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.revenge.extract",
                        "file": "commands/extract.md",
                        "description": "Run extraction pipeline",
                    },
                    {
                        "name": "speckit.revenge.analyzer",
                        "file": "commands/analyzer.md",
                        "description": "Codebase analyzer subagent",
                    },
                ]
            },
        }))

        # Orchestrator command (no execution: → stays a skill)
        (ext_dir / "commands" / "extract.md").write_text(dedent("""\
            ---
            description: Run extraction pipeline
            behavior:
              invocation: automatic
            ---
            Run the extraction pipeline for $ARGUMENTS
        """))

        # Analyzer subagent (execution:agent → .claude/agents/)
        (ext_dir / "commands" / "analyzer.md").write_text(dedent("""\
            ---
            description: Codebase analyzer subagent
            behavior:
              execution: agent
              capability: strong
              tools: read-only
            ---
            You are a codebase analysis specialist.
            Analyze the codebase at $ARGUMENTS and return structured findings.
        """))

        # Install extension
        manager = ExtensionManager(project_root)
        manager.install_from_directory(ext_dir, speckit_version="0.1.0")

        # extract → .claude/skills/ (no execution: → command type)
        skill_file = project_root / ".claude" / "skills" / "speckit-revenge-extract" / "SKILL.md"
        assert skill_file.exists(), "extract should deploy as skill"
        skill_fm = yaml.safe_load(skill_file.read_text().split("---")[1])
        assert skill_fm.get("disable-model-invocation") is False  # behavior: invocation: automatic

        # analyzer → .claude/agents/ (execution:agent)
        agent_file = project_root / ".claude" / "agents" / "speckit-revenge-analyzer.md"
        assert agent_file.exists(), "analyzer should deploy as agent definition"
        agent_fm = yaml.safe_load(agent_file.read_text().split("---")[1])
        assert agent_fm.get("model") == "claude-opus-4-6"      # capability: strong
        assert agent_fm.get("tools") == "Read Grep Glob"        # tools: read-only
        assert "user-invocable" not in agent_fm
        assert "disable-model-invocation" not in agent_fm
        assert "behavior" not in agent_fm

        # analyzer must NOT also be in skills dir
        skill_analyzer = project_root / ".claude" / "skills" / "speckit-revenge-analyzer" / "SKILL.md"
        assert not skill_analyzer.exists()
