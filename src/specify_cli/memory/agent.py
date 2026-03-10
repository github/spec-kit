"""
Memory-Aware Agent - Implements structured prompt template workflow.

Provides Before/When/After workflow for memory-aware AI agents.
"""

from typing import Dict, List, Optional
from pathlib import Path

from .orchestrator import MemoryOrchestrator
from .file_manager import FileMemoryManager
from .logging import get_logger


class MemoryAwareAgent:
    """Memory-aware agent with structured Before/When/After workflow."""

    def __init__(self, project_id: str, memory_root: Optional[Path] = None):
        """Initialize memory-aware agent.

        Args:
            project_id: Project identifier
            memory_root: Root directory for memory files
        """
        self.project_id = project_id
        self.logger = get_logger()

        self.orchestrator = MemoryOrchestrator(
            project_id=project_id,
            memory_root=memory_root
        )
        self.file_manager = FileMemoryManager(
            project_id=project_id,
            memory_root=memory_root
        )

    def before_task(self, limit: int = 10) -> Dict[str, List[str]]:
        """BEFORE TASK: Read headers-first for context (~80-120 tokens).

        Args:
            limit: Maximum headers per file

        Returns:
            Dict mapping file types to header lists
        """
        self.logger.info("=== BEFORE TASK: Headers-First Reading ===")

        headers = self.file_manager.read_headers_first(limit=limit)

        total_headers = sum(len(h) for h in headers.values())
        self.logger.info(f"Headers read: {total_headers} total (~80-120 tokens)")

        return headers

    def when_stuck(self, query: str, scope: str = "auto") -> List[Dict]:
        """WHEN STUCK: Vector search + deep dive.

        Args:
            query: Search query describing the problem
            scope: "local", "global", or "auto"

        Returns:
            List of search results
        """
        self.logger.info(f"=== WHEN STUCK: Searching for '{query}' ===")

        # Vector/search
        results = self.orchestrator.search(query, scope=scope)

        self.logger.info(f"Found {len(results)} results")

        return results

    def after_task(
        self,
        problem: str,
        solution: str,
        lessons: str,
        importance: float = 0.5,
        related_projects: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """AFTER TASK: Auto-document and save to memory.

        Args:
            problem: What was solved
            solution: How it was solved
            lessons: What was learned
            importance: Importance score (0.0-1.0) for routing
            related_projects: Projects this affects
            tags: Search keywords

        Returns:
            True if saved successfully
        """
        self.logger.info("=== AFTER TASK: Auto-Documentation ===")

        # Determine memory type based on importance
        if importance > 0.7:
            memory_type = "architecture"
            file_type = "architecture"
        elif importance > 0.4:
            memory_type = "pattern"
            file_type = "pattern"
        else:
            memory_type = "log"
            file_type = "log"

        # Build content with structured format
        content = self._build_structured_content(
            problem, solution, lessons, related_projects, tags
        )

        # Extract title and one-liner
        title = self._extract_title(problem)
        one_liner = self._extract_one_liner(problem)

        # Save to file
        success = self.file_manager.write_entry(
            file_type=file_type,
            title=title,
            content=content,
            one_liner=one_liner
        )

        # Also save to vector memory (if available)
        # TODO: Implement vector save when agent-memory-mcp integrated

        return success

    def _build_structured_content(
        self,
        problem: str,
        solution: str,
        lessons: str,
        related_projects: Optional[List[str]],
        tags: Optional[List[str]]
    ) -> str:
        """Build structured content for memory entry.

        Args:
            problem: Problem description
            solution: Solution description
            lessons: Lessons learned
            related_projects: Related projects
            tags: Search tags

        Returns:
            Structured markdown content
        """
        content = f"### Problem\n{problem}\n\n"
        content += f"### Solution\n{solution}\n\n"
        content += f"### Lessons Learned\n{lessons}\n\n"

        if related_projects:
            content += f"### Related Projects\n"
            content += ", ".join(related_projects)
            content += "\n\n"

        if tags:
            content += f"### Tags\n"
            content += ", ".join(tags)
            content += "\n"

        return content

    def _extract_title(self, problem: str) -> str:
        """Extract title from problem description.

        Args:
            problem: Problem description

        Returns:
            Title string
        """
        # First line or first 50 chars
        lines = problem.strip().split("\n")
        first_line = lines[0].strip()

        if len(first_line) > 50:
            return first_line[:47] + "..."
        return first_line

    def _extract_one_liner(self, problem: str) -> str:
        """Extract one-line summary from problem description.

        Args:
            problem: Problem description

        Returns:
            One-line summary (max 100 chars)
        """
        # Take first sentence, truncate to 100 chars
        lines = problem.strip().split("\n")
        first_line = lines[0].strip()

        # Remove common prefixes
        for prefix in ["Error:", "Issue:", "Problem:", "Warning:"]:
            if first_line.startswith(prefix):
                first_line = first_line[len(prefix):].strip()
                break

        if len(first_line) > 100:
            # Truncate at word boundary
            first_line = first_line[:97].rsplit(" ", 1)[0] + "..."

        return first_line

    def get_prompt_template(self) -> str:
        """Get the memory-aware prompt template for agents.

        Returns:
            Prompt template string
        """
        return """
## Memory-Aware Workflow Template

### Before Any Task (Execute Always)
1. Read headers-first (~80-120 tokens):
   - lessons.md: grep "^## " | tail -10
   - patterns.md: grep "^## " | tail -10
   - architecture.md: grep "^#{1,3} "
2. Check relevance: Any header match current task?
3. If yes → Read full section
4. If no → Proceed with task

### When Stuck (Execute On-Demand)
1. Vector search: memory_search(query="problem context")
2. Deep dive: Read full relevant section
3. Cross-project: If <3 local results → Offer global

### After Task (Execute Always)
1. AI classify importance (0.0-1.0)
2. Route to appropriate file:
   - >0.7 → architecture.md
   - 0.4-0.7 → patterns.md
   - <0.4 → projects-log.md
3. Save with Problem → Solution → Lessons → Tags
4. Update vector memory (if available)

**Context Usage**:
- Before: ~80-120 tokens
- When Stuck: ~500-2000 tokens (on-demand)
- After: Save only (no context cost)
"""
