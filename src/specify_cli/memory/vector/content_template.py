"""
Content template for structured memory storage.

Provides templates for different types of memory content.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class MemoryContentTemplate:
    """Templates for structured memory content."""

    # Problem-Solution-Lessons template
    PROBLEM_SOLUTION_TEMPLATE = """## {title}

**Type**: {type}
**Date**: {date}
**Tags**: {tags}
**Project**: {project}

### Problem
{problem}

### Solution
{solution}

### Lessons Learned
{lessons}

### Related
{related}
"""

    # Pattern template
    PATTERN_TEMPLATE = """## {name} - {summary}

**Category**: {category}
**Date**: {date}
**Tags**: {tags}
**Project**: {project}

### Context
{context}

### Pattern
{pattern}

### Example
```{language}
{example}
```

### Benefits
- {benefits}

### Trade-offs
{tradeoffs}

### Related Patterns
{related}
"""

    # Architecture decision template
    DECISION_TEMPLATE = """## {title}

**Status**: {status}
**Date**: {date}
**Decision Makers**: {decision_makers}

### Context
{context}

### Decision
{decision}

### Consequences
**Positive**:
- {positive_consequences}

**Negative**:
- {negative_consequences}

### Alternatives Considered
{alternatives}

### Related Decisions
{related}
"""

    # Episodic memory template
    EPISODIC_TEMPLATE = """## {title}

**When**: {timestamp}
**Where**: {location}
**Who**: {participants}
**Type**: {event_type}

### What Happened
{description}

### Key Insights
{insights}

### Impact
{impact}

