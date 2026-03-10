"""
Tests for Phase 7: Agent Creation functionality.

Tests for template generator, auto-improvement, handoff, and skill workflow.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from specify_cli.memory.agents.template_generator import AgentTemplateGenerator
from specify_cli.memory.agents.auto_improvement import AutoImprovementSystem
from specify_cli.memory.agents.auto_handoff import AutoHandoffSystem
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow
from specify_cli.memory.agents.agent_templates import (
    get_template,
    list_templates,
    get_all_templates,
    create_custom_template
)


class TestAgentTemplateGenerator:
    """Test agent template generator."""

    def test_initialization(self):
        """Test generator initialization."""
        gen = AgentTemplateGenerator()
        assert gen.memory_root == Path.home() / ".claude" / "memory"

    def test_generate_agent_basic(self):
        """Test basic agent generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = AgentTemplateGenerator(memory_root=Path(tmpdir))

            files = gen.generate_agent(
                agent_name="test-agent",
                role="Test Agent Role"
            )

            assert "agents" in files
            assert "soul" in files
            assert "user" in files
            assert "memory" in files
            assert "memory_dir" in files

            # Check files exist
            assert files["agents"].exists()
            assert files["soul"].exists()
            assert files["user"].exists()
            assert files["memory"].exists()
            assert files["memory_dir"].is_dir()

    def test_generate_agent_with_team(self):
        """Test agent generation with team."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = AgentTemplateGenerator(memory_root=Path(tmpdir))

            files = gen.generate_agent(
                agent_name="team-agent",
                role="Team Agent",
                team=["agent1", "agent2"],
                skills=["skill1", "skill2"]
            )

            # Check AGENTS.md contains team
            content = files["agents"].read_text()
            assert "agent1" in content
            assert "agent2" in content
            assert "skill1" in content
            assert "skill2" in content

    def test_generate_agent_default_personality(self):
        """Test default personality based on agent name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = AgentTemplateGenerator(memory_root=Path(tmpdir))

            # Frontend agent - check for personality section
            files = gen.generate_agent(
                agent_name="frontend-dev",
                role="Frontend Developer"
            )
            content = files["soul"].read_text()
            assert "## Personality" in content
            assert len(content) > 100  # Has substantial content

            # Backend agent - check for personality section
            files = gen.generate_agent(
                agent_name="backend-dev",
                role="Backend Developer"
            )
            content = files["soul"].read_text()
            assert "## Personality" in content

    def test_memory_files_created(self):
        """Test that memory subdirectory files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = AgentTemplateGenerator(memory_root=Path(tmpdir))

            files = gen.generate_agent(
                agent_name="memory-test",
                role="Memory Test"
            )

            memory_dir = files["memory_dir"]

            # Check all memory files exist
            assert (memory_dir / "lessons.md").exists()
            assert (memory_dir / "patterns.md").exists()
            assert (memory_dir / "projects-log.md").exists()
            assert (memory_dir / "architecture.md").exists()
            assert (memory_dir / "handoff.md").exists()


class TestAutoImprovementSystem:
    """Test auto-improvement system."""

    def test_initialization(self):
        """Test system initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            memory_dir = agent_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            sys = AutoImprovementSystem("test-project", memory_root=agent_dir)
            assert sys.project_id == "test-project"

    def test_record_first_error(self):
        """Test recording first error creates pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            memory_dir = agent_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            sys = AutoImprovementSystem("test-project", memory_root=agent_dir)

            result = sys.record_error(
                error_type="CORS",
                error_message="CORS policy blocked request",
                solution="Add proper CORS headers"
            )

            assert result is True

            # Check pattern file created
            patterns_file = Path(tmpdir) / "test-project" / "memory" / "patterns.md"
            assert patterns_file.exists()

            content = patterns_file.read_text()
            assert "CORS" in content
            assert "(repeat: 1)" in content

    def test_record_repeated_error(self):
        """Test that repeated errors increment count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            memory_dir = agent_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            sys = AutoImprovementSystem("test-project", memory_root=agent_dir)

            # First error
            sys.record_error(
                error_type="JWT",
                error_message="Token expired",
                solution="Implement refresh token flow"
            )

            # Same error again
            sys.record_error(
                error_type="JWT",
                error_message="Token expired",
                solution="Implement refresh token flow"
            )

            # Check count increased
            patterns_file = Path(tmpdir) / "test-project" / "memory" / "patterns.md"
            content = patterns_file.read_text()
            assert "(repeat: 2)" in content

    def test_three_repeats_promotes_to_lesson(self):
        """Test that 3 repeats promote to lesson."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            memory_dir = agent_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            sys = AutoImprovementSystem("test-project", memory_root=agent_dir)

            # Record same error 3 times
            for _ in range(3):
                sys.record_error(
                    error_type="Database",
                    error_message="Connection pool exhausted",
                    solution="Increase pool size"
                )

            # Check lesson file created
            lessons_file = Path(tmpdir) / "test-project" / "memory" / "lessons.md"
            assert lessons_file.exists()

            content = lessons_file.read_text()
            assert "Database" in content
            assert "Rule:" in content

    def test_get_pattern_summary(self):
        """Test pattern summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            memory_dir = agent_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            sys = AutoImprovementSystem("test-project", memory_root=agent_dir)

            # Record some patterns
            sys.record_error("Error1", "Msg1", "Sol1")
            sys.record_error("Error1", "Msg1", "Sol1")
            sys.record_error("Error2", "Msg2", "Sol2")

            summary = sys.get_pattern_summary()

            assert summary["total_patterns"] == 2
            assert "Error1" in summary["by_type"]


