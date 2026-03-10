"""
Cross-project learning for memory system.

Enables knowledge transfer between related projects.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

from .logging import get_logger
from .project_detector import ProjectDetector
from .file_manager import FileMemoryManager
from .classifier import AIImportanceClassifier


class CrossProjectLearning:
    """Enables learning across related projects."""

    # Similarity threshold for considering projects "related"
    SIMILARITY_THRESHOLD = 0.3

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize cross-project learning.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"

        self.detector = ProjectDetector(global_home)
        self.file_manager = FileMemoryManager(global_home)
        self.classifier = AIImportanceClassifier()

    def find_related_projects(
        self,
        current_project_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find projects related to current project.

        Args:
            current_project_id: Current project identifier
            limit: Maximum number of related projects

        Returns:
            List of related project info dicts
        """
        all_projects = self.detector.list_all_projects()

        # Filter out current project
        other_projects = [
            p for p in all_projects
            if p.get("project_id") != current_project_id
        ]

        # Calculate similarities
        scored_projects = []

        for project in other_projects:
            similarity = self._calculate_project_similarity(
                current_project_id,
                project.get("project_id", "")
            )

            if similarity >= self.SIMILARITY_THRESHOLD:
                scored_projects.append({
                    **project,
                    "similarity": similarity
                })

        # Sort by similarity and limit
        scored_projects.sort(key=lambda x: x["similarity"], reverse=True)

        return scored_projects[:limit]

    def _calculate_project_similarity(
        self,
        project1: str,
        project2: str
    ) -> float:
        """Calculate similarity between two project IDs.

        Args:
            project1: First project ID
            project2: Second project ID

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # String similarity
        string_sim = SequenceMatcher(None, project1, project2).ratio()

        # Check for common prefixes/technologies
        tech_keywords = ["react", "vue", "angular", "node", "python", "rust", "go"]

        tech1 = [kw for kw in tech_keywords if kw in project1.lower()]
        tech2 = [kw for kw in tech_keywords if kw in project2.lower()]

        tech_sim = len(set(tech1) & set(tech2)) / max(len(set(tech1) | set(tech2)), 1)

        # Combined score
        return (string_sim * 0.7) + (tech_sim * 0.3)

    def search_related_memory(
        self,
        query: str,
        current_project_id: str,
        project_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search memory in related projects.

        Args:
            query: Search query
            current_project_id: Current project (to exclude from results)
            project_ids: Specific projects to search (default: auto-detect related)

        Returns:
            List of relevant memory entries with project context
        """
        # Determine which projects to search
        if project_ids is None:
            related = self.find_related_projects(current_project_id)
            project_ids = [p["project_id"] for p in related]

        results = []

        for project_id in project_ids:
            # Search in this project's memory
            project_results = self._search_project_memory(project_id, query)

            # Add project context
            for result in project_results:
                result["project_id"] = project_id

            results.extend(project_results)

        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

        return results

    def _search_project_memory(
        self,
        project_id: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Search memory in a single project.

        Args:
            project_id: Project identifier
            query: Search query

        Returns:
            List of matching entries
        """
        results = []

        # Search in each memory file type
        file_types = ["lessons", "patterns", "architecture"]

        for file_type in file_types:
            headers = self.file_manager.read_headers_first(
                file_type=file_type,
                project_id=project_id
            )

            for header in headers:
                # Calculate relevance based on query match
                relevance = self._calculate_relevance(query, header)

                if relevance > 0.1:  # Minimal relevance threshold
                    results.append({
                        "file_type": file_type,
                        "title": header.get("title", ""),
                        "summary": header.get("summary", ""),
                        "relevance": relevance
                    })

        return results

    def _calculate_relevance(
        self,
        query: str,
        header: Dict[str, str]
    ) -> float:
        """Calculate relevance of header to query.

        Args:
            query: Search query
            header: Header dict

        Returns:
            Relevance score (0.0 to 1.0)
        """
        query_lower = query.lower()

        title = header.get("title", "").lower()
        summary = header.get("summary", "").lower()

        # Direct match in title
        if query_lower in title:
            return 1.0

        # Partial match in title
        title_words = set(title.split())
        query_words = set(query_lower.split())

        if title_words & query_words:
            return 0.7

        # Match in summary
        if query_lower in summary:
            return 0.5

        return 0.0

    def transfer_learning(
        self,
        source_project_id: str,
        target_project_id: str,
        min_importance: float = 0.6
    ) -> int:
        """Transfer important learnings from source to target project.

        Args:
            source_project_id: Source project ID
            target_project_id: Target project ID
            min_importance: Minimum importance score to transfer

        Returns:
            Number of entries transferred
        """
        transferred = 0

        # Read source project's patterns and architecture
        file_types = ["patterns", "architecture"]

        for file_type in file_types:
            headers = self.file_manager.read_headers_first(
                file_type=file_type,
                project_id=source_project_id
            )

            for header in headers:
                # Get full content
                content = self.file_manager.read_section(
                    file_type=file_type,
                    header_match=header["title"],
                    project_id=source_project_id
                )

                if content:
                    # Calculate importance
                    importance = self.classifier.calculate_importance(content)

                    if importance.get("overall_score", 0) >= min_importance:
                        # Transfer to target
                        self.file_manager.write_entry(
                            file_type=file_type,
                            title=f"{header['title']} (from {source_project_id})",
                            content=content,
                            one_liner=header.get("summary"),
                            project_id=target_project_id
                        )

                        transferred += 1

        return transferred

    def suggest_relevant_patterns(
        self,
        current_context: str,
        current_project_id: str
    ) -> List[Dict[str, Any]]:
        """Suggest relevant patterns from related projects.

        Args:
            current_context: Current task/problem context
            current_project_id: Current project ID

        Returns:
            List of suggested patterns with relevance
        """
        # Find related projects
        related = self.find_related_projects(current_project_id)

        # Search for relevant patterns
        results = self.search_related_memory(
            query=current_context,
            current_project_id=current_project_id,
            project_ids=[p["project_id"] for p in related]
        )

        # Filter to only patterns
        patterns = [r for r in results if r.get("file_type") == "patterns"]

        return patterns[:5]  # Top 5 suggestions
