"""
SkillsMP API client for skill search.

Provides access to 425K+ agent skills from SkillsMP.com.
API Documentation: https://skillsmp.com/docs/api
"""

import requests
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

from ..logging import get_logger


class SkillsMPAPIClient:
    """Client for SkillsMP API."""

    # API endpoints (based on https://skillsmp.com/docs/api)
    BASE_URL = "https://api.skillsmp.com/v1"
    SEARCH_ENDPOINT = "/skills/search"
    GET_SKILL_ENDPOINT = "/skills/{skill_id}"
    LIST_ENDPOINT = "/skills"
    CATEGORIES_ENDPOINT = "/categories"

    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    RATE_LIMIT_WINDOW = 60  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        rate_limit: int = DEFAULT_RATE_LIMIT
    ):
        """Initialize SkillsMP API client.

        Args:
            api_key: SkillsMP API key (optional, for higher rate limits)
            cache_dir: Directory for cache storage
            rate_limit: Requests per minute
        """
        self.logger = get_logger()
        self.api_key = api_key
        self.cache_dir = cache_dir or Path.home() / ".claude" / "memory" / "cache" / "skillsmp"

        # Rate limiting
        self.rate_limit = rate_limit
        self.request_times: List[float] = []

        # Setup cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "SpecKit-Memory-System/1.0"
            })

    def _check_rate_limit(self) -> bool:
        """Check if request is allowed under rate limit.

        Returns:
            True if request allowed
        """
        now = time.time()

        # Remove old request times outside window
        self.request_times = [
            t for t in self.request_times
            if now - t < self.RATE_LIMIT_WINDOW
        ]

        return len(self.request_times) < self.rate_limit

    def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit would be exceeded."""
        while not self._check_rate_limit():
            wait_time = self.RATE_LIMIT_WINDOW / self.rate_limit
            self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
            time.sleep(wait_time)

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated API request.

        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body

        Returns:
            Response data or None
        """
        # Rate limiting
        self._wait_for_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(
                    url,
                    params=params,
                    timeout=30
                )
            elif method == "POST":
                response = self.session.post(
                    url,
                    json=data,
                    timeout=30
                )
            else:
                self.logger.error(f"Unsupported method: {method}")
                return None

            # Record request time
            self.request_times.append(time.time())

            # Check response
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.logger.error("Invalid API key")
                return None
            elif response.status_code == 429:
                self.logger.warning("Rate limit exceeded, backing off")
                time.sleep(5)
                return None
            else:
                self.logger.warning(f"API error: {response.status_code}")
                return None

        except requests.Timeout:
            self.logger.warning("Request timeout")
            return None
        except Exception as e:
            self.logger.warning(f"Request error: {e}")
            return None

    def search_skills(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_stars: int = 2
    ) -> List[Dict[str, Any]]:
        """Search for skills.

        Args:
            query: Search query
            limit: Max results
            category: Filter by category
            min_stars: Minimum GitHub stars

        Returns:
            List of skill entries
        """
        # Check cache first
        cache_key = self._get_cache_key("search", query, category, min_stars)
        cached = self._get_cache(cache_key)
        if cached:
            self.logger.debug(f"Cache hit for search: {query}")
            return cached[:limit]

        # Make API request
        params = {
            "q": query,
            "limit": limit * 2,  # Fetch more for filtering
            "min_stars": min_stars
        }

        if category:
            params["category"] = category

        response = self._make_request(self.SEARCH_ENDPOINT, params=params)

        if not response:
            return []

        skills = response.get("skills", [])

        # Filter by min_stars (API might not support it)
        if min_stars > 0:
            skills = [
                s for s in skills
                if s.get("github_stars", 0) >= min_stars
            ]

        # Cache results
        self._set_cache(cache_key, skills, ttl=3600)  # 1 hour

        return skills[:limit]

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get skill details by ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill details or None
        """
        # Check cache
        cache_key = f"skill:{skill_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        endpoint = self.GET_SKILL_ENDPOINT.format(skill_id=skill_id)
        response = self._make_request(endpoint)

        if response:
            skill = response.get("skill")
            self._set_cache(cache_key, skill, ttl=86400)  # 24 hours
            return skill

        return None

    def list_categories(self) -> List[Dict[str, Any]]:
        """List available skill categories.

        Returns:
            List of categories
        """
        cache_key = "categories"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        response = self._make_request(self.CATEGORIES_ENDPOINT)

        if response:
            categories = response.get("categories", [])
            self._set_cache(cache_key, categories, ttl=86400)  # 24 hours
            return categories

        return []

    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Arguments to include in key

        Returns:
            Cache key string
        """
        key_str = ":".join(str(a) for a in args)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check expiration
            expires_at = data.get("expires_at")
            if expires_at:
                exp_time = datetime.fromisoformat(expires_at)
                if datetime.now() > exp_time:
                    cache_file.unlink()
                    return None

            return data.get("value")

        except Exception:
            return None

    def _set_cache(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
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
        """Get API client status.

        Returns:
            Status dict
        """
        return {
            "api_key_configured": bool(self.api_key),
            "cache_dir": str(self.cache_dir),
            "rate_limit": self.rate_limit,
            "recent_requests": len(self.request_times)
        }


class SkillsMPError(Exception):
    """SkillsMP API error."""

    def __init__(self, message: str, code: Optional[str] = None):
        """Initialize error.

        Args:
            message: Error message
            code: Error code
        """
        super().__init__(message)
        self.code = code