class TestAutoHandoffSystem:
    """Test auto handoff system."""

    def test_initialization(self):
        """Test system initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory").mkdir(parents=True, exist_ok=True)
            
            sys = AutoHandoffSystem("test-project", memory_root=agent_dir)
            assert sys.project_id == "test-project"

    def test_create_handoff(self):
        """Test handoff file creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory").mkdir(parents=True, exist_ok=True)
            
            sys = AutoHandoffSystem("test-project", memory_root=agent_dir)

            result = sys.create_handoff(
                active_tasks=[
                    {"title": "Task 1", "status": "in_progress", "description": "Test task"}
                ],
                blocked_issues=[
                    {"type": "CORS", "description": "CORS error"}
                ]
            )

            assert result is True

            # Check handoff file created
            handoff_file = Path(tmpdir) / "test-project" / "memory" / "handoff.md"
            assert handoff_file.exists()

            content = handoff_file.read_text()
            assert "Task 1" in content
            assert "CORS" in content
            assert "Last Updated" in content

    def test_restore_context(self):
        """Test context restoration from handoff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory").mkdir(parents=True, exist_ok=True)
            
            sys = AutoHandoffSystem("test-project", memory_root=agent_dir)

            # Create handoff first
            sys.create_handoff(
                active_tasks=[{"title": "Active Task"}]
            )

            # Restore context
            context = sys.restore_context()

            assert "last_session" in context
            assert "active_tasks" in context
            assert len(context["active_tasks"]) > 0

    def test_handoff_contains_headers(self):
        """Test that handoff includes memory headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "test-project"
            agent_dir.mkdir(parents=True, exist_ok=True)
            memory_dir = agent_dir / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            sys = AutoHandoffSystem("test-project", memory_root=agent_dir)
            sys.create_handoff()

            handoff_file = memory_dir / "handoff.md"
            content = handoff_file.read_text()

            # Check handoff structure exists
            assert "Session Handoff" in content
            assert "Last Updated" in content
            assert "Memory Access" in content


