"""
GitHub fallback for SkillsMP when API unavailable.

Provides skill search using GitHub API as backup.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

from ..logging import get_logger


class GitHubSkillSearcher:
    """GitHub API-based skill search (fallback)."""

    # GitHub API
    API_BASE = "https://api.github.com"
    SEARCH_ENDPOINT = "/search/code"
    REPO_ENDPOINT = "/repos/{owner}/{repo}"

    # Rate limiting
    RATE_LIMIT = 60  # requests per hour (unauthenticated)
    RATE_LIMIT_AUTH = 5000  # authenticated

    def __init__(
        self,
        token: Optional[str] = None,
        cache_dir: Optional[Path] = None
    ):
        """Initialize GitHub skill searcher.

        Args:
            token: GitHub personal access token (optional)
            cache_dir: Cache directory
        """
        self.logger = get_logger()
        self.token = token
        self.cache_dir = cache_dir or Path.home() / ".claude" / "memory" / "cache" / "github"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Session
        self.session = requests.Session()

        if token:
            self.session.headers.update({
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            })

        self.rate_limit = self.RATE_LIMIT_AUTH if token else self.RATE_LIMIT
        self.request_count = 0
        self.reset_time = None

    def search_skills(
        self,
        query: str,
        limit: int = 10,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search GitHub for skills (agents, MCP servers, etc.).

        Args:
            query: Search query
            limit: Max results
            language: Filter by programming language

        Returns:
            List of skill entries
        """
        # Build search query
        search_terms = [
            query,
            "agent",
            "skill",
            "mcp",
            "tool"
        ]

        if language:
            search_terms.append(f"language:{language}")

        q = " ".join(search_terms)

        # Check cache
        cache_key = f"search:{hashlib.md5(q.encode()).hexdigest()}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached[:limit]

        # Check rate limit
        if self._is_rate_limited():
            self.logger.warning("GitHub rate limit exceeded")
            return []

        # Make request
        params = {
            "q": q,
            "per_page": min(limit, 100)  # GitHub max is 100
        }

        response = self._make_request(self.SEARCH_ENDPOINT, params=params)

        if not response:
            return []

        # Parse results
        items = response.get("items", [])

        skills = []
        for item in items[:limit]:
            skill = self._parse_github_result(item)
            if skill:
                skills.append(skill)

        # Cache
        self._set_cache(cache_key, skills, ttl=1800)  # 30 min

        return skills

    def get_repo_details(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository details.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository details
        """
        endpoint = self.REPO_ENDPOINT.format(owner=owner, repo=repo)

        response = self._make_request(endpoint)

        if response:
            return {
                "name": response.get("name"),
                "full_name": response.get("full_name"),
                "description": response.get("description"),
                "stargazers_count": response.get("stargazers_count", 0),
                "language": response.get("language"),
                "updated_at": response.get("updated_at"),
                "html_url": response.get("html_url"),
                "topics": response.get("topics", [])
            }

        return None

    def _parse_github_result(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse GitHub search result into skill format.

        Args:
            item: GitHub API item

        Returns:
            Skill dict or None
        """
        try:
            name = item.get("name", "")
            path = item.get("path", "")
            repository = item.get("repository", {})

            # Skip if not in common skill locations
            skill_paths = ["agent", "skill", "mcp", "tool", "extension"]
            if not any(p in path.lower() for p in skill_paths):
                return None

            return {
                "title": name,
                "description": repository.get("description", ""),
                "github_stars": repository.get("stargazers_count", 0),
                "github_repo": repository.get("full_name", ""),
                "language": repository.get("language"),
                "updated_at": repository.get("updated_at"),
                "html_url": repository.get("html_url"),
                "path": path,
                "source": "github"
            }

        except Exception:
            return None

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make GitHub API request.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response data or None
        """
        url = f"{self.API_BASE}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)

            # Update rate limit info
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))

            self.request_count = self.rate_limit - remaining
            self.reset_time = reset_time

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                self.logger.warning("GitHub rate limit hit")
                return None
            elif response.status_code == 404:
                return None
            else:
                self.logger.warning(f"GitHub API error: {response.status_code}")
                return None

        except requests.Timeout:
            self.logger.warning("GitHub request timeout")
            return None
        except Exception as e:
            self.logger.warning(f"GitHub request error: {e}")
            return None

    def _is_rate_limited(self) -> bool:
        """Check if rate limited.

        Returns:
            True if rate limited
        """
        if self.reset_time:
            # Check if reset time passed
            if time.time() > self.reset_time:
                self.request_count = 0
                self.reset_time = None
                return False

            return self.request_count >= self.rate_limit

        return self.request_count >= self.rate_limit

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get from cache."""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            expires_at = data.get("expires_at")
            if expires_at:
                exp_time = datetime.fromisoformat(expires_at)
                if datetime.now() > exp_time:
                    cache_file.unlink()
                    return None

            return data.get("value")

        except Exception:
            return None

    def _set_cache(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set cache value."""
        cache_file = self.cache_dir / f"{key}.json"

        try:
            import json
            expires_at = datetime.now() + timedelta(seconds=ttl)

            data = {
                "value": value,
                "expires_at": expires_at.isoformat()
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

        except Exception as e:
            self.logger.warning(f"Cache write error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get searcher status.

        Returns:
            Status dict
        """
        return {
            "token_configured": bool(self.token),
            "rate_limit": self.rate_limit,
            "requests_used": self.request_count,
            "rate_limited": self._is_rate_limited()
        }


# Import for cache key generation
import hashlib
