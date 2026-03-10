"""
Unified SkillsMP integration with API key management.

Combines SkillsMP API, GitHub fallback, and local caching.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .api_client import SkillsMPAPIClient, SkillsMPError
from .api_key_storage import APIKeyStorage
from .github_fallback import GitHubSkillSearcher
from .skill_comparison import SkillSelector, ConflictResolver
from ..logging import get_logger


class SkillsMPIntegration:
    """Unified SkillsMP integration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        global_home: Optional[Path] = None
    ):
        """Initialize SkillsMP integration.

        Args:
            api_key: SkillsMP API key (optional)
            github_token: GitHub token (for fallback)
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"

        # API key storage
        self.key_storage = APIKeyStorage()

        # Use provided key or try to load from storage
        self.api_key = api_key or self.key_storage.get_api_key()

        # Initialize clients
        self.skillsmp_client = None
        self.github_searcher = None

        if self.api_key:
            self.skillsmp_client = SkillsMPAPIClient(
                api_key=self.api_key,
                cache_dir=self.global_home / "memory" / "cache" / "skillsmp"
            )

        if github_token:
            self.github_searcher = GitHubSkillSearcher(
                token=github_token,
                cache_dir=self.global_home / "memory" / "cache" / "github"
            )

        # Skill selection
        self.skill_selector = SkillSelector()

    def search_skills(
        self,
        query: str,
        limit: int = 10,
        use_github_fallback: bool = True,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for skills across sources.

        Args:
            query: Search query
            limit: Max results
            use_github_fallback: Use GitHub if SkillsMP unavailable
            category: Filter by category

        Returns:
            List of skills
        """
        results = []

        # Try SkillsMP API first
        if self.skillsmp_client:
            try:
                skillsmp_results = self.skillsmp_client.search_skills(
                    query=query,
                    limit=limit,
                    category=category
                )

                if skillsmp_results:
                    results.extend([
                        {**s, "source": "skillsmp"}
                        for s in skillsmp_results
                    ])

            except Exception as e:
                self.logger.warning(f"SkillsMP API error: {e}")

        # GitHub fallback if needed
        if use_github_fallback and len(results) < limit:
            remaining = limit - len(results)

            if self.github_searcher:
                try:
                    github_results = self.github_searcher.search_skills(
                        query=query,
                        limit=remaining
                    )

                    if github_results:
                        results.extend([
                            {**s, "source": "github"}
                            for s in github_results
                        ])

                except Exception as e:
                    self.logger.warning(f"GitHub search error: {e}")

        # Rank and filter
        ranked = self.skill_selector.comparator.rank_skills(query, results)

        # Remove duplicates
        unique = self.skill_selector.comparator.filter_duplicates(ranked)

        return unique[:limit]

    def get_skill_details(
        self,
        skill_id: str,
        source: str = "skillsmp"
    ) -> Optional[Dict[str, Any]]:
        """Get detailed skill information.

        Args:
            skill_id: Skill identifier
            source: Source system

        Returns:
            Skill details
        """
        if source == "skillsmp" and self.skillsmp_client:
            return self.skillsmp_client.get_skill(skill_id)
        elif source == "github" and self.github_searcher:
            # Parse skill_id as "owner/repo"
            if "/" in skill_id:
                owner, repo = skill_id.split("/", 1)
                return self.github_searcher.get_repo_details(owner, repo)

        return None

    def compare_skills(
        self,
        query: str,
        skills: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compare and rank skills.

        Args:
            query: Search query
            skills: List of skills

        Returns:
            Ranked skills
        """
        return self.skill_selector.comparator.rank_skills(query, skills)

    def resolve_conflicts(
        self,
        skills: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """Resolve skill selection conflicts.

        Args:
            skills: Conflicting skills
            query: Original query

        Returns:
            Resolution result
        """
        resolver = ConflictResolver()
        return resolver.resolve_selection(skills, query)

    def setup_api_key(self, api_key: str) -> bool:
        """Setup and store API key.

        Args:
            api_key: SkillsMP API key

        Returns:
            True if successful
        """
        # Validate key format (basic check)
        if not api_key or len(api_key) < 10:
            self.logger.error("Invalid API key format")
            return False

        # Store key
        if self.key_storage.store_api_key(api_key):
            # Reinitialize client
            self.api_key = api_key
            self.skillsmp_client = SkillsMPAPIClient(api_key=api_key)
            return True

        return False

    def has_api_key(self) -> bool:
        """Check if API key is configured.

        Returns:
            True if configured
        """
        return bool(self.api_key)

    def get_status(self) -> Dict[str, Any]:
        """Get integration status.

        Returns:
            Status dict
        """
        return {
            "skillsmp": {
                "configured": bool(self.skillsmp_client),
                "api_key_stored": self.key_storage.has_api_key(),
                "status": self.skillsmp_client.get_status() if self.skillsmp_client else None
            },
            "github": {
                "configured": bool(self.github_searcher),
                "status": self.github_searcher.get_status() if self.github_searcher else None
            }
        }

    def list_categories(self) -> List[Dict[str, Any]]:
        """List available skill categories.

        Returns:
            List of categories
        """
        if self.skillsmp_client:
            return self.skillsmp_client.list_categories()

        return []
