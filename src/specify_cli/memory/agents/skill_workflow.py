"""
Skill Creation Workflow - Search before create for agents.

Integrates with SkillsMP to find existing agents/skills before creating new ones.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..logging import get_logger
from ..skillsmp.integration import SkillsMPIntegration
from .template_generator import AgentTemplateGenerator


class SkillCreationWorkflow:
    """Workflow for creating agents with search-before-create pattern.

    Workflow:
    1. Define requirements (what agent needed)
    2. Search SkillsMP for existing agents
    3. Search GitHub as fallback
    4. Present options to user
    5a. Use existing agent OR
    5b. Create new agent with templates
    """

    def __init__(self, memory_root: Optional[Path] = None):
        """Initialize skill creation workflow.

        Args:
            memory_root: Root directory for memory files
        """
        self.logger = get_logger()
        self.memory_root = memory_root

        # Initialize components
        self.template_generator = AgentTemplateGenerator(memory_root=memory_root)
        self.skillsmp_integration = None

        # Try to initialize SkillsMP (optional)
        self._init_skillsmp()

    def _init_skillsmp(self) -> None:
        """Initialize SkillsMP integration if available."""
        try:
            self.skillsmp_integration = SkillsMPIntegration(
                global_home=self.memory_root or Path.home() / ".claude"
            )
            self.logger.info("SkillsMP integration available")
        except Exception as e:
            self.logger.warning(f"SkillsMP not available: {e}")
            self.skillsmp_integration = None

    def search_agents(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for existing agents/skills.

        Args:
            query: Search query describing needed agent
            limit: Max results

        Returns:
            Search results with options
        """
        self.logger.info(f"=== Searching for Agents: '{query}' ===")

        results = {
            "query": query,
            "skillsmp": [],
            "github": [],
            "found": False
        }

        if self.skillsmp_integration:
            # Search SkillsMP first
            try:
                skillsmp_results = self.skillsmp_integration.search_skills(
                    query=query,
                    limit=limit
                )

                results["skillsmp"] = skillsmp_results
                if skillsmp_results:
                    results["found"] = True
                    self.logger.info(f"Found {len(skillsmp_results)} SkillsMP results")

            except Exception as e:
                self.logger.warning(f"SkillsMP search failed: {e}")

        # GitHub fallback if SkillsMP not available or no results
        if not results["found"]:
            try:
                github_results = self.skillsmp_integration.search_skills(
                    query=query,
                    limit=limit,
                    use_github_fallback=True
                )

                results["github"] = [r for r in github_results if r.get("source") == "github"]
                if results["github"]:
                    results["found"] = True
                    self.logger.info(f"Found {len(results['github'])} GitHub results")

            except Exception as e:
                self.logger.warning(f"GitHub search failed: {e}")

        return results

    def present_options(
        self,
        search_results: Dict[str, Any]
    ) -> str:
        """Present search options to user.

        Args:
            search_results: Results from search_agents()

        Returns:
            Formatted options text
        """
        output = f"\n=== Agent Search Results: '{search_results['query']}' ===\n\n"

        if not search_results["found"]:
            output += "❌ No existing agents found.\n"
            output += "💡 Recommendation: Create new agent from templates\n"
            return output

        # SkillsMP results
        if search_results["skillsmp"]:
            output += "## 🎯 SkillsMP Agents (Verified)\n\n"
            for i, agent in enumerate(search_results["skillsmp"][:5], 1):
                title = agent.get("title", "Unknown")
                description = agent.get("description", "")
                stars = agent.get("github_stars", 0)

                output += f"{i}. **{title}**"
                if stars:
                    output += f" ⭐ {stars}"
                output += "\n"

                if description:
                    output += f"   {description[:100]}...\n"
                output += "\n"

        # GitHub results
        if search_results["github"]:
            output += "## 🔍 GitHub Agents (Community)\n\n"
            for i, agent in enumerate(search_results["github"][:5], 1):
                title = agent.get("title", "Unknown")
                description = agent.get("description", "")
                repo = agent.get("github_repo", "")

                output += f"{i}. **{title}**"
                if repo:
                    output += f" 📦 {repo}"
                output += "\n"

                if description:
                    output += f"   {description[:100]}...\n"
                output += "\n"

        output += "---\n\n"
        output += "💡 **Options**:\n"
        output += "1. Use existing agent (specify number)\n"
        output += "2. Create new agent from templates\n"
        output += "3. Search with different query\n"

        return output

    def create_agent_from_requirements(
        self,
        agent_name: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Path]:
        """Create new agent from requirements.

        Args:
            agent_name: Name for new agent
            requirements: Agent requirements dict containing:
                - role: Primary role
                - personality: Optional personality traits
                - team: Optional team members
                - skills: Optional skill list
                - user_context: Optional user profile

        Returns:
            Dict mapping file types to created paths
        """
        self.logger.info(f"=== Creating Agent: {agent_name} ===")

        # Generate agent files
        created_files = self.template_generator.generate_agent(
            agent_name=agent_name,
            role=requirements.get("role", f"Agent for {agent_name}"),
            personality=requirements.get("personality"),
            team=requirements.get("team"),
            skills=requirements.get("skills"),
            user_context=requirements.get("user_context")
        )

        # Record in projects-log
        self._record_agent_creation(
            agent_name=agent_name,
            requirements=requirements
        )

        return created_files

    def _record_agent_creation(
        self,
        agent_name: str,
        requirements: Dict[str, Any]
    ) -> None:
        """Record agent creation in projects-log.

        Args:
            agent_name: Agent name
            requirements: Agent requirements
        """
        from ..file_manager import FileMemoryManager

        # Use a special "agents" project for tracking
        log_manager = FileMemoryManager(
            project_id="agents",
            memory_root=self.memory_root
        )

        # Build log entry
        title = f"Created agent: {agent_name}"
        content = f"""
### Agent Created

**Name**: {agent_name}
**Role**: {requirements.get('role', 'Not specified')}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Requirements

"""
        for key, value in requirements.items():
            if value:
                content += f"- **{key}**: {value}\n"

        content += f"\n### Files Created\n\n"
        content += f"- AGENTS.md\n"
        content += f"- SOUL.md\n"
        content += f"- USER.md\n"
        content += f"- MEMORY.md\n"
        content += f"- memory/ (with 4-level memory system)\n"

        # Write to log
        log_manager.write_entry(
            file_type="log",
            title=title,
            content=content,
            one_liner=f"Agent {agent_name} created with 4-level memory"
        )

        self.logger.info(f"Recorded agent creation: {agent_name}")

    def get_agent_template(self, template_type: str) -> str:
        """Get predefined agent template.

        Args:
            template_type: Type of template (frontend, backend, fullstack, etc.)

        Returns:
            Template description
        """
        templates = {
            "frontend": {
                "role": "Frontend Developer Agent",
                "personality": "Творческий и внимательный к UI/UX деталям, фокус на пользовательском опыте",
                "skills": [
                    "React/Next.js development",
                    "TypeScript",
                    "CSS/Tailwind styling",
                    "Responsive design",
                    "Accessibility (WCAG)"
                ],
                "team": ["backend-dev", "tester"]
            },
            "backend": {
                "role": "Backend Developer Agent",
                "personality": "Аналитический и системный, фокус на архитектуре и надёжности",
                "skills": [
                    "API design (REST/GraphQL)",
                    "Database modeling",
                    "Authentication/authorization",
                    "Error handling and logging",
                    "Performance optimization"
                ],
                "team": ["frontend-dev", "architect"]
            },
            "fullstack": {
                "role": "Fullstack Developer Agent",
                "personality": "Универсальный и адаптивный, баланс между фронтендом и бэкендом",
                "skills": [
                    "Frontend: React/Next.js, TypeScript",
                    "Backend: Node.js, Express, PostgreSQL",
                    "API integration",
                    "DevOps basics",
                    "Testing (unit, integration)"
                ],
                "team": ["architect", "tester"]
            },
            "architect": {
                "role": "Software Architect Agent",
                "personality": "Стратегический и дальновидный, фокус на масштабируемости",
                "skills": [
                    "System design",
                    "Technology stack selection",
                    "Scalability patterns",
                    "Security architecture",
                    "Cost optimization"
                ],
                "team": ["frontend-dev", "backend-dev"]
            },
            "tester": {
                "role": "QA Tester Agent",
                "personality": "Тщательный и скептичный, фокус на качестве и краевых случаях",
                "skills": [
                    "Test strategy design",
                    "Automation testing",
                    "Edge case identification",
                    "Performance testing",
                    "Security testing basics"
                ],
                "team": ["fullstack"]
            }
        }

        return templates.get(template_type, templates["fullstack"])

    def list_available_templates(self) -> List[str]:
        """List available agent templates.

        Returns:
            List of template names
        """
        return ["frontend", "backend", "fullstack", "architect", "tester"]