### Follow-up Actions
{actions}
"""

    @staticmethod
    def format_problem_solution(
        title: str,
        problem: str,
        solution: str,
        lessons: str,
        tags: Optional[List[str]] = None,
        project: Optional[str] = None,
        related: Optional[str] = None
    ) -> str:
        """Format problem-solution entry.

        Args:
            title: Entry title
            problem: Problem description
            solution: Solution description
            lessons: Lessons learned
            tags: Optional tags
            project: Optional project ID
            related: Related entries

        Returns:
            Formatted markdown
        """
        return MemoryContentTemplate.PROBLEM_SOLUTION_TEMPLATE.format(
            title=title,
            type="Problem-Solution",
            date=datetime.now().strftime("%Y-%m-%d"),
            tags=", ".join(tags or []),
            project=project or "Unknown",
            problem=problem,
            solution=solution,
            lessons=lessons,
            related=related or "None"
        )

    @staticmethod
    def format_pattern(
        name: str,
        summary: str,
        pattern: str,
        context: str,
        language: str = "python",
        example: str = "",
        benefits: str = "",
        tradeoffs: str = "",
        category: str = "Design Pattern",
        tags: Optional[List[str]] = None,
        project: Optional[str] = None,
        related: str = ""
    ) -> str:
        """Format pattern entry.

        Args:
            name: Pattern name
            summary: One-line summary
            pattern: Pattern description
            context: Usage context
            language: Example code language
            example: Code example
            benefits: Benefits
            tradeoffs: Trade-offs
            category: Pattern category
            tags: Optional tags
            project: Optional project ID
            related: Related patterns

        Returns:
            Formatted markdown
        """
        return MemoryContentTemplate.PATTERN_TEMPLATE.format(
            name=name,
            summary=summary,
            pattern=pattern,
            context=context,
            language=language,
            example=example or "# Example code here",
            benefits=benefits or "TBD",
            tradeoffs=tradeoffs or "None identified",
            category=category,
            date=datetime.now().strftime("%Y-%m-%d"),
            tags=", ".join(tags or []),
            project=project or "Unknown",
            related=related or "None"
        )

    @staticmethod
    def format_decision(
        title: str,
        context: str,
        decision: str,
        positive: str = "",
        negative: str = "",
        alternatives: str = "",
        status: str = "Accepted",
        decision_makers: str = "AI Assistant",
        related: str = ""
    ) -> str:
        """Format architecture decision.

        Args:
            title: Decision title
            context: Decision context
            decision: The decision itself
            positive: Positive consequences
            negative: Negative consequences
            alternatives: Alternatives considered
            status: Decision status
            decision_makers: Who made the decision
            related: Related decisions

        Returns:
            Formatted markdown
        """
        return MemoryContentTemplate.DECISION_TEMPLATE.format(
            title=title,
            context=context,
            decision=decision,
            positive_consequences=positive or "TBD",
            negative_consequences=negative or "None identified",
            alternatives=alternatives or "None",
            status=status,
            date=datetime.now().strftime("%Y-%m-%d"),
            decision_makers=decision_makers,
            related=related or "None"
        )

    @staticmethod
    def format_episodic(
        title: str,
        description: str,
        insights: str,
        event_type: str = "Task",
        location: str = "Development",
        participants: str = "AI Assistant",
        impact: str = "",
        actions: str = ""
    ) -> str:
        """Format episodic memory entry.

        Args:
            title: Event title
            description: What happened
            insights: Key insights
            event_type: Type of event
            location: Where it happened
            participants: Who was involved
            impact: Impact of event
            actions: Follow-up actions

        Returns:
            Formatted markdown
        """
        return MemoryContentTemplate.EPISODIC_TEMPLATE.format(
            title=title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            location=location,
            participants=participants,
            event_type=event_type,
            description=description,
            insights=insights,
            impact=impact or "Not specified",
            actions=actions or "None"
        )


class StructuredMemory:
    """Helper for creating structured memory entries."""

    def __init__(self, project_id: str):
        """Initialize structured memory helper.

        Args:
            project_id: Project identifier
        """
        self.project_id = project_id

    def create_problem_entry(
        self,
        title: str,
        problem: str,
        solution: str,
        lessons: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create problem-solution entry.

        Args:
            title: Entry title
            problem: Problem description
            solution: Solution description
            lessons: Lessons learned
            tags: Optional tags

        Returns:
            Entry dict with content and metadata
        """
        content = MemoryContentTemplate.format_problem_solution(
            title=title,
            problem=problem,
            solution=solution,
            lessons=lessons,
            tags=tags,
            project=self.project_id
        )

        return {
            "content": content,
            "type": "problem_solution",
            "title": title,
            "tags": tags or [],
            "project": self.project_id,
            "created_at": datetime.now().isoformat()
        }

    def create_pattern_entry(
        self,
        name: str,
        summary: str,
        pattern: str,
        context: str,
        language: str = "python",
        example: str = ""
    ) -> Dict[str, Any]:
        """Create pattern entry.

        Args:
            name: Pattern name
            summary: One-line summary
            pattern: Pattern description
            context: Usage context
            language: Example code language
            example: Code example

        Returns:
            Entry dict with content and metadata
        """
        content = MemoryContentTemplate.format_pattern(
            name=name,
            summary=summary,
            pattern=pattern,
            context=context,
            language=language,
            example=example
        )

        return {
            "content": content,
            "type": "pattern",
            "title": name,
            "summary": summary,
            "project": self.project_id,
            "created_at": datetime.now().isoformat()
        }

    def create_decision_entry(
        self,
        title: str,
        context: str,
        decision: str,
        positive: str = "",
        negative: str = ""
    ) -> Dict[str, Any]:
        """Create architecture decision entry.

        Args:
            title: Decision title
            context: Decision context
            decision: The decision
            positive: Positive consequences
            negative: Negative consequences

        Returns:
            Entry dict with content and metadata
        """
        content = MemoryContentTemplate.format_decision(
            title=title,
            context=context,
            decision=decision,
            positive=positive,
            negative=negative
        )

        return {
            "content": content,
            "type": "decision",
            "title": title,
            "project": self.project_id,
            "created_at": datetime.now().isoformat()
        }
