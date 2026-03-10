"""
Smart search scope determination.

Automatically determines whether to search locally or globally based on query intent.
"""

import re
from typing import Dict, List, Any, Optional
from enum import Enum

from .logging import get_logger
from .project_detector import ProjectDetector
from .file_manager import FileMemoryManager
from .cross_project import CrossProjectLearning


class SearchScope(Enum):
    """Search scope options."""
    LOCAL = "local"       # Current project only
    GLOBAL = "global"     # All projects
    AUTO = "auto"         # Automatically determine


class SmartSearchEngine:
    """Smart search with automatic scope determination."""

    # Patterns indicating global search intent
    GLOBAL_MARKERS = [
        r"\bвообще\b",
        r"\bвезде\b",
        r"\bглобально\b",
        r"\bво всех проектах\b",
        r"\bacross\s+projects?\b",
        r"\bgenerally\b",
        r"\bglobally\b"
    ]

    # Patterns indicating local search intent
    LOCAL_MARKERS = [
        r"\bздесь\b",
        r"\bв этом проекте\b",
        r"\blocally\b",
        r"\bin this project\b",
        r"\bcurrent project\b"
    ]

    # Patterns indicating question (need broader search)
    QUESTION_PATTERNS = [
        r"\?",
        r"\bкак\b",
        r"\bкакие\b",
        r"\bгде\b",
        r"\bпочему\b",
        r"\bкак\b",
        r"\bwhat\b",
        r"\bwhere\b",
        r"\bwhy\b",
        r"\bhow\b"
    ]

    # Patterns indicating fix/debug (likely global)
    FIX_PATTERNS = [
        r"\bисправить\b",
        r"\bошибка\b",
        r"\bfix\b",
        r"\berror\b",
        r"\bbug\b",
        r"\bdebug\b"
    ]

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize smart search engine.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"

        self.detector = ProjectDetector(global_home)
        self.file_manager = FileMemoryManager(global_home)
        self.cross_project = CrossProjectLearning(global_home)

        # Compile regex patterns
        self._global_regex = re.compile("|".join(self.GLOBAL_MARKERS), re.IGNORECASE)
        self._local_regex = re.compile("|".join(self.LOCAL_MARKERS), re.IGNORECASE)
        self._question_regex = re.compile("|".join(self.QUESTION_PATTERNS), re.IGNORECASE)
        self._fix_regex = re.compile("|".join(self.FIX_PATTERNS), re.IGNORECASE)

    def determine_scope(self, query: str) -> SearchScope:
        """Determine search scope based on query.

        Args:
            query: Search query

        Returns:
            SearchScope (LOCAL, GLOBAL, or AUTO)
        """
        # Explicit global markers
        if self._global_regex.search(query):
            return SearchScope.GLOBAL

        # Explicit local markers
        if self._local_regex.search(query):
            return SearchScope.LOCAL

        # Auto-determine based on intent
        return SearchScope.AUTO

    def search(
        self,
        query: str,
        scope: str = "auto",
        current_project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute search with determined scope.

        Args:
            query: Search query
            scope: "local", "global", or "auto"
            current_project_id: Current project (auto-detected if None)

        Returns:
            Search results dict with scope used and results
        """
        # Detect current project if needed
        if current_project_id is None:
            project_info = self.detector.detect_current_project()
            current_project_id = project_info.get("project_id", ".global")

        # Determine scope
        if scope == "auto":
            determined_scope = self.determine_scope(query)

            # Auto-determine intent
            if determined_scope == SearchScope.AUTO:
                determined_scope = self._auto_determine_intent(query)
        else:
            determined_scope = SearchScope(scope)

        # Execute search based on scope
        if determined_scope == SearchScope.LOCAL:
            results = self._search_local(query, current_project_id)
        else:
            results = self._search_global(query, current_project_id)

        return {
            "scope": determined_scope.value,
            "query": query,
            "project_id": current_project_id,
            "results": results
        }

    def _auto_determine_intent(self, query: str) -> SearchScope:
        """Auto-determine search intent from query.

        Args:
            query: Search query

        Returns:
            Determined SearchScope
        """
        # Questions likely need broader search
        if self._question_regex.search(query):
            # Fix/error questions → global
            if self._fix_regex.search(query):
                return SearchScope.GLOBAL
            # Other questions → local first
            return SearchScope.LOCAL

        # Default to local
        return SearchScope.LOCAL

    def _search_local(
        self,
        query: str,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Search in local project only.

        Args:
            query: Search query
            project_id: Project ID

        Returns:
            List of results
        """
        results = []

        # Search across all file types
        file_types = ["lessons", "patterns", "architecture", "projects-log"]

        for file_type in file_types:
            headers = self.file_manager.read_headers_first(
                file_type=file_type,
                project_id=project_id
            )

            # Filter by query relevance
            for header in headers:
                relevance = self._calculate_relevance(query, header)

                if relevance > 0.1:
                    results.append({
                        "file_type": file_type,
                        "title": header.get("title", ""),
                        "summary": header.get("summary", ""),
                        "relevance": relevance,
                        "project_id": project_id
                    })

        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return results

    def _search_global(
        self,
        query: str,
        current_project_id: str
    ) -> List[Dict[str, Any]]:
        """Search across all projects.

        Args:
            query: Search query
            current_project_id: Current project to exclude

        Returns:
            List of results from all projects
        """
        # Use cross-project search
        results = self.cross_project.search_related_memory(
            query=query,
            current_project_id=current_project_id,
            project_ids=None  # Auto-detect related projects
        )

        # Also include local results
        local_results = self._search_local(query, current_project_id)

        # Combine and deduplicate
        all_results = local_results + results

        # Sort by relevance
        all_results.sort(key=lambda x: x["relevance"], reverse=True)

        return all_results

    def _calculate_relevance(
        self,
        query: str,
        header: Dict[str, str]
    ) -> float:
        """Calculate relevance score.

        Args:
            query: Search query
            header: Header dict

        Returns:
            Relevance score (0.0 to 1.0)
        """
        query_lower = query.lower()

        title = header.get("title", "").lower()
        summary = header.get("summary", "")

        # Exact match in title
        if query_lower in title:
            return 1.0

        # Word overlap in title
        query_words = set(query_lower.split())
        title_words = set(title.split())

        overlap = query_words & title_words

        if overlap:
            return len(overlap) / max(len(query_words), 1) * 0.8

        # Match in summary
        if query_lower in summary.lower():
            return 0.5

        return 0.0

    def suggest_expansion(
        self,
        local_results: List[Dict[str, Any]],
        query: str,
        current_project_id: str
    ) -> Optional[Dict[str, Any]]:
        """Suggest expanding to global search if local results are poor.

        Args:
            local_results: Local search results
            query: Search query
            current_project_id: Current project ID

        Returns:
            Suggestion dict or None if local results are sufficient
        """
        # Check if local results are insufficient
        if len(local_results) >= 3 and local_results[0]["relevance"] > 0.7:
            return None  # Good local results

        # Suggest global expansion
        global_results = self._search_global(query, current_project_id)

        if len(global_results) > len(local_results):
            return {
                "reason": "Limited local results",
                "local_count": len(local_results),
                "global_count": len(global_results),
                "global_results": global_results[:5]  # Top 5
            }

        return None
