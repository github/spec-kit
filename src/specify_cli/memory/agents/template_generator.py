"""
Agent Template Generator - Creates agent structure based on AgentForge patterns.

Generates AGENTS.md, SOUL.md, USER.md, MEMORY.md for new agents.
Based on 4-level memory system + AgentForge patterns (without OpenClaw dependency).
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from ..logging import get_logger
from ..orchestrator import MemoryOrchestrator


class AgentTemplateGenerator:
    """Generates agent file templates with 4-level memory support."""

    def __init__(self, memory_root: Optional[Path] = None):
        """Initialize agent template generator.

        Args:
            memory_root: Root directory for memory files
        """
        self.logger = get_logger()
        self.memory_root = memory_root or Path.home() / ".claude" / "memory"

    def generate_agent(
        self,
        agent_name: str,
        role: str,
        personality: Optional[str] = None,
        team: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        agent_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """Generate complete agent structure with all required files.

        Args:
            agent_name: Name of the agent (e.g., "frontend-dev", "backend-architect")
            role: Primary role and responsibility
            personality: Optional personality traits (for SOUL.md)
            team: Optional list of related agents
            skills: Optional list of agent skills
            user_context: Optional user profile data
            agent_dir: Directory to create agent files (default: ~/.claude/agents/{name})

        Returns:
            Dict mapping file type to created file path
        """
        self.logger.info(f"=== Generating Agent: {agent_name} ===")

        # Determine agent directory
        if agent_dir is None:
            agent_dir = self.memory_root.parent / "agents" / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Generate files
        created_files = {}

        # AGENTS.md
        agents_path = agent_dir / "AGENTS.md"
        agents_content = self._generate_agents_md(
            agent_name=agent_name,
            role=role,
            team=team or [],
            skills=skills or []
        )
        agents_path.write_text(agents_content, encoding="utf-8")
        created_files["agents"] = agents_path
        self.logger.info(f"Created: {agents_path}")

        # SOUL.md
        soul_path = agent_dir / "SOUL.md"
        soul_content = self._generate_soul_md(
            agent_name=agent_name,
            personality=personality or self._default_personality(agent_name)
        )
        soul_path.write_text(soul_content, encoding="utf-8")
        created_files["soul"] = soul_path
        self.logger.info(f"Created: {soul_path}")

        # USER.md
        user_path = agent_dir / "USER.md"
        user_content = self._generate_user_md(
            user_context=user_context or {}
        )
        user_path.write_text(user_content, encoding="utf-8")
        created_files["user"] = user_path
        self.logger.info(f"Created: {user_path}")

        # MEMORY.md
        memory_path = agent_dir / "MEMORY.md"
        memory_content = self._generate_memory_md(
            agent_name=agent_name,
            role=role
        )
        memory_path.write_text(memory_content, encoding="utf-8")
        created_files["memory"] = memory_path
        self.logger.info(f"Created: {memory_path}")

        # memory/ subdirectory
        memory_dir = agent_dir / "memory"
        memory_dir.mkdir(exist_ok=True)
        created_files["memory_dir"] = memory_dir

        # Create initial memory files
        for file_type in ["lessons", "patterns", "projects-log", "architecture", "handoff"]:
            mem_file = memory_dir / f"{file_type}.md"
            if not mem_file.exists():
                mem_content = self._generate_memory_file_template(file_type)
                mem_file.write_text(mem_content, encoding="utf-8")

        self.logger.info(f"Agent {agent_name} created at {agent_dir}")

        return created_files

    def _generate_agents_md(
        self,
        agent_name: str,
        role: str,
        team: List[str],
        skills: List[str]
    ) -> str:
        """Generate AGENTS.md content.

        Args:
            agent_name: Agent name
            role: Agent role description
            team: List of related agents
            skills: List of agent skills

        Returns:
            AGENTS.md content
        """
        content = f"""# {agent_name}

> **Role**: {role}
> **Created**: {datetime.now().strftime("%Y-%m-%d")}
> **Memory System**: 4-Level (File + Vector + Context + Identity)

---

## Agent Role

{role}

---

## Team

"""
        if team:
            for member in team:
                content += f"- **{member}**\n"
        else:
            content += "_No team members defined yet_\n"

        content += "\n## Skills\n\n"
        if skills:
            for skill in skills:
                content += f"- {skill}\n"
        else:
            content += "_No skills defined yet_\n"

        content += """
## Memory Files