class TestSkillCreationWorkflow:
    """Test skill creation workflow."""

    def test_initialization(self):
        """Test workflow initialization."""
        workflow = SkillCreationWorkflow()
        assert workflow.template_generator is not None

    def test_search_agents(self):
        """Test agent search."""
        workflow = SkillCreationWorkflow()

        # Mock SkillsMP integration
        with patch.object(workflow, 'skillsmp_integration') as mock_smp:
            mock_smp.search_skills.return_value = [
                {"title": "Test Agent", "description": "Test", "github_stars": 10}
            ]

            results = workflow.search_agents("test query")

            assert results["query"] == "test query"
            assert results["found"] is True

    def test_present_options(self):
        """Test options presentation."""
        workflow = SkillCreationWorkflow()

        results = {
            "query": "frontend",
            "found": True,
            "skillsmp": [
                {"title": "React Agent", "description": "React development", "github_stars": 50}
            ],
            "github": []  # Add missing key
        }

        output = workflow.present_options(results)

        assert "React Agent" in output
        assert "Options" in output or "options" in output.lower()

    def test_create_agent_from_requirements(self):
        """Test creating agent from requirements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = SkillCreationWorkflow(memory_root=Path(tmpdir))

            files = workflow.create_agent_from_requirements(
                agent_name="workflow-test",
                requirements={
                    "role": "Test Role",
                    "personality": "Test Personality",
                    "skills": ["skill1", "skill2"]
                }
            )

            assert "agents" in files
            assert files["agents"].exists()

    def test_get_agent_template(self):
        """Test getting predefined template."""
        workflow = SkillCreationWorkflow()

        template = workflow.get_agent_template("frontend")

        assert "role" in template
        assert "skills" in template
        assert len(template["skills"]) > 0


class TestAgentTemplates:
    """Test agent templates module."""

    def test_list_templates(self):
        """Test listing available templates."""
        templates = list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "frontend-dev" in templates
        assert "backend-dev" in templates

    def test_get_template(self):
        """Test getting specific template."""
        template = get_template("frontend-dev")

        assert template["name"] == "frontend-dev"
        assert "role" in template
        assert "personality" in template
        assert "skills" in template
        assert "team" in template

    def test_get_invalid_template(self):
        """Test getting invalid template raises error."""
        with pytest.raises(KeyError):
            get_template("invalid-template-name")

    def test_get_all_templates(self):
        """Test getting all templates."""
        templates = get_all_templates()
        assert isinstance(templates, dict)
        assert len(templates) >= 5

    def test_create_custom_template(self):
        """Test creating custom template."""
        custom = create_custom_template(
            name="custom-agent",
            role="Custom Role",
            personality="Custom personality",
            skills=["skill1"],
            team=["agent1"]
        )

        assert custom["name"] == "custom-agent"
        assert custom["role"] == "Custom Role"
        assert len(custom["skills"]) == 1
        assert len(custom["team"]) == 1


class TestAgentCreationIntegration:
    """Integration tests for agent creation."""

    def test_full_agent_creation_workflow(self):
        """Test complete agent creation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # AgentTemplateGenerator creates in {tmpdir}/agents/{name}/
            agents_dir = Path(tmpdir) / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            agent_dir = agents_dir / "integration-test"
            
            # 1. Generate agent
            gen = AgentTemplateGenerator(memory_root=agents_dir)
            files = gen.generate_agent(
                agent_name="integration-test",
                role="Integration Test Agent",
                skills=["Testing"]
            )

            # 2. Record error (auto-improvement)
            # AutoImprovementSystem expects the agent directory
            ai = AutoImprovementSystem("integration-test", memory_root=agent_dir)
            ai.record_error(
                error_type="TestError",
                error_message="Test error message",
                solution="Test solution"
            )

            # 3. Create handoff
            ah = AutoHandoffSystem("integration-test", memory_root=agent_dir)
            ah.create_handoff()

            # Verify all files exist
            # Agent is created in {tmpdir}/agents/integration-test/
            memory_dir = Path(tmpdir) / "agents" / "integration-test" / "memory"
            assert (memory_dir / "patterns.md").exists()
            assert (memory_dir / "handoff.md").exists()

    def test_agent_template_then_workflow(self):
        """Test using template then skill workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / "backend-test"
            agent_dir.mkdir(parents=True, exist_ok=True)
            # Get template
            template = get_template("backend-dev")

            # Create agent with template
            workflow = SkillCreationWorkflow(memory_root=Path(tmpdir))
            files = workflow.create_agent_from_requirements(
                agent_name="backend-test",
                requirements=template
            )

            # Verify backend-specific skills in AGENTS.md
            agents_content = files["agents"].read_text()
            assert "API" in agents_content.lower() or "database" in agents_content.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