- **AGENTS.md** - This file (role, team, skills)
- **SOUL.md** - Personality and principles
- **USER.md** - User profile and preferences
- **MEMORY.md** - Knowledge summary
- **memory/** - 4-level memory files
  - `lessons.md` - Accumulated lessons (3+ repeats → rule)
  - `patterns.md` - Improvement patterns (error → pattern)
  - `projects-log.md` - Task history
  - `architecture.md` - Architectural decisions
  - `handoff.md` - Session context (auto-generated)

## Auto-Improvement System

1. **Error occurs** → Record in `memory/patterns.md`
2. **3 repeats** → Promote to `memory/lessons.md` as rule
3. **Weekly** → Auto-handoff analysis
"""
        return content

    def _generate_soul_md(self, agent_name: str, personality: str) -> str:
        """Generate SOUL.md content.

        Args:
            agent_name: Agent name
            personality: Personality description

        Returns:
            SOUL.md content
        """
        return f"""# {agent_name} - Soul

> **Created**: {datetime.now().strftime("%Y-%m-%d")}

---

## Personality

{personality}

---

## Core Principles

1. **Clarity First** - Communicate clearly and concisely
2. **Context Awareness** - Always consider memory context before acting
3. **Continuous Learning** - Learn from every interaction
4. **Graceful Degradation** - Function even when memory unavailable

---

## Communication Style

- **Tone**: Professional, direct, constructive
- **Language**: Russian (as requested)
- **Format**: Structured markdown with clear sections
- **Emojis**: Only when explicitly requested

---

## Decision Making

1. **Before Task**: Read headers-first from memory
2. **When Stuck**: Search vector memory + deep dive
3. **After Task**: Auto-document and save

---

## Constraints

- **No OpenClaw integration** - AgentForge patterns only
- **4-level memory system** - File, Vector, Context, Identity
- **Respect user preferences** - Check USER.md before assumptions
"""

    def _default_personality(self, agent_name: str) -> str:
        """Generate default personality based on agent name.

        Args:
            agent_name: Agent name

        Returns:
            Default personality description
        """
        personalities = {
            "frontend": "Творческий и внимательный к UI/UX деталям, фокус на пользовательском опыте",
            "backend": "Аналитический и системный, фокус на архитектуре и надёжности",
            "fullstack": "Универсальный и адаптивный, баланс между фронтендом и бэкендом",
            "architect": "Стратегический и дальновидный, фокус на масштабируемости",
            "tester": "Тщательный и sceptical, фокус на качестве и краевых случаях",
            "default": "Профессиональный и конструктивный, фокус на решении задач"
        }

        for key, value in personalities.items():
            if key in agent_name.lower():
                return value

        return personalities["default"]

    def _generate_user_md(self, user_context: Dict[str, Any]) -> str:
        """Generate USER.md content.

        Args:
            user_context: User profile data

        Returns:
            USER.md content
        """
        content = """# User Profile

> **Last Updated**: """ + datetime.now().strftime("%Y-%m-%d") + """

---

## User Identity

"""

        if "name" in user_context:
            content += f"**Name**: {user_context['name']}\n"
        if "role" in user_context:
            content += f"**Role**: {user_context['role']}\n"
        if "location" in user_context:
            content += f"**Location**: {user_context['location']}\n"

        content += """
---

## Preferences

### Communication

- **Language**: Russian
- **Style**: Direct, technical, concise
- **Format**: Markdown with code examples

### Work Style

"""
        if "work_style" in user_context:
            content += f"{user_context['work_style']}\n"
        else:
            content += "- Detail-oriented but pragmatic\n"
            content += "- Prefers working code over extensive documentation\n"
            content += "- Values tests and validation\n"

        content += """
### Technical Preferences

"""
        if "tech_stack" in user_context:
            content += f"**Preferred Stack**: {user_context['tech_stack']}\n"
        if "editor" in user_context:
            content += f"**Editor**: {user_context['editor']}\n"

        content += """
---

## Project Context

See project-specific memory in `../projects/{project-name}/` for:
- Architecture decisions
- Accumulated patterns
- Project-specific lessons
"""

        return content

    def _generate_memory_md(self, agent_name: str, role: str) -> str:
        """Generate MEMORY.md content.

        Args:
            agent_name: Agent name
            role: Agent role

        Returns:
            MEMORY.md content
        """
        return f"""# {agent_name} - Knowledge Summary

> **Role**: {role}
> **Last Updated**: {datetime.now().strftime("%Y-%m-%d")}

---

## Quick Access

### Recent Lessons (5)
_See `memory/lessons.md` for full list_

### Active Patterns (5)
_See `memory/patterns.md` for full list_

### Current Context
_See `memory/handoff.md` for active session context_

---

## Memory Structure

This agent uses the **4-level memory system**:

1. **File-Based** (Level 1) - Structured markdown files
2. **Vector-Based** (Level 2) - Semantic search (if Ollama available)
3. **Contextual** (Level 3) - Session context with headers-first reading
4. **Identity** (Level 4) - AGENTS.md, SOUL.md, USER.md, MEMORY.md

---

## Accessing Memory

### Headers-First (~80-120 tokens)
```bash
# Read only titles and one-liners
grep "^##" memory/lessons.md | tail -5
grep "^##" memory/patterns.md | tail -5
```

### Deep Dive (~500-2000 tokens)
```bash
# Read full section when relevant
cat memory/lessons.md
```

### Vector Search (if available)
```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

orchestrator = MemoryOrchestrator(project_id="{agent_name}")
results = orchestrator.search("database connection error")
```
"""

    def _generate_memory_file_template(self, file_type: str) -> str:
        """Generate initial memory file content.

        Args:
            file_type: Type of memory file

        Returns:
            File content
        """
        templates = {
            "lessons": """# Lessons Learned

_Accumulated rules from 3+ repeated patterns_

---

*No lessons yet. Lessons are auto-promoted from patterns.md after 3 repeats.*
""",
            "patterns": """# Improvement Patterns

_Error → Pattern recording_

---

*No patterns yet. Patterns are recorded when errors occur.*
""",
            "projects-log": """# Projects Log

_Task history and outcomes_

---

*No tasks recorded yet.*
""",
            "architecture": """# Architecture Decisions

_High-importance decisions (>0.7 score)_

---

*No architectural decisions yet.*
""",
            "handoff": """# Session Handoff

_Weekly context analysis_

---

## Last Session

**Date**: """ + datetime.now().strftime("%Y-%m-%d") + """
**Status**: Initial setup

## Active Tasks
_None_

## Blocked Issues
_None_

## Next Session Focus
_Set up agent workflows and begin accumulation_
"""
        }

        return templates.get(file_type, "# " + file_type.title() + "\n\n_No content_\n")
